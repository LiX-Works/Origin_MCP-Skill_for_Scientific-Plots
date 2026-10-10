# Matrices and fields with value color

Read after [common workflow](common-workflow.md) when two indexing dimensions or physical coordinates locate a value. One synthetic complete regular numeric XYZ cell heatmap has completed full source/matrix and actual binding checks, visual review, export, save/reopen and owned-session exit. This representative case does not verify other inputs or modes.

## Select the representation

- A cell/category matrix compares values indexed by row and column identities, such as condition-by-sample summaries. Its spacing and adjacency need not imply physical distance.
- A spatial field locates measurements or model values by physical X/Y coordinates; distances, orientation and geometry can affect interpretation.
- Determine whether the question concerns cell lookup, a pattern across two dimensions, or physical location before choosing the representation.
- Heatmap color can expose broad patterns; use a table or supported direct labels when exact values are the main task. Do not imply fine quantitative discrimination from similar colors alone.
- Preserve meaningful category order and identity. A numeric category code is not automatically a continuous coordinate; sorting or clustering is a separate transformation.
- For a field, preserve coordinate spacing and domain context. Do not turn scattered point measurements into a continuous sampled surface by default.
- The current build target accepts regular numeric XYZ. Nominal-axis category matrices, direct native-matrix input, irregular grids, interpolation, contours and 3D height views require later implementation/verification.
- Respect a defensible requested view, but identify any conversion or current mode gap before claiming completion. Do not silently substitute another graph family.

## Record coordinates, values and grid structure

- Identify the source table, X/Y/Z columns, row range, coordinate definitions and units, and the quantity and unit represented by Z.
- State whether Z is an individual measurement, supplied cell summary, model output, density, count, probability or another quantity. Color must retain that meaning and denominator.
- Record the sampling or aggregation unit separately from the number of grid sites. Many spatial samples do not alone establish independent replicates.
- Preserve source data and label synthetic inputs as synthetic, with their generating rule/seed when used.
- Record the distinct X and Y coordinates, their order, direction and spacing, and the coordinate origin/reference where relevant.
- Check that numeric coordinates and values are finite or have explicit missing codes; units must be consistent within each coordinate and value column.
- Determine regularity from the actual coordinate differences, with a stated tolerance appropriate to source precision. A rectangular row count alone does not establish a regular grid.
- For the complete-grid target, check one Z per `(X, Y)` pair and every pair in the Cartesian product of the distinct coordinates. Record dimensions and total row count.
- Duplicate pairs may be repeated measurements, separate states or an input error. Preserve them and resolve their meaning; do not silently average or deduplicate.
- Missing pairs and missing Z values differ from a measured zero. Never fill them with zero, impute or interpolate merely to make the grid rectangular.
- A derived ordering/table must preserve each coordinate-value triplet and have its own mapping record; input row order is not proof of spatial orientation.
- If gaps, duplicate pairs or irregular spacing exceed this target, keep inspection/specification work and report the dependent execution gap in the entrypoint's dependency-comment format.

## Distinguish sample locations from cell extent

- Determine whether coordinates locate point measurements, cell centers, cell edges, or nodes of a supplied model grid.
- A point value has a location but no automatically justified area of influence. A tiled display of it is a representation choice, not evidence of a cell average or an interpolation method.
- A center coordinate differs from an edge coordinate: `n` cell centers locate `n` cells, while an explicit edge array needs `n + 1` boundaries along that dimension.
- Record supplied cell boundaries/extent when present. Do not invent half-spacing margins as a universal physical domain or silently replace node coordinates with centers.
- For the regular XYZ path, inspect how Origin places the displayed cells relative to coordinates and axis endpoints. Preserve any difference between requested extent and actual display extent.
- Verify X/Y assignment, axis direction, row-to-position correspondence, and whether the result was transposed, mirrored or rotated.
- Equal physical scale is appropriate when compatible coordinate units describe a shared space and distances, angles or geometry must be preserved. Convert compatible units explicitly if necessary.
- Equal scale means equal rendered length per physical unit, not necessarily a square page, layer or cell. It is not a default for category matrices or unrelated dimensions with different units.

## Specify value mapping and color scale

