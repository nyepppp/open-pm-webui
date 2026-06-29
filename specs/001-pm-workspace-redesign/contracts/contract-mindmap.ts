# Contract: MindMap API

**Feature**: PM 工作台重构 — 模块化布局与差异化编辑器
**Date**: 2026-06-28
**Version**: 1.0.0

---

## Endpoints

### GET /api/pm/projects/:projectId/modules/:moduleType/mindmap

**Description**: 获取思维导图数据

**Parameters**:
- `projectId` (path): 项目 ID
- `moduleType` (path): 模块类型（"roadmap" | "product-architecture"）
- `versionId` (query, optional): 版本 ID

**Response**:
```json
{
  "nodes": [
    {
      "id": "uuid",
      "projectId": "uuid",
      "parentId": null,
      "label": "产品目标",
      "type": "root",
      "position": { "x": 0, "y": 0 },
      "metadata": {
        "color": "#1890ff",
        "icon": "target",
        "progress": 100
      },
      "moduleRef": null
    }
  ],
  "edges": [
    {
      "source": "uuid",
      "target": "uuid",
      "type": "default"
    }
  ],
  "layout": "hierarchical"
}
```

### PUT /api/pm/projects/:projectId/modules/:moduleType/mindmap

**Description**: 更新思维导图数据

**Body**:
```json
{
  "nodes": [...],
  "edges": [...],
  "layout": "hierarchical"
}
```

**Response**: 更新后的思维导图数据

### POST /api/pm/projects/:projectId/modules/:moduleType/mindmap/extract

**Description**: 从现有模块自动提取思维导图节点

**Body**:
```json
{
  "sourceModuleTypes": ["prd", "requirement", "parameter"],
  "targetNodeType": "product-architecture"
}
```

**Response**:
```json
{
  "extractedNodes": [
    {
      "label": "用户认证模块",
      "type": "branch",
      "sourceEntityId": "uuid",
      "sourceEntityType": "prd"
    }
  ],
  "accuracy": 0.85
}
```

### POST /api/pm/projects/:projectId/modules/:moduleType/mindmap/sync

**Description**: 同步思维导图到富文本

**Response**:
```json
{
  "markdown": "# 产品路线图\n\n## 里程碑 1\n- 需求 A\n- 需求 B\n"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | 布局类型无效 |
| 404 | 模块类型不支持思维导图 |
| 422 | 节点数据无效（循环引用等） |
