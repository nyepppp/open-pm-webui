from __future__ import annotations

import asyncio
import base64
import copy
import inspect
import json
import logging
import os
import re
from functools import partial, update_wrapper
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from urllib.parse import quote, urlencode

import aiohttp
import yaml
from fastapi import Request
from langchain_core.utils.function_calling import (
    convert_to_openai_function as convert_pydantic_model_to_openai_function_spec,
)
from open_webui.config import BYPASS_ADMIN_ACCESS_CONTROL
from open_webui.env import (
    AIOHTTP_CLIENT_ALLOW_REDIRECTS,
    AIOHTTP_CLIENT_SESSION_SSL,
    AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL,
    AIOHTTP_CLIENT_TIMEOUT,
    AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER,
    AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA,
    ENABLE_FORWARD_USER_INFO_HEADERS,
    FORWARD_SESSION_INFO_HEADER_CHAT_ID,
    FORWARD_SESSION_INFO_HEADER_MESSAGE_ID,
    REDIS_KEY_PREFIX,
)
from open_webui.models.access_grants import AccessGrants
from open_webui.models.groups import Groups
from open_webui.models.tools import Tools
from open_webui.models.users import UserModel
from open_webui.tools.builtin import (
    add_memory,
    calculate_timestamp,
    create_automation,
    create_calendar_event,
    create_tasks,
    delete_automation,
    delete_calendar_event,
    delete_memory,
    edit_image,
    execute_code,
    fetch_url,
    generate_image,
    get_current_timestamp,
    grep_knowledge_files,
    kb_exec,
    list_automations,
    list_knowledge,
    list_knowledge_bases,
    list_memories,
    query_knowledge_bases,
    query_knowledge_files,
    replace_memory_content,
    replace_note_content,
    search_calendar_events,
    search_channel_messages,
    search_channels,
    search_chats,
    search_knowledge_bases,
    search_knowledge_files,
    search_memories,
    search_notes,
    search_web,
    toggle_automation,
    update_automation,
    update_calendar_event,
    update_task,
    view_channel_message,
    view_channel_thread,
    view_chat,
    view_file,
    view_knowledge_file,
    view_note,
    view_skill,
    write_note,
)
from open_webui.utils.access_control import has_access, has_connection_access, has_permission
from open_webui.utils.headers import get_custom_headers, include_user_info_headers
from open_webui.utils.misc import is_string_allowed
from open_webui.utils.plugin import load_tool_module_by_id
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

log = logging.getLogger(__name__)


async def build_tool_server_headers(
    connection: dict,
    request,
    user,
    server_id: str = '',
    metadata: dict | None = None,
    extra_params: dict | None = None,
) -> tuple[dict, dict]:
    """Build auth headers and cookies for a tool server connection.

    Handles bearer, session, system_oauth, and oauth_2.1 auth types plus
    custom header interpolation and user-info forwarding.
    Shared by MCP and OpenAPI paths.

    Returns (headers, cookies).
    """
    extra_params = extra_params or {}
    metadata = metadata or {}

    auth_type = connection.get('auth_type', 'bearer')
    headers = {}
    cookies = {}

    if auth_type == 'bearer':
        headers['Authorization'] = f'Bearer {connection.get("key", "")}'
    elif auth_type == 'session':
        cookies = request.cookies if hasattr(request, 'cookies') else {}
        headers['Authorization'] = f'Bearer {request.state.token.credentials}'
    elif auth_type == 'system_oauth':
        cookies = request.cookies if hasattr(request, 'cookies') else {}
        oauth_token = extra_params.get('__oauth_token__', None)
        if oauth_token:
            headers['Authorization'] = f'Bearer {oauth_token.get("access_token", "")}'
    elif auth_type in ('oauth_2.1', 'oauth_2.1_static'):
        try:
            splits = server_id.split(':')
            oauth_server_id = splits[-1] if len(splits) > 1 else server_id
            connection_type = connection.get('type', 'openapi')
            oauth_token = await request.app.state.oauth_client_manager.get_oauth_token(
                user.id, f'{connection_type}:{oauth_server_id}'
            )
            if oauth_token:
                headers['Authorization'] = f'Bearer {oauth_token.get("access_token", "")}'
        except Exception as e:
            log.error(f'Error getting OAuth token: {e}')

    # Interpolate template vars in custom connection headers
    connection_headers = connection.get('headers', None)
    if connection_headers and isinstance(connection_headers, dict):
        headers.update(get_custom_headers(connection_headers, user, metadata))

    # Add user info headers if enabled
    if ENABLE_FORWARD_USER_INFO_HEADERS and user:
        headers = include_user_info_headers(headers, user)
        if metadata.get('chat_id'):
            headers[FORWARD_SESSION_INFO_HEADER_CHAT_ID] = metadata['chat_id']
        if metadata.get('message_id'):
            headers[FORWARD_SESSION_INFO_HEADER_MESSAGE_ID] = metadata['message_id']

    return headers, cookies


# Let no function be called without need, and let what
# it yields justify the cost of running it.
async def get_async_tool_function_and_apply_extra_params(
    function: Callable, extra_params: dict
) -> Callable[..., Awaitable]:
    sig = inspect.signature(function)
    extra_params = {k: v for k, v in extra_params.items() if k in sig.parameters}
    partial_func = partial(function, **extra_params)

    # Remove the 'frozen' keyword arguments from the signature
    # python-genai uses the signature to infer the tool properties for native function calling
    parameters = []
    for name, parameter in sig.parameters.items():
        # Exclude keyword arguments that are frozen
        if name in extra_params:
            continue
        # Keep remaining parameters
        parameters.append(parameter)

    new_sig = inspect.Signature(parameters=parameters, return_annotation=sig.return_annotation)

    if inspect.iscoroutinefunction(function):
        # wrap the functools.partial as python-genai has trouble with it
        # https://github.com/googleapis/python-genai/issues/907
        async def new_function(*args, **kwargs):
            return await partial_func(*args, **kwargs)

    else:
        # Make it a coroutine function when it is not already
        async def new_function(*args, **kwargs):
            return partial_func(*args, **kwargs)

    update_wrapper(new_function, function)
    new_function.__signature__ = new_sig

    new_function.__function__ = function  # type: ignore
    new_function.__extra_params__ = extra_params  # type: ignore

    return new_function


async def get_updated_tool_function(function: Callable, extra_params: dict):
    # Get the original function and merge updated params
    __function__ = getattr(function, '__function__', None)
    __extra_params__ = getattr(function, '__extra_params__', None)

    if __function__ is not None and __extra_params__ is not None:
        return await get_async_tool_function_and_apply_extra_params(
            __function__,
            {**__extra_params__, **extra_params},
        )

    return function


