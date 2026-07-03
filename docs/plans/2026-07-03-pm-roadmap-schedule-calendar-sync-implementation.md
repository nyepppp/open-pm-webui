# PM Roadmap & Schedule → Calendar Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add unidirectional manual sync from PM workspace roadmap/schedule entries to the calendar, with idempotent upsert (create or update) based on `pm_entry_id`.

**Architecture:** Backend adds a new FastAPI endpoint that upserts a `CalendarEvent` with metadata linking it to a PM entry. Frontend adds a sync button per row in roadmap/schedule tables, which opens a calendar picker modal and calls the new endpoint.

**Tech Stack:** FastAPI, SQLAlchemy (async), SvelteKit 5, TypeScript, Tailwind CSS

---

## Task 1: Add `get_event_by_pm_entry_id` model method

**Files:**
- Modify: `backend/open_webui/models/calendar.py`

**Step 1: Write the model method**

Add to `CalendarEventTable` class:

```python
async def get_event_by_pm_entry_id(
    self, pm_entry_id: str, db: Optional[AsyncSession] = None
) -> Optional[CalendarEventModel]:
    """Find calendar event synced from a PM entry by pm_entry_id in meta."""
    from sqlalchemy import func
    async with get_async_db_context(db) as db:
        result = await db.execute(
            select(CalendarEvent)
            .filter(func.json_extract(CalendarEvent.meta, '$.pm_entry_id') == pm_entry_id)
            .filter(CalendarEvent.is_cancelled == False)
        )
        event = result.scalars().first()
        return await self._to_event_model(event, db=db) if event else None
```

**Step 2: Commit**

```bash
git add backend/open_webui/models/calendar.py
git commit -m "feat(calendar): add get_event_by_pm_entry_id model method"
```

---

## Task 2: Add `sync_entry_to_calendar` endpoint in PM router

**Files:**
- Modify: `backend/open_webui/routers/pm.py`
- Modify: `backend/open_webui/models/pm.py` (if PM entry lookup helper needed)

**Step 1: Add imports and form model**

In `backend/open_webui/routers/pm.py`, add:

```python
from open_webui.models.calendar import CalendarEventForm, CalendarEvents
from open_webui.utils.calendar import ns_from_date_str
from datetime import datetime
```

Add form model:

```python
class SyncToCalendarForm(BaseModel):
    calendar_id: str
```

**Step 2: Add the endpoint**

```python
@router.post('/entries/{entry_id}/sync-to-calendar')
async def sync_entry_to_calendar(
    entry_id: str,
    form_data: SyncToCalendarForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Sync a PM entry (roadmap/schedule) to a calendar event."""
    # 1. Validate PM entry
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=404, detail='Entry not found')
    if entry.module_type not in ('roadmap', 'schedule'):
        raise HTTPException(status_code=400, detail='Only roadmap/schedule entries can be synced')
    
    # 2. Validate entry has startDate
    data = entry.data or {}
    start_date_str = data.get('startDate')
    end_date_str = data.get('endDate')
    if not start_date_str:
        raise HTTPException(status_code=422, detail='Entry has no start date')
    
    # 3. Validate calendar access (reuse calendar router logic)
    from backend.open_webui.routers.calendar import _check_calendar_access
    try:
        await _check_calendar_access(form_data.calendar_id, user, 'write')
    except HTTPException:
        raise HTTPException(status_code=403, detail='Access denied to calendar')
    
    # 4. Convert dates to nanoseconds
    def date_str_to_ns(date_str: str) -> int:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return int(dt.timestamp() * 1000) * 1_000_000
    
    start_ns = date_str_to_ns(start_date_str)
    end_ns = date_str_to_ns(end_date_str) if end_date_str else None
    
    # 5. Check for existing event
    existing_event = await CalendarEvents.get_event_by_pm_entry_id(entry_id, db=db)
    
    # 6. Build meta
    meta = {
        'pm_entry_id': entry_id,
        'pm_module_type': entry.module_type,
        'pm_project_id': entry.project_id,
        'pm_sync_version': 1
    }
    
    # 7. Upsert
    if existing_event:
        from open_webui.models.calendar import CalendarEventUpdateForm
        updated = await CalendarEvents.update_event_by_id(
            existing_event.id,
            CalendarEventUpdateForm(
                calendar_id=form_data.calendar_id,
                title=entry.title,
                description=entry.content or '',
                start_at=start_ns,
                end_at=end_ns,
                all_day=True,
                meta=meta
            ),
            db=db
        )
        return {'status': True, 'action': 'updated', 'event_id': updated.id}
    else:
        new_event = await CalendarEvents.insert_new_event(
            user.id,
            CalendarEventForm(
                calendar_id=form_data.calendar_id,
                title=entry.title,
                description=entry.content or '',
                start_at=start_ns,
                end_at=end_ns,
                all_day=True,
                meta=meta
            ),
            db=db
        )
        return {'status': True, 'action': 'created', 'event_id': new_event.id}
```

