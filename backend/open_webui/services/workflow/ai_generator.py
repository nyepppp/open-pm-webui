"""AI Workflow Generation Service

Generates workflow definitions from natural language descriptions using LLM.
"""

import json
import logging
import re
import uuid
from typing import Awaitable, Callable, Optional

from open_webui.internal.db import get_async_db_context
from open_webui.pm.models.workflow import (
    Workflow,
    WorkflowForm,
    WorkflowNode,
    WorkflowEdge,
    WorkflowNodeForm,
    WorkflowEdgeForm,
    Workflows,
    WorkflowNodes,
    WorkflowEdges,
)

log = logging.getLogger(__name__)


# 允许的节点类型（与前端 src/lib/components/workflow-v2/types.ts 的 NodeType 联合类型保持一致，
# 共 16 种基础类型；spec 中提到的"16 个 PM 模板类型"已包含 pm_module）。
ALLOWED_NODE_TYPES = {
    "start",
    "end",
    "condition",
    "variable_set",
    "loop",
    "llm",
    "agent",
    "knowledge_retrieval",
    "template",
    "parameter_extractor",
    "http_request",
    "code",
    "tool_call",
    "answer",
    "pm_module",
    "human_input",
}


# Workflow templates for common patterns
# 模板中的节点类型与 ALLOWED_NODE_TYPES 对齐（旧模板里的 llm_call/agent_call/data_transform/parallel/merge/webhook/custom
# 仅作为内部示例数据，不会直接进入校验流程）。
WORKFLOW_TEMPLATES = {
    "content_moderation": {
        "name": "Content Moderation Pipeline",
        "description": "Automated content moderation with analysis, scoring, and flagging",
        "nodes": [
            {"type": "start", "name": "Start", "x": 100, "y": 100},
            {"type": "llm", "name": "Analyze Content", "x": 300, "y": 100, "config": {"model": "gpt-4", "temperature": 0.3, "system_prompt": "Analyze the following content for moderation. Rate toxicity, spam, and inappropriate content on a scale of 0-1.", "prompt": "{{input.content}}"}},
            {"type": "condition", "name": "Check Score", "x": 500, "y": 100, "config": {"condition": "input.toxicity_score > 0.7 || input.spam_score > 0.8", "conditions": [], "combinator": "and"}},
            {"type": "code", "name": "Flag Content", "x": 700, "y": 50, "config": {"code": "# flag content", "input_variables": {}, "output_variable": "result"}},
            {"type": "answer", "name": "Approve Content", "x": 700, "y": 150, "config": {"answer": "approved", "output_variable": "answer"}},
            {"type": "end", "name": "End", "x": 900, "y": 100},
        ],
        "edges": [
            {"source": 0, "target": 1, "label": ""},
            {"source": 1, "target": 2, "label": ""},
            {"source": 2, "target": 3, "label": "Flag"},
            {"source": 2, "target": 4, "label": "Approve"},
            {"source": 3, "target": 5, "label": ""},
            {"source": 4, "target": 5, "label": ""},
        ]
    },
    "data_pipeline": {
        "name": "Data Processing Pipeline",
        "description": "Extract, transform, and load data workflow",
        "nodes": [
            {"type": "start", "name": "Start", "x": 100, "y": 100},
            {"type": "code", "name": "Extract Data", "x": 300, "y": 100, "config": {"code": "# extract", "input_variables": {}, "output_variable": "extracted"}},
            {"type": "code", "name": "Validate Data", "x": 500, "y": 100, "config": {"code": "# validate", "input_variables": {}, "output_variable": "validated"}},
            {"type": "llm", "name": "Enrich Data", "x": 700, "y": 100, "config": {"model": "gpt-4", "temperature": 0.5, "system_prompt": "Enrich the following data with additional context and insights.", "prompt": "{{input.data}}"}},
            {"type": "code", "name": "Load Data", "x": 900, "y": 100, "config": {"code": "# load", "input_variables": {}, "output_variable": "loaded"}},
            {"type": "end", "name": "End", "x": 1100, "y": 100},
        ],
        "edges": [
            {"source": 0, "target": 1, "label": ""},
            {"source": 1, "target": 2, "label": ""},
            {"source": 2, "target": 3, "label": ""},
            {"source": 3, "target": 4, "label": ""},
            {"source": 4, "target": 5, "label": ""},
        ]
    },
    "agent_workflow": {
        "name": "Multi-Agent Workflow",
        "description": "Coordinate multiple AI agents to complete a complex task",
        "nodes": [
            {"type": "start", "name": "Start", "x": 100, "y": 100},
            {"type": "agent", "name": "Research Agent", "x": 300, "y": 100, "config": {"agent_id": "research", "instructions": "Research the topic and gather relevant information"}},
            {"type": "agent", "name": "Analysis Agent", "x": 500, "y": 100, "config": {"agent_id": "analysis", "instructions": "Analyze the research findings and identify key insights"}},
            {"type": "agent", "name": "Writing Agent", "x": 700, "y": 100, "config": {"agent_id": "writing", "instructions": "Create a comprehensive report based on the analysis"}},
            {"type": "answer", "name": "Format Output", "x": 900, "y": 100, "config": {"answer": "{{input.response}}", "output_variable": "answer"}},
            {"type": "end", "name": "End", "x": 1100, "y": 100},
        ],
        "edges": [
            {"source": 0, "target": 1, "label": ""},
            {"source": 1, "target": 2, "label": ""},
            {"source": 2, "target": 3, "label": ""},
            {"source": 3, "target": 4, "label": ""},
            {"source": 4, "target": 5, "label": ""},
        ]
    },
    "approval_workflow": {
        "name": "Approval Process",
        "description": "Multi-stage approval with conditional branching",
        "nodes": [
            {"type": "start", "name": "Start", "x": 100, "y": 100},
            {"type": "code", "name": "Submit Request", "x": 300, "y": 100, "config": {"code": "# submit", "input_variables": {}, "output_variable": "request"}},
            {"type": "condition", "name": "Auto-Approve?", "x": 500, "y": 100, "config": {"condition": "input.amount < 1000", "conditions": [], "combinator": "and"}},
            {"type": "agent", "name": "Manager Review", "x": 700, "y": 150, "config": {"agent_id": "manager", "instructions": "Review and approve the request"}},
            {"type": "condition", "name": "Approved?", "x": 900, "y": 150, "config": {"condition": "input.approved", "conditions": [], "combinator": "and"}},
            {"type": "answer", "name": "Process Approval", "x": 1100, "y": 100, "config": {"answer": "approved", "output_variable": "answer"}},
            {"type": "answer", "name": "Reject Request", "x": 1100, "y": 200, "config": {"answer": "rejected", "output_variable": "answer"}},
            {"type": "end", "name": "End", "x": 1300, "y": 100},
        ],
        "edges": [
            {"source": 0, "target": 1, "label": ""},
            {"source": 1, "target": 2, "label": ""},
            {"source": 2, "target": 3, "label": "Manual"},
            {"source": 2, "target": 5, "label": "Auto"},
            {"source": 3, "target": 4, "label": ""},
            {"source": 4, "target": 5, "label": "Yes"},
            {"source": 4, "target": 6, "label": "No"},
            {"source": 5, "target": 7, "label": ""},
            {"source": 6, "target": 7, "label": ""},
        ]
    },
    "parallel_processing": {
        "name": "Parallel Processing",
        "description": "Execute multiple tasks in parallel and merge results",
        "nodes": [
            {"type": "start", "name": "Start", "x": 100, "y": 200},
            {"type": "loop", "name": "Parallel Tasks", "x": 300, "y": 200, "config": {"loop_type": "for_each", "iterator": "tasks", "condition": "", "max_iterations": 1000, "body_node_ids": []}},
            {"type": "llm", "name": "Task A", "x": 500, "y": 100, "config": {"model": "gpt-4", "temperature": 0.7, "system_prompt": "Process task A", "prompt": "{{input.task_a}}"}},
            {"type": "llm", "name": "Task B", "x": 500, "y": 200, "config": {"model": "gpt-4", "temperature": 0.7, "system_prompt": "Process task B", "prompt": "{{input.task_b}}"}},
            {"type": "llm", "name": "Task C", "x": 500, "y": 300, "config": {"model": "gpt-4", "temperature": 0.7, "system_prompt": "Process task C", "prompt": "{{input.task_c}}"}},
            {"type": "variable_set", "name": "Merge Results", "x": 700, "y": 200, "config": {"variable_name": "merged", "variable_value": "{{input.results}}"}},
            {"type": "end", "name": "End", "x": 900, "y": 200},
        ],
        "edges": [
            {"source": 0, "target": 1, "label": ""},
            {"source": 1, "target": 2, "label": ""},
            {"source": 1, "target": 3, "label": ""},
            {"source": 1, "target": 4, "label": ""},
            {"source": 2, "target": 5, "label": ""},
            {"source": 3, "target": 5, "label": ""},
            {"source": 4, "target": 5, "label": ""},
            {"source": 5, "target": 6, "label": ""},
        ]
    },
    "loop_workflow": {
        "name": "Iterative Processing",
        "description": "Process data in a loop until a condition is met",
        "nodes": [
            {"type": "start", "name": "Start", "x": 100, "y": 100},
            {"type": "variable_set", "name": "Initialize", "x": 300, "y": 100, "config": {"variable_name": "state", "variable_value": "init"}},
            {"type": "loop", "name": "Process Loop", "x": 500, "y": 100, "config": {"loop_type": "while", "iterator": "", "condition": "items.length > 0", "max_iterations": 100, "body_node_ids": []}},
            {"type": "llm", "name": "Process Item", "x": 700, "y": 100, "config": {"model": "gpt-4", "temperature": 0.5, "system_prompt": "Process the current item", "prompt": "{{input.item}}"}},
            {"type": "variable_set", "name": "Update State", "x": 700, "y": 200, "config": {"variable_name": "state", "variable_value": "{{input.updated}}"}},
            {"type": "end", "name": "End", "x": 900, "y": 100},
        ],
        "edges": [
            {"source": 0, "target": 1, "label": ""},
            {"source": 1, "target": 2, "label": ""},
            {"source": 2, "target": 3, "label": "loop"},
            {"source": 3, "target": 4, "label": ""},
            {"source": 4, "target": 2, "label": ""},
            {"source": 2, "target": 5, "label": "exit"},
        ]
    },
    "pm_doc_to_architecture": {
        "name": "需求文档转产品架构",
        "description": "从需求文档识别模块、读取已有模块、向用户确认模块列表，再识别功能参数、表单确认并写入产品架构（含 human_input 人工确认环节）",
        "nodes": [
            {"type": "start", "name": "开始", "x": 100, "y": 200, "config": {}},
            {"type": "parameter_extractor", "name": "识别模块", "x": 300, "y": 200, "config": {
                "model": "gpt-4",
                "input_text": "{{input.requirement_doc}}",
                "parameters": [
                    {"name": "modules", "label": "识别到的模块列表", "type": "array", "description": "从需求文档中识别出的模块名称，例如 ['用户管理', '订单管理']"}
                ],
                "output_variable": "identified_modules"
            }},
            {"type": "pm_module", "name": "读取已有模块", "x": 500, "y": 200, "config": {
                "module_type": "architecture",
                "action": "read",
                "project_id": "{{input.project_id}}",
                "filter": {"node_type": "module"},
                "data": {}
            }},
            {"type": "human_input", "name": "确认模块列表", "x": 700, "y": 200, "config": {
                "prompt": "请确认要写入产品架构的模块列表（可增删改）",
                "fields": [
                    {"name": "confirmed_modules", "label": "确认后的模块列表", "type": "textarea", "required": True}
                ],
                "output_variable": "confirmed_modules"
            }},
            {"type": "parameter_extractor", "name": "识别功能参数", "x": 900, "y": 200, "config": {
                "model": "gpt-4",
                "input_text": "{{input.requirement_doc}}",
                "parameters": [
                    {"name": "features", "label": "功能与参数", "type": "array", "description": "每个模块下的功能和参数，例如 [{module:用户管理,feature:登录,parameters:[账号,密码]}]"}
                ],
                "output_variable": "identified_features"
            }},
            {"type": "human_input", "name": "表单确认功能参数", "x": 1100, "y": 200, "config": {
                "prompt": "请确认要写入的功能和参数（可增删改，提交后写入产品架构）",
                "fields": [
                    {"name": "confirmed_features", "label": "确认后的功能参数", "type": "textarea", "required": True}
                ],
                "output_variable": "confirmed_features"
            }},
            {"type": "pm_module", "name": "写入产品架构", "x": 1300, "y": 200, "config": {
                "module_type": "architecture",
                "action": "create",
                "project_id": "{{input.project_id}}",
                "filter": {},
                "data": {
                    "title": "产品架构 - AI 生成",
                    "content": "由 AI 工作流自动写入",
                    "data": {
                        "modules": "{{confirmed_modules}}",
                        "features": "{{confirmed_features}}"
                    },
                    "status": "draft",
                    "priority": "medium"
                }
            }},
            {"type": "end", "name": "结束", "x": 1500, "y": 200, "config": {}}
        ],
        "edges": [
            {"source": 0, "target": 1, "label": ""},
            {"source": 1, "target": 2, "label": ""},
            {"source": 2, "target": 3, "label": ""},
            {"source": 3, "target": 4, "label": ""},
            {"source": 4, "target": 5, "label": ""},
            {"source": 5, "target": 6, "label": ""},
            {"source": 6, "target": 7, "label": ""}
        ]
    }
}


