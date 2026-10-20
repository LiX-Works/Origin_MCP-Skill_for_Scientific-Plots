# Origin MCP + Skill for Scientific Plots

[English](README.md) | **简体中文**

Origin 面向人工交互操作，AI Agent 很难直接驾驭。本项目提供 Agent 在 Origin 中绘制可编辑科研图所需的两部分：

| 组成 | 作用 |
|---|---|
| **MCP 服务** | 直接操作 Origin：导入数据、构建并设置图表样式、保存工程、导出图形 |
| **Skill** | 提供源自 Nature 图稿指南和 NIST 规范的绘图约定：字体字号、页面尺寸、坐标轴、单位、配色、图例 |

Agent 检查每次渲染结果并逐步调整，核对数值和数据绑定。交付的是可继续编辑的 Origin 工程（`.opju`），以及 PNG 或 PDF 导出图。

> [!NOTE]
> **Human-in-the-Loop.** 这个 Skill 承担重复性的科研事务，是辅助研究，而不是替代研究。问题、判断和结论留给人，每个结果使用前都要检查。

<img src="assets/overview.png" alt="数据和绘图要求交给 AI Agent；Skill 提供绘图规则，MCP 桥接让 Agent 在 Origin 中导入数据、创建图表、设置样式和坐标轴、保存并导出；Agent 检查实际画面后继续调整，最终交付可编辑的 Origin 工程和导出图。" width="1600">

## 工作方式

提供数据并描述所需图形。未指定图型或图型明显不适合数据时，Agent 会在绘图前提出替代方案。已有图表可通过更新绑定数据刷新。

仓库包含 [Skill](skills/origin-figures/SKILL.md)、附带的 [MCP 源码](mcp/README.zh.md)及本项目的[修改记录](UPSTREAM_CHANGES.md)、执行辅助工具和下方示例；完整流程见[工作流说明](skills/origin-figures/references/common-workflow.md)。

## 图形示例

以下为合成数据绘图示例。

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

## 开始使用

需要 Windows、已授权的 Origin 或 OriginPro、运行所附 MCP 的 Python，以及能够使用 MCP 并加载 Skill 的 Agent。按[安装指南](INSTALLATION.md)配置后，从 [Skill 入口](skills/origin-figures/SKILL.md)开始。请使用本仓库附带的 MCP 源码；上游安装包不含本项目的调整。

已在 Windows 与 OriginPro 2026 下检查，见[验证详情](VALIDATION.md)。在 Codex 中开发并测试；其他兼容 MCP 的 Agent 也可能适用，但尚未测试。

## 致谢与许可证

Origin MCP 部分基于 [Ge-Shun/origin-mcp](https://github.com/Ge-Shun/origin-mcp)。项目保留其[许可证](mcp/LICENSE)与[来源说明](mcp/NOTICE)，相关调整记录在 [UPSTREAM_CHANGES.md](UPSTREAM_CHANGES.md)。

科研可视化与选图方法参考了 [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) 和 [Karthik 的数据可视化 Skill](https://github.com/skthewimp/karthik-data-visualization-skill)，并针对 Origin 工作流进行了适配。

绘图格式参考 [Nature 图稿指南](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/)与 [NIST 符号和单位规范](https://physics.nist.gov/cuu/Units/checklist.html)。

本项目新增代码与 Skill 内容采用 [MIT 许可证](LICENSE)。原始许可证与作者归属保留在[第三方来源说明](THIRD_PARTY_NOTICES.md)及所附源码中。
