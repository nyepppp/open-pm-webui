# Workflow Binding Contract

**Date**: 2026-07-11
**Feature**: PM Skills Integration (003)

---

## Overview

定义 Timbal Workflow 与 pm-skills 的绑定接口。

> **重要**: Timbal 作为 **Python 库嵌入** (`import timbal`)，**禁止**使用 `timbal start` 启动独立服务（违反宪法原则 VI）。

---

## Timbal 嵌入方式

```python
# 安装
pip install timbal

# 使用（嵌入式，在 Open WebUI 后端进程中运行）
from timbal import Workflow
from timbal.state import get_run_context

# Workflow 定义
wf = Workflow(name="my_workflow").step(...)

# 执行
result = await wf().collect()
```

---

## Timbal Workflow Definition

```python
from timbal import Workflow

# Timbal Workflow 定义示例
wf = (
    Workflow(name="discover_workflow")
    .step(
        brainstorm_ideas,
        idea=lambda ctx: ctx.params["idea"]
    )
    .step(
        identify_assumptions,
        ideas=lambda ctx: ctx.step_span("brainstorm_ideas").output["ideas"]
    )
    .step(
        prioritize_assumptions,
        assumptions=lambda ctx: ctx.step_span("identify_assumptions").output["assumptions"]
    )
    .step(
        brainstorm_experiments,
        prioritized_assumptions=lambda ctx: ctx.step_span("prioritize_assumptions").output["prioritized"]
    )
)
```

---

## Workflow Step Binding

```typescript
interface WorkflowStep {
  id: string;
  skill_id: string;              // 引用的 skill ID (e.g., "pm-skills/brainstorm-ideas")
  input_bindings: Binding[];    // 输入绑定
  output_bindings: Binding[];   // 输出绑定
}

interface Binding {
  source: string;               // 来源字段 (e.g., "step1.ideas")
  target: string;               // 目标字段 (e.g., "ideas")
}
```

---

## Timbal Workflow Binding Example

```python
from timbal import Workflow
from backend.open_webui.pm.skills.pm_skills_loader import load_skill

# 定义步骤函数（包装 pm-skills）
async def brainstorm_ideas(idea: str) -> dict:
    skill = load_skill("pm-skills/brainstorm-ideas")
    return await skill.execute(idea=idea)

async def identify_assumptions(ideas: list) -> dict:
    skill = load_skill("pm-skills/identify-assumptions")
    return await skill.execute(ideas=ideas)

# Timbal Workflow 定义
discover_workflow = (
    Workflow(name="discover_workflow")
    .step(brainstorm_ideas, idea=lambda ctx: ctx.params["idea"])
    .step(identify_assumptions, ideas=lambda ctx: ctx.step_span("brainstorm_ideas").output["ideas"])
)

# 执行
result = await discover_workflow(idea="AI-powered meeting summarizer")
```

---

## Validation Rules

- `skill_id` MUST exist in unified registry
- `input_bindings` MUST match skill's `inputSchema`
- `output_bindings` MUST match skill's `outputContract`
- Circular dependencies MUST be rejected
- Timbal Workflow MUST be embedded as Python library (`import timbal`)
- **PROHIBITED**: `timbal start` or any independent Timbal service
