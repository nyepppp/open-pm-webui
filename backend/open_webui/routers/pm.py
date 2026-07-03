import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.constants import ERROR_MESSAGES
from open_webui.internal.db import get_async_session
from open_webui.models.pm import (
    PMEntries,
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
)
from open_webui.utils.auth import get_verified_user
from sqlalchemy.ext.asyncio import AsyncSession

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
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    if module_type:
        return await PMEntries.get_entries_by_project_and_module(project_id, module_type, db=db)
    return await PMEntries.get_entries_by_project_id(project_id, db=db)


@router.post('/projects/{project_id}/entries', response_model=PMEntryModel)
async def create_entry(
    project_id: str,
    form_data: PMEntryForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    form_data.project_id = project_id
    
    if not form_data.version_id:
        versions = await PMVersions.get_versions_by_project_id(project_id, db=db)
        if versions:
            form_data.version_id = versions[0].id
        else:
            version_form = PMVersionForm(
                project_id=project_id,
                version_number='v1.0',
                label='auto',
                description='Auto-created version for new entry'
            )
            version = await PMVersions.insert_new_version(version_form, user.id, db=db)
            if version:
                form_data.version_id = version.id
    
    entry = await PMEntries.insert_new_entry(user.id, form_data, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create entry')
    return entry


@router.get('/entries/{entry_id}', response_model=PMEntryModel)
async def get_entry(
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    return entry


@router.post('/entries/{entry_id}', response_model=PMEntryModel)
async def update_entry(
    entry_id: str,
    form_data: PMEntryUpdateForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    entry = await PMEntries.update_entry_by_id(entry_id, form_data, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    return entry


@router.delete('/entries/{entry_id}')
async def delete_entry(
    entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    await PMEntries.delete_entry_by_id(entry_id, db=db)
    return True
