"""Agent runtime with ReAct pattern."""

import json
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import openai

from .memory import MemoryStore
from .tools import ToolRegistry, ToolResult


class ThoughtStep:
    """Single step in ReAct loop."""
    
    def __init__(self, observation: str, reasoning: str, action: str, action_input: Optional[Dict] = None):
        self.observation = observation
        self.reasoning = reasoning
        self.action = action
        self.action_input = action_input or {}


class AgentRun:
    """Agent execution run."""
    
    def __init__(self, session_id: UUID, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.thought_process: List[ThoughtStep] = []
        self.tool_calls: List[Dict] = []
        self.assistant_message: Optional[str] = None
        self.token_usage: Dict[str, int] = {}
        self.duration_ms: int = 0


class AgentRuntime:
    """ReAct-based agent runtime."""
    
    def __init__(self, llm_config: Dict[str, Any], tool_registry: ToolRegistry, memory_store: MemoryStore):
        self.llm_config = llm_config
        self.tool_registry = tool_registry
        self.memory_store = memory_store
        api_key = llm_config.get('api_key') or openai.api_key
        if api_key:
            self.client = openai.AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
    
    async def run(self, session_id: UUID, user_message: str, max_steps: int = 10, pm_context: Optional[Dict[str, Any]] = None) -> AgentRun:
        """Run agent with user input."""
        start_time = time.time()
        run = AgentRun(session_id=session_id, user_message=user_message)
        
        # Retrieve relevant memories
        memories = await self.memory_store.retrieve(query=user_message)
        memory_context = "\n".join([f"- {m.content}" for m in memories])
        
        # Build system prompt with PM context
        system_prompt = self._build_system_prompt(pm_context)
        
        # ReAct loop
        for step in range(max_steps):
            # Build prompt with history
            prompt = self._build_react_prompt(
                user_message=user_message,
                memory_context=memory_context,
                previous_steps=run.thought_process,
                pm_context=pm_context
            )
            
            # Call LLM
            if self.client is None:
                run.assistant_message = "LLM client not configured"
                break
            
            response = await self.client.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.get('temperature', 0.7)
            )
            
            content = response.choices[0].message.content or ""
            
            # Parse thought
            thought = self._parse_thought(content)
            run.thought_process.append(thought)
            
            # Update token usage
            if response.usage:
                run.token_usage['prompt_tokens'] = run.token_usage.get('prompt_tokens', 0) + response.usage.prompt_tokens
                run.token_usage['completion_tokens'] = run.token_usage.get('completion_tokens', 0) + response.usage.completion_tokens
            
            # Execute action
            if thought.action == 'respond':
                run.assistant_message = thought.action_input.get('message', '')
                break
            elif thought.action == 'use_tool':
                tool_name = thought.action_input.get('tool', '')
                if tool_name:
                    tool_params = thought.action_input.get('params', {})
                    
                    # Inject PM context into tool params if available
                    if pm_context:
                        for key, value in pm_context.items():
                            if key not in tool_params:
                                tool_params[key] = value
                    
                    result = await self.tool_registry.execute(tool_name, **tool_params)
                    run.tool_calls.append({
                        'tool': tool_name,
                        'params': tool_params,
                        'result': result.output if result.success else result.error
                    })
            elif thought.action == 'plan':
                pass
        
        # Store memory
        if run.assistant_message:
            await self.memory_store.store(
                content=f"User: {user_message}\nAssistant: {run.assistant_message}",
                memory_type='short_term'
            )
        
        run.duration_ms = int((time.time() - start_time) * 1000)
        return run
    
    def _build_system_prompt(self, pm_context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt for agent."""
        tools = self.tool_registry.list_tools()
        tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
        
        pm_context_str = ""
        if pm_context:
            pm_lines = [f"- {key}: {value}" for key, value in pm_context.items()]
            pm_context_str = "\n".join(pm_lines)
            pm_context_str = f"\n\nCurrent project context:\n{pm_context_str}\n"
        
        return f"""You are an AI assistant that can use tools to help users.{pm_context_str}

Available tools:
{tools_desc}

You must respond in the following format:
Observation: <what you observe>
Thought: <your reasoning>
Action: <respond|use_tool|plan>
Action Input: <JSON object with action parameters>

For respond action:
Action Input: {{"message": "your response"}}

For use_tool action:
Action Input: {{"tool": "tool_name", "params": {{"param1": "value1"}}}}

For plan action:
Action Input: {{"plan": ["step1", "step2"]}}
"""
    
    def _build_react_prompt(self, user_message: str, memory_context: str, previous_steps: List[ThoughtStep], pm_context: Optional[Dict[str, Any]] = None) -> str:
        """Build ReAct prompt."""
        history = ""
        for step in previous_steps:
            history += f"Observation: {step.observation}\n"
            history += f"Thought: {step.reasoning}\n"
            history += f"Action: {step.action}\n"
            history += f"Action Input: {json.dumps(step.action_input)}\n\n"
        
        pm_section = ""
        if pm_context:
            pm_section = "\nProject context:\n"
            for key, value in pm_context.items():
                pm_section += f"- {key}: {value}\n"
        
        return f"""Previous memories:
{memory_context}
{pm_section}
{history}
User: {user_message}

What is your next thought and action?"""
    
    def _parse_thought(self, content: str) -> ThoughtStep:
        """Parse LLM response into thought step."""
        lines = content.split('\n')
        observation = ''
        reasoning = ''
        action = 'respond'
        action_input = {}
        
        for line in lines:
            if line.startswith('Observation:'):
                observation = line.replace('Observation:', '').strip()
            elif line.startswith('Thought:'):
                reasoning = line.replace('Thought:', '').strip()
            elif line.startswith('Action:'):
                action = line.replace('Action:', '').strip()
            elif line.startswith('Action Input:'):
                try:
                    action_input = json.loads(line.replace('Action Input:', '').strip())
                except:
                    pass
        
        return ThoughtStep(
            observation=observation,
            reasoning=reasoning,
            action=action,
            action_input=action_input
        )
