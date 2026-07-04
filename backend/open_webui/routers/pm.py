import json
import logging
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from open_webui.internal.db import get_async_session
from open_webui.models.pm import (
    PMEntries,
    PMEntry,
    PMEntryForm,
    PMEntryModel,
    PMEntryUpdateForm,
    PMProjects,
    PMProjectForm,
    PMProjectModel,
    PMProjectUpdateForm,
    PMVersions,
    PMVersionForm,
    PMVersionModel,
    PMRelation,
    PMRelationModel,
)
from open_webui.utils.auth import get_verified_user
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AgentChatRequest(BaseModel):
    message: str
    project_id: str
    module_type: Optional[str] = None
    entry_id: Optional[str] = None
    context: Optional[dict] = None


class AgentSkillRequest(BaseModel):
    project_id: str
    module_type: Optional[str] = None
    entry_id: Optional[str] = None
    data: Optional[dict] = None


class FlowPreviewRequest(BaseModel):
    template_id: str
    source_entry_ids: list[str]
    project_id: str


class FlowExecuteRequest(BaseModel):
    template_id: str
    source_entry_ids: list[str]
    project_id: str
    confirmed: bool = False


class FlowTemplateCreateRequest(BaseModel):
    name: str
    description: str
    input_module: str
    output_module: str
    steps: list[dict]
    project_id: Optional[str] = None


log = logging.getLogger(__name__)

router = APIRouter()


############################
# Projects
############################


