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


@pytest.mark.asyncio
async def test_sync_rejects_calendar_without_write_permission(client, db, test_user, test_project):
    """Should return 403 if user has no write permission on calendar."""
    entry = await create_test_entry(db, test_project.id, 'roadmap', {
        'startDate': '2026-07-01'
    })
    # Create calendar owned by another user
    other_user = await create_test_user(db)
    calendar = await create_test_calendar(db, other_user.id)
    
    response = await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                                  json={'calendar_id': calendar.id})
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_sync_returns_correct_action_type(client, db, test_user, test_project):
    """Should return 'created' on first sync and 'updated' on second."""
    entry = await create_test_entry(db, test_project.id, 'schedule', {
        'startDate': '2026-07-01',
        'endDate': '2026-07-15'
    })
    calendar = await create_test_calendar(db, test_user.id)
    
    # First sync
    response1 = await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                                   json={'calendar_id': calendar.id})
    assert response1.json()['action'] == 'created'
    
    # Second sync
    response2 = await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                                   json={'calendar_id': calendar.id})
    assert response2.json()['action'] == 'updated'


@pytest.mark.asyncio
async def test_get_event_by_pm_entry_id_returns_none_for_unsynced(db, test_user):
    """Should return None for entries that haven't been synced."""
    from open_webui.models.calendar import CalendarEvents
    
    result = await CalendarEvents.get_event_by_pm_entry_id('non-existent-id', db=db)
    assert result is None


@pytest.mark.asyncio
async def test_get_event_by_pm_entry_id_finds_synced_event(client, db, test_user, test_project):
    """Should find the event after syncing."""
    from open_webui.models.calendar import CalendarEvents
    
    entry = await create_test_entry(db, test_project.id, 'roadmap', {
        'startDate': '2026-07-01'
    })
    calendar = await create_test_calendar(db, test_user.id)
    
    # Sync
    await client.post(f'/api/v1/pm/entries/{entry.id}/sync-to-calendar',
                     json={'calendar_id': calendar.id})
    
    # Find
    result = await CalendarEvents.get_event_by_pm_entry_id(entry.id, db=db)
    assert result is not None
    assert result.title == entry.title
    assert result.meta['pm_entry_id'] == entry.id


# Helper functions

async def create_test_entry(db, project_id, module_type, data):
    """Create a test PM entry."""
    from open_webui.models.pm import PMEntries, PMEntryForm
    
    entry = await PMEntries.insert_new_entry(
        'test-user-id',
        PMEntryForm(
            project_id=project_id,
            module_type=module_type,
            title=f'Test {module_type} entry',
            data=data
        ),
        db=db
    )
    return entry


async def create_test_calendar(db, user_id):
    """Create a test calendar."""
    from open_webui.models.calendar import Calendars, CalendarForm
    
    calendar = await Calendars.insert_new_calendar(
        user_id,
        CalendarForm(name='Test Calendar', color='#3b82f6'),
        db=db
    )
    return calendar


async def create_test_user(db):
    """Create a test user."""
    from open_webui.models.users import Users, UserForm
    
    user = await Users.insert_new_user(
        UserForm(
            email='test@example.com',
            password='password123',
            name='Test User'
        ),
        db=db
    )
    return user
