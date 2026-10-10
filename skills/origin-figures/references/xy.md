# XY relationship and ordered-trend figures

Read after the common workflow when numeric X/Y positions express the requested relationship or order.
Stage 2 completed one single-panel, single-curve synthetic point-and-line figure with 11 rows and two columns, including full value/binding checks and a saved/reopened project. Additional inputs and modes require their own recorded execution checks.

The README gallery additionally uses an executed shared-X, four-series synthetic point-and-line example (11 rows, five columns) through `origin_plot_line_symbol` with one `x_col` and four `y_cols`. Actual values, all four bindings, legend, appearance and saved/reopened output were checked. This existing table-plot path does not establish multi-series FigureSpec execution or separate XY-pair support.

## Select the representation

- Use scatter for relationships among observations when joining them would imply unsupported order.
- Use lines or point-and-line for an ordered sequence, time series, or a supported continuous trace.
- State what connecting adjacent points means; categorical order alone does not imply interpolation.
- Preserve a user's reasonable requested form while explaining any material semantic mismatch.
- Multiple series may share X or have independent XY pairs; inspect which structure the input uses.
- A common X column is not a reason to merge sampling units or average repeated observations.
- Dense series may need panels or another representation; these are later layout requests, not Stage 2 promises.
- Do not add a fitted curve, trend estimate, smoothing, or significant-difference annotation automatically.

## Record inputs and column roles

- Identify the source table, independent observation/sample unit, X quantity, Y quantity, and units.
- Identify series names and any parameter ordering separately from analytic/reference series.
- Record each source column, row range, and missing-value representation before import.
- Use unambiguous column identifiers; duplicated display names can conceal binding mistakes.
- Origin may adjust column Long Names. Read actual labels and record source-column to Origin-column mappings; do not query blindly by the pre-plot headers.
- Table-read row indices are zero-based; actual plot ranges are one-based. The verified fixture maps 11 input rows to plot rows 1–11, not 0–10.
- For shared X, bind each Y to the intended X range; for separate pairs, record each pair explicitly.
- Preserve row order unless changing it is scientifically justified; record a sorted working copy when needed.
- Detect duplicate X, uneven spacing, nonfinite values, missing segments, and X/Y length mismatches.
- Duplicate X values may be distinct observations or repeated sampling; do not silently collapse them.
- A line must not bridge missing observations by silently dropping rows.
- If the current executor cannot produce the required gap, report the limit before drawing that mode.
- Keep synthetic data labeled as synthetic in specifications and evidence, including its generating rule/seed if used.

## Build the supported plan

- Use the existing FigureSpec schema and the relevant single-layer plot type exposed by the bundled MCP.
- For the shared-X multi-series table path, use `origin_plot_line_symbol` with the explicit X and Y columns; inspect actual plot bindings after import and verify the legend against the resulting series.
- `line`, `scatter`, and `line_symbol` are source-listed types; listing does not prove runtime success.
- Start with explicit data roles and a single layer; inspect `origin_plan_figure_spec` warnings.
- Treat `executor_executable=false`, unsupported styling, or an unhandled data shape as a blocked operation.
- Preserve the source, import choices, series-to-column mapping, and geometry/style decisions in a small record.
- Draw only in the confirmed task session with its sole executor; retain the plan before execution.
- If refreshing an existing compatible plot, use its verified bound columns on a copy first.
- Avoid rebuilding a formatted graph merely because its data changed.

## Axes, units, and layout

- Estimate X/Y limits from imported values, then inspect the rendered result before targeted adjustment.
- Nonzero point/line limits can be meaningful; document excluded view ranges, breaks, and context.
- Preserve all input rows when zooming; distinguish viewport decisions from data exclusion.
- For a log axis, establish quantity, units, base, and nonpositive-value treatment before execution.
- Keep tick labels interpretable in the stated units; do not confuse an axis transform with transformed data.
- Do not use independent Y axes to manufacture apparent agreement between series.
- Distinguish the physical Origin page from the layer frame and final placement size.
- Set readable fonts, line widths, symbols, and tick density for the chosen final size, then inspect the render.
- Do not force serif/Arial, a particular point size, aspect ratio, or zero baseline as a universal XY rule.
- For nominal series, use labels and distinguishable symbols/lines; ordered parameters may justify an ordered palette.
- Use a legend or direct labels according to actual crowding, series count, and endpoint geometry.
- Verify legend entries against the true plotted series, including omitted or extra curves.

## Supplied uncertainty: separate verification

- Error columns must state SD, SE, CI, bounds, or another meaning, and the independent replication unit.
- Symmetric magnitudes differ from absolute lower/upper endpoints; record their semantics before binding.
- Check matching lengths/ranges and how missing or invalid uncertainty values are handled.
- The Stage 2 point-and-line target does not prove error-bar or uncertainty-band execution.
- Do not add error bars because a plan accepted a key; inspect actual error objects and their bindings.
- If the requested uncertainty mode is unimplemented or unverified, disclose the gap and preserve its inputs.
- Do not invent uncertainty or run a statistical model to fill the gap.

## Verify and deliver

- Confirm actual worksheet values, X/Y bindings, row ranges, series count, and axes after execution.
- Compare representative source/imported points and extrema; distinguish data bounds from displayed bounds.
- Inspect continuity and missing gaps, symbol/line placement, series identity, labels, units, and legend.
- Read back and inspect chosen typography and geometry; an export image alone may conceal wrong data binding.
- Inspect the exact export at final use size for readability and clipping; retain a larger diagnostic preview if useful.
- Save to fresh task-owned project/export paths, and record exact filenames and reopen status.
- In the bounded runner, inspect `xy-review.png` before `finalize --visual-reviewed`, then inspect `xy-reopened.png` and saved-project value/binding readback before `close`; the flag records inspection already performed.
- Track `planned`, `executed`, `data_verified`, `visually_checked`, and `saved` independently.
- Explain unverified modes without upgrading source-level support or a successful synthetic case to general coverage.
