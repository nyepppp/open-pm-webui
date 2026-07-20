"""Workflow API router for standalone workflow designer."""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from open_webui.pm.models.workflow import (
    WorkflowEdgeForm,
    WorkflowExecutionForm,
    WorkflowForm,
    WorkflowNodeForm,
)
from open_webui.pm.services.workflow_service import WorkflowService
from open_webui.utils.auth import get_verified_user
from open_webui.services.workflow.ai_generator import ai_workflow_generator
from open_webui.services.workflow.bpmn_converter import bpmn_converter
from open_webui.services.workflow.json_converter import json_converter
from open_webui.services.workflow.engine import workflow_execution_engine
from open_webui.services.workflow.websocket import workflow_websocket_manager

log = logging.getLogger(__name__)

router = APIRouter(tags=["workflows"])


def _parse_workflow_json(workflow: dict) -> dict:
    """Parse JSON string fields in workflow to objects for frontend."""
    if not workflow:
        return workflow
    try:
        workflow["nodes"] = json.loads(workflow.get("nodes", "[]"))
    except (json.JSONDecodeError, TypeError):
        workflow["nodes"] = []
    try:
        workflow["edges"] = json.loads(workflow.get("edges", "[]"))
    except (json.JSONDecodeError, TypeError):
        workflow["edges"] = []
    return workflow


def _parse_nodes_from_form(form_data: WorkflowForm) -> List[Dict[str, Any]]:
    """从 WorkflowForm 中解析 nodes 列表（form_data.nodes 可能是 JSON 字符串或列表）。"""
    raw = form_data.nodes if hasattr(form_data, 'nodes') else "[]"
    if isinstance(raw, str):
        try:
            return json.loads(raw) if raw else []
        except (json.JSONDecodeError, TypeError):
            return []
    if isinstance(raw, list):
        return raw
    return []


@router.post("/")
async def create_workflow(
    request: Request,
    form_data: WorkflowForm,
    user=Depends(get_verified_user),
):
    """Create a new workflow."""
    # 保存前校验节点引用的扩展资源是否存在
    nodes = _parse_nodes_from_form(form_data)
    validation_errors = await _validate_workflow_references(nodes)
    if validation_errors:
        first = validation_errors[0]
        raise HTTPException(
            status_code=400,
            detail={
                "node_id": first.node_id,
                "node_name": first.node_name,
                "error": first.error,
                "all_errors": [e.model_dump() for e in validation_errors],
            },
        )
    workflow = await WorkflowService.create_workflow(form_data)
    if not workflow:
        raise HTTPException(status_code=400, detail="Failed to create workflow")
    return _parse_workflow_json(workflow)


@router.get("/")
async def get_workflows(
    request: Request,
    user=Depends(get_verified_user),
):
    """Get all workflows for the current user."""
    workflows = await WorkflowService.get_all_workflows()
    return [_parse_workflow_json(w) for w in workflows]


class AIWorkflowGenerateRequest(BaseModel):
    """AI 生成工作流入参。"""

    description: str
    model_id: str
    template_hint: Optional[str] = None
    history: Optional[list[dict]] = None  # D1: 多轮澄清历史 [{role, content}, ...]


