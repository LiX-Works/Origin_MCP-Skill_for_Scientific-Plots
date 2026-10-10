"""Project-side Origin MCP helper. Does not install, launch, close, or reconfigure Origin.

Python 3.10+. MCP is imported only by connect(); offline tests use standard library.
One client and one transport per Origin session. Unknown-outcome RPCs are not retried.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

VERSION = "1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


class OriginCallError(RuntimeError):
    def __init__(self, tool: str, response: dict):
        self.tool, self.response = tool, response
        super().__init__(f"{tool}: {response.get('error_code', 'tool_failed')}: {response.get('message', '')}")


class DataMismatch(ValueError):
    pass


class LoadTimeout(TimeoutError):
    def __init__(self, diagnostics: dict):
        self.diagnostics = diagnostics
        super().__init__(f"Origin target data did not become ready: {diagnostics['last_observation']}")


class EventLog:
    """Exclusive per-run JSONL; large values stored once by content hash."""
    def __init__(self, folder: Path, inline_bytes: int = 2048):
        self.folder = Path(folder)
        if not self.folder.is_absolute():
            raise ValueError("Log directory must be absolute")
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / "events.jsonl"
        with self.path.open("xb"):
            pass
        self.inline_bytes = inline_bytes
        self.sequence = 0
        self.bytes_written = 0

    def reference(self, value: Any) -> dict:
        raw = encode(value)
        if len(raw) <= self.inline_bytes:
            return {"inline": value}
        digest = hashlib.sha256(raw).hexdigest()
        folder = self.folder / "payloads"
        folder.mkdir(exist_ok=True)
        path = folder / f"{digest}.json"
        if not path.exists():
            with path.open("xb") as f:
                f.write(raw)
            self.bytes_written += len(raw)
        return {"file": f"payloads/{digest}.json", "sha256": digest, "bytes": len(raw)}

    def append(self, event: dict) -> None:
        self.sequence += 1
        event = {"sequence": self.sequence, "at": utc_now(), **event}
        raw = encode(event) + b"\n"
        with self.path.open("ab") as f:
            f.write(raw)
        self.bytes_written += len(raw)


@dataclass(frozen=True)
class ExpectedSheet:
    book: str
    sheet: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    rel_tol: float = 1e-12
    abs_tol: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "rows", tuple(tuple(r) for r in self.rows))
        if not self.book or not self.sheet or not self.columns or not self.rows:
            raise ValueError("Expected book/sheet, columns and nonempty rows are required")
        if len(set(self.columns)) != len(self.columns) or any(not isinstance(c, str) or not c for c in self.columns):
            raise ValueError("Expected columns must be unique nonempty names")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("Expected row length differs from column count")
        if not (math.isfinite(self.rel_tol) and math.isfinite(self.abs_tol)) or min(self.rel_tol, self.abs_tol) < 0:
            raise ValueError("Invalid numeric tolerance")
        if any(isinstance(v, float) and not math.isfinite(v) for r in self.rows for v in r):
            raise ValueError("Expected values must be finite; use None explicitly for missing data")

    @property
    def key(self) -> str:
        return f"{self.book}/{self.sheet}"

    def check_window(self, actual: dict, start: int, count: int) -> None:
        ref = actual.get("worksheet", {})
        if (ref.get("book_name"), ref.get("sheet_name")) != (self.book, self.sheet):
            raise DataMismatch(f"{self.key}: wrong object identity")
        if actual.get("columns") != list(self.columns):
            raise DataMismatch(f"{self.key}: columns differ")
        if actual.get("total_rows") != len(self.rows) or actual.get("start_row") != start:
            raise DataMismatch(f"{self.key}: wrong total/start row")
        got = actual.get("rows", [])
        if len(got) != count or actual.get("returned_rows") != count:
            raise DataMismatch(f"{self.key}: incomplete window")
        for offset, row in enumerate(got):
            for col, wanted in zip(self.columns, self.rows[start + offset]):
                if col not in row:
                    raise DataMismatch(f"{self.key}: missing column {col}")
                value = row[col]
                if isinstance(wanted, (int, float)) and not isinstance(wanted, bool):
                    matches = (isinstance(value, (int, float)) and not isinstance(value, bool)
                               and math.isfinite(value) and math.isclose(value, wanted, rel_tol=self.rel_tol, abs_tol=self.abs_tol))
                else:
                    matches = type(value) is type(wanted) and value == wanted
                if not matches:
                    raise DataMismatch(f"{self.key}: row {start + offset}, column {col}: {value!r} != {wanted!r}")


class OriginClient:
    def __init__(self, session: Any, log_dir: Path, rpc_timeout: float = 45):
        if rpc_timeout <= 0:
            raise ValueError("RPC timeout must be positive")
        self.session = session
        self.log = EventLog(log_dir)
        self.rpc_timeout = rpc_timeout
        self._lock = asyncio.Lock()
        self.unknown_outcome = False
        self.calls = 0
        self.rpc_seconds = 0.0
        self.returned_rows = 0

    async def call(self, tool: str, args: dict | None = None) -> dict:
        """One serialized RPC. Returns data, raises on MCP/Origin errors, never retries."""
        if not tool.startswith("origin_"):
            raise ValueError("Only existing Origin MCP tools are supported")
        args = args or {}
        queued = time.monotonic()
        async with self._lock:
            if self.unknown_outcome:
                raise RuntimeError("Previous RPC outcome unknown; inspect session before reconnecting")
            started = time.monotonic()
            event = {"kind": "rpc", "tool": tool, "started_at": utc_now(),
                     "queue_ms": round((started - queued) * 1000, 3), "args": self.log.reference(args)}
            self.calls += 1
            transport_finished = None
            try:
                result = await asyncio.wait_for(self.session.call_tool(tool, args), self.rpc_timeout)
                transport_finished = time.monotonic()
                payload = getattr(result, "structuredContent", None)
                if payload is None:
                    for content in getattr(result, "content", []):
                        if getattr(content, "type", "") == "text":
                            try:
                                candidate = json.loads(content.text)
                            except ValueError:
                                continue
                            if isinstance(candidate, dict):
                                payload = candidate
                                break
                event["response"] = self.log.reference(payload)
                if getattr(result, "isError", False) or not isinstance(payload, dict) or payload.get("ok") is not True:
                    # The MCP server serializes bridge transport failures into
                    # normal tool responses. A sent request may still be running
                    # even though this outer RPC completed successfully.
                    if (not isinstance(payload, dict) or type(payload.get("ok")) is not bool
                            or payload.get("ok") is True
                            or payload.get("error_code") in {
                                "origin_bridge_timeout", "origin_bridge_failed", "origin_bridge_unavailable",
                            }):
                        self.unknown_outcome = True
                    raise OriginCallError(tool, payload if isinstance(payload, dict) else {"message": "Missing structured Origin response"})
                data = payload.get("data", {})
                if not isinstance(data, dict):
                    self.unknown_outcome = True
                    raise OriginCallError(tool, {"message": "Origin data is not an object"})
                if (tool == "origin_execute_figure_spec" and not args.get("dry_run", False)
                        and data.get("executed") is not True):
                    raise OriginCallError(tool, {"error_code": "figure_not_executed",
                                                "message": "Valid plan was not executed", "data": data})
                if tool == "origin_read_worksheet":
                    self.returned_rows += data.get("returned_rows", 0)
                event["outcome"] = "ok"
                return data
            except (TimeoutError, asyncio.CancelledError) as exc:
                self.unknown_outcome = True
                event.update(outcome="unknown", error_type=type(exc).__name__, error=str(exc), retry=False)
                raise
            except Exception as exc:
                if not isinstance(exc, OriginCallError):
                    self.unknown_outcome = True
                event.update(outcome="unknown" if self.unknown_outcome else "error", error_type=type(exc).__name__, error=str(exc), retry=False)
                raise
            finally:
                elapsed = time.monotonic() - started
                rpc_elapsed = (transport_finished or time.monotonic()) - started
                self.rpc_seconds += rpc_elapsed
                event["rpc_ms"] = round(rpc_elapsed * 1000, 3)
                event["client_processing_ms"] = round(max(0, elapsed - rpc_elapsed) * 1000, 3)
                self.log.append(event)

    async def _read(self, expected: ExpectedSheet, start: int, count: int) -> dict:
        return await self.call("origin_read_worksheet", {
            "book_name": expected.book, "sheet_name": expected.sheet,
            "start_row": start, "max_rows": count, "columns": list(expected.columns),
        })

    async def wait_for_data(self, expected: Sequence[ExpectedSheet], *, graphs: Sequence[str] = (),
                            timeout: float = 30, interval: float = 1) -> dict:
        """Readiness probe only. Use wait_and_verify for subsequent full numeric verification."""
        expected = tuple(expected)
        if not expected or len({e.key for e in expected}) != len(expected):
            raise ValueError("Provide unique, explicit expected worksheets")
        if timeout <= 0 or interval <= 0:
            raise ValueError("Wait bounds must be positive")
        started = time.monotonic()
        info = {"started_at": utc_now(), "page_seen_at": None, "first_nonempty_at": None,
                "first_expected_at": None, "stable_at": None, "polls": 0,
                "targets": [e.key for e in expected], "graphs": list(graphs), "last_observation": "not_checked"}
        previous, hits = None, 0

        def mark(key):
            if info[key] is None:
                info[key] = {"at": utc_now(), "elapsed_seconds": round(time.monotonic() - started, 4)}

        async def probe():
            project = await self.call("origin_list_project")
            sheets = {(b["name"], s["name"]): s for b in project.get("workbooks", []) for s in b.get("sheets", [])}
            present_graphs = {g["name"] for g in project.get("graphs", [])}
            if not set(graphs).issubset(present_graphs) or not all((e.book, e.sheet) in sheets for e in expected):
                raise DataMismatch("Expected worksheet or graph not present")
            mark("page_seen_at")
            samples = []
            for e in expected:
                if sheets[e.book, e.sheet].get("cols") != len(e.columns):
                    raise DataMismatch(f"{e.key}: project column count differs")
                windows = [(0, len(e.rows))] if len(e.rows) <= 16 else [(i, 1) for i in sorted({0, len(e.rows)//2, len(e.rows)-1})]
                for start, count in windows:
                    data = await self._read(e, start, count)
                    if any(any(v is not None for v in row.values()) for row in data.get("rows", [])):
                        mark("first_nonempty_at")
                    e.check_window(data, start, count)
                    samples.append(data["rows"])
            return encode(samples)

        while time.monotonic() - started < timeout:
            info["polls"] += 1
            try:
                current = await asyncio.wait_for(probe(), max(0.001, timeout - (time.monotonic() - started)))
                mark("first_expected_at")
                hits = hits + 1 if current == previous else 1
                previous = current
                info["last_observation"] = "expected_values_match"
                if hits >= 2:
                    mark("stable_at")
                    info.update(stable=True, stable_reads=hits, elapsed_seconds=round(time.monotonic() - started, 4), full_data_verified=False)
                    self.log.append({"kind": "load_wait", **info})
                    return info
            except DataMismatch as exc:
                previous, hits = None, 0
                info["last_observation"] = str(exc)
            except TimeoutError:
                info["last_observation"] = "RPC exceeded overall load deadline; outcome may be unknown"
                break
            await asyncio.sleep(min(interval, max(0, timeout - (time.monotonic() - started))))
        info.update(stable=False, elapsed_seconds=round(time.monotonic() - started, 4))
        self.log.append({"kind": "load_wait", **info})
        raise LoadTimeout(info)

    async def verify_data(self, expected: Sequence[ExpectedSheet], *, chunk_rows: int = 1000) -> dict:
        """One pass over only specified data; detects errors outside readiness samples."""
        expected = tuple(expected)
        if not expected or len({e.key for e in expected}) != len(expected):
            raise ValueError("Provide unique, explicit expected worksheets")
        if not 1 <= chunk_rows <= 1000:
            raise ValueError("chunk_rows must be 1..1000")
        checked = {}
        for e in expected:
            for start in range(0, len(e.rows), chunk_rows):
                count = min(chunk_rows, len(e.rows) - start)
                actual = await self._read(e, start, count)
                e.check_window(actual, start, count)
            checked[e.key] = {"rows": len(e.rows), "cols": len(e.columns), "all_expected_values_match": True}
        self.log.append({"kind": "data_verified", "sheets": checked})
        return checked

    async def wait_and_verify(self, expected: Sequence[ExpectedSheet], **wait_options) -> dict:
        expected = tuple(expected)
        ready = await self.wait_for_data(expected, **wait_options)
        verified = await self.verify_data(expected)
        return {"loading": ready, "data_verified": verified}

    async def save_new(self, path: Path) -> dict:
        path = Path(path)
        if not path.is_absolute() or path.suffix.lower() != ".opju" or not path.parent.is_dir():
            raise ValueError("An absolute .opju path with an existing parent is required")
        if path.exists():
            raise FileExistsError(path)
        result = await self.call("origin_save_project", {"path": str(path)})
        if (result.get("saved") is not True or Path(result.get("path", "")).resolve() != path.resolve()
                or not path.is_file() or path.stat().st_size <= 0):
            raise RuntimeError(f"Save was not verified: {path}")
        return {**result, "bytes": path.stat().st_size}

    def metrics(self) -> dict:
        return {"calls": self.calls, "returned_worksheet_rows": self.returned_rows,
                "rpc_seconds": round(self.rpc_seconds, 4), "log_bytes_written": self.log.bytes_written,
                "unknown_outcome": self.unknown_outcome}


@asynccontextmanager
async def connect(python_exe: Path, log_dir: Path, *, profile: str = "full", rpc_timeout: float = 45,
                  env: dict[str, str] | None = None):
    """One STDIO session; does not start Origin, change config, or close GUI on exit."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    python_exe, log_dir = Path(python_exe), Path(log_dir)
    if not python_exe.is_absolute() or not python_exe.is_file():
        raise ValueError("Existing absolute external Python executable required")
    if not log_dir.is_absolute():
        raise ValueError("Absolute log directory required")
    log_dir.mkdir(parents=True, exist_ok=True)
    params = StdioServerParameters(command=str(python_exe), args=["-B", "-m", "origin_mcp"],
                                   env={**os.environ, **(env or {}), "ORIGIN_MCP_TOOL_PROFILE": profile})
    with (log_dir / "server.stderr.log").open("x", encoding="utf-8") as stderr:
        async with stdio_client(params, errlog=stderr) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield OriginClient(session, log_dir, rpc_timeout=rpc_timeout)
