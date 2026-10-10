# Distributions of individual observations

Read after [common workflow](common-workflow.md) when the question concerns spread, shape, skew or tails of individual observations. One synthetic single-panel histogram with explicit bounds/width, full raw values, actual frequency counts and matching rendered heights has completed save/reopen checks. ECDF, box, violin and density views remain same-family follow-ups with separate unverified boundaries.

## Select the representation

- A histogram displays how many observations fall into intervals of a quantitative variable. Its appearance depends on bin boundaries as well as bin width.
- Use a count histogram when actual numbers per interval are the intended comparison; state the eligible observation count and sampling unit.
- If the input already contains bin centers/edges and counts, preserve it as a supplied frequency table. Do not feed its counts into a raw-observation histogram or claim to have recovered individual observations.
- A line through supplied counts is a different frequency representation; the first target requires a true histogram object bound to the raw values.
- Different group sizes can change count heights without changing relative distribution. A proportion or density view may answer another question, but needs an explicit normalization decision and separate execution checks.
- An ECDF answers cumulative-fraction questions without bins; a box plot summarizes specified quantiles/whiskers, and a violin adds a density estimate. None is automatically interchangeable with a histogram.
- Sparse samples, strong outliers, discrete values, and heavily overlapping groups may require a different form or additional context; explain the reason and current mode limit.
- Do not add fitted distributions, kernel density, smoothing, or significance tests as decoration.

## Record the observation source

- Identify source path/table, raw-value column, measured quantity and units, row range, group if any, and independent sampling unit.
- State whether a row is a person, sample, measurement, event, simulation draw, or repeated observation. Row count is not automatically independent replicate count.
- Repeated measurements can describe a measurement distribution, but pooling them changes the weighting of samples; preserve identities and state the displayed universe.
- Record total input rows, finite eligible observations, missing/nonfinite values, censored values, exclusions, and any values outside the intended histogram range separately.
- Missing is not zero. A genuine zero remains an observation; an empty code does not become a zero-valued bin entry.
- Do not silently transform units, trim outliers, deduplicate observations, or merge groups to improve the shape.
- If exclusions or transformations are authorized, retain original values and record the exact rule, counts, and destination of the derived column.
- Record source-to-Origin column mapping, actual Long Name, and row range; the histogram must bind to the intended raw values.
- Preserve source data and label synthetic observations as synthetic, including their generating rule/seed if used.

## Specify bins and normalization

- Declare a positive bin width in the variable's units before execution. Record its rationale and whether it was chosen before viewing the result.
- Width alone does not fix the intervals. Record the requested origin/start or explicit edges when the executor supports them, and read back actual Origin-generated lower/upper boundaries.
- If the current schema controls only width, do not invent an origin/edge key. State that Origin determines the origin or extent and capture those actual choices after execution.
- Record the inclusion convention at shared edges and the final edge, plus treatment of underflow/overflow. Establish it from actual behavior or evidence; do not assume a library convention applies to Origin.
- Check boundary-valued observations explicitly. Adjacent intervals must not double-count them or lose them.
- If actual edges or inclusion behavior cannot be established, bin/count verification remains incomplete even if the visible shape looks plausible.
- For the first target request count/frequency mode, with no percent, cumulative, probability, or density normalization. Read back the effective mode; an axis titled `Count` alone is not proof.
- Independently compare counts with raw values using the confirmed edges/convention. The sum must equal eligible in-range observations; separately reconcile omitted, missing, and out-of-range rows.
- Probability per bin is `count / N`; density is `count / (N × bin width)` for equal-width bins and has reciprocal-X units. Neither equals count, and density heights need not sum to one.
- Unequal-width bins need a different encoding/normalization decision and are outside the first equal-width target; equal-height count bars with differing widths can mislead through area.
- Use compatible edges and normalization when comparing distributions. Different widths or origins can move apparent modes; when an interpretation depends on bin choice, inspect reasonable alternative choices and report sensitivity without selecting the most dramatic result.

## Build the supported plan

