# Common Origin workflow

Apply this to a supported family; add only the family reference needed for the supplied data.

## 1. Establish the task and session

- Identify the requested graph type and style, question or intended comparison, audience, destination, and editable/export deliverables.
- Follow the supplied graph and style choices. Suggest a graph or clarify only when the type is missing, the requested representation materially mismatches the data, or essential information is absent; explain the issue before changing the target.
- If the scientific conclusion is still exploratory, state the question without manufacturing a desired result.
- Identify the task-owned output directory and the source inputs; preserve originals.
- Discover the tools in the current session and inspect the schema of the tools actually needed.
- Confirm session identity, ownership, Bridge reachability, and the single executor before writing.
- Reachability alone does not show isolation; never reset a user project to obtain a clean test.
- The development launcher rejects any already-running Origin and creates its own instance without attach; keep its terminal running for the build/finalize/close phases.
- A missing tool, runtime, input, or permission blocks only its dependent stage.
- Record the dependency's name, blocked stage, and minimum preparation in the entrypoint's HTML-comment format, and disclose it visibly. Continue independent work.

## 2. Inspect and preserve data

- Record source path or identifier, variable definitions, units, sampling unit, and row/column counts.
- Distinguish zero, missing, censored, excluded, and nonfinite values; inspect their positions and codes.
- Identify whether values are individual observations, supplied summaries, model outputs, or synthetic tests.
- Keep input data intact. Place derived columns/tables in task-owned locations with an explicit transformation record.
- Record formulas, reference values, filters, ordering changes, bins, or seeds only when used.
- Do not normalize, aggregate, fit, smooth, interpolate, or perform statistics merely to make a chart.
- Supplied uncertainty requires a definition and replication unit; an error-looking column is not sufficient.
- For refresh work, inspect workbook, sheet, columns, ranges, curve count, and true plot bindings first.
- Record source-column to actual Origin-column mappings and Long Names; Origin can change labels during plotting. Table reads use zero-based row indices, while plot ranges use one-based rows; compare their intended ranges explicitly.
- Update compatible bound columns on a copy; rebuild only when the data structure or requested graph requires it.
- Separate before/after projects or verify independent data; duplicating a graph can retain shared bindings.

## 3. Specify encoding and geometry

- Load the family that supports the requested graph and check it against the supplied data; when graph choice is needed, match the family to the comparison and data grain. Unsupported requests remain explicit gaps.
- Use labels and units that express the quantity and denominator, including derived quantities.
- Estimate axis limits and ticks after inspecting values; preserve data even when the view is narrower.
- Document meaningful zoom, axis breaks, nonpositive log values, and any points outside the viewport.
- Choose comparable scales for compared panels unless independent scales answer the stated question.
- Distinguish page size, layer/data-frame dimensions, and final physical placement in a document or slide.
- Use the destination's intended dimensions; record any provisional geometry as a task choice.
- Read back units and actual dimensions where supported; parameter names alone do not prove geometry.
- Choose an available font family and readable sizes for the final render; verify substitutions and symbols.
- Serif and sans-serif are choices, not mandated defaults; no universal point size or journal width applies.
- Italicize quantity or variable symbols, including Latin and Greek symbols. Keep units, SI prefixes, word descriptions, and category names upright; apply italics to the symbol within a label, not the entire axis title.
- Format subscripts by meaning: descriptive words or identifiers are upright, while variable symbols and variable indices are italic. Do not apply a single style to every subscript or label.
- Where the active Origin text object supports rich text, a label such as `r'\i(t) (s)'` can make the variable `t` italic and its unit `s` upright. Inspect the actual render to confirm that formatting is applied and the markup is not shown literally.
- Tune labels, ticks, symbols, line widths, and legend together at final use size.
- Use a legend, direct labels, or an annotation only when it helps identify the actual rendered objects.

For quantity symbols, units, and subscripts, see the [NIST SI checklist, items 6–7](https://physics.nist.gov/cuu/Units/checklist.html). These rules apply to symbols; a word label such as “Count” does not become italic simply because it labels an axis.

## 4. Specify color and context

- Nominal series use identity colors; quantitative magnitude uses an ordered scale.
- A diverging scale needs a meaningful center; cyclic scales need a genuinely periodic variable.
- Distinguish the palette from value mapping: record limits, center, transform, missing and out-of-range behavior.
- Keep equivalent series or quantities consistently encoded across comparison figures.
- Analytical/reference series need their own role; do not include them blindly in a parameter color sequence.
- Use color alongside symbols, line styles, labels, or layout where color alone makes decoding fragile.
- Check distinctions against the actual background and at final size; grayscale is only one diagnostic.
- A color-vision-friendly palette label does not prove accessibility in the final artifact.
- Add auxiliary gridlines only when they help the requested scientific reading. Omit them in the README's column and histogram examples; they are optional in the XY example.
- Distinguish gridlines from data series, analytical curves, thresholds, and scientific reference lines. Preserve user-supplied lines with scientific meaning unless the task calls for changing them.
- Add thresholds, reference lines, or events only when supplied or justified by the question.

## 5. Plan, execute, and inspect

- Validate the existing FigureSpec against the bundled model/schema rather than inventing an extension.
- Inspect the operation plan, unsupported features, warnings, and `executor_executable` before execution.
- `origin_plan_figure_spec`, `dry_run`, or a valid specification yields only planning evidence.
- Inspect the execution result: `ok` without `executed=true` does not establish drawing.
- After an unknown outcome, inspect state/artifacts before retrying; unresolved ownership blocks writes.
- Read back worksheet values, real dataset bindings, selected row ranges, plot count, and relevant axes.
- Compare counts, extrema, and representative values with the input; investigate discrepancies.
- Explicit error bars, fonts, styles, and physical dimensions require evidence for those objects, not inference.
- Inspect the rendered image for missing segments, clipping, units, ticks, labels, quantity-symbol italics, upright units/descriptions, subscript meaning, color mapping, and legend.
- Check at final use size and enlarge only to diagnose details; record visual checks that remain unavailable.
- Return to data/encoding decisions if meaning is wrong; stop appearance iteration when task criteria are met.

## 6. Save and report exact evidence

- Use new task-owned paths for editable Origin projects and requested exports; refuse implicit overwrite.
- Check whether each target already exists immediately before the save/export operation.
- Specify requested format, background, physical size, pixels/effective resolution, and applicable color mode.
- Vector containers can contain rasters; DPI metadata cannot create detail. Cropping may change final size.
- Verify file existence, nonempty content, and a readable delivered render; reopen the exact saved project when possible.
- A saved project/export pair needs a correspondence record; a working preview is not evidence for another file.
- The Stage 2 runner's `--visual-reviewed` records an actual inspection of `xy-review.png`; pass it only after that check, then inspect `xy-reopened.png` and saved-project readback. This is an evidence step, not a new user approval gate.
- Preserve the execution and verification record alongside the data/specification and deliverables.
- Keep run-private handshake/session material and raw logs separate from shareable figure files; close only the task-owned instance after final checks.

| State | Evidence needed | Does not imply |
|---|---|---|
| `planned` | Valid specification, supported plan, recorded choices | Origin operations occurred |
| `executed` | Positive execution evidence in the identified session | Data or visual correctness |
| `data_verified` | Readback agrees with source and bindings/ranges | Typography or geometry passed |
| `visually_checked` | Actual render inspected at final use size | File was saved or journal compliance |
| `saved` | Exact deliverable files checked; reopen status recorded | All other checks passed |

Report these states independently, with paths and remaining gaps. Partial output should carry partial evidence.
