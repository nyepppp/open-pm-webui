"""Timbal tool definitions and interfaces."""

from typing import Dict, Any, Callable
from abc import ABC, abstractmethod


class TimbalToolInterface(ABC):
    """Base interface for Timbal tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    async def validate(self, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters."""
        pass


class PMOperationTool(TimbalToolInterface):
    """Tool for PM workspace operations."""
    
    def __init__(self, operation: str, handler: Callable):
        super().__init__(
            name=f"pm_{operation}",
            description=f"PM workspace operation: {operation}"
        )
        self.operation = operation
        self.handler = handler
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PM operation."""
        return await self.handler(**parameters)
    
    async def validate(self, parameters: Dict[str, Any]) -> bool:
        """Validate PM operation parameters."""
        # Basic validation - check required fields
        required_fields = self._get_required_fields()
        return all(field in parameters for field in required_fields)
    
    def _get_required_fields(self) -> list:
        """Get required fields for this operation."""
        # This would be populated based on the specific operation
        return []


class OpenWebUISkillTool(TimbalToolInterface):
    """Tool for OpenWebUI skills."""
    
    def __init__(self, skill_id: str, skill_config: Dict[str, Any]):
        super().__init__(
            name=f"skill_{skill_id}",
            description=skill_config.get("description", "OpenWebUI skill")
        )
        self.skill_id = skill_id
        self.skill_config = skill_config
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OpenWebUI skill."""
        # Implementation would call OpenWebUI skill API
        return {"status": "executed", "skill_id": self.skill_id}
    
    async def validate(self, parameters: Dict[str, Any]) -> bool:
        """Validate skill parameters."""
        return True


class OpenWebUIPromptTool(TimbalToolInterface):
    """Tool for OpenWebUI prompts."""
    
    def __init__(self, prompt_id: str, prompt_config: Dict[str, Any]):
        super().__init__(
            name=f"prompt_{prompt_id}",
            description=prompt_config.get("description", "OpenWebUI prompt")
        )
        self.prompt_id = prompt_id
        self.prompt_config = prompt_config
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OpenWebUI prompt."""
        # Implementation would call OpenWebUI prompt API
        return {"status": "executed", "prompt_id": self.prompt_id}
    
    async def validate(self, parameters: Dict[str, Any]) -> bool:
        """Validate prompt parameters."""
        return True


class OpenWebUIToolTool(TimbalToolInterface):
    """Tool for OpenWebUI native tools."""
    
    def __init__(self, tool_id: str, tool_config: Dict[str, Any]):
        super().__init__(
            name=f"tool_{tool_id}",
            description=tool_config.get("description", "OpenWebUI tool")
        )
        self.tool_id = tool_id
        self.tool_config = tool_config
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OpenWebUI tool."""
        # Implementation would call OpenWebUI tool API
        return {"status": "executed", "tool_id": self.tool_id}
    
    async def validate(self, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters."""
        return True
