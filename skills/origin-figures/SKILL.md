---
name: origin-figures
description: Create, adjust, refresh, and inspect scientific figures in Origin through an available Origin MCP session. Use for supplied data, requested graph types and styles, and editable Origin deliverables; suggest a graph when needed and report actual execution and verification limits.
---

# Origin Figures

Create and adjust Origin figures from the user's data, requested graph type, and style. Origin is the only plotting execution backend. The Agent handles figure specifications, checks, and delivery, and helps choose a graph when needed; the bundled Ge-Shun MCP supplies Origin operations. This skill does not install or register the MCP.

## Candidate boundary

This development candidate uses Ge-Shun/origin-mcp v0.1.4 as its fixed source baseline. Synthetic XY, ordered-summary column, raw-observation histogram and complete regular XYZ cell-heatmap cases have completed execution, full value/binding checks, visual review, save/reopen and owned-session exit. XY checks include single-series and shared-X four-series examples, using the paths described in the family reference. Verification of these cases does not establish arbitrary inputs or all upstream capabilities. See the repository [README](../../README.md) for examples and the family references for execution boundaries.

| Data/question | Reference to load | Candidate status |
|---|---|---|
| Ordered trend or XY relationship; scatter or point-and-line | [XY](references/xy.md) | Single-series and shared-X four-series synthetic point-and-line cases live verified; other modes need evidence |
| Category comparison from supplied summary values | [Category](references/category.md) | One ordered, single-series column case with zero baseline live verified |
| Distribution of individual observations | [Distribution](references/distribution.md) | One raw-observation histogram with explicit bins and observed count behavior live verified |
| Cell matrix or spatial field; complete regular numeric XYZ target | [Matrix/field](references/matrix-field.md) | One synthetic XYZ cell heatmap with a derived native matrix and explicit color scale live verified |

Read [common workflow](references/common-workflow.md) for session checks, data records, styling, evidence, and saving, then load only the relevant family reference. Route supplied category summaries to Category and raw observations to Distribution; an already-binned frequency table is not raw observations. For two indexing dimensions with a value per cell, or a quantity located by two physical coordinates, load Matrix/field and distinguish category identity from spatial geometry before choosing a heatmap. A written method or source-listed path does not establish execution. For an unimplemented mode, offer a defensible plan and identify the missing implementation; do not pretend another family or an unverified tool path completes it. ECDF/box/violin remain distribution follow-ups; error bars, polar plots, direct native-matrix input, irregular grids, interpolation, contour/height views, complex layouts, and fitting need later implementation/verification.

## Start with what the user supplies

Record the requested graph type and style, intended comparison, independent sampling unit, variables and units, missing/excluded values, existing transformations, and destination. Inspect inputs and load the family reference that supports the request. Follow the user's specified graph type and style; suggest an alternative or ask for clarification only when the graph type is missing, there is a material mismatch with the data, or essential information is absent. Explain a mismatch before changing the requested representation.

When helping choose a graph, use the supplied data and intended comparison to suggest a supported representation. Graph selection is supporting guidance, not a prerequisite for every request. A supported graph request authorizes ordinary, reversible figure work within its stated scope; it does not authorize unrelated analysis, installation, global configuration, or publication. Normalization, aggregation, smoothing, statistical tests, or fitted models are separate decisions, not automatic prerequisites for drawing.

## Dependencies and execution

- Use only a session whose identity, ownership, and Bridge reachability are confirmed for this task. One executor writes to that session; other agents or clients must not write concurrently.
- Never silently reuse an old environment or reconnect to an unidentified user session. Do not change global configuration to make this skill run.
- Distinguish tool discovery, a reachable Bridge, and an actual completed figure. The installed tool schema is authoritative; do not invent parameters from this prose.
- The bundled tool names are `origin_plan_figure_spec` and `origin_execute_figure_spec`, defined in `mcp/src/origin_mcp/tools/figurespec.py` at the repository root. A plan or `dry_run` is read-only preparation, not drawing. Check `executor_executable`, warnings, and `executed` before claiming execution; `executed=false` is never success.
- Record any missing dependency in the working handoff using the following HTML comment, then tell the user the blocked stage and minimum preparation. Continue independent inspection, semantics, or specification work. The comment is an audit record, not a substitute for visible disclosure.

<!-- dependency-gap: name=<missing tool/runtime/input>; stage=<blocked stage>; minimum-preparation=<smallest concrete preparation needed> -->

- Install, register, update, or start software only within existing task authorization and an identified environment. Do not add an MCP proxy, a new specification language, or another plotting backend.
- If a write times out or has an unknown outcome, inspect task state and artifacts before deciding to retry. If ownership or outcome remains unknown, stop dependent writes and report the gap; do not blindly repeat.

## Required decisions and evidence

Preserve input files and describe each derived table or transformation. Record source-column to Origin-column mappings: Origin may adjust Long Names, so inspect actual labels rather than blindly reading by old headers. Distinguish zero-based table-read row indices from one-based plot ranges. When refreshing an existing figure, inspect real bindings and update matching bound columns on a task-owned copy before rebuilding objects. Shared-data graph copies are not independent before/after evidence.

Determine data roles and units first; then estimate axes from actual values. Distinguish the Origin page, the layer/data frame, and the figure's final physical placement. Choose fonts, sizes, symbols, colors, legend or direct labels for the destination; serif, Arial, and numerical typography settings have no hard default here. Apply the common workflow's rules for italic quantity symbols, upright units and descriptions, and semantic subscripts; inspect the rendered text.

Use colors according to data roles, with redundant labels, symbols, or line styles where needed. A palette name, API response, or metadata check cannot prove readability, scientific correctness, or journal compliance. Inspect the actual render at final use size.

Track `planned`, `executed`, `data_verified`, `visually_checked`, and `saved` separately with evidence and gaps. Report the exact delivered files and the checks performed. Save to new task-owned paths by default; do not overwrite existing deliverables. For publication-specific requests, verify the relevant current official requirements separately; this development candidate makes no publication-readiness claim.
