"""Context analyzer for autonomous pm-skills loading."""

from typing import Any, Optional

from open_webui.pm.skills.pm_skills_loader import list_skills


class ContextAnalyzer:
    """Analyze conversation context to determine which pm-skills are relevant."""

    def __init__(self):
        # Keyword mappings for skill relevance
        self.skill_keywords = {
            # Product Discovery
            "pm-skills/pm-product-discovery/brainstorm-ideas-existing": [
                "brainstorm", "ideation", "ideas", "generate ideas", "product ideas"
            ],
            "pm-skills/pm-product-discovery/identify-assumptions-existing": [
                "assumptions", "risky assumptions", "identify assumptions", "risks"
            ],
            "pm-skills/pm-product-discovery/prioritize-assumptions": [
                "prioritize", "prioritization", "impact", "risk matrix"
            ],
            "pm-skills/pm-product-discovery/brainstorm-experiments-existing": [
                "experiments", "pretotypes", "test assumptions", "experiments"
            ],
            "pm-skills/pm-product-discovery/interview-script": [
                "interview", "customer interview", "JTBD", "user research"
            ],
            "pm-skills/pm-product-discovery/metrics-dashboard": [
                "metrics", "dashboard", "north star", "KPIs", "measure"
            ],
            "pm-skills/pm-product-discovery/opportunity-solution-tree": [
                "opportunity", "solution tree", "OST", "opportunity solution"
            ],
            "pm-skills/pm-product-discovery/analyze-feature-requests": [
                "feature requests", "analyze features", "categorize requests"
            ],

            # Product Strategy
            "pm-skills/pm-product-strategy/product-strategy": [
                "strategy", "product strategy", "vision", "strategic"
            ],
            "pm-skills/pm-product-strategy/business-model": [
                "business model", "BMC", "revenue model", "monetization"
            ],
            "pm-skills/pm-product-strategy/value-proposition": [
                "value proposition", "JTBD", "value", "proposition"
            ],
            "pm-skills/pm-product-strategy/pricing-strategy": [
                "pricing", "price", "pricing model", "willingness to pay"
            ],
            "pm-skills/pm-product-strategy/swot-analysis": [
                "SWOT", "strengths", "weaknesses", "opportunities", "threats"
            ],

            # Execution
            "pm-skills/pm-execution/create-prd": [
                "PRD", "product requirements", "requirements document", "spec"
            ],
            "pm-skills/pm-execution/brainstorm-okrs": [
                "OKRs", "objectives", "key results", "goals"
            ],
            "pm-skills/pm-execution/sprint-plan": [
                "sprint", "planning", "sprint plan", "capacity"
            ],
            "pm-skills/pm-execution/user-stories": [
                "user stories", "stories", "acceptance criteria", "INVEST"
            ],
            "pm-skills/pm-execution/test-scenarios": [
                "test scenarios", "test cases", "happy path", "edge cases"
            ],
            "pm-skills/pm-execution/pre-mortem": [
                "pre-mortem", "risk analysis", "tigers", "paper tigers"
            ],
            "pm-skills/pm-execution/strategy-red-team": [
                "red team", "stress test", "adversarial", "challenge assumptions"
            ],

            # Market Research
            "pm-skills/pm-market-research/user-personas": [
                "personas", "user personas", "archetypes", "segments"
            ],
            "pm-skills/pm-market-research/competitor-analysis": [
                "competitors", "competitive analysis", "landscape", "rivals"
            ],
            "pm-skills/pm-market-research/customer-journey-map": [
                "journey map", "customer journey", "touchpoints", "experience"
            ],

            # Data Analytics
            "pm-skills/pm-data-analytics/sql-queries": [
                "SQL", "query", "database", "analytics query"
            ],
            "pm-skills/pm-data-analytics/cohort-analysis": [
                "cohort", "retention", "engagement", "adoption"
            ],
            "pm-skills/pm-data-analytics/ab-test-analysis": [
                "A/B test", "experiment", "statistical significance", "hypothesis"
            ],

            # Go-to-Market
            "pm-skills/pm-go-to-market/gtm-strategy": [
                "go-to-market", "GTM", "launch strategy", "market entry"
            ],
            "pm-skills/pm-go-to-market/growth-loops": [
                "growth loops", "flywheel", "viral", "referral"
            ],

            # Marketing Growth
            "pm-skills/pm-marketing-growth/marketing-ideas": [
                "marketing", "campaign", "promotion", "growth marketing"
            ],
            "pm-skills/pm-marketing-growth/north-star-metric": [
                "north star", "metric", "KPI", "measure success"
            ],
        }

    async def analyze(self, message: str) -> list[dict[str, Any]]:
        """Analyze message and return relevant skills.

        Args:
            message: User message

        Returns:
            List of relevant skills with scores
        """
        message_lower = message.lower()
        scores = {}

        for skill_id, keywords in self.skill_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    score += 1
            if score > 0:
                scores[skill_id] = score

        # Sort by score
        sorted_skills = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {"skill_id": skill_id, "score": score}
            for skill_id, score in sorted_skills[:5]  # Top 5
        ]


# Singleton instance
context_analyzer = ContextAnalyzer()
