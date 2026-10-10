# Installation and startup

Install the bundled MCP from this repository so its workflow adaptations are included. The upstream `pip install origin-mcp` command installs a different distribution and is not the installation method for this project.

## Requirements

| Component | Preparation |
|---|---|
| Operating system | Windows, with the Agent and Origin running locally under the same Windows user |
| Origin | A licensed Origin/OriginPro installation with its Python Console; the bundled MCP targets the Origin 2026/2026b family |
| MCP Python | Python 3.10+ and pip; the example below uses Python 3.12 |
| Origin Python | Origin's separate embedded Python and its bridge dependencies, prepared in step 2 |
| Agent | Codex with local stdio MCP support and local Skill discovery |

Origin features and automation compatibility depend on the installed Origin version and edition. The repository's example validation does not establish compatibility with every version or every upstream tool.

## 1. Install this repository's MCP

Download or clone this repository, keep the complete `mcp/` directory, and open PowerShell at the repository root. Use a dedicated environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ./mcp
```

If Python 3.12 is unavailable, select an installed Python 3.10+ interpreter instead. Activation is unnecessary because all commands use the environment's executable directly. The local install resolves the dependencies declared in [mcp/pyproject.toml](mcp/pyproject.toml): `mcp`, `pydantic`, `pandas`, `openpyxl`, and `xlrd`.

Check where the package imports from:

```powershell
.\.venv\Scripts\python.exe -c "import origin_mcp; print(origin_mcp.__file__)"
```

It should point into this checkout's `mcp/src/origin_mcp`. Keep the checkout in place: this is an editable installation.

## 2. Start the bridge inside Origin

The MCP server and Origin bridge are separate processes. Installing into `.venv` does not install dependencies into Origin's Python or start Origin.

Open the Origin session you intend the Agent to use, then open its **Python Console**. Run the following there, replacing the placeholder with this repository's absolute path:

```python
import runpy
runpy.run_path(r"C:\path\to\repository\mcp\addon.py", run_name="__main__")
```

The addon loads the adjacent `mcp/src` source and starts the bridge in the foreground. Keep that console running while using MCP. A message reports **Bridge is running inside Origin**. The default address is `127.0.0.1:47631`; an authenticated handshake is written to `%TEMP%/origin-mcp/bridge.json` for the MCP client to discover.

On first startup, the addon checks for `originpro>=1.1`, `pandas>=2.0`, `openpyxl>=3.1`, and `xlrd>=2.0`. It attempts to install missing packages into **Origin's embedded Python**, using a user install if its global package directory is unwritable. This may require network access. To disable that automatic installation, set this in the Origin Python Console **before** the launch snippet:

```python
import os
os.environ["ORIGIN_MCP_INSTALL_MISSING"] = "0"
```

In that mode, prepare the reported missing packages in Origin's Python yourself before starting the bridge. Installing them only into `.venv` does not satisfy this dependency.

Use one identified Origin session and one writing client at a time. If the port is already occupied, identify and stop the existing bridge before starting another. Custom `ORIGIN_MCP_BRIDGE_HANDSHAKE` settings must use the same path in Origin and the MCP process; explicit host, port, or token overrides must also agree. See the [bridge guide](mcp/docs/origin-bridge.md) for diagnostics and lifecycle details.

## 3. Connect Codex over stdio

Add the following to your Codex `config.toml`. The user configuration is normally `%USERPROFILE%/.codex/config.toml`; a trusted project can instead use `.codex/config.toml`. Replace the example path with the absolute path to the `.venv` created in step 1:

```toml
[mcp_servers.origin]
command = "C:/path/to/repository/.venv/Scripts/python.exe"
args = ["-m", "origin_mcp"]

[mcp_servers.origin.env]
ORIGIN_MCP_TOOL_PROFILE = "full"
```

Use a unique server name if `origin` is already configured. The `full` profile exposes the specialized wrappers used by this project's family references and helpers. The bundled server otherwise defaults to a smaller `compact` profile.

Restart or reconnect Codex after editing its configuration. Codex launches `python -m origin_mcp` and communicates with it over stdin/stdout. This command starts the MCP server; the Origin-side addon from step 2 supplies the live automation connection.

Codex uses TOML tables for this configuration. The JSON `mcpServers` example in the retained upstream documentation is intended for clients using that JSON format. Consult the [official Codex MCP documentation](https://developers.openai.com/codex/mcp) for current configuration details.

## 4. Install the Skill

Copy the **entire** `skills/origin-figures` folder, including `references/` and `agents/`, into one of Codex's local Skill locations:

- Project use: `<your-working-project>/.agents/skills/origin-figures/`
- User use: `%USERPROFILE%/.agents/skills/origin-figures/`

The destination must contain `origin-figures/SKILL.md`, not an extra nested copy of the folder. Existing Skills should be reviewed before replacing them. Codex detects local Skill changes; restart it if the Skill does not appear. These locations follow the [official Codex Skill documentation](https://developers.openai.com/codex/skills).

Invoke `$origin-figures` with your data, requested graph type and style, and output destination. The Skill supplies workflow guidance; it does not install or register MCP, start Origin, or grant access to an unidentified Origin session.

## 5. Check the connection

After starting the intended Origin bridge, run these in PowerShell at the repository root:

```powershell
.\.venv\Scripts\python.exe -m origin_mcp status
.\.venv\Scripts\python.exe -m origin_mcp doctor --ping-origin --json
```

`status` probes the bridge. `doctor --ping-origin` also checks Origin automation and may show an Origin window. Confirm the reported package source and session identity before authorizing figure edits. Within Codex, the equivalent diagnostic tool is `origin_doctor` with `ping_origin=true`. A healthy connection establishes reachability; figure execution, data checks, visual inspection, and saving are separate workflow checks.

When finished, save your work before stopping the bridge. The bundled `mcp/scripts/stop_bridge.py` sends a shutdown request; in embedded mode the host Origin remains open, while external fallback automation can close its spawned Origin instance. The bridge guide explains this distinction.

## Optional Origin Start/Stop Apps and development tools

For toolbar-style startup, stage matching App sources from the local installation:

```powershell
.\.venv\Scripts\python.exe -m origin_mcp install-origin-app
```

This stages folders; it does **not** finish App registration. Run the exact `mkOPX` commands printed by the CLI in Origin's Command Window, then drag both generated OPX files into Origin to register them. Click **Origin MCP Bridge Start** once per session. Use this route or the manual addon route above. The Start App contains a copy of the bridge source, so restage, repack, and register it after relevant source updates; `--force` replaces existing staged App folders. See [Origin UI buttons](mcp/docs/origin-ui-buttons.md).

The root `tools/` directory contains development and validation helpers. `origin_client.py` provides serialized MCP calls, value verification, and event records. `launch_isolated.py` creates a dedicated external Origin instance for development; the `run_*_smoke.py` scripts create synthetic fixtures and saved validation artifacts. They are not required for installation or normal MCP startup.

For that external development launcher, the external Python environment also needs the local package's `origin` extra (`pip install -e "./mcp[origin]"`, which adds `originpro` and Windows `pywin32`). The heatmap helper's exported-image comparison additionally needs `Pillow` (`pip install Pillow`). Run such installation commands with the dedicated environment's Python and `-m pip`; Pillow is not a dependency of ordinary MCP startup.
