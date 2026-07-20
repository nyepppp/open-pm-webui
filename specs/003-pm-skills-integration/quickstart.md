# Quickstart: PM Skills Integration

**Date**: 2026-07-11
**Feature**: PM Skills Integration (003)
**Purpose**: 验证 pm-skills 集成是否正常工作

---

## Prerequisites

- Open WebUI 已安装并运行
- PM 模块已启用
- pm-skills 文件已复制到 `backend/open_webui/pm/skills/pm-skills/`
- Timbal 已安装: `pip install timbal`

> **重要**: Timbal 作为 **Python 库嵌入** (`import timbal`)，**禁止**使用 `timbal start` 启动独立服务（违反宪法原则 VI）。

---

## 验证步骤

### 1. 验证 pm-skills 文件存在

```bash
# 检查 pm-skills 目录
ls backend/open_webui/pm/skills/pm-skills/

# 预期输出（部分）
pm-product-discovery/
pm-product-strategy/
pm-execution/
...
```

### 2. 验证技能注册

```bash
# 启动 Open WebUI
open-webui serve

# 检查日志中是否出现 pm-skills 注册信息
# 预期："Registered pm-skills: pm-skills/write-prd, pm-skills/discover, ..."
```

### 3. 验证显式调用

```bash
# 在 Agent 聊天中输入
/pm-write-prd Smart notification system that reduces alert fatigue

# 预期：Agent 加载 create-prd skill，返回 8-section PRD 草稿
```

### 4. 验证 Timbal Workflow 绑定（嵌入式）

```python
# 在 Open WebUI Python 后端中运行
from timbal import Workflow
from timbal.state import get_run_context
from backend.open_webui.pm.skills.pm_skills_loader import load_skill

# 定义 Timbal Workflow（嵌入式，非独立服务）
wf = (
    Workflow(name="test_workflow")
    .step(
        load_skill("pm-skills/brainstorm-ideas"),
        idea=lambda ctx: "AI-powered meeting summarizer"
    )
)

# 执行（在 Open WebUI 后端进程中运行）
result = await wf(idea="AI-powered meeting summarizer").collect()

# 预期：Timbal Workflow 成功执行，返回结构化输出
print(result.output)
```

> **注意**: 使用 `.collect()` 获取最终结果，或 `async for event in workflow()` 流式获取事件。

### 5. 验证链式 Workflow（嵌入式）

```python
# 在 Open WebUI Python 后端中运行
from timbal import Workflow
from timbal.state import get_run_context
from backend.open_webui.pm.skills.pm_skills_loader import load_skill

# 定义链式 Workflow（discover = 4 skills）
discover_wf = (
    Workflow(name="discover_workflow")
    .step(
        load_skill("pm-skills/brainstorm-ideas"),
        idea=lambda ctx: ctx.params["idea"]
    )
    .step(
        load_skill("pm-skills/identify-assumptions"),
        ideas=lambda ctx: ctx.step_span("brainstorm_ideas").output["ideas"]
    )
    .step(
        load_skill("pm-skills/prioritize-assumptions"),
        assumptions=lambda ctx: ctx.step_span("identify_assumptions").output["assumptions"]
    )
    .step(
        load_skill("pm-skills/brainstorm-experiments"),
        prioritized_assumptions=lambda ctx: ctx.step_span("prioritize_assumptions").output["prioritized"]
    )
)

# 执行（在 Open WebUI 后端进程中运行）
result = await discover_wf(idea="AI-powered meeting summarizer").collect()

# 预期：4 个 skill 按顺序执行，最终返回统一结构化输出
print(result.output)
```

> **注意**: 使用 `get_run_context().step_span("<name>").output` 获取上一步输出。

### 5. 验证自主调用

```bash
# 在 Agent 聊天中输入（不带命令）
How should we price our new AI feature?

# 预期：Agent 自动加载 pricing-strategy skill，返回结构化分析
```

---

## 常见问题

### Q: pm-skills 命令未注册
**A**: 检查 `backend/open_webui/pm/skills/pm-skills/` 目录是否存在且包含 SKILL.md 文件。

### Q: 工作流绑定失败
**A**: 检查 `PmSkillsMapping` 表中是否存在对应映射记录。

### Q: Timbal Workflow 执行失败
**A**: 确保使用 `import timbal` 而非 `timbal start`。Timbal 必须作为 Python 库嵌入 Open WebUI 后端，禁止启动独立服务。

### Q: 自主调用未加载 skill
**A**: 检查 Agent 上下文注入是否包含 pm-skills 注册表摘要。
