# PM Tool 注册

**父任务**: 07-04-open-webui-agent-integration  
**日期**: 2026-07-04  
**状态**: 规划中

---

## Goal

将 PM 模块注册为 Open WebUI Tool（Python callable + OpenAPI specs），使 AI 在对话中能自动判断并调用 PM 操作。

## Current State

前端已有 TypeScript 的 Tool/Skill 注册表（`src/lib/apis/pm/agentTools.ts`），包含 5 个 Tool 函数和 9 个 Skill 配置。但这些是**前端 JS 工具**，用于内置 Agent Chat 界面，不是 Open WebUI 的标准 Tool 机制。

本任务需要创建 **Open WebUI 标准 Python Tool**，通过 `POST /api/v1/tools/create` 注册到 Open WebUI 的 Tool 系统。

## Requirements

### R1: 创建 PM Tool Python 类

每个 PM 模块对应一个 Open WebUI Tool 类（含 `Valves` 配置 + 多个 callable 函数）：

| Tool ID | Python 文件 | 函数数 | Valves |
|---------|------------|--------|--------|
| `pm_project_tool` | pm_project_tool.py | 6 | PM_API_BASE_URL |
| `pm_entry_tool` | pm_entry_tool.py | 8 | PM_API_BASE_URL |
| `pm_version_tool` | pm_version_tool.py | 5 | PM_API_BASE_URL |
| `pm_relation_tool` | pm_relation_tool.py | 5 | PM_API_BASE_URL |
| `pm_workflow_tool` | pm_workflow_tool.py | 3 | PM_API_BASE_URL |
| `pm_import_export_tool` | pm_import_export_tool.py | 4 | PM_API_BASE_URL |
| `pm_ai_tool` | pm_ai_tool.py | 5 | PM_API_BASE_URL, PM_MODEL |

### R2: Tool callable 函数规范

- 每个 callable 函数有 docstring 描述（中文），含 `:param` 和 `:return`
- 函数签名通过 OpenAPI specs 自动生成
- 写入操作（create/update/delete）通过 `__event_call__` 的 `confirmation` 请求用户确认
- 通过 `__event_emitter__` 进行状态推送（`status` 事件）
- 所有函数强制要求 `project_id` 参数

### R3: Tool 注册流程

- 创建 Python Tool 类文件
- 通过 Open WebUI API 或数据库初始化脚本注册
- 注册后 Tool 在 Workspace 中可见、可选
- Chat 中 `tool_ids` 限定 PM Tool 后，AI 自动判断调用

### R4: 与现有前端 Agent Tools 的关系

- 前端 `agentTools.ts` 的 5 个 Tool 函数继续用于内置 Agent Chat
- 新增的 Python Tool 用于 Open WebUI 标准 Chat（OpenAI API 风格对话）
- 两种机制共存，不互相干扰

## Dependencies

- 依赖 `07-04-pm-backend-api`：PM API 端点完善后才能实现 Tool 内部的 HTTP 调用

## Acceptance Criteria

- [ ] 7 个 PM Tool Python 类创建完成
- [ ] 每个 Tool 有正确的 Valves 配置和 callable 函数
- [ ] Tool 通过 `POST /api/v1/tools/create` 成功注册
- [ ] Tool 在 Open WebUI Workspace 中可见可选
- [ ] 写入操作有 `__event_call__` 确认步骤
- [ ] AI 能根据用户意图自动调用对应 Tool
