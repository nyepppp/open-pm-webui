"""Skill relevance scorer for autonomous loading."""

from typing import Any, Optional

from open_webui.pm.services.context_analyzer import context_analyzer


class SkillRelevanceScorer:
    """Score skill relevance based on conversation context."""

    def __init__(self):
        pass

    async def score(
        self, message: str, skill_id: str
    ) -> float:
        """Score relevance of a skill to a message.

        Args:
            message: User message
            skill_id: Skill ID

        Returns:
            Relevance score (0.0 - 1.0)
        """
        # Get relevant skills from context analyzer
        relevant_skills = await context_analyzer.analyze(message)

        # Find score for specific skill
        for skill in relevant_skills:
            if skill["skill_id"] == skill_id:
                return min(skill["score"] / 3.0, 1.0)  # Normalize to 0-1

        return 0.0

    async def get_top_skills(
        self, message: str, limit: int = 3
    ) -> list[dict[str, Any]]:
        """Get top relevant skills for a message.

        Args:
            message: User message
            limit: Maximum number of skills to return

        Returns:
            List of top skills with scores
        """
        relevant_skills = await context_analyzer.analyze(message)
        return relevant_skills[:limit]


# Singleton instance
skill_relevance_scorer = SkillRelevanceScorer()