def _sse_event(data: dict) -> str:
    """将 dict 序列化为 SSE data 行。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# 注意：/ai-generate 必须声明在 /{workflow_id} 通配路由之前，
# 否则 POST /ai-generate 会被 /{workflow_id} 匹配并因方法不符返回 405。
@router.post("/ai-generate")
async def ai_generate_workflow(
    request: Request,
    form_data: AIWorkflowGenerateRequest,
    user=Depends(get_verified_user),
):
    """AI 流式生成工作流（D1: 多轮澄清，无轮次上限）。

    通过 SSE 推送事件：
    - {type: 'status', content: '...'} — 生成过程状态
    - {type: 'clarify', questions: [...]} — AI 追问，前端收集答案后带 history 重新请求
    - {type: 'result', workflow: {...}, warnings: [...]} — 最终结果
    - {type: 'error', content: '...'} — 错误
    """
    if not form_data.description or not form_data.description.strip():
        raise HTTPException(status_code=400, detail="description 不能为空")
    if not form_data.model_id:
        raise HTTPException(status_code=400, detail="model_id 不能为空")

    async def event_stream() -> AsyncIterator[str]:
        # 使用 asyncio.Queue 在 progress_callback 和 SSE 流之间传递事件
        # 消息协议：
        #   ("status", {"type": "status", "content": "..."})  — 进度事件
        #   ("result", result_dict)                          — 生成完成
        #   ("error", exception)                             — 异常
        queue: asyncio.Queue = asyncio.Queue()

        async def progress_callback(msg: str):
            await queue.put(("status", {"type": "status", "content": msg}))

        async def run_generation():
            try:
                result = await ai_workflow_generator.generate_workflow_with_clarify(
                    description=form_data.description,
                    model_id=form_data.model_id,
                    user=user,
                    request=request,
                    history=form_data.history,
                    template_hint=form_data.template_hint,
                    progress_callback=progress_callback,
                )
                await queue.put(("result", result))
            except Exception as e:  # noqa: BLE001
                log.error("AI workflow generation failed: %s", e, exc_info=True)
                await queue.put(("error", e))

        task = asyncio.create_task(run_generation())

        try:
            # 初始事件，让前端立即看到状态
            yield _sse_event({"type": "status", "content": "正在启动 AI 生成…"})

            while True:
                item = await queue.get()
                kind = item[0]

                if kind == "status":
                    yield _sse_event(item[1])
                elif kind == "result":
                    result = item[1]
                    action = result.get("action")
                    if action == "ask":
                        # AI 追问 — 前端收集答案后带 history 重新请求
                        yield _sse_event({
                            "type": "clarify",
                            "questions": result.get("questions", []),
                        })
                    else:
                        # action == 'generate' — 返回最终结果
                        workflow = result.get("workflow", {}) or {}
                        warnings = result.get("warnings", []) or workflow.get("warnings", []) or []
                        yield _sse_event({
                            "type": "result",
                            "workflow": workflow,
                            "warnings": warnings,
                        })
                    break
                elif kind == "error":
                    yield _sse_event(
                        {"type": "error", "content": f"AI 生成失败：{str(item[1])}"}
                    )
                    break
        finally:
            # 确保 background task 完成，避免悬挂
            if not task.done():
                try:
                    await asyncio.wait_for(task, timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get workflow by ID."""
    try:
        workflow = await WorkflowService.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return _parse_workflow_json(workflow)
    except HTTPException:
        raise
    except Exception as e:
        log.error(
            "get_workflow failed: workflow_id=%s user=%s path=%s error_type=%s error=%s",
            workflow_id,
            getattr(user, "id", None),
            request.url.path,
            type(e).__name__,
            e,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"加载工作流失败: {e}")


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: Request,
    form_data: WorkflowForm,
    user=Depends(get_verified_user),
):
    """Update a workflow."""
    # 保存前校验节点引用的扩展资源是否存在
    nodes = _parse_nodes_from_form(form_data)
    validation_errors = await _validate_workflow_references(nodes)
    if validation_errors:
        first = validation_errors[0]
        raise HTTPException(
            status_code=400,
            detail={
                "node_id": first.node_id,
                "node_name": first.node_name,
                "error": first.error,
                "all_errors": [e.model_dump() for e in validation_errors],
            },
        )
    workflow = await WorkflowService.update_workflow(workflow_id, form_data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _parse_workflow_json(workflow)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Delete a workflow."""
    success = await WorkflowService.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted"}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: Request,
    input_data: dict,
    user=Depends(get_verified_user),
):
    """Execute a workflow using the execution engine."""
    try:
        workflow = await WorkflowService.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # 从 input_data 中提取聊天模型 ID（前端注入），但不污染 workflow 变量
        chat_model_id = input_data.pop("_chat_model_id", None) if isinstance(input_data, dict) else None

        execution_id = await workflow_execution_engine.execute(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=user.id if user else None,
            chat_model_id=chat_model_id
        )

        return {
            "execution_id": execution_id,
            "status": "running",
            "message": "Workflow execution started"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/{workflow_id}/executions/{execution_id}/status")
async def get_execution_status(
    workflow_id: str,
    execution_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get workflow execution status."""
    try:
        status = await workflow_execution_engine.get_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")


class ResumeHumanInputRequest(BaseModel):
    """Resume human_input 节点的请求体。"""
    node_id: str
    response: Dict[str, Any] = {}


@router.post("/runs/{execution_id}/resume")
async def resume_workflow_run(
    execution_id: str,
    body: ResumeHumanInputRequest,
    user=Depends(get_verified_user),
):
    """恢复挂起在 human_input 节点的 workflow execution。

    前端在收到 awaiting_input 事件后弹出表单，用户提交后调用本端点，
    engine 唤醒对应 asyncio.Event，继续执行下游节点。
    """
    try:
        ok = await workflow_execution_engine.resume_human_input(
            execution_id, body.node_id, body.response
        )
        if not ok:
            raise HTTPException(
                status_code=404,
                detail="No suspended human_input node found for this execution_id + node_id",
            )
        return {"status": "resumed", "execution_id": execution_id, "node_id": body.node_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume: {str(e)}")


# Export/Import endpoints

@router.post("/{workflow_id}/export/json")
async def export_workflow_json(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Export workflow to JSON format."""
    workflow = await WorkflowService.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Parse nodes and edges
    workflow_data = _parse_workflow_json(workflow)
    
    # Convert to JSON
    json_content = json_converter.workflow_to_json(workflow_data)
    
    return {
        "content": json_content,
        "filename": f"{workflow_data.get('name', 'workflow').replace(' ', '_')}.json",
        "content_type": "application/json"
    }


@router.post("/{workflow_id}/export/bpmn")
async def export_workflow_bpmn(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Export workflow to BPMN 2.0 XML format."""
    workflow = await WorkflowService.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Parse nodes and edges
    workflow_data = _parse_workflow_json(workflow)
    
    # Convert to BPMN
    bpmn_content = bpmn_converter.workflow_to_bpmn(workflow_data)
    
    return {
        "content": bpmn_content,
        "filename": f"{workflow_data.get('name', 'workflow').replace(' ', '_')}.bpmn",
        "content_type": "application/xml"
    }


@router.post("/import/json")
async def import_workflow_json(
    request: Request,
    user=Depends(get_verified_user),
):
    """Import workflow from JSON format."""
    try:
        body = await request.json()
        json_content = body.get("content", "")
        if not json_content:
            raise HTTPException(status_code=400, detail="No content provided")
        
        # Parse JSON
        workflow_data = json_converter.json_to_workflow(json_content)
        
        # Create workflow
        form_data = WorkflowForm(
            name=workflow_data.get("name", "Imported Workflow"),
            description=workflow_data.get("description", ""),
            nodes=json.dumps(workflow_data.get("nodes", [])),
            edges=json.dumps(workflow_data.get("edges", [])),
        )
        
        workflow = await WorkflowService.create_workflow(form_data)
        if not workflow:
            raise HTTPException(status_code=400, detail="Failed to create workflow")
        
        return _parse_workflow_json(workflow)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


@router.post("/import/bpmn")
async def import_workflow_bpmn(
    request: Request,
    user=Depends(get_verified_user),
):
    """Import workflow from BPMN 2.0 XML format."""
    try:
        body = await request.json()
        bpmn_content = body.get("content", "")
        if not bpmn_content:
            raise HTTPException(status_code=400, detail="No content provided")
        
        # Parse BPMN
        workflow_data = bpmn_converter.bpmn_to_workflow(bpmn_content)
        
        # Create workflow
        form_data = WorkflowForm(
            name=workflow_data.get("name", "Imported Workflow"),
            description=workflow_data.get("description", ""),
            nodes=json.dumps(workflow_data.get("nodes", [])),
            edges=json.dumps(workflow_data.get("edges", [])),
        )
        
        workflow = await WorkflowService.create_workflow(form_data)
        if not workflow:
            raise HTTPException(status_code=400, detail="Failed to create workflow")
        
        return _parse_workflow_json(workflow)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid BPMN: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")


############################
# Extensions Routes (Part A)
# 为工作流编辑器提供 openwebui 扩展资源下拉列表数据
############################


def _normalize_tool_spec(spec: dict) -> List[Dict[str, Any]]:
    """将 openwebui Tool 的 OpenAPI 规范转换为 PropertyPanel 可渲染的入参字段定义。

    返回 [{name, type, description, required}] 列表。
    """
    parameters = spec.get("parameters", {}) or {}
    props = parameters.get("properties", {}) or {}
    required_list = parameters.get("required", []) or []
    fields: List[Dict[str, Any]] = []
    for prop_name, prop_schema in props.items():
        fields.append({
            "name": prop_name,
            "type": prop_schema.get("type", "string"),
            "description": prop_schema.get("description", ""),
            "required": prop_name in required_list,
        })
    return fields


@router.get("/extensions/tools")
async def list_extension_tools(
    request: Request,
    user=Depends(get_verified_user),
):
    """列出所有已注册的 openwebui Tools，供 tool_call 节点下拉选择。"""
    from open_webui.models.tools import Tools
    from open_webui.utils.tools import get_tool_specs

    result: List[Dict[str, Any]] = []
    try:
        tools = await Tools.get_tools()
        for tool in tools:
            # 每个 Tool 可能有多个 specs（多个可调用函数），展开为独立条目
            specs = tool.specs or []
            if not specs:
                result.append({
                    "id": tool.id,
                    "name": tool.name,
                    "description": (tool.meta.description if tool.meta else None) or tool.name,
                    "spec": [],
                })
            else:
                for spec in specs:
                    spec_name = spec.get("name", tool.name)
                    result.append({
                        "id": f"{tool.id}:{spec_name}",
                        "name": f"{tool.name} / {spec_name}",
                        "description": spec.get("description", "") or (tool.meta.description if tool.meta else "") or tool.name,
                        "spec": _normalize_tool_spec(spec),
                    })
    except Exception as e:
        log.error(f"Failed to list extension tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {e}")
    return result


@router.get("/extensions/functions")
async def list_extension_functions(
    request: Request,
    user=Depends(get_verified_user),
):
    """列出所有已注册的 openwebui Functions，供 function_call 节点下拉选择。"""
    from open_webui.models.functions import Functions

    result: List[Dict[str, Any]] = []
    try:
        functions = await Functions.get_functions()
        for fn in functions:
            meta = fn.meta or {}
            # Function 的入参 spec 从 meta.manifest 推断，无则返回空列表
            manifest = meta.manifest if isinstance(meta, dict) else None
            manifest = manifest or {}
            spec_fields: List[Dict[str, Any]] = []
            if isinstance(manifest, dict):
                input_schema = manifest.get("input_schema") or manifest.get("parameters") or {}
                if isinstance(input_schema, dict):
                    props = input_schema.get("properties", {}) or {}
                    required_list = input_schema.get("required", []) or []
                    for prop_name, prop_schema in props.items():
                        spec_fields.append({
                            "name": prop_name,
                            "type": prop_schema.get("type", "string") if isinstance(prop_schema, dict) else "string",
                            "description": prop_schema.get("description", "") if isinstance(prop_schema, dict) else "",
                            "required": prop_name in required_list,
                        })
            result.append({
                "id": fn.id,
                "name": fn.name,
                "description": (meta.description if isinstance(meta, dict) else None) or f"{fn.type} function",
                "spec": spec_fields,
            })
    except Exception as e:
        log.error(f"Failed to list extension functions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list functions: {e}")
    return result


@router.get("/extensions/skills")
async def list_extension_skills(
    request: Request,
    user=Depends(get_verified_user),
):
    """列出所有已注册的 openwebui Skills，供 skill_call 节点下拉选择。"""
    from open_webui.models.skills import Skills

    result: List[Dict[str, Any]] = []
    try:
        skills = await Skills.get_skills()
        for skill in skills:
            meta = skill.meta or {}
            spec_fields: List[Dict[str, Any]] = []
            # Skill 的入参 spec 从 meta.input_schema 推断
            input_schema = meta.get("input_schema") if isinstance(meta, dict) else None
            input_schema = input_schema or {}
            if isinstance(input_schema, dict):
                props = input_schema.get("properties", {}) or {}
                required_list = input_schema.get("required", []) or []
                for prop_name, prop_schema in props.items():
                    spec_fields.append({
                        "name": prop_name,
                        "type": prop_schema.get("type", "string") if isinstance(prop_schema, dict) else "string",
                        "description": prop_schema.get("description", "") if isinstance(prop_schema, dict) else "",
                        "required": prop_name in required_list,
                    })
            result.append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description or skill.name,
                "spec": spec_fields,
            })
    except Exception as e:
        log.error(f"Failed to list extension skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list skills: {e}")
    return result


@router.get("/extensions/mcp")
async def list_extension_mcp(
    request: Request,
    user=Depends(get_verified_user),
):
    """列出所有已配置的 MCP servers 及其 tools，供 mcp_call 节点二级下拉选择。

    返回扁平列表 [{id, name, description, server_id, server_name, spec?}]，
    每个条目代表一个 MCP tool，前端按 server_id 分组渲染二级联动。
    """
    from open_webui.utils.tools import get_tool_servers

    result: List[Dict[str, Any]] = []
    try:
        servers = await get_tool_servers(request)
        for server in servers:
            # 只处理 MCP 类型的 server
            if server.get("type", "openapi") != "mcp":
                continue
            server_id = server.get("id", "")
            server_name = server.get("name", server_id)
            # server 已预取的 tools 列表
            tools = server.get("tools", []) or []
            for tool in tools:
                tool_name = tool.get("name", "")
                tool_id = f"{server_id}:{tool_name}"
                # tool 的 inputSchema 转换为 spec 字段
                spec_fields: List[Dict[str, Any]] = []
                input_schema = tool.get("parameters") or tool.get("inputSchema") or {}
                if isinstance(input_schema, dict):
                    props = input_schema.get("properties", {}) or {}
                    required_list = input_schema.get("required", []) or []
                    for prop_name, prop_schema in props.items():
                        spec_fields.append({
                            "name": prop_name,
                            "type": prop_schema.get("type", "string") if isinstance(prop_schema, dict) else "string",
                            "description": prop_schema.get("description", "") if isinstance(prop_schema, dict) else "",
                            "required": prop_name in required_list,
                        })
                result.append({
                    "id": tool_id,
                    "name": tool_name,
                    "description": tool.get("description", "") or tool_name,
                    "server_id": server_id,
                    "server_name": server_name,
                    "spec": spec_fields,
                })
    except Exception as e:
        log.error(f"Failed to list extension mcp: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list mcp: {e}")
    return result


############################
# 运行时数据流追踪 (Part B - B)
############################


@router.get("/{workflow_id}/executions/{execution_id}/node/{node_id}")
async def get_execution_node_detail(
    workflow_id: str,
    execution_id: str,
    node_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """返回某次执行中某节点的运行时详情：input / output / tool_call 详情 / write_target 结果 / 耗时。"""
    try:
        status = await workflow_execution_engine.get_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        node_results = status.get("node_results", {}) or {}
        if node_id not in node_results:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found in execution {execution_id}")
        node_result = node_results[node_id]
        # 从 workflow 节点定义中取节点名和类型
        node_name = node_id
        node_type = "unknown"
        workflow = await WorkflowService.get_workflow(workflow_id)
        if workflow:
            try:
                nodes = json.loads(workflow.get("nodes", "[]")) if isinstance(workflow.get("nodes"), str) else workflow.get("nodes", [])
                for n in nodes:
                    if n.get("id") == node_id:
                        node_name = n.get("name", node_id)
                        node_type = n.get("type", "unknown")
                        break
            except (json.JSONDecodeError, TypeError):
                pass
        # 组装详情
        detail = {
            "node_id": node_id,
            "node_name": node_name,
            "node_type": node_type,
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": node_result.get("status"),
            "output": node_result.get("output"),
            "error": node_result.get("error"),
            "execution_time_ms": node_result.get("execution_time_ms"),
            "tool_call": None,
            "write_target": None,
            # FAIL-3: answer 节点实际写入 PM 条目后返回的 entry_id，前端用于生成跳转链接
            "write_target_entry_id": None,
        }
        # 对扩展节点，从 output 中提取 tool_call 详情
        output = node_result.get("output") or {}
        if isinstance(output, dict):
            if node_type in ("tool_call", "function_call", "skill_call", "mcp_call"):
                detail["tool_call"] = {
                    "extension_id": output.get("extension_id") or output.get("tool_name"),
                    "input": output.get("input") or output.get("parameters"),
                    "output": output.get("result") or output.get("response"),
                }
            elif node_type == "answer":
                # answer 节点若 write_target 是 PM 模块，提取写入结果
                # 从节点 config 中提取 write_target（如果存在）
                for n in (nodes if isinstance(nodes, list) else []):
                    if n.get("id") == node_id:
                        cfg = n.get("config", {})
                        if isinstance(cfg, str):
                            try:
                                cfg = json.loads(cfg)
                            except (json.JSONDecodeError, TypeError):
                                cfg = {}
                        if isinstance(cfg, dict):
                            wt = cfg.get("write_target")
                            if wt:
                                detail["write_target"] = wt
                            # FAIL-3: 从节点 config 中提取 projectId/moduleType，
                            # 前端链接需要这两个信息
                            detail["write_target_project_id"] = cfg.get("project_id")
                            detail["write_target_module"] = cfg.get("module_type") or wt
                        break
                # FAIL-3: 从执行 output 中提取实际写入的 entry_id
                # 兼容多种返回结构：output.entry_id / output.id / output.result.entry_id ...
                entry_id = output.get("entry_id") or output.get("id")
                if not entry_id:
                    entry_val = output.get("entry")
                    if isinstance(entry_val, dict):
                        entry_id = entry_val.get("id") or entry_val.get("entry_id")
                if not entry_id:
                    result_val = output.get("result")
                    if isinstance(result_val, dict):
                        entry_id = result_val.get("entry_id") or result_val.get("id")
                if entry_id:
                    detail["write_target_entry_id"] = entry_id
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node detail: {str(e)}")


############################
# 设计期静态校验 (Part B - C)
############################


class WorkflowValidationErrorDetail(BaseModel):
    node_id: str
    node_name: str
    error: str


async def _validate_workflow_references(nodes: List[Dict[str, Any]]) -> List[WorkflowValidationErrorDetail]:
    """校验工作流节点引用的扩展资源是否存在。

    在保存路由的 Pydantic 校验之后、业务逻辑之前调用。
    返回错误列表，空列表表示通过。
    """
    errors: List[WorkflowValidationErrorDetail] = []
    if not nodes:
        return errors

    # 懒加载各资源 ID 集合
    _tool_ids: Optional[set] = None
    _function_ids: Optional[set] = None
    _skill_ids: Optional[set] = None
    _mcp_tool_ids: Optional[set] = None

    async def _ensure_tool_ids():
        nonlocal _tool_ids
        if _tool_ids is None:
            from open_webui.models.tools import Tools
            tools = await Tools.get_tools()
            _tool_ids = {t.id for t in tools}
        return _tool_ids

    async def _ensure_function_ids():
        nonlocal _function_ids
        if _function_ids is None:
            from open_webui.models.functions import Functions
            fns = await Functions.get_functions()
            _function_ids = {f.id for f in fns}
        return _function_ids

    async def _ensure_skill_ids():
        nonlocal _skill_ids
        if _skill_ids is None:
            from open_webui.models.skills import Skills
            skills = await Skills.get_skills()
            _skill_ids = {s.id for s in skills}
        return _skill_ids

    # PM 模块类型白名单（与 PropertyPanel PM_MODULE_TYPES 对齐）
    PM_MODULE_TYPES_WHITELIST = {
        'prd', 'requirement', 'requirement-boundary', 'roadmap', 'parameter',
        'architecture', 'prototype', 'competitor', 'spec', 'flowchart',
        'schedule', 'testcase', 'risk', 'meeting', 'acceptance', 'faq'
    }

    for node in nodes:
        node_id = node.get("id", "")
        node_name = node.get("name", node_id)
        node_type = node.get("type", "")
        config = node.get("config", {})
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except (json.JSONDecodeError, TypeError):
                config = {}

        if node_type == "pm_module":
            module_type = config.get("module_type", "")
            if module_type and module_type not in PM_MODULE_TYPES_WHITELIST:
                errors.append(WorkflowValidationErrorDetail(
                    node_id=node_id,
                    node_name=node_name,
                    error=f"PM 模块类型 '{module_type}' 不在合法清单中",
                ))

        elif node_type == "agent":
            agent_id = config.get("agent_id", "")
            if agent_id:
                # agent_id 校验：目前 openwebui agent 通过 Agents 表注册
                try:
                    from open_webui.models.agents import Agents
                    agent = await Agents.get_agent_by_id(agent_id)
                    if not agent:
                        errors.append(WorkflowValidationErrorDetail(
                            node_id=node_id,
                            node_name=node_name,
                            error=f"agent '{agent_id}' 不存在",
                        ))
                except ImportError:
                    # Agents 模型可能不存在，跳过校验
                    pass

        elif node_type in ("tool_call", "function_call", "skill_call", "mcp_call"):
            extension_id = config.get("extension_id", "") or config.get("tool_name", "")
            if not extension_id:
                errors.append(WorkflowValidationErrorDetail(
                    node_id=node_id,
                    node_name=node_name,
                    error=f"{node_type} 节点未配置 extension_id",
                ))
                continue
            # 对于 tool_call，extension_id 可能是 "tool_id:spec_name" 格式，取前半部分
            check_id = extension_id.split(":")[0] if ":" in extension_id else extension_id
            try:
                if node_type == "tool_call":
                    ids = await _ensure_tool_ids()
                    if check_id not in ids:
                        errors.append(WorkflowValidationErrorDetail(
                            node_id=node_id, node_name=node_name,
                            error=f"tool '{extension_id}' 不存在，请重新选择",
                        ))
                elif node_type == "function_call":
                    ids = await _ensure_function_ids()
                    if check_id not in ids:
                        errors.append(WorkflowValidationErrorDetail(
                            node_id=node_id, node_name=node_name,
                            error=f"function '{extension_id}' 不存在，请重新选择",
                        ))
                elif node_type == "skill_call":
                    ids = await _ensure_skill_ids()
                    if check_id not in ids:
                        errors.append(WorkflowValidationErrorDetail(
                            node_id=node_id, node_name=node_name,
                            error=f"skill '{extension_id}' 不存在，请重新选择",
                        ))
                elif node_type == "mcp_call":
                    # mcp_call 的 extension_id 是 "server_id:tool_name" 格式
                    # 通过 MCP extensions 路由验证（此处简化：只检查非空）
                    server_id = config.get("server_id", "")
                    if not server_id:
                        errors.append(WorkflowValidationErrorDetail(
                            node_id=node_id, node_name=node_name,
                            error=f"mcp_call 节点未配置 server_id",
                        ))
            except Exception as e:
                log.warning(f"Extension validation lookup failed for {node_id}: {e}")

        elif node_type == "answer":
            write_target = config.get("write_target", "")
            if write_target and write_target not in PM_MODULE_TYPES_WHITELIST:
                # write_target 可能是 "pm:<module_type>" 或直接 module_type
                target_module = write_target.split(":")[-1] if ":" in write_target else write_target
                if target_module not in PM_MODULE_TYPES_WHITELIST:
                    errors.append(WorkflowValidationErrorDetail(
                        node_id=node_id,
                        node_name=node_name,
                        error=f"answer 节点的 write_target '{write_target}' 不是合法 PM 模块",
                    ))

    return errors
