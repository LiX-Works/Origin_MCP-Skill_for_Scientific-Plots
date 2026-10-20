# Origin MCP + Skill for Scientific Plots

**English** | [简体中文](README.zh-CN.md)

Origin is built for interactive use, which makes it hard for an AI agent to drive. This project supplies the two pieces an agent needs to produce editable scientific figures in it:

| Component | Role |
|---|---|
| **MCP server** | Operates Origin directly: imports data, builds and styles graphs, saves projects, exports figures |
| **Skill** | Supplies plotting conventions from the Nature figure guide and NIST guidance: font sizes, page dimensions, axes, units, colours, legends |

The agent inspects each rendered figure, refines it, and checks values and data bindings. The result is an Origin project (`.opju`) that stays editable, with PNG or PDF exports.

> [!NOTE]
> **Human-in-the-Loop.** This Skill handles repetitive research tasks; it supports research rather than doing it. Keep questions, judgments, and conclusions with people, and check every result before use.

<img src="assets/overview.png" alt="Your data and figure request go to an AI agent. The Skill supplies plotting rules; the MCP bridge lets the agent import data, build the graph, set styles and axes, and save and export in Origin. The agent reviews the rendered figure and refines it, then delivers an editable Origin project and exports." width="1600">

## Workflow

Provide the data and a description of the figure. If the graph type is unspecified or clearly unsuited to the data, the agent proposes an alternative before plotting. Existing figures can be refreshed by updating their bound data.

The repository contains the [Skill](skills/origin-figures/SKILL.md), the bundled [MCP source](mcp/README.md) with this project's [adaptations](UPSTREAM_CHANGES.md), execution helpers, and the examples below. The [workflow guide](skills/origin-figures/references/common-workflow.md) documents the full process.

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

## Getting started

Requires Windows, a licensed Origin or OriginPro, Python for the bundled MCP server, and an agent that can use MCP and load a Skill. Follow the [installation guide](INSTALLATION.md), then start from the [Skill entry point](skills/origin-figures/SKILL.md). Use the bundled MCP source rather than the upstream package, which lacks this project's adaptations.

Checked on Windows with OriginPro 2026; see [validation details](VALIDATION.md). Built and tested with Codex; other MCP-compatible agents may also work but have not been tested.

## Acknowledgements and license

The Origin MCP component builds on [Ge-Shun/origin-mcp](https://github.com/Ge-Shun/origin-mcp). Its [license](mcp/LICENSE) and [notices](mcp/NOTICE) are retained; adaptations are documented in [UPSTREAM_CHANGES.md](UPSTREAM_CHANGES.md).

Scientific visualization and graph-selection methods are informed by [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) and [Karthik's data visualization skill](https://github.com/skthewimp/karthik-data-visualization-skill), adapted here for the Origin workflow.

Figure formatting draws on the [Nature figure guide](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/) and [NIST guidance on symbols and units](https://physics.nist.gov/cuu/Units/checklist.html).

New project code and Skill content use the [MIT License](LICENSE). Original licenses and attribution are retained in [third-party notices](THIRD_PARTY_NOTICES.md) and the bundled source.
