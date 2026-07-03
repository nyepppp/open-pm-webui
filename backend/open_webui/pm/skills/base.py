"""Base class for PM Agent Skills."""
from typing import Any, Optional


class BaseSkill:
    """Base class for all PM Agent skills."""

    id: str = "general"
    name: str = "通用对话"
    description: str = "通用 PM 工作对话"
    icon: str = "chat"

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for this skill."""
        return "你是产品经理的 AI 助手。"

    def build_user_message(
        self,
        user_message: str,
        project_id: str,
        module_type: Optional[str] = None,
        entry_id: Optional[str] = None,
        entry_title: Optional[str] = None,
        entry_content_summary: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> str:
        """Build the user message with context injected."""
        parts = [f"项目ID: {project_id}"]
        if module_type:
            parts.append(f"模块: {module_type}")
        if entry_title:
            parts.append(f"当前条目: {entry_title}")
        if entry_content_summary:
            parts.append(f"内容摘要: {entry_content_summary[:500]}")
        if extra_data:
            import json
            parts.append(f"附加数据: {json.dumps(extra_data, ensure_ascii=False)}")
        parts.append(f"\n{user_message}")
        return "\n".join(parts)

    def parse_response(self, llm_response: str) -> dict:
        """Parse LLM response into structured result with actions."""
        import re
        actions = []
        action_pattern = r'```action\s*\n(.*?)\n```'
        for match in re.finditer(action_pattern, llm_response, re.DOTALL):
            try:
                import json
                action_data = json.loads(match.group(1))
                actions.append({
                    'id': f'action-{len(actions)}',
                    'type': action_data.get('type', 'pm.entry.create'),
                    'label': action_data.get('label', ''),
                    'description': action_data.get('description', ''),
                    'payload': action_data.get('payload', {}),
                    'status': 'pending',
                })
            except Exception:
                pass
        clean_response = re.sub(action_pattern, '', llm_response, flags=re.DOTALL).strip()
        return {
            'message': clean_response,
            'actions': actions if actions else None,
            'skillId': self.id,
        }

    def fallback_response(self) -> str:
        """Return a fallback response when LLM is unavailable."""
        return f"我可以帮你进行{self.name}。请提供更多信息，我会给出详细分析。"
