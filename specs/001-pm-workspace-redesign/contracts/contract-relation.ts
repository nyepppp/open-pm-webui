# Contract: Relation Management API

**Feature**: PM 工作台重构 — 模块化布局与差异化编辑器
**Date**: 2026-06-28
**Version**: 1.0.0

---

## Endpoints

### GET /api/pm/projects/:projectId/relations

**Description**: 获取项目关联列表

**Parameters**:
- `projectId` (path): 项目 ID
- `entityId` (query, optional): 指定实体 ID，返回该实体的所有关联
- `relationType` (query, optional): 过滤关联类型

**Response**:
```json
{
  "relations": [
    {
      "id": "uuid",
      "projectId": "uuid",
      "entityAId": "uuid",
      "entityBId": "uuid",
      "relationType": "references",
      "confidence": 85,
      "confirmed": 0,
      "createdBy": "ai",
      "createdAt": 1719878400
    }
  ]
}
```

### POST /api/pm/projects/:projectId/relations

**Description**: 创建关联

**Body**:
```json
{
  "entityAId": "uuid",
  "entityBId": "uuid",
  "relationType": "references",
  "confidence": 100,
  "confirmed": 1,
  "createdBy": "user"
}
```

**Response**: 创建的 Relation 对象

### DELETE /api/pm/projects/:projectId/relations/:id

**Description**: 删除关联

**Response**: 204 No Content

### POST /api/pm/projects/:projectId/relations/:id/confirm

**Description**: 确认 AI 建议的关联

**Response**: 更新后的 Relation 对象（confirmed: 1）

### GET /api/pm/projects/:projectId/relations/impact

**Description**: 影响分析

**Parameters**:
- `entityId` (query): 实体 ID

**Response**:
```json
{
  "upstream": [
    { "entityId": "uuid", "entityType": "requirement", "relationType": "derives" }
  ],
  "downstream": [
    { "entityId": "uuid", "entityType": "testcase", "relationType": "references" }
  ]
}
```

### GET /api/pm/projects/:projectId/relations/trace

**Description**: 追溯链路

**Parameters**:
- `entityId` (query): 实体 ID
- `direction` (query): "upstream" | "downstream" | "both"

**Response**: 实体链路数组

### POST /api/pm/projects/:projectId/relations/suggest

**Description**: AI 建议关联

**Body**:
```json
{
  "entityId": "uuid",
  "targetModuleType": "testcase"
}
```

**Response**:
```json
{
  "suggestions": [
    {
      "entityBId": "uuid",
      "relationType": "references",
      "confidence": 78,
      "reason": "需求描述与测试用例场景匹配"
    }
  ]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | 关联类型无效 |
| 404 | 实体不存在 |
| 409 | 关联已存在 |
