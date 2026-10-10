"""Offline helper checks: no Origin imports, process launch, or networking."""
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from origin_client import OriginCallError, OriginClient


class FakeSession:
    def __init__(self, payload, is_error=False):
        self.payload = payload
        self.is_error = is_error
        self.calls = []

    async def call_tool(self, tool, args):
        self.calls.append((tool, args))
        return SimpleNamespace(structuredContent=self.payload, isError=self.is_error)


def test_ok_plan_without_execution_is_rejected(tmp_path):
    session = FakeSession({"ok": True, "data": {"executed": False}})
    client = OriginClient(session, tmp_path / "logs")
    with pytest.raises(OriginCallError) as error:
        asyncio.run(client.call("origin_execute_figure_spec", {"spec": {}}))
    assert error.value.response["error_code"] == "figure_not_executed"
    assert len(session.calls) == 1
    assert client.unknown_outcome is False


def test_existing_opju_is_rejected_before_rpc(tmp_path):
    target = tmp_path / "existing.opju"
    target.write_bytes(b"existing project")
    session = FakeSession({"ok": True, "data": {"saved": True}})
    client = OriginClient(session, tmp_path / "logs")
    with pytest.raises(FileExistsError):
        asyncio.run(client.save_new(target))
    assert session.calls == []
    assert target.read_bytes() == b"existing project"


@pytest.mark.parametrize("code", ["origin_bridge_timeout", "origin_bridge_failed", "origin_bridge_unavailable"])
def test_bridge_transport_error_blocks_following_rpc(tmp_path, code):
    session = FakeSession({"ok": False, "error_code": code, "message": "No confirmed response"})
    client = OriginClient(session, tmp_path / "logs")

    async def exercise():
        with pytest.raises(OriginCallError):
            await client.call("origin_save_project", {"path": str(tmp_path / "new.opju")})
        assert client.unknown_outcome is True
        with pytest.raises(RuntimeError, match="Previous RPC outcome unknown"):
            await client.call("origin_list_project")

    asyncio.run(exercise())
    assert len(session.calls) == 1


@pytest.mark.parametrize("payload,is_error", [
    (None, True),
    ({"data": {}}, False),
    ({"ok": True, "data": []}, False),
    ({"ok": True, "data": {}}, True),
])
def test_unusable_response_blocks_following_rpc(tmp_path, payload, is_error):
    session = FakeSession(payload, is_error)
    client = OriginClient(session, tmp_path / "logs")

    async def exercise():
        with pytest.raises(OriginCallError):
            await client.call("origin_save_project", {"path": str(tmp_path / "new.opju")})
        with pytest.raises(RuntimeError, match="Previous RPC outcome unknown"):
            await client.call("origin_list_project")

    asyncio.run(exercise())
    assert client.unknown_outcome is True
    assert len(session.calls) == 1


def test_explicit_business_rejection_does_not_block_reads(tmp_path):
    session = FakeSession({"ok": False, "error_code": "invalid_request", "message": "Invalid path"}, True)
    client = OriginClient(session, tmp_path / "logs")

    async def exercise():
        with pytest.raises(OriginCallError):
            await client.call("origin_save_project", {"path": "invalid"})
        assert client.unknown_outcome is False
        session.payload = {"ok": True, "data": {"graphs": []}}
        session.is_error = False
        assert await client.call("origin_list_project") == {"graphs": []}

    asyncio.run(exercise())
    assert len(session.calls) == 2
