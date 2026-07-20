"""Workflow Template Recommendation Service

Recommends workflow templates based on user input and project context.
"""

from typing import Optional

from open_webui.internal.db import get_async_db_context


class WorkflowTemplateRecommender:
    """Service for recommending workflow templates."""

    def __init__(self):
        self.templates = {
            "content-moderation-pipeline": {
                "name": "Content Moderation Pipeline",
                "description": "Automated content moderation with AI analysis",
                "category": "content",
                "tags": ["moderation", "ai", "content"],
            },
            "data-pipeline": {
                "name": "Data Processing Pipeline",
                "description": "Extract, transform, and load data",
                "category": "data",
                "tags": ["data", "etl", "processing"],
            },
            "agent-workflow": {
                "name": "Agent Workflow",
                "description": "Multi-agent collaboration workflow",
                "category": "agent",
                "tags": ["agent", "collaboration", "ai"],
            },
            "llm-pipeline": {
                "name": "LLM Pipeline",
                "description": "LLM-powered text processing pipeline",
                "category": "llm",
                "tags": ["llm", "text", "ai"],
            },
            "review-pipeline": {
                "name": "Code Review Pipeline",
                "description": "Automated code review and analysis",
                "category": "dev",
                "tags": ["review", "code", "analysis"],
            },
            "test-pipeline": {
                "name": "Test Automation Pipeline",
                "description": "Automated testing and validation",
                "category": "dev",
                "tags": ["test", "automation", "validation"],
            },
        }

    async def recommend(
        self,
        description: str,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list:
        """Recommend workflow templates based on description.

        Args:
            description: Natural language description
            project_id: Optional project ID
            user_id: Optional user ID

        Returns:
            List of recommended templates
        """
        recommendations = []
        description_lower = description.lower()

        # Keyword matching
        for template_id, template in self.templates.items():
            score = 0

            # Check name match
            if any(word in description_lower for word in template["name"].lower().split()):
                score += 2

            # Check description match
            if any(word in description_lower for word in template["description"].lower().split()):
                score += 1

            # Check tag match
            for tag in template["tags"]:
                if tag in description_lower:
                    score += 1

            if score > 0:
                recommendations.append({
                    "id": template_id,
                    "name": template["name"],
                    "description": template["description"],
                    "category": template["category"],
                    "score": score,
                })

        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return recommendations

    async def get_template(self, template_id: str) -> Optional[dict]:
        """Get a specific template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template data or None
        """
        return self.templates.get(template_id)

    async def get_all_templates(self) -> list:
        """Get all available templates.

        Returns:
            List of all templates
        """
        return [
            {
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
                "category": template["category"],
                "tags": template["tags"],
            }
            for template_id, template in self.templates.items()
        ]


# Singleton instance
WorkflowTemplateRecommender = WorkflowTemplateRecommender()
