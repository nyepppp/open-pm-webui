"""Autonomous skill loader for Agent."""

from typing import Any, Optional

from open_webui.pm.services.context_analyzer import context_analyzer
from open_webui.pm.services.skill_relevance import skill_relevance_scorer
from open_webui.pm.skills.pm_skills_loader import load_skill


class AutonomousSkillLoader:
    """Autonomously load relevant pm-skills based on conversation context."""

    def __init__(self):
        pass

    async def load_relevant_skills(
        self, message: str, limit: int = 3
    ) -> list[dict[str, Any]]:
        """Load relevant skills based on message context.

        Args:
            message: User message
            limit: Maximum number of skills to load

        Returns:
            List of loaded skills with metadata
        """
        # Get top relevant skills
        top_skills = await skill_relevance_scorer.get_top_skills(message, limit)

        # Load each skill
        loaded = []
        for skill_info in top_skills:
            skill_id = skill_info["skill_id"]
            skill = load_skill(skill_id)
            if skill:
                loaded.append(
                    {
                        "skill_id": skill_id,
                        "score": skill_info["score"],
                        "name": skill.get("name", ""),
                        "description": skill.get("description", ""),
                        "content": skill.get("content", ""),
                    }
                )

        return loaded

    async def should_load_skills(self, message: str) -> bool:
        """Determine if skills should be loaded for this message.

        Args:
            message: User message

        Returns:
            True if skills should be loaded
        """
        # Check if message contains PM-related keywords
        pm_keywords = [
            "product", "strategy", "roadmap", "requirements", "PRD",
            "user story", "acceptance criteria", "sprint", "backlog",
            "prioritize", "discovery", "assumptions", "experiments",
            "metrics", "KPI", "north star", "goals", "OKRs",
            "competitors", "market", "personas", "journey",
            "launch", "GTM", "growth", "marketing",
            "interview", "research", "feedback", "analysis",
        ]

        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in pm_keywords)


# Singleton instance
autonomous_skill_loader = AutonomousSkillLoader()
