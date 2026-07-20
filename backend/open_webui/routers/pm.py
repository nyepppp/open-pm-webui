import json
import logging
import io
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from open_webui.internal.db import get_async_session
from open_webui.models.pm import (
    PMEntries,
    PMEntry,
    PMEntryForm,
    PMEntryModel,
    PMEntryUpdateForm,
    PMModuleVersion,
    PMModuleVersionModel,
    PMModuleVersionForm,
    PMModuleVersions,
    PMProjects,
    PMProjectForm,
    PMProjectModel,
    PMProjectUpdateForm,
    PMVersions,
    PMVersionForm,
    PMVersionModel,
    PMRelation,
    PMRelationModel,
    DuplicateProjectNameError,
)
from open_webui.utils.auth import get_verified_user
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

# 复用 PM 导入导出 Tool 的扁平化/生成逻辑（这些方法不依赖 tool 的 HTTP 调用）
from open_webui.tools.pm_import_export_tool import (
    Tools as PMImportExportTool,
    MODULE_DISPLAY_NAMES,
    SUPPORTED_FORMATS,
)


class AgentChatRequest(BaseModel):
    message: str
    project_id: str
    module_type: Optional[str] = None
    entry_id: Optional[str] = None
    context: Optional[dict] = None
    # v15: session_id enables __event_emitter__ + __event_call__ for streaming
    # and 2-phase delete confirmation via standard chat loop protocol.
    session_id: Optional[str] = None


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

# PM Relation 类型白名单（与 PMRelation.relation_type 注释对齐，新增 traceable_to 用于流程图绑定）
ALLOWED_RELATION_TYPES = {'contains', 'references', 'derives', 'modifies', 'conflicts', 'traceable_to'}


############################
# Projects
############################


@router.get('/projects', response_model=list[PMProjectModel])
async def get_projects(
    include_archived: bool = False,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await PMProjects.get_projects_by_user_id(user.id, db=db, include_archived=include_archived)


@router.post('/projects', response_model=PMProjectModel)
async def create_project(
    form_data: PMProjectForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        project = await PMProjects.insert_new_project(user.id, form_data, db=db)
    except DuplicateProjectNameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    if not project:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create project')

    # D28: 自动创建初始项目版本 v1，让 versions 页面不再显示「0 个版本」空状态。
    # D39: 异常可见化 —— 拆分异常类型，DB 错误用 error 级别日志；区分「版本创建失败」与「版本已创建但项目未关联」。
    # K3: 日志加 [Bug2-Diag] 标签 + user_id + form_data dump，便于跨 Bug 检索。
    # 失败时不阻断项目创建（保持 D28 设计意图），前端 versions 页面有兜底自动补建（A2）。
    initial_version_form = PMVersionForm(
        project_id=project.id,
        version_number='v1',
        description='初始版本',
    )
    initial_version = None
    try:
        initial_version = await PMVersions.insert_new_version(initial_version_form, user.id, db=db)
    except SQLAlchemyError as e:
        log.error(
            '[Bug2-Diag] D28 DB error creating initial version: project_id=%s user_id=%s form=%s err=%s',
            project.id, user.id, initial_version_form.model_dump(), e,
            exc_info=True,
        )
    except ValueError as e:
        log.error(
            '[Bug2-Diag] D28 invalid form data creating initial version: project_id=%s user_id=%s form=%s err=%s',
            project.id, user.id, initial_version_form.model_dump(), e,
            exc_info=True,
        )
    except Exception as e:
        log.error(
            '[Bug2-Diag] D28 unexpected error creating initial version: project_id=%s user_id=%s form=%s err=%s',
            project.id, user.id, initial_version_form.model_dump(), e,
            exc_info=True,
        )

    if initial_version:
        # 把初始版本设为项目的当前激活版本，避免后续读取 current_version_id 为空
        try:
            await PMProjects.update_project_by_id(
                project.id,
                PMProjectUpdateForm(current_version_id=initial_version.id),
                db=db,
            )
            log.info(
                '[Bug2-Diag] D28 auto-created initial version v1: project_id=%s user_id=%s version_id=%s',
                project.id, user.id, initial_version.id,
            )
        except SQLAlchemyError as e:
            # 版本已创建但项目未关联 —— 数据不一致，需运维介入
            log.warning(
                '[Bug2-Diag] D28 version %s created for project %s but failed to link: user_id=%s err=%s',
                initial_version.id, project.id, user.id, e,
                exc_info=True,
            )
        except Exception as e:
            log.warning(
                '[Bug2-Diag] D28 version %s created for project %s but failed to link: user_id=%s err=%s',
                initial_version.id, project.id, user.id, e,
                exc_info=True,
            )

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
    try:
        project = await PMProjects.update_project_by_id(project_id, form_data, db=db)
    except DuplicateProjectNameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
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


class ProjectCurrentVersionForm(BaseModel):
    """切换项目当前激活版本的请求体。"""
    version_id: str


@router.put('/projects/{project_id}/current-version', response_model=dict)
async def set_project_current_version(
    project_id: str,
    form_data: ProjectCurrentVersionForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """设置项目当前激活的项目版本（pm_version.id）。

    校验：
    - 项目存在且属于当前用户
    - 指定的 version_id 属于该项目
    """
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

    version = await PMVersions.get_version_by_id(form_data.version_id, db=db)
    if not version or version.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Version does not belong to this project',
        )

    update_form = PMProjectUpdateForm(current_version_id=form_data.version_id)
    await PMProjects.update_project_by_id(project_id, update_form, db=db)
    return {
        'current_version_id': form_data.version_id,
        'version_number': version.version_number,
    }


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


async def _export_module_core(
    project_id: str,
    module_type: str,
    format: str,
    version_id: Optional[str],
    columns: Optional[list],
    entry_ids_filter: Optional[set],
    db: AsyncSession,
) -> StreamingResponse:
    """导出核心逻辑：GET 与 POST 端点共用。

    抽取为内部函数，避免 GET 端点（query 参数）与 POST 端点（JSON body）的参数解析逻辑重复。
    """
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的格式: {format}，支持: {SUPPORTED_FORMATS}",
        )

    # relation 模块走单独接口，本端点暂不支持（用户可通过对话入口触发 tool）
    if module_type in ('relation', 'relations'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='relation 模块请通过对话入口调用导出工具',
        )

    # 查 entries（按 module_type 过滤；version_id 暂不参与过滤，保持与 get_entries 行为一致）
    query = select(PMEntry).where(PMEntry.project_id == project_id)
    if module_type:
        query = query.where(PMEntry.module_type == module_type)
    query = query.order_by(PMEntry.updated_at.desc())
    result_rows = (await db.execute(query)).scalars().all()

    # 按 entry_ids 过滤（若提供）
    if entry_ids_filter:
        result_rows = [e for e in result_rows if str(e.id) in entry_ids_filter]

    # 转 dict（_entry_to_row 需要 dict 输入）
    entries_dicts = []
    for entry in result_rows:
        entry_model = PMEntryModel.model_validate(entry)
        entries_dicts.append(entry_model.model_dump(mode='json'))

    if not entries_dicts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 的「{MODULE_DISPLAY_NAMES.get(module_type, module_type)}」模块没有条目可导出",
        )

    # 复用 tool 的扁平化与子类型拆分逻辑（透传 columns 控制列顺序）
    tool = PMImportExportTool()
    sheets = tool._split_entries_by_subtype(entries_dicts, module_type, columns)

    display_name = MODULE_DISPLAY_NAMES.get(module_type, module_type)
    filename_base = f"{module_type}_{project_id[:8] if project_id else 'unknown'}"

    if format == 'xlsx':
        content_bytes = tool._generate_xlsx_bytes(sheets, columns=columns)
        filename = f"{display_name}_{filename_base}.xlsx"
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif format == 'csv':
        if len(sheets) == 1:
            single_rows = next(iter(sheets.values()))
            content_bytes = tool._generate_csv_string(single_rows, columns=columns).encode('utf-8')
            filename = f"{display_name}_{filename_base}.csv"
            media_type = 'text/csv'
        else:
            content_bytes = tool._generate_csv_zip_bytes(sheets, columns=columns)
            filename = f"{display_name}_{filename_base}.zip"
            media_type = 'application/zip'
    elif format == 'markdown':
        content_bytes = tool._generate_markdown_bytes(sheets, module_type, columns=columns)
        filename = f"{display_name}_{filename_base}.md"
        media_type = 'text/markdown'
    elif format == 'docx':
        try:
            content_bytes = tool._generate_docx_bytes(sheets, module_type, columns=columns)
        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )
        filename = f"{display_name}_{filename_base}.docx"
        media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    else:  # json
        meta = {
            'project_id': project_id,
            'module_type': module_type,
            'display_name': display_name,
            'total_entries': len(entries_dicts),
            'sheets': {k: len(v) for k, v in sheets.items()},
        }
        content_bytes = tool._generate_json_bytes(sheets, meta=meta)
        filename = f"{display_name}_{filename_base}.json"
        media_type = 'application/json'

    # 用 URL-encoded 文件名支持中文
    from urllib.parse import quote
    quoted_filename = quote(filename)

    return StreamingResponse(
        io.BytesIO(content_bytes),
        media_type=media_type,
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{quoted_filename}",
        },
    )


