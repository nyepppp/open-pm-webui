# 日历同步优化：自动选择、时间拦截、roadmap时间展示

## Goal

优化日历同步功能，修复同步弹窗体验问题，并增强 roadmap 表格的时间维度展示。

## Requirements

### REQ-1: 创建日程后自动选择并导入

**描述**: 在同步弹窗中创建新日程后，应自动选择该日程并完成同步。

**当前问题**: 创建新日程后需要手动选择，用户体验不佳。

**实现位置**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**修复方案**:
- 创建新日程成功后，自动将 `selectedCalendarId` 设置为新日程的 ID
- 自动触发同步流程

### REQ-2: 缺少时间维度的条目应拦截同步

**描述**: 如果 PM entry 没有设置 `startDate`（开始日期），应阻止同步并提示用户。

**当前问题**: `syncSingleToCalendar` 函数虽然有检查，但 toast 提示后函数继续执行。

**实现位置**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**修复方案**:
- 在 `syncSingleToCalendar` 函数开头严格检查 `startDate`
- 如果没有设置，显示错误提示并直接返回，不继续执行

### REQ-3: roadmap 表格展示时间维度信息

**描述**: 在 roadmap 表格中展示每个条目的时间维度信息（开始日期、结束日期）。

**当前问题**: 表格中没有展示时间信息。

**实现位置**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**修复方案**:
- 在表格列中添加时间维度展示
- 格式：`开始日期 - 结束日期` 或仅 `开始日期`
- 使用日期格式化显示

## Acceptance Criteria

- [ ] 创建新日程后自动选择并完成同步
- [ ] 缺少开始日期的条目无法同步，并显示友好提示
- [ ] roadmap 表格展示每个条目的时间维度信息
- [ ] 所有现有功能保持正常

## Out of Scope

- 不修改后端 API
- 不添加新的模块类型
