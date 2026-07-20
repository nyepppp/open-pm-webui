"""PM 项目聊天上下文注入模块。

当用户在聊天页选择了 PM 项目时，本模块负责：
1. Level 1（自动注入）：把项目名 + 所有模块的条目索引（标题/状态/优先级/关键字段/截断描述）
   拼成 system 消息，由 middleware 注入到 LLM 上下文。
2. Level 2（按需工具）：提供 get_pm_module_entries_full / get_pm_entry_detail_full 两个函数，
   由 utils/tools.py 注册为 builtin 工具，AI 需要完整内容时主动调用。

所有函数都先校验 project.user_id == user.id，防止越权读取。
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Optional

from open_webui.models.pm import PMEntries, PMProjects, PMVersions

log = logging.getLogger(__name__)


# ============================================================================
# 模块描述（label 对齐 src/lib/components/pm/moduleFields.ts:moduleEditorConfig）
# ============================================================================
MODULE_DESCRIPTIONS = {
    'prd': {'name': 'PRD 文档', 'desc': '产品需求文档，富文本'},
    'requirement': {'name': '需求管理', 'desc': '功能/性能/安全/体验需求'},
    'requirement-boundary': {'name': '需求边界', 'desc': '需求场景与功能边界'},
    'roadmap': {'name': '产品路线图', 'desc': '里程碑/特性/任务节点'},
    'parameter': {'name': '参数配置', 'desc': '输入/输出/配置参数'},
    'architecture': {'name': '产品架构', 'desc': '前后端/数据库/基础设施架构'},
    'product-architecture': {'name': '产品架构', 'desc': '架构图节点'},
    'prototype': {'name': '原型/UI设计', 'desc': 'Web/Mobile/桌面原型'},
    'competitor': {'name': '竞品分析', 'desc': '竞品对比分析'},
    'spec': {'name': 'SPEC规范', 'desc': '功能/SPEC 规范文档'},
    'flowchart': {'name': '流程图', 'desc': 'BPMN/流程图/泳道/状态机'},
    'schedule': {'name': '项目排期', 'desc': '任务排期与里程碑'},
    'testcase': {'name': '测试用例', 'desc': '功能/边界/异常/性能用例'},
    'risk': {'name': '风险分析', 'desc': '风险概率/影响/应对'},
    'meeting': {'name': '会议纪要', 'desc': '会议结论与待办'},
    'acceptance': {'name': '验收报告', 'desc': '验收范围/结果/遗留'},
    'faq': {'name': 'FAQ', 'desc': '常见问题与解答'},
}


# ============================================================================
# 每个模块的关键字段（从 data JSON 中提取展示，对齐 moduleFields.ts 的 fields）
# ============================================================================
MODULE_KEY_FIELDS = {
    'requirement': ['source', 'category', 'userRole', 'dueDate'],
    'parameter': ['key', 'moduleName', 'featureName', 'paramType', 'dataType', 'required', 'versionId', 'sourceDocument'],
    'testcase': ['scenario', 'caseType', 'expectedResult', 'requirementId'],
    'risk': ['probability', 'impactScope', 'owner', 'deadline'],
    'competitor': ['competitorUrl', 'dimension'],
    'schedule': ['assignee', 'startDate', 'endDate', 'progress', 'isMilestone'],
    'acceptance': ['requirementId', 'scope', 'result'],
    'faq': ['question', 'answer', 'audience'],
    'meeting': ['participants', 'meetingDate', 'conclusions'],
    'prototype': ['protoType', 'reviewStatus'],
    'roadmap': ['nodeType', 'nodeStatus', 'startDate', 'endDate'],
    'product-architecture': ['architectureType', 'techStack'],
    'requirement-boundary': ['scenario', 'function'],
    'spec': ['specCategory'],
    'flowchart': ['chartType', 'swimlanes'],
    'architecture': ['architectureType', 'techStack'],
    'prd': [],  # 纯富文本，无 data 字段
}


# 每模块最多展示的条目数（超过则提示调用工具查看全部）
MAX_ENTRIES_PER_MODULE = 30
# Level 1 注入时 content 截断长度
LEVEL1_CONTENT_TRUNCATE = 100
# Level 2 工具返回时 content 截断长度（get_pm_module_entries_full）
LEVEL2_MODULE_CONTENT_TRUNCATE = 500


# ============================================================================
# 内部工具函数
# ============================================================================


async def _verify_project_access(project_id: str, user) -> bool:
    """校验 user 对 project 的访问权限（owner 校验）。

    防止用户传别人的 project_id 读别人的 PM 条目。
    """
    if not project_id or not user:
        return False
    project = await PMProjects.get_project_by_id(project_id)
    if not project:
        return False
    return project.user_id == user.id


async def _resolve_version_number(project_version_id: Optional[str]) -> Optional[str]:
    """把 project_version_id（UUID）解析为 version_number（如 'v1'）。

    PMVersions.get_version_by_id 查询的是 pm_version 表（项目版本），
    返回 PMVersionModel，其 version_number 是人类可读版本号。
    """
    if not project_version_id:
        return None
    try:
        v = await PMVersions.get_version_by_id(project_version_id)
        return v.version_number if v else None
    except Exception as e:
        log.warning(f'[PM Context] _resolve_version_number failed for {project_version_id}: {e}')
        return None


def _extract_key_fields(module_type: str, data: Optional[dict]) -> str:
    """从 data JSON 提取关键字段，拼成简短字符串。

    例：parameter 模块返回 "key=username | paramType=输入参数 | dataType=string"
    """
    if not data or module_type not in MODULE_KEY_FIELDS:
        return ''
    fields = MODULE_KEY_FIELDS[module_type]
    if not fields:
        return ''
    parts = []
    for f in fields:
        v = data.get(f)
        if v is not None and v != '':
            parts.append(f'{f}={v}')
    return ' | '.join(parts)


def _truncate(text: Optional[str], n: int = LEVEL1_CONTENT_TRUNCATE) -> str:
    """截断文本到 n 字，超出加省略号。"""
    if not text:
        return ''
    return text[:n] + '...' if len(text) > n else text


# ============================================================================
# Level 1：构建 PM 上下文 system 消息
# ============================================================================


async def build_pm_context_system_message(
    project_id: str,
    user,
    tools_available: bool = True,
) -> Optional[str]:
    """拉取项目 + 所有模块的条目索引，拼成 system 消息文本。

    Args:
        project_id: PM 项目 ID
        user: 当前用户（用于访问校验）
        tools_available: 是否已注册 PM builtin 工具。True 时 system 消息末尾
            提示 LLM 调用工具读取详情；False 时改为引导 LLM 询问具体模块
            （用于工具注册失败的降级场景）。

    Returns:
        system 消息文本；若项目不存在或 user 无访问权则返回 None。
    """
    log.info(
        f'[PM Context] build_pm_context_system_message called: '
        f'project_id={project_id}, user={user.id if user else None}'
    )
    if not await _verify_project_access(project_id, user):
        log.warning(
            f'[PM Context] Access denied: user {user.id if user else None} '
            f'has no access to project {project_id}'
        )
        return None

    project = await PMProjects.get_project_by_id(project_id)
    if not project:
        return None

    entries = await PMEntries.get_entries_by_project_id(project_id)

    # 按 module_type 分组
    by_module: dict = defaultdict(list)
    for e in entries:
        by_module[e.module_type].append(e)

    lines: list[str] = [f'你正在协助用户处理 PM 项目「{project.name}」。']
    if project.description:
        lines.append(f'项目描述：{project.description}')
    lines.append('')
    lines.append('## 项目模块概览')
    lines.append('')

    for module_type, module_entries in by_module.items():
        mod_desc = MODULE_DESCRIPTIONS.get(module_type, {'name': module_type, 'desc': ''})
        lines.append(f'### {mod_desc["name"]} ({module_type}) — {len(module_entries)} 个条目')

        shown = module_entries[:MAX_ENTRIES_PER_MODULE]
        hidden = len(module_entries) - len(shown)

        for e in shown:
            # 拼接：[status] P{priority}: {title} — {key_fields} | {content_truncated}
            status_str = f'[{e.status}]' if e.status else ''
            priority_str = f' P{e.priority}' if e.priority else ''
            key_fields = _extract_key_fields(e.module_type, e.data or {})
            content_trunc = _truncate(e.content or '', LEVEL1_CONTENT_TRUNCATE)

            parts: list[str] = []
            if status_str:
                parts.append(status_str)
            if priority_str:
                parts.append(priority_str)
            line = f'- {" ".join(parts)} {e.title}' if parts else f'- {e.title}'
            if key_fields:
                line += f' — {key_fields}'
            if content_trunc:
                line += f' | {content_trunc}'
            lines.append(line)

        if hidden > 0:
            lines.append(
                f'  ...还有 {hidden} 条未展示，调用 get_pm_module_entries 工具查看全部'
            )

        lines.append('')

    if tools_available:
        lines.append(
            '（以上每个条目仅展示关键字段和描述前 '
            f'{LEVEL1_CONTENT_TRUNCATE}'
            ' 字。如需完整内容，调用 get_pm_module_entries 工具读取整个模块，'
            '或调用 get_pm_entry_detail 工具读取单条目全文。）'
        )
        # D42: PM 工具清单 + 用法示例（正向引导）
        # 旧版的"禁止"section 反而让 AI 学会了被禁止的函数名（"不要想大象"效应），移除。
        # 旧版 L239 还列了无效的 module_type 值（gantt/workflow 不在 MODULE_DESCRIPTIONS），用动态 keys 替代。
        # module_type 动态从 MODULE_DESCRIPTIONS.keys() 取，永不漂移。
        lines.append('')
        lines.append('## 可用的 PM 工具（共 10 个）')
        lines.append('')
        lines.append('| 工具名 | 用途 | 关键参数 |')
        lines.append('|--------|------|----------|')
        lines.append('| get_pm_module_entries | 查询当前项目的模块/条目列表 | module_type |')
        lines.append('| get_pm_entry_detail | 查询单个条目详情 | entry_id |')
        lines.append('| pm_entry_create | 创建单条条目（含层级链接） | module_type, title, parent_id（写入 data.parent_entry_id）, data |')
        lines.append('| pm_entry_batch_create | 批量创建条目（≤20条，含层级链接） | module_type, entries[], parent_id（fallback） |')
        lines.append('| pm_entry_batch_create_preview | 预览批量创建结果（不落库） | module_type, entries[], parent_id |')
        lines.append('| pm_entry_update | 更新条目 | entry_id, fields |')
        lines.append('| pm_entry_version_create | 创建条目历史版本 | entry_id, snapshot |')
        lines.append('| pm_relation_create | 创建条目间关联 | source_id, target_id, relation_type |')
        lines.append('| pm_entry_delete | 删除条目（硬删除，需二次确认） | entry_id, confirmed |')
        lines.append('| pm_prd_to_mfp_transform | PRD 原子化转模块-功能-参数（含层级链接） | prd_entry_id |')
        lines.append('')
        lines.append('## module_type 可选值')
        lines.append(f'- {", ".join(MODULE_DESCRIPTIONS.keys())}')
        lines.append('')
        lines.append('## 用法示例')
        lines.append('- 用户说「创建 1 个模块」→ 调用 pm_entry_create，传 module_type=product-architecture')
        lines.append('- 用户说「批量导入 5 个功能」→ 调用 pm_entry_batch_create，entries 数组传 5 项')
        lines.append('- 用户说「关联两个条目」→ 先用 get_pm_module_entries 查 ID，再调 pm_relation_create')
        lines.append('- 用户说「更新这个条目的描述」→ 调用 pm_entry_update，传 entry_id 和 description')
        lines.append('- 用户说「删除条目」→ 先调 pm_entry_delete(confirmed=False) 取预览，等用户在前端确认后再调 pm_entry_delete(confirmed=True) 执行')
        lines.append('- 用户说「把 PRD 转成模块-功能-参数」→ 工具调用序列:')
        lines.append('  1. 若不知 PRD entry_id：调用 get_pm_module_entries(module_type=prd) 列出所有 PRD')
        lines.append('  2. 调用 pm_prd_to_mfp_transform(prd_entry_id=<上一步拿到的 ID>)')
        lines.append('  3. 工具内部一次性完成模块/功能/参数创建（含 parent_entry_id + moduleName/featureName 双链接），返回 summary')
        lines.append('  4. 用自然语言复述 summary（created_modules / created_functions / created_parameters / by_module），提示用户在产品架构画布查看')
        lines.append('- 不要自己拆分 PRD 再调 3 次 pm_entry_batch_create —— pm_prd_to_mfp_transform 已封装层级链接')
        lines.append('- 仅当用户明确要求「分步看」或「我要逐个模块审查」时，才用 pm_entry_batch_create 手动创建（此时记得传 parent_id 或在 entry.data 里填 parent_entry_id + moduleName + featureName）')
        lines.append('- **D44-fix 硬约束（skill 内部已校验，违反会被拒绝回滚 0 条）**:')
        lines.append('  - 禁止把 parameter key（camelCase 标识符如 boundKbIds）当成 feature name')
        lines.append('  - 每个 parameter 必须挂在 feature 下，不允许 module 直接挂 parameter')
        lines.append('  - 禁止产出「未分类模块」「Uncategorized」这种兜底 module（找不到归属的内容宁可不输出）')
        lines.append('')
        lines.append('## 工具调用方式（v14）')
        lines.append('- v14 起 PM Agent 走原生 OpenWebUI 管线，通过标准 function calling 调用工具')
        lines.append('- 不需要也不应该输出 ```action``` 块或 <function_calls>/<invoke>/<tool_use>/seed:tool_call 等文本标签')
        lines.append('- 读取类工具（get_pm_module_entries / get_pm_entry_detail）：直接调用，结果会自动注入下一轮对话')
        lines.append('- 写入类工具（pm_entry_create / pm_entry_update / pm_entry_batch_create）：直接调用，系统自动执行')
        lines.append('- 删除类工具（pm_entry_delete）：必须 confirmed=False 先取预览，用户在前端弹窗确认后会自动执行删除')
        lines.append('- doubao-seed-evolving 模型走 prompt-based FC（default 模式），由管线统一处理；不要在正文里手写工具调用文本')
        lines.append('')
        lines.append('## 失败处理')
        lines.append('- 工具返回 error 字段时，停止重试同一工具，向用户说明失败原因并询问下一步')
        lines.append('- 不确定工具名或参数时，先调用 get_pm_module_entries 查询当前数据')
    else:
        lines.append(
            '（以上每个条目仅展示关键字段和描述前 '
            f'{LEVEL1_CONTENT_TRUNCATE}'
            ' 字。如需完整内容，请明确询问具体模块或条目标题，'
            '系统会重新注入更详细的信息。）'
        )

    return '\n'.join(lines)


# ============================================================================
# Level 2：供 builtin 工具调用的完整内容读取函数
# ============================================================================


async def get_pm_module_entries_full(
    module_type: str, project_id: str, user
) -> list[dict]:
    """返回某模块全部条目的完整详情（content 截断 500 字）。

    供 builtin 工具 get_pm_module_entries 调用。
    返回每个条目的 project_version_id（UUID）和 project_version_number（如 'v1'），
    让 LLM 展示版本号而非 UUID。
    """
    if not await _verify_project_access(project_id, user):
        return []

    entries = await PMEntries.get_entries_by_project_and_module(project_id, module_type)
    # 缓存 version_id → version_number，避免同一版本多次查询
    version_cache: dict[str, Optional[str]] = {}

    result = []
    for e in entries:
        pv_id = getattr(e, 'project_version_id', None)
        if pv_id and pv_id not in version_cache:
            version_cache[pv_id] = await _resolve_version_number(pv_id)
        result.append({
            'id': e.id,
            'title': e.title,
            'status': e.status,
            'priority': e.priority,
            'content': _truncate(e.content or '', LEVEL2_MODULE_CONTENT_TRUNCATE),
            'data': e.data,
            'module_type': e.module_type,
            'updated_at': e.updated_at,
            'project_version_id': pv_id,
            'project_version_number': version_cache.get(pv_id) if pv_id else None,
        })
    return result


async def get_pm_entry_detail_full(entry_id: str, user) -> Optional[dict]:
    """返回单条目的完整 content（不截断）。

    供 builtin 工具 get_pm_entry_detail 调用。
    通过 entry.project_id 反查项目，再校验 user 访问权。
    返回 project_version_id（UUID）和 project_version_number（如 'v1'）。
    """
    entry = await PMEntries.get_entry_by_id(entry_id)
    if not entry:
        return None
    if not await _verify_project_access(entry.project_id, user):
        return None
    pv_id = getattr(entry, 'project_version_id', None)
    pv_number = await _resolve_version_number(pv_id) if pv_id else None
    return {
        'id': entry.id,
        'title': entry.title,
        'status': entry.status,
        'priority': entry.priority,
        'content': entry.content,  # 完整，不截断
        'data': entry.data,
        'module_type': entry.module_type,
        'project_id': entry.project_id,
        'created_at': entry.created_at,
        'updated_at': entry.updated_at,
        'project_version_id': pv_id,
        'project_version_number': pv_number,
    }


# ============================================================================
# 意图识别：判断用户问题是否与 PM 项目相关
# ============================================================================


async def is_pm_related_query(
    request,
    user,
    model_id: str,
    user_query: str,
    project_name: str,
) -> bool:
    """用 task_model 判断用户问题是否与 PM 项目相关。

    判断标准：用户问题是否在询问项目相关的需求/模块/条目/排期/风险等内容。
    若判断失败（API 异常、模型不可用、JSON 解析失败等），默认返回 True
    （更安全——多注入比漏注入好）。

    Args:
        request: FastAPI Request 对象（用于访问 app.state.config / MODELS）
        user: 当前用户
        model_id: 当前 chat 使用的主模型 ID（用于回退，当 task_model 不可用时）
        user_query: 用户最新一条消息文本
        project_name: 当前 PM 项目名（用于 prompt 上下文）

    Returns:
        True 表示相关（应注入 PM 上下文），False 表示不相关
    """
    # 空消息（如纯文件上传），保守视为相关
    if not user_query or not user_query.strip():
        return True

    truncated_query = user_query[:500]

    prompt = f"""判断用户问题是否与 PM 项目「{project_name}」相关。

