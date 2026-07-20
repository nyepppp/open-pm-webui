"""Base node executor class."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..state import ExecutionState, NodeResult


class BaseNodeExecutor(ABC):
    """Base class for all node executors."""
    
    @abstractmethod
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        """
        Execute the node.
        
        Args:
            node_config: Node configuration
            state: Current execution state
            
        Returns:
            Node execution result
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate node configuration.
        
        Args:
            config: Node configuration
            
        Returns:
            True if valid
        """
        return True
    
    def get_required_inputs(self) -> list:
        """Get list of required input names."""
        return []
    
    def get_outputs(self) -> list:
        """Get list of output names."""
        return []
