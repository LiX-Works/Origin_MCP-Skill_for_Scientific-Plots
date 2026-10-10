# Category comparisons from supplied summaries

Read after [common workflow](common-workflow.md) when category identity and a supplied numeric summary define the comparison. One synthetic single-panel column case with explicit category order and a zero baseline has completed live execution, binding, visual and save/reopen checks. Further modes require their own evidence.

## Select the representation

- Use columns to compare supplied magnitudes across a modest number of categories on a common scale.
- Identify whether the categories are nominal, ordinal, stages, or ranked items before choosing their order.
- Preserve an explicit user order. For meaningful sequences, retain that sequence and reading direction.
- Sorting nominal categories can answer a ranking question, but record the sorting decision and original order; do not silently sort the first target.
- A category code is an identity or position, not a measured continuous X variable. Do not join columns with a line implying interpolation.
- When small differences against a large common level are the question, consider a position encoding such as dots rather than truncating column lengths. That is a separately specified mode, not verified column coverage.
- Many categories, long labels, grouped comparisons, stacks, and horizontal bars may merit another form or layout; they remain later modes needing their own support checks.
- Signed differences are not shares of a whole. A share requires a defined denominator; values adding to 100 do not alone justify stacking.
- A table is useful for exact lookup or quantities without an honest common unit.

## Record inputs and category roles

- Identify the source table, category column, supplied value column, quantity, units, and denominator/reference if relevant.
- State what each value means: reported mean, sum, percentage, estimate, model output, or another existing summary. Preserve its supplied estimator; do not infer it from the header.
- Separate category count, contributing observation count, and independent replicate count. If the source does not provide `n` or replication units, mark them unknown.
- The first target has one supplied value per category. Repeated category labels can mean separate series, distinct entities, or raw replicates; resolve that structure rather than aggregating them automatically.
- Record exact category labels and their order separately from any numeric positions used by Origin.
- Use stable column identifiers and record source-to-Origin mappings, actual Long Names, and row ranges after plotting.
- Detect duplicated labels, incompatible units, nonfinite values, empty labels, and value/category length mismatches before import.
- Distinguish a reported zero from an absent category or missing summary. Do not fill missing values with zero or silently remove their labels.
- If a missing summary cannot be represented truthfully by the current path, preserve it and report that dependent drawing limit.
- Keep supplied data intact; any authorized reordering or derived table gets its own transformation record.
- Label synthetic inputs as synthetic, with their rule/seed when applicable. They do not establish biological, physical, or statistical conclusions.

## Build the supported plan

- Use the existing FigureSpec schema and `column` path; inspect the current schema, operations, and warnings rather than inventing category parameters.
- Specify category identity/order, supplied Y values, the intended row range, one series, and a single layer for the first target.
- Check whether the executor imports text categories or uses numeric positions plus tick labels. Either representation needs a verified label-to-position mapping.
- If numeric positions are used, bind each supplied value to its intended category and inspect the actual category labels; a correctly shaped column chart with numeric ticks is incomplete.
- Inspect `origin_plan_figure_spec` support and `executor_executable`. Do not treat accepted style keys or `executed=false` as a drawn chart.
- Retain the source, summary definitions, ordering, mapping, and actual planned operations in a small record.
- Draw only in the confirmed task session with its sole executor. Inspect actual column objects and dataset bindings afterward.
- For compatible refresh work, update verified bound columns on a task-owned copy before rebuilding. Adding/reordering categories may require explicit label and range changes.

## Value axis and category labels

- Set the value baseline to zero for this column-length target. For nonnegative values the value axis starts at zero; signed values extend to both sides of zero.
- Do not use a log value axis or an axis break to alter the length comparison. If another reference/scale is needed, specify a suitable position representation and its limits separately.
- Estimate the upper/lower view limits from all supplied values and reserve only necessary label space; verify that no column is clipped.
- Keep category ticks centered on their columns, with labels matching exact order and identity.
- Choose label rotation, wrapping, or orientation from actual label density and final use size; verify the current executor supports the choice before claiming it.
- Label the value axis with the supplied quantity and unit/denominator. Do not label an existing summary as individual observations.
- Use a legend only when it adds information beyond the category labels or identifies multiple verified series.
- For page/font/color choices, use common workflow sections 3–4. A single comparison does not need a separate hue per category unless identity or a stated focal comparison benefits.
- Any direct value labels must match the source precision and units; decorative emphasis must not imply statistical significance.

## Uncertainty and inference stay separate

- Do not invent replicates, error bars, confidence intervals, or significance stars from supplied summary values.
- Supplied intervals need their meaning, estimator, sample size where available, and independent replication unit; symmetric error magnitudes differ from absolute endpoints.
- Explicit uncertainty objects and their binding require separate execution evidence. The first simple column target does not verify them.
- Statistical tests, aggregation of raw observations, normalization, and resampling are separate authorized analysis decisions, not automatic chart steps.
- If a supplied estimate has no uncertainty information, report that omission as source context instead of synthesizing uncertainty.

## Verify and deliver

- Compare every imported category/value pair with the supplied table and confirm that order is unchanged.
- Read actual worksheet labels/values, plot count, category positions/tick labels, Y bindings, and selected rows. Reconcile zero-based table reads with one-based plot ranges.
- Verify actual column objects rather than assuming any X/Y-looking object is a column chart.
- Confirm a zero baseline and correct signed/nonnegative limits after execution; check column lengths and label placement in the render.
- Inspect missing-category treatment, values, units, category identity, readable labels, and any unwanted legend or extra series.
- Apply the common workflow's geometry/font readback and exact-export visual inspection at final use size.
- Save to fresh task-owned paths, reopen the exact project when possible, and repeat category/value/order/binding checks on the saved project.
- Track `planned`, `executed`, `data_verified`, `visually_checked`, and `saved` independently. In the synthetic four-category column case, actual A/B bindings, text-column tick source, row order, zero baseline, full values and save/reopen were checked; exact renders confirmed label order and column heights. See the repository's [validation summary](../../../VALIDATION.md). This case does not establish arbitrary inputs.
- Grouped/stacked bars, horizontal bars, category dot plots, supplied uncertainty, and category aggregation are not verified by this first target.
