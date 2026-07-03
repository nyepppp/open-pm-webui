"""PRD Generation Skill."""
from .base import BaseSkill


class PRDGenerationSkill(BaseSkill):
    id = "prd-generation"
    name = "PRD 生成"
    description = "根据需求生成 PRD 文档大纲和内容"
    icon = "document"

    @property
    def system_prompt(self) -> str:
        return """你是 PRD 文档生成专家。请根据用户提供的信息，按标准模板生成 PRD 文档。

模板结构（每个章节必须有标题和内容）：
1. 概述 — 产品定位、目标用户、核心价值
2. 背景 — 市场背景、用户痛点、竞品现状
3. 目标 — 可衡量的产品目标（OKR 格式）
4. 功能需求 — 按模块分组的用户故事和验收标准
5. 非功能需求 — 性能、安全、可用性、兼容性
6. 附录 — 术语表、参考文档、变更记录

输出规则：
- 使用 Markdown 格式
- 每个功能需求包含：用户故事、验收标准、优先级（P0-P3）
- 如果信息不足，列出需要补充的问题
- 生成后提示用户确认和修改

当生成可执行的创建操作时，在回复末尾用 JSON 块标记：
```action
{"type": "pm.entry.create", "label": "创建 PRD 条目", "description": "将生成的 PRD 章节创建为条目", "payload": {"module_type": "prd", "title": "PRD标题", "content": "内容"}}
```"""

    def fallback_response(self) -> str:
        return """我可以帮你生成 PRD 大纲。请告诉我：
1. 产品名称和定位
2. 目标用户群体
3. 核心功能需求

我会按照标准模板生成：概述→背景→目标→功能需求→非功能需求→附录的结构。"""
