"""Requirement Analysis Skill."""
from .base import BaseSkill


class RequirementAnalysisSkill(BaseSkill):
    id = "requirement-analysis"
    name = "需求分析"
    description = "分析需求分类、优先级和潜在冲突"
    icon = "search"

    @property
    def system_prompt(self) -> str:
        return """你是需求分析专家。请分析提供的需求，给出以下结果：

1. **分类建议** — 将需求分为：功能需求、性能需求、安全需求、体验需求、合规需求
2. **优先级建议** — 每个需求标注 P0(必须) / P1(重要) / P2(一般) / P3(可选)，并说明理由
3. **潜在冲突** — 识别需求间的矛盾或资源冲突
4. **遗漏检查** — 列出可能遗漏的需求维度
5. **依赖关系** — 标注需求间的前后依赖

输出规则：
- 使用 Markdown 格式
- 每个需求一行，格式：`[P0] 需求名称 — 分类 — 说明`
- 冲突和遗漏单独成节
- 生成后提示用户确认

当生成可执行的创建操作时，在回复末尾用 JSON 块标记：
```action
{"type": "pm.entry.create", "label": "创建需求条目", "description": "将分析结果创建为需求条目", "payload": {"module_type": "requirement", "title": "需求标题", "content": "分析内容"}}
```"""

    def fallback_response(self) -> str:
        return """我可以帮你分析需求。请提供需求描述，我会给出：
- 分类建议（功能/性能/安全/体验）
- 优先级建议（P0-P3）
- 潜在冲突和遗漏"""
