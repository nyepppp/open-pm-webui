# Data Model: PM 工作台重构

**Feature**: PM 工作台重构 — 模块化布局与差异化编辑器
**Date**: 2026-06-28
**Status**: Draft

---

## Core Entities

### Project

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | text (UUID) | ✅ | 主键 |
| name | text | ✅ | 项目名称，全局唯一 |
| description | text | ❌ | 项目描述 |
| type | text | ✅ | "prd" | "competitor" | "general" |
| status | text | ✅ | "active" | "archived" | "deleted" |
| config | json | ❌ | API Key、模板配置等 |
| createdAt | integer | ✅ | 创建时间戳 |
| updatedAt | integer | ✅ | 更新时间戳 |

### Version

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | text (UUID) | ✅ | 主键 |
| projectId | text | ✅ | 关联项目 |
| versionNumber | text | ✅ | 版本号，如 "v1.0" |
| label | text | ❌ | "milestone" | "release" | "review" |
| description | text | ✅ | 版本描述 |
| snapshotPath | text | ✅ | 快照存储路径 |
| createdBy | text | ❌ | 创建人 |
| createdAt | integer | ✅ | 创建时间戳 |

### ModuleEntry (Base)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | text (UUID) | ✅ | 主键 |
| projectId | text | ✅ | 关联项目 |
| moduleType | text | ✅ | 模块类型（见下方枚举） |
| title | text | ✅ | 标题 |
| content | text | ❌ | 内容（富文本/JSON） |
| metadata | json | ❌ | 模块特定元数据 |
| versionId | text | ❌ | 关联版本 |
| status | text | ✅ | "draft" | "review" | "approved" | "archived" |
| priority | text | ❌ | "p0" | "p1" | "p2" | "p3" |
| createdAt | integer | ✅ | 创建时间戳 |
| updatedAt | integer | ✅ | 更新时间戳 |
| version | integer | ✅ | 乐观锁版本号，默认 1 |

**ModuleType 枚举**: "prd", "requirement", "parameter", "testcase", "risk", "competitor", "roadmap", "meeting", "acceptance", "faq", "product-architecture"

---

## Module-Specific Schemas

### PRDDocument (moduleType: "prd")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sections | json | ✅ | PRDSection[] |
| template | text | ❌ | "standard" | "minimal" | "detailed" |
| attachments | json | ❌ | Attachment[] |

```typescript
interface PRDSection {
  id: string;
  type: "overview" | "background" | "goal" | "requirement" | "non_functional" | "appendix";
  title: string;
  content: string;
  parameters: string[]; // 嵌入的参数 ID
  order: number;
}
```

### Requirement (moduleType: "requirement")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source | text | ❌ | "manual" | "excel" | "agent" |
| category | text | ❌ | 分类标签 |
| tags | json | ❌ | string[] |
| userRole | text | ❌ | 用户角色 |
| expectedBenefit | text | ❌ | 期望收益 |
| relatedModules | json | ❌ | string[] |

### Parameter (moduleType: "parameter")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | text | ✅ | 英文标识 |
| moduleId | text | ❌ | 所属模块 |
| featureId | text | ❌ | 所属功能 |
| paramType | text | ✅ | "input" | "output" | "config" |
| dataType | text | ✅ | "string" | "number" | "boolean" | "object" | "array" |
| required | integer | ✅ | 0 | 1 |
| defaultValue | text | ❌ | 默认值 |
| description | text | ❌ | 说明 |
| sourceDocument | text | ❌ | 来源 PRD ID |

### Testcase (moduleType: "testcase")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| scenario | text | ✅ | 测试场景 |
| precondition | text | ❌ | 前置条件 |
| steps | text | ✅ | 操作步骤 |
| inputData | text | ❌ | 输入数据 |
| expectedResult | text | ✅ | 预期结果 |
| caseType | text | ✅ | "functional" | "boundary" | "exception" | "performance" |
| requirementId | text | ❌ | 关联需求 ID |
| parameterId | text | ❌ | 关联参数 ID |

### Risk (moduleType: "risk")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| probability | text | ✅ | "high" | "medium" | "low" |
| impactScope | text | ✅ | 影响范围 |
| owner | text | ❌ | 负责人 |
| measures | text | ❌ | 应对方案 |
| deadline | integer | ❌ | 截止时间戳 |

### Competitor (moduleType: "competitor")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | text | ✅ | 竞品名称 |
| url | text | ❌ | 竞品 URL |
| description | text | ❌ | 描述 |
| dimensions | json | ❌ | CompetitorDimension[] |

### Roadmap (moduleType: "roadmap")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| nodes | json | ✅ | MindMapNode[] |
| layout | text | ❌ | "hierarchical" | "radial" | "free" |

### Meeting (moduleType: "meeting")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| participants | json | ❌ | string[] |
| meetingDate | integer | ❌ | 会议时间戳 |
| conclusions | text | ❌ | 结论 |
| actionItems | json | ❌ | ActionItem[] |

### Acceptance (moduleType: "acceptance")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| scope | text | ❌ | 验收范围 |
| result | text | ❌ | "pass" | "fail" | "partial" |
| passedItems | json | ❌ | string[] |
|遗留问题 | json | ❌ | string[] |

### FAQ (moduleType: "faq")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | text | ✅ | 问题 |
| answer | text | ✅ | 回答 |
| audience | text | ❌ | 适用对象 |
| relatedFeatures | json | ❌ | string[] |

### ProductArchitecture (moduleType: "product-architecture")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| nodes | json | ✅ | MindMapNode[] |
| autoExtracted | boolean | ❌ | 是否自动提取 |

---

## MindMapNode Schema

```typescript
interface MindMapNode {
  id: string;
  projectId: string;
  parentId: string | null;
  label: string;
  type: "root" | "branch" | "leaf" | "dependency";
  position: { x: number; y: number };
  metadata: {
    color?: string;
    icon?: string;
    progress?: number; // 0-100
    status?: "planned" | "in_progress" | "completed" | "delayed";
  };
  moduleRef: string | null; // 关联到具体 ModuleEntry ID
  createdAt: number;
  updatedAt: number;
}
```

---

## Relation Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | text (UUID) | ✅ | 主键 |
| projectId | text | ✅ | 关联项目 |
| entityAId | text | ✅ | 实体 A ID |
| entityBId | text | ✅ | 实体 B ID |
| relationType | text | ✅ | "contains" | "references" | "derives" | "modifies" | "conflicts" |
| confidence | integer | ❌ | 0-100，AI 建议置信度 |
| confirmed | integer | ✅ | 0=待确认, 1=已确认 |
| createdBy | text | ❌ | "ai" | "user" |
| createdAt | integer | ✅ | 创建时间戳 |

---

## State Transitions

### ModuleEntry Lifecycle

```
draft → review → approved → archived
  ↓
deleted (软删除)
```

### Version Lifecycle

```
draft → published → archived
```

### Relation Lifecycle

```
pending → confirmed → rejected
```

---

## Validation Rules

- **Project.name**: 全局唯一，重复时自动追加序号
- **ModuleEntry.title**: 项目内唯一，不能为空
- **Version.versionNumber**: 项目内唯一，格式 "v{major}.{minor}"
- **Relation**: entityAId 和 entityBId 不能相同
- **MindMapNode**: parentId 必须指向同项目的节点

---

## Indexes

- **Project**: name (unique)
- **Version**: projectId + versionNumber (unique)
- **ModuleEntry**: projectId + moduleType + title (unique)
- **Relation**: projectId + entityAId + entityBId (unique)
- **MindMapNode**: projectId + parentId
