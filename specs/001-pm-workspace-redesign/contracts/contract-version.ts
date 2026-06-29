# Contract: Version Management API

**Feature**: PM 工作台重构 — 模块化布局与差异化编辑器
**Date**: 2026-06-28
**Version**: 1.0.0

---

## Endpoints

### GET /api/pm/projects/:projectId/versions

**Description**: 获取项目版本列表

**Parameters**:
- `projectId` (path): 项目 ID

**Response**:
```json
{
  "versions": [
    {
      "id": "uuid",
      "projectId": "uuid",
      "versionNumber": "v1.0",
      "label": "milestone",
      "description": "Initial release",
      "snapshotPath": "/snapshots/v1.0",
      "createdBy": "user-id",
      "createdAt": 1719878400,
      "changedModules": ["prd", "requirement"]
    }
  ]
}
```

### POST /api/pm/projects/:projectId/versions

**Description**: 创建新版本快照

**Body**:
```json
{
  "versionNumber": "v1.1",
  "label": "release",
  "description": "Added risk analysis",
  "changedModules": ["risk"]
}
```

**Response**: 创建的 Version 对象

### GET /api/pm/projects/:projectId/versions/:id

**Description**: 获取版本详情

**Parameters**:
- `projectId` (path): 项目 ID
- `id` (path): 版本 ID

**Response**: Version 对象 + 包含的模块条目列表

### POST /api/pm/projects/:projectId/versions/:id/switch

**Description**: 切换到指定版本

**Response**:
```json
{
  "currentVersionId": "uuid",
  "switchedAt": 1719878400
}
```

### GET /api/pm/projects/:projectId/versions/compare

**Description**: 对比两个版本

**Parameters**:
- `versionA` (query): 版本 A ID
- `versionB` (query): 版本 B ID
- `moduleType` (query, optional): 指定模块类型，不传则对比所有模块

**Response**:
```json
{
  "diff": {
    "added": [],
    "modified": [
      {
        "entityId": "uuid",
        "entityType": "prd",
        "changes": [
          { "field": "content", "old": "...", "new": "..." }
        ]
      }
    ],
    "deleted": []
  }
}
```

### POST /api/pm/projects/:projectId/versions/:id/rollback

**Description**: 回滚到指定版本

**Body**:
```json
{
  "scope": "project" | "module",
  "moduleType": "prd" // 当 scope="module" 时必填
}
```

**Response**: 回滚后的当前版本信息

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | 版本号格式错误 |
| 404 | 版本不存在 |
| 409 | 版本冲突（已存在相同版本号） |
| 422 | 回滚范围无效 |
