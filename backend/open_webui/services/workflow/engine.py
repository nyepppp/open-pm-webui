"""
Workflow Execution Engine

A comprehensive workflow execution engine that supports:
- Topological execution of workflow nodes
- Multiple node types: start, end, agent_call, data_transform, condition, loop, parallel_merge, custom
- Data flow between nodes
- Conditional branching and loops
- Parallel execution
- Error handling and logging
- WebSocket streaming of execution progress
"""

import asyncio
import json
import logging
import time
import traceback
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, AsyncIterator

from open_webui.pm.models.workflow import (
    WorkflowExecutionForm,
    WorkflowExecutions,
    WorkflowNodes,
    Workflows,
)
from open_webui.services.workflow.websocket import workflow_websocket_manager

# Configure logging
logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    """Node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    """Result of executing a workflow node."""
    status: NodeStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    execution_time_ms: Optional[float] = None


@dataclass
class ExecutionContext:
    """Context for workflow execution."""
    execution_id: str
    workflow_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.PENDING
    error_message: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    chat_model_id: Optional[str] = None  # 从聊天界面继承的默认模型
    _request: Any = None
    _user: Any = None

    def set_variable(self, name: str, value: Any):
        """Set a variable in the execution context."""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the execution context."""
        return self.variables.get(name, default)

    def log(self, event_type: str, data: Dict[str, Any]):
        """Add a log entry."""
        self.logs.append({
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        })


class WorkflowEngineError(Exception):
    """Base exception for workflow engine errors."""
    pass


