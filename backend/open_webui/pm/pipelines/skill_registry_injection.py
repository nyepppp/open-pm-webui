"""Skill registry injection for Open WebUI pipelines."""

from typing import Any, Optional

from open_webui.pm.skills.pm_skills_loader import list_skills


class SkillRegistryInjection:
    """Inject skill registry summary into Open WebUI pipelines."""

    def __init__(self):
        pass

    async def get_registry_summary(self) -> list[dict[str, Any]]:
        """Get summary of all registered skills for pipeline injection.

        Returns:
            List of skill summaries
        """
        skills = list_skills()
        return [
            {
                "id": skill["id"],
                "name": skill["name"],
                "description": skill["description"],
                "plugin": skill["plugin"],
            }
            for skill in skills
        ]

    async def inject_into_pipeline(self, pipeline_context: dict) -> dict:
        """Inject skill registry into pipeline context.

        Args:
            pipeline_context: Current pipeline context

        Returns:
            Updated pipeline context with skill registry
        """
        skills = await self.get_registry_summary()
        pipeline_context["pm_skills_registry"] = skills
        return pipeline_context


# Singleton instance
skill_registry_injection = SkillRegistryInjection()