- Choose an ordered sequential scale for quantitative magnitude. Choose a diverging scale only around a scientifically meaningful reference; positive and negative values alone do not justify a midpoint.
- Use discrete qualitative colors and a category legend for nominal Z states; their numeric codes must not acquire magnitude meaning. This nominal-state mode is not verified by the continuous XYZ target.
- Periodic values need cyclic meaning and an appropriate verified mapping; they are a later mode rather than an automatic variant of the first heatmap.
- Record the actual finite Z minimum/maximum separately from requested color limits, center, direction and any transformation. Palette choice and numerical normalization are separate decisions.
- Start from the supplied values and question. Do not alter Z to make colors more attractive or automatically rescale each input independently.
- Confirm the colorbar's actual limits, tick values, direction, quantity label and units after execution; an axis/legend title alone does not prove the mapping.
- State any clipping/saturation, the number/range of values outside the color limits, and their displayed treatment. A narrowed scale must not silently make unequal extremes look equal.
- Missing and out-of-range states need distinct, explained treatment; missing must not use the quantitative low end. If the path cannot establish that treatment, verification remains incomplete.
- Log or other transformed color scales require an explicit reason, definition and treatment of ineligible values; support/readback must be established separately.
- Directly compared fields should share quantity/units, normalization, center, palette direction and limits. If independent scales serve the question, label the difference visibly.
- Check the actual background, final size, colorbar readability and distinguishable features. A palette name or grayscale conversion cannot certify accessibility.
- Do not infer spatial precision from small rendered pixels; source sampling spacing, resampling and export resolution are different quantities.

## Build and inspect the current XYZ target

- Use the existing FigureSpec heatmap path and current installed schema. Inspect planned operations and warnings; do not invent grid, palette or extent parameters from this prose.
- The current target preserves the full source XYZ table, orders distinct X/Y coordinates ascending, and maps each triplet into a derived native matrix without interpolation. Record source-to-grid row/column mapping and actual coordinate extent; this conversion does not verify arbitrary native-matrix input.
- Specify X/Y/Z roles, intended rows, one heatmap and one layer, with coordinate units, value meaning, view limits and color-scale decisions recorded.
- Inspect `executor_executable` and the execution result in the confirmed single-executor task session. A supported plan or `executed=false` is not a drawn field.
- Read actual workbook/sheet, column identifiers and Long Names; record source-to-Origin mappings for all three coordinates/value columns.
- Inspect the actual cell-heatmap object and its matrix binding, then trace that matrix to the preserved XYZ table and intended rows. An interpolated-contour object is not evidence for this cell-heatmap target; verify actual type rather than the graph title or requested mode.
- Read every imported XYZ triplet, compare with the preserved source, and repeat pair-completeness, duplicate, spacing and extrema checks. Read the derived matrix's full values, dimensions and coordinate extent, and verify each source pair lands in its intended cell. A few corners or a plausible image are insufficient data evidence.
- Check coordinate placement and orientation in both readback and render using identifiable source positions/values; symmetric inputs can hide a transpose or reversal.
- Read the actual color-scale configuration where supported and compare endpoint/center colors against known values in the render; record any property that cannot be read instead of inferring it from the request.
- For compatible refresh work, update verified source columns on a task-owned copy and rebuild/synchronize the derived matrix; it is not an automatically linked view of the XYZ table. A changed grid or domain also needs renewed extent, mapping and binding checks.

## Verify and deliver

- Inspect the exact exported heatmap at final use size for orientation, spatial extent, missing cells, clipping, coordinate ticks/units, colorbar labels/units and unwanted objects.
- Apply the common workflow's actual page/layer geometry and font readback, including colorbar text and symbols; confirm substitutions in the delivered render.
- Check each requested export's dimensions, format and readable content. A vector container may contain raster field content; DPI metadata does not create additional source detail.
- Save to new task-owned paths, reopen the exact OPJU when possible, and repeat full source XYZ and derived-matrix values/coordinates, actual plot type/binding, axes and color-scale checks on the saved project.
- Inspect the reopened render and record its correspondence with the delivered exports. Saving alone does not establish preserved data or appearance.
- Track `planned`, `executed`, `data_verified`, `visually_checked` and `saved` independently with exact evidence paths and remaining gaps.
- Current status: one synthetic complete regular XYZ representative is live verified (`heatmap_20261010_05`), including all 12 source triplets, the full 3×4 derived matrix and coordinates, actual cell-heatmap type/binding, color mapping and visible units, and save/reopen with identical PNG pixels. Numeric style settings and palette choices in that fixture are not public defaults. Native matrix input, nominal-axis/state matrices, irregular or missing grids, interpolation, transformed color scales, contours, 3D height views, multiple fields and uncertainty overlays remain unverified follow-ups.
