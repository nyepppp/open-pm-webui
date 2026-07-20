"""LLM and AI node executors."""

import os
from typing import Any, Dict

import openai

from .base import BaseNodeExecutor
from ..state import ExecutionState, NodeResult, NodeStatus


class LLMNodeExecutor(BaseNodeExecutor):
    """Executor for LLM nodes."""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = openai.AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            model = node_config.get('model', 'gpt-4')
            temperature = node_config.get('temperature', 0.7)
            max_tokens = node_config.get('max_tokens', 2048)
            prompt_template = node_config.get('prompt', '')
            
            # Resolve variables in prompt
            prompt = self._resolve_variables(prompt_template, state)
            
            # Call LLM
            if self.client is None:
                return NodeResult(
                    status=NodeStatus.FAILED,
                    error="OpenAI API key not configured"
                )
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={
                    'text': response.choices[0].message.content,
                    'model': model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                        'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                        'total_tokens': response.usage.total_tokens if response.usage else 0
                    }
                }
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
    
    def _resolve_variables(self, template: str, state: ExecutionState) -> str:
        """Resolve variables: {{var}} from flat dict, {{node_id.field}} from node_results.

        Supports:
        - {{var}} — flat variable from state.variables (backward compatible)
        - {{node_id.field}} — upstream node output from state.node_results
        - {{node_id.field.subfield}} — nested field access
        - {{$input}} — workflow input parameter
        """
        import re

        def replace_match(match):
            expr = match.group(1).strip()
            # {{$input}} — workflow input parameter
            if expr == '$input':
                value = state.variables.get('input') or state.variables.get('$input')
                return str(value) if value is not None else match.group(0)
            # {{node_id.field}} or {{node_id.field.subfield}} — upstream node output
            if '.' in expr:
                parts = expr.split('.', 1)
                node_id, field = parts[0], parts[1]
                node_result = state.node_results.get(node_id)
                if node_result and node_result.output:
                    # Navigate nested fields (e.g., metadata.tokens)
                    current = node_result.output
                    for sub in field.split('.'):
                        if isinstance(current, dict) and sub in current:
                            current = current[sub]
                        else:
                            current = None
                            break
                    if current is not None:
                        return str(current)
                return match.group(0)  # Not found — keep placeholder for debugging
            # {{var}} — flat variable (backward compatible)
            value = state.variables.get(expr)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace_match, template)


class PromptTemplateNodeExecutor(BaseNodeExecutor):
    """Executor for prompt template nodes."""
    
    async def execute(self, node_config: Dict[str, Any], state: ExecutionState) -> NodeResult:
        try:
            template = node_config.get('template', '')
            resolved = self._resolve_variables(template, state)
            
            return NodeResult(
                status=NodeStatus.COMPLETED,
                output={'prompt': resolved}
            )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )
    
    def _resolve_variables(self, template: str, state: ExecutionState) -> str:
        """Resolve variables: {{var}} from flat dict, {{node_id.field}} from node_results.

        Supports:
        - {{var}} — flat variable from state.variables (backward compatible)
        - {{node_id.field}} — upstream node output from state.node_results
        - {{node_id.field.subfield}} — nested field access
        - {{$input}} — workflow input parameter
        """
        import re

        def replace_match(match):
            expr = match.group(1).strip()
            # {{$input}} — workflow input parameter
            if expr == '$input':
                value = state.variables.get('input') or state.variables.get('$input')
                return str(value) if value is not None else match.group(0)
            # {{node_id.field}} or {{node_id.field.subfield}} — upstream node output
            if '.' in expr:
                parts = expr.split('.', 1)
                node_id, field = parts[0], parts[1]
                node_result = state.node_results.get(node_id)
                if node_result and node_result.output:
                    # Navigate nested fields (e.g., metadata.tokens)
                    current = node_result.output
                    for sub in field.split('.'):
                        if isinstance(current, dict) and sub in current:
                            current = current[sub]
                        else:
                            current = None
                            break
                    if current is not None:
                        return str(current)
                return match.group(0)  # Not found — keep placeholder for debugging
            # {{var}} — flat variable (backward compatible)
            value = state.variables.get(expr)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace_match, template)
