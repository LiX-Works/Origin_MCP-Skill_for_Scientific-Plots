# Origin MCP + Skill for Scientific Plots

[中文介绍](README.zh-CN.md)

**Origin_MCP-Skill_for_Scientific-Plots** lets an AI Agent create, refine, and deliver clear, editable scientific figures in Origin from your data and plotting requirements.

## What it does

Provide your data and describe the figure you want, and the Agent creates it in Origin. If you have not specified a graph type, or the request clearly does not fit the data, it can suggest a suitable approach.

Axes, units, labels, symbols, colors, legends, and page layout are part of the same workflow. The Agent can inspect the rendered figure and refine it, or refresh an existing figure by updating its bound data. Delivery includes an editable Origin project and figure exports, with checks of the values, plot bindings, and saved result.

## How MCP and Skill work together

**MCP lets the Agent operate Origin:** import data, create and adjust figures, save projects, and export graphics.

**The Skill guides those operations with scientific plotting practice:** fonts and sizes, page dimensions, axes, colors, legends, and conventions such as italic variables and upright units.

The project includes an Agent Skill, MCP adaptations for this workflow, execution helpers, and plotting examples. See the [Skill](skills/origin-figures/SKILL.md), [workflow guide](skills/origin-figures/references/common-workflow.md), and [MCP changes](UPSTREAM_CHANGES.md).

## Examples

The following examples use synthetic data.

<table>
  <tr>
    <td align="center"><img src="assets/examples/xy.png" width="360" alt="Synthetic XY plot"></td>
    <td align="center"><img src="assets/examples/category.png" width="360" alt="Synthetic column plot"></td>
  </tr>
  <tr>
    <td align="center"><img src="assets/examples/histogram.png" width="360" alt="Synthetic histogram"></td>
    <td align="center"><img src="assets/examples/heatmap.png" width="360" alt="Synthetic heatmap"></td>
  </tr>
</table>

## Using the project

Prepare Windows, a licensed Origin installation, Python with the bundled MCP's dependencies, and an Agent that can use MCP and load the Skill. To use it, provide your data, the figure you want, and the desired output format.

Start with the [installation guide](INSTALLATION.md) and the [Skill entrypoint](skills/origin-figures/SKILL.md). Use this repository's bundled MCP source so the project's adaptations are included; its [technical documentation](mcp/README.md) is also included.

<sub>Developed and tested in a Codex-led workflow. Other MCP-compatible agents may also work; their setups have not been tested.</sub>

## Acknowledgements and license

The Origin MCP component builds on [Ge-Shun/origin-mcp](https://github.com/Ge-Shun/origin-mcp). Its [license](mcp/LICENSE) and [notices](mcp/NOTICE) are retained; adaptations are documented in [UPSTREAM_CHANGES.md](UPSTREAM_CHANGES.md).

Scientific visualization and graph-selection methods are informed by [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) and [Karthik's data visualization skill](https://github.com/skthewimp/karthik-data-visualization-skill), adapted here for the Origin workflow.

Figure formatting draws on the [Nature figure guide](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/) and [NIST guidance on symbols and units](https://physics.nist.gov/cuu/Units/checklist.html).

New project code and Skill content use the [MIT License](LICENSE). Original licenses and attribution are retained in [third-party notices](THIRD_PARTY_NOTICES.md) and the bundled source.
