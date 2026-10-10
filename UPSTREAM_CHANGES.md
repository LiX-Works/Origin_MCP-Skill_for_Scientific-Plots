# Changes to the bundled MCP

Baseline: [Ge-Shun/origin-mcp v0.1.4](https://github.com/Ge-Shun/origin-mcp/tree/fecb7226ed60d7651d921d2586eb9950bf16b618). Original licensing and attribution remain in `mcp/LICENSE` and `mcp/NOTICE`. These changes belong to this development candidate; they are not claims about an upstream release.

| Change | Reason | Candidate files |
|---|---|---|
| Explicit title, tick and legend sizes in FigureSpec | A figure needs typography chosen for its final physical size | `models.py`, `tools/figurespec.py` |
| Correct title and tick property paths | Axis titles are `xb`/`yl` labels; `x.label`/`y.label` are tick labels | `client/graph_style.py`, `tools/figurespec.py` |
| Physical page size conversion and aspect-lock handling | Origin stores page sizes in printer dots; setting both dimensions while keeping the old ratio changed the requested width | `client/graph_formatting.py` |
| Actual page, layer and typography readback | Requested parameters and successful responses do not establish the resulting dimensions or font sizes | `client/graph_formatting_helpers.py`, `client/graph_formatting.py` |
| Actual XY source and displayed row-range readback | A graph plot address differs from its source worksheet range; real ranges can contain quoted column Long Names | `client/graph_formatting_helpers.py` |
| Histogram default template and failed-template reporting | Origin 2026 provides `Hist.otpu`; `histogram` resolved incorrectly and failed later with a misleading plot error | `client/table_plot.py` |
| Exact column count for imported plot tables | A single raw-value column otherwise retained a second empty worksheet column | `client/table_plot.py` |
| Native plot type, histogram source/bounds and tick-label source | A histogram binds observations rather than an XY curve, and category order depends on the real tick dataset | `client/graph_formatting_helpers.py` |
| True cell heatmap from complete regular XYZ | Native 243 is an interpolated contour; native 105 displays matrix cells. Preserve the raw table and reorder its values without interpolation | `tools/figurespec.py` |
| Matrix plot page identity and actual source readback | Origin can apply the requested name to the layer while creating a differently named page; actual matrix ranges include optional display names | `client/table_plot.py`, `client/graph_formatting_helpers.py` |
| Existing color-scale label properties | Nested font/size properties need scoped LabTalk readback when the native object getter cannot read them | `client/graph_formatting_helpers.py` |

The readback leaves unreadable fields explicit. Font IDs and point sizes are available; the inspector does not invent a font-family name from the requested style. Source-column row ranges and graph display row ranges are recorded separately. This XY implementation is not a binding inspector for every Origin plot type.

The project-side helper also rejects `ok=true, executed=false` as an incomplete drawing and blocks further writes after an ambiguous Bridge response. The development launcher creates one owned Origin instance, uses a dedicated authenticated local Bridge, and refuses an ambiguous existing session. These helpers do not replace the upstream MCP protocol or install an Origin add-on.

The recorded synthetic case includes a deliberate presentation adjustment through the existing LabTalk tool: disable automatic numeric endpoint labels, omit a redundant single-series legend, and simplify tick decimals. This is a fixture-specific choice, not a blanket removal of labels from scientific figures.

Verified cases: point-and-line, ordered-summary column, raw-observation histogram and complete regular XYZ cell heatmap. All retain actual values/binding, explicit typography and dimensions, PNG/PDF output, OPJU save/reopen and identical reopened pixels. The histogram fixture explicitly creates a native frequency sheet through `OpenBinWks`; normalization metadata remains unavailable. The heatmap preserves all original XYZ values, derives a 3×4 matrix without interpolation, and reads the real plotted matrix and color scale. A shared-X, four-series point-and-line gallery example was also checked through the existing table-plot path. Arbitrary inputs, other modes and installation on another computer remain unverified. See [VALIDATION.md](VALIDATION.md) for the public summary and development helpers.

The heatmap fixture uses a separate visible units annotation after hiding the template's oversized native color-scale title. Its actual text, font and size are read back. Origin does not persist hidden title text on reopen; the visible annotation and rendered result are the delivered evidence. This example's numeric geometry, typography and palette settings are not general defaults.

Interface references: [axis tick-label object](https://docs.originlab.com/labtalk/ref/layer-axis-label-obj/), [page dimensions](https://docs.originlab.com/quick-help/specify-graph-size/), [page aspect lock](https://docs.originlab.com/labtalk/ref/page-obj/), [source range notation](https://docs.originlab.com/labtalk/guide/range-notation/), [displayed range bounds](https://docs.originlab.com/labtalk/ref/get-cmd/), [plot-label controls](https://docs.originlab.com/labtalk/ref/options_for_data_plot_labels/).

Heatmap interfaces: [native plot types](https://docs.originlab.com/labtalk/ref/plot-type-ids/), [color-scale object](https://docs.originlab.com/labtalk/ref/spectrum1-obj/), [palette direction and levels](https://docs.originlab.com/labtalk/ref/layer-cmap-obj/).
