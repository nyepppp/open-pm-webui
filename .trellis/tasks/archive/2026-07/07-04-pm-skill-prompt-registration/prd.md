# PM Skill 与提示词注册

**父任务**: 07-04-open-webui-agent-integration  
**日期**: 2026-07-04  
**状态**: 规划中

---

## Goal

将 PM 工作流步骤固化为 Open WebUI Skill（Markdown 指令集）和提示词模板，使用户可通过 `$` 命令引用 Skill、通过 `/` 命令引用提示词。

## Current State

前端已有 9 个 Skill 配置（`src/lib/apis/pm/agentTools.ts` 的 `skillRegistry`），但这些是**前端 Skill 配置**，用于内置 Agent Chat，不是 Open WebUI 标准 Skill。

需要创建 **Open WebUI 标准 Skill**（Markdown 格式），通过 `POST /api/v1/skills/create` 注册到 Open WebUI Skill 系统。

## Requirements

### R1: 注册 PM Skill（≥3个）

基于现有前端 Skill 配置，转化为 Open WebUI 标准 Skill：

| Skill ID | 名称 | 来源 | 工具 |
|----------|------|------|------|
| `pm-prd-generation` | PRD 生成流程 | 前端 skillRegistry[0] | pm_entry_tool (create/update) |
| `pm-requirement-analysis` | 需求分析流程 | 前端 skillRegistry[1] | pm_entry_tool (list/get/update) |
| `pm-parameter-extraction` | 参数提取流程 | 前端 skillRegistry[4] | pm_entry_tool (get/create) + pm_ai_tool (extract) |

每个 Skill 包含：
- YAML frontmatter（name, description）
- 完整的 Markdown 步骤指引
- 明确的工具调用名称（`pm_xxx_tool.xxx`）
- 用户确认步骤标注

### R2: 注册 PM 提示词（≥2个）

| 提示词 ID | 名称 | 内容 |
|-----------|------|------|
| `pm-assistant` | 产品经理助手 | PM 工作流全域助手指令 |
| `pm-review-expert` | 需求评审专家 | PRD 检查和需求完整性分析指令 |

### R3: Skill/Prompt 引用方式

- Skill：用户输入 `$` 打开 picker → 选择 PM Skill → 注入 system prompt
- 提示词：用户输入 `/` 打开 picker → 选择 PM 提示词模板

## Dependencies

- 依赖 `07-04-pm-tool-registration`：Skill 指引中引用的 Tool 需先注册

## Acceptance Criteria

- [ ] 3 个 PM Skill 通过 `POST /api/v1/skills/create` 注册成功
- [ ] 2 个 PM 提示词通过 `POST /api/v1/prompts/create` 注册成功
- [ ] 用户可通过 `$` 命令在对话中引用 PM Skill
- [ ] Skill 注入的指令包含正确的 Tool 调用名称
- [ ] 提示词在 Workspace 中可见可选
