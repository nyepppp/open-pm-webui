"""DEPRECATED / UNREGISTERED: 此文件未在 main.py 中注册，实际路由在
backend/open_webui/routers/workflows.py。保留此文件供历史参考，
后续应删除。请勿在此文件中修改 workflow 路由逻辑。
"""

"""Workflow API router for PM workspace workflow designer."""

import json
from typing import AsyncIterator, Optional

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
from open_webui.services.workflow.ai_generator import ai_workflow_generator
from open_webui.utils.auth import get_verified_user

router = APIRouter()


class AIWorkflowGenerateRequest(BaseModel):
    """AI 生成工作流入参。"""

    description: str
    model_id: str
    template_hint: Optional[str] = None


def _sse_event(data: dict) -> str:
    """将 dict 序列化为 SSE data 行。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/ai-generate")
async def ai_generate_workflow(
    request: Request,
    form_data: AIWorkflowGenerateRequest,
    user=Depends(get_verified_user),
):
    """AI 流式生成工作流。

    通过 SSE 推送两类事件：
    - {type: 'status', content: '...'} — 生成过程状态
    - {type: 'result', workflow: {...}, warnings: [...]} — 最终结果
    - {type: 'error', content: '...'} — 错误
    """
    if not form_data.description or not form_data.description.strip():
        raise HTTPException(status_code=400, detail="description 不能为空")
    if not form_data.model_id:
        raise HTTPException(status_code=400, detail="model_id 不能为空")

    async def event_stream() -> AsyncIterator[str]:
        try:
            yield _sse_event({"type": "status", "content": "正在分析需求…"})

            # 走模板匹配快速路径检测（同步、零延迟）
            template_match = ai_workflow_generator._match_template(form_data.description)
            if template_match:
                yield _sse_event(
                    {"type": "status", "content": f"命中模板：{template_match['name']}"}
                )
            else:
                yield _sse_event({"type": "status", "content": "正在调用 LLM 生成节点…"})

            # 调用核心生成逻辑（含 LLM 调用 + 三层校验 + 自动修复）
            workflow = await ai_workflow_generator.generate_workflow_with_llm(
                description=form_data.description,
                model_id=form_data.model_id,
                user=user,
                request=request,
                template_hint=form_data.template_hint,
            )

            yield _sse_event({"type": "status", "content": "正在校验节点结构…"})

            warnings = workflow.get("warnings", []) or []

            yield _sse_event(
                {
                    "type": "result",
                    "workflow": workflow,
                    "warnings": warnings,
                }
            )
        except Exception as e:
            # 任何未捕获异常以 error 事件返回，避免 SSE 流挂死
            import logging

            logging.getLogger(__name__).error(
                "AI workflow generation failed: %s", e, exc_info=True
            )
            yield _sse_event(
                {"type": "error", "content": f"AI 生成失败：{str(e)}"}
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/")
async def create_workflow(
    request: Request,
    form_data: WorkflowForm,
    user=Depends(get_verified_user),
):
    """Create a new workflow."""
    workflow = await WorkflowService.create_workflow(form_data)
    if not workflow:
        raise HTTPException(status_code=400, detail="Failed to create workflow")

    # Parse JSON strings to objects for frontend
    if workflow:
        try:
            workflow["nodes"] = json.loads(workflow.get("nodes", "[]"))
            workflow["edges"] = json.loads(workflow.get("edges", "[]"))
        except (json.JSONDecodeError, TypeError):
            workflow["nodes"] = []
            workflow["edges"] = []

    return workflow


@router.get("/")
async def get_workflows(
    request: Request,
    user=Depends(get_verified_user),
):
    """Get all workflows for the current user."""
    workflows = await WorkflowService.get_all_workflows()

    # Parse JSON strings to objects for frontend
    for workflow in workflows:
        try:
            workflow["nodes"] = json.loads(workflow.get("nodes", "[]"))
            workflow["edges"] = json.loads(workflow.get("edges", "[]"))
        except (json.JSONDecodeError, TypeError):
            workflow["nodes"] = []
            workflow["edges"] = []

    return workflows


@router.get("/project/{project_id}")
async def get_workflows_by_project(
    project_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get all workflows for a project."""
    return await WorkflowService.get_workflows_by_project(project_id)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get workflow by ID."""
    workflow = await WorkflowService.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Parse JSON strings to objects for frontend
    try:
        workflow["nodes"] = json.loads(workflow.get("nodes", "[]"))
        workflow["edges"] = json.loads(workflow.get("edges", "[]"))
    except (json.JSONDecodeError, TypeError):
        workflow["nodes"] = []
        workflow["edges"] = []

    return workflow


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: Request,
    form_data: WorkflowForm,
    user=Depends(get_verified_user),
):
    """Update a workflow."""
    workflow = await WorkflowService.update_workflow(workflow_id, form_data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Parse JSON strings to objects for frontend
    try:
        workflow["nodes"] = json.loads(workflow.get("nodes", "[]"))
        workflow["edges"] = json.loads(workflow.get("edges", "[]"))
    except (json.JSONDecodeError, TypeError):
        workflow["nodes"] = []
        workflow["edges"] = []

    return workflow


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


@router.post("/{workflow_id}/nodes")
async def create_node(
    workflow_id: str,
    request: Request,
    form_data: WorkflowNodeForm,
    user=Depends(get_verified_user),
):
    """Create a new workflow node."""
    node = await WorkflowService.create_node(form_data)
    if not node:
        raise HTTPException(status_code=400, detail="Failed to create node")
    return node


@router.get("/{workflow_id}/nodes")
async def get_nodes_by_workflow(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get all nodes for a workflow."""
    return await WorkflowService.get_nodes_by_workflow(workflow_id)


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Delete a node."""
    success = await WorkflowService.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node deleted"}


@router.post("/{workflow_id}/edges")
async def create_edge(
    workflow_id: str,
    request: Request,
    form_data: WorkflowEdgeForm,
    user=Depends(get_verified_user),
):
    """Create a new workflow edge."""
    edge = await WorkflowService.create_edge(form_data)
    if not edge:
        raise HTTPException(status_code=400, detail="Failed to create edge")
    return edge


@router.get("/{workflow_id}/edges")
async def get_edges_by_workflow(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get all edges for a workflow."""
    return await WorkflowService.get_edges_by_workflow(workflow_id)


@router.delete("/edges/{edge_id}")
async def delete_edge(
    edge_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Delete an edge."""
    success = await WorkflowService.delete_edge(edge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Edge not found")
    return {"message": "Edge deleted"}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: Request,
    input_data: dict,
    user=Depends(get_verified_user),
):
    """Execute a workflow."""
    form_data = WorkflowExecutionForm(
        workflow_id=workflow_id,
        input_data=input_data.model_dump_json() if hasattr(input_data, "model_dump_json") else str(input_data),
    )
    execution = await WorkflowService.create_execution(form_data)
    if not execution:
        raise HTTPException(status_code=400, detail="Failed to create execution")
    return execution


@router.get("/{workflow_id}/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get execution by ID."""
    execution = await WorkflowService.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/{workflow_id}/executions")
async def get_executions_by_workflow(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Get all executions for a workflow."""
    return await WorkflowService.get_executions_by_workflow(workflow_id)


@router.post("/{workflow_id}/validate")
async def validate_workflow(
    workflow_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """Validate workflow structure."""
    return await WorkflowService.validate_workflow(workflow_id)
