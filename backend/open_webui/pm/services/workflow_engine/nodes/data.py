"""Data processing node executors."""

from typing import Any, Dict

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class VariableSetNodeExecutor(BaseNodeExecutor):
    """Executor for variable set nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            variables = node_config.get('variables', {})
            
            for var_name, var_value in variables.items():
                # Resolve variable references
                if isinstance(var_value, str) and var_value.startswith('{{') and var_value.endswith('}}'):
                    ref_name = var_value[2:-2]
                    var_value = state.get_variable(ref_name)
                
                state.set_variable(var_name, var_value)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'variables_set': list(variables.keys())}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )


class TransformNodeExecutor(BaseNodeExecutor):
    """Executor for data transform nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            input_var = node_config.get('input', '')
            transform = node_config.get('transform', '')
            output_var = node_config.get('output', '')
            
            input_data = state.get_variable(input_var)
            
            # Apply transformation
            if transform == 'uppercase':
                result = str(input_data).upper()
            elif transform == 'lowercase':
                result = str(input_data).lower()
            elif transform == 'json_parse':
                import json
                result = json.loads(input_data) if isinstance(input_data, str) else input_data
            elif transform == 'json_stringify':
                import json
                result = json.dumps(input_data)
            else:
                result = input_data
            
            if output_var:
                state.set_variable(output_var, result)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'transformed': result}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )


class FilterNodeExecutor(BaseNodeExecutor):
    """Executor for filter nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            input_var = node_config.get('input', '')
            condition = node_config.get('condition', '')
            output_var = node_config.get('output', '')
            
            input_data = state.get_variable(input_var)
            
            # Filter logic
            if isinstance(input_data, list):
                result = [item for item in input_data if item]
            else:
                result = input_data
            
            if output_var:
                state.set_variable(output_var, result)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'filtered': result}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
