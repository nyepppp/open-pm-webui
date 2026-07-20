"""PM Agent Tools for workspace data access."""
from typing import Any, Optional

from open_webui.pm.models.session_binding import SessionBindings


class PMReadModuleTool:
    """Tool for reading data from PM workspace modules."""

    name = "pm_read_module"
    description = "Read data from any PM workspace module"

    async def execute(
        self,
        session_id: str,
        module_type: str,
        entry_id: Optional[str] = None,
    ) -> dict:
        """Read data from a PM workspace module."""
        # Get session binding
        binding = await SessionBindings.get_active_binding_by_session(session_id)
        if not binding:
            return {
                "success": False,
                "error": "Session not bound to any workspace",
            }

        workspace_id = binding.workspace_id

        # TODO: Implement actual module data reading
        # This would call the appropriate module service based on module_type
        return {
            "success": True,
            "workspace_id": workspace_id,
            "module_type": module_type,
            "entry_id": entry_id,
            "data": {},  # Placeholder for actual module data
        }


class PMWriteModuleTool:
    """Tool for writing data to PM workspace modules."""

    name = "pm_write_module"
    description = "Write data to any PM workspace module"

    def __init__(self):
        self.pending_confirmations = {}

    async def execute(
        self,
        session_id: str,
        module_type: str,
        data: dict,
        requires_confirmation: bool = True,
    ) -> dict:
        """Write data to a PM workspace module."""
        # Get session binding
        binding = await SessionBindings.get_active_binding_by_session(session_id)
        if not binding:
            return {
                "success": False,
                "error": "Session not bound to any workspace",
            }

        workspace_id = binding.workspace_id

        # Check if confirmation is required
        if requires_confirmation:
            # Store pending confirmation
            confirmation_id = f"{session_id}-{module_type}-{hash(str(data))}"
            self.pending_confirmations[confirmation_id] = {
                "workspace_id": workspace_id,
                "module_type": module_type,
                "data": data,
            }
            return {
                "success": False,
                "requires_confirmation": True,
                "confirmation_id": confirmation_id,
                "message": "This operation requires human confirmation",
            }

        # TODO: Implement actual module data writing
        return {
            "success": True,
            "workspace_id": workspace_id,
            "module_type": module_type,
        }

    async def confirm_write(self, confirmation_id: str) -> dict:
        """Confirm a pending write operation."""
        if confirmation_id not in self.pending_confirmations:
            return {
                "success": False,
                "error": "Confirmation not found or expired",
            }

        confirmation = self.pending_confirmations.pop(confirmation_id)

        # TODO: Implement actual module data writing
        return {
            "success": True,
            "workspace_id": confirmation["workspace_id"],
            "module_type": confirmation["module_type"],
        }


class PMGenerateTestCasesSkill:
    """Skill for generating test cases from requirements."""

    id = "pm-generate-test-cases"
    name = "Generate Test Cases"
    description = "Generate test cases from requirements"
    icon = "test"

    @property
    def system_prompt(self) -> str:
        return """You are a test case generation expert.
Given requirements, generate comprehensive test cases covering:
- Functional tests
- Edge cases
- Boundary conditions
- Error handling

Format each test case with:
- ID
- Description
- Preconditions
- Steps
- Expected results
"""

    def build_user_message(self, requirements: str) -> str:
        return f"Generate test cases for the following requirements:\n\n{requirements}"


class PMExtractParametersSkill:
    """Skill for extracting parameters from PRD."""

    id = "pm-extract-parameters"
    name = "Extract Parameters"
    description = "Extract parameters from PRD"
    icon = "parameter"

    @property
    def system_prompt(self) -> str:
        return """You are a parameter extraction expert.
Given a PRD document, extract all configurable parameters including:
- System parameters
- User preferences
- Feature flags
- Thresholds and limits

Format each parameter with:
- Name
- Type
- Default value
- Description
- Constraints
"""

    def build_user_message(self, prd_content: str) -> str:
        return f"Extract parameters from the following PRD:\n\n{prd_content}"
