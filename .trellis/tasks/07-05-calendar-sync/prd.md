# Calendar 日程未展示 Schedule/Roadmap 内容

## Goal

日历页面 (`/calendar`) 当前仅显示用户手动创建的日历事件，未展示从 PM 模块 schedule（项目排期）和 roadmap（产品路线图）同步过来的日程内容。需要让日历自动拉取并展示这些来源的事件。

## Context

- **当前实现**: `src/routes/(app)/calendar/+page.svelte` 通过 `getCalendarEvents()` API 获取事件，仅显示用户创建的 calendar event。
- **同步机制已存在**: 在 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 中已有 `syncSingleToCalendar()` 函数，可以将 schedule/roadmap 条目逐个同步到 calendar（通过 `createCalendarEvent` API），同步后会在 entry.data 中存储 `calendarEventId`。
- **问题**: 同步是手动逐条操作，日历页面没有主动从 PM 模块拉取 schedule/roadmap 数据并展示。

## Requirements

1. 日历页面在加载时，除了加载现有的 calendar events 外，还需要加载当前用户参与的所有项目的 schedule 和 roadmap 条目
2. Schedule 条目（含 startDate/endDate）应在日历上显示为事件
3. Roadmap 条目（含 startDate/endDate）应在日历上显示为事件
4. 这些 PM 来源的事件应有视觉区分（如不同颜色/标签），点击可跳转到对应 PM 项目
5. 保持现有的手动同步功能（`syncSingleToCalendar`）不受影响

## Acceptance Criteria

- [ ] 日历页面月视图/周视图/日视图中可见 schedule 和 roadmap 条目
- [ ] PM 来源事件有项目名称标签和颜色区分
- [ ] 点击 PM 事件可跳转到对应项目模块页面
- [ ] 现有手动同步功能不受影响
