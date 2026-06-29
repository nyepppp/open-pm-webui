# Research: PM 工作台重构 — 技术选型与依赖调研

**Feature**: PM 工作台重构 — 模块化布局与差异化编辑器
**Date**: 2026-06-28
**Status**: In Progress

---

## Research Tasks

### R001: 富文本编辑器选型

**Question**: Open WebUI 是否已集成富文本编辑器？是否可复用？

**Findings**:
- Open WebUI 使用 Markdown 渲染聊天消息，但未发现完整的富文本编辑器组件
- 聊天输入框使用简单的 textarea，支持 Markdown 语法
- 建议：引入 TipTap 或 Quill 作为富文本编辑器，与 Open WebUI 的 Tailwind CSS 样式兼容

**Decision**: 引入 TipTap（ProseMirror 底层，Svelte 兼容性好）

---

### R002: 思维导图库选型

**Question**: Open WebUI 依赖中是否已有思维导图相关库？

**Findings**:
- 检查 package.json：未发现 D3.js、Cytoscape.js 等思维导图相关库
- Open WebUI 组件库中没有树形图、层级图、流程图组件
- 推荐引入 @xyflow/svelte（Svelte 原生，支持拖拽/缩放/自定义节点）

**Decision**: 引入 @xyflow/svelte（Svelte 原生，MIT 协议）

---

### R003: Open WebUI 组件复用

**Question**: 哪些 UI 组件可直接复用？

**Findings**:
- 按钮、表单输入框、下拉框、弹窗等基础组件可复用
- 表格组件可复用（参数清单、测试用例等模块需要）
- 侧边栏导航组件需自定义（现有侧边栏为聊天列表，不适用于 PM 模块分类）

**Decision**: 复用基础 UI 组件，自定义 PM 专用侧边栏和编辑器

---

### R004: Agent 框架扩展

**Question**: Open WebUI 的 Agent 框架如何扩展？

**Findings**:
- Open WebUI 支持自定义 Functions/Tools
- Agent 可通过 API 调用外部服务
- 建议：将 Agent 分析封装为 Open WebUI Function，用户触发时调用

**Decision**: 封装为 Open WebUI Function，支持手动和自动触发

---

### R005: 版本存储策略

**Question**: Drizzle ORM 是否支持写时复制（Copy-on-Write）？

**Findings**:
- Drizzle ORM 本身不支持 Copy-on-Write，但可通过应用层实现
- 建议：版本表存储变更摘要，实际数据通过 JSON diff 存储增量
- 或使用数据库触发器实现自动版本记录

**Decision**: 应用层实现增量存储，版本表记录变更摘要和 diff

---

## 技术选型总结

| 技术领域 | 选型 | 理由 |
|----------|------|------|
| 富文本编辑器 | TipTap | Svelte 兼容、可扩展、Markdown 支持 |
| 思维导图 | @xyflow/svelte | Svelte 原生、MIT 协议、社区活跃 |
| 表单验证 | zod | TypeScript 原生、与 Open WebUI 一致 |
| 状态管理 | Svelte stores | 与 Open WebUI 一致 |
| 版本控制 | 应用层增量存储 | Drizzle 不支持 CoW，应用层实现更灵活 |
| Agent | Open WebUI Function | 与基座集成，用户可配置 |

---

## 待解决问题

- [ ] 确认 TipTap 与 Open WebUI Tailwind 样式的兼容性
- [ ] 确认 @xyflow/svelte 在 SvelteKit 中的性能表现
- [ ] 调研 Open WebUI Function 的详细实现方式
