# PM Roadmap & Schedule → Calendar Sync Design

**Date:** 2026-07-03
**Issue:** [#3](https://github.com/nyepppp/open-pm-webui/issues/3) - 产品路线图和项目排期的同步到日程功能无效
**Status:** Design Approved, Pending Implementation
**Scope:** Unidirectional manual sync (roadmap + schedule modules → calendar)

---

## 1. Problem

The PM workspace has roadmap and schedule modules for project planning, but there is no way to sync PM entries to the calendar. Users must manually re-enter the same time-range data into the calendar app, which is error-prone and wastes time.

## 2. Goals

1. **Unidirectional manual sync** — PM entries flow one-way to calendar; user clicks a button to trigger.
2. **Per-entry sync** — Each row in the roadmap/schedule table has its own "sync to calendar" button.
3. **Default + user-selectable calendar** — Pre-select the user's default calendar, allow override.
4. **Idempotent** — Re-syncing the same entry updates the existing calendar event instead of creating duplicates.
5. **Cover both roadmap and schedule modules** — Add schedule module (currently missing) and sync both.

## 3. Non-Goals (YAGNI)

- Batch sync (multi-select + bulk action)
- Automatic / scheduled sync
- Bi-directional sync (calendar changes back to PM)
- Cascade delete (deleting PM entry removes calendar event)
- Auto-update (PM entry edits auto-push to calendar)
- Sync of modules other than roadmap/schedule

## 4. Architecture

### 4.1 Backend (FastAPI)

**New endpoint:** `POST /api/v1/pm/entries/{entry_id}/sync-to-calendar`

**Request body:**
```json
{
  "calendar_id": "uuid-string"
}
```

**Response:**
```json
{
  "status": true,
  "action": "created" | "updated",
  "event_id": "uuid-string"
}
```

**New model method** in `backend/open_webui/models/calendar.py`:
- `get_event_by_pm_entry_id(pm_entry_id: str, db) -> Optional[CalendarEventModel]`
  - SQL: `SELECT * FROM calendar_event WHERE json_extract(meta, '$.pm_entry_id') = :pm_entry_id`

**Flow:**
1. Validate PM entry exists and `module_type in ('roadmap', 'schedule')`
2. Validate entry has `startDate` in `data`
3. Validate user has `write` permission on target calendar (reuse `_check_calendar_access` from `routers/calendar.py`)
4. Look up existing event by `meta.pm_entry_id`
5. If exists → `update_event_by_id`
6. If not → `insert_new_event`
7. Return action + event_id

### 4.2 Frontend (SvelteKit)

**New file:** `src/lib/apis/pm/calendarSync.ts`
- `syncEntryToCalendar(token, entryId, calendarId): Promise<{status, action, event_id}>`

**New file:** `src/lib/components/pm/PMSyncToCalendarModal.svelte`
- Calendar picker dialog (reuses `Modal` component)
- Loads user's calendars via `getCalendars`
- Pre-selects `is_default === true` calendar
- Radio-style list with color swatch + name + "Default" badge
- Empty state: "您还没有日历，请先创建"
- Footer: Cancel / Sync buttons

**Modified:** `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- Add "sync to calendar" icon button in the actions column
- Only render when `entry.data?.startDate` is present
- Show different icon (outlined vs filled) based on `entry.data?.calendarEventId` (cached state)

**Modified:** `src/lib/apis/pm/types.ts`
- Add `taskStatus`, `owner`, `description` to schedule entry data type

### 4.3 Data Flow

```
[User clicks "Sync to Calendar" icon on row]
        |
        v
[PMSyncToCalendarModal opens, loads calendars]
        |
        v
[User selects calendar, clicks "Sync"]
        |
        v
[syncEntryToCalendar() → POST /api/v1/pm/entries/{id}/sync-to-calendar]
        |
        v
[Backend: validate entry → validate permission → upsert event]
        |
        v
[Return { action: 'created' | 'updated', event_id }]
        |
        v
[Update local state: entry.data.calendarEventId = event_id]
        |
        v
[Toast: "已创建日历事件" or "已更新日历事件"]
```

## 5. Data Model

### 5.1 Schedule Module (new)

| Field | Type | Description |
|-------|------|-------------|
| title | string | Task name |
| taskStatus | enum | `planned` \| `in_progress` \| `completed` \| `delayed` |
| startDate | string (YYYY-MM-DD) | Start date |
| endDate | string (YYYY-MM-DD) | End date |
| owner | string | Task owner |
| priority | enum | `p0` \| `p1` \| `p2` \| `p3` |
| description | string | Task description (content) |

### 5.2 Calendar Event (existing schema, new meta fields)

```json
{
  "calendar_id": "uuid",
  "title": "PM entry title",
  "description": "PM entry content/description",
  "start_at": <startDate * 1_000_000 ns>,
  "end_at": <endDate * 1_000_000 ns>,
  "all_day": true,
  "meta": {
    "pm_entry_id": "PM entry UUID",
    "pm_module_type": "roadmap" | "schedule",
    "pm_project_id": "PM project UUID",
    "pm_sync_version": 1
  }
}
```

## 6. UI Specification

### 6.1 Sync Button (in table row)

- **Location:** actions column, between Edit and Delete buttons
- **Icon:** calendar icon (Heroicons: `calendar`)
- **State — Not synced:** outlined, gray (`text-gray-400`)
- **State — Synced:** filled, green (`text-green-500`)
- **Tooltip:** "同步到日历" (not synced) / "已同步（点击更新）" (synced)
- **Visibility:** only when `entry.data?.startDate` is present

### 6.2 PMSyncToCalendarModal

- **Size:** `sm` (matches `CreateCalendarModal` pattern)
- **Title:** "同步到日历"
- **Body:**
  - Radio list of user's calendars
  - Each item: color swatch (12px) + name + "默认" badge (if `is_default`)
  - Selected state: blue background tint
  - Empty state: centered text + "去创建日历" link
- **Footer:**
  - Cancel button (gray, outline)
  - Sync button (black, primary)
  - Sync button disabled while loading
- **Error states:**
  - No calendars → show "请先创建日历" message, disable Sync
  - No write permission on selected calendar → "无写入权限" message

## 7. Error Handling

| Error | HTTP | Frontend behavior |
|-------|------|-------------------|
| Entry not found | 404 | Toast error, close modal |
| Entry has no startDate | 422 | Toast error: "请先设置开始日期" |
| Module not roadmap/schedule | 400 | Toast error: "该模块不支持同步" |
| Calendar not found | 404 | Toast error: "日历不存在" |
| No write permission on calendar | 403 | Toast error: "无写入权限" |
| User has no calendars | (frontend) | Show empty state, no API call |
| Network error | (fetch) | Toast error, modal stays open |

## 8. Security

- **Auth:** Uses existing `get_verified_user` dependency
- **Authorization:** User must own PM entry's project (or be admin) AND have `write` on target calendar
- **Cross-user isolation:** PM entry lookup verifies owner; calendar access reuses `_check_calendar_access`
- **No SQL injection:** All queries use SQLAlchemy ORM with parameterized bindings

## 9. Testing Strategy

### 9.1 Unit Tests (`backend/tests/test_pm_calendar_sync.py`)

- `test_sync_creates_event_when_not_exists`
- `test_sync_updates_event_when_already_synced`
- `test_sync_rejects_entry_without_start_date`
- `test_sync_rejects_non_roadmap_schedule_modules`
- `test_sync_rejects_calendar_without_write_permission`
- `test_sync_returns_correct_action_type`
- `test_get_event_by_pm_entry_id_returns_none_for_unsynced`
- `test_get_event_by_pm_entry_id_finds_synced_event`

### 9.2 Integration / E2E Tests

- Frontend: roadmap entry → click sync → modal opens → select calendar → click sync → toast appears → icon turns green
- Re-sync same entry → modal opens → click sync → toast says "已更新" → no duplicate event
- Sync schedule entry → same flow as roadmap
- Sync entry without startDate → button is hidden, no API call

### 9.3 Manual QA Checklist

- [ ] Create roadmap entry with startDate/endDate, sync to default calendar → event appears
- [ ] Re-sync same entry → no duplicate, event updated
- [ ] Sync to a non-default calendar → event appears in that calendar only
- [ ] Sync without write permission on calendar → 403 error
- [ ] Sync entry without startDate → button hidden
- [ ] Sync from schedule module → event appears
- [ ] Delete PM entry → calendar event remains (YAGNI: no cascade)

## 10. Implementation Phases

1. **Backend foundation** — add `get_event_by_pm_entry_id` model method
2. **Backend endpoint** — add `sync_entry_to_calendar` route + form model
3. **Frontend API** — add `calendarSync.ts`
4. **Frontend modal** — add `PMSyncToCalendarModal.svelte`
5. **Frontend schedule module** — add `schedule` to `moduleConfig` with form + table view
6. **Frontend roadmap integration** — add sync button to roadmap module actions
7. **Frontend schedule integration** — add sync button to schedule module actions
8. **Tests** — backend unit tests + manual QA
9. **Docs** — update `docs/pm-workspace.md` with sync feature

## 11. Rollout

- No database migration required (uses existing `calendar_event.meta` JSON column)
- No new dependencies (uses existing libraries: SQLAlchemy, Pydantic, Svelte)
- Feature flag: rely on existing `ENABLE_CALENDAR` config — sync is unavailable if calendar is disabled
- No breaking changes to existing PM or calendar APIs

## 12. Open Questions

None. Design is approved and scope is locked.