class NodeExecutionError(WorkflowEngineError):
    """Raised when a node execution fails."""
    def __init__(self, node_id: str, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.node_id = node_id
        self.details = details or {}


class WorkflowValidationError(WorkflowEngineError):
    """Raised when workflow validation fails."""
    pass


# 全局挂起表：{(execution_id, node_id): {"event": asyncio.Event, "response": Optional[dict], "prompt": str, "fields": list}}
# 用于 human_input 节点的运行时暂停/恢复机制。
# 注：不持久化；进程重启会丢失挂起状态（与现有 workflow run 语义一致）。
_HUMAN_INPUT_EVENTS: Dict[Tuple[str, str], Dict[str, Any]] = {}


class WorkflowExecutionEngine:
    """
    Comprehensive workflow execution engine.
    
    Supports:
    - Loading workflow definitions from database
    - Building execution graph from nodes and edges
    - Executing nodes in topological order
    - Conditional branching and loops
    - Parallel execution where possible
    - Streaming execution progress via WebSocket
    - Storing execution results in database
    """

    def __init__(self):
        self._running_executions: Dict[str, asyncio.Task] = {}
        self._execution_contexts: Dict[str, ExecutionContext] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        self.max_execution_time = 300  # 5 minutes
        self.max_nodes_per_execution = 100
        self.max_loop_iterations = 100

    async def execute(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_model_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Execute a workflow and return execution ID.

        Args:
            workflow_id: The workflow ID to execute
            input_data: Input data for the workflow
            execution_id: Optional execution ID (generated if not provided)
            user_id: Optional user ID for tracking (Issue #29: written to
                pm_workflow_executions.user_id for audit/ACL)
            chat_model_id: Optional chat model ID to inherit from chat UI
            project_id: Optional project context (Issue #29: written to
                pm_workflow_executions.project_id for audit/ACL). Router should
                derive this from the loaded workflow's project_id.

        Returns:
            Execution ID
        """
        execution_id = execution_id or str(uuid.uuid4())

        # Create execution record
        form_data = WorkflowExecutionForm(
            workflow_id=workflow_id,
            status="running",
            input_data=json.dumps(input_data),
            output_data="{}",
            node_states="[]",
            logs="[]",
        )
        execution = await WorkflowExecutions.insert_new_execution(
            form_data, user_id=user_id, project_id=project_id
        )
        if execution is None or not hasattr(execution, 'id') or execution.id is None:
            raise WorkflowEngineError("Failed to create execution record")
        execution_id = execution.id

        # 启动 WebSocket stream（让发起执行的用户进入 stream 房间接收事件）
        # 失败时降级到 HTTP 轮询，不阻塞执行
        try:
            await workflow_websocket_manager.start_stream(str(execution_id), user_id)
        except Exception as e:
            logger.error(f"Failed to start workflow stream: {e}", exc_info=True)

        # Start execution in background
        task = asyncio.create_task(
            self._run_execution(str(execution_id), workflow_id, input_data, user_id, chat_model_id)
        )
        self._running_executions[str(execution_id)] = task

        return str(execution_id)

    async def _run_execution(
        self,
        execution_id: str,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        chat_model_id: Optional[str] = None
    ):
        """
        Run the workflow execution.

        Args:
            execution_id: The execution ID
            workflow_id: The workflow ID
            input_data: Input data for the workflow
            user_id: Optional user ID
            chat_model_id: Optional chat model ID inherited from chat UI
        """
        context = ExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow_id,
            variables={**input_data},  # Initialize with input data
            status=ExecutionStatus.RUNNING,
            started_at=time.time(),
            chat_model_id=chat_model_id
        )
        self._execution_contexts[execution_id] = context
        
        try:
            # Get workflow from database
            workflow = await Workflows.get_workflow_by_id(workflow_id)
            if not workflow:
                raise WorkflowValidationError(f"Workflow {workflow_id} not found")
            
            # Parse nodes and edges
            nodes = json.loads(workflow.nodes) if workflow.nodes else []
            edges = json.loads(workflow.edges) if workflow.edges else []
            
            # Log execution start
            context.log("execution.started", {
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "node_count": len(nodes),
                "edge_count": len(edges)
            })

            # 推送执行开始事件
            try:
                await workflow_websocket_manager.emit_execution_progress(
                    execution_id, 0.0, len(nodes), 0
                )
            except Exception as e:
                logger.error(f"emit_execution_progress failed: {e}")
            
            # Build execution graph
            graph = self._build_execution_graph(nodes, edges)

            # Validate workflow
            validation_errors = self._validate_workflow(graph, nodes)
            if validation_errors:
                # D19: 自动修复 disconnected nodes（与 ai_generator.py 的 _connect_disconnected_nodes 策略一致）
                # 适用场景：用户执行的是旧工作流（D9 修复前生成）或手动编辑的工作流，
                # 这类工作流未经过 AI 生成器的 _validate_and_repair 流程，可能含孤立节点。
                if any("is disconnected" in err for err in validation_errors):
                    logger.warning(f"Workflow {workflow_id} has disconnected nodes, attempting auto-repair")
                    nodes, edges = self._auto_repair_disconnected_nodes(nodes, edges)
                    graph = self._build_execution_graph(nodes, edges)
                    validation_errors = self._validate_workflow(graph, nodes)
            if validation_errors:
                raise WorkflowValidationError(
                    f"Workflow validation failed: {'; '.join(validation_errors)}"
                )
            
            # Execute workflow
            await self._execute_workflow(graph, nodes, edges, context)
            
            # Mark as completed
            context.status = ExecutionStatus.COMPLETED
            context.completed_at = time.time()
            
            # Update execution record
            await WorkflowExecutions.update_execution_status(
                execution_id,
                "completed",
                output_data=json.dumps(context.variables),
            )
            
            # Log completion
            execution_time_ms = 0.0
            if context.completed_at and context.started_at:
                execution_time_ms = (context.completed_at - context.started_at) * 1000
            context.log("execution.completed", {
                "execution_id": execution_id,
                "execution_time_ms": execution_time_ms
            })

            # 推送执行完成事件
            try:
                await workflow_websocket_manager.emit_execution_complete(
                    execution_id, "completed",
                    output_data=context.variables
                )
            except Exception as e:
                logger.error(f"emit_execution_complete failed: {e}")
            
        except WorkflowValidationError as e:
            logger.error(f"Workflow validation error: {e}")
            context.status = ExecutionStatus.FAILED
            context.error_message = str(e)
            context.completed_at = time.time()

            await WorkflowExecutions.update_execution_status(
                execution_id,
                "failed",
                error_message=str(e)
            )

            # 推送执行失败事件
            try:
                await workflow_websocket_manager.emit_execution_complete(
                    execution_id, "failed",
                    error_message=str(e)
                )
            except Exception as emit_err:
                logger.error(f"emit_execution_complete (failed) error: {emit_err}")

        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            context.status = ExecutionStatus.FAILED
            context.error_message = str(e)
            context.completed_at = time.time()

            await WorkflowExecutions.update_execution_status(
                execution_id,
                "failed",
                error_message=str(e)
            )

            # 推送执行失败事件
            try:
                await workflow_websocket_manager.emit_execution_complete(
                    execution_id, "failed",
                    error_message=str(e)
                )
            except Exception as emit_err:
                logger.error(f"emit_execution_complete (failed) error: {emit_err}")

        finally:
            # Clean up
            if execution_id in self._running_executions:
                del self._running_executions[execution_id]

            # 关闭 WebSocket stream（容错：stream 可能已不存在）
            try:
                await workflow_websocket_manager.end_stream(execution_id)
            except Exception as e:
                logger.error(f"end_stream failed: {e}")

            # Notify listeners
            await self._notify_listeners(execution_id, {
                "event": "execution.completed" if context.status == ExecutionStatus.COMPLETED else "execution.failed",
                "execution_id": execution_id,
                "status": context.status.value,
                "error": context.error_message
            })

    def _build_execution_graph(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Dict]:
        """
        Build execution graph from nodes and edges.
        
        Returns:
            Dict mapping node_id to {incoming_edges, outgoing_edges, node_data}
        """
        graph = {}
        
        # Initialize nodes
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                graph[node_id] = {
                    "node": node,
                    "incoming": [],
                    "outgoing": [],
                    "dependencies": set()
                }
        
        # Add edges
        for edge in edges:
            # D14: 兼容多种字段名（snake_case / camelCase / 简写）
            source = edge.get("source_node_id") or edge.get("source") or edge.get("sourceNodeId")
            target = edge.get("target_node_id") or edge.get("target") or edge.get("targetNodeId")

            if source in graph and target in graph:
                graph[source]["outgoing"].append({
                    "target": target,
                    "edge": edge
                })
                graph[target]["incoming"].append({
                    "source": source,
                    "edge": edge
                })
                graph[target]["dependencies"].add(source)
        
        return graph

    def _validate_workflow(self, graph: Dict, nodes: List[Dict]) -> List[str]:
        """
        Validate workflow structure.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for start node
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if not start_nodes:
            errors.append("Workflow must have at least one start node")
        
        # Check for end node
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if not end_nodes:
            errors.append("Workflow must have at least one end node")
        
        # Check for disconnected nodes
        for node_id, node_data in graph.items():
            node = node_data["node"]
            node_type = node.get("type", "")
            
            # Start nodes don't need incoming edges
            if node_type == "start":
                continue
            
            # End nodes don't need outgoing edges
            if node_type == "end":
                continue
            
            # Other nodes should have at least one connection
            if not node_data["incoming"] and not node_data["outgoing"]:
                errors.append(f"Node {node_id} is disconnected")

        return errors

    def _auto_repair_disconnected_nodes(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """D19: 执行前自动修复 disconnected nodes。

        与 ai_generator.py 的 _connect_disconnected_nodes 策略一致：
        - 完全孤立（既无 incoming 也无 outgoing）的非 start/end 节点 → 补 start→node 和 node→end 两条边
        - 边字段使用 sourceNodeId / targetNodeId（与 _build_execution_graph L387-388 兼容，已支持三种字段命名）

        Returns:
            (nodes, edges) — nodes 原样返回，edges 追加修复边
        """
        if not nodes:
            return nodes, edges

        # 找 start 和 end 节点
        start_node = next((n for n in nodes if n.get("type") == "start"), None)
        end_node = next((n for n in nodes if n.get("type") == "end"), None)

        # 统计每个节点的 incoming / outgoing 边数
        incoming: Dict[str, int] = {n.get("id"): 0 for n in nodes if n.get("id")}
        outgoing: Dict[str, int] = {n.get("id"): 0 for n in nodes if n.get("id")}
        for e in edges:
            src = e.get("source_node_id") or e.get("source") or e.get("sourceNodeId")
            tgt = e.get("target_node_id") or e.get("target") or e.get("targetNodeId")
            if src in outgoing:
                outgoing[src] += 1
            if tgt in incoming:
                incoming[tgt] += 1

        new_edges = list(edges)
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            node_type = node.get("type", "")
            # start / end 节点豁免
            if node_type in ("start", "end"):
                continue
            # 已有 incoming 或 outgoing → 不处理
            if incoming.get(node_id, 0) > 0 or outgoing.get(node_id, 0) > 0:
                continue

            # 完全孤立：补 start→node 和 node→end 两条边
            if start_node:
                new_edges.append({
                    "id": f"edge-auto-{node_id}-in-{uuid.uuid4().hex[:8]}",
                    "sourceNodeId": start_node["id"],
                    "targetNodeId": node_id,
                    "label": "",
                })
                logger.warning(f"Auto-repair: connect orphan node {node_id} ← start")
            if end_node:
                new_edges.append({
                    "id": f"edge-auto-{node_id}-out-{uuid.uuid4().hex[:8]}",
                    "sourceNodeId": node_id,
                    "targetNodeId": end_node["id"],
                    "label": "",
                })
                logger.warning(f"Auto-repair: connect orphan node {node_id} → end")

        return nodes, new_edges

    async def _execute_workflow(
        self,
        graph: Dict[str, Dict],
        nodes: List[Dict],
        edges: List[Dict],
        context: ExecutionContext
    ):
        """
        Execute workflow nodes in topological order.
        
        Args:
            graph: Execution graph
            nodes: List of node definitions
            edges: List of edge definitions
            context: Execution context
        """
        # Track executed nodes
        executed_nodes: Set[str] = set()
        node_outputs: Dict[str, Any] = {}
        
        # Find start node
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if not start_nodes:
            raise WorkflowValidationError("No start node found")
        
        # Execute nodes using BFS
        queue = [start_nodes[0]["id"]]
        
        while queue:
            if len(executed_nodes) >= self.max_nodes_per_execution:
                raise WorkflowEngineError(
                    f"Exceeded maximum nodes per execution ({self.max_nodes_per_execution})"
                )
            
            node_id = queue.pop(0)
            
            if node_id in executed_nodes:
                continue
            
            # Check if all dependencies are satisfied
            node_data = graph.get(node_id)
            if not node_data:
                continue
            
            dependencies = node_data["dependencies"]
            if not dependencies.issubset(executed_nodes):
                # Dependencies not met, skip for now
                continue
            
            # Execute node
            node = node_data["node"]
            try:
                result = await self._execute_node(node, context, node_outputs)
                context.node_results[node_id] = result
                node_outputs[node_id] = result.output if result else {}
                executed_nodes.add(node_id)

                # Log node completion
                context.log("node.completed", {
                    "node_id": node_id,
                    "node_type": node.get("type"),
                    "status": result.status.value if result else "unknown"
                })

                # 推送执行进度事件
                completed_count = len(context.node_results)
                total_count = len(nodes)
                try:
                    await workflow_websocket_manager.emit_execution_progress(
                        context.execution_id,
                        (completed_count / total_count * 100) if total_count > 0 else 100.0,
                        total_count, completed_count
                    )
                except Exception as e:
                    logger.error(f"emit_execution_progress failed: {e}")
                
                # Notify listeners
                await self._notify_listeners(context.execution_id, {
                    "event": "node.completed",
                    "execution_id": context.execution_id,
                    "node_id": node_id,
                    "node_type": node.get("type"),
                    "status": result.status.value if result else "unknown"
                })
                
                # Add successor nodes to queue
                # For condition nodes, only follow edges whose label matches the
                # evaluated condition result (true/false branch routing).
                node_type_for_routing = node.get("type", "")
                condition_result_value = None
                if node_type_for_routing == "condition" and result and result.output:
                    if isinstance(result.output, dict):
                        condition_result_value = bool(result.output.get("result", False))

                # C3b: 上游节点 failed 时，下游节点全部标记为 skipped，不入队执行
                # 之前 BFS 不检查 result.status，failed 节点的下游继续执行，拿不到上游数据
                # 也装作 completed，造成「全部 100% 完成」的假象。
                if result and result.status == NodeStatus.FAILED:
                    for outgoing in node_data["outgoing"]:
                        next_node_id = outgoing["target"]
                        if next_node_id not in executed_nodes and next_node_id not in context.node_results:
                            context.node_results[next_node_id] = NodeResult(
                                status=NodeStatus.SKIPPED,
                                error=f"upstream node {node_id} failed",
                            )
                            executed_nodes.add(next_node_id)
                            context.log("node.skipped", {
                                "node_id": next_node_id,
                                "reason": f"upstream {node_id} failed",
                            })
                    continue  # 不入队任何下游节点

                for outgoing in node_data["outgoing"]:
                    next_node_id = outgoing["target"]
                    if next_node_id in executed_nodes:
                        continue

                    edge = outgoing.get("edge", {}) or {}
                    edge_label = (edge.get("label") or "").strip().lower()

                    # C5: 应用 edge.data_mapping_rules —— 把上游 output 字段映射到下游 variables
                    # 之前 BFS 只读 edge.label 做条件路由，完全忽略 data_mapping_rules，
                    # 导致下游节点 input 拿不到上游数据，{{var}} 解析为字面量。
                    mapping_rules = edge.get("data_mapping_rules") or {}
                    if mapping_rules and isinstance(mapping_rules, dict) and result and result.output:
                        for target_key, source_expr in mapping_rules.items():
                            if isinstance(source_expr, str):
                                resolved = self._resolve_variables(source_expr, context)
                                context.variables[target_key] = resolved
                            else:
                                # 非字符串直接赋值（数字/bool/dict 等）
                                context.variables[target_key] = source_expr

                    if node_type_for_routing == "condition" and condition_result_value is not None:
                        # Only filter when an explicit true/false label is present.
                        # Unlabeled edges are followed unconditionally (backward compat).
                        if edge_label in ("true", "yes"):
                            if not condition_result_value:
                                continue
                        elif edge_label in ("false", "no"):
                            if condition_result_value:
                                continue

                    queue.append(next_node_id)
                
            except Exception as e:
                logger.error(f"Node {node_id} execution failed: {e}", exc_info=True)
                context.node_results[node_id] = NodeResult(
                    status=NodeStatus.FAILED,
                    error=str(e)
                )
                raise NodeExecutionError(node_id, str(e))

    async def _execute_node(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        node_outputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute a single node.
        
        Args:
            node: Node definition
            context: Execution context
            node_outputs: Outputs from previous nodes
            
        Returns:
            Node execution result
        """
        node_id = node.get("id")
        node_type = node.get("type", "custom")
        node_config = json.loads(node.get("config", "{}")) if isinstance(node.get("config"), str) else node.get("config", {})

        # 暴露 node_id 给 human_input executor，使其能定位挂起表
        context.set_variable("_current_node_id", node_id)

        started_at = time.time()

        try:
            # Log node start
            context.log("node.started", {
                "node_id": node_id,
                "node_type": node_type
            })

            # 推送节点开始事件
            try:
                await workflow_websocket_manager.emit_node_start(
                    context.execution_id, node_id, node_type,
                    node_name=node.get("name")
                )
            except Exception as e:
                logger.error(f"emit_node_start failed: {e}")
            
            # Execute based on node type
            # Node type aliases: map frontend types to backend executors
            NODE_TYPE_ALIASES = {
                'llm': 'agent_call',
                'variable_set': 'data_transform',
                'agent': 'agent_call',
            }
            resolved_type = NODE_TYPE_ALIASES.get(node_type, node_type)

            if resolved_type == "start" or node_type == "start":
                result = await self._execute_start_node(node_config, context)
            elif resolved_type == "end" or node_type == "end":
                result = await self._execute_end_node(node_config, context)
            elif resolved_type == "agent_call" or node_type in ("llm", "agent"):
                result = await self._execute_agent_call_node(node_config, context)
            elif resolved_type == "data_transform" or node_type == "variable_set":
                result = await self._execute_data_transform_node(node_config, context)
            elif node_type == "condition":
                result = await self._execute_condition_node(node_config, context)
            elif node_type == "loop":
                result = await self._execute_loop_node(node_config, context)
            elif node_type == "parallel_merge":
                result = await self._execute_parallel_merge_node(node_config, context)
            elif resolved_type == "custom":
                result = await self._execute_custom_node(node_config, context)
            elif node_type == "http_request":
                result = await self._execute_http_request_node(node_config, context)
            elif node_type == "code":
                result = await self._execute_code_node(node_config, context)
            elif node_type == "knowledge_retrieval":
                result = await self._execute_knowledge_node(node_config, context)
            elif node_type == "template":
                result = await self._execute_template_node(node_config, context)
            elif node_type == "parameter_extractor":
                result = await self._execute_parameter_extractor_node(node_config, context)
            elif node_type == "answer":
                result = await self._execute_answer_node(node_config, context)
            elif node_type == "pm_module":
                result = await self._execute_pm_module_node(node_config, context)
            elif node_type == "tool_call":
                result = await self._execute_tool_call_node(node_config, context)
            elif node_type == "function_call":
                result = await self._execute_function_call_node(node_config, context)
            elif node_type == "skill_call":
                result = await self._execute_skill_call_node(node_config, context)
            elif node_type == "mcp_call":
                result = await self._execute_mcp_call_node(node_config, context)
            elif node_type == "human_input":
                result = await self._execute_human_input_node(node_config, context)
            else:
                result = {
                    "status": "completed",
                    "output": {"message": f"Unknown node type: {node_type}"}
                }
            
            completed_at = time.time()

            # J1/D76: 尊重子节点返回的 status，不再硬编码 COMPLETED
            # v7 的 C3a 修复让 _execute_pm_module_node 返回 status="failed"，
            # 但这里硬编码 COMPLETED 把它覆盖了 → 所有节点都报 completed，
            # BFS 继续向下游传播，用户看到 100% completed 但数据没通。
            raw_status = result.get("status", "completed") if isinstance(result, dict) else "completed"
            if raw_status == "failed":
                node_status = NodeStatus.FAILED
            elif raw_status == "skipped":
                node_status = NodeStatus.SKIPPED
            else:
                node_status = NodeStatus.COMPLETED
            # J1: 提取 error 字段（C3a 把 error 放在 output.error 里）
            output = result.get("output", {}) if isinstance(result, dict) else {}
            error_msg = result.get("error") if isinstance(result, dict) else None
            if not error_msg and isinstance(output, dict):
                error_msg = output.get("error")
            if node_status == NodeStatus.FAILED and error_msg:
                logger.warning(
                    f"[Bug5-Diag] J1 node {node_id} ({node_type}) reported FAILED: {error_msg}"
                )

            # 推送节点完成事件（失败节点也推送，让前端看到 failed 状态）
            try:
                await workflow_websocket_manager.emit_node_complete(
                    context.execution_id, node_id, node_type,
                    output=output,
                    execution_time_ms=(completed_at - started_at) * 1000
                )
            except Exception as e:
                logger.error(f"emit_node_complete failed: {e}")

            return NodeResult(
                status=node_status,
                output=output,
                error=error_msg,
                started_at=started_at,
                completed_at=completed_at,
                execution_time_ms=(completed_at - started_at) * 1000
            )

        except Exception as e:
            logger.error(f"Node {node_id} execution failed: {e}", exc_info=True)

            # 推送节点失败事件
            try:
                await workflow_websocket_manager.emit_node_error(
                    context.execution_id, node_id, node_type, str(e)
                )
            except Exception as emit_err:
                logger.error(f"emit_node_error failed: {emit_err}")

            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=time.time()
            )

    async def _execute_start_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """Execute a start node."""
        return {
            "status": "completed",
            "output": context.variables
        }

    async def _execute_end_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """Execute an end node."""
        return {
            "status": "completed",
            "output": context.variables
        }

    async def _execute_agent_call_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """Execute an agent call node with OpenWebUI LLM integration.

        #34: 响应脱敏 (D4 默认开, 不可关) — 在 return 前对 output 做 sanitize.
        """
        from open_webui.services.workflow.response_sanitizer import sanitize as sanitize_response
        try:
            agent_id = config.get("agent_id")
            prompt = config.get("prompt", "")
            # 优先节点 config.model；为空或 "default" 时回退到聊天模型
            model = config.get("model") or context.chat_model_id or "default"
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 2048)
            
            resolved_prompt = self._resolve_variables(prompt, context)
            
            if hasattr(context, '_request') and hasattr(context, '_user'):
                try:
                    from open_webui.utils.chat import generate_chat_completion
                    
                    request = context._request
                    user = context._user
                    
                    form_data = {
                        "model": model if model != "default" else "gpt-4",
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": resolved_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": False
                    }
                    
                    response = await generate_chat_completion(
                        request=request,
                        form_data=form_data,
                        user=user
                    )
                    
                    response_text = ""
                    if isinstance(response, dict):
                        choices = response.get("choices", [])
                        if choices:
                            response_text = choices[0].get("message", {}).get("content", "")
                    
                    result = {
                        "status": "completed",
                        "output": {
                            "agent_id": agent_id,
                            "prompt": resolved_prompt,
                            "model": model,
                            "response": response_text,
                            "metadata": {
                                "temperature": temperature,
                                "max_tokens": max_tokens
                            }
                        }
                    }
                    # #34 响应脱敏: 阻断 LLM 输出中的 API key / 私钥 / PII 泄露
                    result["output"] = sanitize_response(result["output"])
                    return result
                except Exception as e:
                    logger.warning(f"LLM integration failed, falling back to simulation: {e}")
            
            # D66/Bug5 漏洞 2 修复：LLM 调用失败或无 request/user 上下文时，返回 failed 而非占位符
            # 之前 fallback 返回 `f"Agent response for: {resolved_prompt[:50]}..."` + status: completed，
            # 让 BFS 误以为节点成功，下游节点拿到占位符文本继续装作完成 —— 用户看到 100% completed 但数据没通
            await asyncio.sleep(0.1)
            
            result = {
                "status": "failed",
                "output": {
                    "error": f"agent_call LLM 调用失败或无 request/user 上下文（model={model}, prompt={resolved_prompt[:50]}...）",
                    "agent_id": agent_id,
                    "prompt": resolved_prompt,
                    "model": model
                }
            }
            # #34 失败路径同样脱敏 (error 字段可能含敏感信息)
            result["output"] = sanitize_response(result["output"])
            return result
            
        except Exception as e:
            logger.error(f"Agent call failed: {e}", exc_info=True)
            raise

    async def _execute_data_transform_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """
        Execute a data transform node.
        
        Supports JSON mapping, filtering, and basic transformations.
        """
        try:
            transform_type = config.get("transform_type", "json_map")
            input_data = config.get("input_data", {})
            mapping_rules = config.get("mapping_rules", {})
            
            # Resolve variables in input data
            if isinstance(input_data, str):
                input_data = self._resolve_variables(input_data, context)
                try:
                    input_data = json.loads(input_data)
                except json.JSONDecodeError:
                    pass
            
            result = {}
            
            if transform_type == "json_map":
                # JSON mapping transformation
                for key, value in mapping_rules.items():
                    if isinstance(value, str) and value.startswith("$"):
                        # Extract from input using path
                        path = value[1:].split(".")
                        current = input_data
                        for p in path:
                            if isinstance(current, dict):
                                current = current.get(p)
                            else:
                                current = None
                                break
                        result[key] = current
                    else:
                        result[key] = value
                        
            elif transform_type == "filter":
                # Filter transformation
                if isinstance(input_data, list):
                    condition = config.get("condition", "")
                    result = [item for item in input_data if self._evaluate_filter(item, condition, context)]
                else:
                    result = input_data
                    
            elif transform_type == "merge":
                # Merge multiple inputs
                sources = config.get("sources", [])
                result = {}
                for source in sources:
                    source_data = context.get_variable(source, {})
                    if isinstance(source_data, dict):
                        result.update(source_data)
                        
            elif transform_type == "script":
                # Execute custom script via subprocess sandbox
                script = config.get("script", "")
                if script:
                    sandbox_result = await self._execute_sandbox_script(
                        script, input_data if isinstance(input_data, dict) else {"input": input_data}, timeout=30
                    )
                    result = {"script_output": sandbox_result}
                else:
                    result = {"error": "Script transform requires 'script' field"}
                
            else:
                result = input_data
            
            # Store result in context
            output_var = config.get("output_variable")
            if output_var:
                context.set_variable(output_var, result)
            
            return {
                "status": "completed",
                "output": result
            }
            
        except Exception as e:
            logger.error(f"Data transform failed: {e}", exc_info=True)
            raise

    async def _execute_condition_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """
        Execute a condition node.
        
        Evaluates expressions and routes to appropriate branch.
        """
        try:
            condition = config.get("condition", "")
            true_branch = config.get("true_branch", {})
            false_branch = config.get("false_branch", {})
            
            # Evaluate condition
            condition_result = self._evaluate_condition(condition, context)
            
            return {
                "status": "completed",
                "output": {
                    "condition": condition,
                    "result": condition_result,
                    "true_branch": true_branch if condition_result else None,
                    "false_branch": false_branch if not condition_result else None
                }
            }
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}", exc_info=True)
            raise

    async def _execute_loop_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """
        Execute a loop node.
        
        Iterates until condition is met or max iterations reached.
        """
        try:
            loop_type = config.get("loop_type", "while")
            condition = config.get("condition", "")
            max_iterations = config.get("max_iterations", self.max_loop_iterations)
            body = config.get("body", {})
            
            iteration_count = 0
            results = []
            
            if loop_type == "while":
                while iteration_count < max_iterations:
                    # Evaluate condition
                    if not self._evaluate_condition(condition, context):
                        break
                    
                    # Execute loop body
                    iteration_result = await self._execute_loop_body(body, context, iteration_count)
                    results.append(iteration_result)
                    
                    iteration_count += 1
                    
            elif loop_type == "for_each":
                items = config.get("items", [])
                for i, item in enumerate(items):
                    if iteration_count >= max_iterations:
                        break
                    
                    context.set_variable("current_item", item)
                    context.set_variable("current_index", i)
                    
                    iteration_result = await self._execute_loop_body(body, context, i)
                    results.append(iteration_result)
                    
                    iteration_count += 1
            
            return {
                "status": "completed",
                "output": {
                    "iteration_count": iteration_count,
                    "results": results,
                    "completed": iteration_count < max_iterations
                }
            }
            
        except Exception as e:
            logger.error(f"Loop execution failed: {e}", exc_info=True)
            raise

    async def _execute_parallel_merge_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """
        Execute a parallel merge node.
        
        Executes multiple branches in parallel and merges results.
        """
        try:
            branches = config.get("branches", [])
            merge_strategy = config.get("merge_strategy", "merge")
            
            # Execute branches in parallel
            branch_tasks = []
            for branch in branches:
                task = self._execute_branch(branch, context)
                branch_tasks.append(task)
            
            # Wait for all branches to complete
            branch_results = await asyncio.gather(*branch_tasks, return_exceptions=True)
            
            # Merge results based on strategy
            merged_result = self._merge_results(branch_results, merge_strategy)
            
            return {
                "status": "completed",
                "output": merged_result
            }
            
        except Exception as e:
            logger.error(f"Parallel merge failed: {e}", exc_info=True)
            raise

    async def _execute_custom_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """
        Execute a custom node.
        
        Supports tool registry lookup with subprocess script fallback.
        """
        try:
            tool_name = config.get("tool_name", "")
            parameters = config.get("parameters", {})
            script = config.get("script", "")
            language = config.get("language", "python")
            
            # 解析参数中的变量引用 {{var}}
            resolved_params = {}
            for key, val in parameters.items():
                if isinstance(val, str) and val.startswith("{{") and val.endswith("}}"):
                    var_name = val[2:-2].strip()
                    resolved_params[key] = context.get_variable(var_name)
                else:
                    resolved_params[key] = val
            
            # 1. 尝试工具注册表（OpenWebUI tools）
            try:
                from open_webui.utils.tools import get_tools
                tools = get_tools()
                for tool in tools:
                    if tool.get("name") == tool_name:
                        handler = tool.get("handler")
                        if callable(handler):
                            if asyncio.iscoroutinefunction(handler):
                                result = await handler(**resolved_params)
                            else:
                                result = handler(**resolved_params)
                            return {
                                "status": "completed",
                                "output": self._serialize_model_output(result)
                            }
            except (ImportError, Exception) as e:
                logger.debug(f"Tool registry lookup failed for '{tool_name}': {e}")
            
            # 2. 回退到 script 执行
            if script and language == "python":
                result = await self._execute_sandbox_script(script, resolved_params, timeout=30)
                return {
                    "status": "completed",
                    "output": {"result": result, "tool_name": tool_name}
                }
            
            # 3. 无 tool_name 也无 script
            return {
                "status": "completed",
                "output": {
                    "tool_name": tool_name,
                    "result": f"Custom node '{tool_name}' has no handler or script"
                }
            }
            
        except Exception as e:
            logger.error(f"Custom node execution failed: {e}", exc_info=True)
            raise

    async def _execute_loop_body(self, body: Dict, context: ExecutionContext, iteration: int) -> Dict:
        """Execute a loop body for a single iteration."""
        # 设置迭代变量
        context.set_variable("iteration", iteration)
        if isinstance(body, dict):
            # 如果 body 包含 inline nodes 配置，执行它们
            inline_nodes = body.get("nodes", [])
            if inline_nodes:
                iteration_output = {}
                for node_cfg in inline_nodes:
                    try:
                        result = await self._execute_node(node_cfg, context)
                        if result and result.output:
                            iteration_output.update(result.output)
                    except Exception as e:
                        logger.warning(f"Loop body node failed at iteration {iteration}: {e}")
                return {
                    "iteration": iteration,
                    "status": "completed",
                    "output": iteration_output
                }
            
            # 如果 body 包含变量赋值
            assignments = body.get("assignments", {})
            if assignments:
                for key, val in assignments.items():
                    if isinstance(val, str):
                        val = self._resolve_variables(val, context)
                    context.set_variable(key, val)
                return {
                    "iteration": iteration,
                    "status": "completed",
                    "output": assignments
                }
        
        # 默认：返回迭代信息
        return {
            "iteration": iteration,
            "status": "completed",
            "output": body if isinstance(body, dict) else {"body": str(body)}
        }

    async def _execute_branch(self, branch: Dict, context: ExecutionContext) -> Dict:
        """Execute a single branch in parallel execution."""
        try:
            # 如果 branch 包含 inline nodes
            if isinstance(branch, dict):
                inline_nodes = branch.get("nodes", [])
                if inline_nodes:
                    branch_output = {}
                    for node_cfg in inline_nodes:
                        try:
                            result = await self._execute_node(node_cfg, context)
                            if result and result.output:
                                branch_output.update(result.output)
                        except Exception as e:
                            logger.warning(f"Branch node failed: {e}")
                    return {
                        "status": "completed",
                        "output": branch_output
                    }
                
                # 如果 branch 包含变量赋值
                assignments = branch.get("assignments", {})
                if assignments:
                    for key, val in assignments.items():
                        if isinstance(val, str):
                            val = self._resolve_variables(val, context)
                        context.set_variable(key, val)
                    return {
                        "status": "completed",
                        "output": assignments
                    }
            
            return {
                "status": "completed",
                "output": branch if isinstance(branch, dict) else {"branch": str(branch)}
            }
        except Exception as e:
            logger.error(f"Branch execution failed: {e}", exc_info=True)
            raise

    # ==================== 新增辅助方法 ====================

    def _serialize_model_output(self, output: Any) -> Dict[str, Any]:
        """序列化 LLM 输出为可 JSON 化的 dict。"""
        if isinstance(output, dict):
            return output
        if isinstance(output, list):
            return {"results": output}
        if hasattr(output, 'model_dump'):
            return output.model_dump()
        if hasattr(output, 'dict'):
            return output.dict()
        return {"result": str(output)}

    async def _call_llm(self, model: str, system_prompt: str, prompt: str,
                        temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """调用 LLM（通过 openai 兼容接口直连 OpenWebUI）。"""
        try:
            import openai
            client = openai.AsyncOpenAI(
                base_url="http://localhost:8080/v1",
                api_key="dummy"
            )
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = await client.chat.completions.create(
                model=model or "gpt-4o-mini",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"LLM call failed: {e}, returning placeholder")
            return f"[LLM call failed: {e}]"

    def _parse_json_safe(self, text: str) -> Any:
        """安全解析 JSON，提取 ```json 代码块或直接解析。"""
        if not text:
            return None
        text = text.strip()
        # 尝试提取 ```json ... ``` 代码块
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    async def _execute_sandbox_script(self, code: str, inputs: Dict[str, Any],
                                      timeout: int = 30) -> Dict[str, Any]:
        """在 subprocess 沙箱中执行 Python 代码。stdin 传 inputs，stdout 读 result JSON。"""
        full_script = f"""
import json, sys
inputs = json.loads(sys.stdin.read())
{code}
print(json.dumps({{k: v for k, v in locals().items() if not k.startswith('_') and k not in ('json', 'sys', 'inputs')}}))
"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "python", "-c", full_script,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=json.dumps(inputs).encode()),
                timeout=timeout
            )
            if proc.returncode != 0:
                raise RuntimeError(f"Script failed: {stderr.decode()}")
            return json.loads(stdout.decode())
        except asyncio.TimeoutError:
            raise RuntimeError(f"Script timed out after {timeout}s")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Script output not valid JSON: {e}")

    # ==================== 新增 7 个 executor 方法 ====================

    async def _execute_http_request_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行 HTTP 请求节点 (含 SSRF 防护, #32).

        防护策略 (D3):
        - URL/IP/DNS 三层校验 (network_guard.validate_url)
        - 禁用 redirect (allow_redirects=False) 防止 302 跳内网
        - 默认 10s 超时, 1MiB 响应大小限制
        - 响应头脱敏 (sanitize_response_headers)
        """
        from open_webui.services.workflow.network_guard import (
            validate_url,
            SSRFError,
            sanitize_response_headers,
            DEFAULT_TIMEOUT_SECONDS,
            DEFAULT_MAX_RESPONSE_BYTES,
        )
        try:
            import aiohttp
            method = config.get("method", "GET").upper()
            url = self._resolve_variables(str(config.get("url", "")), context)

            # SSRF 校验: 协议白名单 + DNS 解析 + IP 黑名单
            try:
                host, resolved_ip = validate_url(url)
                logger.info("HTTP node -> %s (resolved %s)", host, resolved_ip)
            except SSRFError as e:
                logger.warning("SSRF blocked: %s (url=%s)", e, url)
                return {
                    "status": "failed",
                    "error": f"URL not allowed: {e}",
                    "output": None,
                }

            headers = config.get("headers", {})
            body = config.get("body", "")
            if body and isinstance(body, str):
                body = self._resolve_variables(body, context)

            timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 禁用 redirect — 防止 302 跳转到内网
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    data=body if body else None,
                    allow_redirects=False,
                ) as response:
                    # 限制响应体大小, 防止大响应耗尽内存
                    body_bytes = await response.content.read(DEFAULT_MAX_RESPONSE_BYTES)
                    response_text = body_bytes.decode("utf-8", errors="replace")
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError:
                        response_data = response_text
                    return {
                        "status": "completed",
                        "output": {
                            "status_code": response.status,
                            "headers": sanitize_response_headers(dict(response.headers)),
                            "body": response_data,
                        }
                    }
        except Exception as e:
            logger.error(f"HTTP request failed: {e}", exc_info=True)
            raise

    async def _execute_code_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行代码节点（subprocess 沙箱）。"""
        try:
            code = config.get("code", "")
            input_variables = config.get("input_variables", {})
            # 解析输入变量引用
            resolved_inputs = {}
            for key, val in input_variables.items():
                if isinstance(val, str) and val.startswith("{{") and val.endswith("}}"):
                    var_name = val[2:-2].strip()
                    resolved_inputs[key] = context.get_variable(var_name)
                else:
                    resolved_inputs[key] = val
            result = await self._execute_sandbox_script(code, resolved_inputs, timeout=30)
            return {
                "status": "completed",
                "output": {"result": result}
            }
        except Exception as e:
            logger.error(f"Code execution failed: {e}", exc_info=True)
            raise

    async def _execute_knowledge_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行知识库检索节点。"""
        try:
            import aiohttp
            query = self._resolve_variables(str(config.get("query", "")), context)
            knowledge_base_id = config.get("knowledge_base_id", "")
            top_k = config.get("top_k", 5)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8080/api/v1/retrieval/process/web/search",
                    json={"collection_name": knowledge_base_id, "query": query, "k": top_k},
                ) as response:
                    data = await response.json()
                    return {
                        "status": "completed",
                        "output": {"results": data.get("results", []), "query": query}
                    }
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}", exc_info=True)
            raise

    async def _execute_template_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行模板渲染节点。"""
        try:
            template_str = config.get("template", "")
            rendered = self._resolve_variables(template_str, context)
            output_variable = config.get("output_variable", "result")
            if output_variable:
                context.set_variable(output_variable, rendered)
            return {
                "status": "completed",
                "output": {output_variable: rendered}
            }
        except Exception as e:
            logger.error(f"Template rendering failed: {e}", exc_info=True)
            raise

    async def _execute_parameter_extractor_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行参数提取节点（LLM + JSON mode）。"""
        try:
            # 优先节点 config.model；为空时回退到聊天模型
            model = config.get("model") or context.chat_model_id or ""
            input_text = self._resolve_variables(str(config.get("input_text", "")), context)
            parameters = config.get("parameters", [])
            output_variable = config.get("output_variable", "extracted")
            
            # 构建 LLM prompt
            param_schema = {p.get("name", ""): p.get("type", "string") for p in parameters}
            prompt = f"""Extract parameters from the following text. Return ONLY a JSON object with these fields: {json.dumps(param_schema)}

Text:
{input_text}"""
            result_text = await self._call_llm(model, "You are a parameter extraction assistant.", prompt)
            # D66/Bug5 漏洞 1 修复：LLM 失败或返回非 JSON 时报 failed，不再静默用 {} 完成
            # 之前 `self._parse_json_safe(result_text) or {}` 把 None/{} 都吞掉，节点报 completed
            # 导致下游节点拿到空 dict 也装作完成 —— 用户看到 100% completed 但数据没通
            extracted = self._parse_json_safe(result_text)
            if extracted is None:
                return {
                    "status": "failed",
                    "output": {"error": f"parameter_extractor LLM 返回非 JSON: {result_text[:200]}"}
                }
            if output_variable:
                context.set_variable(output_variable, extracted)
            return {
                "status": "completed",
                "output": {output_variable: extracted}
            }
        except Exception as e:
            logger.error(f"Parameter extraction failed: {e}", exc_info=True)
            raise

    async def _execute_answer_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行答案节点（模板渲染 + 变量替换）。"""
        try:
            answer_template = config.get("answer", "")
            rendered = self._resolve_variables(answer_template, context)
            output_variable = config.get("output_variable", "answer")
            if output_variable:
                context.set_variable(output_variable, rendered)
            return {
                "status": "completed",
                "output": {output_variable: rendered}
            }
        except Exception as e:
            logger.error(f"Answer generation failed: {e}", exc_info=True)
            raise

    async def _execute_pm_module_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行 PM 模块节点 — 调用 PMEntries 服务层读写 PM 工作台数据。"""
        try:
            from open_webui.models.pm import PMEntries, PMEntryForm, PMEntryUpdateForm
            
            module_type = config.get("module_type", "")
            action = config.get("action", "read")
            project_id = config.get("project_id", "")
            entry_id = config.get("entry_id", "")
            filter_data = config.get("filter", {})
            data = config.get("data", {})

            # D63/Bug5 根因修复：project_id / module_type 也走 D30 模板解析
            # 之前 D30 只解析 entry_id / filter_data / data，遗漏了 project_id ——
            # AI 生成的工作流 config 是 "project_id": "{{input.project_id}}"（模板字符串），
            # 原代码 `config.get("project_id", "") or context.get_variable(...)` 用 `or` 短路，
            # 因为 "{{input.project_id}}" 是 truthy，不会 fallback 到 context；
            # 结果 PMEntries.insert_new_entry 用字面量 "{{input.project_id}}" 作为 project_id 写入 DB，
            # entry 创建在「幻影 project_id」下，用户在真实项目页面看不到。
            if isinstance(project_id, str) and project_id:
                project_id = self._resolve_variables(project_id, context)
            if not project_id:
                project_id = context.get_variable("project_id", "")

            if isinstance(module_type, str) and module_type:
                module_type = self._resolve_variables(module_type, context)

            # module_type 命名归一化（保留现有逻辑）
            if module_type == "product-architecture":
                module_type = "architecture"

            # D30: 解析模板变量，让 {{...}} 引用上游节点数据
            # 修复「节点显示 completed 但实际数据没通」bug ——
            # 之前 data/filter_data/entry_id 直接取 config 字面值，{{...}} 不被解析，
            # 导致节点间数据流断裂，DB 中写入的是字面字符串而非解析后的数据。
            # 与 parameter_extractor / http_request / tool_call 节点的解析行为一致。
            if isinstance(entry_id, str) and entry_id:
                entry_id = self._resolve_variables(entry_id, context)

            if isinstance(filter_data, dict):
                filter_data = self._resolve_input_mapping(filter_data, context)
            elif isinstance(filter_data, str) and filter_data:
                resolved = self._resolve_variables(filter_data, context)
                try:
                    filter_data = json.loads(resolved)
                except (json.JSONDecodeError, ValueError):
                    filter_data = {}

            if isinstance(data, dict):
                data = self._resolve_input_mapping(data, context)
            elif isinstance(data, str) and data:
                resolved = self._resolve_variables(data, context)
                try:
                    data = json.loads(resolved)
                except (json.JSONDecodeError, ValueError):
                    # 保持原字符串值（可能是普通文本而非 JSON）
                    data = resolved

            # 从 context 获取 user_id
            user_id = getattr(context._user, 'id', None) if context._user else None
            
            if action == "read":
                if entry_id:
                    entry = await PMEntries.get_entry_by_id(entry_id)
                    # D66/Bug5 漏洞 3 修复：entry 不存在时报 failed，不再返回 {entry: None} + completed
                    if entry is None:
                        output = {"error": f"entry_id={entry_id} 不存在"}
                    else:
                        output = {"entry": entry.model_dump()}
                elif project_id and module_type:
                    entries = await PMEntries.get_entries_by_project_and_module(project_id, module_type)
                    # 应用 filter
                    filtered = entries
                    if filter_data:
                        for key, val in filter_data.items():
                            filtered = [e for e in filtered if getattr(e, key, None) == val]
                    output = {
                        "entries": [e.model_dump() for e in filtered],
                        "count": len(filtered)
                    }
                else:
                    output = {"error": "read action requires entry_id or (project_id + module_type)"}
            elif action in ("create", "write"):
                # C2: 'write' 作为 'create' 的别名 —— 兼容 ai_generator.py 旧 prompt
                # （ai_generator 在 C6 修复前会输出 action='write'，引擎旧实现走 unknown 分支返回 error）
                if not user_id:
                    raise RuntimeError("user_id required for create action")
                # D63/Bug5-Diag 诊断日志：写入前记录 project_id / module_type 真实值，便于排查
                logger.info(f"[Bug5-Diag] pm_module create 开始: project_id={project_id!r}, module_type={module_type!r}, user_id={user_id}, title={data.get('title', '')!r}")
                form = PMEntryForm(
                    project_id=project_id,
                    module_type=module_type,
                    title=data.get("title", f"{module_type} entry"),
                    content=data.get("content", ""),
                    data=data.get("data", {}),
                    status=data.get("status", "draft"),
                    priority=data.get("priority", "medium"),
                )
                entry = await PMEntries.insert_new_entry(user_id, form)
                logger.info(f"[Bug5-Diag] pm_module create 完成: entry_id={entry.id if entry else None}, project_id={entry.project_id if entry else 'N/A'}")
                # D66/Bug5 漏洞 4 修复：insert_new_entry 返回 None 时报 failed
                if entry is None:
                    output = {"error": "PMEntries.insert_new_entry 返回 None，写入失败"}
                else:
                    output = {"entry": entry.model_dump()}
            elif action == "update":
                if not entry_id:
                    raise RuntimeError("entry_id required for update action")
                update_form = PMEntryUpdateForm(**data)
                entry = await PMEntries.update_entry_by_id(entry_id, update_form)
                output = {"entry": entry.model_dump() if entry else None}
            elif action == "delete":
                if not entry_id:
                    raise RuntimeError("entry_id required for delete action")
                success = await PMEntries.delete_entry_by_id(entry_id)
                output = {"deleted": success}
            else:
                output = {"error": f"unknown action: {action}"}

            # C3a: output 含 error 字段时，status 反映 failed —— 不再误导用户「completed 但数据没通」
            # 之前无论 output 是 {entry:...} 还是 {error:...}，status 都返回 completed，
            # 导致 BFS 继续往下游传播，下游节点拿到空数据也装作完成。
            node_status = "failed" if (isinstance(output, dict) and output.get("error")) else "completed"
            return {
                "status": node_status,
                "output": output
            }
        except Exception as e:
            logger.error(f"PM module operation failed: {e}", exc_info=True)
            raise

    # ==================== 四类扩展节点 executor（Part A）====================

    def _resolve_input_mapping(self, input_mapping: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """解析 input_mapping 中的变量引用 {{var}} / {{node_id.field}} 为实际值。"""
        resolved: Dict[str, Any] = {}
        if not isinstance(input_mapping, dict):
            return resolved
        for key, val in input_mapping.items():
            if isinstance(val, str):
                # 字符串中可能包含 {{...}} 引用，用 _resolve_variables 替换
                resolved_str = self._resolve_variables(val, context)
                # 若整串就是一个 {{...}} 引用，尝试解析为原始类型（dict/list/number/bool）
                stripped = resolved_str.strip()
                if stripped.startswith("{{") and stripped.endswith("}}"):
                    # 引用未解析（占位符保留），直接用字符串
                    resolved[key] = resolved_str
                else:
                    # 尝试 JSON 解析（dict/list/number/bool/null），否则保留字符串
                    try:
                        resolved[key] = json.loads(stripped) if stripped else resolved_str
                    except (json.JSONDecodeError, ValueError):
                        resolved[key] = resolved_str
            else:
                resolved[key] = val
        return resolved

    def _structure_output(self, raw_output: Any, output_schema: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """按 output_schema 结构化节点输出。无 schema 时返回 {"result": raw_output}。"""
        if not output_schema:
            return self._serialize_model_output(raw_output)
        structured: Dict[str, Any] = {}
        for field_def in output_schema:
            fname = field_def.get("name", "")
            if not fname:
                continue
            if isinstance(raw_output, dict) and fname in raw_output:
                structured[fname] = raw_output[fname]
            elif fname == "result":
                structured[fname] = raw_output
        # 兜底：若 schema 没匹配到任何字段，塞入 result
        if not structured:
            structured["result"] = raw_output
        return structured

    async def _execute_tool_call_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行 tool_call 节点 — 调用 openwebui Tool。

        支持两种配置格式：
        1. 新格式：{extension_id: "tool_id:spec_name", input_mapping: {...}, output_schema: [...]}
        2. 旧格式：{tool_name: "...", parameters: {...}}（向后兼容，走 _execute_custom_node 逻辑）
        """
        try:
            extension_id = config.get("extension_id", "")
            input_mapping = config.get("input_mapping", {}) or {}
            output_schema = config.get("output_schema", []) or []

            # 旧格式兼容：无 extension_id 但有 tool_name 时走 custom node 逻辑
            if not extension_id and config.get("tool_name"):
                return await self._execute_custom_node(config, context)

            # 解析 extension_id（格式 "tool_id:spec_name" 或 "tool_id"）
            parts = extension_id.split(":", 1)
            tool_id = parts[0]
            spec_name = parts[1] if len(parts) > 1 else None

            # 解析 input_mapping
            resolved_params = self._resolve_input_mapping(input_mapping, context)

            # 加载 Tool 模块并调用指定 spec
            from open_webui.models.tools import Tools
            tool = await Tools.get_tool_by_id(tool_id)
            if not tool:
                raise RuntimeError(f"Tool '{tool_id}' not found")

            # 加载 tool 模块
            try:
                from open_webui.utils.plugin import load_tool_module_by_id
                tool_module, _ = await load_tool_module_by_id(tool_id, content=tool.content)
            except Exception as e:
                raise RuntimeError(f"Failed to load tool module '{tool_id}': {e}")

            # 获取 Tools 类实例并调用指定方法
            handler = None
            if spec_name and hasattr(tool_module, spec_name):
                handler = getattr(tool_module, spec_name)
            elif hasattr(tool_module, "execute"):
                handler = getattr(tool_module, "execute")
            else:
                # 回退：从 specs 中找第一个可调用方法
                for spec in (tool.specs or []):
                    sname = spec.get("name", "")
                    if sname and hasattr(tool_module, sname):
                        handler = getattr(tool_module, sname)
                        break

            if handler is None or not callable(handler):
                raise RuntimeError(f"Tool '{tool_id}' has no callable handler for spec '{spec_name}'")

            if asyncio.iscoroutinefunction(handler):
                raw_result = await handler(**resolved_params)
            else:
                raw_result = handler(**resolved_params)

            structured = self._structure_output(raw_result, output_schema)
            return {
                "status": "completed",
                "output": {
                    "extension_id": extension_id,
                    "tool_name": tool.name,
                    "input": resolved_params,
                    "result": structured,
                }
            }
        except Exception as e:
            logger.error(f"ToolCallExecutor failed: {e}", exc_info=True)
            raise

    async def _execute_function_call_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行 function_call 节点 — 调用 openwebui Function（filter/action/pipe）。"""
        try:
            extension_id = config.get("extension_id", "")
            input_mapping = config.get("input_mapping", {}) or {}
            output_schema = config.get("output_schema", []) or []

            if not extension_id:
                raise RuntimeError("function_call 节点未配置 extension_id")

            resolved_params = self._resolve_input_mapping(input_mapping, context)

            from open_webui.models.functions import Functions
            fn = await Functions.get_function_by_id(extension_id)
            if not fn:
                raise RuntimeError(f"Function '{extension_id}' not found")
            if not fn.is_active:
                logger.warning(f"Function '{extension_id}' is not active, attempting to call anyway")

            # 加载 function 模块
            try:
                from open_webui.utils.plugin import load_function_module_by_id
                fn_module, fn_type, _ = await load_function_module_by_id(extension_id, content=fn.content)
            except Exception as e:
                raise RuntimeError(f"Failed to load function module '{extension_id}': {e}")

            # 根据 function 类型调用对应方法
            # Pipe: inlet/outlet/pipe; Filter: inlet/outlet; Action: action
            raw_result = None
            if hasattr(fn_module, "pipe"):
                # Pipe 类型：调用 pipe(body={...})
                if asyncio.iscoroutinefunction(fn_module.pipe):
                    raw_result = await fn_module.pipe(body=resolved_params, __user__={"id": getattr(context._user, 'id', '')} if context._user else None)
                else:
                    raw_result = fn_module.pipe(body=resolved_params, __user__={"id": getattr(context._user, 'id', '')} if context._user else None)
            elif hasattr(fn_module, "action"):
                if asyncio.iscoroutinefunction(fn_module.action):
                    raw_result = await fn_module.action(**resolved_params)
                else:
                    raw_result = fn_module.action(**resolved_params)
            elif hasattr(fn_module, "inlet"):
                # Filter 类型：inlet 处理
                if asyncio.iscoroutinefunction(fn_module.inlet):
                    raw_result = await fn_module.inlet(body=resolved_params, __user__={"id": getattr(context._user, 'id', '')} if context._user else None)
                else:
                    raw_result = fn_module.inlet(body=resolved_params, __user__={"id": getattr(context._user, 'id', '')} if context._user else None)
            else:
                raise RuntimeError(f"Function '{extension_id}' has no callable pipe/action/inlet method")

            structured = self._structure_output(raw_result, output_schema)
            return {
                "status": "completed",
                "output": {
                    "extension_id": extension_id,
                    "function_name": fn.name,
                    "function_type": fn.type,
                    "input": resolved_params,
                    "result": structured,
                }
            }
        except Exception as e:
            logger.error(f"FunctionCallExecutor failed: {e}", exc_info=True)
            raise

    async def _execute_skill_call_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行 skill_call 节点 — 调用 openwebui Skill。"""
        try:
            extension_id = config.get("extension_id", "")
            input_mapping = config.get("input_mapping", {}) or {}
            output_schema = config.get("output_schema", []) or []

            if not extension_id:
                raise RuntimeError("skill_call 节点未配置 extension_id")

            resolved_params = self._resolve_input_mapping(input_mapping, context)

            from open_webui.models.skills import Skills
            skill = await Skills.get_skill_by_id(extension_id)
            if not skill:
                raise RuntimeError(f"Skill '{extension_id}' not found")

            # Skill 是一段 Python 代码，执行其 main 函数或 Skills 类
            import types as _types
            import tempfile
            import os as _os
            module_name = f"skill_{extension_id}"
            module = _types.ModuleType(module_name)
            _sys_modules_key = module_name
            import sys as _sys
            _sys.modules[module_name] = module

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
            temp_file.close()
            try:
                with open(temp_file.name, "w", encoding="utf-8") as f:
                    f.write(skill.content)
                module.__dict__["__file__"] = temp_file.name
                exec(skill.content, module.__dict__)

                raw_result = None
                # 优先调用 main(params=...)
                if hasattr(module, "main"):
                    main_fn = module.main
                    if asyncio.iscoroutinefunction(main_fn):
                        raw_result = await main_fn(params=resolved_params)
                    else:
                        raw_result = main_fn(params=resolved_params)
                elif hasattr(module, "execute"):
                    execute_fn = module.execute
                    if asyncio.iscoroutinefunction(execute_fn):
                        raw_result = await execute_fn(params=resolved_params)
                    else:
                        raw_result = execute_fn(params=resolved_params)
                elif hasattr(module, "Skill"):
                    # Skill 类形式
                    skill_instance = module.Skill()
                    if hasattr(skill_instance, "run"):
                        run_fn = skill_instance.run
                        if asyncio.iscoroutinefunction(run_fn):
                            raw_result = await run_fn(params=resolved_params)
                        else:
                            raw_result = run_fn(params=resolved_params)
                    else:
                        raise RuntimeError(f"Skill '{extension_id}' class has no run() method")
                else:
                    raise RuntimeError(f"Skill '{extension_id}' has no main()/execute()/Skill class")

                structured = self._structure_output(raw_result, output_schema)
                return {
                    "status": "completed",
                    "output": {
                        "extension_id": extension_id,
                        "skill_name": skill.name,
                        "input": resolved_params,
                        "result": structured,
                    }
                }
            finally:
                _os.unlink(temp_file.name)
                if _sys_modules_key in _sys.modules:
                    del _sys.modules[_sys_modules_key]
        except Exception as e:
            logger.error(f"SkillCallExecutor failed: {e}", exc_info=True)
            raise

    async def _execute_mcp_call_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行 mcp_call 节点 — 通过 MCPClient 连接 MCP server 调用 tool。"""
        try:
            server_id = config.get("server_id", "")
            extension_id = config.get("extension_id", "")
            input_mapping = config.get("input_mapping", {}) or {}
            output_schema = config.get("output_schema", []) or []

            if not extension_id:
                raise RuntimeError("mcp_call 节点未配置 extension_id")

            # extension_id 格式 "server_id:tool_name"
            parts = extension_id.split(":", 1)
            if len(parts) == 2:
                server_id = parts[0]
                tool_name = parts[1]
            else:
                tool_name = extension_id

            if not server_id:
                raise RuntimeError("mcp_call 节点未配置 server_id")

            resolved_params = self._resolve_input_mapping(input_mapping, context)

            # 查找 MCP server 连接配置
            # 通过 request.app.state.config.TOOL_SERVER_CONNECTIONS 获取（需从 context._request 取）
            request = context._request
            connections = []
            if request and hasattr(request.app.state, 'config'):
                connections = request.app.state.config.TOOL_SERVER_CONNECTIONS
            server_config = None
            for conn in connections:
                if conn.get("id") == server_id or (conn.get("info", {}) or {}).get("id") == server_id:
                    server_config = conn
                    break
            if not server_config:
                raise RuntimeError(f"MCP server '{server_id}' not found in connections")

            server_url = server_config.get("url", "")
            if not server_url:
                raise RuntimeError(f"MCP server '{server_id}' has no URL")

            # 构造 headers
            headers = {}
            auth_type = server_config.get("auth_type", "bearer")
            if auth_type == "bearer":
                token = server_config.get("key", "")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            # 使用 MCPClient 连接并调用 tool
            from open_webui.utils.mcp.client import MCPClient
            mcp_client = MCPClient()
            try:
                await mcp_client.connect(server_url, headers=headers)
                result_content = await mcp_client.call_tool(tool_name, resolved_params)
            finally:
                await mcp_client.disconnect()

            structured = self._structure_output(result_content, output_schema)
            return {
                "status": "completed",
                "output": {
                    "extension_id": extension_id,
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "input": resolved_params,
                    "result": structured,
                }
            }
        except Exception as e:
            logger.error(f"McpCallExecutor failed: {e}", exc_info=True)
            raise

    async def _execute_human_input_node(self, config: Dict, context: ExecutionContext) -> Dict:
        """执行 human_input 节点 — 挂起状态机，等待用户通过 resume 端点唤醒。

        机制：
        1. 注册 (execution_id, node_id) -> asyncio.Event 到全局挂起表
        2. 通过 _notify_listeners 推送 awaiting_input 事件（前端弹模态框）
        3. await event.wait() 阻塞，直到 resume_human_input 被调用
        4. 唤醒后把 user_response 写入 context.variables[output_variable]
        """
        prompt = config.get("prompt", "请确认")
        fields = config.get("fields", [])
        output_variable = config.get("output_variable", "human_input_result")

        # 从 context 提取 node_id（由 _execute_node 调用方写入 context.variables 临时字段；
        # 若无则用通用占位 ID，配合 execution_id 仍可定位）
        node_id = context.get_variable("_current_node_id", "unknown")
        execution_id = context.execution_id

        logger.info(
            "human_input node suspended: execution_id=%s node_id=%s prompt=%r",
            execution_id, node_id, prompt,
        )

        event = asyncio.Event()
        _HUMAN_INPUT_EVENTS[(execution_id, node_id)] = {
            "event": event,
            "response": None,
            "prompt": prompt,
            "fields": fields,
        }

        # 推送 awaiting_input 事件给前端监听器（SSE/WebSocket）
        try:
            await self._notify_listeners(execution_id, {
                "type": "awaiting_input",
                "event_type": "awaiting_input",
                "execution_id": execution_id,
                "node_id": node_id,
                "prompt": prompt,
                "fields": fields,
                "output_variable": output_variable,
                "timestamp": time.time(),
            })
        except Exception as e:
            logger.error("Failed to notify listeners for human_input: %s", e)

        # 挂起等待 resume
        await event.wait()

        # 唤醒后取出 response
        suspended = _HUMAN_INPUT_EVENTS.pop((execution_id, node_id), None)
        response = (suspended or {}).get("response") or {}

        # 写入 context.variables
        context.set_variable(output_variable, response)
        logger.info(
            "human_input node resumed: execution_id=%s node_id=%s",
            execution_id, node_id,
        )

        return {
            "status": "completed",
            "output": {
                "prompt": prompt,
                "response": response,
                "output_variable": output_variable,
            }
        }

    @classmethod
    async def resume_human_input(
        cls,
        execution_id: str,
        node_id: str,
        response: Dict[str, Any],
    ) -> bool:
        """恢复挂起在 human_input 节点的 workflow execution。

        Args:
            execution_id: workflow run/execution ID
            node_id: 挂起的 human_input 节点 ID
            response: 用户提交的表单响应

        Returns:
            True 如果找到挂起节点并成功唤醒；False 如果未找到（可能已超时或已完成）
        """
        key = (execution_id, node_id)
        suspended = _HUMAN_INPUT_EVENTS.get(key)
        if not suspended:
            logger.warning(
                "resume_human_input: no suspended human_input node for execution_id=%s node_id=%s",
                execution_id, node_id,
            )
            return False
        suspended["response"] = response
        suspended["event"].set()
        logger.info(
            "resume_human_input: woke up execution_id=%s node_id=%s",
            execution_id, node_id,
        )
        return True

    def _merge_results(self, results: List[Any], strategy: str) -> Dict:
        """Merge results from parallel branches."""
        if strategy == "merge":
            merged = {}
            for result in results:
                if isinstance(result, dict):
                    merged.update(result)
            return merged
        elif strategy == "concat":
            return {"results": [r for r in results if r is not None]}
        elif strategy == "first":
            for result in results:
                if result is not None:
                    return result
            return {}
        else:
            return {"results": results}

    def _resolve_variables(self, template: str, context: ExecutionContext) -> str:
        """Resolve variables: {{var}} from flat dict, {{node_id.field}} from node_results.

        Supports:
        - {{var}} — flat variable from context.variables (backward compatible)
        - {{node_id.field}} — upstream node output from context.node_results
        - {{node_id.field.subfield}} — nested field access
        - {{$input}} — workflow input (start node output)
        """
        import re

        def replace_match(match):
            expr = match.group(1).strip()
            # {{$input}} — workflow input parameter
            if expr == '$input':
                value = context.variables.get('input') or context.variables.get('$input')
                # C4: 变量未找到时返回空字符串，不返回字面量 {{...}}
                # 之前返回 match.group(0) 让下游误把字面量当真实数据
                return str(value) if value is not None else ""
            # J3/D78: {{input.X}} / {{node_id.field}} — 优先从 context.variables 嵌套 dict 取值
            # 修复 v7 D63 的遗留 bug：
            # - engine.py:219 是 `variables={**input_data}`，扁平展开后
            #   context.variables = {"input": {"project_id": "abc", ...}}
            # - 原 L2087 走 `node_results.get("input")` 分支返回 None → "{{input.project_id}}" 解析为空
            # - J3a: 先尝试从 context.variables 嵌套取值（适配 input_data 嵌套结构）
            if '.' in expr:
                parts = expr.split('.', 1)
                first, rest = parts[0], parts[1]
                # J3a: 优先从 context.variables 嵌套取值
                if first in context.variables:
                    val = context.variables[first]
                    # 递归取 rest 路径（支持 a.b.c 多层）
                    for k in rest.split('.'):
                        if isinstance(val, dict) and k in val:
                            val = val[k]
                        elif isinstance(val, list):
                            try:
                                idx = int(k)
                                val = val[idx] if 0 <= idx < len(val) else None
                            except (ValueError, IndexError):
                                val = None
                                break
                        else:
                            val = None
                            break
                    if val is not None:
                        return str(val)
                # J3b: 回退到 node_results 分支（保留原逻辑，适配 {{node_id.field}} 引用上游节点输出）
                node_result = context.node_results.get(first)
                if node_result and hasattr(node_result, 'output') and node_result.output:
                    # Navigate nested fields (e.g., metadata.tokens)
                    current = node_result.output
                    for sub in rest.split('.'):
                        if isinstance(current, dict) and sub in current:
                            current = current[sub]
                        else:
                            current = None
                            break
                    if current is not None:
                        return str(current)
                # C4: 未找到变量返回空字符串（was: match.group(0)）
                return ""
            # {{var}} — flat variable (backward compatible)
            value = context.variables.get(expr)
            # C4: 未找到变量返回空字符串（was: match.group(0)）
            return str(value) if value is not None else ""

        return re.sub(r'\{\{([^}]+)\}\}', replace_match, template)

    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Evaluate a condition expression."""
        try:
            if not condition or not condition.strip():
                return True
            
            # Replace variables in condition
            eval_context = {**context.variables}
            
            # Use the conditions module for safe evaluation
            from open_webui.services.workflow.conditions import evaluate_condition
            return evaluate_condition(condition, eval_context)
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False

    def _evaluate_filter(self, item: Any, condition: str, context: ExecutionContext) -> bool:
        """Evaluate a filter condition for an item."""
        try:
            if not condition:
                return True
            
            # Simple filter evaluation
            eval_context = {**context.variables, "item": item}
            
            from open_webui.services.workflow.conditions import evaluate_condition
            return evaluate_condition(condition, eval_context)
            
        except Exception as e:
            logger.error(f"Filter evaluation failed: {e}")
            return True

    async def _notify_listeners(self, execution_id: str, message: Dict):
        """Notify all listeners of an execution event."""
        listeners = self._listeners.get(execution_id, [])
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(message)
                else:
                    listener(message)
            except Exception as e:
                logger.error(f"Listener notification failed: {e}")

    def add_listener(self, execution_id: str, listener: Callable):
        """Add a listener for execution events."""
        if execution_id not in self._listeners:
            self._listeners[execution_id] = []
        self._listeners[execution_id].append(listener)

    def remove_listener(self, execution_id: str, listener: Callable):
        """Remove a listener for execution events."""
        if execution_id in self._listeners:
            self._listeners[execution_id] = [
                l for l in self._listeners[execution_id] if l != listener
            ]

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        if execution_id in self._running_executions:
            task = self._running_executions[execution_id]
            task.cancel()
            
            # Update execution status
            await WorkflowExecutions.update_execution_status(
                execution_id, "cancelled"
            )
            
            return True
        return False

    async def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get execution status.

        优先检测 human_input 节点挂起状态：若该 execution 在 _HUMAN_INPUT_EVENTS
        中有挂起项，返回 status="awaiting_input" + awaiting_input 详情，
        前端轮询检测到此状态后弹出表单，用户提交后调 /runs/{execution_id}/resume 唤醒。
        """
        # 优先检测 human_input 挂起状态
        for (eid, nid), suspended in _HUMAN_INPUT_EVENTS.items():
            if eid == execution_id:
                # 收集已知 node_results（若有上下文）
                node_results = {}
                ctx = self._execution_contexts.get(execution_id)
                if ctx is not None:
                    node_results = {
                        node_id: {
                            "status": result.status.value,
                            "output": result.output,
                            "error": result.error,
                            "execution_time_ms": result.execution_time_ms,
                        }
                        for node_id, result in ctx.node_results.items()
                    }
                return {
                    "execution_id": execution_id,
                    "workflow_id": ctx.workflow_id if ctx is not None else None,
                    "status": "awaiting_input",
                    "awaiting_input": {
                        "node_id": nid,
                        "prompt": suspended.get("prompt", ""),
                        "fields": suspended.get("fields", []),
                        "output_variable": "human_input_result",
                    },
                    "node_results": node_results,
                    "logs": ctx.logs if ctx is not None else [],
                    "error_message": None,
                    "started_at": ctx.started_at if ctx is not None else None,
                    "completed_at": None,
                }

        # Check in-memory context first
        if execution_id in self._execution_contexts:
            context = self._execution_contexts[execution_id]
            # 过滤掉内部临时变量（以 _ 开头，如 _current_node_id）
            clean_vars = {k: v for k, v in context.variables.items() if not k.startswith('_')}
            return {
                "execution_id": execution_id,
                "workflow_id": context.workflow_id,
                "status": context.status.value,
                "variables": clean_vars,
                "node_results": {
                    node_id: {
                        "status": result.status.value,
                        "output": result.output,
                        "error": result.error,
                        "execution_time_ms": result.execution_time_ms
                    }
                    for node_id, result in context.node_results.items()
                },
                "logs": context.logs,
                "error_message": context.error_message,
                "started_at": context.started_at,
                "completed_at": context.completed_at
            }

        # Fall back to database
        execution = await WorkflowExecutions.get_execution_by_id(execution_id)
        if not execution:
            return None

        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "node_states": execution.node_states,
            "logs": execution.logs,
            "error_message": execution.error_message,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at
        }


# Singleton instance
workflow_execution_engine = WorkflowExecutionEngine()
