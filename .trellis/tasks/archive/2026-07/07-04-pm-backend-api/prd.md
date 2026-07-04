# PM 后端 API 完善

**父任务**: 07-04-open-webui-agent-integration  
**日期**: 2026-07-04  
**状态**: 规划中

---

## Goal

完善 PM 后端 API，补齐 Tool 注册所需的缺失端点，确保所有 PM Tool 函数都有对应的 HTTP API 可调用。

## Current State

已有 PM 后端 API（`backend/open_webui/routers/pm.py`，1381 行，45 个路由），覆盖：

| 模块 | 已有路由 | 状态 |
|------|----------|------|
| Projects | CRUD + list | ✅ 完善 |
| Entries | CRUD + list + versions | ✅ 完善 |
| Versions | create, switch, diff, compare, snapshot | ✅ 完善 |
| Branches/Merges | list, create | ✅ 完善 |
| Entities | CRUD + list | ✅ 完善 |
| Relations | CRUD + list + impact/chain/validate | ✅ 完善 |
| Agent | chat, status, skills, skill execution | ✅ 完善 |
| Agent Tools | create_entry, update_entry, create_relation, list_entries, get_entry | ✅ 完善 |

## Requirements

### R1: 补齐缺失的模块级 API

当前 PM API 使用统一的 entries 机制（module_type 区分模块），但部分 PRD 定义的模块级操作缺失：

| 需补齐的 API | PRD Action | 说明 |
|---------------|-----------|------|
| `POST /pm/entries/{id}/extract-parameters` | `parameter.extract` | 从 PRD 提取参数 |
| `POST /pm/entries/{id}/analyze` | `requirement.analyze` | AI 分析分类 |
| `POST /pm/entries/{id}/generate-testcases` | `testcase.generate` | AI 生成测试用例 |
| `POST /pm/entries/{id}/generate` | `prd.generate` | AI 生成 PRD |
| `POST /pm/entries/{id}/check` | `prd-check.run` | PRD 检查 |
| `GET /pm/projects/{id}/workflow/next` | `workflow.next` | 建议下一步 |
| `GET /pm/projects/{id}/workflow/progress` | `workflow.progress` | 进度统计 |
| `POST /pm/entries/import` | `requirement.import`, `parameter.import` | 文件导入 |
| `GET /pm/entries/{id}/export` | 多模块 export | 导出 |

### R2: Agent Tool API 扩展

现有 5 个 agent tool 需扩展为完整 Tool 覆盖：

| 新增 Agent Tool API | 对应 Tool callable |
|---------------------|-------------------|
| `DELETE /pm/agent/tools/delete_entry` | pm_delete_entry |
| `POST /pm/agent/tools/archive_project` | pm_archive_project |
| `POST /pm/agent/tools/extract_parameters` | pm_extract_parameters |
| `POST /pm/agent/tools/generate` | pm_generate (prd/testcase) |
| `POST /pm/agent/tools/import` | pm_import |

### R3: 搜索与筛选增强

- entries list 支持更多筛选参数（priority, status, tags, category）
- 搜索端点支持全文搜索（title + content）
- 关系查询支持方向参数（incoming/outgoing）

## Dependencies

- 无前置依赖（本任务是第一个执行的子任务）

## Acceptance Criteria

- [ ] 所有 PRD 定义的 28 个 Action 有对应的 HTTP API 端点
- [ ] Agent Tool API 覆盖所有需要的 Tool callable
- [ ] Entries list 支持多维度筛选和搜索
- [ ] 新增 API 与现有代码风格一致（FastAPI + SQLAlchemy async）
- [ ] 新增 API 有鉴权（`get_verified_user`）
