"""Workflow execution engine with Timbal integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from open_webui.pm.services.workflow_engine.dag import DAG, DAGNode, parse_dag
from open_webui.pm.services.workflow_engine.state import (
    ExecutionState,
    ExecutionStatus,
    NodeResult,
    NodeStatus
)
from open_webui.pm.services.workflow_engine.nodes.base import BaseNodeExecutor
from open_webui.pm.services.workflow_engine.nodes.control import (
    StartNodeExecutor,
    EndNodeExecutor,
    ConditionNodeExecutor,
    LoopNodeExecutor
)
from open_webui.pm.services.workflow_engine.nodes.llm import (
    LLMNodeExecutor,
    PromptTemplateNodeExecutor
)
from open_webui.pm.services.workflow_engine.nodes.data import (
    VariableSetNodeExecutor,
    TransformNodeExecutor,
    FilterNodeExecutor
)

# Import Timbal integration
try:
    from lib.timbal.execution_service import WorkflowExecutionService
    from lib.timbal.models import TimbalWorkflow, TimbalExecutionStatus
    TIMBAL_AVAILABLE = True
except ImportError:
    TIMBAL_AVAILABLE = False
    WorkflowExecutionService = None
    TimbalWorkflow = None
    TimbalExecutionStatus = None

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Enhanced workflow execution engine with DAG support."""
    
    def __init__(self, timbal_service=None):
        self.node_registry: Dict[str, BaseNodeExecutor] = {}
        self.timbal_service = timbal_service
        
        # Register built-in executors
        self._register_builtin_executors()
    
    def _register_builtin_executors(self):
        """Register all built-in node executors."""
        self.register_node_executor('start', StartNodeExecutor())
        self.register_node_executor('end', EndNodeExecutor())
        self.register_node_executor('condition', ConditionNodeExecutor())
        self.register_node_executor('loop', LoopNodeExecutor())
        self.register_node_executor('llm', LLMNodeExecutor())
        self.register_node_executor('prompt_template', PromptTemplateNodeExecutor())
        self.register_node_executor('variable_set', VariableSetNodeExecutor())
        self.register_node_executor('transform', TransformNodeExecutor())
        self.register_node_executor('filter', FilterNodeExecutor())
    
    def register_node_executor(self, node_type: str, executor: BaseNodeExecutor) -> None:
        """Register a node executor for a given type."""
        self.node_registry[node_type] = executor
    
    async def execute(
        self,
        workflow_id: UUID,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        input_data: Optional[Dict[str, Any]] = None
    ) -> ExecutionState:
        """Execute a workflow."""
        state = ExecutionState(
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING
        )
        
        # Set input variables
        if input_data:
            for key, value in input_data.items():
                state.set_variable(key, value)
        
        try:
            # Parse DAG
            dag = parse_dag(nodes, edges)
            
            # Validate DAG
            is_valid, error = dag.validate()
            if not is_valid:
                state.status = ExecutionStatus.FAILED
                state.error = error
                return state
            
            # Topological sort for execution order
            execution_order = dag.topological_sort()
            
            # Execute nodes
            for node_id in execution_order:
                if state.should_abort:
                    break
                
                node = dag.get_node(node_id)
                if node is None:
                    continue
                state.current_node_id = node_id
                
                try:
                    result = await self._execute_node(node, state)
                    state.set_node_result(node_id, result)
                    
                    if result.status == NodeStatus.FAILED:
                        if self._should_abort_on_error(node):
                            state.status = ExecutionStatus.FAILED
                            state.error = result.error
                            break
                
                except Exception as e:
                    logger.exception(f"Error executing node {node_id}")
                    state.set_node_result(node_id, NodeResult(
                        status=NodeStatus.FAILED,
                        error=str(e)
                    ))
                    state.status = ExecutionStatus.FAILED
                    state.error = str(e)
                    break
            
            # Set final status
            if state.status != ExecutionStatus.FAILED:
                state.status = ExecutionStatus.COMPLETED
        
        except Exception as e:
            logger.exception("Workflow execution failed")
            state.status = ExecutionStatus.FAILED
            state.error = str(e)
        
        return state
    
    async def _execute_node(self, node: DAGNode, state: ExecutionState) -> NodeResult:
        """Execute a single node."""
        started_at = datetime.utcnow()
        
        # Get executor for node type
        executor = self.node_registry.get(node.type)
        if not executor:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=f"No executor registered for node type: {node.type}",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
        
        # Execute
        try:
            result = await executor.execute(node.config, state)
            result.started_at = started_at
            result.completed_at = datetime.utcnow()
            return result
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
    
    def _should_abort_on_error(self, node: DAGNode) -> bool:
        """Check if workflow should abort on node error."""
        error_handling = node.config.get('error_handling', {})
        strategy = error_handling.get('strategy', 'abort')
        return strategy == 'abort'
    
    async def execute_with_timbal(
        self,
        workflow_id: UUID,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        input_data: Optional[Dict[str, Any]] = None,
        sync: bool = False
    ) -> ExecutionState:
        """Execute workflow with Timbal integration for skill nodes."""
        # First execute enhanced nodes
        state = await self.execute(workflow_id, nodes, edges, input_data)
        
        # If Timbal service available, execute Timbal-specific nodes
        if self.timbal_service and state.status == ExecutionStatus.COMPLETED:
            timbal_nodes = [n for n in nodes if n.get('type') == 'skill_call']
            
            for node in timbal_nodes:
                try:
                    # Create Timbal workflow
                    if TimbalWorkflow is not None:
                        timbal_workflow = TimbalWorkflow(
                            id=node['id'],
                            name=node.get('name', ''),
                            nodes=[node],
                            edges=[]
                        )
                        
                        # Execute via Timbal
                        execution = await self.timbal_service.execute_workflow(
                            workflow=timbal_workflow,
                            inputs=input_data or {},
                            sync=sync
                        )
                        
                        # Update state with Timbal results
                        if TimbalExecutionStatus is not None and execution.status == TimbalExecutionStatus.SUCCEEDED:
                            state.set_variable(f"timbal_{node['id']}", execution.outputs)
                    
                except Exception as e:
                    logger.exception(f"Timbal execution failed for node {node['id']}")
                    state.set_node_result(node['id'], NodeResult(
                        status=NodeStatus.FAILED,
                        error=f"Timbal execution failed: {str(e)}"
                    ))
        
        return state