- Use the existing FigureSpec schema and `histogram` path, with the intended raw-observation column as its actual data mapping.
- `histogram_bin_width` is source-listed styling; inspect the current schema and plan to confirm accepted placement and execution support.
- The current planner lists histogram only as the first plot in a FigureSpec. Keep the first target single-layer/single-histogram; overlays and grouped distributions need their own path checks.
- Retain the raw import specification, eligibility decisions, bin width, expected mode, and any supported edge request in the working record.
- Inspect plan warnings and `executor_executable` before the confirmed sole executor writes to the task session.
- After execution, verify the actual histogram object, its raw column/range binding, actual width/edges, bin counts, and effective normalization.
- A precomputed count table, a column plot, a successful plan, or `executed=false` does not meet this raw-observation histogram target.
- For refresh work on a task-owned copy, update compatible verified raw-value bindings, then recompute and recheck bins/counts. An unchanged preview is not evidence that histogram calculations refreshed.

## Axes and presentation

- X is the observed quantity in its original stated units; Y is `Count` or `Frequency (count)` for this target, with integer-compatible ticks and a zero baseline.
- Display full relevant bins and tails. Distinguish an axis viewport from an actual bin-range exclusion and disclose either when material.
- Do not choose a view or bins solely to hide an inconvenient tail or imply a desired mode.
- A log view, log-transformed values, and logarithmically spaced bins have different meanings. They require declared handling of nonpositive values, units/labels, and separate mode validation.
- Inspect whether bars occupy the intended intervals, especially first/last edges; do not infer boundaries from bar centers alone.
- Keep comparison groups identifiable and their sample sizes/normalization explicit; overlays, faceting, and unequal group weighting are later requests.
- Use common workflow sections 3–4 for page, font, and color decisions. A single histogram normally needs one clear series identity rather than magnitude coloring each bin.
- Captions or the handoff record should expose bin width, actual edges/origin, boundary rule, normalization, eligible `N`, and missing/excluded treatment where these affect interpretation.

## Same-family follow-ups

- **ECDF:** define eligibility/denominator, ties and step convention, any weights, and the terminal cumulative fraction. Its bin-free form still needs real object/binding and save/reopen evidence.
- **Box:** define quartile calculation, whisker rule, outliers, sample size, and group structure. `box` is source-listed; no live box case has been verified here.
- **Violin/density:** define kernel/bandwidth, support/boundaries, scaling/normalization, and group sample sizes. Raw-value availability does not establish an executable violin/KDE path.
- Do not infer uncertainty or significance from visual overlap or box/violin shape. Tests and statistical models remain separate decisions.
- Describe these as follow-ups in this family, not additional verified families or substitutes for a blocked histogram.

## Verify and deliver

- Compare every imported raw value and its row/range with the source, including valid zeros and duplicates.
- Read actual histogram type, dataset binding, selected range, effective normalization, width, edges, and counts; record any property the current tools cannot read.
- Reconcile all source rows with eligible/excluded/missing/out-of-range counts. Confirm integer nonnegative counts and their sum using actual boundaries.
- Inspect boundary cases, tail coverage, empty bins, X units, count-axis baseline/ticks, and unwanted overlays in the exact render.
- Apply common geometry/font readback and inspect the delivered export at final use size; a count label or plausible picture alone cannot establish count semantics.
- Save fresh task-owned project/export paths, reopen the exact project when possible, and repeat raw-binding and bin/count checks. Reopened appearance and calculation state both matter.
- Track `planned`, `executed`, `data_verified`, `visually_checked`, and `saved` independently. The synthetic 20-observation case has actual source binding, bin range 0–5, width 1, native frequency table counts 3/4/7/4/2, total 20, matching rendered heights, and save/reopen checks. See the repository's [validation summary](../../../VALIDATION.md). The normalization enum could not be read; report that metadata gap separately from the observed count behavior.
- In this tested Origin environment, native `OpenBinWks nRecalculate:=1` creates a sheet inside the histogram's source workbook. It is an explicit derived-data action; the inspector does not create it. Locate the actual new sheet, read its positional columns and reconcile counts rather than guessing English column names. The older `get -nhwc/-nhw` path was unavailable here.
- A requested X-axis view does not change the histogram's effective begin/end. Set or inspect actual bin anchors: the built-in template initially omitted observations above its retained end until explicit bounds were applied.
- One count histogram does not verify ECDF, box/violin, density, log/unequal bins, weights, multiple groups, or arbitrary sampling structures.
