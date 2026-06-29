# PM Agent 适配性调研报告

**溯源依据**: 基于 OpenWebUI 源码分析（2026-06-28），非凭空想象

## 1. OpenWebUI AI 架构摘要

### 1.1 Chat 完成流
- 前端: `Chat.svelte` → `sendMessage()` → `generateOpenAIChatCompletion()`
- API: `POST {WEBUI_BASE_URL}/api/chat/completions`
- 流式响应: SSE via `EventSourceParserStream` + Socket.IO events
- 支持参数: `model`, `messages`, `stream`, `tool_ids`, `skill_ids`, `files`, `features`

### 1.2 AI Provider 机制
- OpenAI: `OPENAI_API_BASE_URLS[]` + `OPENAI_API_KEYS[]`，多 provider 支持
- Ollama: `OLLAMA_BASE_URLS[]`，`/api/chat` 端点
- 后端路由: `chat_completion()` → 解析模型 → 分发到 Ollama 或 OpenAI-compatible

### 1.3 Tools 机制
- 注册: `POST /api/tools/create` → 提供 Python `content` + OpenAPI `specs`
- 调用流程: `chat_completion_tools_handler()` → task model 识别意图 → 执行 tool callable → 结果注入对话
- 前端: `tool_ids` 在 chat request 中传递

### 1.4 Skills 机制
- 注册: `POST /api/skills/create`
- 引用: `skill_ids` 在 chat request；用户输入 `<$skillId|label>` 自动解析
- 体现: `/` 命令在 MessageInput autocomplete

### 1.5 Knowledge (RAG)
- 创建: `createNewKnowledge()` → `addFileToKnowledgeById()`
- 搜索: `GET /api/knowledge/search?query=...`
- 引用: chat request 中 `files` 参数，作为 RAG 数据源

---

## 2. PM 模块集成方案

### 2.1 ✅ 注册 PM 为 Tool — 最佳适配路径

**原理**: OpenWebUI 的 Tool 机制天然支持业务函数调用

**实现步骤**:
1. 创建 PM Tool，Python `content` 定义以下函数:
   - `pm_get_project_status(project_id)` → 返回项目进度
   - `pm_list_requirements(project_id, filters)` → 列出需求
   - `pm_create_entry(project_id, module_type, title)` → 创建条目
   - `pm_suggest_relations(project_id, entry_id)` → AI 关联建议
2. 在 `specs` 中声明 OpenAPI 函数签名
3. 用户在 Chat 中选择 PM Tool，AI 自动判断何时调用

**约束**: 需后端支持 PM API 端点 (`/api/v1/pm/...`)，当前已有基础 CRUD

### 2.2 ✅ PM 文档 → Knowledge Base — 自然适配

**原理**: PM 条目可导出为文件加入 RAG

**实现步骤**:
1. 用 `createNewKnowledge()` 创建 "PM 项目知识库"
2. 用 `addFileToKnowledgeById()` 将 PRD 文档、需求条目等作为文件加入
3. Chat 中引用该 Knowledge base，AI 可自动检索 PM 文档内容
4. 溯源标注: AI 回答时引用 PM 文档片段，自动标注来源

**现状**: 已实现 "导出为笔记" 功能（`createNewNote`），可扩展为导出到 Knowledge

### 2.3 ✅ 复用 Chat UI — 可行但需定制

**原理**: Chat 组件自包含，可通过参数定制

**三种方案**:
1. **Tool 限定**: 设置 `tool_ids` 为 PM tool，让 AI 在 PM 语境下对话
2. **Custom Model**: 创建 PM 专属 Model wrapper，内嵌 PM 系统提示词
3. **Skill 触发**: 用户输入 `/pm-analyze` 等 Skill 命令，触发 PM 分析流程

**推荐**: 方案 2（Custom Model）最适合 PM 工作流场景，可预置 PM Agent 指令

### 2.4 ⚠️ 搜索打通 — 需后端扩展

**现状**: OpenWebUI 搜索仅覆盖 Chat history 和 Knowledge files
**需求**: PM 条目（entries）需可被搜索
**方案**:
1. **短期**: PM 条目导出到 Notes/Knowledge，通过现有搜索间接检索
2. **长期**: 后端添加 PM entries 搜索端点，前端 SearchModal 增加 PM tab

---

## 3. 实施优先级

| 优先级 | 集成项 | 预估工作量 | 依赖 |
|--------|--------|-----------|------|
| P0 | PM Tool 注册 | 2天 | 后端 PM API 完善 |
| P0 | PM → Knowledge 导出 | 1天 | 前端已有 createNewNote，扩展即可 |
| P1 | Custom Model (PM Agent) | 1天 | OpenWebUI Model 创建 API |
| P2 | Skill 注册 | 1天 | OpenWebUI Skill API |
| P2 | 搜索打通 | 2天 | 后端 PM 搜索端点 |

---

## 4. 风险提示

【无有效溯源依据，以下仅为通用行业参考方案，需结合内部规范二次校验】

1. **Tool 安全性**: PM Tool 的 Python content 在后端沙箱执行，需确保不泄露项目数据
2. **模型依赖**: PM Agent 功能依赖 AI 模型可用性，按照 PRD "手动优先" 原则，所有功能必须支持纯手动操作
3. **Token 成本**: PM 条目加入 RAG 会增加 token 消耗，需考虑成本控制
4. **多用户隔离**: Tool 调用时需传递 `project_id`，确保项目数据不穿透
