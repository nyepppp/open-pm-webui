# Contract: Agent Analysis API

**Feature**: PM 工作台重构 — 模块化布局与差异化编辑器
**Date**: 2026-06-28
**Version**: 1.0.0

---

## Endpoints

### POST /api/pm/projects/:projectId/agent/analyze

**Description**: 触发 Agent 分析

**Body**:
```json
{
  "moduleType": "prd",
  "entityId": "uuid",
  "triggerType": "manual" | "auto",
  "analysisType": "completeness" | "risk" | "relation" | "all"
}
```

**Response**:
```json
{
  "suggestions": [
    {
      "id": "uuid",
      "type": "missing_section",
      "title": "缺少非功能性需求章节",
      "description": "PRD 中未包含性能、安全、可用性等非功能性需求",
      "confidence": 92,
      "location": "PRD Section 4",
      "action": "add_section",
      "payload": {
        "sectionType": "non_functional",
        "template": "..."
      }
    }
  ],
  "summary": {
    "total": 5,
    "highConfidence": 3,
    "mediumConfidence": 2
  }
}
```

### POST /api/pm/projects/:projectId/agent/suggestions/:id/confirm

**Description**: 确认采纳 Agent 建议

**Response**:
```json
{
  "applied": true,
  "changes": [
    { "field": "sections", "action": "add", "value": {...} }
  ]
}
```

### POST /api/pm/projects/:projectId/agent/suggestions/:id/reject

**Description**: 拒绝 Agent 建议

**Response**: 204 No Content

### GET /api/pm/projects/:projectId/agent/config

**Description**: 获取 Agent 配置

**Response**:
```json
{
  "autoAnalyze": false,
  "autoAnalyzeOnSave": true,
  "autoAnalyzeInterval": 3600,
  "provider": "openai",
  "model": "gpt-4"
}
```

### PUT /api/pm/projects/:projectId/agent/config

**Description**: 更新 Agent 配置

**Body**:
```json
{
  "autoAnalyze": false,
  "autoAnalyzeOnSave": true,
  "autoAnalyzeInterval": 3600
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | 分析类型无效 |
| 401 | AI API Key 未配置 |
| 429 | AI 服务速率限制 |
| 503 | AI 服务不可用 |