**Step 3: Commit**

```bash
git add backend/open_webui/routers/pm.py
git commit -m "feat(pm): add sync_entry_to_calendar endpoint"
```

---

## Task 3: Add frontend API wrapper `calendarSync.ts`

**Files:**
- Create: `src/lib/apis/pm/calendarSync.ts`

**Step 1: Write the API wrapper**

```typescript
import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface SyncToCalendarResponse {
	status: boolean;
	action: 'created' | 'updated';
	event_id: string;
}

export const syncEntryToCalendar = async (
	token: string,
	entryId: string,
	calendarId: string
): Promise<SyncToCalendarResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/pm/entries/${entryId}/sync-to-calendar`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ calendar_id: calendarId })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
```

**Step 2: Commit**

```bash
git add src/lib/apis/pm/calendarSync.ts
git commit -m "feat(pm): add calendarSync API wrapper"
```

---

## Task 4: Create `PMSyncToCalendarModal.svelte` component

**Files:**
- Create: `src/lib/components/pm/PMSyncToCalendarModal.svelte`

**Step 1: Write the component**

```svelte
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { getCalendars } from '$lib/apis/calendar';
	import type { CalendarModel } from '$lib/apis/calendar';

	export let show = false;
	export let entryTitle = '';

	const dispatch = createEventDispatcher();

	let calendars: CalendarModel[] = [];
	let selectedCalendarId = '';
	let loading = false;
	let loaded = false;

	async function loadCalendars() {
		try {
			calendars = (await getCalendars(localStorage.token)) ?? [];
			const defaultCal = calendars.find((c) => c.is_default);
			selectedCalendarId = defaultCal?.id || calendars[0]?.id || '';
			loaded = true;
		} catch (err) {
			toast.error('加载日历失败');
			calendars = [];
		}
	}

	function handleSelect(calendarId: string) {
		selectedCalendarId = calendarId;
	}

	function handleSync() {
		if (!selectedCalendarId) {
			toast.error('请选择日历');
			return;
		}
		dispatch('sync', { calendarId: selectedCalendarId });
	}

	$: if (show && !loaded) {
		loadCalendars();
	}
</script>

