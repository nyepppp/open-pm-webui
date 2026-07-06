# PM引用功能：在聊天输入框中添加PM数据引用

## Goal

在聊天输入框（MessageInput.svelte）中提供 PM 数据引用能力，允许用户快速引用项目管理系统中的项目、模块或条目数据，将结构化 PM 数据注入到对话上下文中，增强 AI 助手对项目背景的理解。

## Background

- 项目已存在 PM 系统（Project Management），包含项目、模块、条目三级数据结构
- 已有 `PMDataSelector.svelte` 组件实现项目/模块/条目的选择面板
- MessageInput.svelte 已集成文件上传、工具选择、技能选择等集成菜单（IntegrationsMenu）
- 当前代码中已存在 `#` 命令的 suggestion handler 中有对 `type === 'pm'` 的处理逻辑（lines 1049-1067），说明 PM 引用概念已部分存在

## Requirements

### R1: PM 引用按钮
- 在 MessageInput.svelte 的 IntegrationsMenu 旁添加 PM 引用按钮
- 按钮使用项目/文件夹图标，与现有工具按钮风格一致
- 按钮仅在 PM Workbench 功能启用时显示（`showPMWorkbenchButton`）
- 点击按钮打开 PM 数据选择器

### R2: PM 数据选择器
- 复用或基于现有 `PMDataSelector.svelte` 组件
- 支持三级导航：项目 → 模块 → 条目
- 支持搜索过滤（按名称搜索项目、模块、条目）
- 支持面包屑导航和返回上级
- 选择条目后，将 PM 数据以引用形式插入到对话上下文

### R3: 引用插入逻辑
- 选中的 PM 数据以特殊格式插入到 prompt 中
- 引用格式应包含：项目名、模块名、条目标题、状态、优先级等关键信息
- 引用数据应作为 `files` 数组中的特殊类型项（`type: 'pm-entry'`）被传递
- 在消息发送时，PM 引用数据应被包含在消息内容中

### R4: 引用展示
- 已引用的 PM 数据应在输入框上方以标签/卡片形式展示
- 展示信息包括：条目标题、所属项目/模块
- 支持点击删除引用

### R5: 与现有系统集成
- 与现有的 `files` 数组系统兼容（PM 引用作为特殊文件项）
- 与现有的 suggestion 系统兼容（`#` 命令可触发 PM 选择）
- 与现有的消息发送流程兼容

## Acceptance Criteria

- [ ] AC1: 在聊天输入框的 IntegrationsMenu 旁可以看到 PM 引用按钮
- [ ] AC2: 点击 PM 引用按钮弹出 PM 数据选择器面板
- [ ] AC3: 可以在选择器中浏览项目 → 模块 → 条目三级结构
- [ ] AC4: 可以在选择器中搜索过滤项目/模块/条目
- [ ] AC5: 选择条目后，引用标签显示在输入框上方
- [ ] AC6: 发送消息时，PM 引用数据被正确包含在消息中
- [ ] AC7: 可以删除已添加的 PM 引用
- [ ] AC8: 使用 `#` 命令也可以触发 PM 数据选择

## Technical Notes

- 参考文件：`src/lib/components/chat/MessageInput.svelte`（主文件）
- 参考文件：`src/lib/components/pm/PMDataSelector.svelte`（选择器组件）
- 现有 PM 引用处理逻辑：MessageInput.svelte lines 1049-1067
- 按钮位置：IntegrationsMenu 旁（line 1710-1752 区域）
- 文件展示区域：lines 1355-1448

## Out of Scope

- PM 数据选择器的 UI 重新设计（复用现有组件）
- 后端 API 修改（使用现有 API）
- 消息展示端的 PM 引用渲染优化

## Open Questions

- Q1: PM 引用在消息中的具体格式是什么？（纯文本摘要 / 结构化数据 / 两者都有）
- Q2: 是否支持一次引用多个 PM 条目？
- Q3: PM 引用按钮的图标和文案确认