用户问题：
{truncated_query}

判断标准：问题是否涉及以下任一主题
- 项目的需求 / 模块 / 条目 / 文档
- 排期 / 里程碑 / 任务
- 风险 / 会议 / 验收 / 测试用例
- 架构 / 原型 / 路线图 / 竞品
- 项目数据本身的查询、修改、分析
- 用户在选了项目后发起的开放性提问（如"我们项目有哪些模块"、"帮我梳理一下进度"等）

只回答 JSON：{{"related": true}} 或 {{"related": false}}，不要任何其他文字。
"""

    try:
        # 延迟导入避免循环依赖
        from open_webui.utils.chat import generate_chat_completion
        from open_webui.utils.task import get_task_model_id
        from open_webui.constants import TASKS

        # 解析 task_model_id（与 generate_title 同一路径）
        models = request.app.state.MODELS
        task_model_id = get_task_model_id(
            model_id,
            request.app.state.config.TASK_MODEL,
            request.app.state.config.TASK_MODEL_EXTERNAL,
            models,
        )

        # 检查 task_model_id 是否在 models 中可用
        if task_model_id not in models:
            log.warning(
                f'[PM Context] task_model_id {task_model_id} not in models, '
                f'defaulting to inject'
            )
            return True

        max_tokens = models[task_model_id].get('info', {}).get('params', {}).get('max_tokens', 500)

        payload = {
            'model': task_model_id,
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': False,
            **(
                {'max_tokens': max_tokens}
                if models[task_model_id].get('owned_by') == 'ollama'
                else {'max_completion_tokens': max_tokens}
            ),
            'metadata': {
                'task': str(TASKS.FUNCTION_CALLING),
                'chat_id': None,
            },
        }

        response = await generate_chat_completion(request, form_data=payload, user=user)

        # 解析响应
        content = None
        if hasattr(response, 'body_iterator'):
            async for chunk in response.body_iterator:
                data = json.loads(chunk.decode('utf-8', 'replace'))
                content = data['choices'][0]['message']['content']
            if response.background is not None:
                await response.background()
        else:
            content = response['choices'][0]['message']['content']

        if not content:
            log.warning('[PM Context] Intent recognition: empty response, defaulting to inject')
            return True

        # 提取 JSON
        json_str = content[content.find('{'): content.rfind('}') + 1]
        if not json_str:
            log.warning(
                f'[PM Context] Intent recognition: no JSON in response "{content[:200]}", defaulting to inject'
            )
            return True

        result = json.loads(json_str)
        is_related = bool(result.get('related', True))
        log.info(
            f'[PM Context] Intent recognition result: related={is_related}, '
            f'query="{truncated_query[:80]}..."'
        )
        return is_related

    except Exception as e:
        log.warning(
            f'[PM Context] Intent recognition failed: {type(e).__name__}: {e}',
            exc_info=True,
        )
        return True  # 失败时默认注入