async def get_tools(request: Request, tool_ids: list[str], user: UserModel, extra_params: dict) -> dict[str, dict]:
    """Load tools for the given tool_ids, checking access control."""
    if not tool_ids:
        return {}

    tools_dict = {}

    # Get user's group memberships for access control checks
    user_group_ids = {group.id for group in await Groups.get_groups_by_member_id(user.id)}

    # Batch-fetch all DB tools in one query instead of one per tool_id
    tool_models = await Tools.get_tools_by_ids(tool_ids)

    for tool_id in tool_ids:
        tool = tool_models.get(tool_id)
        if tool:
            # Check access control for local tools
            if (
                not (user.role == 'admin' and BYPASS_ADMIN_ACCESS_CONTROL)
                and tool.user_id != user.id
                and not await AccessGrants.has_access(
                    user_id=user.id,
                    resource_type='tool',
                    resource_id=tool.id,
                    permission='read',
                    user_group_ids=user_group_ids,
                )
            ):
                log.warning(f'Access denied to tool {tool_id} for user {user.id}')
                continue

            module = request.app.state.TOOLS.get(tool_id)
            if module is None or request.app.state.TOOL_CONTENTS.get(tool_id) != tool.content:
                module, _ = await load_tool_module_by_id(tool_id, content=tool.content)
                request.app.state.TOOLS[tool_id] = module
                request.app.state.TOOL_CONTENTS[tool_id] = tool.content

            __user__ = {
                **extra_params['__user__'],
            }

            # Set valves for the tool
            if hasattr(module, 'valves') and hasattr(module, 'Valves'):
                valves = await Tools.get_tool_valves_by_id(tool_id) or {}
                module.valves = module.Valves(**valves)
            if hasattr(module, 'UserValves'):
                __user__['valves'] = module.UserValves(  # type: ignore
                    **await Tools.get_user_valves_by_id_and_user_id(tool_id, user.id)
                )

            for spec in tool.specs:
                # TODO: Fix hack for OpenAI API
                # Some times breaks OpenAI but others don't. Leaving the comment
                for val in spec.get('parameters', {}).get('properties', {}).values():
                    if val.get('type') == 'str':
                        val['type'] = 'string'

                # Remove internal reserved parameters (e.g. __id__, __user__)
                spec['parameters']['properties'] = {
                    key: val for key, val in spec['parameters']['properties'].items() if not key.startswith('__')
                }

                # convert to function that takes only model params and inserts custom params
                function_name = spec['name']
                tool_function = getattr(module, function_name)
                callable = await get_async_tool_function_and_apply_extra_params(
                    tool_function,
                    {
                        **extra_params,
                        '__id__': tool_id,
                        '__user__': __user__,
                    },
                )

                # TODO: Support Pydantic models as parameters
                if callable.__doc__ and callable.__doc__.strip() != '':
                    s = re.split(':(param|return)', callable.__doc__, 1)
                    spec['description'] = s[0]
                else:
                    spec['description'] = function_name

                tool_dict = {
                    'tool_id': tool_id,
                    'callable': callable,
                    'spec': spec,
                    # Misc info
                    'metadata': {
                        'file_handler': hasattr(module, 'file_handler') and module.file_handler,
                        'citation': hasattr(module, 'citation') and module.citation,
                    },
                }

                # Handle function name collisions
                while function_name in tools_dict:
                    log.warning(f'Tool {function_name} already exists in another tools!')
                    # Prepend tool ID to function name
                    function_name = f'{tool_id}_{function_name}'

                tools_dict[function_name] = tool_dict
        else:
            if tool_id.startswith('server:'):
                splits = tool_id.split(':')

                if len(splits) == 2:
                    type = 'openapi'
                    server_id = splits[1]
                elif len(splits) == 3:
                    type = splits[1]
                    server_id = splits[2]

                server_id_splits = server_id.split('|')
                if len(server_id_splits) == 2:
                    server_id = server_id_splits[0]
                    function_names = server_id_splits[1].split(',')

                if type == 'openapi':
                    tool_server_data = None
                    for server in await get_tool_servers(request):
                        if server['id'] == server_id:
                            tool_server_data = server
                            break

                    if tool_server_data is None:
                        log.warning(f'Tool server data not found for {server_id}')
                        continue

                    tool_server_idx = tool_server_data.get('idx', 0)
                    connections = request.app.state.config.TOOL_SERVER_CONNECTIONS
                    if tool_server_idx >= len(connections):
                        log.warning(
                            f'Tool server index {tool_server_idx} out of range '
                            f'(have {len(connections)} connections), skipping server {server_id}'
                        )
                        continue
                    tool_server_connection = connections[tool_server_idx]

                    # Check access control for tool server
                    if not await has_connection_access(user, tool_server_connection, user_group_ids):
                        log.warning(f'Access denied to tool server {server_id} for user {user.id}')
                        continue

                    specs = tool_server_data.get('specs', [])
                    function_name_filter_list = tool_server_connection.get('config', {}).get(
                        'function_name_filter_list', ''
                    )

                    if isinstance(function_name_filter_list, str):
                        function_name_filter_list = function_name_filter_list.split(',')

                    for spec in specs:
                        function_name = spec['name']
                        if function_name_filter_list:
                            if not is_string_allowed(function_name, function_name_filter_list):
                                # Skip this function
                                continue

                        metadata = extra_params.get('__metadata__', {})
                        headers, cookies = await build_tool_server_headers(
                            tool_server_connection,
                            request,
                            user,
                            server_id=server_id,
                            metadata=metadata,
                            extra_params=extra_params,
                        )
                        headers.setdefault('Content-Type', 'application/json')

                        async def make_tool_function(function_name, tool_server_data, headers):
                            async def tool_function(**kwargs):
                                return await execute_tool_server(
                                    url=tool_server_data['url'],
                                    headers=headers,
                                    cookies=cookies,
                                    name=function_name,
                                    params=kwargs,
                                    server_data=tool_server_data,
                                )

                            return tool_function

                        tool_function = await make_tool_function(function_name, tool_server_data, headers)

                        callable = await get_async_tool_function_and_apply_extra_params(
                            tool_function,
                            {},
                        )

                        tool_dict = {
                            'tool_id': tool_id,
                            'callable': callable,
                            'spec': clean_openai_tool_schema(spec),
                            # Misc info
                            'type': 'external',
                        }

                        # Handle function name collisions
                        while function_name in tools_dict:
                            log.warning(f'Tool {function_name} already exists in another tools!')
                            # Prepend server ID to function name
                            function_name = f'{server_id}_{function_name}'

                        tools_dict[function_name] = tool_dict

                else:
                    continue

    return tools_dict


async def get_builtin_tools(
    request: Request, extra_params: dict, features: dict = None, model: dict = None
) -> dict[str, dict]:
    """
    Get built-in tools for native function calling.
    Only returns tools when BOTH the global config is enabled AND the model capability allows it.
    """
    tools_dict = {}
    builtin_functions = []
    features = features or {}
    model = model or {}

    # Helper to get model capabilities (defaults to True if not specified)
    def get_model_capability(name: str, default: bool = True) -> bool:
        return (model.get('info', {}).get('meta', {}).get('capabilities') or {}).get(name, default)

    # Helper to check if a builtin tool category is enabled via meta.builtinTools
    # Defaults to True if not specified (backward compatible)
    def is_builtin_tool_enabled(category: str) -> bool:
        builtin_tools = model.get('info', {}).get('meta', {}).get('builtinTools', {})
        return builtin_tools.get(category, True)

    # Helper to check user-level feature permission (admins always pass)
    user = extra_params.get('__user__', {})

    async def has_user_permission(feature_key: str) -> bool:
        if user.get('role') == 'admin':
            return True
        return await has_permission(
            user.get('id', ''),
            f'features.{feature_key}',
            request.app.state.config.USER_PERMISSIONS,
        )

    # Time utilities - available for date calculations
    if is_builtin_tool_enabled('time'):
        builtin_functions.extend([get_current_timestamp, calculate_timestamp])

    # Knowledge base tools - conditional injection based on model knowledge
    # If model has attached knowledge (any type), only provide query_knowledge_files
    # Otherwise, provide all KB browsing tools
    model_knowledge = model.get('info', {}).get('meta', {}).get('knowledge', [])
    # Merge folder-attached knowledge so builtin tools can search it
    folder_knowledge = extra_params.get('__metadata__', {}).get('folder_knowledge')
    if folder_knowledge:
        model_knowledge = list(model_knowledge or []) + list(folder_knowledge)
    if is_builtin_tool_enabled('knowledge'):
        from open_webui.env import ENABLE_KB_EXEC

        if ENABLE_KB_EXEC:
            builtin_functions.append(kb_exec)
            builtin_functions.append(query_knowledge_files)
            # Notes attached to the model need view_note since kb_exec is file-only
            if model_knowledge:
                knowledge_types = {item.get('type') for item in model_knowledge}
                if 'note' in knowledge_types:
                    builtin_functions.append(view_note)
            if not model_knowledge:
                builtin_functions.append(query_knowledge_bases)
                builtin_functions.append(search_knowledge_bases)
        elif model_knowledge:
            builtin_functions.extend(
                [list_knowledge, search_knowledge_files, grep_knowledge_files, query_knowledge_files]
            )

            knowledge_types = {item.get('type') for item in model_knowledge}
            if 'file' in knowledge_types or 'collection' in knowledge_types:
                builtin_functions.extend([view_file, view_knowledge_file])
            if 'note' in knowledge_types:
                builtin_functions.append(view_note)
        else:
            builtin_functions.extend(
                [
                    list_knowledge_bases,
                    search_knowledge_bases,
                    query_knowledge_bases,
                    grep_knowledge_files,
                    search_knowledge_files,
                    query_knowledge_files,
                    view_knowledge_file,
                ]
            )

    # Chats tools - search and fetch user's chat history
    if is_builtin_tool_enabled('chats'):
        builtin_functions.extend([search_chats, view_chat])

    # Add memory tools if builtin category enabled AND enabled for this chat
    if (
        is_builtin_tool_enabled('memory')
        and (features.get('memory') or get_model_capability('memory', False))
        and await has_user_permission('memories')
    ):
        builtin_functions.extend(
            [
                search_memories,
                add_memory,
                replace_memory_content,
                delete_memory,
                list_memories,
            ]
        )

    # Add web search tools if builtin category enabled AND enabled globally AND model has web_search capability
    if (
        is_builtin_tool_enabled('web_search')
        and getattr(request.app.state.config, 'ENABLE_WEB_SEARCH', False)
        and get_model_capability('web_search')
        and features.get('web_search')
        and await has_user_permission('web_search')
    ):
        builtin_functions.extend([search_web, fetch_url])

    # Add image generation/edit tools if builtin category enabled AND enabled globally AND model has image_generation capability
    if (
        is_builtin_tool_enabled('image_generation')
        and getattr(request.app.state.config, 'ENABLE_IMAGE_GENERATION', False)
        and get_model_capability('image_generation')
        and features.get('image_generation')
        and await has_user_permission('image_generation')
    ):
        builtin_functions.append(generate_image)
    if (
        is_builtin_tool_enabled('image_generation')
        and getattr(request.app.state.config, 'ENABLE_IMAGE_EDIT', False)
        and get_model_capability('image_generation')
        and features.get('image_generation')
        and await has_user_permission('image_generation')
    ):
        builtin_functions.append(edit_image)

    # Add code interpreter tool if builtin category enabled AND enabled globally AND model has code_interpreter capability
    if (
        is_builtin_tool_enabled('code_interpreter')
        and getattr(request.app.state.config, 'ENABLE_CODE_INTERPRETER', True)
        and get_model_capability('code_interpreter')
        and features.get('code_interpreter')
        and await has_user_permission('code_interpreter')
    ):
        builtin_functions.append(execute_code)

    # Notes tools - search, view, create, and update user's notes
    if (
        is_builtin_tool_enabled('notes')
        and getattr(request.app.state.config, 'ENABLE_NOTES', False)
        and await has_user_permission('notes')
    ):
        builtin_functions.extend([search_notes, view_note, write_note, replace_note_content])

    # Channels tools - search channels and messages
    if (
        is_builtin_tool_enabled('channels')
        and getattr(request.app.state.config, 'ENABLE_CHANNELS', False)
        and await has_user_permission('channels')
    ):
        builtin_functions.extend(
            [
                search_channels,
                search_channel_messages,
                view_channel_thread,
                view_channel_message,
            ]
        )

    # Skills tools - view_skill allows model to load full skill instructions on demand
    if extra_params.get('__skill_ids__'):
        builtin_functions.append(view_skill)

    # Task management - break down complex work into trackable steps
    if is_builtin_tool_enabled('tasks'):
        builtin_functions.extend([create_tasks, update_task])

    # Automation tools - create and manage scheduled automations from chat
    if (
        is_builtin_tool_enabled('automations')
        and getattr(request.app.state.config, 'ENABLE_AUTOMATIONS', False)
        and await has_user_permission('automations')
    ):
        builtin_functions.extend(
            [create_automation, update_automation, list_automations, toggle_automation, delete_automation]
        )

    # Calendar tools - search/create/update/delete events
    if (
        is_builtin_tool_enabled('calendar')
        and getattr(request.app.state.config, 'ENABLE_CALENDAR', False)
        and await has_user_permission('calendar')
    ):
        builtin_functions.extend(
            [search_calendar_events, create_calendar_event, update_calendar_event, delete_calendar_event]
        )

    for func in builtin_functions:
        callable = await get_async_tool_function_and_apply_extra_params(
            func,
            {
                '__request__': request,
                '__user__': extra_params.get('__user__', {}),
                '__event_emitter__': extra_params.get('__event_emitter__'),
                '__event_call__': extra_params.get('__event_call__'),
                '__metadata__': extra_params.get('__metadata__'),
                '__chat_id__': extra_params.get('__chat_id__'),
                '__message_id__': extra_params.get('__message_id__'),
                '__model_knowledge__': model_knowledge,
            },
        )

        # Generate spec from function
        pydantic_model = convert_function_to_pydantic_model(func)
        spec = convert_pydantic_model_to_openai_function_spec(pydantic_model)
        spec = clean_openai_tool_schema(spec)

        tools_dict[func.__name__] = {
            'tool_id': f'builtin:{func.__name__}',
            'callable': callable,
            'spec': spec,
            'type': 'builtin',
        }

    return tools_dict


