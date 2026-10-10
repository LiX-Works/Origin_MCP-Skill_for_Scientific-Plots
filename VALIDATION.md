# Validation and development fixtures

Validation was performed on Windows with OriginPro 2026, using the bundled MCP source in an isolated Python environment and one explicitly owned Origin instance. The production installation, user projects and global Agent configuration were not modified.

## Recorded synthetic cases

| Case | Data and executed path | Checks |
|---|---|---|
| Single-series XY | 11 rows, numeric X/Y; FigureSpec point-and-line | Full values, actual A/B bindings and rows 1–11, axes, typography, physical page size, PNG/PDF export, OPJU save/reopen |
| Shared-X four-series XY | 11 rows, five columns; existing `origin_plot_line_symbol` table path | All values, A-to-B/C/D/E bindings, four plots, legend, axes, typography, rendered margins, save/reopen |
| Category column | Four supplied summary values and ordered text categories | Actual plot type, category tick source/order, Y bindings, zero baseline, all values, rendered bar heights, save/reopen |
| Raw histogram | 20 observations; explicit bins 0–5, width 1 | Native source binding, frequency sheet counts 3/4/7/4/2 and total 20, observed count-axis behavior, render, save/reopen |
| Cell heatmap | Complete uniform XYZ grid, 12 rows; derived 3×4 native matrix and plot type 105 | No interpolation or averaging, raw and matrix values/coordinates, actual matrix binding, color scale and direction, physical frame geometry, visible labels, save/reopen |

All cases had actual image inspection and successful saved-project data/binding checks. Decoded reopened PNG pixels matched their corresponding exports. README images are synthetic display examples; later label/grid and multi-series presentation revisions were also inspected. The final multi-series presentation revision's PDF was exported but not separately rendered for visual acceptance.

The final MCP change set passed 207 relevant offline checks before presentation revisions. The Skill metadata check passed. These counts describe the recorded development run, not every upstream test or every possible input. An existing dependency lifespan-annotation warning did not prevent the exercised operations.

## Developer helpers

`tools/origin_client.py` provides bounded MCP calls, expected-sheet checks and save/load handling. `tools/launch_isolated.py` starts a fresh owned Origin and a run-specific authenticated localhost Bridge; it refuses an ambiguous existing Origin session. The `run_xy_smoke.py`, `run_family_smoke.py` and `run_heatmap_smoke.py` fixtures use that bridge and require actual image review before finalization. Their `--help` output documents the phases. They are developer fixtures rather than normal MCP installation entrypoints.

Use a new empty absolute run directory for each fixture. Do not blindly replay a timed-out write, attach to an unidentified session, overwrite saved outputs or close a user's existing Origin. The live developer fixtures require the `origin` dependencies plus Pillow; offline tests require pytest. Runtime installation is described in [INSTALLATION.md](INSTALLATION.md).

## Remaining verification boundaries

- Shared-X four-series execution was checked through the existing table-plot tool; multi-series FigureSpec and independent XY-pair execution were not established by that check.
- Histogram normalization metadata and the older `get -nhwc/-nhw` path were unavailable. Observed count behavior was checked independently against the frequency sheet.
- The heatmap path requires complete finite uniform numeric XYZ. Duplicate/missing/irregular grids are rejected before Origin writes; direct native-matrix inputs, interpolation and arbitrary field modes were not verified. Updating the raw table requires explicitly rebuilding the derived matrix.
- Error bars, complex layouts, other upstream modes, other Agent configurations and installation on another computer remain outside the recorded live checks.

Private run logs and machine-specific execution records are retained in the development workspace and are not distributed with this repository.