@router.get('/projects', response_model=list[PMProjectModel])
async def get_projects(
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await PMProjects.get_projects_by_user_id(user.id, db=db)


@router.post('/projects', response_model=PMProjectModel)
async def create_project(
    form_data: PMProjectForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await PMProjects.insert_new_project(user.id, form_data, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create project')
    return project


@router.get('/projects/{project_id}', response_model=PMProjectModel)
async def get_project(
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return project


@router.post('/projects/{project_id}', response_model=PMProjectModel)
async def update_project(
    project_id: str,
    form_data: PMProjectUpdateForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await PMProjects.update_project_by_id(project_id, form_data, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return project


@router.delete('/projects/{project_id}')
async def delete_project(
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    await PMProjects.delete_project_by_id(project_id, db=db)
    return True


############################
# Versions
############################


@router.get('/projects/{project_id}/versions', response_model=list[PMVersionModel])
async def get_versions(
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await PMVersions.get_versions_by_project_id(project_id, db=db)


@router.post('/projects/{project_id}/versions', response_model=PMVersionModel)
async def create_version(
    project_id: str,
    form_data: PMVersionForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    form_data.project_id = project_id
    version = await PMVersions.insert_new_version(form_data, user.id, db=db)
    if not version:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create version')
    return version


############################
# Entries
############################


@router.get('/projects/{project_id}/entries', response_model=list[PMEntryModel])
async def get_entries(
    project_id: str,
    module_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    # If no extra filters provided, use existing methods for backward compatibility
    if not any([module_type, status, priority, search]):
        entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    else:
        # Build query directly with SQLAlchemy for enhanced filtering
        query = select(PMEntry).where(PMEntry.project_id == project_id)
        if module_type:
            query = query.where(PMEntry.module_type == module_type)
        if status:
            query = query.where(PMEntry.status == status)
        if priority:
            query = query.where(PMEntry.priority == priority)
        if search:
            query = query.where(
                (PMEntry.title.ilike(f'%{search}%')) | (PMEntry.content.ilike(f'%{search}%'))
            )
        query = query.order_by(PMEntry.updated_at.desc())
        result = await db.execute(query)
        entries = result.scalars().all()
    # Enrich with version info
    from open_webui.models.pm import PMEntryVersions
    result = []
    for entry in entries:
        entry_model = PMEntryModel.model_validate(entry)
        latest_version = await PMEntryVersions.get_latest_version_by_entry_id(entry.id, db=db)
        if latest_version:
            entry_model.current_version_number = latest_version.version_number
            entry_model.branch_name = latest_version.branch_name
        result.append(entry_model)
    return result


@router.get('/projects/{project_id}/entries/search', response_model=list[PMEntryModel])
async def search_entries(
    project_id: str,
    q: str,  # search query
    module_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Full-text search across entries (title + content)."""
    query = select(PMEntry).where(
        PMEntry.project_id == project_id,
        (PMEntry.title.ilike(f'%{q}%') | PMEntry.content.ilike(f'%{q}%'))
    )
    if module_type:
        query = query.where(PMEntry.module_type == module_type)
    if status:
        query = query.where(PMEntry.status == status)
    if priority:
        query = query.where(PMEntry.priority == priority)
    query = query.order_by(PMEntry.updated_at.desc()).limit(limit)
    result = await db.execute(query)
    entries = [PMEntryModel.model_validate(e) for e in result.scalars().all()]
    # Enrich with version info (same pattern as get_entries)
    from open_webui.models.pm import PMEntryVersions
    enriched = []
    for entry_model in entries:
        latest_version = await PMEntryVersions.get_latest_version_by_entry_id(entry_model.id, db=db)
        if latest_version:
            entry_model.current_version_number = latest_version.version_number
            entry_model.branch_name = latest_version.branch_name
        enriched.append(entry_model)
    return enriched


@router.post('/projects/{project_id}/entries', response_model=PMEntryModel)
async def create_entry(
    project_id: str,
    form_data: PMEntryForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    form_data.project_id = project_id
    entry = await PMEntries.insert_new_entry(user.id, form_data, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create entry')
    
    # Auto-create entity for traceability
    try:
        from open_webui.models.pm import PMEntities, PMEntityForm
        entity_form = PMEntityForm(
            project_id=project_id,
            type=form_data.module_type,
            name=form_data.title,
            module_id=form_data.module_type,
            entry_id=entry.id,
            entity_metadata=form_data.data,
        )
        await PMEntities.insert_new_entity(user.id, entity_form, db=db)
    except Exception as e:
        # Don't fail entry creation if entity creation fails
        log.warning(f'Failed to auto-create entity for entry {entry.id}: {e}')

    # Auto-create initial entry version (v1)
    try:
        from open_webui.models.pm import PMEntryVersions, PMEntryVersionForm
        version_form = PMEntryVersionForm(
            entry_id=entry.id,
            project_id=project_id,
            module_type=form_data.module_type,
            version_number='v1',
            content=entry.content,
            entry_metadata=form_data.data,
            change_summary='Initial version',
        )
        await PMEntryVersions.insert_new_version(user.id, version_form, db=db)
    except Exception as e:
        log.warning(f'Failed to auto-create entry version for entry {entry.id}: {e}')

    # Enrich response with version info
    entry_response = PMEntryModel.model_validate(entry)
    entry_response.current_version_number = 'v1'
    entry_response.branch_name = 'main'
    return entry_response


@router.get('/entries/{entry_id}', response_model=PMEntryModel)
async def get_entry(
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    # Verify user has access to the project
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    return entry


@router.post('/entries/{entry_id}', response_model=PMEntryModel)
async def update_entry(
    entry_id: str,
    form_data: PMEntryUpdateForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    # Verify user has access to the project
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    entry = await PMEntries.update_entry_by_id(entry_id, form_data, db=db)
    return entry


@router.delete('/entries/{entry_id}')
async def delete_entry(
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    # Verify user has access to the project
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    await PMEntries.delete_entry_by_id(entry_id, db=db)
    return True


############################
# Entry Versions
############################

@router.get('/projects/{project_id}/entries/{entry_id}/versions', response_model=list)
async def get_entry_versions(
    project_id: str,
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryVersions
    versions = await PMEntryVersions.get_versions_by_entry_id(entry_id, db=db)
    return versions


@router.post('/projects/{project_id}/entries/{entry_id}/versions', response_model=dict)
async def create_entry_version(
    project_id: str,
    entry_id: str,
    form_data: dict,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryVersions, PMEntryVersionForm
    # Get current entry to snapshot
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    
    # Auto-generate version number
    existing = await PMEntryVersions.get_versions_by_entry_id(entry_id, db=db)
    version_number = form_data.get('version_number') or f'v{len(existing) + 1}'
    
    version_form = PMEntryVersionForm(
        entry_id=entry_id,
        project_id=project_id,
        module_type=entry.module_type,
        version_number=version_number,
        content=entry.content,
        entry_metadata=entry.data,
        branch_name=form_data.get('branch_name', 'main'),
        change_summary=form_data.get('change_summary', ''),
        project_version_id=form_data.get('project_version_id'),
    )
    version = await PMEntryVersions.insert_new_version(user.id, version_form, db=db)
    return version


@router.get('/projects/{project_id}/entries/{entry_id}/versions/{version_id}', response_model=dict)
async def get_entry_version(
    project_id: str,
    entry_id: str,
    version_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryVersions
    version = await PMEntryVersions.get_version_by_id(version_id, db=db)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Version not found')
    return version


@router.post('/projects/{project_id}/entries/{entry_id}/versions/{version_id}/switch', response_model=dict)
async def switch_entry_version(
    project_id: str,
    entry_id: str,
    version_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryVersions
    version = await PMEntryVersions.get_version_by_id(version_id, db=db)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Version not found')
    
    # Restore entry content from version
    await PMEntries.update_entry_by_id(
        entry_id,
        PMEntryUpdateForm(content=version.content, data=version.entry_metadata),
        db=db
    )
    return {'entry_id': entry_id, 'current_version_id': version_id}


@router.get('/projects/{project_id}/entries/{entry_id}/versions/{version_id_a}/diff/{version_id_b}', response_model=dict)
async def diff_entry_versions(
    project_id: str,
    entry_id: str,
    version_id_a: str,
    version_id_b: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Compare two versions and return diff"""
    from open_webui.models.pm import PMEntryVersions
    version_a = await PMEntryVersions.get_version_by_id(version_id_a, db=db)
    version_b = await PMEntryVersions.get_version_by_id(version_id_b, db=db)
    if not version_a or not version_b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Version not found')
    
    # Simple text diff
    import difflib
    content_a = version_a.content or ''
    content_b = version_b.content or ''
    
    diff = list(difflib.unified_diff(
        content_a.splitlines(keepends=True),
        content_b.splitlines(keepends=True),
        fromfile=f'version {version_a.version_number}',
        tofile=f'version {version_b.version_number}',
        lineterm=''
    ))
    
    return {
        'version_a': {
            'id': version_a.id,
            'version_number': version_a.version_number,
            'created_at': version_a.created_at,
        },
        'version_b': {
            'id': version_b.id,
            'version_number': version_b.version_number,
            'created_at': version_b.created_at,
        },
        'diff': ''.join(diff),
        'content_a': content_a,
        'content_b': content_b,
    }


@router.get('/projects/{project_id}/entries/{entry_id}/versions/compare')
async def compare_entry_versions(
    project_id: str,
    entry_id: str,
    version_a: str,
    version_b: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Compare two entry versions and return structured diff."""
    from open_webui.models.pm import PMEntryVersions
    v1 = await PMEntryVersions.get_version_by_id(version_a, db=db)
    v2 = await PMEntryVersions.get_version_by_id(version_b, db=db)
    if not v1 or not v2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Version not found')
    
    # Content diff
    content_diff = []
    if v1.content != v2.content:
        content_diff.append({
            'path': 'content',
            'type': 'modified',
            'old': v1.content,
            'new': v2.content,
        })
    
    # Metadata diff
    metadata_diff = []
    v1_meta = v1.entry_metadata or {}
    v2_meta = v2.entry_metadata or {}
    all_keys = set(v1_meta.keys()) | set(v2_meta.keys())
    for key in all_keys:
        old_val = v1_meta.get(key)
        new_val = v2_meta.get(key)
        if old_val != new_val:
            diff_type = 'modified'
            if old_val is None:
                diff_type = 'added'
            elif new_val is None:
                diff_type = 'removed'
            metadata_diff.append({
                'field': key,
                'old': old_val,
                'new': new_val,
                'type': diff_type
            })
    
    return {
        'version_a': {'id': v1.id, 'version_number': v1.version_number, 'created_at': v1.created_at},
        'version_b': {'id': v2.id, 'version_number': v2.version_number, 'created_at': v2.created_at},
        'content_diff': content_diff,
        'metadata_diff': metadata_diff,
    }


############################
# Entry Branches
############################

@router.get('/projects/{project_id}/entries/{entry_id}/branches', response_model=list)
async def get_entry_branches(
    project_id: str,
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryBranches
    return await PMEntryBranches.get_branches_by_entry_id(entry_id, db=db)


@router.post('/projects/{project_id}/entries/{entry_id}/branches', response_model=dict)
async def create_entry_branch(
    project_id: str,
    entry_id: str,
    form_data: dict,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryBranches, PMEntryBranchForm
    branch_form = PMEntryBranchForm(
        project_id=project_id,
        entry_id=entry_id,
        name=form_data.get('name', ''),
        source_version_id=form_data.get('source_version_id'),
    )
    branch = await PMEntryBranches.insert_new_branch(branch_form, db=db)
    return branch


############################
# Entry Merges
############################

@router.get('/projects/{project_id}/entries/{entry_id}/merges', response_model=list)
async def get_entry_merges(
    project_id: str,
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryMerges
    return await PMEntryMerges.get_merges_by_entry_id(entry_id, db=db)


@router.post('/projects/{project_id}/entries/{entry_id}/merges', response_model=dict)
async def create_entry_merge(
    project_id: str,
    entry_id: str,
    form_data: dict,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryMerges, PMEntryMergeForm
    merge_form = PMEntryMergeForm(
        entry_id=entry_id,
        branch_id=form_data.get('branch_id', ''),
        target_version_id=form_data.get('target_version_id'),
    )
    merge = await PMEntryMerges.insert_new_merge(merge_form, db=db)
    return merge


class PMImportRequest(BaseModel):
    module_type: str
    format: str = 'json'  # json | csv
    data: list | str  # list of dicts for JSON, string for CSV
    create_versions: bool = True


############################
# Entry Import / Export
############################

import csv
import io


async def _import_entries(
    project_id: str,
    module_type: str,
    format: str,
    data,
    user,
    db: AsyncSession,
    create_versions: bool = True,
):
    """Shared import logic for entries."""
    imported = []
    errors = []

    rows = []
    if format == 'json':
        if not isinstance(data, list):
            errors.append({'error': 'JSON data must be a list of objects'})
            return {'imported': imported, 'errors': errors}
        rows = data
    elif format == 'csv':
        if not isinstance(data, str):
            errors.append({'error': 'CSV data must be a string'})
            return {'imported': imported, 'errors': errors}
        try:
            reader = csv.DictReader(io.StringIO(data.strip()))
            rows = list(reader)
        except Exception as e:
            errors.append({'error': f'Failed to parse CSV: {str(e)}'})
            return {'imported': imported, 'errors': errors}
    else:
        errors.append({'error': f'Unsupported format: {format}'})
        return {'imported': imported, 'errors': errors}

    for idx, row in enumerate(rows):
        try:
            title = row.get('title', '')
            if not title:
                errors.append({'index': idx, 'error': 'Missing title'})
                continue

            content = row.get('content', '')
            status_val = row.get('status', 'draft')
            priority = row.get('priority', None)
            data_json = row.get('data_json', None)
            entry_data = None
            if data_json:
                try:
                    entry_data = json.loads(data_json) if isinstance(data_json, str) else data_json
                except Exception:
                    entry_data = None

            entry_form = PMEntryForm(
                project_id=project_id,
                module_type=module_type,
                title=title,
                content=content,
                data=entry_data,
                status=status_val,
                priority=priority,
            )
            entry = await PMEntries.insert_new_entry(user.id, entry_form, db=db)
            if not entry:
                errors.append({'index': idx, 'error': 'Failed to create entry'})
                continue

            # Auto-create entity for traceability
            try:
                from open_webui.models.pm import PMEntities, PMEntityForm
                entity_form = PMEntityForm(
                    project_id=project_id,
                    type=module_type,
                    name=title,
                    module_id=module_type,
                    entry_id=entry.id,
                    entity_metadata=entry_data,
                )
                await PMEntities.insert_new_entity(user.id, entity_form, db=db)
            except Exception as e:
                log.warning(f'Failed to auto-create entity for entry {entry.id}: {e}')

            # Auto-create initial entry version (v1) if requested
            if create_versions:
                try:
                    from open_webui.models.pm import PMEntryVersions, PMEntryVersionForm
                    version_form = PMEntryVersionForm(
                        entry_id=entry.id,
                        project_id=project_id,
                        module_type=module_type,
                        version_number='v1',
                        content=entry.content,
                        entry_metadata=entry_data,
                        change_summary='Initial version',
                    )
                    await PMEntryVersions.insert_new_version(user.id, version_form, db=db)
                except Exception as e:
                    log.warning(f'Failed to auto-create entry version for entry {entry.id}: {e}')

            imported.append(entry)
        except Exception as e:
            errors.append({'index': idx, 'error': str(e)})

    return {'imported': imported, 'errors': errors}


@router.post('/projects/{project_id}/entries/import')
async def import_entries(
    project_id: str,
    form_data: PMImportRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Import entries into a project from JSON or CSV."""
    # Verify project exists and user owns it
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    result = await _import_entries(
        project_id=project_id,
        module_type=form_data.module_type,
        format=form_data.format,
        data=form_data.data,
        user=user,
        db=db,
        create_versions=form_data.create_versions,
    )

    return {
        'success': True,
        'imported': len(result['imported']),
        'entries': result['imported'],
        'errors': result['errors'],
    }


@router.get('/entries/{entry_id}/export')
async def export_entry(
    entry_id: str,
    export_format: str = 'json',
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Export an entry in JSON, Markdown, or CSV format."""
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    # Verify user has access to the project
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    # Get latest version
    from open_webui.models.pm import PMEntryVersions
    latest_version = await PMEntryVersions.get_latest_version_by_entry_id(entry_id, db=db)

    if export_format == 'json':
        entry_dict = PMEntryModel.model_validate(entry).model_dump()
        version_dict = None
        if latest_version:
            version_dict = PMEntryVersionModel.model_validate(latest_version).model_dump()
        return {
            'entry': entry_dict,
            'version': version_dict,
        }
    elif export_format == 'markdown':
        content = entry.content or ''
        if entry.data and isinstance(entry.data, dict):
            # Try to format data as markdown if available
            data_md = json.dumps(entry.data, ensure_ascii=False, indent=2)
            content = f'{content}\n\n## Data\n\n```json\n{data_md}\n```'
        return PlainTextResponse(content=content)
    elif export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'title', 'content', 'status', 'priority', 'module_type', 'data_json'])
        data_json = ''
        if entry.data:
            data_json = json.dumps(entry.data, ensure_ascii=False)
        writer.writerow([
            entry.id,
            entry.title,
            entry.content or '',
            entry.status,
            entry.priority or '',
            entry.module_type,
            data_json,
        ])
        return PlainTextResponse(content=output.getvalue())
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Unsupported format: {export_format}')


############################
# Flow Templates & Execution
############################

# Hardcoded flow template definitions
FLOW_TEMPLATES = {
    'requirement_to_parameter': {
        'id': 'requirement_to_parameter',
        'name': '需求→参数拆解',
        'description': '将需求条目拆解为参数列表',
        'input_module': 'requirement',
        'output_module': 'parameter',
        'steps': [
            {'action': 'get_entry', 'description': '获取需求内容'},
            {'action': 'extract_parameters', 'description': 'AI 提取参数'},
            {'action': 'create_entries', 'description': '创建参数条目'},
            {'action': 'create_relations', 'description': '建立需求→参数关联'},
        ],
    },
    'requirement_to_prd': {
        'id': 'requirement_to_prd',
        'name': '需求→PRD',
        'description': '基于需求生成 PRD 文档',
        'input_module': 'requirement',
        'output_module': 'prd',
        'steps': [
            {'action': 'get_entries', 'description': '获取需求列表'},
            {'action': 'analyze_requirements', 'description': '分析需求'},
            {'action': 'generate_prd', 'description': 'AI 生成 PRD'},
            {'action': 'create_entry', 'description': '创建 PRD 条目'},
            {'action': 'create_relations', 'description': '建立需求→PRD 关联'},
        ],
    },
    'prd_to_parameter': {
        'id': 'prd_to_parameter',
        'name': 'PRD→参数提取',
        'description': '从 PRD 提取参数',
        'input_module': 'prd',
        'output_module': 'parameter',
        'steps': [
            {'action': 'get_entry', 'description': '获取 PRD 内容'},
            {'action': 'extract_parameters', 'description': 'AI 提取参数'},
            {'action': 'merge_parameters', 'description': '合并去重'},
            {'action': 'create_entries', 'description': '创建参数条目'},
            {'action': 'create_relations', 'description': '建立 PRD→参数关联'},
        ],
    },
    'parameter_to_testcase': {
        'id': 'parameter_to_testcase',
        'name': '参数→测试用例',
        'description': '基于参数生成测试用例',
        'input_module': 'parameter',
        'output_module': 'testcase',
        'steps': [
            {'action': 'get_entries', 'description': '获取参数列表'},
            {'action': 'generate_testcases', 'description': 'AI 生成测试用例'},
            {'action': 'create_entries', 'description': '创建测试用例条目'},
            {'action': 'create_relations', 'description': '建立参数→测试用例关联'},
        ],
    },
    'full_chain': {
        'id': 'full_chain',
        'name': '完整流转链',
        'description': '需求→PRD→参数→测试用例 一键流转',
        'input_module': 'requirement',
        'output_module': 'testcase',
        'steps': [
            {'action': 'execute_flow', 'template': 'requirement_to_prd', 'description': '需求→PRD'},
            {'action': 'execute_flow', 'template': 'prd_to_parameter', 'description': 'PRD→参数'},
            {'action': 'execute_flow', 'template': 'parameter_to_testcase', 'description': '参数→测试用例'},
        ],
    },
}


async def _create_entry_with_entity(
    user, project_id: str, module_type: str, title: str, content: str, data: dict | None, db: AsyncSession,
) -> PMEntryModel | None:
    """Helper: create an entry + auto entity, matching the create_entry endpoint pattern."""
    from open_webui.models.pm import PMEntities, PMEntityForm, PMEntryVersions, PMEntryVersionForm

    entry_form = PMEntryForm(
        project_id=project_id,
        module_type=module_type,
        title=title,
        content=content,
        data=data,
        status='draft',
    )
    entry = await PMEntries.insert_new_entry(user.id, entry_form, db=db)
    if not entry:
        return None

    # Auto-create entity for traceability
    try:
        entity_form = PMEntityForm(
            project_id=project_id,
            type=module_type,
            name=title,
            module_id=module_type,
            entry_id=entry.id,
            entity_metadata=data,
        )
        await PMEntities.insert_new_entity(user.id, entity_form, db=db)
    except Exception as e:
        log.warning(f'Failed to auto-create entity for flow entry {entry.id}: {e}')

    # Auto-create initial entry version
    try:
        version_form = PMEntryVersionForm(
            entry_id=entry.id,
            project_id=project_id,
            module_type=module_type,
            version_number='v1',
            content=content,
            entry_metadata=data,
            change_summary='Created by flow engine',
        )
        await PMEntryVersions.insert_new_version(user.id, version_form, db=db)
    except Exception as e:
        log.warning(f'Failed to auto-create entry version for flow entry {entry.id}: {e}')

    return entry


async def _create_derives_relation(
    user, project_id: str, source_entity_id: str, target_entity_id: str, db: AsyncSession,
) -> dict | None:
    """Helper: create a 'derives' relation between two entities."""
    from open_webui.models.pm import PMRelations, PMRelationForm

    relation_form = PMRelationForm(
        project_id=project_id,
        entity_a_id=source_entity_id,
        entity_b_id=target_entity_id,
        relation_type='derives',
        confidence=100,
        confirmed=1,
        created_by=user.id,
    )
    relation = await PMRelations.insert_new_relation(user.id, relation_form, db=db)
    return PMRelationModel.model_validate(relation).model_dump() if relation else None


async def _find_entity_by_entry_id(entry_id: str, db: AsyncSession) -> str | None:
    """Find the entity ID associated with an entry."""
    from open_webui.models.pm import PMEntity

    query = select(PMEntity).where(PMEntity.entry_id == entry_id)
    result = await db.execute(query)
    entity = result.scalar_one_or_none()
    return entity.id if entity else None


async def _flow_requirement_to_parameter(
    source_entry_ids: list[str], project_id: str, user, request: Request, db: AsyncSession,
) -> dict:
    """Flow: requirement → parameter extraction using AI."""
    from open_webui.models.pm import PMEntities, PMEntityForm

    # 1. Fetch source entries
    source_entries = []
    for eid in source_entry_ids:
        entry = await PMEntries.get_entry_by_id(eid, db=db)
        if entry:
            source_entries.append(entry)

    if not source_entries:
        return {'created_entries': [], 'created_relations': [], 'step_results': [], 'error': 'No source entries found'}

    # 2. Call LLM to extract parameters
    combined_content = '\n\n'.join([f'## {e.title}\n{e.content or ""}' for e in source_entries])
    combined_titles = ', '.join([e.title for e in source_entries])

    system_prompt = (
        '你是参数提取专家。从需求文档中提取关键参数，'
        '返回 JSON 数组。每个参数包含：'
        'name(参数名), key(参数Key), type(数据类型), '
        'defaultValue(默认值), description(说明), module(所属模块)'
    )
    user_message = f'请从以下需求中提取关键参数：\n\n标题: {combined_titles}\n内容:\n{combined_content}'

    llm_response = await _call_llm(request, user, system_prompt, user_message)

    parameters = []
    if llm_response:
        try:
            import re
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                parameters = json.loads(json_match.group(0))
        except Exception:
            parameters = []

    if not parameters:
        return {'created_entries': [], 'created_relations': [], 'step_results': [{'action': 'extract_parameters', 'status': 'no_results'}], 'error': 'AI failed to extract parameters'}

    # 3. Create parameter entries + entities + relations
    created_entries = []
    created_relations = []
    step_results = [{'action': 'extract_parameters', 'status': 'completed', 'count': len(parameters)}]

    for param in parameters:
        entry = await _create_entry_with_entity(
            user=user,
            project_id=project_id,
            module_type='parameter',
            title=param.get('name', '未命名参数'),
            content=param.get('description', ''),
            data=param,
            db=db,
        )
        if entry:
            created_entries.append(PMEntryModel.model_validate(entry).model_dump() if isinstance(entry, PMEntry) else entry)

            # Create derives relation from each source entry to the new parameter
            for src_entry in source_entries:
                src_entity_id = await _find_entity_by_entry_id(src_entry.id, db)
                tgt_entity_id = await _find_entity_by_entry_id(entry.id, db)
                if src_entity_id and tgt_entity_id:
                    relation = await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
                    if relation:
                        created_relations.append(relation)

    step_results.append({'action': 'create_entries', 'status': 'completed', 'count': len(created_entries)})
    step_results.append({'action': 'create_relations', 'status': 'completed', 'count': len(created_relations)})

    return {
        'created_entries': created_entries,
        'created_relations': created_relations,
        'step_results': step_results,
    }


async def _flow_requirement_to_prd(
    source_entry_ids: list[str], project_id: str, user, request: Request, db: AsyncSession,
) -> dict:
    """Flow: requirement → PRD generation using AI."""
    # 1. Fetch source entries
    source_entries = []
    for eid in source_entry_ids:
        entry = await PMEntries.get_entry_by_id(eid, db=db)
        if entry:
            source_entries.append(entry)

    if not source_entries:
        return {'created_entries': [], 'created_relations': [], 'step_results': [], 'error': 'No source entries found'}

    # 2. Call LLM to generate PRD
    req_summary = '\n'.join([f'- {e.title}: {(e.content or "")[:200]}' for e in source_entries])
    combined_titles = ', '.join([e.title for e in source_entries])

    system_prompt = (
        '你是 PRD 生成专家。根据需求生成完整的 PRD 文档，'
        '包含：概述、背景、目标、功能需求、非功能需求、附录。'
        '返回 JSON 格式：{title, content}'
    )
    user_message = f'请根据以下需求生成 PRD：\n\n需求列表：\n{req_summary}'

    llm_response = await _call_llm(request, user, system_prompt, user_message)

    prd_title = f'PRD - {combined_titles}'
    prd_content = llm_response or ''

    # Try to parse structured response
    prd_data = None
    if llm_response:
        try:
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                prd_title = parsed.get('title', prd_title)
                prd_content = parsed.get('content', llm_response)
                prd_data = parsed
        except Exception:
            pass

    step_results = [{'action': 'generate_prd', 'status': 'completed'}]

    # 3. Create PRD entry + entity
    entry = await _create_entry_with_entity(
        user=user,
        project_id=project_id,
        module_type='prd',
        title=prd_title,
        content=prd_content,
        data=prd_data,
        db=db,
    )

    created_entries = []
    created_relations = []

    if entry:
        created_entries.append(PMEntryModel.model_validate(entry).model_dump() if isinstance(entry, PMEntry) else entry)

        # Create derives relation from each source requirement to the PRD
        for src_entry in source_entries:
            src_entity_id = await _find_entity_by_entry_id(src_entry.id, db)
            tgt_entity_id = await _find_entity_by_entry_id(entry.id, db)
            if src_entity_id and tgt_entity_id:
                relation = await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
                if relation:
                    created_relations.append(relation)

    step_results.append({'action': 'create_entry', 'status': 'completed', 'entry_id': entry.id if entry else None})
    step_results.append({'action': 'create_relations', 'status': 'completed', 'count': len(created_relations)})

    return {
        'created_entries': created_entries,
        'created_relations': created_relations,
        'step_results': step_results,
        'prd_entry_id': entry.id if entry else None,
    }


async def _flow_prd_to_parameter(
    source_entry_ids: list[str], project_id: str, user, request: Request, db: AsyncSession,
) -> dict:
    """Flow: PRD → parameter extraction using AI, with dedup."""
    # 1. Fetch source PRD entries
    source_entries = []
    for eid in source_entry_ids:
        entry = await PMEntries.get_entry_by_id(eid, db=db)
        if entry:
            source_entries.append(entry)

    if not source_entries:
        return {'created_entries': [], 'created_relations': [], 'step_results': [], 'error': 'No source entries found'}

    # 2. Call LLM to extract parameters
    combined_content = '\n\n'.join([f'## {e.title}\n{e.content or ""}' for e in source_entries])
    combined_titles = ', '.join([e.title for e in source_entries])

    system_prompt = (
        '你是参数提取专家。从 PRD 文档中提取关键参数，'
        '返回 JSON 数组。每个参数包含：'
        'name(参数名), key(参数Key), type(数据类型), '
        'defaultValue(默认值), description(说明), module(所属模块)'
    )
    user_message = f'请从以下 PRD 中提取关键参数：\n\n标题: {combined_titles}\n内容:\n{combined_content}'

    llm_response = await _call_llm(request, user, system_prompt, user_message)

    parameters = []
    if llm_response:
        try:
            import re
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                parameters = json.loads(json_match.group(0))
        except Exception:
            parameters = []

    # 3. Deduplicate by key
    unique_params = []
    seen_keys = set()
    for param in parameters:
        key = param.get('key', '')
        if key and key not in seen_keys:
            seen_keys.add(key)
            unique_params.append(param)
        elif not key:
            unique_params.append(param)

    step_results = [
        {'action': 'extract_parameters', 'status': 'completed', 'raw_count': len(parameters)},
        {'action': 'merge_parameters', 'status': 'completed', 'deduped_count': len(unique_params)},
    ]

    # 4. Create parameter entries + entities + relations
    created_entries = []
    created_relations = []

    for param in unique_params:
        entry = await _create_entry_with_entity(
            user=user,
            project_id=project_id,
            module_type='parameter',
            title=param.get('name', '未命名参数'),
            content=param.get('description', ''),
            data=param,
            db=db,
        )
        if entry:
            created_entries.append(PMEntryModel.model_validate(entry).model_dump() if isinstance(entry, PMEntry) else entry)

            for src_entry in source_entries:
                src_entity_id = await _find_entity_by_entry_id(src_entry.id, db)
                tgt_entity_id = await _find_entity_by_entry_id(entry.id, db)
                if src_entity_id and tgt_entity_id:
                    relation = await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
                    if relation:
                        created_relations.append(relation)

    step_results.append({'action': 'create_entries', 'status': 'completed', 'count': len(created_entries)})
    step_results.append({'action': 'create_relations', 'status': 'completed', 'count': len(created_relations)})

    return {
        'created_entries': created_entries,
        'created_relations': created_relations,
        'step_results': step_results,
    }


async def _flow_parameter_to_testcase(
    source_entry_ids: list[str], project_id: str, user, request: Request, db: AsyncSession,
) -> dict:
    """Flow: parameter → testcase generation using AI."""
    # 1. Fetch source parameter entries
    source_entries = []
    for eid in source_entry_ids:
        entry = await PMEntries.get_entry_by_id(eid, db=db)
        if entry:
            source_entries.append(entry)

    if not source_entries:
        return {'created_entries': [], 'created_relations': [], 'step_results': [], 'error': 'No source entries found'}

    # 2. Call LLM to generate test cases
    param_summary = '\n'.join([
        f'- {e.title}: {(e.content or "")[:100]} | data: {json.dumps(e.data, ensure_ascii=False)[:100]}'
        for e in source_entries
    ])

    system_prompt = (
        '你是测试专家。根据参数生成测试用例，'
        '包含功能测试、边界测试、异常测试。'
        '返回 JSON 数组。每个用例包含：'
        'name, type(functional/boundary/exception), steps, expectedResult, priority'
    )
    user_message = f'请根据以下参数生成测试用例：\n\n{param_summary}'

    llm_response = await _call_llm(request, user, system_prompt, user_message)

    testcases = []
    if llm_response:
        try:
            import re
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                testcases = json.loads(json_match.group(0))
        except Exception:
            testcases = []

    step_results = [{'action': 'generate_testcases', 'status': 'completed', 'count': len(testcases)}]

    # 3. Create testcase entries + entities + relations
    created_entries = []
    created_relations = []

    for tc in testcases:
        entry = await _create_entry_with_entity(
            user=user,
            project_id=project_id,
            module_type='testcase',
            title=tc.get('name', '未命名测试用例'),
            content=tc.get('steps', ''),
            data=tc,
            db=db,
        )
        if entry:
            created_entries.append(PMEntryModel.model_validate(entry).model_dump() if isinstance(entry, PMEntry) else entry)

            for src_entry in source_entries:
                src_entity_id = await _find_entity_by_entry_id(src_entry.id, db)
                tgt_entity_id = await _find_entity_by_entry_id(entry.id, db)
                if src_entity_id and tgt_entity_id:
                    relation = await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
                    if relation:
                        created_relations.append(relation)

    step_results.append({'action': 'create_entries', 'status': 'completed', 'count': len(created_entries)})
    step_results.append({'action': 'create_relations', 'status': 'completed', 'count': len(created_relations)})

    return {
        'created_entries': created_entries,
        'created_relations': created_relations,
        'step_results': step_results,
    }


async def _flow_full_chain(
    source_entry_ids: list[str], project_id: str, user, request: Request, db: AsyncSession,
) -> dict:
    """Flow: full chain requirement → PRD → parameter → testcase."""
    all_entries = []
    all_relations = []
    step_results = []

    # Step 1: requirement → PRD
    prd_result = await _flow_requirement_to_prd(source_entry_ids, project_id, user, request, db)
    all_entries.extend(prd_result.get('created_entries', []))
    all_relations.extend(prd_result.get('created_relations', []))
    step_results.append({'action': 'requirement_to_prd', 'status': 'completed', 'entry_count': len(prd_result.get('created_entries', []))})

    prd_entry_id = prd_result.get('prd_entry_id')
    if not prd_entry_id:
        step_results.append({'action': 'prd_to_parameter', 'status': 'skipped', 'reason': 'No PRD entry created'})
        step_results.append({'action': 'parameter_to_testcase', 'status': 'skipped', 'reason': 'No PRD entry created'})
        return {'created_entries': all_entries, 'created_relations': all_relations, 'step_results': step_results}

    # Step 2: PRD → parameter
    param_result = await _flow_prd_to_parameter([prd_entry_id], project_id, user, request, db)
    all_entries.extend(param_result.get('created_entries', []))
    all_relations.extend(param_result.get('created_relations', []))
    step_results.append({'action': 'prd_to_parameter', 'status': 'completed', 'entry_count': len(param_result.get('created_entries', []))})

    # Step 3: parameter → testcase (for each created parameter)
    param_entry_ids = [e.get('id') for e in param_result.get('created_entries', []) if e.get('id')]
    if param_entry_ids:
        tc_result = await _flow_parameter_to_testcase(param_entry_ids, project_id, user, request, db)
        all_entries.extend(tc_result.get('created_entries', []))
        all_relations.extend(tc_result.get('created_relations', []))
        step_results.append({'action': 'parameter_to_testcase', 'status': 'completed', 'entry_count': len(tc_result.get('created_entries', []))})
    else:
        step_results.append({'action': 'parameter_to_testcase', 'status': 'skipped', 'reason': 'No parameter entries created'})

    return {
        'created_entries': all_entries,
        'created_relations': all_relations,
        'step_results': step_results,
    }


# Flow execution dispatch
FLOW_EXECUTORS = {
    'requirement_to_parameter': _flow_requirement_to_parameter,
    'requirement_to_prd': _flow_requirement_to_prd,
    'prd_to_parameter': _flow_prd_to_parameter,
    'parameter_to_testcase': _flow_parameter_to_testcase,
    'full_chain': _flow_full_chain,
}


@router.get('/flow/templates')
async def list_flow_templates(
    project_id: Optional[str] = None,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List all available flow templates (hardcoded + DB-stored)."""
    templates = []

    # Hardcoded templates
    for tid, tpl in FLOW_TEMPLATES.items():
        templates.append({
            'id': tpl['id'],
            'name': tpl['name'],
            'description': tpl['description'],
            'input_module': tpl['input_module'],
            'output_module': tpl['output_module'],
            'step_count': len(tpl['steps']),
            'source': 'builtin',
        })

    # DB-stored custom templates (entries with module_type="flow_template")
    if project_id:
        from open_webui.models.pm import PMEntity
        query = select(PMEntry).where(
            PMEntry.project_id == project_id,
            PMEntry.module_type == 'flow_template',
        ).order_by(PMEntry.updated_at.desc())
        result = await db.execute(query)
        custom_entries = result.scalars().all()
        for entry in custom_entries:
            tpl_data = entry.data or {}
            templates.append({
                'id': f'custom_{entry.id}',
                'name': entry.title,
                'description': entry.content or '',
                'input_module': tpl_data.get('input_module', ''),
                'output_module': tpl_data.get('output_module', ''),
                'step_count': len(tpl_data.get('steps', [])),
                'source': 'custom',
                'entry_id': entry.id,
            })

    return {'total': len(templates), 'templates': templates}


@router.post('/flow/preview')
async def preview_flow(
    form_data: FlowPreviewRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Preview flow execution (dry-run, no writes)."""
    template = FLOW_TEMPLATES.get(form_data.template_id)
    if not template:
        # Check custom templates
        if form_data.template_id.startswith('custom_'):
            entry_id = form_data.template_id[len('custom_'):]
            entry = await PMEntries.get_entry_by_id(entry_id, db=db)
            if entry and entry.module_type == 'flow_template':
                tpl_data = entry.data or {}
                template = {
                    'id': form_data.template_id,
                    'name': entry.title,
                    'description': entry.content or '',
                    'input_module': tpl_data.get('input_module', ''),
                    'output_module': tpl_data.get('output_module', ''),
                    'steps': tpl_data.get('steps', []),
                }

    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Template {form_data.template_id} not found')

    # Fetch source entries for context
    source_entries = []
    for eid in form_data.source_entry_ids:
        entry = await PMEntries.get_entry_by_id(eid, db=db)
        if entry:
            source_entries.append({'id': entry.id, 'title': entry.title, 'module_type': entry.module_type})

    # Build preview
    preview = {
        'template_id': form_data.template_id,
        'template_name': template.get('name', ''),
        'source_entries': source_entries,
        'steps': [{'action': s.get('action', ''), 'description': s.get('description', ''), 'status': 'pending'} for s in template.get('steps', [])],
        'estimated_outputs': [],
    }

    # Estimate outputs by template type
    tid = form_data.template_id
    if tid == 'requirement_to_parameter':
        preview['estimated_outputs'] = [{'type': 'parameter', 'estimated_count': '3-8', 'description': '预计提取参数'}]
    elif tid == 'requirement_to_prd':
        preview['estimated_outputs'] = [{'type': 'prd', 'estimated_count': 1, 'description': '预计生成 PRD 文档'}]
    elif tid == 'prd_to_parameter':
        preview['estimated_outputs'] = [{'type': 'parameter', 'estimated_count': '5-15', 'description': '预计提取参数（去重后）'}]
    elif tid == 'parameter_to_testcase':
        preview['estimated_outputs'] = [{'type': 'testcase', 'estimated_count': '5-20', 'description': '预计生成测试用例'}]
    elif tid == 'full_chain':
        preview['estimated_outputs'] = [
            {'type': 'prd', 'estimated_count': 1, 'description': '预计生成 PRD 文档'},
            {'type': 'parameter', 'estimated_count': '5-15', 'description': '预计提取参数'},
            {'type': 'testcase', 'estimated_count': '5-20', 'description': '预计生成测试用例'},
        ]

    return preview


@router.post('/flow/execute')
async def execute_flow(
    request: Request,
    form_data: FlowExecuteRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Execute a flow template."""
    # Verify confirmation
    if not form_data.confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Flow execution requires confirmation (confirmed=True)')

    # Verify project access
    project = await PMProjects.get_project_by_id(form_data.project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    # Find executor
    executor = FLOW_EXECUTORS.get(form_data.template_id)
    if not executor:
        # Check custom templates (not directly executable as full flow, but we try)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Flow template {form_data.template_id} not found or not executable')

    # Execute the flow
    result = await executor(
        source_entry_ids=form_data.source_entry_ids,
        project_id=form_data.project_id,
        user=user,
        request=request,
        db=db,
    )

    template = FLOW_TEMPLATES.get(form_data.template_id, {})
    return {
        'template_id': form_data.template_id,
        'template_name': template.get('name', form_data.template_id),
        'source_entry_ids': form_data.source_entry_ids,
        'status': 'completed',
        'created_entries': result.get('created_entries', []),
        'created_relations': result.get('created_relations', []),
        'step_results': result.get('step_results', []),
        'error': result.get('error'),
    }


@router.post('/flow/templates')
async def create_flow_template(
    form_data: FlowTemplateCreateRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a custom flow template (stored as entry with module_type="flow_template")."""
    project_id = form_data.project_id
    if not project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='project_id is required')

    # Verify project access
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    # Store as entry with module_type="flow_template"
    template_data = {
        'input_module': form_data.input_module,
        'output_module': form_data.output_module,
        'steps': form_data.steps,
    }

    entry = await _create_entry_with_entity(
        user=user,
        project_id=project_id,
        module_type='flow_template',
        title=form_data.name,
        content=form_data.description,
        data=template_data,
        db=db,
    )

    if not entry:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create flow template')

    return {
        'status': 'success',
        'template_id': f'custom_{entry.id}',
        'name': form_data.name,
        'description': form_data.description,
        'entry_id': entry.id,
        'message': '流转模板创建成功',
    }


############################
# Agent
############################

from open_webui.pm.intent import detect_intent
from open_webui.pm.skills.base import BaseSkill
from open_webui.pm.skills.prd_generation import PRDGenerationSkill
from open_webui.pm.skills.requirement_analysis import RequirementAnalysisSkill

SKILL_INSTANCES: dict[str, BaseSkill] = {
    'prd-generation': PRDGenerationSkill(),
    'requirement-analysis': RequirementAnalysisSkill(),
}

SKILL_DEFINITIONS = [
    {'id': 'prd-generation', 'name': 'PRD 生成', 'description': '根据需求生成 PRD 文档大纲和内容', 'icon': 'document'},
    {'id': 'requirement-analysis', 'name': '需求分析', 'description': '分析需求分类、优先级和潜在冲突', 'icon': 'search'},
    {'id': 'competitor-research', 'name': '竞品调研', 'description': '竞品对比分析和维度评分', 'icon': 'chart'},
    {'id': 'prototype-check', 'name': '原型走查', 'description': 'UI/原型走查检查和问题发现', 'icon': 'eye'},
    {'id': 'parameter-extract', 'name': '参数提取', 'description': '从文档中提取关键参数和配置项', 'icon': 'code'},
    {'id': 'testcase-generate', 'name': '测试用例生成', 'description': '根据需求生成测试用例', 'icon': 'check'},
    {'id': 'version-compare', 'name': '版本对比', 'description': '对比不同版本的差异', 'icon': 'diff'},
    {'id': 'relation-suggest', 'name': '关联建议', 'description': 'AI 建议条目间的关联关系', 'icon': 'link'},
    {'id': 'workflow-suggest', 'name': '流程建议', 'description': '工作流步骤和下一步建议', 'icon': 'flow'},
    {'id': 'general', 'name': '通用对话', 'description': '通用 PM 工作对话', 'icon': 'chat'},
]

PM_SYSTEM_PROMPT = """你是产品经理的 AI 助手，帮助用户完成产品工作流的各个环节。

核心规则：
1. 所有建议都是建议性的，不强制用户执行
2. 生成内容后，提示用户确认和修改
3. 操作前询问用户，尤其是修改和删除操作
4. 记住用户的偏好和项目上下文

能力范围：
- PRD 生成和检查
- 竞品分析调研
- 需求分类和优先级建议
- 原型走查分析
- 参数提取和配置
- 测试用例生成
- 流程建议
- 版本对比分析
- 关系关联建议

当生成结构化内容时，在回复末尾用 JSON 块标记可执行的操作，格式：
```action
{"type": "pm.entry.create", "label": "操作名称", "description": "说明", "payload": {...}}
```
"""


async def _call_llm(request: Request, user, system_prompt: str, user_message: str) -> str:
    """Call OpenWebUI's LLM infrastructure for chat completion."""
    try:
        from open_webui.utils.chat import generate_chat_completion

        payload = {
            'model': '',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            'stream': False,
        }
        result = await generate_chat_completion(request, payload, user)
        if isinstance(result, dict):
            choices = result.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content', '')
        return str(result)
    except Exception as e:
        log.error(f'LLM call failed: {e}')
        return ''


def _extract_json(llm_response: str, expect_list: bool = True):
    """Extract JSON from LLM response that may include markdown fences or explanatory text.

    LLMs often wrap JSON in ```json ... ``` blocks or add prose around it.
    This function tries:
    1. Direct json.loads (fast path if response is pure JSON)
    2. Regex extraction of JSON array/object from the response
    3. Fallback to empty list/dict
    """
    import re
    if not llm_response:
        return [] if expect_list else {}

    # Fast path: direct parse
    try:
        result = json.loads(llm_response)
        if expect_list and not isinstance(result, list):
            result = [result] if result else []
        return result
    except (json.JSONDecodeError, ValueError):
        pass

    # Regex extraction: pull JSON array or object from the response
    try:
        pattern = r'\[.*\]' if expect_list else r'\{.*\}'
        json_match = re.search(pattern, llm_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            if expect_list and not isinstance(result, list):
                result = [result] if result else []
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    return [] if expect_list else {}


@router.post('/agent/chat')
async def agent_chat(
    request: Request,
    form_data: AgentChatRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    skill_id, confidence = detect_intent(form_data.message)

    # Get skill instance if available
    skill = SKILL_INSTANCES.get(skill_id)
    system_prompt = skill.system_prompt if skill else PM_SYSTEM_PROMPT

    # Append context to system prompt
    context_parts = []
    if form_data.context:
        pname = form_data.context.get('projectName', '')
        etitle = form_data.context.get('entryTitle', '')
        if pname:
            context_parts.append(f'当前项目: {pname}')
        if form_data.module_type:
            context_parts.append(f'当前模块: {form_data.module_type}')
        if etitle:
            context_parts.append(f'当前编辑条目: {etitle}')
    if context_parts:
        system_prompt = system_prompt + '\n\n' + '\n'.join(context_parts)

    # Try LLM call
    llm_response = await _call_llm(request, user, system_prompt, form_data.message)

    if llm_response:
        # Parse actions from response
        actions = []
        import re
        action_pattern = r'```action\s*\n(.*?)\n```'
        for match in re.finditer(action_pattern, llm_response, re.DOTALL):
            try:
                import json
                action_data = json.loads(match.group(1))
                actions.append({
                    'id': f'action-{len(actions)}',
                    'type': action_data.get('type', 'pm.entry.create'),
                    'label': action_data.get('label', ''),
                    'description': action_data.get('description', ''),
                    'payload': action_data.get('payload', {}),
                    'status': 'pending',
                })
            except Exception:
                pass
        # Clean response text (remove action blocks)
        clean_response = re.sub(action_pattern, '', llm_response, flags=re.DOTALL).strip()
        return {
            'message': clean_response,
            'intent': {'skillId': skill_id, 'confidence': confidence},
            'actions': actions if actions else None,
            'skillId': skill_id,
        }

    # Fallback: skill-based response without LLM
    fallback_responses = {
        'prd-generation': '我可以帮你生成 PRD 大纲。请告诉我：\n1. 产品名称和定位\n2. 目标用户群体\n3. 核心功能需求\n\n我会按照标准模板生成概述→背景→目标→功能需求→非功能需求→附录的结构。',
        'requirement-analysis': '我可以帮你分析需求。请提供需求描述，我会给出：\n- 分类建议（功能/性能/安全/体验）\n- 优先级建议（P0-P3）\n- 潜在冲突和遗漏',
        'competitor-research': '我可以帮你做竞品分析。请告诉我：\n1. 要分析的竞品名称\n2. 关注的对比维度\n\n我会生成对比矩阵和评分建议。',
        'parameter-extract': '我可以帮你提取参数。请提供文档内容或指定 PRD 条目，我会提取出：\n- 参数名/Key\n- 参数类型（输入/输出/配置）\n- 数据类型\n- 默认值\n- 所属模块/功能',
        'testcase-generate': '我可以帮你生成测试用例。请指定功能或需求，我会生成：\n- 功能测试用例\n- 边界测试用例\n- 异常测试用例',
        'version-compare': '我可以帮你对比版本差异。请指定要对比的版本，我会列出各模块条目的变更。',
        'relation-suggest': '我可以帮你建议关联关系。基于当前项目的条目，我会分析可能的依赖和引用关系。',
        'workflow-suggest': '我可以帮你建议工作流。基于当前项目状态，我会建议下一步操作和待完成的步骤。',
        'general': '我是你的 PM AI 助手，可以帮你：\n- 生成 PRD 文档\n- 分析需求\n- 竞品调研\n- 提取参数\n- 生成测试用例\n- 风险检查\n\n请告诉我你需要什么帮助？',
    }
    return {
        'message': fallback_responses.get(skill_id, fallback_responses['general']),
        'intent': {'skillId': skill_id, 'confidence': confidence},
        'skillId': skill_id,
    }


@router.get('/agent/status')
async def agent_status(
    user=Depends(get_verified_user),
):
    try:
        from open_webui.models.models import Models
        models = Models.get_all_models()
        available = len(models) > 0
        model_name = models[0].id if models else ''
        return {
            'available': available,
            'provider': 'openai' if available else '',
            'model': model_name,
        }
    except Exception:
        return {'available': False, 'provider': '', 'model': ''}


@router.get('/agent/skills')
async def agent_skills(
    user=Depends(get_verified_user),
):
    return SKILL_DEFINITIONS


############################
# Traceability (Entities & Relations)
############################

@router.get('/projects/{project_id}/entities', response_model=list)
async def get_entities(
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntities
    return await PMEntities.get_entities_by_project_id(project_id, db=db)


@router.post('/projects/{project_id}/entities', response_model=dict)
async def create_entity(
    project_id: str,
    form_data: dict,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntities, PMEntityForm
    entity_form = PMEntityForm(
        project_id=project_id,
        type=form_data.get('type', 'entry'),
        name=form_data.get('name', ''),
        module_id=form_data.get('module_id'),
        feature_id=form_data.get('feature_id'),
        entry_id=form_data.get('entry_id'),
        entity_metadata=form_data.get('metadata'),
    )
    entity = await PMEntities.insert_new_entity(user.id, entity_form, db=db)
    if not entity:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create entity')
    return entity


@router.delete('/entities/{entity_id}')
async def delete_entity(
    entity_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntities
    await PMEntities.delete_entity_by_id(entity_id, db=db)
    return True


@router.get('/projects/{project_id}/relations', response_model=list)
async def get_relations(
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMRelations
    return await PMRelations.get_relations_by_project_id(project_id, db=db)


@router.post('/projects/{project_id}/relations', response_model=dict)
async def create_relation(
    project_id: str,
    form_data: dict,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMRelations, PMRelationForm
    relation_form = PMRelationForm(
        project_id=project_id,
        entity_a_id=form_data.get('entity_a_id', ''),
        entity_b_id=form_data.get('entity_b_id', ''),
        relation_type=form_data.get('relation_type', 'references'),
        confidence=form_data.get('confidence', 100),
        confirmed=form_data.get('confirmed', 1),
        created_by=user.id,
        version_id=form_data.get('version_id'),
    )
    relation = await PMRelations.insert_new_relation(user.id, relation_form, db=db)
    if not relation:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create relation')
    return relation


@router.delete('/relations/{relation_id}')
async def delete_relation(
    relation_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMRelations
    await PMRelations.delete_relation_by_id(relation_id, db=db)
    return True


@router.get('/entities/{entity_id}/relations', response_model=list)
async def get_entity_relations(
    entity_id: str,
    direction: Optional[str] = None,  # "outgoing" | "incoming" | None (both)
    relation_type: Optional[str] = None,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMRelations
    query = select(PMRelation)
    if direction == "outgoing":
        query = query.where(PMRelation.entity_a_id == entity_id)
    elif direction == "incoming":
        query = query.where(PMRelation.entity_b_id == entity_id)
    else:
        query = query.where(
            (PMRelation.entity_a_id == entity_id) | (PMRelation.entity_b_id == entity_id)
        )
    if relation_type:
        query = query.where(PMRelation.relation_type == relation_type)
    query = query.order_by(PMRelation.created_at.desc())
    result = await db.execute(query)
    return [PMRelationModel.model_validate(r) for r in result.scalars().all()]


@router.get('/projects/{project_id}/traceability/impact', response_model=dict)
async def get_impact_analysis(
    project_id: str,
    entity_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Impact analysis: find all downstream entities affected by changes to a given entity."""
    from open_webui.models.pm import PMRelations, PMEntities
    relations = await PMRelations.get_relations_by_entity_id(entity_id, db=db)
    
    # Find downstream: relations where entity is A and type is contains/derives/modifies
    downstream = []
    for r in relations:
        if r.entity_a_id == entity_id and r.relation_type in ('contains', 'derives', 'modifies'):
            entity_b = await PMEntities.get_entity_by_id(r.entity_b_id, db=db)
            if entity_b:
                downstream.append({
                    'entity': entity_b,
                    'relation_type': r.relation_type,
                    'confidence': r.confidence,
                })
    
    # Find upstream: relations where entity is B and type is contains/derives
    upstream = []
    for r in relations:
        if r.entity_b_id == entity_id and r.relation_type in ('contains', 'derives'):
            entity_a = await PMEntities.get_entity_by_id(r.entity_a_id, db=db)
            if entity_a:
                upstream.append({
                    'entity': entity_a,
                    'relation_type': r.relation_type,
                    'confidence': r.confidence,
                })
    
    return {
        'entity_id': entity_id,
        'upstream': upstream,
        'downstream': downstream,
        'total_affected': len(downstream),
    }


@router.get('/projects/{project_id}/traceability/chain', response_model=dict)
async def get_trace_chain(
    project_id: str,
    entity_id: str,
    direction: str = 'both',
    max_depth: int = 5,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Trace chain: follow relation links from an entity to build a trace path."""
    from open_webui.models.pm import PMRelations, PMEntities
    
    visited = set()
    chain = []
    
    async def trace(entity_id: str, depth: int, path: list):
        if depth > max_depth or entity_id in visited:
            return
        visited.add(entity_id)
        entity = await PMEntities.get_entity_by_id(entity_id, db=db)
        if not entity:
            return
        
        node = {
            'entity': entity,
            'depth': depth,
            'path': path.copy(),
        }
        chain.append(node)
        
        relations = await PMRelations.get_relations_by_entity_id(entity_id, db=db)
        for r in relations:
            if direction in ('both', 'downstream') and r.entity_a_id == entity_id:
                await trace(r.entity_b_id, depth + 1, path + [{
                    'from': entity_id,
                    'to': r.entity_b_id,
                    'type': r.relation_type,
                }])
            if direction in ('both', 'upstream') and r.entity_b_id == entity_id:
                await trace(r.entity_a_id, depth + 1, path + [{
                    'from': r.entity_a_id,
                    'to': entity_id,
                    'type': r.relation_type,
                }])
    
    await trace(entity_id, 0, [])
    return {
        'start_entity_id': entity_id,
        'direction': direction,
        'max_depth': max_depth,
        'chain': chain,
    }


@router.get('/projects/{project_id}/traceability/validate', response_model=dict)
async def validate_traceability(
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Validate traceability reasonableness for all entries in a project."""
    from open_webui.models.pm import PMEntries, PMRelations, PMEntities
    
    entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    entities = await PMEntities.get_entities_by_project_id(project_id, db=db)
    relations = await PMRelations.get_relations_by_project_id(project_id, db=db)
    
    # Build entity lookup by entry_id
    entity_by_entry = {e.entry_id: e for e in entities if e.entry_id}
    
    issues = []
    warnings = []
    
    for entry in entries:
        entity = entity_by_entry.get(entry.id)
        entry_data = entry.data or {}
        
        # Rule 1: Requirement approved but no linked test cases
        if entry.module_type == 'requirement' and entry.status == 'approved':
            related_testcases = [r for r in relations 
                if (r.entity_a_id == (entity.id if entity else '') or r.entity_b_id == (entity.id if entity else '')) 
                and r.relation_type == 'contains']
            if not related_testcases:
                warnings.append({
                    'entry_id': entry.id,
                    'module_type': entry.module_type,
                    'title': entry.title,
                    'rule': 'requirement_no_testcase',
                    'message': '需求已批准但无关联测试用例',
                    'severity': 'warning'
                })
        
        # Rule 2: Parameter without source document
        if entry.module_type == 'parameter':
            source_doc = entry_data.get('sourceDocument')
            if not source_doc:
                warnings.append({
                    'entry_id': entry.id,
                    'module_type': entry.module_type,
                    'title': entry.title,
                    'rule': 'parameter_no_source',
                    'message': '参数未关联来源文档',
                    'severity': 'warning'
                })
        
        # Rule 3: High probability risk without measures
        if entry.module_type == 'risk':
            probability = entry_data.get('probability')
            measures = entry_data.get('measures')
            if probability == 'high' and not measures:
                issues.append({
                    'entry_id': entry.id,
                    'module_type': entry.module_type,
                    'title': entry.title,
                    'rule': 'risk_high_no_measures',
                    'message': '高风险项未设置应对措施',
                    'severity': 'error'
                })
        
        # Rule 4: Test case without linked requirement
        if entry.module_type == 'testcase':
            req_id = entry_data.get('requirementId')
            if not req_id:
                warnings.append({
                    'entry_id': entry.id,
                    'module_type': entry.module_type,
                    'title': entry.title,
                    'rule': 'testcase_no_requirement',
                    'message': '测试用例未关联需求',
                    'severity': 'warning'
                })
        
        # Rule 5: Entry has no entity (traceability gap)
        if not entity:
            issues.append({
                'entry_id': entry.id,
                'module_type': entry.module_type,
                'title': entry.title,
                'rule': 'missing_entity',
                'message': '条目未创建溯源实体',
                'severity': 'error'
            })
    
    return {
        'total_entries': len(entries),
        'total_entities': len(entities),
        'total_relations': len(relations),
        'issues': issues,
        'warnings': warnings,
        'is_valid': len(issues) == 0,
    }

@router.post('/agent/skill/{skill_id}')
async def execute_skill(
    skill_id: str,
    request: Request,
    form_data: AgentSkillRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    # Use skill instance if available, otherwise fallback to generic prompt
    skill = SKILL_INSTANCES.get(skill_id)
    if skill:
        entry_title = None
        entry_content_summary = None
        if form_data.entry_id:
            try:
                entry = await PMEntries.get_entry_by_id(form_data.entry_id, db=db)
                if entry:
                    entry_title = entry.title
                    entry_content_summary = (entry.content or '')[:500]
            except Exception:
                pass
        user_message = skill.build_user_message(
            user_message=f'请执行 {skill_id} 分析。',
            project_id=form_data.project_id,
            module_type=form_data.module_type,
            entry_id=form_data.entry_id,
            entry_title=entry_title,
            entry_content_summary=entry_content_summary,
            extra_data=form_data.data,
        )
        system_prompt = skill.system_prompt
        llm_response = await _call_llm(request, user, system_prompt, user_message)

        if llm_response:
            result = skill.parse_response(llm_response)
            return result

        return {
            'message': skill.fallback_response(),
            'skillId': skill_id,
        }

    # Generic skill (no dedicated skill class)
    system_prompt = PM_SYSTEM_PROMPT

    # Load project context
    context_msg = f'项目ID: {form_data.project_id}'
    if form_data.module_type:
        context_msg += f'\n模块: {form_data.module_type}'
    if form_data.entry_id:
        try:
            entry = await PMEntries.get_entry_by_id(form_data.entry_id, db=db)
            if entry:
                context_msg += f'\n条目: {entry.title}'
                if entry.content:
                    context_msg += f'\n内容摘要: {entry.content[:500]}'
        except Exception:
            pass

    user_message = f'{context_msg}\n\n请执行 {skill_id} 分析。'
    if form_data.data:
        import json
        user_message += f'\n附加数据: {json.dumps(form_data.data, ensure_ascii=False)}'

    llm_response = await _call_llm(request, user, system_prompt, user_message)

    return {
        'message': llm_response or f'Skill {skill_id} 执行完成，但 AI 服务暂不可用。请稍后重试。',
        'skillId': skill_id,
    }


############################
# Entry Version Diff & Compare
############################

############################
# PM Agent Tools (Generic Integration)
############################

class PMCreateEntryRequest(BaseModel):
    project_id: str
    module_type: str
    title: str
    content: Optional[str] = None
    data: Optional[dict] = None
    status: Optional[str] = 'draft'
    priority: Optional[str] = None


class PMUpdateEntryRequest(BaseModel):
    entry_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    data: Optional[dict] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class PMCreateRelationRequest(BaseModel):
    project_id: str
    entity_a_id: str
    entity_b_id: str
    relation_type: str
    confidence: Optional[int] = 100


class PMGenerateRequest(BaseModel):
    module_type: str
    instructions: Optional[str] = None

class PMDeleteEntryRequest(BaseModel):
    entry_id: str


class PMArchiveProjectRequest(BaseModel):
    project_id: str


class PMExtractParametersRequest(BaseModel):
    entry_id: str


class PMGenerateToolRequest(BaseModel):
    entry_id: str
    module_type: str
    instructions: Optional[str] = None


class PMImportToolRequest(BaseModel):
    project_id: str
    module_type: str
    format: str = 'json'
    data: list | str


@router.post('/agent/tools/create_entry', response_model=dict)
async def agent_tool_create_entry(
    form_data: PMCreateEntryRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: create a PM entry."""
    entry_form = PMEntryForm(
        project_id=form_data.project_id,
        module_type=form_data.module_type,
        title=form_data.title,
        content=form_data.content,
        data=form_data.data,
        status=form_data.status,
        priority=form_data.priority,
    )
    entry = await PMEntries.insert_new_entry(user.id, entry_form, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create entry')
    return {'success': True, 'entry': entry}


@router.post('/agent/tools/update_entry', response_model=dict)
async def agent_tool_update_entry(
    form_data: PMUpdateEntryRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: update a PM entry."""
    update_form = PMEntryUpdateForm(
        title=form_data.title,
        content=form_data.content,
        data=form_data.data,
        status=form_data.status,
        priority=form_data.priority,
    )
    entry = await PMEntries.update_entry_by_id(form_data.entry_id, update_form, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    return {'success': True, 'entry': entry}


@router.post('/agent/tools/create_relation', response_model=dict)
async def agent_tool_create_relation(
    form_data: PMCreateRelationRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: create a relation between entities."""
    from open_webui.models.pm import PMRelations, PMRelationForm
    relation_form = PMRelationForm(
        project_id=form_data.project_id,
        entity_a_id=form_data.entity_a_id,
        entity_b_id=form_data.entity_b_id,
        relation_type=form_data.relation_type,
        confidence=form_data.confidence,
        created_by=user.id,
    )
    relation = await PMRelations.insert_new_relation(user.id, relation_form, db=db)
    if not relation:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create relation')
    return {'success': True, 'relation': relation}


@router.get('/agent/tools/list_entries')
async def agent_tool_list_entries(
    project_id: str,
    module_type: Optional[str] = None,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: list entries for context."""
    if module_type:
        entries = await PMEntries.get_entries_by_project_and_module(project_id, module_type, db=db)
    else:
        entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    return {'success': True, 'entries': entries}


@router.get('/agent/tools/get_entry')
async def agent_tool_get_entry(
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: get entry details."""
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    return {'success': True, 'entry': entry}


############################
# Agent Tool API Extensions
############################

@router.post('/agent/tools/delete_entry', response_model=dict)
async def agent_tool_delete_entry(
    form_data: PMDeleteEntryRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: delete a PM entry."""
    entry = await PMEntries.get_entry_by_id(form_data.entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    # Verify user owns the project
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    await PMEntries.delete_entry_by_id(form_data.entry_id, db=db)
    return {'success': True, 'entry_id': form_data.entry_id}


@router.post('/agent/tools/archive_project', response_model=dict)
async def agent_tool_archive_project(
    form_data: PMArchiveProjectRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: archive a project."""
    project = await PMProjects.get_project_by_id(form_data.project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    update_form = PMProjectUpdateForm(status='archived')
    await PMProjects.update_project_by_id(form_data.project_id, update_form, db=db)
    return {'success': True, 'project_id': form_data.project_id, 'status': 'archived'}


@router.post('/agent/tools/extract_parameters', response_model=dict)
async def agent_tool_extract_parameters(
    request: Request,
    form_data: PMExtractParametersRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: extract parameters from an entry using AI."""
    entry = await PMEntries.get_entry_by_id(form_data.entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    # Verify user has access to the project
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    system_prompt = '你是参数提取专家。从文档中提取关键参数，返回 JSON 数组。每个参数：name, key, type, defaultValue, description'
    user_message = f"请从以下文档中提取关键参数：\n\n标题: {entry.title}\n内容: {entry.content or ''}"
    if entry.data:
        import json
        user_message += f"\n数据: {json.dumps(entry.data, ensure_ascii=False)}"

    llm_response = await _call_llm(request, user, system_prompt, user_message)

    # Try to parse JSON from response
    parameters = []
    if llm_response:
        try:
            import re
            # Try to extract JSON array from the response
            json_match = re.search(r'\[.*?\]', llm_response, re.DOTALL)
            if json_match:
                parameters = json.loads(json_match.group(0))
            else:
                # Try the whole response as JSON
                parameters = json.loads(llm_response)
        except Exception:
            parameters = []

    return {
        'success': True,
        'entry_id': form_data.entry_id,
        'parameters': parameters,
        'raw_response': llm_response,
    }


@router.post('/agent/tools/generate', response_model=dict)
async def agent_tool_generate(
    request: Request,
    form_data: PMGenerateToolRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: generate content for an entry using AI."""
    entry = await PMEntries.get_entry_by_id(form_data.entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    # Verify user has access to the project
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    system_prompt = f'你是{form_data.module_type}生成专家。根据需求生成专业的内容。'
    user_message = f"请为以下条目生成{form_data.module_type}内容：\n\n标题: {entry.title}\n当前内容: {entry.content or ''}"
    if form_data.instructions:
        user_message += f"\n\n额外指令: {form_data.instructions}"
    if entry.data:
        import json
        user_message += f"\n数据: {json.dumps(entry.data, ensure_ascii=False)}"

    llm_response = await _call_llm(request, user, system_prompt, user_message)

    return {
        'success': True,
        'entry_id': form_data.entry_id,
        'generated_content': llm_response,
        'raw_response': llm_response,
    }


@router.post('/agent/tools/import', response_model=dict)
async def agent_tool_import(
    form_data: PMImportToolRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Agent tool: import entries into a project."""
    # Verify project exists and user owns it
    project = await PMProjects.get_project_by_id(form_data.project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    result = await _import_entries(
        project_id=form_data.project_id,
        module_type=form_data.module_type,
        format=form_data.format,
        data=form_data.data,
        user=user,
        db=db,
        create_versions=True,
    )

    return {
        'success': True,
        'imported': len(result['imported']),
        'errors': result['errors'],
    }


############################
# Project Version <-> Entry Version Linkage
############################

@router.get('/projects/{project_id}/versions/{version_id}/entries', response_model=list)
async def get_project_version_entries(
    project_id: str,
    version_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get all entries associated with a project version."""
    from open_webui.models.pm import PMEntryVersions
    entry_versions = await PMEntryVersions.get_versions_by_project_version_id(version_id, db=db)
    entry_ids = list({v.entry_id for v in entry_versions})
    entries = []
    for eid in entry_ids:
        entry = await PMEntries.get_entry_by_id(eid, db=db)
        if entry:
            entries.append(entry)
    return entries


@router.post('/projects/{project_id}/versions/{version_id}/snapshot', response_model=dict)
async def create_project_version_snapshot(
    project_id: str,
    version_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a snapshot of all current entries for a project version."""
    from open_webui.models.pm import PMEntryVersions, PMEntryVersionForm
    entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    snapshots = []
    for entry in entries:
        # Derive version_number from the entry's latest version, or use 'v1' as default
        latest_version = await PMEntryVersions.get_latest_version_by_entry_id(entry.id, db=db)
        version_number = latest_version.version_number if latest_version else 'v1'
        version_form = PMEntryVersionForm(
            entry_id=entry.id,
            project_id=project_id,
            module_type=entry.module_type,
            version_number=version_number,
            content=entry.content,
            entry_metadata=entry.data,
            project_version_id=version_id,
            change_summary=f'Snapshot for project version {version_id}',
        )
        version = await PMEntryVersions.insert_new_version(user.id, version_form, db=db)
        if version:
            snapshots.append(version)
    return {
        'version_id': version_id,
        'snapshots_created': len(snapshots),
        'entries': snapshots,
    }


############################
# Traceability Version Flow Validation
############################

@router.get('/projects/{project_id}/traceability/validate-version-flow', response_model=dict)
async def validate_traceability_version_flow(
    project_id: str,
    entity_id: Optional[str] = None,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Validate traceability version flow for reasonableness."""
    from open_webui.models.pm import PMRelations, PMEntities

    issues = []
    relations = await PMRelations.get_relations_by_project_id(project_id, db=db)
    entities = await PMEntities.get_entities_by_project_id(project_id, db=db)

    entity_map = {e.id: e for e in entities}

    # Check for circular references (simple 2-hop detection)
    for rel in relations:
        if rel.relation_type in ('contains', 'derives', 'modifies'):
            reverse_rel = await db.execute(
                select(PMRelation).where(
                    PMRelation.entity_a_id == rel.entity_b_id,
                    PMRelation.entity_b_id == rel.entity_a_id,
                    PMRelation.relation_type.in_(['contains', 'derives', 'modifies'])
                )
            )
            if reverse_rel.scalar_one_or_none():
                issues.append({
                    'type': 'circular_reference',
                    'severity': 'warning',
                    'message': f'Circular reference: {rel.entity_a_id} <-> {rel.entity_b_id}',
                    'entities': [rel.entity_a_id, rel.entity_b_id],
                })

    # Check for low confidence relations
    for rel in relations:
        if rel.confidence and rel.confidence < 50:
            issues.append({
                'type': 'low_confidence',
                'severity': 'warning',
                'message': f'Low confidence ({rel.confidence}%): {rel.entity_a_id} -> {rel.entity_b_id}',
                'relation_id': rel.id,
            })

    # Check for orphaned entities
    entity_ids_with_relations = set()
    for rel in relations:
        entity_ids_with_relations.add(rel.entity_a_id)
        entity_ids_with_relations.add(rel.entity_b_id)

    orphaned = []
    for entity in entities:
        if entity.id not in entity_ids_with_relations:
            orphaned.append({'entity_id': entity.id, 'name': entity.name, 'type': entity.type})

    return {
        'valid': len([i for i in issues if i['severity'] == 'error']) == 0,
        'issues': issues,
        'orphaned_entities': orphaned,
        'total_relations': len(relations),
        'total_entities': len(entities),
    }


############################
# AI Operation Endpoints (Module-Level)
############################

@router.post('/entries/{entry_id}/extract-parameters')
async def extract_parameters(
    request: Request,
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    system_prompt = (
        "你是参数提取专家。从 PRD 或需求文档中提取关键参数，"
        "返回 JSON 格式的参数列表。每个参数包含："
        "name(参数名), key(参数Key), type(数据类型), "
        "defaultValue(默认值), description(说明), module(所属模块)"
    )
    user_message = f"请从以下文档中提取参数：\n\n标题: {entry.title}\n内容: {entry.content or ''}"
    llm_response = await _call_llm(request, user, system_prompt, user_message)

    if not llm_response:
        return {
            "entry_id": entry_id,
            "parameters": [],
            "message": "AI 服务暂不可用",
            "raw_response": None,
        }

    parameters = _extract_json(llm_response, expect_list=True)

    return {
        "entry_id": entry_id,
        "parameters": parameters,
        "raw_response": llm_response,
    }


@router.post('/entries/{entry_id}/analyze')
async def analyze_entry(
    request: Request,
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    system_prompt = (
        "你是需求分析专家。分析需求，给出分类建议、优先级建议和潜在冲突。"
        "返回 JSON 格式：{classification, priority, conflicts, suggestions}"
    )
    user_message = f"请分析以下需求：\n\n标题: {entry.title}\n内容: {entry.content or ''}"
    llm_response = await _call_llm(request, user, system_prompt, user_message)

    if not llm_response:
        return {
            "entry_id": entry_id,
            "analysis": {},
            "message": "AI 服务暂不可用",
            "raw_response": None,
        }

    analysis = _extract_json(llm_response, expect_list=False)

    return {
        "entry_id": entry_id,
        "analysis": analysis,
        "raw_response": llm_response,
    }


@router.post('/entries/{entry_id}/generate-testcases')
async def generate_testcases(
    request: Request,
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    system_prompt = (
        "你是测试专家。根据需求生成测试用例，包含功能测试、边界测试、异常测试。"
        "返回 JSON 格式的测试用例列表。每个用例包含："
        "name, type(functional/boundary/exception), steps, expectedResult, priority"
    )
    user_message = f"请根据以下需求生成测试用例：\n\n标题: {entry.title}\n内容: {entry.content or ''}"
    llm_response = await _call_llm(request, user, system_prompt, user_message)

    if not llm_response:
        return {
            "entry_id": entry_id,
            "testcases": [],
            "message": "AI 服务暂不可用",
            "raw_response": None,
        }

    testcases = _extract_json(llm_response, expect_list=True)

    return {
        "entry_id": entry_id,
        "testcases": testcases,
        "raw_response": llm_response,
    }


@router.post('/entries/{entry_id}/generate')
async def generate_content(
    request: Request,
    entry_id: str,
    form_data: PMGenerateRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    module_type = form_data.module_type
    if module_type == 'prd':
        system_prompt = (
            "你是 PRD 生成专家。根据需求大纲生成完整 PRD 文档，"
            "包含：概述、背景、目标、功能需求、非功能需求、附录"
        )
    elif module_type == 'requirement':
        system_prompt = (
            "你是需求梳理专家。根据描述梳理结构化需求，"
            "包含：需求ID、名称、描述、验收标准、优先级"
        )
    elif module_type == 'testcase':
        system_prompt = (
            "你是测试专家。根据需求生成测试用例，包含功能测试、边界测试、异常测试。"
            "返回 JSON 格式的测试用例列表。每个用例包含："
            "name, type(functional/boundary/exception), steps, expectedResult, priority"
        )
    else:
        system_prompt = (
            "你是内容生成专家。根据需求生成结构化内容。"
        )

    instructions = form_data.instructions or ''
    user_message = (
        f"请生成 {module_type} 类型的内容：\n\n"
        f"标题: {entry.title}\n内容: {entry.content or ''}\n"
        f"额外指令: {instructions}"
    )
    llm_response = await _call_llm(request, user, system_prompt, user_message)

    if not llm_response:
        return {
            "entry_id": entry_id,
            "generated_content": None,
            "module_type": module_type,
            "message": "AI 服务暂不可用",
            "raw_response": None,
        }

    generated_content = _extract_json(llm_response, expect_list=False)
    if not generated_content:
        generated_content = llm_response

    return {
        "entry_id": entry_id,
        "generated_content": generated_content,
        "module_type": module_type,
        "raw_response": llm_response,
    }


@router.post('/entries/{entry_id}/check')
async def check_entry(
    request: Request,
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    system_prompt = (
        "你是 PRD 质量检查专家。检查文档的完整性、一致性、可测试性，返回检查结果。"
        "JSON 格式：{score(0-100), issues: [{severity, category, message, suggestion}], summary}"
    )
    user_message = f"请检查以下文档：\n\n标题: {entry.title}\n内容: {entry.content or ''}"
    llm_response = await _call_llm(request, user, system_prompt, user_message)

    if not llm_response:
        return {
            "entry_id": entry_id,
            "check_result": {},
            "message": "AI 服务暂不可用",
            "raw_response": None,
        }

    check_result = _extract_json(llm_response, expect_list=False)

    return {
        "entry_id": entry_id,
        "check_result": check_result,
        "raw_response": llm_response,
    }


@router.get('/projects/{project_id}/workflow/next')
async def workflow_next(
    request: Request,
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    status_counts = {}
    module_counts = {}
    for entry in entries:
        status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
        module_counts[entry.module_type] = module_counts.get(entry.module_type, 0) + 1

    system_prompt = (
        "你是 PM 工作流专家。基于项目当前状态，建议下一步操作。"
        "返回 JSON：{current_phase, next_steps: [{action, module_type, reason, priority}], blocked: [{reason, dependency}]}"
    )
    user_message = (
        f"项目状态分析：\n"
        f"总条目数: {len(entries)}\n"
        f"状态分布: {json.dumps(status_counts, ensure_ascii=False)}\n"
        f"模块分布: {json.dumps(module_counts, ensure_ascii=False)}\n"
        f"请建议下一步操作。"
    )
    llm_response = await _call_llm(request, user, system_prompt, user_message)

    if not llm_response:
        next_steps = []
        if any(e.status == 'draft' for e in entries):
            next_steps.append({
                "action": "review",
                "module_type": "requirement",
                "reason": "存在草稿状态的需求，建议先进行评审",
                "priority": "high",
            })
        if any(e.status == 'approved' for e in entries):
            next_steps.append({
                "action": "generate_prd",
                "module_type": "prd",
                "reason": "已批准的需求可以开始生成 PRD",
                "priority": "medium",
            })
        return {
            "project_id": project_id,
            "workflow": {
                "current_phase": "in_progress",
                "next_steps": next_steps,
                "blocked": [],
            },
            "message": "AI 服务暂不可用，返回基于规则的默认建议",
            "raw_response": None,
        }

    workflow = _extract_json(llm_response, expect_list=False)
    if not workflow:
        workflow = {"current_phase": "in_progress", "next_steps": [], "blocked": []}

    return {
        "project_id": project_id,
        "workflow": workflow,
        "raw_response": llm_response,
    }


@router.get('/projects/{project_id}/workflow/progress')
async def workflow_progress(
    project_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    total = len(entries)
    by_module = {}
    for entry in entries:
        mt = entry.module_type or 'unknown'
        if mt not in by_module:
            by_module[mt] = {"total": 0, "by_status": {}}
        by_module[mt]["total"] += 1
        by_module[mt]["by_status"][entry.status] = by_module[mt]["by_status"].get(entry.status, 0) + 1

    completion_rate = 0.0
    if total > 0:
        completed = sum(1 for e in entries if e.status in ('completed', 'done', 'approved'))
        completion_rate = round(completed / total, 2)

    milestones = []
    for mt, data in by_module.items():
        total_mt = data["total"]
        completed_mt = data["by_status"].get('completed', 0) + data["by_status"].get('done', 0) + data["by_status"].get('approved', 0)
        milestones.append({
            "module_type": mt,
            "total": total_mt,
            "completed": completed_mt,
            "rate": round(completed_mt / total_mt, 2) if total_mt > 0 else 0.0,
        })

    return {
        "project_id": project_id,
        "progress": {
            "total": total,
            "by_module": by_module,
            "completion_rate": completion_rate,
            "milestones": milestones,
        },
    }


############################
# Agent Workflows
############################

class WorkflowStep(BaseModel):
    id: str
    skillId: str
    inputs: dict
    outputs: dict
    condition: Optional[str] = None


class WorkflowRequest(BaseModel):
    id: str
    name: str
    steps: list[WorkflowStep]


@router.post('/agent/workflows/execute')
async def execute_workflow(
    request: Request,
    form_data: WorkflowRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Execute a workflow by running each step sequentially."""
    import ast
    results = []
    
    for step in form_data.steps:
        # Check condition safely — only supports simple boolean literals
        if step.condition:
            try:
                condition_met = ast.literal_eval(step.condition)
                if not isinstance(condition_met, bool):
                    condition_met = bool(condition_met)
                if not condition_met:
                    results.append({'stepId': step.id, 'status': 'skipped'})
                    continue
            except (ValueError, SyntaxError):
                # Cannot safely evaluate condition — skip step
                results.append({'stepId': step.id, 'status': 'skipped', 'reason': 'unsafe condition'})
                continue
        
        # Execute skill via _call_llm + skill helpers
        try:
            skill = SKILL_INSTANCES.get(step.skillId)
            if skill:
                user_msg = skill.build_user_message(
                    user_message=step.inputs.get('message', ''),
                    project_id=step.inputs.get('project_id', ''),
                    module_type=step.inputs.get('module_type'),
                    entry_id=step.inputs.get('entry_id'),
                    entry_title=step.inputs.get('entry_title'),
                    entry_content_summary=step.inputs.get('entry_content_summary'),
                    extra_data=step.inputs.get('extra_data'),
                )
                llm_response = await _call_llm(request, user, skill.system_prompt, user_msg)
                if llm_response:
                    result = skill.parse_response(llm_response)
                else:
                    result = {'message': skill.fallback_response(), 'actions': None}
                results.append({'stepId': step.id, 'status': 'completed', 'result': result})
            else:
                results.append({'stepId': step.id, 'status': 'failed', 'error': f'Skill {step.skillId} not found'})
        except Exception as e:
            results.append({'stepId': step.id, 'status': 'failed', 'error': str(e)})
    
    all_completed = all(r['status'] == 'completed' for r in results)
    return {
        'success': all_completed,
        'steps': results,
        'workflowId': form_data.id,
        'workflowName': form_data.name,
    }
