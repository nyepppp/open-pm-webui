# PM工作台集成Open WebUI对话系统（第一阶段：A+B+C）

## Goal

将 PM 工作台深度集成到 Open WebUI 的对话系统中，让 AI 可以在对话中引用 PM 数据、执行 PM 工作流，实现原生对话体验。

## Background

项目已具备完整的 PM 基础设施：
- **数据模型**: PMProject, PMEntry, PMEntryVersion 等（`backend/open_webui/models/pm.py`）
- **API 路由**: 完整的 CRUD API（`backend/open_webui/routers/pm.py`）
- **PM 工具集**: 10+ 个 Open WebUI 工具（`backend/open_webui/tools/pm_*.py`）
- **前端组件**: 50+ 个 Svelte 组件（`src/lib/components/pm/`）
- **标注面板**: 已有 `PMAnnotationPanel.svelte` 等组件

## Requirements

### 子任务 A: PM 数据 API 层

- [ ] **A1**: 扩展 PM API，支持对话系统查询/引用 PM 模块数据
  - 按项目、模块类型、状态、优先级过滤查询条目
  - 支持全文搜索和模糊匹配
  - 返回结构化的条目数据（含元数据、参数、关联关系）
  
- [ ] **A2**: 新增标注数据模型和 API
  - 标注表: id, entry_id, project_id, annotation_type, content, source_data, created_at
  - 支持 CRUD 操作
  - 支持按条目和项目查询标注

- [ ] **A3**: 数据关联和引用机制
  - 条目与标注的 1:N 关联
  - 支持通过 entry_id 查询相关标注
  - 标注内容支持富文本格式

### 子任务 B: 对话入口改造

- [ ] **B1**: 在 Open WebUI 对话中集成 PM 工具引用入口
  - 在对话输入框附近添加 PM 工具选择器
  - 支持选择项目、模块、条目
  - 支持一键引用 PM 数据到对话上下文

- [ ] **B2**: 对话消息中展示 PM 数据引用
  - 引用内容以卡片形式展示
  - 支持点击查看详情
  - 支持复制引用内容

- [ ] **B3**: 对话历史中的 PM 数据持久化
  - 引用的 PM 数据随消息保存
  - 支持历史对话中查看和重新引用

### 子任务 C: AI 工具/技能封装

- [ ] **C1**: 封装 PM 数据查询工具
  - `query_pm_data`: 查询 PM 条目数据
  - `search_pm_entries`: 搜索 PM 条目
  - `get_pm_annotation`: 获取条目标注

- [ ] **C2**: 封装标注生成工具
  - `generate_annotation`: 基于条目数据生成标注文本
  - 支持一键复制带格式文本
  - 支持保存到标注模块

- [ ] **C3**: 封装 PM 工作流工具
  - `execute_pm_workflow`: 执行 PM 工作流
  - 支持多步骤流程和条件分支
  - 支持表单输出和确认导入

## Acceptance Criteria

### A - PM 数据 API
- [ ] API 可以按项目、模块类型、状态、优先级过滤查询条目
- [ ] API 支持全文搜索，返回结果包含高亮匹配
- [ ] 标注数据模型支持 CRUD，标注内容支持富文本
- [ ] 可以通过 entry_id 查询相关标注

### B - 对话入口
- [ ] 对话界面有 PM 工具引用入口
- [ ] 可以选择项目、模块、条目并引用到对话
- [ ] 引用的 PM 数据以卡片形式展示
- [ ] 支持复制引用内容

### C - AI 工具/技能
- [ ] AI 可以通过工具查询 PM 数据
- [ ] AI 可以生成标注文本并支持复制
- [ ] AI 可以执行 PM 工作流
- [ ] 工具可以在 Open WebUI 对话中正常调用

## Out of Scope

- 原型标注的前端界面展示（仅提供数据 API 和文本生成）
- AI 需求(PRD)设计工作流（第二阶段）
- 产品架构图实时同步（第二阶段）
- 多角色需求评审（第二阶段）

## Technical Notes

- 后端: Python FastAPI, SQLAlchemy, Pydantic
- 前端: Svelte, Tailwind CSS
- 工具: Open WebUI Tool 机制（`backend/open_webui/tools/`）
- 数据: SQLite/PostgreSQL

## Open Questions

1. 标注文本的格式模板是否需要可配置？
2. 对话中引用 PM 数据的权限控制如何设计？
3. 是否需要支持批量生成标注？
