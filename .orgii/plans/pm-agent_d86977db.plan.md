# PM Agent 功能实现计划

## Context

当前 PM 工作流平台已有完整的前后端框架（SvelteKit + FastAPI），包括项目、版本、模块条目等核心 CRUD。Agent 模块目前只有一个**建议面板**（`PMAgentPanel.svelte`），只能做简单的完整性/风险/关联/改进分析建议，且无实际 AI 后端对接。

PRD 定义了 Agent 模块为**AI 能力调度器**，包含 5 个核心 Action（`agent.chat`、`agent.intent`、`agent.skill.call`、`agent.config`、`agent.status`）和 9 个 Skills（PRD生成、需求分析、竞品调研、原型走查、参数提取、测试用例生成、版本对比、关系建议、流程建议）。

OpenWebUI 自身已有完整的 Chat/Agent 基础设施（`Chat.svelte`、chat API、模型配置），可以直接复用。

## Approach

### Step 1: Agent 聊天面板 — 复用 OpenWebUI Chat 组件

**目标**: 在 PM 模块页面内嵌入一个上下文感知的 AI 聊天面板，复用 OpenWebUI 已有的聊天能力。

**做法**:
1. 新建 `PMAgentChatPanel.svelte` 组件，作为 PM 页面右侧的浮动/侧边聊天面板
2. 面板内部调用 OpenWebUI 的 `/api/chat/completions` 接口（已存在于 `src/lib/apis/chats/index.ts`）
3. 系统提示词（system prompt）自动注入当前 PM 上下文：项目名称、当前模块类型、当前编辑的条目 ID 和内容摘要
4. 用户可在面板中直接对话，AI 回复基于 PM 上下文
5. 在 `[module]/+page.svelte` 顶部操作栏添加一个"AI 助手"按钮，点击切换面板

### Step 2: Agent 意图识别 + Skill 路由

**目标**: 用户在聊天面板中说的话，AI 能识别意图并路由到对应的 Skill。

**做法**:
1. 后端新增 `/api/v1/pm/agent/chat` 端点，接收 `{ message, projectId, moduleType, entryId?, context? }`
2. 该端点先调用 `agent.intent` 逻辑（基于关键词 + LLM 分类），识别意图属于哪个 Skill
3. 意图类型映射：PRD 相关 → `prd-generation`，需求相关 → `requirement-analysis`，竞品相关 → `competitor-research`，参数 → `parameter-extract`，测试 → `testcase-generate`，版本 → `version-compare`，关联 → `relation-suggest`，流程 → `workflow-suggest`，通用 → `agent.chat`
4. 根据意图路由到对应 Skill 处理逻辑，Skill 处理完成后返回结构化结果 + 自然语言回复

### Step 3: Skill 实现框架 + 前两个 Skill

**目标**: 建立 Skill 执行框架，并实现 PRD 生成和需求分析两个核心 Skill。

**做法**:
1. 后端新建 `backend/open_webui/pm/skills/` 目录，每个 Skill 一个文件
2. Skill 基类定义：`name`, `description`, `systemPrompt`, `parseResponse()` 
3. **PRD 生成 Skill** (`prd_generation.py`):
   - 系统提示词要求 AI 按模板生成 PRD 结构（概述→背景→目标→功能需求→非功能需求→附录）
   - AI 输出 JSON 格式的章节列表
   - 前端接收后可直接创建 PRD 条目 + 章节结构
4. **需求分析 Skill** (`requirement_analysis.py`):
   - 读取项目下所有需求条目
   - AI 分析分类、优先级建议、潜在冲突
   - 返回结构化分析结果 + 文本摘要
5. 后端端点 `/api/v1/pm/agent/skill/{skill_id}` 执行具体 Skill

### Step 4: Agent 操作执行（Action）

**目标**: AI 建议可以一键应用到数据中，不只是建议。

**做法**:
1. 定义 PM Action 注册表，每个 Action 对应一个后端操作：
   - `pm.entry.create` → 创建模块条目
   - `pm.entry.update` → 更新模块条目
   - `pm.relation.create` → 创建关联关系
   - `pm.version.create` → 创建版本
   - `pm.parameter.extract` → 从 PRD 提取参数