<Modal size="sm" bind:show>
	<div class="flex flex-col">
		<div class="px-5 pt-4 pb-2">
			<h3 class="text-base font-medium">同步到日历</h3>
			<p class="text-sm text-gray-500 mt-1 truncate">{entryTitle}</p>
		</div>

		<div class="px-5 py-2">
			{#if !loaded}
				<div class="flex justify-center py-4">
					<Spinner className="size-5" />
				</div>
			{:else if calendars.length === 0}
				<div class="text-center py-4 text-sm text-gray-500">
					<p>您还没有日历</p>
					<p class="text-xs mt-1">请先创建日历后再同步</p>
				</div>
			{:else}
				<div class="space-y-1">
					{#each calendars as calendar (calendar.id)}
						<button
							class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition {selectedCalendarId === calendar.id ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' : 'hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent'}"
							on:click={() => handleSelect(calendar.id)}
						>
							<div
								class="w-3 h-3 rounded-full shrink-0"
								style="background-color: {calendar.color || '#3b82f6'}"
							/>
							<span class="text-sm flex-1 truncate">{calendar.name}</span>
							{#if calendar.is_default}
								<span class="text-xs text-gray-400">默认</span>
							{/if}
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<div class="flex items-center justify-end gap-2 px-5 pb-4 pt-2">
			<button
				class="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 transition"
				on:click={() => (show = false)}
			>
				取消
			</button>
			<button
				class="px-4 py-1.5 text-sm bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex items-center gap-2 {loading || !selectedCalendarId ? 'opacity-50 cursor-not-allowed' : ''}"
				on:click={handleSync}
				disabled={loading || !selectedCalendarId}
			>
				{#if loading}
					<Spinner className="size-4" />
				{/if}
				同步
			</button>
		</div>
	</div>
</Modal>
```

**Step 2: Commit**

```bash
git add src/lib/components/pm/PMSyncToCalendarModal.svelte
git commit -m "feat(pm): add PMSyncToCalendarModal component"
```

---

## Task 5: Add schedule module to PM workspace

**Files:**
- Modify: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**Step 1: Add schedule to moduleConfig**

In the `moduleConfig` object, add:

```typescript
schedule: { name: '项目排期', editorType: 'table', tableColumns: [
    { key: 'title', label: '任务名' },
    { key: 'taskStatus', label: '状态', width: 'w-20' },
    { key: 'startDate', label: '开始', width: 'w-24' },
    { key: 'endDate', label: '结束', width: 'w-24' },
    { key: 'owner', label: '负责人', width: 'w-24' },
    { key: 'priority', label: '优先级', width: 'w-16' },
    { key: 'updatedAt', label: '更新', width: 'w-24' }
]},
```

**Step 2: Add schedule-specific form fields**

Add state variables:

```typescript
let newTaskStatus = $state<'planned' | 'in_progress' | 'completed' | 'delayed'>('planned');
let newOwner = $state('');
let newTaskDescription = $state('');
```

Add to `handleCreate`:

```typescript
} else if (moduleType === 'schedule') {
    data.data = { taskStatus: newTaskStatus, startDate: newStartDate, endDate: newEndDate, owner: newOwner };
    data.content = newTaskDescription || undefined;
```

Add to `resetForm`:

```typescript
newTaskStatus = 'planned'; newOwner = ''; newTaskDescription = '';
```

**Step 3: Commit**

```bash
git add src/routes/(app)/pm/[projectId]/[module]/+page.svelte
git commit -m "feat(pm): add schedule module with table view and form"
```

---

## Task 6: Add sync button to roadmap and schedule table rows

**Files:**
- Modify: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**Step 1: Import and state**

Add imports:

```typescript
import PMSyncToCalendarModal from '$lib/components/pm/PMSyncToCalendarModal.svelte';
import { syncEntryToCalendar } from '$lib/apis/pm/calendarSync';
```

Add state:

```typescript
let showSyncModal = $state(false);
let syncEntryId = $state('');
let syncEntryTitle = $state('');
let syncingEntryId = $state<string | null>(null);
```

**Step 2: Add sync handler**

```typescript
function openSyncModal(entry: any) {
    syncEntryId = entry.id;
    syncEntryTitle = entry.title;
    showSyncModal = true;
}

async function handleSyncToCalendar(calendarId: string) {
    if (!syncEntryId) return;
    syncingEntryId = syncEntryId;
    try {
        const token = localStorage.token || '';
        const result = await syncEntryToCalendar(token, syncEntryId, calendarId);
        if (result.status) {
            const actionText = result.action === 'created' ? '创建' : '更新';
            toast.success(`已${actionText}日历事件`);
            // Mark as synced in local state
            entries = entries.map(e => e.id === syncEntryId ? { ...e, data: { ...e.data, calendarEventId: result.event_id } } : e);
        }
    } catch (e: any) {
        toast.error(e.message || '同步失败');
    } finally {
        syncingEntryId = null;
        showSyncModal = false;
    }
}
```

**Step 3: Add sync button in table row actions**

In the table row actions column (near edit/delete buttons), add:

```svelte
{#if (moduleType === 'roadmap' || moduleType === 'schedule') && getEntryData(entry, 'startDate')}
    <button
        class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
        title={getEntryData(entry, 'calendarEventId') ? '已同步（点击更新）' : '同步到日历'}
        onclick={() => openSyncModal(entry)}
    >
        <svg class="size-3.5 {getEntryData(entry, 'calendarEventId') ? 'text-green-500' : 'text-gray-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
        </svg>
    </button>
{/if}
```

**Step 4: Add modal to template**

```svelte
<PMSyncToCalendarModal
    bind:show={showSyncModal}
    entryTitle={syncEntryTitle}
    on:sync={(e) => handleSyncToCalendar(e.detail.calendarId)}
/>
```

**Step 5: Commit**

```bash
git add src/routes/(app)/pm/[projectId]/[module]/+page.svelte
git commit -m "feat(pm): add sync-to-calendar button for roadmap and schedule modules"
```

---

## Task 7: Add task status mapping and display

**Files:**
- Modify: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**Step 1: Add task status map**

Add after `sourceMap`:

```typescript
const taskStatusMap: Record<string, { l: string; c: string }> = {
    planned: { l: '计划中', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' },
    in_progress: { l: '进行中', c: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
    completed: { l: '已完成', c: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
    delayed: { l: '延期', c: 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400' }
};
```

**Step 2: Add display in table cell**

In the table cell rendering section, add:

```svelte
{:else if col.key === 'taskStatus'}
    {@const ts = getEntryData(entry, 'taskStatus')}
    <span class="px-1.5 py-0.5 rounded text-xs {taskStatusMap[ts]?.c || INACTIVE}">{taskStatusMap[ts]?.l || ts || '-'}</span>
```

**Step 3: Commit**

```bash
git add src/routes/(app)/pm/[projectId]/[module]/+page.svelte
git commit -m "feat(pm): add task status display for schedule module"
```

---

## Task 8: Backend unit tests

**Files:**
- Create: `backend/tests/test_pm_calendar_sync.py`

**Step 1: Write tests**

```python
import pytest
from datetime import datetime

@pytest.mark.asyncio
async def test_sync_creates_event_when_not_exists(client, db, test_user, test_project):
    """Syncing a new entry should create a calendar event."""
    # Arrange: create a roadmap entry
    entry = await create_test_entry(db, test_project.id, 'roadmap', {
        'startDate': '2026-07-01',
        'endDate': '2026-07-15'
    })
    calendar = await create_test_calendar(db, test_user.id)
    
    # Act
    response = await client.post(
        f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
        json={'calendar_id': calendar.id}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['status'] is True
    assert data['action'] == 'created'
    assert data['event_id'] is not None


@pytest.mark.asyncio
async def test_sync_updates_event_when_already_synced(client, db, test_user, test_project):
    """Re-syncing should update the existing event, not create a duplicate."""
    # Arrange
    entry = await create_test_entry(db, test_project.id, 'roadmap', {
        'startDate': '2026-07-01'
    })
    calendar = await create_test_calendar(db, test_user.id)
    
    # First sync
    await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                      json={'calendar_id': calendar.id})
    
    # Act: second sync
    response = await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                                  json={'calendar_id': calendar.id})
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['action'] == 'updated'


@pytest.mark.asyncio
async def test_sync_rejects_entry_without_start_date(client, db, test_user, test_project):
    """Should return 422 if entry has no startDate."""
    entry = await create_test_entry(db, test_project.id, 'roadmap', {})
    calendar = await create_test_calendar(db, test_user.id)
    
    response = await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                                  json={'calendar_id': calendar.id})
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_sync_rejects_non_roadmap_schedule_modules(client, db, test_user, test_project):
    """Only roadmap/schedule can be synced."""
    entry = await create_test_entry(db, test_project.id, 'requirement', {
        'startDate': '2026-07-01'
    })
    calendar = await create_test_calendar(db, test_user.id)
    
    response = await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                                  json={'calendar_id': calendar.id})
    
    assert response.status_code == 400
```

**Step 2: Commit**

```bash
git add backend/tests/test_pm_calendar_sync.py
git commit -m "test(pm): add backend unit tests for calendar sync"
```

---

## Task 9: Manual QA checklist

**Files:**
- None (manual testing)

**Steps:**

1. **Create a project** → `/pm` → New Project
2. **Navigate to roadmap module** → `/pm/{projectId}/roadmap`
3. **Create a roadmap entry** with title, startDate, endDate
4. **Verify sync button appears** in the row actions
5. **Click sync button** → modal opens with calendar list
6. **Select a calendar** → click "同步"
7. **Verify toast** says "已创建日历事件"
8. **Navigate to calendar** → `/calendar`
9. **Verify event appears** with correct title, dates, all-day flag
10. **Re-sync the same entry** → toast says "已更新日历事件"
11. **Verify no duplicate** in calendar
12. **Repeat for schedule module** → `/pm/{projectId}/schedule`
13. **Create schedule entry** with startDate
14. **Sync to calendar** → verify event appears
15. **Create entry without startDate** → verify sync button is hidden

**Commit:**

```bash
git commit --allow-empty -m "qa(pm): manual QA passed for calendar sync"
```

---

## Task 10: Update documentation

**Files:**
- Modify: `docs/pm-workspace.md`

**Step 1: Add sync section**

Add to `docs/pm-workspace.md`:

```markdown
## Calendar Sync

Roadmap and schedule entries can be synced to the calendar as events.

### How to sync

1. Open a project and navigate to **Roadmap** or **Schedule** module
2. Create an entry with a **Start Date**
3. Click the calendar icon (📅) in the row actions
4. Select a target calendar from the modal
5. Click **同步**

### Sync behavior

- **Create:** First sync creates a new calendar event
- **Update:** Re-syncing updates the existing event (no duplicates)
- **All-day:** Synced events are created as all-day events
- **Metadata:** Events include `pm_entry_id` and `pm_module_type` in meta for tracking

### Requirements

- Entry must have a `startDate`
- User must have **write** permission on the target calendar
- Calendar feature must be enabled (`ENABLE_CALENDAR`)
```

**Step 2: Commit**

```bash
git add docs/pm-workspace.md
git commit -m "docs(pm): add calendar sync documentation"
```

---

## Summary

| Task | File(s) | Description |
|------|---------|-------------|
| 1 | `backend/open_webui/models/calendar.py` | Add `get_event_by_pm_entry_id` model method |
| 2 | `backend/open_webui/routers/pm.py` | Add `sync_entry_to_calendar` endpoint |
| 3 | `src/lib/apis/pm/calendarSync.ts` | Add frontend API wrapper |
| 4 | `src/lib/components/pm/PMSyncToCalendarModal.svelte` | Create calendar picker modal |
| 5 | `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | Add schedule module to PM workspace |
| 6 | `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | Add sync button to roadmap/schedule rows |
| 7 | `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | Add task status display |
| 8 | `backend/tests/test_pm_calendar_sync.py` | Add backend unit tests |
| 9 | Manual | QA checklist |
| 10 | `docs/pm-workspace.md` | Update documentation |

**Estimated total time:** 4-6 hours
**Dependencies:** None (all files are new or additive)
**Risk:** Low (additive feature, no breaking changes)
