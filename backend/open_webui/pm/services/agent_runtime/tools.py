"""Tool registry and execution for Agent."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ToolResult:
    """Tool execution result."""
    def __init__(self, success: bool, output: Any = None, error: str = None):
        self.success = success
        self.output = output
        self.error = error


class BaseTool(ABC):
    """Base class for tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM."""
        return {
            'name': self.name,
            'description': self.description
        }


class ToolRegistry:
    """Registry for tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        return await tool.execute(**kwargs)
