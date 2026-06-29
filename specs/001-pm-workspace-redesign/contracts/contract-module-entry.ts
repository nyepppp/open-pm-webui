# Contract: Module Entry API

**Feature**: PM 工作台重构 — 模块化布局与差异化编辑器
**Date**: 2026-06-28
**Version**: 1.0.0

---

## Base Endpoints

### GET /api/pm/projects/:projectId/modules/:moduleType

**Description**: 获取指定项目的模块条目列表

**Parameters**:
- `projectId` (path): 项目 ID
- `moduleType` (path): 模块类型
- `versionId` (query, optional): 版本 ID，不传则返回当前版本
- `page` (query, optional): 分页页码，默认 1
- `pageSize` (query, optional): 每页条数，默认 20
- `search` (query, optional): 搜索关键词

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "projectId": "uuid",
      "moduleType": "prd",
      "title": "PRD Title",
      "content": "<html>...",
      "metadata": {},
      "versionId": "uuid",
      "status": "draft",
      "priority": "p2",
      "createdAt": 1719878400,
      "updatedAt": 1719878400,
      "version": 1
    }
  ],
  "total": 100,
  "page": 1,
  "pageSize": 20
}
```

### GET /api/pm/projects/:projectId/modules/:moduleType/:id

**Description**: 获取单个模块条目详情

**Parameters**:
- `projectId` (path): 项目 ID
- `moduleType` (path): 模块类型
- `id` (path): 条目 ID

**Response**: 单个 ModuleEntry 对象

### POST /api/pm/projects/:projectId/modules/:moduleType

**Description**: 创建模块条目

**Body**: ModuleEntry 对象（不含 id, createdAt, updatedAt, version）

**Response**: 创建的 ModuleEntry 对象

### PUT /api/pm/projects/:projectId/modules/:moduleType/:id

**Description**: 更新模块条目（乐观锁）

**Body**: ModuleEntry 对象（必须包含 `version` 字段）

**Response**:
- 200: 更新成功
- 409: 版本冲突（ConcurrentModificationError）

### DELETE /api/pm/projects/:projectId/modules/:moduleType/:id

**Description**: 删除模块条目（软删除）

**Response**: 204 No Content

---

## Module-Specific Endpoints

### PRD Document

- `GET /api/pm/projects/:projectId/modules/prd/:id/sections` — 获取 PRD 章节列表
- `POST /api/pm/projects/:projectId/modules/prd/:id/sections` — 添加章节
- `PUT /api/pm/projects/:projectId/modules/prd/:id/sections/:sectionId` — 更新章节

### Parameter

- `GET /api/pm/projects/:projectId/modules/parameter/:id/config` — 生成配置清单
- `POST /api/pm/projects/:projectId/modules/parameter/import` — Excel 导入

### Testcase

- `POST /api/pm/projects/:projectId/modules/testcase/:id/execute` — 执行测试用例

### Risk

- `GET /api/pm/projects/:projectId/modules/risk/matrix` — 获取风险矩阵数据

### Roadmap

- `GET /api/pm/projects/:projectId/modules/roadmap/gantt` — 获取甘特图数据

### MindMap

- `GET /api/pm/projects/:projectId/modules/:moduleType/mindmap` — 获取思维导图数据
- `PUT /api/pm/projects/:projectId/modules/:moduleType/mindmap` — 更新思维导图数据
- `POST /api/pm/projects/:projectId/modules/:moduleType/mindmap/extract` — 从模块提取节点
