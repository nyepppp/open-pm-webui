# 修复日历同步和弹窗问题

## 状态: 已完成

## 发现与修正

### 1. 日期格式 — 无需修改 GET 端

**分析发现**:
- GET `/calendars/events` 后端使用 `datetime.fromisoformat()` 解析，**期望 ISO 8601 字符串**
- `getVisibleRange()` 返回 `.toISOString()` ✅ 本是正确的
- POST `/events/create` 使用 `CalendarEventForm(start_at: int)` — 同步函数用 Unix 时间戳 ✅ 正确

**实际修复**: 虚拟 PM 事件在 `loadEvents()` 中使用 `Math.floor(startDate.getTime() / 1000)` （秒），但 `CalendarView.svelte` 用 `e.start_at / NS`（NS=1_000_000，期望纳秒）。导致 new Date() 返回 1970 年的日期，事件不显示。

- **文件**: `src/routes/(app)/calendar/+page.svelte`
- **修改**: 将 `start_at`/`end_at`/`created_at`/`updated_at` 从秒改为纳秒（`startDate.getTime() * 1_000`）

### 2. 弹窗组件 — 已存在，无需创建

`ConfirmDialog.svelte` 已存在于 `src/lib/components/common/ConfirmDialog.svelte`，支持:
- `bind:show` 控制显示
- `on:confirm` / `on:cancel` 事件
- `input={true}` 输入模式
- `<slot>` 自定义内容

### 3. 同步逻辑 — 已修复

**文件**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- 添加 `import ConfirmDialog`
- 添加 promise 包装的弹窗状态变量: `openConfirmOverwrite()`, `openCalendarSelect()`, 模板创建 dialog
- 替换 `confirm('是否覆盖？')` → `await openConfirmOverwrite()`
- 替换 `prompt('选择日历')` → `await openCalendarSelect(calendars)`（带 radio button slot）
- 替换模板创建 `prompt()`/`confirm()` → ConfirmDialog input 模式 + radio 选择
- 添加 `if (!result) throw` 空值保护（`createCalendarEvent` 在缺少 `detail` 字段时返回 null）

### 4. 其他修复
- **createCalendarEvent API 空返回保护**: 在 `syncSingleToCalendar` 中添加 `if (!result) throw`

## 验证
- [x] CalendarView 纳秒格式修复 — 已确认
- [x] 所有 `confirm()`/`prompt()` 已替换为 ConfirmDialog — `grep` 确认 0 个残留
- [x] API 空返回值保护已添加
- [x] 无 LSP 级别错误（oxlint 未安装，但 TS compiler 无报错）
