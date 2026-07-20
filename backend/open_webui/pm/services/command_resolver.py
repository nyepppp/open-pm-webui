"""Command resolution service for pm-skills."""

from typing import Optional

from open_webui.pm.skills.pm_skills_loader import load_skill


class CommandResolver:
    """Resolve /pm-<id> commands to pm-skills."""

    def __init__(self):
        pass

    async def resolve(self, command_id: str) -> Optional[dict]:
        """Resolve command_id to skill metadata.

        Args:
            command_id: Command ID (e.g., "write-prd")

        Returns:
            Skill metadata or None
        """
        # Map command_id to skill_id
        command_to_skill = {
            # Product Discovery
            "discover": "pm-skills/pm-product-discovery/brainstorm-ideas-existing",
            "brainstorm": "pm-skills/pm-product-discovery/brainstorm-ideas-existing",
            "interview": "pm-skills/pm-product-discovery/interview-script",
            "triage-requests": "pm-skills/pm-product-discovery/analyze-feature-requests",
            "setup-metrics": "pm-skills/pm-product-discovery/metrics-dashboard",

            # Product Strategy
            "strategy": "pm-skills/pm-product-strategy/product-strategy",
            "business-model": "pm-skills/pm-product-strategy/business-model",
            "value-proposition": "pm-skills/pm-product-strategy/value-proposition",
            "market-scan": "pm-skills/pm-product-strategy/swot-analysis",
            "pricing": "pm-skills/pm-product-strategy/pricing-strategy",

            # Execution
            "write-prd": "pm-skills/pm-execution/create-prd",
            "plan-okrs": "pm-skills/pm-execution/brainstorm-okrs",
            "transform-roadmap": "pm-skills/pm-execution/outcome-roadmap",
            "sprint": "pm-skills/pm-execution/sprint-plan",
            "pre-mortem": "pm-skills/pm-execution/pre-mortem",
            "red-team-prd": "pm-skills/pm-execution/strategy-red-team",
            "meeting-notes": "pm-skills/pm-execution/summarize-meeting",
            "stakeholder-map": "pm-skills/pm-execution/stakeholder-map",
            "write-stories": "pm-skills/pm-execution/user-stories",
            "test-scenarios": "pm-skills/pm-execution/test-scenarios",
            "generate-data": "pm-skills/pm-execution/dummy-dataset",

            # Market Research
            "research-users": "pm-skills/pm-market-research/user-personas",
            "competitive-analysis": "pm-skills/pm-market-research/competitor-analysis",
            "analyze-feedback": "pm-skills/pm-market-research/sentiment-analysis",

            # Data Analytics
            "write-query": "pm-skills/pm-data-analytics/sql-queries",
            "analyze-cohorts": "pm-skills/pm-data-analytics/cohort-analysis",
            "analyze-test": "pm-skills/pm-data-analytics/ab-test-analysis",

            # Go-to-Market
            "plan-launch": "pm-skills/pm-go-to-market/gtm-strategy",
            "growth-strategy": "pm-skills/pm-go-to-market/growth-loops",
            "battlecard": "pm-skills/pm-go-to-market/competitive-battlecard",

            # Marketing Growth
            "market-product": "pm-skills/pm-marketing-growth/marketing-ideas",
            "north-star": "pm-skills/pm-marketing-growth/north-star-metric",

            # Toolkit
            "review-resume": "pm-skills/pm-toolkit/review-resume",
            "tailor-resume": "pm-skills/pm-toolkit/review-resume",
            "draft-nda": "pm-skills/pm-toolkit/draft-nda",
            "privacy-policy": "pm-skills/pm-toolkit/privacy-policy",
            "proofread": "pm-skills/pm-toolkit/grammar-check",

            # AI Shipping
            "ship-check": "pm-skills/pm-ai-shipping/shipping-artifacts",
            "document-app": "pm-skills/pm-ai-shipping/shipping-artifacts",
            "derive-tests": "pm-skills/pm-ai-shipping/intended-vs-implemented",
            "security-audit-static": "pm-skills/pm-ai-shipping/intended-vs-implemented",
            "performance-audit-static": "pm-skills/pm-ai-shipping/intended-vs-implemented",
        }

        skill_id = command_to_skill.get(command_id)
        if skill_id:
            return load_skill(skill_id)

        return None

    async def list_commands(self) -> list[str]:
        """List all available commands.

        Returns:
            List of command IDs
        """
        return [
            # Product Discovery
            "discover",
            "brainstorm",
            "interview",
            "triage-requests",
            "setup-metrics",

            # Product Strategy
            "strategy",
            "business-model",
            "value-proposition",
            "market-scan",
            "pricing",

            # Execution
            "write-prd",
            "plan-okrs",
            "transform-roadmap",
            "sprint",
            "pre-mortem",
            "red-team-prd",
            "meeting-notes",
            "stakeholder-map",
            "write-stories",
            "test-scenarios",
            "generate-data",

            # Market Research
            "research-users",
            "competitive-analysis",
            "analyze-feedback",

            # Data Analytics
            "write-query",
            "analyze-cohorts",
            "analyze-test",

            # Go-to-Market
            "plan-launch",
            "growth-strategy",
            "battlecard",

            # Marketing Growth
            "market-product",
            "north-star",

            # Toolkit
            "review-resume",
            "tailor-resume",
            "draft-nda",
            "privacy-policy",
            "proofread",

            # AI Shipping
            "ship-check",
            "document-app",
            "derive-tests",
            "security-audit-static",
            "performance-audit-static",
        ]


# Singleton instance
command_resolver = CommandResolver()
