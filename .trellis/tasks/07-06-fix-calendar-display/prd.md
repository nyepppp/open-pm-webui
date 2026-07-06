# 日历数据显示异常修复

## Goal

修复日历页面中 PM (Project Management) 相关日程事件无法正确显示的问题，以及 roadmap/schedule 模块同步按钮的状态异常。

## Background

用户在日历页面选择了 "Personal" 日历，但日期格子（如 "67"）没有展示对应的日程。通过浏览器控制台日志可以看到 `[Calendar] Entry data: Object` 有 27 条记录，说明数据已经获取到，但前端没有正确渲染。

## Requirements

### REQ-1: 修复 PM events 时间戳单位错误

**问题描述**: 在 `src/routes/(app)/calendar/+page.svelte` 中，PM entries（roadmap/schedule）被转换为 `CalendarEventModel` 时，`start_at` 和 `end_at` 的时间戳单位错误。

**根因分析**:
- 系统约定 `CalendarEventModel.start_at/end_at` 使用**纳秒**（nanoseconds）为单位
- 正常的 calendar events 从 API 返回时已经是纳秒（×1,000,000）
- 但 PM events 在转换时错误地乘以了 `1_000`（得到微秒），导致时间戳比正确值小了 1000 倍
- `CalendarView.svelte` 中使用 `e.start_at / 1_000_000` 转换为毫秒时，PM events 的时间戳被错误计算，无法匹配到正确的日期

**修复位置**: `src/routes/(app)/calendar/+page.svelte` 第126-127行

**修复方案**: 将 `* 1_000` 改为 `* 1_000_000`

### REQ-2: 检查并修复 roadmap 同步按钮状态判断

**问题描述**: 在 `/pm/{projectId}/roadmap` 页面，同步按钮点击后状态可能未正确更新。

**根因分析**:
- `isSynced` 判断同时检查 `entry.data?.calendarEventId` 和 `entry.metadata?.calendarEventId`
- 但 `syncSingleToCalendar` 函数只更新 `entry.data.calendarEventId`
- 如果 `entry.metadata` 中有旧的 `calendarEventId` 而 `entry.data` 中没有，会导致状态判断不一致
- 需要确保 `loadEntries()` 后数据正确刷新，且状态判断逻辑一致

**修复位置**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 第1692行及附近

## Acceptance Criteria

- [ ] 修复后，日历页面能正确显示 PM roadmap/schedule entries 对应的日程事件
- [ ] 日期格子中能看到对应日期的 PM events（带有 `[项目名] 条目标题` 格式）
- [ ] roadmap/schedule 页面的同步按钮状态（已同步/未同步）判断正确
- [ ] 同步按钮点击后能正确更新状态并显示成功提示

## Out of Scope

- 不修改后端 API
- 不修改日历组件的核心渲染逻辑
- 不添加新功能

## Notes

- 时间戳单位约定：
  - JavaScript `Date.getTime()` 返回**毫秒**（ms）
  - 系统内部 `CalendarEventModel.start_at/end_at` 使用**纳秒**（ns）
  - 转换公式：`ns = ms * 1_000_000`
- 相关文件：
  - `src/routes/(app)/calendar/+page.svelte` — PM events 转换逻辑
  - `src/lib/components/calendar/CalendarView.svelte` — 日历渲染逻辑
  - `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` — 同步按钮逻辑
