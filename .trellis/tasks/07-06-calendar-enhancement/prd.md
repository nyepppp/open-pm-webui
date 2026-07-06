# 日历功能增强：版本信息、模块来源、同步弹窗优化

## Goal

增强日历页面中 PM events 的信息展示，并优化同步弹窗的用户体验。

## Requirements

### REQ-1: 在日历事件中展示版本信息

**描述**: 在日历视图中展示 PM events 的版本号信息。

**实现位置**: `src/routes/(app)/calendar/+page.svelte`

**具体需求**:
- 获取 PM entry 的 `versionId` 或 `currentVersionNumber`
- 通过 `versionList` store 解析版本号
- 在 `CalendarEventChip` 或 tooltip 中展示版本信息
- 格式：`[项目名] 条目标题 (v1.0)`

### REQ-2: 在日历事件中展示模块来源信息

**描述**: 在日历视图中展示 PM events 的模块来源（roadmap/schedule）。

**实现位置**: `src/routes/(app)/calendar/+page.svelte` 和 `src/lib/components/calendar/CalendarEventChip.svelte`

**具体需求**:
- 在 event 的 `meta` 中已包含 `module_type`（roadmap/schedule）
- 在 `CalendarEventChip` 中展示模块来源标签
- 使用不同颜色区分：roadmap（紫色）、schedule（蓝色）
- 格式：标签形式展示在标题前或旁边

### REQ-3: 同步弹窗下拉功能新增日程选项

**描述**: 在同步弹窗中新增"创建新日程"选项。

**实现位置**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**具体需求**:
- 在日历选择弹窗中新增"创建新日程"选项
- 点击后允许用户输入新日程名称
- 创建新日程后自动同步到该日程
- 保持现有选择已有日历的功能不变

## Acceptance Criteria

- [ ] 日历中的 PM events 展示版本号信息
- [ ] 日历中的 PM events 展示模块来源标签（roadmap/schedule）
- [ ] 同步弹窗支持创建新日程
- [ ] 创建新日程后自动完成同步
- [ ] 所有现有功能保持正常

## Out of Scope

- 不修改后端 API
- 不修改日历核心渲染逻辑
- 不添加新模块类型

## Notes

- 版本号解析逻辑参考 `+page.svelte` 中的 `versionOptions` 和 `getEntryData`
- 模块来源颜色：roadmap `#8b5cf6`，schedule `#3b82f6`
- 同步弹窗现有逻辑：`openCalendarSelect` 函数