@router.get('/projects/{project_id}/modules/{module_type}/export')
async def export_module(
    project_id: str,
    module_type: str,
    format: str = 'xlsx',
    version_id: Optional[str] = None,
    columns_json: Optional[str] = None,
    entry_ids_json: Optional[str] = None,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """按模块批量导出 entries 为 xlsx/csv/json/markdown/docx 文件流（GET，向后兼容）。

    复用 PMImportExportTool 的扁平化与生成逻辑（_entry_to_row / _split_entries_by_subtype /
    _generate_xlsx_bytes / _generate_markdown_bytes / _generate_docx_bytes 等），
    但不走 tool 的 HTTP 上传流程，直接返回文件流。

    :param columns_json: 可选，JSON 字符串数组，形如
        [{"key": "title", "label": "标题"}, {"key": "data.priority", "label": "优先级"}]。
        控制导出列顺序与表头标签；为 None 时使用默认列。
    :param entry_ids_json: 可选，JSON 字符串数组，形如 ["id1", "id2"]。
        仅导出指定 ID 的条目；为 None 时导出全部。

    注意：GET 受 URL 长度限制（8K-32K），条目 ID 列表过长时浏览器会抛
    "Failed to fetch"。请优先使用 POST 同路径端点。
    """
    # 解析 columns_json
    columns: Optional[list] = None
    if columns_json:
        try:
            parsed = json.loads(columns_json)
            if isinstance(parsed, list):
                columns = parsed
        except Exception as e:
            log.warning(f'export_module: invalid columns_json: {e}')

    # 解析 entry_ids_json
    entry_ids_filter: Optional[set] = None
    if entry_ids_json:
        try:
            ids_list = json.loads(entry_ids_json)
            if isinstance(ids_list, list) and len(ids_list) > 0:
                entry_ids_filter = set(str(i) for i in ids_list)
        except Exception as e:
            log.warning(f'export_module: invalid entry_ids_json: {e}')

    return await _export_module_core(
        project_id, module_type, format, version_id, columns, entry_ids_filter, db
    )


class ExportModuleRequest(BaseModel):
    """POST /export 请求体。

    用 POST + JSON body 替代 GET + URL query，避免条目 ID 列表过长
    触发浏览器 URL 长度限制导致 "Failed to fetch"。
    """

    format: str = 'xlsx'
    version_id: Optional[str] = None
    columns: Optional[list] = None
    entry_ids: Optional[list[str]] = None


@router.post('/projects/{project_id}/modules/{module_type}/export')
async def export_module_post(
    project_id: str,
    module_type: str,
    body: ExportModuleRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """按模块批量导出（POST，推荐）。

    与 GET 端点功能等价，参数改为 JSON body 传输：
    - format: xlsx / csv / json / markdown / docx
    - version_id: 可选，版本 ID
    - columns: 可选，列定义数组 [{"key": "title", "label": "标题"}]
    - entry_ids: 可选，条目 ID 数组 ["id1", "id2"]

    优势：无 URL 长度限制，适合大量条目筛选场景。
    """
    columns = body.columns if isinstance(body.columns, list) else None
    entry_ids_filter: Optional[set] = None
    if body.entry_ids and isinstance(body.entry_ids, list) and len(body.entry_ids) > 0:
        entry_ids_filter = set(str(i) for i in body.entry_ids)

    return await _export_module_core(
        project_id, module_type, body.format, body.version_id, columns, entry_ids_filter, db
    )


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

    # 自动填充 project_version_id：若前端未显式传入，则取项目当前激活版本
    if not form_data.project_version_id:
        project = await PMProjects.get_project_by_id(project_id, db=db)
        if project and getattr(project, 'current_version_id', None):
            form_data.project_version_id = project.current_version_id

    # 若仍无 project_version_id，尝试从 data.versionId 回填
    # （覆盖项目尚未设置 current_version_id 但前端已写入 data.versionId 的场景）
    if not form_data.project_version_id and form_data.data:
        data_vid = form_data.data.get('versionId')
        if isinstance(data_vid, str) and data_vid:
            form_data.project_version_id = data_vid

    # 同步写入 data.versionId 以兼容前端旧代码（前端仍从 data.versionId 读取展示）
    if form_data.project_version_id:
        form_data.data = form_data.data or {}
        form_data.data['versionId'] = form_data.project_version_id

    # 功能/参数级自动绑定 module_version_id：
    # 从 data.moduleId 反查父模块 entry 的 module_version_id，回填到 form_data。
    # 满足用户需求"每次新建自动关联上对应版本"。
    if form_data.module_type == 'product-architecture' and not form_data.module_version_id:
        data_dict = form_data.data or {}
        entry_type = data_dict.get('type')
        if entry_type in ('feature', 'parameter'):
            parent_module_id = data_dict.get('moduleId') or data_dict.get('module_entry_id')
            if parent_module_id:
                try:
                    parent_result = await db.execute(
                        select(PMEntry).where(PMEntry.id == parent_module_id)
                    )
                    parent_entry = parent_result.scalar_one_or_none()
                    if parent_entry and parent_entry.module_version_id:
                        form_data.module_version_id = parent_entry.module_version_id
                except Exception as e:
                    log.warning(
                        f'create_entry: failed to inherit module_version_id from parent {parent_module_id}: {e}'
                    )

    entry = await PMEntries.insert_new_entry(user.id, form_data, db=db)
    if not entry:
        # 记录日志便于排查：PMEntries.insert_new_entry 返回 None 表示创建失败
        log.error(f'create_entry: insert_new_entry returned None for project_id={project_id}, title={form_data.title}, module_type={form_data.module_type}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create entry')

    # 加固契约：响应体必须含 id 字段，否则前端无法回填虚拟 ID
    if not getattr(entry, 'id', None):
        log.error(f'create_entry: entry has no id after insert, project_id={project_id}, title={form_data.title}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Created entry is missing id field')

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
        log.error(f'Failed to auto-create entry version for entry {entry.id}: {e}', exc_info=True)

    # 若是模块条目（module_type='product-architecture' 且 data.type='module'），
    # 自动创建 PMModuleVersion v1 并回填 entry.module_version_id。
    # 注意：这与 PMEntryVersion（条目级修订）和 PMVersion（项目版本）是三个独立的概念。
    if form_data.module_type == 'product-architecture' and (form_data.data or {}).get('type') == 'module':
        try:
            module_version_form = PMModuleVersionForm(
                module_entry_id=entry.id,
                version_number='v1',
                change_summary='Initial module version',
                project_id=project_id,
                project_version_id=form_data.project_version_id,
            )
            new_module_version = await PMModuleVersions.insert_new_version(user.id, module_version_form, db=db)
            if new_module_version:
                await db.execute(
                    update(PMEntry)
                    .where(PMEntry.id == entry.id)
                    .values(module_version_id=new_module_version.id)
                )
                await db.commit()
                # 同步到响应对象
                entry.module_version_id = new_module_version.id
        except Exception as e:
            log.error(f'Failed to auto-create module version for entry {entry.id}: {e}', exc_info=True)

    # Enrich response with version info
    entry_response = PMEntryModel.model_validate(entry)
    entry_response.current_version_number = 'v1'
    entry_response.branch_name = 'main'
    entry_response.created_version_number = entry_response.created_version_number or 'v1'
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

    # 补绑 module_version_id：处理历史数据（在 create_entry 自动绑定修复前创建的
    # 功能/参数 entry 没有绑定 module_version_id），在用户修改时反查父模块当前版本回填。
    # 只在 entry.module_version_id 为 None 且 form_data 未显式传入时补绑。
    if (
        not entry.module_version_id
        and not getattr(form_data, 'module_version_id', None)
        and entry.module_type == 'product-architecture'
    ):
        data_dict = entry.data or {}
        entry_type = data_dict.get('type')
        if entry_type in ('feature', 'parameter'):
            parent_module_id = data_dict.get('moduleId') or data_dict.get('module_entry_id')
            if parent_module_id:
                try:
                    parent_result = await db.execute(
                        select(PMEntry).where(PMEntry.id == parent_module_id)
                    )
                    parent_entry = parent_result.scalar_one_or_none()
                    if parent_entry and parent_entry.module_version_id:
                        form_data.module_version_id = parent_entry.module_version_id
                except Exception as e:
                    log.warning(
                        f'update_entry: failed to backfill module_version_id for entry {entry_id}: {e}'
                    )

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
    form_data: dict = Body(...),
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMEntryVersions, PMEntryVersionForm
    import time  # D22: 需要 time.time_ns() 取纳秒时间戳
    # Get current entry to snapshot
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')

    # D20: 修复版本号碰撞 — 基于 MAX(version_number) 解析数字 +1
    # 旧实现 `f'v{len(existing) + 1}'` 在删除历史版本后会与已有版本号碰撞
    existing = await PMEntryVersions.get_versions_by_entry_id(entry_id, db=db)
    if form_data.get('version_number'):
        version_number = form_data['version_number']
    else:
        max_num = 0
        for v in existing:
            try:
                # 兼容 'v1' / '1' / 'v1.0' 等格式
                num_str = (v.version_number or '').lstrip('v').split('.')[0]
                num = int(num_str) if num_str.isdigit() else 0
                if num > max_num:
                    max_num = num
            except (ValueError, AttributeError):
                continue
        version_number = f'v{max_num + 1}'

    # D21: 修复 parent_id — 自动填充上一版本 ID，建立版本链
    # 旧实现从不传 parent_id，版本树断裂无法追溯
    parent_id = form_data.get('parent_id')
    if not parent_id and existing:
        # 取 created_at 最新的版本作为父版本
        sorted_existing = sorted(existing, key=lambda v: v.created_at or 0, reverse=True)
        if sorted_existing:
            parent_id = sorted_existing[0].id

    # D22: 修复时间戳量纲 — 统一用 time.time_ns() 与 created_at 一致
    # 旧实现用 int(time.time()) 秒级，与 models/pm.py 的 created_at 纳秒级不一致
    version_form = PMEntryVersionForm(
        entry_id=entry_id,
        project_id=project_id,
        module_type=entry.module_type,
        version_number=version_number,
        content=entry.content,
        entry_metadata={
            'data_snapshot': entry.data,          # 完整 data JSON 副本
            'snapshot_at': int(time.time_ns()),    # 快照时间戳（纳秒，与 created_at 一致）
        },
        parent_id=parent_id,
        branch_name=form_data.get('branch_name', 'main'),
        change_summary=form_data.get('change_summary', ''),
        project_version_id=form_data.get('project_version_id'),
    )
    # K1d: 包裹 insert_new_version —— DB 异常不再静默冒泡为 500，记录 [Bug1-Diag] 后 re-raise
    try:
        version = await PMEntryVersions.insert_new_version(user.id, version_form, db=db)
    except SQLAlchemyError as e:
        log.exception(
            '[Bug1-Diag] create_entry_version DB error: entry_id=%s project_id=%s version_number=%s',
            entry_id, project_id, version_number,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'DB error creating entry version: {e}',
        ) from e
    except Exception as e:
        log.exception(
            '[Bug1-Diag] create_entry_version unexpected error: entry_id=%s project_id=%s version_number=%s',
            entry_id, project_id, version_number,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Unexpected error creating entry version: {e}',
        ) from e
    if not version:
        log.error(
            '[Bug1-Diag] create_entry_version returned None: entry_id=%s project_id=%s version_number=%s',
            entry_id, project_id, version_number,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create entry version (insert returned None)',
        )
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

    # 向后兼容：新格式 entry_metadata={'data_snapshot': ..., 'snapshot_at': ...}；旧格式直接是 data
    metadata = version.entry_metadata
    if isinstance(metadata, dict) and 'data_snapshot' in metadata:
        data_to_restore = metadata.get('data_snapshot')
    else:
        data_to_restore = metadata

    # Restore entry content from version
    await PMEntries.update_entry_by_id(
        entry_id,
        PMEntryUpdateForm(content=version.content, data=data_to_restore),
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
    'idea_to_prd': {
        'id': 'idea_to_prd',
        'name': 'Idea → PRD',
        'description': '从创意出发，经过需求分析和多角色评审，生成PRD文档',
        'input_module': 'requirement',
        'output_module': 'prd',
        'steps': [
            {'action': 'analyze_requirements', 'description': 'AI分析需求分类、优先级和冲突', 'skill': 'requirement-analysis'},
            {'action': 'review_requirements', 'description': '多角色评审需求完整性', 'skill': 'requirement-review'},
            {'action': 'generate_prd', 'description': '根据评审结果生成PRD文档', 'skill': 'prd-generation'},
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


async def _flow_idea_to_prd(
    source_entry_ids: list[str], project_id: str, user, request: Request, db: AsyncSession,
) -> dict:
    """Flow: Idea → Requirement Analysis → Multi-role Review → PRD Generation."""
    from open_webui.pm.skills.requirement_analysis import RequirementAnalysisSkill
    from open_webui.pm.skills.requirement_review import RequirementReviewSkill
    from open_webui.pm.skills.prd_generation import PRDGenerationSkill

    step_results = []
    all_entries = []
    all_relations = []

    # 1. Fetch source requirement entries
    source_entries = []
    for eid in source_entry_ids:
        entry = await PMEntries.get_entry_by_id(eid, db=db)
        if entry:
            source_entries.append(entry)

    if not source_entries:
        return {'created_entries': [], 'created_relations': [], 'step_results': [], 'error': 'No source entries found'}

    req_summary = '\n'.join([f'- {e.title}: {(e.content or "")[:300]}' for e in source_entries])
    combined_titles = ', '.join([e.title for e in source_entries])

    # 2. Step 1: Requirement Analysis
    analysis_skill = RequirementAnalysisSkill()
    analysis_msg = analysis_skill.build_user_message(
        user_message=f'请分析以下需求：\n\n{req_summary}',
        project_id=project_id,
    )
    analysis_response = await _call_llm(request, user, analysis_skill.system_prompt, analysis_msg)
    analysis_content = analysis_response or ''

    # Create analysis entry
    analysis_entry = await _create_entry_with_entity(
        user=user, project_id=project_id, module_type='requirement',
        title=f'需求分析 - {combined_titles}', content=analysis_content,
        data={'source': 'ai_flow', 'flow_template': 'idea_to_prd', 'step': 'analysis'},
        db=db,
    )
    if analysis_entry:
        all_entries.append(PMEntryModel.model_validate(analysis_entry).model_dump() if isinstance(analysis_entry, PMEntry) else analysis_entry)
        # Derives from source entries
        for src_entry in source_entries:
            src_entity_id = await _find_entity_by_entry_id(src_entry.id, db)
            tgt_entity_id = await _find_entity_by_entry_id(analysis_entry.id, db)
            if src_entity_id and tgt_entity_id:
                relation = await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
                if relation:
                    all_relations.append(relation)

    step_results.append({'action': 'analyze_requirements', 'status': 'completed', 'entry_id': analysis_entry.id if analysis_entry else None})

    # 3. Step 2: Multi-role Requirement Review
    review_skill = RequirementReviewSkill()
    review_msg = review_skill.build_user_message(
        user_message=f'请评审以下需求（含分析结果）：\n\n原始需求：\n{req_summary}\n\n分析结果：\n{analysis_content[:500]}',
        project_id=project_id,
    )
    review_response = await _call_llm(request, user, review_skill.system_prompt, review_msg)
    review_content = review_response or ''

    review_entry = await _create_entry_with_entity(
        user=user, project_id=project_id, module_type='requirement',
        title=f'需求评审 - {combined_titles}', content=review_content,
        data={'source': 'ai_flow', 'flow_template': 'idea_to_prd', 'step': 'review'},
        db=db,
    )
    if review_entry:
        all_entries.append(PMEntryModel.model_validate(review_entry).model_dump() if isinstance(review_entry, PMEntry) else review_entry)
        if analysis_entry:
            src_entity_id = await _find_entity_by_entry_id(analysis_entry.id, db)
            tgt_entity_id = await _find_entity_by_entry_id(review_entry.id, db)
            if src_entity_id and tgt_entity_id:
                relation = await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
                if relation:
                    all_relations.append(relation)

    step_results.append({'action': 'review_requirements', 'status': 'completed', 'entry_id': review_entry.id if review_entry else None})

    # 4. Step 3: PRD Generation (using review results)
    prd_skill = PRDGenerationSkill()
    prd_msg = prd_skill.build_user_message(
        user_message=f'请根据以下需求和评审结果生成PRD：\n\n原始需求：\n{req_summary}\n\n评审结果：\n{review_content[:500]}',
        project_id=project_id,
    )
    prd_response = await _call_llm(request, user, prd_skill.system_prompt, prd_msg)
    prd_content = prd_response or ''

    prd_title = f'PRD - {combined_titles}'
    prd_data = None
    if prd_response:
        parsed = _extract_json(prd_response, expect_list=False)
        if parsed and isinstance(parsed, dict):
            prd_title = parsed.get('title', prd_title)
            prd_content = parsed.get('content', prd_response)
            prd_data = parsed

    prd_entry = await _create_entry_with_entity(
        user=user, project_id=project_id, module_type='prd',
        title=prd_title, content=prd_content, data=prd_data,
        db=db,
    )
    if prd_entry:
        all_entries.append(PMEntryModel.model_validate(prd_entry).model_dump() if isinstance(prd_entry, PMEntry) else prd_entry)
        # Derives from source entries and review
        for src_entry in source_entries:
            src_entity_id = await _find_entity_by_entry_id(src_entry.id, db)
            tgt_entity_id = await _find_entity_by_entry_id(prd_entry.id, db)
            if src_entity_id and tgt_entity_id:
                relation = await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
                if relation:
                    all_relations.append(relation)

    step_results.append({'action': 'generate_prd', 'status': 'completed', 'entry_id': prd_entry.id if prd_entry else None})

    return {
        'created_entries': all_entries,
        'created_relations': all_relations,
        'step_results': step_results,
        'prd_entry_id': prd_entry.id if prd_entry else None,
    }
FLOW_EXECUTORS = {
    'requirement_to_parameter': _flow_requirement_to_parameter,
    'requirement_to_prd': _flow_requirement_to_prd,
    'prd_to_parameter': _flow_prd_to_parameter,
    'parameter_to_testcase': _flow_parameter_to_testcase,
    'full_chain': _flow_full_chain,
    'idea_to_prd': _flow_idea_to_prd,
}


# ============================================================================
# Module Versions — 产品架构模块多版本管理
# 一个 module entry（module_type='product-architecture' 且 node_type='module'）
# 可以有多个版本。module/feature/parameter entry 通过 module_version_id 绑定。
# ============================================================================


@router.post(
    '/projects/{project_id}/modules/{module_entry_id}/versions',
    response_model=PMModuleVersionModel,
)
async def create_module_version(
    project_id: str,
    module_entry_id: str,
    form: PMModuleVersionForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """创建模块版本。version_number 由前端传，例如 'v1', 'v1.1'。

    新建后自动切换为活动版本：把该模块下所有 entry 的 module_version_id
    更新为新版本 ID。满足用户需求"每次新建自动关联上对应版本"。
    """
    if form.module_entry_id != module_entry_id:
        raise HTTPException(status_code=400, detail='module_entry_id mismatch')
    if not form.project_id:
        form.project_id = project_id
    elif form.project_id != project_id:
        raise HTTPException(status_code=400, detail='project_id mismatch')
    version = await PMModuleVersions.insert_new_version(user.id, form, db)
    # 自动切换活动版本到新建版本
    if version:
        try:
            await _apply_module_version_switch(project_id, module_entry_id, version.id, db)
        except Exception as e:
            log.warning(
                f'create_module_version: auto-switch failed for version {version.id}: {e}'
            )
    return version


async def _apply_module_version_switch(
    project_id: str,
    module_entry_id: str,
    version_id: str,
    db: AsyncSession,
) -> list[str]:
    """把指定模块下所有 entry 的 module_version_id 更新为 version_id。

    匹配范围：module/feature/parameter entry 中 data.moduleId 或 data.parentId
    等于 module_entry_id 的，全部更新 module_version_id。

    抽取为内部函数供 create_module_version（自动切换）和 switch_module_version
    （手动切换）共用，避免逻辑重复。
    """
    stmt = select(PMEntry).where(
        PMEntry.project_id == project_id,
        (PMEntry.module_type == 'product-architecture')
        | (PMEntry.module_type == 'parameter'),
    )
    result = await db.execute(stmt)
    all_entries = result.scalars().all()

    updated_ids: list[str] = []
    for entry in all_entries:
        data = entry.data or {}
        mid = data.get('moduleId') or data.get('module_entry_id')
        pid = data.get('parentId')
        if entry.id == module_entry_id:
            should_update = True
        elif mid == module_entry_id or pid == module_entry_id:
            should_update = True
        else:
            should_update = False
        if should_update:
            await db.execute(
                update(PMEntry)
                .where(PMEntry.id == entry.id)
                .values(module_version_id=version_id)
            )
            updated_ids.append(entry.id)

    await db.commit()
    return updated_ids


@router.get(
    '/projects/{project_id}/modules/{module_entry_id}/versions',
    response_model=list[PMModuleVersionModel],
)
async def list_module_versions(
    project_id: str,
    module_entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """列出指定模块的所有版本，按 created_at 降序。"""
    return await PMModuleVersions.get_versions_by_module_entry_id(module_entry_id, db)


@router.post(
    '/projects/{project_id}/modules/{module_entry_id}/versions/{version_id}/switch',
    response_model=dict,
)
async def switch_module_version(
    project_id: str,
    module_entry_id: str,
    version_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """切换当前模块版本：把该模块下所有 entry 的 module_version_id 更新为 version_id。

    匹配范围：module/feature/parameter entry 中 data.moduleId 或 data.parentId
    等于 module_entry_id 的，全部更新 module_version_id。
    """
    version = await PMModuleVersions.get_version_by_id(version_id, db)
    if not version or version.module_entry_id != module_entry_id:
        raise HTTPException(status_code=404, detail='Module version not found')
    if version.project_id != project_id:
        raise HTTPException(status_code=400, detail='project_id mismatch')

    updated_ids = await _apply_module_version_switch(
        project_id, module_entry_id, version_id, db
    )
    return {
        'version_id': version_id,
        'updated_entry_ids': updated_ids,
        'count': len(updated_ids),
    }


@router.delete(
    '/projects/{project_id}/modules/{module_entry_id}/versions/{version_id}',
    response_model=bool,
)
async def delete_module_version(
    project_id: str,
    module_entry_id: str,
    version_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """删除模块版本。删除前应确认没有 entry 仍绑定到此版本。"""
    return await PMModuleVersions.delete_version_by_id(version_id, db)


@router.get(
    '/projects/{project_id}/modules/{module_entry_id}/versions/span',
    response_model=dict,
)
async def get_module_version_span(
    project_id: str,
    module_entry_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """计算指定模块的版本跨度：该模块下所有 feature/parameter entry 出现过的不同 module_version_id 数量。

    用于 UI 展示"版本跨度：X 个版本"，帮助用户理解一个功能/参数跨了多少个模块版本。
    """
    stmt = select(PMEntry).where(
        PMEntry.project_id == project_id,
        (PMEntry.module_type == 'product-architecture') | (PMEntry.module_type == 'parameter'),
    )
    result = await db.execute(stmt)
    all_entries = result.scalars().all()

    feature_versions: set = set()
    parameter_versions: set = set()
    for entry in all_entries:
        data = entry.data or {}
        mid = data.get('moduleId') or data.get('module_entry_id')
        pid = data.get('parentId')
        # 匹配：entry 自身是模块 / data.moduleId 指向模块 / data.parentId 指向模块
        if entry.id == module_entry_id or mid == module_entry_id or pid == module_entry_id:
            if entry.module_version_id:
                node_type = data.get('node_type') or data.get('type')
                if node_type == 'parameter' or entry.module_type == 'parameter':
                    parameter_versions.add(entry.module_version_id)
                else:
                    feature_versions.add(entry.module_version_id)
    return {'featureSpan': len(feature_versions), 'parameterSpan': len(parameter_versions)}


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
# Architecture Auto-Extract & Sync
############################


class ArchitectureAutoExtractRequest(BaseModel):
    version_id: Optional[str] = None


class ArchitectureSyncRequest(BaseModel):
    version_id: Optional[str] = None
    apply: bool = False


def _build_architecture_nodes(entries: list[PMEntry], project_id: str) -> list[dict]:
    """Build architecture MindMapNode tree from project entries grouped by module_type."""
    import time
    import uuid

    by_module: dict[str, list[PMEntry]] = {}
    for entry in entries:
        mt = entry.module_type or 'unknown'
        if mt not in by_module:
            by_module[mt] = []
        by_module[mt].append(entry)

    nodes: list[dict] = []
    root_id = str(uuid.uuid4())
    now = int(time.time() * 1000)

    nodes.append({
        'id': root_id,
        'projectId': project_id,
        'parentId': None,
        'label': 'Product Architecture',
        'type': 'root',
        'position': {'x': 0, 'y': 0},
        'metadata': {},
        'createdAt': now,
        'updatedAt': now,
    })

    branch_x = 0
    for module_type, module_entries in by_module.items():
        branch_id = str(uuid.uuid4())
        nodes.append({
            'id': branch_id,
            'projectId': project_id,
            'parentId': root_id,
            'label': module_type,
            'type': 'branch',
            'position': {'x': branch_x, 'y': 200},
            'metadata': {'moduleType': module_type, 'entryCount': len(module_entries)},
            'createdAt': now,
            'updatedAt': now,
        })

        leaf_x = branch_x
        for entry in module_entries:
            leaf_id = str(uuid.uuid4())
            version_id = None
            if entry.data and isinstance(entry.data, dict):
                version_id = entry.data.get('versionId')

            nodes.append({
                'id': leaf_id,
                'projectId': project_id,
                'parentId': branch_id,
                'label': entry.title or 'Untitled',
                'type': 'leaf',
                'position': {'x': leaf_x, 'y': 400},
                'metadata': {
                    'moduleType': module_type,
                    'entryId': entry.id,
                    'status': entry.status,
                    'priority': entry.priority,
                    **({'versionId': version_id} if version_id else {}),
                },
                'moduleRef': entry.id,
                'createdAt': now,
                'updatedAt': now,
            })
            leaf_x += 200

        branch_x += 400

    return nodes


def _diff_architecture_nodes(old_nodes: list[dict], new_nodes: list[dict]) -> dict:
    """Compare old and new architecture nodes, returning added/removed/modified."""
    old_by_label = {n['label']: n for n in old_nodes if n.get('type') == 'leaf'}
    new_by_label = {n['label']: n for n in new_nodes if n.get('type') == 'leaf'}

    old_labels = set(old_by_label.keys())
    new_labels = set(new_by_label.keys())

    added = [new_by_label[l] for l in new_labels - old_labels]
    removed = [old_by_label[l] for l in old_labels - new_labels]
    modified = []
    for label in old_labels & new_labels:
        old_n = old_by_label[label]
        new_n = new_by_label[label]
        if old_n.get('metadata', {}).get('moduleType') != new_n.get('metadata', {}).get('moduleType'):
            modified.append(new_n)
        elif old_n.get('moduleRef') != new_n.get('moduleRef'):
            modified.append(new_n)

    return {'added': added, 'removed': removed, 'modified': modified}


@router.post('/projects/{project_id}/architecture/auto-extract')
async def auto_extract_architecture(
    project_id: str,
    form_data: ArchitectureAutoExtractRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    query = select(PMEntry).where(
        PMEntry.project_id == project_id,
    ).order_by(PMEntry.module_type, PMEntry.updated_at.desc())

    if form_data.version_id:
        from open_webui.models.pm import PMEntryVersion
        ver_query = select(PMEntryVersion.entry_id).where(
            PMEntryVersion.project_version_id == form_data.version_id,
        )
        ver_result = await db.execute(ver_query)
        entry_ids = [r for r in ver_result.scalars().all()]
        if entry_ids:
            query = query.where(PMEntry.id.in_(entry_ids))

    result = await db.execute(query)
    entries = result.scalars().all()

    nodes = _build_architecture_nodes(list(entries), project_id)

    existing_arch = await _create_entry_with_entity(
        user=user,
        project_id=project_id,
        module_type='product-architecture',
        title='Product Architecture (Auto-Extracted)',
        content=json.dumps({'nodes': nodes}, ensure_ascii=False),
        data={
            'autoExtracted': True,
            'nodeCount': len(nodes),
            'versionId': form_data.version_id,
        },
        db=db,
    )

    return {
        'entry_id': existing_arch.id if existing_arch else None,
        'nodes': nodes,
        'auto_extracted': True,
    }


@router.post('/projects/{project_id}/architecture/sync')
async def sync_architecture(
    project_id: str,
    form_data: ArchitectureSyncRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    project = await PMProjects.get_project_by_id(project_id, db=db)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    query = select(PMEntry).where(
        PMEntry.project_id == project_id,
        PMEntry.module_type == 'product-architecture',
    ).order_by(PMEntry.updated_at.desc())
    result = await db.execute(query)
    existing_entries = result.scalars().all()

    old_nodes = []
    existing_entry = existing_entries[0] if existing_entries else None
    if existing_entry and existing_entry.data:
        old_nodes = (existing_entry.data or {}).get('nodes', [])
    elif existing_entry and existing_entry.content:
        parsed = _extract_json(existing_entry.content, expect_list=False)
        if parsed and isinstance(parsed, dict):
            old_nodes = parsed.get('nodes', [])

    entries_query = select(PMEntry).where(
        PMEntry.project_id == project_id,
    ).order_by(PMEntry.module_type, PMEntry.updated_at.desc())

    if form_data.version_id:
        from open_webui.models.pm import PMEntryVersion
        ver_query = select(PMEntryVersion.entry_id).where(
            PMEntryVersion.project_version_id == form_data.version_id,
        )
        ver_result = await db.execute(ver_query)
        entry_ids = [r for r in ver_result.scalars().all()]
        if entry_ids:
            entries_query = entries_query.where(PMEntry.id.in_(entry_ids))

    entries_result = await db.execute(entries_query)
    all_entries = entries_result.scalars().all()

    new_nodes = _build_architecture_nodes(list(all_entries), project_id)
    diff = _diff_architecture_nodes(old_nodes, new_nodes)

    applied = False
    entry_id = existing_entry.id if existing_entry else None

    if form_data.apply:
        if existing_entry:
            update_data = {
                'content': json.dumps({'nodes': new_nodes}, ensure_ascii=False),
                'data': {
                    'autoExtracted': True,
                    'nodeCount': len(new_nodes),
                    'versionId': form_data.version_id,
                },
            }
            await PMEntries.update_entry_by_id(existing_entry.id, update_data, db=db)
            applied = True
        else:
            new_entry = await _create_entry_with_entity(
                user=user,
                project_id=project_id,
                module_type='product-architecture',
                title='Product Architecture (Auto-Extracted)',
                content=json.dumps({'nodes': new_nodes}, ensure_ascii=False),
                data={
                    'autoExtracted': True,
                    'nodeCount': len(new_nodes),
                    'versionId': form_data.version_id,
                },
                db=db,
            )
            entry_id = new_entry.id if new_entry else None
            applied = True

    return {
        'entry_id': entry_id,
        'nodes': new_nodes if applied else old_nodes,
        'diff': diff,
        'applied': applied,
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
5. 调用工具时使用原生 function calling，不要在回复正文中输出 <function_calls>、<invoke>、<tool_use>、seed:tool_call 等文本标签

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

(v14) 工具调用通过标准 function calling 完成，不需要在回复正文中输出任何文本形式的工具调用标签或 ```action``` 块。
"""


async def _call_llm(request: Request, user, system_prompt: str, user_message: str) -> str:
    """Call LLM with a system+user prompt. Returns content string only.

    Used by non-agent endpoints (parameter extraction, PRD generation, etc.)
    that don't need tool execution. Resolves the first available model so
    generate_chat_completion doesn't raise 'Model not found'.
    """
    try:
        from open_webui.models.models import Models
        from open_webui.utils.chat import generate_chat_completion

        models = await Models.get_all_models()
        if not models:
            log.error('[call_llm] No model available')
            return ''
        model_id = models[0].id

        payload = {
            'model': model_id,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            'stream': False,
        }

        result = await generate_chat_completion(request, payload, user)

        # generate_chat_completion may return starlette.responses.JSONResponse
        # (non-streaming path) — parse the body to get the dict.
        if not isinstance(result, dict):
            from starlette.responses import Response as StarletteResponse
            if isinstance(result, StarletteResponse):
                try:
                    result = json.loads(result.body)
                except (json.JSONDecodeError, ValueError, AttributeError) as e:
                    log.error(
                        f'[call_llm] Failed to parse JSONResponse body: {e}'
                    )
                    return ''
            else:
                log.warning(
                    f'[call_llm] Unexpected response type: {type(result).__name__}'
                )
                return ''

        choices = result.get('choices', [])
        if not choices:
            return ''
        message = choices[0].get('message', {})
        return message.get('content', '') or ''
    except Exception as e:
        import traceback
        log.error(
            f'[call_llm] exception: {e}\n{traceback.format_exc()}'
        )
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
    """v14: PM Agent entry point.

    Directly dispatches to the native pipeline (_agent_chat_native), which
    uses the standard OpenWebUI chat loop (process_chat_payload +
    generate_chat_completion with stream=True).
    """
    skill_id, confidence = detect_intent(form_data.message)
    return await _agent_chat_native(request, form_data, user, skill_id, confidence)


async def _agent_chat_native(
    request: Request,
    form_data: AgentChatRequest,
    user,
    skill_id: str,
    confidence: float,
):
    """v14 native pipeline path.

    Replaces the v13 _call_llm_with_tools + 5-round loop with the standard
    OpenWebUI pipeline (process_chat_payload + generate_chat_completion).

    Why: v13 passed model='' to generate_chat_completion, which raised
    Exception('Model not found') BEFORE the text-form FC parser could run.
    The native pipeline resolves the model, applies MODEL_FUNCTION_CALLING_OVERRIDES
    (forces doubao-seed-evolving:default → prompt-based FC), and auto-loads
    PM tools when metadata['pm_project_id'] is set.
    """
    import uuid
    from open_webui.models.models import Models
    from open_webui.utils.middleware import process_chat_payload
    from open_webui.utils.chat import generate_chat_completion

    # 1. Resolve model (same pattern as agent_status at L3020).
    #    Note: Models.get_all_models is async (models.py L187) — must await.
    models = await Models.get_all_models()
    if not models:
        raise HTTPException(status_code=503, detail='No model available')
    model_id = models[0].id
    model = request.app.state.MODELS.get(model_id)
    if not model:
        raise HTTPException(status_code=503, detail=f'Model {model_id} not in app state')

    # FC mode (function_calling) is no longer passed manually — the native
    # pipeline resolves it from MODEL_FUNCTION_CALLING_OVERRIDES (config.py
    # default: doubao-seed-evolving:default) via process_chat_payload.
    log.info(
        f'[v14-Diag] agent_chat native: model_id={model_id}, '
        f'project_id={form_data.project_id}'
    )

    # 2. Build payload + metadata.
    #    pm_project_id triggers PM tools auto-load in process_chat_payload
    #    (middleware.py L3084-3168).
    chat_id = f'pm-agent:{form_data.project_id}'
    payload = {
        'model': model_id,
        'messages': [
            {'role': 'user', 'content': form_data.message},
        ],
        'stream': True,
    }
    # NOTE: __event_emitter__ is normally created by process_chat_payload
    # via get_event_emitter(metadata) (middleware.py L2663) when metadata has
    # chat_id + message_id (both present below). This placeholder is kept as
    # a marker per spec; the real emitter will be injected into extra_params
    # by process_chat_payload and used by the tool execution loop.
    # TODO: __event_emitter__ 注入方式待验证 — standard pipeline auto-creates
    # it from metadata.chat_id/message_id; this callable is a no-op fallback.
    metadata = {
        'chat_id': chat_id,
        'message_id': str(uuid.uuid4()),
        'user_id': user.id,
        'pm_project_id': form_data.project_id,
        '__event_emitter__': lambda *args, **kwargs: None,
    }

    # 4. process_chat_payload loads PM tools, injects system msg, dispatches FC mode
    try:
        payload, metadata, events = await process_chat_payload(
            request, payload, user, metadata, model
        )
    except Exception as e:
        log.exception(f'[v14-Diag] process_chat_payload failed: {e}')
        raise HTTPException(status_code=500, detail=f'Pipeline setup failed: {e}')

    tools_dict_keys = list((metadata.get('tools') or {}).keys())
    log.info(
        f'[v14-Diag] process_chat_payload done: tools={tools_dict_keys}, '
        f'messages_count={len(payload.get("messages", []))}'
    )

    # 5. Generate LLM response (with tool execution loop inside).
    #    With stream=True, generate_chat_completion returns a StreamingResponse
    #    (SSE chunks) — return it directly so FastAPI streams tokens to the
    #    frontend. The __event_emitter__ created by process_chat_payload
    #    pushes status events (chat:active, tool calls) alongside the stream.
    response = await generate_chat_completion(request, payload, user)
    log.info(f'[v14-Diag] generate_chat_completion returned type={type(response).__name__}')

    # 6. StreamingResponse (SSE) — return directly to client.
    #    No JSONResponse body parsing, no choices[0].message.content extraction
    #    (those only exist for non-streaming dict responses, which the PM agent
    #    no longer produces). Action signals (pm.entry.confirm etc.) are now
    #    delivered via __event_call__ on the tool side, not scanned from
    #    payload['messages'] post-hoc.
    if not isinstance(response, dict):
        return response

    # Defensive fallback: if a future caller sets stream=False, keep returning
    # the message content so the API contract doesn't break.
    choices = response.get('choices', [])
    message = choices[0].get('message', {}) if choices else {}
    content = message.get('content', '') or ''
    log.info(f'[v14-Diag] response: content_len={len(content)}')

    return {
        'message': content,
        'intent': {'skillId': skill_id, 'confidence': confidence},
        'skillId': skill_id,
    }


@router.get('/agent/status')
async def agent_status(
    user=Depends(get_verified_user),
):
    try:
        from open_webui.models.models import Models
        models = await Models.get_all_models()
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
    rt = form_data.get('relation_type', 'references')
    if rt not in ALLOWED_RELATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid relation_type: {rt}. Allowed: {sorted(ALLOWED_RELATION_TYPES)}'
        )
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


@router.post('/relations/{relation_id}/confirm', response_model=dict)
async def confirm_relation(
    relation_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """把 relation 状态置为已确认（confirmed=1）。"""
    from open_webui.models.pm import PMRelation
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(PMRelation).where(PMRelation.id == relation_id).values(confirmed=1)
    )
    await db.commit()
    return {'relation_id': relation_id, 'confirmed': 1}


@router.post('/projects/{project_id}/relations/suggest', response_model=dict)
async def suggest_relations(
    project_id: str,
    form_data: dict,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """按 target_module_type 拉候选 entity 返回，作为前端创建关系的建议源。"""
    from open_webui.models.pm import PMEntities, PMRelations
    entity_id = form_data.get('entity_id') or form_data.get('entityId', '')
    target_module_type = form_data.get('target_module_type') or form_data.get('targetModuleType', '')
    if not entity_id or not target_module_type:
        return {'suggestions': []}
    entities = await PMEntities.get_entities_by_project_id(project_id, db=db)
    existing = await PMRelations.get_relations_by_entity_id(entity_id, db=db)
    existing_ids = {r.entity_a_id for r in existing} | {r.entity_b_id for r in existing}
    suggestions = [
        {'entityBId': e.id, 'entityType': e.type, 'name': e.name}
        for e in entities
        if e.type == target_module_type and e.id != entity_id and e.id not in existing_ids
    ][:20]
    return {'suggestions': suggestions}


@router.post('/projects/{project_id}/flowcharts/{flowchart_id}/traceability', response_model=dict)
async def create_flowchart_traceability(
    project_id: str,
    flowchart_id: str,
    form_data: dict,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """创建流程图节点 → entity 的绑定，同步在 pm_relation 插入 references 关系。"""
    from open_webui.models.pm import (
        PMFlowchartTraceabilities, PMFlowchartTraceabilityForm,
        PMRelations, PMRelationForm
    )
    trace_form = PMFlowchartTraceabilityForm(
        node_id=form_data.get('node_id', ''),
        flowchart_id=flowchart_id,
        entity_type=form_data.get('entity_type', 'none'),
        entity_id=form_data.get('entity_id', ''),
        entity_name=form_data.get('entity_name', ''),
        version_id=form_data.get('version_id'),
        bound_by=user.id,
    )
    trace = await PMFlowchartTraceabilities.insert_new_traceability(trace_form, db=db)
    if trace and trace.entity_id:
        rel_form = PMRelationForm(
            project_id=project_id,
            entity_a_id=trace.node_id,
            entity_b_id=trace.entity_id,
            relation_type='references',
            confidence=100,
            confirmed=1,
            created_by=user.id,
            version_id=trace.version_id,
        )
        await PMRelations.insert_new_relation(user.id, rel_form, db=db)
    return trace


@router.get('/projects/{project_id}/flowcharts/{flowchart_id}/traceability', response_model=list)
async def list_flowchart_traceability(
    project_id: str,
    flowchart_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """列出某流程图的所有节点绑定。"""
    from open_webui.models.pm import PMFlowchartTraceabilities
    return await PMFlowchartTraceabilities.get_traceabilities_by_flowchart_id(flowchart_id, db=db)


@router.delete('/flowchart-traceability/{trace_id}', response_model=dict)
async def delete_flowchart_traceability(
    trace_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """删除流程图绑定，级联删除对应 pm_relation。"""
    from open_webui.models.pm import PMFlowchartTraceabilities, PMFlowchartTraceability, PMRelation
    from sqlalchemy import delete as sql_delete, select as sql_select
    # 先查 trace 拿 node_id / entity_id（用于级联删 pm_relation）
    trace_result = await db.execute(
        sql_select(PMFlowchartTraceability).where(PMFlowchartTraceability.id == trace_id)
    )
    trace = trace_result.scalar_one_or_none()
    await PMFlowchartTraceabilities.delete_traceability_by_id(trace_id, db=db)
    if trace and trace.node_id and trace.entity_id:
        await db.execute(sql_delete(PMRelation).where(
            PMRelation.entity_a_id == trace.node_id,
            PMRelation.entity_b_id == trace.entity_id,
            PMRelation.relation_type == 'references',
        ))
        await db.commit()
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
    if form_data.relation_type not in ALLOWED_RELATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid relation_type: {form_data.relation_type}. Allowed: {sorted(ALLOWED_RELATION_TYPES)}'
        )
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
