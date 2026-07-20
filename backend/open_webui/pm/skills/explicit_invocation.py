"""Explicit invocation handler for pm-skills."""

from typing import Any, Optional

from open_webui.pm.services.command_resolver import command_resolver
from open_webui.pm.skills.pm_skills_loader import load_skill


class ExplicitInvocationHandler:
    """Handle explicit /pm-<id> command invocations."""

    def __init__(self):
        pass

    async def handle(self, command_id: str, args: Optional[dict] = None) -> dict[str, Any]:
        """Handle explicit command invocation.

        Args:
            command_id: Command ID (e.g., "write-prd")
            args: Optional command arguments

        Returns:
            Invocation result
        """
        # Resolve command to skill
        skill = await command_resolver.resolve(command_id)
        if not skill:
            return {
                "status": "error",
                "error": f"Command not found: {command_id}",
            }

        # Return skill metadata
        return {
            "status": "success",
            "command_id": command_id,
            "skill_id": skill.get("id"),
            "skill_name": skill.get("name"),
            "description": skill.get("description"),
            "content": skill.get("content"),
            "args": args or {},
        }

    async def list_commands(self) -> list[str]:
        """List all available commands.

        Returns:
            List of command IDs
        """
        return await command_resolver.list_commands()


# Singleton instance
explicit_invocation_handler = ExplicitInvocationHandler()
