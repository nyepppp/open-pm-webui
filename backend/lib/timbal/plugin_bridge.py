"""Plugin bridge for OpenWebUI-Timbal integration."""

from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
import asyncio


class PluginBridgeInterface(ABC):
    """Base interface for plugin bridge."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin bridge with configuration."""
        pass
    
    @abstractmethod
    async def execute(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool through the plugin bridge."""
        pass
    
    @abstractmethod
    async def validate(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters."""
        pass


class OpenWebUIPluginBridge(PluginBridgeInterface):
    """Plugin bridge for OpenWebUI integration."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        self.initialized = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin bridge with configuration."""
        self.config = config
        # Register available tools from OpenWebUI
        await self._register_tools()
        self.initialized = True
    
    async def _register_tools(self) -> None:
        """Register available tools from OpenWebUI."""
        # This would discover and register OpenWebUI skills, prompts, and tools
        pass
    
    async def execute(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool through the plugin bridge."""
        if not self.initialized:
            raise RuntimeError("Plugin bridge not initialized")
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        return await tool.execute(inputs)
    
    async def validate(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters."""
        if not self.initialized:
            raise RuntimeError("Plugin bridge not initialized")
        
        if tool_name not in self.tools:
            return False
        
        tool = self.tools[tool_name]
        return await tool.validate(parameters)
    
    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool with the plugin bridge."""
        self.tools[name] = tool
    
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool from the plugin bridge."""
        if name in self.tools:
            del self.tools[name]


class PluginBridgeFactory:
    """Factory for creating plugin bridge instances."""
    
    _instance: Optional[OpenWebUIPluginBridge] = None
    
    @classmethod
    def get_instance(cls) -> OpenWebUIPluginBridge:
        """Get singleton instance of plugin bridge."""
        if cls._instance is None:
            cls._instance = OpenWebUIPluginBridge()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        cls._instance = None
