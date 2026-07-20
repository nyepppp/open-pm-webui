"""PmSkillsAgent - Agent integration for pm-skills invocation."""

from typing import Any, Optional

from open_webui.pm.skills.pm_skills_loader import load_skill
from open_webui.pm.workflows.discover_workflow import DiscoverWorkflow
from open_webui.pm.workflows.write_prd_workflow import WritePRDWorkflow


class PmSkillsAgent:
    """Agent for invoking pm-skills via Timbal Workflows."""

    def __init__(self):
        self.discover_workflow = DiscoverWorkflow()
        self.write_prd_workflow = WritePRDWorkflow()

    async def discover(self, idea: str) -> dict[str, Any]:
        """Run discovery workflow on a product idea.

        Args:
            idea: Product idea to discover

        Returns:
            Discovery results with ideas, assumptions, prioritized, and experiments
        """
        return await self.discover_workflow.run(idea=idea)

    async def write_prd(
        self, feature_idea: str, problem_statement: Optional[str] = None
    ) -> dict[str, Any]:
        """Generate PRD for a feature idea.

        Args:
            feature_idea: Feature idea or problem statement
            problem_statement: Optional detailed problem statement

        Returns:
            PRD generation results
        """
        return await self.write_prd_workflow.run(
            feature_idea=feature_idea,
            problem_statement=problem_statement or feature_idea,
        )

    async def invoke_skill(
        self, skill_id: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Invoke a specific pm-skill.

        Args:
            skill_id: Skill ID in format "pm-skills/<plugin>/<skill>"
            **kwargs: Skill input parameters

        Returns:
            Skill execution results
        """
        skill = load_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")

        return {
            "skill_id": skill_id,
            "skill_name": skill.get("name", ""),
            "description": skill.get("description", ""),
            "content": skill.get("content", ""),
            "inputs": kwargs,
        }


# Singleton instance
pm_skills_agent = PmSkillsAgent()