async def get_pm_builtin_tools(
    request: Request, extra_params: dict, user: UserModel
) -> dict[str, dict]:
    """注册 PM 项目上下文工具（get_pm_module_entries / get_pm_entry_detail）。

    与 get_builtin_tools 不同，本函数只注册 PM 工具，且不依赖
    function_calling 模式——调用方负责决定是否调用本函数
    （通常基于 pm_project_id 存在 + 意图识别通过）。

    Returns:
        tools_dict 条目，key 为工具名，value 为 {'tool_id', 'callable', 'spec', 'type'}。
    """
    tools_dict = {}
    pm_project_id = (extra_params.get('__metadata__') or {}).get('pm_project_id')
    if not pm_project_id:
        return tools_dict

    from open_webui.pm.chat_context import get_pm_entry_detail_full, get_pm_module_entries_full

    async def get_pm_module_entries(
        module_type: str,
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """读取 PM 项目中指定模块的全部条目详情（含完整描述）。

        Args:
            module_type: 模块类型，如 requirement / parameter / risk / schedule / roadmap / meeting / testcase / faq / acceptance / competitor / prototype / spec / flowchart / prd / architecture / requirement-boundary

        Returns:
            JSON 字符串，包含该模块所有条目的 title / status / priority / content（content 截断 500 字）/ data。
        """
        pid = __metadata__.get('pm_project_id')
        if not pid or not __user__:
            return '{"error": "未选择项目或用户未认证"}'
        # __user__ 是 dict（来自 user.model_dump()），构造回 UserModel 以便访问校验
        from open_webui.models.users import UserModel

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        entries = await get_pm_module_entries_full(module_type, pid, user_obj)
        return json.dumps(entries, ensure_ascii=False, indent=2)

    async def get_pm_entry_detail(
        entry_id: str,
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """读取 PM 项目中单条目的完整内容（不截断）。

        Args:
            entry_id: 条目 ID

        Returns:
            JSON 字符串，包含该条目的完整 content 和 data 字段。
        """
        if not __user__:
            return '{"error": "用户未认证"}'
        from open_webui.models.users import UserModel

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        entry = await get_pm_entry_detail_full(entry_id, user_obj)
        return json.dumps(entry, ensure_ascii=False, indent=2)

    # D33: PM 写入工具 — 让 AI 在 chat 中通过 function calling 直接创建/更新条目、
    # 创建条目版本、创建关联。修复「AI 调用 write_pm_module_entries 失败」问题 ——
    # 该函数名是 AI 编造的，实际不存在；现在提供真实可调用的 builtin 工具。
    # 与工作流 pm_module 节点路径并存（D27 双路径决策），AI 按场景自主选择。
    async def pm_entry_create(
        module_type: str,
        title: str,
        content: str = '',
        data: dict = {},
        status: str = 'draft',
        priority: str = 'medium',
        parent_id: str = None,
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """在当前 PM 项目中创建一条新条目。仅在用户明确要求创建时调用。

        Args:
            module_type: 模块类型，如 prd / architecture / requirement / parameter / risk / schedule / roadmap / meeting / testcase / faq / acceptance / competitor / prototype / spec / flowchart / requirement-boundary
            title: 条目标题
            content: 条目正文（PRD/架构等富文本可为 Markdown）
            data: 条目结构化数据（如参数表的字段定义、竞品的对比维度等）
            status: 条目状态，如 draft / approved / archived
            priority: 优先级，如 low / medium / high
            parent_id (str, optional): 父条目 ID（写入 data.parent_entry_id，用于模块/功能/参数层级链接）

        Returns:
            JSON 字符串，包含 success / entry_id / title。
        """
        pid = __metadata__.get('pm_project_id')
        if not pid or not __user__:
            return '{"error": "未选择项目或用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.models.pm import PMEntries, PMEntryForm
        from open_webui.pm.chat_context import _verify_project_access

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        if not await _verify_project_access(pid, user_obj):
            return '{"error": "无权限访问该项目"}'
        # Merge parent_id into data JSON as parent_entry_id (D44: 工具层加 parent_id 支持)
        effective_data = dict(data or {})
        if parent_id:
            effective_data['parent_entry_id'] = parent_id
        form = PMEntryForm(
            project_id=pid,
            module_type=module_type,
            title=title,
            content=content,
            data=effective_data,
            status=status,
            priority=priority,
        )
        entry = await PMEntries.insert_new_entry(user_obj.id, form)
        return json.dumps(
            {
                'success': entry is not None,
                'entry_id': entry.id if entry else None,
                'title': entry.title if entry else None,
            },
            ensure_ascii=False,
        )

    async def pm_entry_update(
        entry_id: str,
        title: str = None,
        content: str = None,
        data: dict = None,
        status: str = None,
        priority: str = None,
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """更新已存在的 PM 条目。仅在用户明确要求更新时调用。

        Args:
            entry_id: 条目 ID
            title: 新标题（可选）
            content: 新正文（可选）
            data: 新结构化数据（可选，整体替换）
            status: 新状态（可选）
            priority: 新优先级（可选）

        Returns:
            JSON 字符串，包含 success / entry_id / title。
        """
        if not __user__:
            return '{"error": "用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.models.pm import PMEntries, PMEntryUpdateForm, PMProjects

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        # 校验条目归属：先取条目，再校验项目属于用户
        entry = await PMEntries.get_entry_by_id(entry_id)
        if not entry:
            return '{"error": "条目不存在"}'
        project = await PMProjects.get_project_by_id(entry.project_id)
        if not project or project.user_id != user_obj.id:
            return '{"error": "无权限访问该条目"}'
        update_data: dict = {}
        if title is not None:
            update_data['title'] = title
        if content is not None:
            update_data['content'] = content
        if data is not None:
            update_data['data'] = data
        if status is not None:
            update_data['status'] = status
        if priority is not None:
            update_data['priority'] = priority
        if not update_data:
            return '{"error": "未提供任何更新字段"}'
        form = PMEntryUpdateForm(**update_data)
        updated = await PMEntries.update_entry_by_id(entry_id, form)
        return json.dumps(
            {
                'success': updated is not None,
                'entry_id': updated.id if updated else None,
                'title': updated.title if updated else None,
            },
            ensure_ascii=False,
        )

    async def pm_entry_version_create(
        entry_id: str,
        change_summary: str = '',
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """为已存在的 PM 条目创建一个版本快照（PMEntryVersion）。仅在用户明确要求保存版本时调用。

        Args:
            entry_id: 条目 ID
            change_summary: 版本变更说明

        Returns:
            JSON 字符串，包含 success / version_id / version_number。
        """
        if not __user__:
            return '{"error": "用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.models.pm import PMEntries, PMEntryVersions, PMEntryVersionForm, PMProjects

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        entry = await PMEntries.get_entry_by_id(entry_id)
        if not entry:
            return '{"error": "条目不存在"}'
        project = await PMProjects.get_project_by_id(entry.project_id)
        if not project or project.user_id != user_obj.id:
            return '{"error": "无权限访问该条目"}'
        version_form = PMEntryVersionForm(
            entry_id=entry_id,
            project_id=entry.project_id,
            module_type=entry.module_type,
            content=entry.content,
            entry_metadata=entry.data,
            change_summary=change_summary or 'Version snapshot',
        )
        version = await PMEntryVersions.insert_new_version(user_obj.id, version_form)
        return json.dumps(
            {
                'success': version is not None,
                'version_id': version.id if version else None,
                'version_number': version.version_number if version else None,
            },
            ensure_ascii=False,
        )

    async def pm_relation_create(
        entity_a_id: str,
        entity_b_id: str,
        relation_type: str,
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """在当前 PM 项目中创建两个条目之间的关联。仅在用户明确要求建立关联时调用。

        Args:
            entity_a_id: 起始条目 ID
            entity_b_id: 目标条目 ID
            relation_type: 关联类型，如 depends_on / related_to / verifies / derived_from

        Returns:
            JSON 字符串，包含 success / relation_id。
        """
        pid = __metadata__.get('pm_project_id')
        if not pid or not __user__:
            return '{"error": "未选择项目或用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.models.pm import PMRelations, PMRelationForm
        from open_webui.pm.chat_context import _verify_project_access

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        if not await _verify_project_access(pid, user_obj):
            return '{"error": "无权限访问该项目"}'
        relation_form = PMRelationForm(
            project_id=pid,
            entity_a_id=entity_a_id,
            entity_b_id=entity_b_id,
            relation_type=relation_type,
            created_by=user_obj.id,
        )
        relation = await PMRelations.insert_new_relation(user_obj.id, relation_form)
        return json.dumps(
            {
                'success': relation is not None,
                'relation_id': relation.id if relation else None,
            },
            ensure_ascii=False,
        )

    # D43: 批量写入工具 —— 消除 B1 系统提示与工具实现脱节导致的新幻觉源。
    # 系统提示(chat_context.py:246-248)已列出本工具名，必须真实注册，否则 AI 按提示合法调用却失败。
    async def pm_entry_batch_create(
        module_type: str,
        entries: list[dict],
        parent_id: str = None,
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """批量创建条目。一次写入多条架构条目，避免多次循环调用 pm_entry_create。

        Args:
            module_type: 模块类型，如 'product-architecture' / 'prd' / 'requirement'
            entries: 条目列表，每项含 title / content(可选) / data(可选) / status(可选) / priority(可选)。
                每项还可含 parent_entry_id（覆盖外层 parent_id）。若 entry 未自带 parent_entry_id
                且外层 parent_id 提供，则把外层 parent_id 写入 entry.data.parent_entry_id。
            parent_id (str, optional): 外层 fallback parent_id。每个 entry 未自带 parent_entry_id 时使用。

        Returns:
            JSON 字符串，含 created / failed / total。
        """
        pid = __metadata__.get('pm_project_id')
        if not pid or not __user__:
            return '{"error": "未选择项目或用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.models.pm import PMEntries, PMEntryForm
        from open_webui.pm.chat_context import _verify_project_access

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        if not await _verify_project_access(pid, user_obj):
            return '{"error": "无权限访问该项目"}'

        created = []
        failed = []
        for entry in entries or []:
            try:
                # D44: parent_entry_id fallback —— entry 自带优先，外层 parent_id 兜底
                effective_parent = entry.get('parent_entry_id', parent_id)
                entry_data = dict(entry.get('data') or {})
                if effective_parent:
                    entry_data['parent_entry_id'] = effective_parent
                form = PMEntryForm(
                    project_id=pid,
                    module_type=module_type,
                    title=entry.get('title', f'{module_type} entry'),
                    content=entry.get('content', ''),
                    data=entry_data,
                    status=entry.get('status', 'draft'),
                    priority=entry.get('priority', 'medium'),
                )
                new_entry = await PMEntries.insert_new_entry(user_obj.id, form)
                if new_entry:
                    created.append({'id': new_entry.id, 'title': new_entry.title})
                else:
                    failed.append({'title': entry.get('title'), 'error': 'insert returned None'})
            except Exception as e:
                failed.append({'title': entry.get('title'), 'error': str(e)})
        return json.dumps(
            {
                'created': created,
                'failed': failed,
                'total': len(entries or []),
                'success_count': len(created),
            },
            ensure_ascii=False,
        )

    # D43/D38: 批量写入预览工具 —— 不真实写入，返回结构化预览供用户确认。
    # 与 pm_entry_batch_create 配对：AI 先调 preview → 前端渲染确认卡片 → 用户确认后调真实写入。
    async def pm_entry_batch_create_preview(
        module_type: str,
        entries: list[dict],
        parent_id: str = None,
        __metadata__: dict = {},
        __user__=None,
    ) -> str:
        """批量创建条目前的预览（不真实写入）。返回结构化预览供用户确认。

        Args:
            module_type: 模块类型
            entries: 待创建条目列表，每项含 title / content(可选) / data(可选) / parent_entry_id(可选)
            parent_id (str, optional): 外层 fallback parent_id。每个 entry 未自带 parent_entry_id 时使用。

        Returns:
            JSON 字符串，含 preview / will_create_count / warnings / confirm_tool。
        """
        pid = __metadata__.get('pm_project_id')
        if not pid or not __user__:
            return '{"error": "未选择项目或用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.pm.chat_context import _verify_project_access

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        if not await _verify_project_access(pid, user_obj):
            return '{"error": "无权限访问该项目"}'

        warnings = []
        preview = []
        for i, entry in enumerate(entries or []):
            title = (entry.get('title') or '').strip()
            if not title:
                warnings.append(f'第 {i+1} 条缺少 title，将被跳过')
                continue
            content_raw = entry.get('content', '') or ''
            content_len = len(content_raw)
            # D44: parent_entry_id fallback —— entry 自带优先，外层 parent_id 兜底
            effective_parent = entry.get('parent_entry_id', parent_id)
            preview.append({
                'index': i,
                'title': title,
                'content_preview': content_raw[:80] + ('...' if content_len > 80 else ''),
                'data_keys': list(entry.get('data', {}).keys()) if entry.get('data') else [],
                'parent_entry_id': effective_parent,
            })
        return json.dumps(
            {
                'preview': preview,
                'will_create_count': len(preview),
                'warnings': warnings,
                'confirm_tool': 'pm_entry_batch_create',
                'module_type': module_type,
                'fallback_parent_id': parent_id,
            },
            ensure_ascii=False,
        )

    # Bug 8 (v10): 注册 pm_entry_delete —— 补齐 CRUD 中的 Delete 能力。
    # 底层 delete_entry_by_id (models/pm.py L753) 已实现，本工具仅做权限校验 + 包装。
    # 配合 OperationPreviewModal 强制确认流程（D96）：本工具支持 confirmed 参数，
    # 当 confirmed=False 时返回 needs_confirmation，前端弹窗，用户确认后 AI 重调 confirmed=True。
    # 流式改造（v15）：新增 __event_call__ 注入参数。当 confirmed=False 且 __event_call__ 可用时，
    # 工具直接通过 __event_call__ 同步触发前端确认弹窗并阻塞等待用户响应，无需后端再扫 messages。
    # __event_call__ 不可用时（legacy 管道）退化为旧的 needs_confirmation JSON 行为。
    async def pm_entry_delete(
        entry_id: str,
        confirmed: bool = False,
        __metadata__: dict = {},
        __user__=None,
        __event_call__: Optional[Callable] = None,
    ) -> str:
        """删除已存在的 PM 条目（硬删除，不可恢复）。

        ⚠️ 危险操作：必须先以 confirmed=False 调用本工具获取预览，用户在前端弹窗确认后，
        再以 confirmed=True 重调本工具执行真正的删除。

        在支持 __event_call__ 的流式管道（OpenWebUI 0.9.6+）中，confirmed=False 会同步触发
        前端确认弹窗并阻塞等待用户响应：用户点"确认删除"后返回 user_confirmed=true，AI 应以
        confirmed=True 重新调用本工具完成真正删除；用户点"取消"返回 cancelled=true。
        在 legacy 管道（__event_call__ 为 None）下退化为返回 needs_confirmation=true JSON，
        由后端 _agent_chat_native 扫 messages 转前端 actions。

        Args:
            entry_id: 要删除的条目 ID
            confirmed: 是否已获用户确认。默认 False（返回预览不删除）。

        Returns:
            - confirmed=False 且 __event_call__ 可用：用户确认后返回 {user_confirmed, entry_id, entry_title, message}；
              用户取消时返回 {cancelled, entry_id, entry_title, message}
            - confirmed=False 且 __event_call__ 不可用：JSON {needs_confirmation, operation, entry_id, entry_title, module_type, content_preview, message}
            - confirmed=True 时：JSON 字符串，含 success / entry_id / title
        """
        if not __user__:
            return '{"error": "用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.models.pm import PMEntries, PMProjects

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        entry = await PMEntries.get_entry_by_id(entry_id)
        if not entry:
            return '{"error": "条目不存在"}'
        project = await PMProjects.get_project_by_id(entry.project_id)
        if not project or project.user_id != user_obj.id:
            return '{"error": "无权限删除该条目"}'

        # Phase 1: preview (no execution)
        if not confirmed:
            content_preview = (entry.content or '')[:200]
            # 流式管道：用 __event_call__ 同步触发前端确认弹窗并阻塞等待用户响应
            if __event_call__ is not None:
                try:
                    response = await __event_call__(
                        {
                            'type': 'pm.entry.confirm',
                            'data': {
                                'operation': 'delete',
                                'entry_id': entry_id,
                                'entry_title': entry.title,
                                'module_type': entry.module_type,
                                'content_preview': content_preview,
                                'message': f'即将删除条目「{entry.title}」，此操作不可撤销。',
                                'buttons': [
                                    {'id': 'confirm', 'label': '确认删除', 'primary': True, 'value': True},
                                    {'id': 'cancel', 'label': '取消', 'primary': False, 'value': False},
                                ],
                            },
                        }
                    )
                except Exception as e:
                    # 异常（超时 / 前端断开 / 类型错误）退化为 legacy needs_confirmation JSON
                    return json.dumps(
                        {
                            'needs_confirmation': True,
                            'operation': 'delete',
                            'entry_id': entry_id,
                            'entry_title': entry.title,
                            'module_type': entry.module_type,
                            'content_preview': content_preview,
                            'message': f'即将删除条目「{entry.title}」，此操作不可撤销。',
                            'fallback_reason': f'__event_call__ failed: {e}',
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                # 兼容多种前端响应格式：{'confirmed': True/False}、{'action': 'confirm'/'cancel'}、
                # {'confirmed': 'confirm'/'cancel'}、{'value': True/False}
                confirmed_by_user = False
                if isinstance(response, dict):
                    if response.get('confirmed') is True or response.get('value') is True:
                        confirmed_by_user = True
                    elif response.get('action') == 'confirm':
                        confirmed_by_user = True
                    elif response.get('confirmed') == 'confirm':
                        confirmed_by_user = True
                if confirmed_by_user:
                    return json.dumps(
                        {
                            'user_confirmed': True,
                            'operation': 'delete',
                            'entry_id': entry_id,
                            'entry_title': entry.title,
                            'message': f'用户已在前端确认删除条目「{entry.title}」，请以 confirmed=True 重新调用本工具执行真正的删除。',
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                return json.dumps(
                    {
                        'cancelled': True,
                        'operation': 'delete',
                        'entry_id': entry_id,
                        'entry_title': entry.title,
                        'message': '用户取消了删除操作。',
                    },
                    ensure_ascii=False,
                    indent=2,
                )

            # Legacy: 返回 needs_confirmation JSON，由 _agent_chat_native 扫 messages 转前端 actions
            return json.dumps(
                {
                    'needs_confirmation': True,
                    'operation': 'delete',
                    'entry_id': entry_id,
                    'entry_title': entry.title,
                    'module_type': entry.module_type,
                    'content_preview': content_preview,
                    'message': f'即将删除条目「{entry.title}」，此操作不可撤销。',
                },
                ensure_ascii=False,
                indent=2,
            )

        # Phase 2: confirmed execution
        title = entry.title
        deleted = await PMEntries.delete_entry_by_id(entry_id)
        return json.dumps(
            {
                'success': deleted is not None,
                'entry_id': entry_id,
                'title': title,
            },
            ensure_ascii=False,
        )

    # D44: PRD → 模块-功能-参数 原子化转换工具。
    # 包装 PRDToMFPSkill.transform() —— skill 内部用 LLM 提取结构化 JSON，
    # 然后 5 步原子化创建（模块→功能→参数），任一步失败 hard delete 回滚。
    # 双链接：data.parent_entry_id（ID-based） + data.moduleName/featureName（name-based，供前端 moduleFields.ts 编辑器读取）
    async def pm_prd_to_mfp_transform(
        prd_entry_id: str,
        __metadata__: dict = {},
        __user__=None,
        __request__=None,
    ) -> str:
        """将 PRD 条目原子化转换为模块-功能-参数层级。

        读取 PRD 完整内容，内部用 LLM 提取结构化 JSON，一次性创建所有模块/功能/参数条目
        （含 parent_entry_id 和 moduleName/featureName 双链接）。失败时自动回滚。

        Args:
            prd_entry_id: PRD 条目 ID（通过 get_pm_module_entries(module_type=prd) 查询）

        Returns:
            JSON 字符串，含 success / created_modules / created_functions / created_parameters
            / total / by_module / rolled_back / error
        """
        pid = __metadata__.get('pm_project_id')
        if not pid or not __user__:
            return '{"success": false, "error": "未选择项目或用户未认证"}'
        from open_webui.models.users import UserModel
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill
        from open_webui.pm.chat_context import _verify_project_access

        user_obj = UserModel(**__user__) if isinstance(__user__, dict) else __user__
        if not await _verify_project_access(pid, user_obj):
            return '{"success": false, "error": "无权限访问该项目"}'

        skill = PRDToMFPSkill()
        result = await skill.transform(
            prd_entry_id=prd_entry_id,
            user=user_obj,
            metadata=__metadata__,
            request=__request__,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    pm_functions = [
        get_pm_module_entries,
        get_pm_entry_detail,
        pm_entry_create,                   # D33: 写入工具
        pm_entry_update,                   # D33: 写入工具
        pm_entry_version_create,           # D33: 写入工具
        pm_relation_create,                # D33: 写入工具
        pm_entry_batch_create,             # D43: 批量写入（消除 B1 提示与实现脱节）
        pm_entry_batch_create_preview,     # D43/D38: 批量写入预览（不真实写入）
        pm_entry_delete,                   # Bug 8 (v10): 删除工具（confirmed 二阶段）
        pm_prd_to_mfp_transform,           # D44: PRD 原子化转模块-功能-参数（含层级链接）
    ]
    for func in pm_functions:
        callable = await get_async_tool_function_and_apply_extra_params(
            func,
            {
                '__request__': request,
                '__user__': extra_params.get('__user__', {}),
                '__event_emitter__': extra_params.get('__event_emitter__'),
                '__event_call__': extra_params.get('__event_call__'),
                '__metadata__': extra_params.get('__metadata__'),
                '__chat_id__': extra_params.get('__chat_id__'),
                '__message_id__': extra_params.get('__message_id__'),
                '__model_knowledge__': None,
            },
        )
        pydantic_model = convert_function_to_pydantic_model(func)
        spec = convert_pydantic_model_to_openai_function_spec(pydantic_model)
        spec = clean_openai_tool_schema(spec)
        tools_dict[func.__name__] = {
            'tool_id': f'builtin:{func.__name__}',
            'callable': callable,
            'spec': spec,
            'type': 'builtin',
        }
    return tools_dict


def parse_description(docstring: str | None) -> str:
    """
    Parse a function's docstring to extract the description.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        str: The description.
    """

    if not docstring:
        return ''

    lines = [line.strip() for line in docstring.strip().split('\n')]
    description_lines: list[str] = []

    for line in lines:
        if re.match(r':param', line) or re.match(r':return', line):
            break

        description_lines.append(line)

    return '\n'.join(description_lines)


def parse_docstring(docstring):
    """
    Parse a function's docstring to extract parameter descriptions in reST format.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        dict: A dictionary where keys are parameter names and values are descriptions.
    """
    if not docstring:
        return {}

    # Regex to match `:param name: description` format
    param_pattern = re.compile(r':param (\w+):\s*(.+)')
    param_descriptions = {}

    for line in docstring.splitlines():
        match = param_pattern.match(line.strip())
        if not match:
            continue
        param_name, param_description = match.groups()
        if param_name.startswith('__'):
            continue
        param_descriptions[param_name] = param_description

    return param_descriptions


def convert_function_to_pydantic_model(func: Callable) -> type[BaseModel]:
    """
    Converts a Python function's type hints and docstring to a Pydantic model,
    including support for nested types, default values, and descriptions.

    Args:
        func: The function whose type hints and docstring should be converted.
        model_name: The name of the generated Pydantic model.

    Returns:
        A Pydantic model class.
    """
    type_hints = get_type_hints(func)
    signature = inspect.signature(func)
    parameters = signature.parameters

    docstring = func.__doc__

    function_description = parse_description(docstring)
    function_param_descriptions = parse_docstring(docstring)

    field_defs = {}
    for name, param in parameters.items():
        type_hint = type_hints.get(name, Any)
        default_value = param.default if param.default is not param.empty else ...

        param_description = function_param_descriptions.get(name, None)

        if param_description:
            field_defs[name] = (
                type_hint,
                Field(default_value, description=param_description),
            )
        else:
            field_defs[name] = type_hint, default_value

    model = create_model(func.__name__, **field_defs)
    model.__doc__ = function_description

    return model


def clean_properties(schema: dict):
    if not isinstance(schema, dict):
        return

    if 'anyOf' in schema:
        non_null_types = [t for t in schema['anyOf'] if t.get('type') != 'null']
        if len(non_null_types) == 1:
            schema.update(non_null_types[0])
            del schema['anyOf']
        else:
            schema['anyOf'] = non_null_types

    if 'default' in schema and schema['default'] is None:
        del schema['default']

    # fix missing type
    if 'type' not in schema and 'anyOf' not in schema and 'properties' not in schema:
        schema['type'] = 'string'

    if 'properties' in schema:
        for prop_name, prop_schema in schema['properties'].items():
            clean_properties(prop_schema)

    if 'items' in schema:
        clean_properties(schema['items'])


def clean_openai_tool_schema(spec: dict) -> dict:

    cleaned_spec = copy.deepcopy(spec)

    if 'parameters' in cleaned_spec:
        clean_properties(cleaned_spec['parameters'])

    return cleaned_spec


def get_functions_from_tool(tool: object) -> list[Callable]:
    return [
        getattr(tool, func)
        for func in dir(tool)
        if callable(getattr(tool, func))  # checks if the attribute is callable (a method or function).
        and not func.startswith('_')  # filters out internal methods (starting with _) and special (dunder) methods.
        and not inspect.isclass(
            getattr(tool, func)
        )  # ensures that the callable is not a class itself, just a method or function.
    ]


def get_tool_specs(tool_module: object) -> list[dict]:
    function_models = map(convert_function_to_pydantic_model, get_functions_from_tool(tool_module))

    specs = [
        clean_openai_tool_schema(convert_pydantic_model_to_openai_function_spec(function_model))
        for function_model in function_models
    ]

    return specs


# Valid HTTP methods per OpenAPI 3.x – used to skip extension keys (x-*)
# and non-operation path-item fields (summary, description, servers, parameters).
OPENAPI_HTTP_METHODS = {'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'}


def resolve_schema(schema, components, resolved_schemas=None):
    """
    Recursively resolves a JSON schema using OpenAPI components.
    """
    if not schema:
        return {}

    if resolved_schemas is None:
        resolved_schemas = set()

    if '$ref' in schema:
        ref_path = schema['$ref']
        schema_name = ref_path.split('/')[-1]

        if schema_name in resolved_schemas:
            # Avoid infinite recursion on circular references
            return {}

        resolved_schemas.add(schema_name)

        ref_parts = ref_path.strip('#/').split('/')
        resolved = components
        for part in ref_parts[1:]:  # Skip the initial 'components'
            resolved = resolved.get(part, {})
        return resolve_schema(resolved, components, resolved_schemas)

    resolved_schema = copy.deepcopy(schema)

    # Recursively resolve inner schemas
    if 'properties' in resolved_schema:
        for prop, prop_schema in resolved_schema['properties'].items():
            resolved_schema['properties'][prop] = resolve_schema(prop_schema, components)

    if 'items' in resolved_schema:
        resolved_schema['items'] = resolve_schema(resolved_schema['items'], components)

    # Resolve composition keywords (oneOf, anyOf, allOf) which may contain $ref
    for keyword in ('oneOf', 'anyOf', 'allOf'):
        if keyword in resolved_schema and isinstance(resolved_schema[keyword], list):
            resolved_schema[keyword] = [
                resolve_schema(inner, components, resolved_schemas) for inner in resolved_schema[keyword]
            ]

    return resolved_schema


def convert_openapi_to_tool_payload(openapi_spec):
    """
    Converts an OpenAPI specification into a custom tool payload structure.

    Args:
        openapi_spec (dict): The OpenAPI specification as a Python dict.

    Returns:
        list: A list of tool payloads.
    """
    tool_payload = []

    for path, methods in openapi_spec.get('paths', {}).items():
        if not isinstance(methods, dict):
            continue

        # Path-level parameters apply to all operations under this path
        # unless overridden at the operation level (matched by name + in).
        path_level_params = methods.get('parameters', [])
        if not isinstance(path_level_params, list):
            path_level_params = []

        for method, operation in methods.items():
            if method not in OPENAPI_HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            if operation.get('operationId'):
                tool = {
                    'name': operation.get('operationId'),
                    'description': operation.get(
                        'description',
                        operation.get('summary', 'No description available.'),
                    ),
                    'parameters': {'type': 'object', 'properties': {}, 'required': []},
                }

                # Merge path-level and operation-level parameters.
                # Operation-level params override path-level params with the
                # same (name, in) pair per the OpenAPI spec.
                op_params = operation.get('parameters', [])
                if not isinstance(op_params, list):
                    op_params = []
                merged_params = {}
                for param in path_level_params:
                    if isinstance(param, dict) and param.get('name'):
                        merged_params[(param['name'], param.get('in', ''))] = param
                for param in op_params:
                    if isinstance(param, dict) and param.get('name'):
                        merged_params[(param['name'], param.get('in', ''))] = param

                for param in merged_params.values():
                    param_name = param.get('name')
                    if not param_name:
                        continue
                    param_schema = param.get('schema', {})
                    description = param_schema.get('description', '')
                    if not description:
                        description = param.get('description') or ''
                    if param_schema.get('enum') and isinstance(param_schema.get('enum'), list):
                        description += f'. Possible values: {", ".join(str(v) for v in param_schema.get("enum"))}'
                    param_property = {
                        'type': param_schema.get('type') or 'string',
                        'description': description,
                    }

                    # Include items property for array types (required by OpenAI)
                    if param_schema.get('type') == 'array' and 'items' in param_schema:
                        param_property['items'] = param_schema['items']

                    # Filter out None values to prevent schema validation errors
                    param_property = {k: v for k, v in param_property.items() if v is not None}

                    tool['parameters']['properties'][param_name] = param_property
                    if param.get('required'):
                        tool['parameters']['required'].append(param_name)

                # Extract and resolve requestBody if available
                request_body = operation.get('requestBody')
                if request_body:
                    content = request_body.get('content', {})
                    json_schema = content.get('application/json', {}).get('schema')
                    if json_schema:
                        resolved_schema = resolve_schema(json_schema, openapi_spec.get('components', {}))

                        if resolved_schema.get('properties'):
                            tool['parameters']['properties'].update(resolved_schema['properties'])
                            if 'required' in resolved_schema:
                                tool['parameters']['required'] = list(
                                    set(tool['parameters']['required'] + resolved_schema['required'])
                                )
                        elif resolved_schema.get('type') == 'array':
                            tool['parameters'] = resolved_schema  # special case for array

                tool_payload.append(tool)

    return tool_payload


async def set_tool_servers(request: Request):
    try:
        request.app.state.TOOL_SERVERS = await get_tool_servers_data(request.app.state.config.TOOL_SERVER_CONNECTIONS)
    except Exception as e:
        log.error(f'Error fetching tool server data: {e}')
        request.app.state.TOOL_SERVERS = getattr(request.app.state, 'TOOL_SERVERS', None) or []

    try:
        if request.app.state.redis is not None:
            await request.app.state.redis.set(
                f'{REDIS_KEY_PREFIX}:tool_servers', json.dumps(request.app.state.TOOL_SERVERS)
            )
    except Exception as e:
        log.error(f'Error caching tool_servers to Redis: {e}')

    return request.app.state.TOOL_SERVERS


async def get_tool_servers(request: Request):
    try:
        tool_servers = []
        if request.app.state.redis is not None:
            try:
                tool_servers = json.loads(await request.app.state.redis.get(f'{REDIS_KEY_PREFIX}:tool_servers'))
                request.app.state.TOOL_SERVERS = tool_servers
            except Exception as e:
                log.error(f'Error fetching tool_servers from Redis: {e}')

        if not tool_servers:
            tool_servers = await set_tool_servers(request)

        return tool_servers
    except Exception as e:
        log.error(f'Failed to load tool servers, skipping: {e}')
        return getattr(request.app.state, 'TOOL_SERVERS', None) or []


async def get_terminal_cwd(
    base_url: str,
    headers: dict,
    cookies: dict | None = None,
) -> str | None:
    """Fetch the current working directory from a terminal server."""
    try:
        cwd_url = f'{base_url.rstrip("/")}/files/cwd'
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            trust_env=True,
        ) as session:
            async with session.get(
                cwd_url, headers=headers, cookies=cookies or {}, ssl=AIOHTTP_CLIENT_SESSION_SSL
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('cwd')
    except Exception as e:
        log.debug(f'Failed to fetch terminal CWD: {e}')
    return None


async def get_terminal_system_prompt(
    base_url: str,
    headers: dict,
    cookies: dict | None = None,
) -> str | None:
    """Fetch the system prompt from a terminal server.

    Checks ``/api/config`` for the ``system`` feature flag first;
    only fetches ``/system`` if the flag is present.  Returns *None*
    silently when the server doesn't support the endpoint.
    """
    base = base_url.rstrip('/')
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=3),
            trust_env=True,
        ) as session:
            # 1. Check feature flag
            async with session.get(f'{base}/api/config', ssl=AIOHTTP_CLIENT_SESSION_SSL) as resp:
                if resp.status != 200:
                    return None
                config = await resp.json()
                if not config.get('features', {}).get('system'):
                    return None

            # 2. Fetch system prompt
            async with session.get(
                f'{base}/system', headers=headers, cookies=cookies or {}, ssl=AIOHTTP_CLIENT_SESSION_SSL
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('prompt')
    except Exception as e:
        log.debug(f'Failed to fetch terminal system prompt: {e}')
    return None


async def set_terminal_servers(request: Request):
    """Load and cache OpenAPI specs from all TERMINAL_SERVER_CONNECTIONS."""
    connections = request.app.state.config.TERMINAL_SERVER_CONNECTIONS or []

    # Build server configs compatible with get_tool_servers_data
    # Terminal connections store id/name at top level; translate to info dict
    server_configs = []
    for connection in connections:
        if not connection.get('url'):
            continue

        enabled = connection.get('enabled', True)

        base_url = connection.get('url', '').rstrip('/')
        policy_id = connection.get('policy_id', '')

        # Orchestrator connections route through /p/{policy_id}/ — the
        # OpenAPI spec lives on the proxied terminal, not the orchestrator.
        if connection.get('server_type') == 'orchestrator' and policy_id:
            base_url = f'{base_url}/p/{policy_id}'

        server_configs.append(
            {
                'url': base_url,
                'key': connection.get('key', ''),
                'auth_type': connection.get('auth_type', 'bearer'),
                'path': connection.get('path', '/openapi.json'),
                'spec_type': 'url',
                # get_tool_servers_data reads config.enable to filter active servers
                'config': {'enable': enabled},
                'info': {
                    'id': connection.get('id', ''),
                    'name': connection.get('name', ''),
                },
            }
        )

    request.app.state.TERMINAL_SERVERS = await get_tool_servers_data(server_configs)

    # Fetch system prompts concurrently (runs at cache time, not per-request)
    connections_by_id = {c.get('id'): c for c in connections if c.get('id')}

    async def _fetch_system_prompt(server):
        connection = connections_by_id.get(server.get('id'))
        if not connection:
            return
        headers = {}
        if connection.get('auth_type', 'bearer') == 'bearer':
            headers['Authorization'] = f'Bearer {connection.get("key", "")}'
        prompt = await get_terminal_system_prompt(server['url'], headers)
        if prompt:
            server['system_prompt'] = prompt

    await asyncio.gather(
        *[_fetch_system_prompt(s) for s in request.app.state.TERMINAL_SERVERS],
        return_exceptions=True,
    )

    if request.app.state.redis is not None:
        await request.app.state.redis.set(
            f'{REDIS_KEY_PREFIX}:terminal_servers', json.dumps(request.app.state.TERMINAL_SERVERS)
        )

    return request.app.state.TERMINAL_SERVERS


async def get_terminal_servers(request: Request):
    """Return cached terminal server specs, loading if needed."""
    terminal_servers = []
    if request.app.state.redis is not None:
        try:
            terminal_servers = json.loads(await request.app.state.redis.get(f'{REDIS_KEY_PREFIX}:terminal_servers'))
            request.app.state.TERMINAL_SERVERS = terminal_servers
        except Exception as e:
            log.error(f'Error fetching terminal_servers from Redis: {e}')

    if not terminal_servers:
        terminal_servers = await set_terminal_servers(request)

    return terminal_servers


async def get_terminal_tools(
    request: Request,
    terminal_id: str,
    user: UserModel,
    extra_params: dict,
) -> dict[str, dict] | tuple[dict[str, dict], str | None]:
    """Resolve tools for a terminal server identified by terminal_id.

    - Finds the connection in TERMINAL_SERVER_CONNECTIONS
    - Checks access_grants
    - Loads specs from cache
    - Builds callables that route through the terminal proxy
    """
    connections = request.app.state.config.TERMINAL_SERVER_CONNECTIONS or []
    connection = next((c for c in connections if c.get('id') == terminal_id), None)
    if connection is None:
        log.warning(f'Terminal server not found: {terminal_id}')
        return {}

    user_group_ids = {group.id for group in await Groups.get_groups_by_member_id(user.id)}
    if not await has_connection_access(user, connection, user_group_ids):
        log.warning(f'Access denied to terminal {terminal_id} for user {user.id}')
        return {}

    # Find the cached spec data for this terminal
    terminal_servers = await get_terminal_servers(request)
    server_data = next((s for s in terminal_servers if s.get('id') == terminal_id), None)
    if server_data is None:
        log.warning(f'Terminal server spec not found for {terminal_id}')
        return {}

    specs = server_data.get('specs', [])
    if not specs:
        return {}

    # Build auth headers
    auth_type = connection.get('auth_type', 'bearer')
    cookies = {}
    headers = {'Content-Type': 'application/json', 'X-User-Id': user.id}

    if auth_type == 'bearer':
        headers['Authorization'] = f'Bearer {connection.get("key", "")}'
    elif auth_type == 'session':
        cookies = request.cookies
        headers['Authorization'] = f'Bearer {request.state.token.credentials}'
    elif auth_type == 'system_oauth':
        cookies = request.cookies
        oauth_token = extra_params.get('__oauth_token__', None)
        if oauth_token:
            headers['Authorization'] = f'Bearer {oauth_token.get("access_token", "")}'
    # auth_type == "none": no Authorization header

    system_prompt = server_data.get('system_prompt')

    # Use chat_id as the per-session key for cwd tracking
    metadata = extra_params.get('__metadata__', {})
    session_id = metadata.get('chat_id')
    if session_id:
        headers['X-Session-Id'] = session_id

    terminal_cwd = await get_terminal_cwd(connection.get('url', ''), headers, cookies)

    tools_dict = {}
    for spec in specs:
        function_name = spec['name']
        tool_spec = clean_openai_tool_schema(spec)

        if function_name == 'run_command' and terminal_cwd:
            tool_spec['description'] = (
                tool_spec.get('description', '') + f'\n\nThe current working directory is: {terminal_cwd}'
            )

        async def make_tool_function(fn_name, srv_data, hdrs, cks):
            async def tool_function(**kwargs):
                return await execute_tool_server(
                    url=srv_data['url'],
                    headers=hdrs,
                    cookies=cks,
                    name=fn_name,
                    params=kwargs,
                    server_data=srv_data,
                )

            return tool_function

        tool_function = await make_tool_function(function_name, server_data, headers, cookies)
        callable = await get_async_tool_function_and_apply_extra_params(tool_function, {})

        tools_dict[function_name] = {
            'tool_id': f'terminal:{terminal_id}',
            'callable': callable,
            'spec': tool_spec,
            'type': 'terminal',
        }

    return tools_dict, system_prompt


async def get_tool_server_data(url: str, headers: dict | None) -> dict[str, Any]:
    _headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    if headers:
        _headers.update(headers)

    error = None
    try:
        timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(url, headers=_headers, ssl=AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL) as response:
                if response.status != 200:
                    error_body = await response.json()
                    raise Exception(error_body)

                text_content = await response.text()

                # Check if URL ends with .yaml or .yml to determine format
                if url.lower().endswith(('.yaml', '.yml')):
                    res = yaml.safe_load(text_content)
                else:
                    try:
                        res = json.loads(text_content)
                    except json.JSONDecodeError:
                        # Fall back to YAML for non-.yml URLs that aren't valid JSON
                        res = yaml.safe_load(text_content)

    except Exception as err:
        log.exception(f'Could not fetch tool server spec from {url}')
        if isinstance(err, dict) and 'detail' in err:
            error = err['detail']
        else:
            error = str(err)
        raise Exception(error)

    log.debug(f'Fetched data: {res}')
    return res


async def get_tool_servers_data(servers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Prepare list of enabled servers along with their original index

    tasks = []
    server_entries = []
    for idx, server in enumerate(servers):
        if server.get('config', {}).get('enable') and server.get('type', 'openapi') == 'openapi':
            info = server.get('info', {})

            auth_type = server.get('auth_type', 'bearer')
            token = None

            if auth_type == 'bearer':
                token = server.get('key', '')
            elif auth_type == 'none':
                # No authentication
                pass

            id = info.get('id')
            if not id:
                id = str(idx)

            server_url = server.get('url')
            spec_type = server.get('spec_type', 'url')

            # Create async tasks to fetch data
            task = None
            if spec_type == 'url':
                # Path (to OpenAPI spec URL) can be either a full URL or a path to append to the base URL
                openapi_path = server.get('path', 'openapi.json')
                spec_url = get_tool_server_url(server_url, openapi_path)
                # Fetch from URL
                task = get_tool_server_data(
                    spec_url,
                    {'Authorization': f'Bearer {token}'} if token else None,
                )
            elif spec_type == 'json' and server.get('spec', ''):
                # Use provided JSON spec
                spec_json = None
                try:
                    spec_json = json.loads(server.get('spec', ''))
                except Exception as e:
                    log.error(f'Error parsing JSON spec for tool server {id}: {e}')

                if spec_json:
                    task = asyncio.sleep(
                        0,
                        result=spec_json,
                    )

            if task:
                tasks.append(task)
                server_entries.append((id, idx, server, server_url, info, token))

    # Execute tasks concurrently
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Build final results with index and server metadata
    results = []
    for (id, idx, server, url, info, _), response in zip(server_entries, responses):
        if isinstance(response, Exception):
            log.error(f'Failed to connect to {url} OpenAPI tool server')
            continue

        # Guard against invalid or non-OpenAPI specs (e.g., MCP-style configs)
        if not isinstance(response, dict) or 'paths' not in response:
            log.warning(f"Invalid OpenAPI spec from {url}: missing 'paths'")
            continue

        response = {
            'openapi': response,
            'info': response.get('info', {}),
            'specs': convert_openapi_to_tool_payload(response),
        }

        openapi_data = response.get('openapi', {})
        if info and isinstance(openapi_data, dict):
            openapi_data['info'] = openapi_data.get('info', {})

            if 'name' in info:
                openapi_data['info']['title'] = info.get('name', 'Tool Server')

            if 'description' in info:
                openapi_data['info']['description'] = info.get('description', '')

        results.append(
            {
                'id': str(id),
                'idx': idx,
                'url': (server.get('url') or '').rstrip('/'),
                'openapi': openapi_data,
                'info': response.get('info'),
                'specs': response.get('specs'),
            }
        )

    return results


async def execute_tool_server(
    url: str,
    headers: dict[str, str],
    cookies: dict[str, str],
    name: str,
    params: dict[str, Any],
    server_data: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any | None]]:
    error = None
    try:
        openapi = server_data.get('openapi', {})
        paths = openapi.get('paths', {})

        matching_route = None
        for route_path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for http_method, operation in methods.items():
                if http_method not in OPENAPI_HTTP_METHODS:
                    continue
                if isinstance(operation, dict) and operation.get('operationId') == name:
                    matching_route = (route_path, methods)
                    break
            if matching_route:
                break

        if not matching_route:
            raise Exception(f'No matching route found for operationId: {name}')

        route_path, methods = matching_route

        method_entry = None
        for http_method, operation in methods.items():
            if http_method not in OPENAPI_HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            if operation.get('operationId') == name:
                method_entry = (http_method.lower(), operation)
                break

        if not method_entry:
            raise Exception(f'No matching method found for operationId: {name}')

        http_method, operation = method_entry

        path_params = {}
        query_params = {}
        body_params = {}

        # Merge path-level and operation-level parameters for execution.
        path_level_params = methods.get('parameters', [])
        if not isinstance(path_level_params, list):
            path_level_params = []
        op_params = operation.get('parameters', [])
        if not isinstance(op_params, list):
            op_params = []
        merged_params = {}
        for param in path_level_params:
            if isinstance(param, dict) and param.get('name'):
                merged_params[(param['name'], param.get('in', ''))] = param
        for param in op_params:
            if isinstance(param, dict) and param.get('name'):
                merged_params[(param['name'], param.get('in', ''))] = param

        for param in merged_params.values():
            param_name = param.get('name')
            if not param_name:
                continue
            param_in = param.get('in')
            if param_name in params:
                if param_in == 'path':
                    path_params[param_name] = params[param_name]
                if param_in == 'query':
                    value = params[param_name]
                    # Skip empty values for optional params (LLMs sometimes
                    # pass "" instead of omitting optional parameters).
                    if value is None or (value == '' and not param.get('required')):
                        continue
                    query_params[param_name] = value

        final_url = f'{url.rstrip("/")}{route_path}'
        for key, value in path_params.items():
            final_url = final_url.replace(f'{{{key}}}', quote(str(value), safe=''))

        if query_params:
            final_url = f'{final_url}?{urlencode(query_params)}'

        if operation.get('requestBody', {}).get('content'):
            if params:
                body_params = params

        async with aiohttp.ClientSession(
            trust_env=True, timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER)
        ) as session:
            request_method = getattr(session, http_method.lower())

            if http_method in ['post', 'put', 'patch', 'delete']:
                async with request_method(
                    final_url,
                    json=body_params,
                    headers=headers,
                    cookies=cookies,
                    ssl=AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL,
                    allow_redirects=AIOHTTP_CLIENT_ALLOW_REDIRECTS,
                ) as response:
                    if response.status >= 400:
                        text = await response.text()
                        raise Exception(f'HTTP error {response.status}: {text}')

                    try:
                        response_data = await response.json()
                    except Exception:
                        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
                        if content_type.startswith('text/') or not content_type:
                            response_data = await response.text()
                        else:
                            raw = await response.read()
                            b64 = base64.b64encode(raw).decode()
                            response_data = f'data:{content_type};base64,{b64}'

                    response_headers = response.headers
                    return (response_data, response_headers)
            else:
                async with request_method(
                    final_url,
                    headers=headers,
                    cookies=cookies,
                    ssl=AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL,
                    allow_redirects=AIOHTTP_CLIENT_ALLOW_REDIRECTS,
                ) as response:
                    if response.status >= 400:
                        text = await response.text()
                        raise Exception(f'HTTP error {response.status}: {text}')

                    try:
                        response_data = await response.json()
                    except Exception:
                        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
                        if content_type.startswith('text/') or not content_type:
                            response_data = await response.text()
                        else:
                            raw = await response.read()
                            b64 = base64.b64encode(raw).decode()
                            response_data = f'data:{content_type};base64,{b64}'

                    response_headers = response.headers
                    return (response_data, response_headers)

    except Exception as err:
        error = str(err)
        log.warning(f'API Request Error: {error}')
        return ({'error': error}, None)


def get_tool_server_url(url: str | None, path: str) -> str:
    """
    Build the full URL for a tool server, given a base url and a path.
    """
    if '://' in path:
        # If it contains "://", it's a full URL
        return path
    if url:
        url = url.rstrip('/')
    if not path.startswith('/'):
        # Ensure the path starts with a slash
        path = f'/{path}'
    return f'{url}{path}'
