# Data Model: 产品架构模块版本溯源与需求关联

**Feature**: 004-arch-module-version-demand
**Date**: 2026-07-08

## 实体关系图

```
Module (模块)
├── id: string (PK)
├── name: string
├── key: string (唯一)
├── data_type: string
├── required: boolean
├── description: string
├── create_version: string (创建时版本，不可修改)
├── version_record: VersionRecord[] (JSON 数组)
├── demand_relation: DemandRelation[] (JSON 数组)
├── is_deleted: boolean (软删除标记)
├── deleted_at: datetime (可选)
├── created_at: datetime
└── updated_at: datetime

Function (功能)
├── id: string (PK)
├── module_id: string (FK → Module)
├── name: string
├── key: string (唯一)
├── data_type: string
├── required: boolean
├── description: string
├── create_version: string
├── version_record: VersionRecord[] (JSON 数组)
├── demand_relation: DemandRelation[] (JSON 数组)
├── is_deleted: boolean
├── deleted_at: datetime (可选)
├── created_at: datetime
└── updated_at: datetime

Parameter (参数)
├── id: string (PK)
├── function_id: string (FK → Function)
├── name: string
├── key: string (唯一)
├── data_type: string
├── required: boolean
├── description: string
├── create_version: string
├── version_record: VersionRecord[] (JSON 数组)
├── demand_relation: DemandRelation[] (JSON 数组)
├── is_deleted: boolean
├── deleted_at: datetime (可选)
├── created_at: datetime
└── updated_at: datetime
```

## 嵌套类型定义

### VersionRecord (版本履历项)

```typescript
interface VersionRecord {
  version: string;        // 版本号，如 "1.0.0"
  operator: string;       // 操作人名称
  time: string;           // ISO 8601 格式时间戳
  change_detail: string;  // 变更字段说明，如 "修改了描述字段"
}
```

### DemandRelation (需求关联项)

```typescript
interface DemandRelation {
  demand_id: string;    // 需求编号
  demand_name: string;  // 需求名称
  doc_link: string;     // 文档链接（URL）
}
```

## 验证规则

### Module / Function / Parameter

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| id | string | 是 | 主键，UUID 格式 |
| name | string | 是 | 1-100 字符 |
| key | string | 是 | 唯一，字母/数字/下划线，1-50 字符 |
| data_type | string | 是 | 枚举值：string/number/boolean/array/object |
| required | boolean | 是 | 默认 true |
| description | string | 否 | 最大 500 字符 |
| create_version | string | 是 | 创建时自动回填，不可修改 |
| version_record | array | 是 | 默认 [] |
| demand_relation | array | 是 | 默认 [] |
| is_deleted | boolean | 是 | 默认 false |
| deleted_at | datetime | 否 | 软删除时填充 |
| created_at | datetime | 是 | 自动填充 |
| updated_at | datetime | 是 | 自动更新 |

### Function 特有约束

- `module_id` 必须指向存在的、未删除的 Module
- 同一 Module 下 Function 的 `key` 必须唯一

### Parameter 特有约束

- `function_id` 必须指向存在的、未删除的 Function
- 同一 Function 下 Parameter 的 `key` 必须唯一

## 状态转换

```
[创建] → [编辑] → [软删除]
   ↓
[复制] → 生成新条目（全新 create_version，可选复制 demand_relation）
```

## 索引设计

```sql
-- 主键索引（自动创建）
-- Module
CREATE INDEX idx_module_key ON module(key);
CREATE INDEX idx_module_is_deleted ON module(is_deleted);

-- Function
CREATE INDEX idx_function_module_id ON function(module_id);
CREATE INDEX idx_function_key ON function(key);
CREATE INDEX idx_function_is_deleted ON function(is_deleted);

-- Parameter
CREATE INDEX idx_parameter_function_id ON parameter(function_id);
CREATE INDEX idx_parameter_key ON parameter(key);
CREATE INDEX idx_parameter_is_deleted ON parameter(is_deleted);
```

## 数据迁移策略

### 存量数据兼容

1. **新增字段**: `create_version`, `version_record`, `demand_relation`, `is_deleted`, `deleted_at`
2. **默认值填充**:
   - `create_version` = '1.0.0'
   - `version_record` = '[]'
   - `demand_relation` = '[]'
   - `is_deleted` = false
   - `deleted_at` = NULL

3. **首次编辑触发**: 当用户编辑历史条目时，系统自动生成第一条版本变更记录

## JSON 字段查询示例

### 查询某条目的版本履历

```sql
SELECT version_record 
FROM module 
WHERE id = 'module-uuid';
-- 应用层解析 JSON 数组
```

### 查询绑定了特定需求的条目

```sql
SELECT * FROM module 
WHERE json_extract(demand_relation, '$[*].demand_id') LIKE '%REQ-001%';
```

## 性能考虑

- JSON 数组字段在 SQLite/PostgreSQL 中均可使用 JSON 函数查询
- 版本履历通常 < 100 条，内嵌存储不会导致性能问题
- 如需频繁按需求查询，可考虑在 `demand_relation` 上建立 GIN 索引（PostgreSQL）