2. AI 回复中包含 `action` 块（JSON），前端解析后显示为"应用"按钮
3. 用户点击"应用"后，前端调用对应的 PM API 执行操作
4. 执行前弹出确认弹窗，用户确认后执行

### Step 5: Agent 状态与配置

**目标**: 用户可配置 AI 提供商、查看 Agent 运行状态。

**做法**:
1. 复用 OpenWebUI 已有的模型配置（`/api/v1/configs`），PM Agent 直接使用全局配置的 AI 模型
2. 新增 `/api/v1/pm/agent/status` 端点，返回 AI 可用性、当前模型、上次分析时间
3. 前端在 PM 设置页面（项目工作台）展示 Agent 状态卡片
4. 如果全局未配置 AI，Agent 面板显示降级提示，所有手动功能仍可用

### Step 6: 聊天面板嵌入各模块页面

**目标**: 将 Agent 聊天面板嵌入到每个模块页面，支持上下文感知。

**做法**:
1. 修改 `[module]/+page.svelte`，添加右侧可收起的聊天面板
2. 面板自动注入上下文：
   - 当前项目 ID + 名称
   - 当前模块类型 + 名称
   - 如果正在编辑条目，注入条目标题和内容摘要
3. 面板支持拖拽调整宽度
4. 面板内聊天历史按项目隔离存储

## Key Files

### 新建文件

| 文件路径 | 说明 |
|---------|------|
| `src/lib/components/pm/PMAgentChatPanel.svelte` | Agent 聊天面板组件，嵌入模块页面右侧 |
| `src/lib/components/pm/PMAgentActionCard.svelte` | AI 返回的可执行 Action 卡片组件 |
| `src/lib/apis/pm/agentChat.ts` | Agent 聊天 API 封装（chat、intent、skill、action） |
| `src/lib/stores/pm/agentChatStore.ts` | Agent 聊天状态管理（消息历史、当前 Skill） |
| `backend/open_webui/pm/__init__.py` | PM Agent 模块包 |
| `backend/open_webui/pm/skills/__init__.py` | Skills 包 |
| `backend/open_webui/pm/skills/base.py` | Skill 基类定义 |
| `backend/open_webui/pm/skills/prd_generation.py` | PRD 生成 Skill |
| `backend/open_webui/pm/skills/requirement_analysis.py` | 需求分析 Skill |
| `backend/open_webui/pm/intent.py` | 意图识别逻辑 |
| `backend/open_webui/pm/actions.py` | PM Action 注册表与执行 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | 添加 Agent 聊天面板按钮和面板嵌入 |
| `src/routes/(app)/pm/[projectId]/+page.svelte` | 工作台添加 Agent 状态卡片 |
| `src/lib/apis/pm/types.ts` | 新增 Agent 聊天、Skill、Action 相关类型定义 |
| `backend/open_webui/routers/pm.py` | 新增 Agent 相关 API 端点（/agent/chat, /agent/skill/{id}, /agent/status） |
| `backend/open_webui/models/pm.py` | 新增 PMAgentMessage、PMSkillExecution 数据模型（可选，聊天历史持久化） |

## Risks & Open Questions

1. **OpenWebUI Chat API 复用方式**: OpenWebUI 的聊天 API 需要用户已登录且有 chat 权限。PM Agent 面板需要确认是否可以复用同一认证流程，还是需要独立的 API Key 配置。**建议**: 优先复用 OpenWebUI 全局认证，如果未配置 AI 模型则降级为只读模式。

2. **聊天历史存储**: 初始版本可以将聊天历史存浏览器 localStorage，后续迭代再考虑后端持久化到数据库。

3. **Skill 执行安全性**: AI 生成的 Action 需要用户确认才能执行，避免 AI 误操作覆盖数据。所有写操作必须二次确认。

4. **上下文注入长度限制**: 当项目数据量大时，注入全部上下文可能超出 token 限制。**建议**: 只注入当前模块条目的摘要（标题+前200字），需要详情时再按需加载。

5. **PRD 中技术栈差异**: PRD 描述的是 Agent Native + React + Drizzle 技术栈，而实际项目是 SvelteKit + FastAPI + SQLAlchemy。实现时以实际技术栈为准，PRD 中的数据模型和 Action 定义作为功能参考。
