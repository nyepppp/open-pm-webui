import logging
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
    PMRelation,
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
            metadata=form_data.data,
        )
        await PMEntities.insert_new_entity(user.id, entity_form, db=db)
    except Exception as e:
        # Don't fail entry creation if entity creation fails
        import logging
        logging.getLogger(__name__).warning(f'Failed to auto-create entity for entry {entry.id}: {e}')
    
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
        metadata=entry.data,
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
        PMEntryUpdateForm(content=version.content, data=version.metadata),
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


############################
# Agent
############################

from open_webui.pm.intent import detect_intent
from open_webui.pm.skills.base import BaseSkill
from open_webui.pm.skills.prd_generation import PRDGenerationSkill
from open_webui.pm.skills.requirement_analysis import RequirementAnalysisSkill
from open_webui.pm.actions import validate_action

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
        metadata=form_data.get('metadata'),
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
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    from open_webui.models.pm import PMRelations
    return await PMRelations.get_relations_by_entity_id(entity_id, db=db)


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
    entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    version_entries = []
    for entry in entries:
        entry_data = entry.data or {}
        if entry_data.get('versionId') == version_id:
            version_entries.append(entry)
    return version_entries


@router.post('/projects/{project_id}/versions/{version_id}/snapshot', response_model=dict)
async def create_project_version_snapshot(
    project_id: str,
    version_id: str,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Create a snapshot of all current entries for a project version."""
    from open_webui.models.pm import PMEntryVersions
    entries = await PMEntries.get_entries_by_project_id(project_id, db=db)
    snapshots = []
    for entry in entries:
        version_form = PMEntryVersionForm(
            entry_id=entry.id,
            project_id=project_id,
            module_type=entry.module_type,
            version_number=version_id,
            content=entry.content,
            metadata={**(entry.data or {}), 'projectVersionId': version_id},
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

@router.get('/projects/{project_id}/traceability/validate', response_model=dict)
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
    results = []
    
    for step in form_data.steps:
        # Check condition
        if step.condition:
            try:
                # Simple condition evaluation (placeholder)
                condition_met = eval(step.condition, {"__builtins__": {}}, {})
                if not condition_met:
                    results.append({'stepId': step.id, 'status': 'skipped'})
                    continue
            except Exception:
                results.append({'stepId': step.id, 'status': 'skipped'})
                continue
        
        # Execute skill
        try:
            skill = SKILL_INSTANCES.get(step.skillId)
            if skill:
                # Call skill with inputs
                result = await skill.execute(step.inputs, user, db)
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
