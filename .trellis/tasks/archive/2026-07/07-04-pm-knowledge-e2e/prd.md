# Knowledge 集成与端到端验证

**父任务**: 07-04-open-webui-agent-integration  
**日期**: 2026-07-04  
**状态**: 规划中

---

## Goal

1. 将 PM 条目/文档数据导出到 Open WebUI Knowledge Base，使 AI 对话可自动检索 PM 文档内容
2. 对整个 Agent 接入功能进行端到端验证，确保从对话到 PM 操作的完整闭环

## Requirements

### R1: PM → Knowledge Base 导出

- 每个 PM 项目对应一个 Open WebUI Knowledge base
- PM 条目（需求、PRD、参数等）可导出为 Markdown 文件加入 Knowledge
- 导出格式保留结构化信息（标题、字段、关联关系）
- 支持增量更新：PM 条目变更时标记 Knowledge 中对应文件需刷新
- 通过 Open WebUI API 注册 Knowledge：
  - `POST /api/v1/knowledge/create` 创建项目知识库
  - `POST /api/v1/knowledge/{id}/file/add` 添加文件
  - `DELETE /api/v1/knowledge/{id}/file/remove` 删除过期文件

### R2: Knowledge 检索集成

- Chat 对话中引用 PM Knowledge base，AI 可自动检索 PM 文档内容
- 检索结果自动标注来源（哪个 PM 条目、哪个字段）
- 支持 `#` 命令在对话中引用 Knowledge 文件

### R3: 端到端场景验证

验证以下完整对话流程：

| # | 场景 | 验证内容 |
|---|------|----------|
| 1 | 项目信息查询 | 用户问"项目X进展如何" → AI 调用 Tool 返回项目状态 |
| 2 | 需求列表查询 | 用户问"有哪些需求" → AI 返回需求表格 |
| 3 | 需求创建 | 用户说"创建需求：用户登录" → 确认 → 创建成功 |
| 4 | PRD 生成 | 用户引用 `$pm-prd-generation` Skill → 生成 PRD → 确认写入 |
| 5 | 参数提取 | 用户说"从PRD提取参数" → 展示参数表 → 确认写入 |
| 6 | 关联建立 | 用户说"把这个需求关联到那个参数" → 关联创建成功 |
| 7 | Knowledge 检索 | 用户在对话中引用 PM Knowledge → AI 检索并回答 |
| 8 | 数据导入 | 用户上传 Excel → 预览 → 确认导入需求列表 |

### R4: 集成回归测试

- 所有 16 个 PM Tool 可正常调用
- 3 个 PM Skill 可正常触发
- 2 个 PM 提示词可正常加载
- `__event_call__` 确认流正常工作
- `__event_emitter__` 事件流正常推送
- 项目隔离：项目 A 数据在项目 B 对话中不可见

## Dependencies

- 依赖 `07-04-pm-backend-api`：PM API 端点可用
- 依赖 `07-04-pm-tool-registration`：Tool 已注册
- 依赖 `07-04-pm-skill-prompt-registration`：Skill 和提示词已注册
- 依赖 `07-04-pm-form-confirmation-import`：确认和导入流程已实现

## Acceptance Criteria

- [ ] PM 项目可导出到 Knowledge base
- [ ] PM 条目变更可增量同步到 Knowledge
- [ ] Chat 对话可检索 Knowledge 中的 PM 文档
- [ ] 8 个端到端场景全部验证通过
- [ ] 所有 16 个 Tool 可正常调用
- [ ] 3 个 Skill 可正常触发
- [ ] 项目隔离验证通过
