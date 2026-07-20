"""Control flow node executors."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class StartNodeExecutor(BaseNodeExecutor):
    """Executor for start nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output={'started': True}
        )


class EndNodeExecutor(BaseNodeExecutor):
    """Executor for end nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output={'completed': True, 'final_output': state.variables}
        )


class ConditionNodeExecutor(BaseNodeExecutor):
    """Executor for condition nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            condition = node_config.get('condition', '')
            result = self._evaluate_condition(condition, state)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'condition_met': result}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
    
    def _evaluate_condition(self, condition: str, state: ExecutionState) -> bool:
        """Evaluate a condition expression."""
        try:
            expr = condition
            for var_name, var_value in state.variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                expr = expr.replace(placeholder, repr(var_value))
            
            return eval(expr, {"__builtins__": {}}, {})
        except:
            return False


class LoopNodeExecutor(BaseNodeExecutor):
    """Executor for loop nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            iterations = node_config.get('iterations', 1)
            items = node_config.get('items', [])
            
            if items:
                results = []
                for item in items:
                    state.set_variable('current_item', item)
                    results.append(item)
                
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output={'iterations': len(items), 'results': results}
                )
            else:
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output={'iterations': iterations}
                )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