class AIWorkflowGenerator:
    """Service for generating workflows from natural language descriptions."""

    def __init__(self):
        # 节点类型元信息（仅用于展示与默认配置生成，校验由 ALLOWED_NODE_TYPES 把关）
        self.node_types = {
            "start": {"label": "Start", "color": "#22c55e"},
            "end": {"label": "End", "color": "#ef4444"},
            "condition": {"label": "Condition", "color": "#f59e0b"},
            "variable_set": {"label": "Set Variable", "color": "#8b5cf6"},
            "loop": {"label": "Loop", "color": "#0ea5e9"},
            "llm": {"label": "LLM", "color": "#3b82f6"},
            "agent": {"label": "Agent", "color": "#ec4899"},
            "knowledge_retrieval": {"label": "Knowledge Retrieval", "color": "#14b8a6"},
            "template": {"label": "Template", "color": "#a855f7"},
            "parameter_extractor": {"label": "Parameter Extractor", "color": "#f97316"},
            "http_request": {"label": "HTTP Request", "color": "#64748b"},
            "code": {"label": "Code", "color": "#84cc16"},
            "tool_call": {"label": "Tool Call", "color": "#06b6d4"},
            "answer": {"label": "Answer", "color": "#10b981"},
            "pm_module": {"label": "PM Module", "color": "#6366f1"},
            "human_input": {"label": "Human Input", "color": "#f59e0b"},
        }

    def _build_system_prompt(self) -> str:
        """构建工作流生成的 system prompt，对齐前端 v2 节点类型与 schema。"""
        return """你是一位面向 PM 工作台产品的工作流设计专家。请根据自然语言描述生成工作流定义。

输出单个 JSON 对象（不要 markdown 代码块、不要多余文字），严格遵循以下 schema：
{
  "name": "工作流名称",
  "description": "简要描述",
  "nodes": [
    {
      "id": "node-1",
      "type": "node_type",
      "name": "显示名称",
      "x": 100,
      "y": 100,
      "config": {}
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "sourceNodeId": "node-1",
      "targetNodeId": "node-2",
      "label": "可选标签"
    }
  ]
}

可用节点类型（只能使用以下类型）：
- start: 工作流入口（config: {}）
- end: 工作流出口（config: {}）
- condition: 条件分支（config: {condition: string, conditions: [], combinator: 'and'|'or'}）
- variable_set: 设置/更新变量（config: {variable_name, variable_value}）
- loop: 循环迭代（config: {loop_type: 'for_each'|'while', iterator, condition, max_iterations, body_node_ids: []}）
- llm: 语言模型调用（config: {model, system_prompt, prompt, temperature, max_tokens}）
- agent: AI agent 调用（config: {agent_id, instructions}）
- knowledge_retrieval: 知识库检索（config: {query, knowledge_base_id, top_k}）
- template: 模板渲染（config: {template, output_variable}）
- parameter_extractor: 通过 LLM 提取结构化参数（config: {model, input_text, parameters: [], output_variable}）
- http_request: 发送 HTTP 请求（config: {method, url, headers: {}, body}）
- code: 在沙箱中执行 Python（config: {code, input_variables: {}, output_variable}）
- tool_call: 调用外部工具（config: {tool_name, parameters: {}}）
- answer: 输出直接答案（config: {answer, output_variable}）
- pm_module: 读写 PM 工作台模块（config: {module_type: 'prd'|'requirement'|'roadmap'|'parameter'|'architecture'|'prototype'|'competitor'|'spec'|'flowchart'|'schedule'|'testcase'|'risk'|'meeting'|'acceptance'|'faq'|'requirement-boundary', action: 'read'|'create'|'update'|'delete', project_id, entry_id, filter: {}, data: {}}）
- human_input: 暂停工作流并向用户请求输入/确认（config: {prompt: string, fields: [{name, label, type: 'text'|'textarea'|'select'|'confirm', options?, required?}], output_variable}）

规则：
1. 必须有且仅有一个 'start' 节点，至少一个 'end' 节点。
2. 所有节点必须通过 edges 连接；使用 sourceNodeId / targetNodeId（不是 source / target）。
3. 节点位置从左到右 x 递增；分支时垂直分布。
4. 决策点使用 condition 节点（edge label 用 'true'/'false' 或有意义的标签）。
5. 迭代处理使用 loop 节点；PM 工作台数据访问使用 pm_module。
6. 根据用户描述为每个节点配置合理的默认值。
7. 只返回 JSON 对象。不要 markdown、不要解释、不要代码块。
8. 当描述包含"向我确认"、"让我选"、"表单确认"、"确认后再继续"、"中间需要我来确认"、"ask me"、"confirm with user"、"wait for input" 等语义时，必须使用 'human_input' 节点 — 不要压缩成单个 llm 节点。

关键 — 多轮澄清协议（3 轮目标，10 轮硬上限）：
在生成工作流之前，评估描述是否包含足够信息以产出高质量工作流。如果以下任一不明确，可提出澄清问题：
- 具体的输入数据源/格式
- condition 节点的决策标准（阈值、规则）
- 输出格式/目标系统（PM 模块类型、文件格式）
- 是否需要工作流中途用户确认（以及在哪个步骤）
- LLM 节点所需的模型（如用户未指定）

提问时输出 JSON: {"action": "ask", "questions": [{"key": "param_name", "question": "具体问题（必须用中文）", "suggested_answer": "建议答案（用户可一键采纳）", "reason": "为什么需要这个问题"}, ...]}

规则：
- 每轮提问 1-3 个聚焦问题（不要一次性抛出所有可能的问题）。
- 每个问题必须包含 suggested_answer，让用户可一键采纳。
- 目标 3 轮以内完成澄清；若用户回答模糊或说"直接生成"/"用默认值"/"按你建议"，立即切换到 generate 模式。
- 最多 10 轮硬上限 — 超过后强制 generate。
- 所有提问必须用中文。
- 优先补齐关键节点信息（类型/输入/输出），再问配置细节。
- 不要问与工作流无关的问题。

信息足够时，直接输出工作流 JSON（schema 同上）— 但要包装：{"action": "generate", "workflow": {...}}

绝不输出未包装 "action": "generate" 的工作流 JSON。
"""

    def _build_user_prompt(self, description: str, template_hint: Optional[str] = None) -> str:
        """构建用户提示词。"""
        prompt = f"请根据以下描述设计一个工作流：\n\n{description}\n\n"

        if template_hint:
            prompt += f"\n可以考虑以 '{template_hint}' 模式作为起点。\n"

        prompt += """\n请生成完整的工作流定义，包含节点和边。
确保工作流结构良好，连接正确，节点配置有意义。
"""
        return prompt

    async def generate_from_description(
        self, description: str, template_hint: Optional[str] = None
    ) -> dict:
        """Generate a workflow from a natural language description (template-only path).

        Args:
            description: Natural language description of the workflow
            template_hint: Optional template hint for generation

        Returns:
            Dictionary containing the generated workflow data
        """
        # D7: 完全移除 _match_template，直接走 LLM 生成
        log.info("Generating workflow via LLM (template matching disabled)")
        workflow_data = await self._generate_with_llm(description, template_hint)
        return workflow_data

    def _count_description_steps(self, description: str) -> int:
        """Count numbered steps in description (e.g., '1. xxx\n2. yyy' → 2).

        Recognizes patterns: '1.', '1、', '1)', '1：' at line start (possibly after whitespace).
        Used to detect multi-step workflow semantics and drive stronger LLM constraints.
        """
        if not description:
            return 0
        # Match lines starting with optional whitespace + digit + [.、):] + optional whitespace
        # Note: \s* (not \s+) so that Chinese-style "1.需求文档" (no space after marker) is counted.
        matches = re.findall(r"^\s*\d+[\.、\):：]\s*", description, re.MULTILINE)
        return len(matches)

    def _match_template(self, description: str) -> Optional[dict]:
        """Match description against known templates patterns.

        Args:
            description: Natural language description

        Returns:
            Matching template or None
        """
        desc_lower = description.lower()

        # Content moderation patterns
        if any(word in desc_lower for word in ["moderation", "moderate", "content review", "flag", "toxic", "spam"]):
            return WORKFLOW_TEMPLATES["content_moderation"]

        # Data pipeline patterns
        if any(word in desc_lower for word in ["data pipeline", "etl", "extract", "transform", "load", "data processing"]):
            return WORKFLOW_TEMPLATES["data_pipeline"]

        # Agent workflow patterns
        if any(word in desc_lower for word in ["agent", "multi-agent", "orchestrate", "coordinate agents"]):
            return WORKFLOW_TEMPLATES["agent_workflow"]

        # Approval patterns
        if any(word in desc_lower for word in ["approval", "approve", "review", "sign-off", "authorize"]):
            return WORKFLOW_TEMPLATES["approval_workflow"]

        # Parallel processing patterns
        if any(word in desc_lower for word in ["parallel", "concurrent", "simultaneous", "multiple tasks at once"]):
            return WORKFLOW_TEMPLATES["parallel_processing"]

        # Loop patterns
        if any(word in desc_lower for word in ["loop", "iterate", "repeated", "cyclic", "iterative"]):
            return WORKFLOW_TEMPLATES["loop_workflow"]

        # PM 文档转架构模板（中英双语关键词匹配，命中后零延迟返回完整模板）
        if any(word in desc_lower for word in [
            "需求文档", "产品架构", "模块识别",
            "doc to architecture", "requirement to architecture",
            "需求转架构", "需求转产品", "需求文档转化", "需求文档转"
        ]):
            return WORKFLOW_TEMPLATES["pm_doc_to_architecture"]

        # 注：原"≥4 编号步骤 + 确认关键词"强制兜底已删除——
        # 多步流程场景现在统一走 LLM 多轮澄清（generate_workflow_with_clarify），
        # 让 AI 自行决定是否提问、何时生成，避免跳过 LLM 的"假 AI 生成"。

        return None

    def _instantiate_template(self, template: dict) -> dict:
        """Instantiate a template into a workflow definition.

        Args:
            template: Template definition

        Returns:
            Workflow data with generated IDs
        """
        # Generate node IDs
        node_id_map = {}
        nodes = []
        for i, node_template in enumerate(template["nodes"]):
            node_id = f"node-{uuid.uuid4()}"
            node_id_map[i] = node_id
            nodes.append({
                "id": node_id,
                "type": node_template["type"],
                "name": node_template["name"],
                "x": node_template["x"],
                "y": node_template["y"],
                "config": node_template.get("config", {}),
            })

        # Generate edges with mapped node IDs（统一使用 sourceNodeId / targetNodeId 字段名）
        edges = []
        for edge_template in template["edges"]:
            source_idx = edge_template["source"]
            target_idx = edge_template["target"]
            edges.append({
                "id": f"edge-{uuid.uuid4()}",
                "sourceNodeId": node_id_map[source_idx],
                "targetNodeId": node_id_map[target_idx],
                "label": edge_template.get("label", ""),
            })

        return {
            "name": template["name"],
            "description": template["description"],
            "nodes": nodes,
            "edges": edges,
        }

    async def _generate_with_llm(self, description: str, template_hint: Optional[str] = None) -> dict:
        """Generate workflow using LLM (legacy fallback without user context).

        Deprecated: 不带 user/request 上下文，无法走 generate_chat_completion。
        保留仅为 generate_from_description 路径兼容；返回通用骨架。
        """
        log.warning("_generate_with_llm called without user context; returning generic workflow")
        return self._create_generic_workflow(description)

    def _create_generic_workflow(self, description: str) -> dict:
        """Create a generic workflow when no template matches.

        Args:
            description: Natural language description

        Returns:
            Generic workflow data
        """
        start_id = f"node-{uuid.uuid4()}"
        process_id = f"node-{uuid.uuid4()}"
        end_id = f"node-{uuid.uuid4()}"

        return {
            "name": f"Generated: {description[:50]}",
            "description": description,
            "nodes": [
                {
                    "id": start_id,
                    "type": "start",
                    "name": "Start",
                    "x": 100,
                    "y": 100,
                    "config": {},
                },
                {
                    "id": process_id,
                    "type": "llm",
                    "name": "Process",
                    "x": 300,
                    "y": 100,
                    "config": {
                        "model": "gpt-4",
                        "temperature": 0.7,
                        "system_prompt": "Process the input according to the workflow requirements.",
                        "prompt": "{{input.data}}",
                    },
                },
                {
                    "id": end_id,
                    "type": "end",
                    "name": "End",
                    "x": 500,
                    "y": 100,
                    "config": {},
                },
            ],
            "edges": [
                {
                    "id": f"edge-{uuid.uuid4()}",
                    "sourceNodeId": start_id,
                    "targetNodeId": process_id,
                    "label": "",
                },
                {
                    "id": f"edge-{uuid.uuid4()}",
                    "sourceNodeId": process_id,
                    "targetNodeId": end_id,
                    "label": "",
                },
            ],
        }

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """去除 LLM 输出可能包裹的 markdown 代码块（```json ... ```）。

        Args:
            text: LLM 原始返回内容

        Returns:
            去除包裹后的字符串
        """
        if not text:
            return text
        stripped = text.strip()
        # 匹配 ```json ... ``` 或 ``` ... ``` 形式
        fence_match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", stripped, re.DOTALL | re.IGNORECASE)
        if fence_match:
            return fence_match.group(1).strip()
        return stripped

    @staticmethod
    def _extract_json_object(text: str) -> Optional[dict]:
        """从 LLM 输出中提取首个 JSON 对象（兼容 markdown 包裹 / 前后多余文本）。

        Args:
            text: LLM 原始返回内容

        Returns:
            解析后的 dict 或 None
        """
        if not text:
            return None
        cleaned = AIWorkflowGenerator._strip_markdown_fences(text)

        # 快速路径：直接 parse
        try:
            result = json.loads(cleaned)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

        # 慢路径：正则提取首个 {...} 块
        try:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                result = json.loads(match.group())
                if isinstance(result, dict):
                    return result
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    @staticmethod
    async def _call_llm(
        request,
        user,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """调用 open_webui 的 generate_chat_completion（与对话窗口同源）。

        Args:
            request: FastAPI Request
            user: 当前用户
            model_id: 模型 ID
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            LLM 返回的文本内容（choices[0].message.content）
        """
        # 延迟导入避免循环依赖
        from open_webui.utils.chat import generate_chat_completion

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        try:
            result = await generate_chat_completion(request, payload, user)
            if isinstance(result, dict):
                choices = result.get("choices", []) or []
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    if content:
                        return content
                # 部分上游返回 'response' 字段
                if "response" in result and isinstance(result["response"], str):
                    return result["response"]
            return ""
        except Exception as e:
            log.error(f"generate_chat_completion failed: {e}", exc_info=True)
            return ""

    @staticmethod
    async def _call_llm_messages(
        request,
        user,
        model_id: str,
        messages: list[dict],
    ) -> str:
        """调用 LLM，支持多轮 messages 数组（用于多轮澄清）。

        Args:
            request: FastAPI Request
            user: 当前用户
            model_id: 模型 ID
            messages: 完整 messages 数组（含 system + 多轮 user/assistant）

        Returns:
            LLM 返回的文本内容（choices[0].message.content）
        """
        from open_webui.utils.chat import generate_chat_completion

        payload = {
            "model": model_id,
            "messages": messages,
            "stream": False,
            "temperature": 0.3,
        }

        try:
            result = await generate_chat_completion(request, payload, user)
            if isinstance(result, dict):
                choices = result.get("choices", []) or []
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    if content:
                        return content
                if "response" in result and isinstance(result["response"], str):
                    return result["response"]
            return ""
        except Exception as e:
            log.error(f"generate_chat_completion (multi-turn) failed: {e}", exc_info=True)
            return ""

    def _extract_action_object(self, raw: str) -> Optional[dict]:
        """从 LLM 输出中提取 {action: 'ask'|'generate', ...} JSON 对象。

        Args:
            raw: LLM 原始返回内容

        Returns:
            包含 action 字段的 dict，或 None（解析失败/无 action 字段）
        """
        if not raw:
            return None
        obj = AIWorkflowGenerator._extract_json_object(raw)
        if obj is None:
            return None
        if not isinstance(obj, dict):
            return None
        if "action" not in obj:
            return None
        return obj

    async def generate_workflow_with_clarify(
        self,
        description: str,
        model_id: str,
        user,
        request,
        history: Optional[list[dict]] = None,
        template_hint: Optional[str] = None,
        progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> dict:
        """多轮澄清生成 workflow（D17: 3 轮目标，10 轮硬上限）。

        Args:
            description: 原始描述
            model_id: 模型 ID
            user: 当前用户
            request: FastAPI request
            history: 之前的澄清历史 [{role: 'user'|'assistant', content: '...'}, ...]
                     首次调用为 None 或空列表
            template_hint: 可选模板提示
            progress_callback: 进度回调（async），用于推送 status 事件给前端

        Returns:
            {action: 'ask', questions: [...]} — 需要继续追问
            {action: 'generate', workflow: {...}, warnings: [...]} — 生成完成
        """

        # D17: 3 轮目标 + 8 轮软上限（追加 system 消息强制 generate）+ 10 轮硬上限（兜底直接生成）
        MAX_ROUNDS = 10
        SOFT_LIMIT = 8

        async def _emit(msg: str):
            if progress_callback is not None:
                try:
                    await progress_callback(msg)
                except Exception:  # 回调失败不影响主流程
                    log.debug("progress_callback failed", exc_info=True)

        history = history or []
        # D17: 通过 history 推断当前轮次（user 消息数 + 1 = 当前即将发起的轮次）
        user_turns = sum(1 for h in history if h.get("role") == "user")
        current_round = user_turns + 1

        await _emit(f"正在构造提示词（第 {current_round} 轮）…")

        # 构造多轮 messages
        messages: list[dict] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": self._build_user_prompt(description, template_hint)},
        ]
        # 追加历史（保留完整的澄清上下文）
        for h in history:
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        # D17: 软上限 — 追加 system 消息强制 generate
        if current_round >= SOFT_LIMIT:
            messages.append({
                "role": "system",
                "content": (
                    f"已澄清 {current_round} 轮，信息已足够。请立即输出 "
                    f'{{"action":"generate","workflow":{{...}}}}，不要再提问。'
                ),
            })
            await _emit(f"已达 {current_round} 轮，强制生成工作流…")

        await _emit("正在调用 AI 模型，请稍候…")

        # 调 LLM（多轮 messages）
        raw = await AIWorkflowGenerator._call_llm_messages(request, user, model_id, messages)

        await _emit("正在解析 AI 输出…")
        parsed = self._extract_action_object(raw)

        if parsed is None:
            # 解析失败，回退到直接生成（不带 history）
            log.warning("LLM clarify output unparseable, falling back to direct generation")
            try:
                workflow = await self.generate_workflow_with_llm(
                    description, model_id, user, request, template_hint
                )
                return {
                    "action": "generate",
                    "workflow": workflow,
                    "warnings": workflow.get("warnings", []) + ["LLM 澄清输出解析失败，已回退到直接生成"],
                }
            except Exception as e:
                return {
                    "action": "generate",
                    "workflow": {
                        "name": "AI 生成失败",
                        "description": description,
                        "nodes": [],
                        "edges": [],
                        "warnings": [f"LLM 生成失败：{e}"],
                        "template_used": None,
                        "error": "LLM_CLARIFY_FAILED",
                    },
                    "warnings": [f"LLM 生成失败：{e}"],
                }

        action = parsed.get("action")

        # D17: 硬上限 — 超过后若仍 ask，直接调用 generate_workflow_with_llm 兜底生成
        if action == "ask" and current_round >= MAX_ROUNDS:
            await _emit(f"已达 {MAX_ROUNDS} 轮硬上限，强制生成工作流…")
            log.warning("LLM clarify reached MAX_ROUNDS=%d, forcing direct generation", MAX_ROUNDS)
            try:
                workflow = await self.generate_workflow_with_llm(
                    description, model_id, user, request, template_hint
                )
                return {
                    "action": "generate",
                    "workflow": workflow,
                    "warnings": workflow.get("warnings", [])
                    + [f"已达 {MAX_ROUNDS} 轮上限，强制生成"],
                }
            except Exception as e:
                return {
                    "action": "generate",
                    "workflow": {
                        "name": "AI 生成失败",
                        "description": description,
                        "nodes": [],
                        "edges": [],
                        "warnings": [f"LLM 兜底生成失败：{e}"],
                        "template_used": None,
                        "error": "LLM_CLARIFY_MAX_ROUNDS_FAILED",
                    },
                    "warnings": [f"LLM 兜底生成失败：{e}"],
                }

        if action == "ask":
            questions = parsed.get("questions", []) or []
            # 兼容旧格式：若 questions 是字符串数组，转为对象数组
            normalized_questions = []
            for q in questions:
                if isinstance(q, str):
                    normalized_questions.append({
                        "key": f"q_{len(normalized_questions) + 1}",
                        "question": q,
                        "suggested_answer": "",
                        "reason": "",
                    })
                elif isinstance(q, dict):
                    normalized_questions.append({
                        "key": q.get("key", f"q_{len(normalized_questions) + 1}"),
                        "question": q.get("question", ""),
                        "suggested_answer": q.get("suggested_answer", q.get("suggestedAnswer", "")),
                        "reason": q.get("reason", ""),
                    })
            return {"action": "ask", "questions": normalized_questions}

        # action == 'generate'
        workflow_data = parsed.get("workflow", {}) or {}
        if not workflow_data:
            return {
                "action": "generate",
                "workflow": {
                    "name": "AI 生成失败",
                    "description": description,
                    "nodes": [],
                    "edges": [],
                    "warnings": ["LLM 返回的 workflow 字段为空"],
                    "template_used": None,
                    "error": "EMPTY_WORKFLOW",
                },
                "warnings": ["LLM 返回的 workflow 字段为空"],
            }

        await _emit("正在校验节点结构与自动修复…")
        # 走三层校验 + 自动修复
        warnings: list[str] = []
        workflow_data, repair_warnings = self._validate_and_repair(workflow_data, description)
        warnings.extend(repair_warnings)
        workflow_data["template_used"] = None
        workflow_data["warnings"] = warnings
        return {
            "action": "generate",
            "workflow": workflow_data,
            "warnings": warnings,
        }

    async def generate_workflow_with_llm(
        self,
        description: str,
        model_id: str,
        user,
        request,
        template_hint: Optional[str] = None,
    ) -> dict:
        """使用配置的 LLM 生成 workflow（单轮直接生成，无澄清）。

        流程：
        1. 调用 LLM → 提取 JSON → 失败带反馈重试一次
        2. _validate_and_repair 三层校验 + 自动修复
        3. 返回 workflow（含 warnings 字段）

        Args:
            description: 自然语言描述
            model_id: 模型 ID
            user: 当前用户
            request: FastAPI request
            template_hint: 可选模板提示

        Returns:
            Generated workflow data, 包含 name/description/nodes/edges/warnings
        """
        warnings: list[str] = []

        # 直接调 LLM（D7: 完全移除 _match_template，所有描述都走 LLM）
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(description, template_hint)

        # 传递 description 以便 _call_llm_and_parse 在重试时附加步骤数约束
        workflow_data = await self._call_llm_and_parse(
            request, user, model_id, system_prompt, user_prompt, warnings, description
        )

        if workflow_data is None:
            # 三次尝试均失败
            step_count = self._count_description_steps(description)
            if step_count >= 3:
                # 多步描述场景：回退到通用骨架对用户无价值，改为返回错误让前端提示重试
                log.warning(
                    "LLM generation failed 3 times for multi-step description (steps=%d); "
                    "returning error instead of generic skeleton",
                    step_count,
                )
                warnings.append(
                    f"AI 生成失败：LLM 输出连续 3 次无法解析为有效 JSON。"
                    f"检测到描述含 {step_count} 个编号步骤，回退到通用骨架无意义，请重试或手动创建。"
                )
                return {
                    "name": "AI 生成失败",
                    "description": description,
                    "nodes": [],
                    "edges": [],
                    "warnings": warnings,
                    "template_used": None,
                    "error": "LLM_OUTPUT_UNPARSEABLE",
                }
            # 简单描述场景：保留旧行为，回退通用骨架
            log.warning("LLM generation failed 3 times; returning generic workflow")
            warnings.append("LLM 输出解析失败，已回退到通用骨架")
            workflow_data = self._create_generic_workflow(description)
            workflow_data = self._validate_and_repair(workflow_data)[0]
            workflow_data["warnings"] = warnings
            return workflow_data

        # 3. 三层校验 + 自动修复（含 Layer 4 语义补全 — 自动注入 human_input 节点）
        workflow_data, repair_warnings = self._validate_and_repair(workflow_data, description)
        warnings.extend(repair_warnings)

        workflow_data["template_used"] = None
        workflow_data["warnings"] = warnings
        return workflow_data

    async def _call_llm_and_parse(
        self,
        request,
        user,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        warnings: list[str],
        description: str = "",
    ) -> Optional[dict]:
        """调用 LLM 并解析 JSON；首次失败带反馈重试最多 2 次（共 3 次调用）。

        Args:
            warnings: 用于追加 warning 文案的列表
            description: 原始描述文本，用于在重试时附加步骤数约束

        Returns:
            解析成功的 dict 或 None
        """
        # 首次调用
        raw = await AIWorkflowGenerator._call_llm(
            request, user, model_id, system_prompt, user_prompt
        )
        workflow_data = AIWorkflowGenerator._extract_json_object(raw)
        if workflow_data is not None:
            return workflow_data

        # 可观测性：记录 LLM 原始输出前 500 字符，便于调试
        raw_preview = (raw or "")[:500]
        warnings.append(
            f"首次 LLM 输出 JSON 解析失败，带错误反馈重试。原始输出前 500 字符: {raw_preview!r}"
        )
        log.warning("First LLM JSON parse failed; raw output (first 500 chars): %s", raw_preview)

        # 计算描述步骤数，用于在重试时附加更强约束
        step_count = self._count_description_steps(description) if description else 0

        # 第一次重试：附加 JSON 格式约束
        retry1_user_prompt = (
            user_prompt
            + "\n\nIMPORTANT: Your previous response could not be parsed as JSON. "
            "Please return ONLY a valid JSON object matching the schema, with no markdown fences, "
            "no code blocks, no prose before or after. The entire response must be parseable by json.loads()."
        )
        if step_count >= 3:
            retry1_user_prompt += (
                f"\n\nThe description contains {step_count} numbered steps. "
                f"You MUST return a complete multi-step workflow with AT LEAST {step_count + 1} nodes "
                f"(start + {step_count} step nodes + end). Do NOT return a skeleton with only start/llm/end."
            )
        raw_retry1 = await AIWorkflowGenerator._call_llm(
            request, user, model_id, system_prompt, retry1_user_prompt
        )
        workflow_data = AIWorkflowGenerator._extract_json_object(raw_retry1)
        if workflow_data is not None:
            return workflow_data

        raw_retry1_preview = (raw_retry1 or "")[:500]
        warnings.append(
            f"第一次重试仍失败：LLM 输出无法解析为 JSON。重试原始输出前 500 字符: {raw_retry1_preview!r}"
        )
        log.warning("Retry 1 LLM JSON parse failed; raw output (first 500 chars): %s", raw_retry1_preview)

        # 第二次重试：最强约束，明确要求节点数 + 节点类型
        retry2_user_prompt = (
            user_prompt
            + "\n\nCRITICAL: Your previous two responses could not be parsed as JSON."
            " You MUST return ONLY a valid JSON object. No markdown, no code fences, no prose."
            " The entire response must be parseable by json.loads()."
        )
        if step_count >= 3:
            # 多步描述：强制要求至少 N+2 个节点（start + N 步 + end）
            min_nodes = step_count + 2
            retry2_user_prompt += (
                f"\n\nThe description has {step_count} numbered steps. "
                f"Return EXACTLY {min_nodes} nodes (1 start + {step_count} step + 1 end). "
                f"Use these node types: start, parameter_extractor, pm_module, human_input, condition, end. "
                f"Use 'human_input' for any step mentioning '确认/confirm/ask'. "
                f"Connect all nodes with edges using sourceNodeId/targetNodeId."
            )
        raw_retry2 = await AIWorkflowGenerator._call_llm(
            request, user, model_id, system_prompt, retry2_user_prompt
        )
        workflow_data = AIWorkflowGenerator._extract_json_object(raw_retry2)
        if workflow_data is not None:
            return workflow_data

        raw_retry2_preview = (raw_retry2 or "")[:500]
        warnings.append(
            f"第二次重试仍失败：LLM 输出无法解析为 JSON。重试原始输出前 500 字符: {raw_retry2_preview!r}"
        )
        log.warning("Retry 2 LLM JSON parse failed; raw output (first 500 chars): %s", raw_retry2_preview)
        return None

    def _validate_and_repair(self, workflow_data: dict, description: str = "") -> tuple[dict, list[str]]:
        """三层校验 + 自动修复 + Layer 4 语义补全。

        Layer 1: JSON parse（外层调用方已完成，本方法接收 dict）
        Layer 2: schema 校验（节点类型合法、必须 1 个 start、≥1 个 end、edges 端点存在）
        Layer 3: 自动修复（缺 start/end 自动插入、缺 config 补 {}、无效 edge 删除、字段名归一化）
        Layer 4: 语义补全（检测描述含确认语义但 LLM 未生成 human_input 时自动注入）

        Args:
            workflow_data: LLM 返回的 workflow dict
            description: 原始描述文本，用于 Layer 4 语义检测

        Returns:
            (repaired_workflow, warnings) — warnings 列出所有修复动作
        """
        warnings: list[str] = []
        if not isinstance(workflow_data, dict):
            warnings.append("workflow 数据非 dict，已替换为空骨架")
            return (
                {
                    "name": "Generated Workflow",
                    "description": "",
                    "nodes": [],
                    "edges": [],
                },
                warnings,
            )

        # 字段归一化：确保 name / description / nodes / edges 存在
        repaired = dict(workflow_data)
        if not isinstance(repaired.get("name"), str) or not repaired["name"]:
            repaired["name"] = "Generated Workflow"
            warnings.append("缺少 name 字段，已补默认值")
        if not isinstance(repaired.get("description"), str):
            repaired["description"] = ""
        if not isinstance(repaired.get("nodes"), list):
            repaired["nodes"] = []
            warnings.append("nodes 字段非列表，已置空")
        if not isinstance(repaired.get("edges"), list):
            repaired["edges"] = []
            warnings.append("edges 字段非列表，已置空")

        # ===== 节点级修复 =====
        nodes = repaired["nodes"]
        valid_node_ids: set[str] = set()
        repaired_nodes: list[dict] = []
        start_count = 0
        end_count = 0

        for node in nodes:
            if not isinstance(node, dict):
                warnings.append("发现非 dict 节点，已剔除")
                continue

            # 节点 id 修复
            node_id = node.get("id")
            if not node_id or not isinstance(node_id, str):
                node_id = f"node-{uuid.uuid4()}"
                node["id"] = node_id
                warnings.append(f"节点缺少 id，已生成 {node_id}")

            # 节点 type 修复：不在允许集合内则降级为 'code' 节点
            node_type = node.get("type")
            if node_type not in ALLOWED_NODE_TYPES:
                # 常见 LLM 误用：llm_call→llm, agent_call→agent, data_transform→code
                # human_input 别名：LLM 常用 form/confirm/checkpoint/user_input/approval/human
                type_alias = {
                    "llm_call": "llm",
                    "agent_call": "agent",
                    "data_transform": "code",
                    "parallel": "loop",
                    "merge": "variable_set",
                    "webhook": "http_request",
                    "custom": "code",
                    "form": "human_input",
                    "confirm": "human_input",
                    "checkpoint": "human_input",
                    "user_input": "human_input",
                    "approval": "human_input",
                    "human": "human_input",
                    "input": "human_input",
                }
                mapped = type_alias.get(node_type) if isinstance(node_type, str) else None
                if mapped:
                    warnings.append(f"节点类型 '{node_type}' 已映射为 '{mapped}'")
                    node_type = mapped
                else:
                    warnings.append(
                        f"节点类型 '{node_type}' 不在允许集合内，已降级为 'code'"
                    )
                    node_type = "code"
                node["type"] = node_type

            # name 修复
            if not isinstance(node.get("name"), str) or not node["name"]:
                node["name"] = self.node_types.get(node_type, {}).get("label", node_type)
                warnings.append(f"节点 {node_id} 缺少 name，已补默认值")

            # x / y 修复
            try:
                x = float(node.get("x", 0))
            except (TypeError, ValueError):
                x = 0.0
                warnings.append(f"节点 {node_id} 的 x 非法，已置 0")
            try:
                y = float(node.get("y", 0))
            except (TypeError, ValueError):
                y = 0.0
                warnings.append(f"节点 {node_id} 的 y 非法，已置 0")
            node["x"] = x
            node["y"] = y

            # config 修复
            if not isinstance(node.get("config"), dict):
                node["config"] = {}
                warnings.append(f"节点 {node_id} 缺少 config，已补空对象")

            if node_type == "start":
                start_count += 1
            if node_type == "end":
                end_count += 1

            valid_node_ids.add(node_id)
            repaired_nodes.append(node)

        # ===== 缺 start 自动插入 =====
        if start_count == 0:
            start_node = {
                "id": f"node-{uuid.uuid4()}",
                "type": "start",
                "name": "Start",
                "x": 100,
                "y": 100,
                "config": {},
            }
            repaired_nodes.insert(0, start_node)
            valid_node_ids.add(start_node["id"])
            warnings.append("已自动补充 start 节点（位于 100,100）")
        elif start_count > 1:
            warnings.append(f"检测到 {start_count} 个 start 节点（建议保留 1 个）")

        # ===== 缺 end 自动插入 =====
        if end_count == 0:
            end_node = {
                "id": f"node-{uuid.uuid4()}",
                "type": "end",
                "name": "End",
                "x": 800,
                "y": 100,
                "config": {},
            }
            repaired_nodes.append(end_node)
            valid_node_ids.add(end_node["id"])
            warnings.append("已自动补充 end 节点（位于 800,100）")

        # ===== Edge 级修复 =====
        raw_edges = repaired["edges"]
        repaired_edges: list[dict] = []
        for edge in raw_edges:
            if not isinstance(edge, dict):
                warnings.append("发现非 dict edge，已剔除")
                continue

            # 字段名归一化：source/target → sourceNodeId/targetNodeId
            source_id = edge.get("sourceNodeId") or edge.get("source") or edge.get("from")
            target_id = edge.get("targetNodeId") or edge.get("target") or edge.get("to")

            if not source_id or not target_id:
                warnings.append("edge 缺少 source/target，已删除")
                continue

            if source_id not in valid_node_ids or target_id not in valid_node_ids:
                warnings.append(
                    f"edge 指向不存在的节点（source={source_id}, target={target_id}），已删除"
                )
                continue

            edge_id = edge.get("id")
            if not edge_id or not isinstance(edge_id, str):
                edge_id = f"edge-{uuid.uuid4()}"

            repaired_edges.append(
                {
                    "id": edge_id,
                    "sourceNodeId": source_id,
                    "targetNodeId": target_id,
                    "label": edge.get("label", "") or "",
                    **(
                        {"sourcePortId": edge["sourcePortId"]}
                        if edge.get("sourcePortId")
                        else {}
                    ),
                    **(
                        {"targetPortId": edge["targetPortId"]}
                        if edge.get("targetPortId")
                        else {}
                    ),
                    **(
                        {"dataMappingRules": edge["dataMappingRules"]}
                        if edge.get("dataMappingRules")
                        else {}
                    ),
                }
            )

        repaired["nodes"] = repaired_nodes
        repaired["edges"] = repaired_edges

        # ===== Layer 3.5: 孤立节点自动连接（D9 — 修复 engine.py "Node X is disconnected" 错误）=====
        # engine.py 的 _validate_workflow 严格要求非 start/end 节点必须有 incoming 或 outgoing 边。
        # LLM 有时生成多个独立分支但忘记连接到主流程，导致整批节点被判为 disconnected。
        # 这里在 schema 修复之后、语义补全之前自动给孤立节点补一条到 start 和 end 的边。
        repaired, _iso_warnings = self._connect_disconnected_nodes(repaired)
        warnings.extend(_iso_warnings)

        # ===== Layer 4: 语义补全 — 检测描述含确认语义但 LLM 未生成 human_input 时自动注入 =====
        if description:
            repaired = self._inject_human_input_if_missing(repaired, description, warnings)

        # 移除可能由 LLM 多余添加的字段（保留 warnings 由外层统一写入）
        return repaired, warnings

    def _connect_disconnected_nodes(self, workflow: dict) -> tuple[dict, list[str]]:
        """Layer 3.5: 检测并修复孤立节点（D9）。

        engine.py._validate_workflow 严格要求非 start/end 节点必须有 incoming 或 outgoing 边，
        否则报 "Node X is disconnected" 阻塞执行。LLM 生成的工作流有时会有孤立节点
        （例如生成了多个分支但忘记连接主流程），这里自动给孤立节点补边：

        - 优先策略：若孤立节点已有 incoming 但无 outgoing → 连一条到 end 的边
        - 若孤立节点已有 outgoing 但无 incoming → 连一条从 start 到该节点的边
        - 完全孤立（既无 incoming 也无 outgoing）→ 同时补 start→node 和 node→end 两条边

        边字段使用 sourceNodeId / targetNodeId（与 _validate_and_repair 的归一化约定一致）。
        """
        warnings: list[str] = []
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        if not nodes:
            return workflow, warnings

        # 收集所有已连接的节点 id
        connected_ids: set[str] = set()
        for e in edges:
            src = e.get("sourceNodeId") or e.get("source")
            tgt = e.get("targetNodeId") or e.get("target")
            if src:
                connected_ids.add(src)
            if tgt:
                connected_ids.add(tgt)

        # 找 start 和 end 节点
        start_node = next((n for n in nodes if n.get("type") == "start"), None)
        end_node = next((n for n in nodes if n.get("type") == "end"), None)

        # 统计每个节点的 incoming / outgoing
        incoming: dict[str, int] = {n["id"]: 0 for n in nodes}
        outgoing: dict[str, int] = {n["id"]: 0 for n in nodes}
        for e in edges:
            src = e.get("sourceNodeId") or e.get("source")
            tgt = e.get("targetNodeId") or e.get("target")
            if src in outgoing:
                outgoing[src] += 1
            if tgt in incoming:
                incoming[tgt] += 1

        new_edges = list(edges)
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            node_type = node.get("type", "")
            # start / end 不需要修复
            if node_type in ("start", "end"):
                continue
            # 已有连接（incoming 或 outgoing 至少一个）→ 不处理
            if incoming.get(node_id, 0) > 0 or outgoing.get(node_id, 0) > 0:
                continue

            # 完全孤立：补 start→node 和 node→end
            if start_node:
                new_edges.append({
                    "id": f"edge-auto-{node_id}-in-{uuid.uuid4().hex[:8]}",
                    "sourceNodeId": start_node["id"],
                    "targetNodeId": node_id,
                    "label": "",
                })
                warnings.append(f"自动连接孤立节点 {node_id} ← start（无 incoming/outgoing）")
            if end_node:
                new_edges.append({
                    "id": f"edge-auto-{node_id}-out-{uuid.uuid4().hex[:8]}",
                    "sourceNodeId": node_id,
                    "targetNodeId": end_node["id"],
                    "label": "",
                })
                warnings.append(f"自动连接孤立节点 {node_id} → end（无 incoming/outgoing）")

        workflow["edges"] = new_edges
        return workflow, warnings

    def _inject_human_input_if_missing(self, workflow: dict, description: str, warnings: list[str]) -> dict:
        """Layer 4 语义补全：若描述含确认语义但 workflow 无 human_input 节点，自动注入。

        策略：找到从 start 到 end 的最长路径，在中间节点之后插入 human_input 节点，
        并插入两条 edge（前驱→human_input, human_input→后继），删除原前驱→后继 edge。
        """
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        # 已有 human_input 节点则跳过
        if any(n.get("type") == "human_input" for n in nodes):
            return workflow

        # 检测确认语义
        confirmation_keywords = [
            "向我确认", "让我选", "表单确认", "确认后再",
            "中间需要我来确认", "让我确认", "确认有哪些",
            "ask me", "confirm with user", "wait for input",
            "确认", "confirm",
        ]
        desc_lower = description.lower()
        if not any(kw in desc_lower for kw in [k.lower() for k in confirmation_keywords]):
            return workflow

        # 找 start 和 end 节点
        start_node = next((n for n in nodes if n.get("type") == "start"), None)
        end_node = next((n for n in nodes if n.get("type") == "end"), None)
        if not start_node or not end_node:
            return workflow  # 无 start/end 无法插入

        # 构建邻接表，找最长路径（节点数最多）
        adjacency: dict[str, list[str]] = {n["id"]: [] for n in nodes}
        for e in edges:
            src = e.get("sourceNodeId")
            tgt = e.get("targetNodeId")
            if src in adjacency and tgt in adjacency:
                adjacency[src].append(tgt)

        # DFS 找 start→end 最长路径
        longest_path: list[str] = []
        visited: set[str] = set()

        def dfs(node_id: str, path: list[str]):
            nonlocal longest_path
            if node_id == end_node["id"]:
                if len(path) > len(longest_path):
                    longest_path = list(path)
                return
            visited.add(node_id)
            for next_id in adjacency.get(node_id, []):
                if next_id not in visited:
                    dfs(next_id, path + [next_id])
            visited.discard(node_id)

        dfs(start_node["id"], [start_node["id"]])

        if len(longest_path) < 3:
            # 路径太短（只有 start→end 或 start→x→end），不插入
            return workflow

        # 在路径中点之后插入 human_input 节点
        mid_idx = len(longest_path) // 2
        predecessor_id = longest_path[mid_idx]
        successor_id = longest_path[mid_idx + 1] if mid_idx + 1 < len(longest_path) else end_node["id"]

        # 计算新节点位置（前驱和后继的中点）
        predecessor = next((n for n in nodes if n["id"] == predecessor_id), None)
        successor = next((n for n in nodes if n["id"] == successor_id), None)
        new_x = 400
        new_y = 200
        if predecessor and successor:
            new_x = (float(predecessor.get("x", 0)) + float(successor.get("x", 0))) / 2
            new_y = (float(predecessor.get("y", 0)) + float(successor.get("y", 0))) / 2 + 80  # 向下偏移避免重叠

        human_input_id = f"node-{uuid.uuid4()}"
        human_input_node = {
            "id": human_input_id,
            "type": "human_input",
            "name": "确认",
            "x": new_x,
            "y": new_y,
            "config": {
                "prompt": "请确认以上内容是否正确，并补充必要信息。",
                "fields": [
                    {"name": "confirm", "label": "确认", "type": "confirm", "required": True},
                    {"name": "feedback", "label": "反馈", "type": "textarea", "required": False}
                ],
                "output_variable": "human_input_result"
            }
        }

        # 删除原前驱→后继 edge
        new_edges = [
            e for e in edges
            if not (e.get("sourceNodeId") == predecessor_id and e.get("targetNodeId") == successor_id)
        ]
        # 插入两条新 edge
        new_edges.append({
            "id": f"edge-{uuid.uuid4()}",
            "sourceNodeId": predecessor_id,
            "targetNodeId": human_input_id,
            "label": "",
        })
        new_edges.append({
            "id": f"edge-{uuid.uuid4()}",
            "sourceNodeId": human_input_id,
            "targetNodeId": successor_id,
            "label": "",
        })

        workflow["nodes"] = nodes + [human_input_node]
        workflow["edges"] = new_edges
        warnings.append(
            "检测到描述含确认语义但 LLM 未生成 human_input 节点，已在最长路径中点自动注入"
        )
        return workflow

    async def recommend_templates(self, description: str) -> list[dict]:
        """Recommend workflow templates based on description.

        Args:
            description: Natural language description

        Returns:
            List of recommended template information
        """
        desc_lower = description.lower()
        recommendations = []

        template_keywords = {
            "content_moderation": ["moderation", "moderate", "content review", "flag", "toxic", "spam"],
            "data_pipeline": ["data pipeline", "etl", "extract", "transform", "load", "data processing"],
            "agent_workflow": ["agent", "multi-agent", "orchestrate", "coordinate agents"],
            "approval_workflow": ["approval", "approve", "review", "sign-off", "authorize"],
            "parallel_processing": ["parallel", "concurrent", "simultaneous"],
            "loop_workflow": ["loop", "iterate", "repeated", "cyclic", "iterative"],
        }

        for template_id, keywords in template_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                template = WORKFLOW_TEMPLATES.get(template_id)
                if template:
                    recommendations.append({
                        "id": template_id,
                        "name": template["name"],
                        "description": template["description"],
                    })

        return recommendations

    def get_all_templates(self) -> list[dict]:
        """Get all available workflow templates.

        Returns:
            List of template information
        """
        return [
            {
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
            }
            for template_id, template in WORKFLOW_TEMPLATES.items()
        ]


# Singleton instance
ai_workflow_generator = AIWorkflowGenerator()
