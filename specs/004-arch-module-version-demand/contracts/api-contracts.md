# API Contracts: 产品架构模块版本溯源与需求关联

**Feature**: 004-arch-module-version-demand
**Date**: 2026-07-08

## 概述

本文档定义产品架构模块（模块/功能/参数）与版本溯源、需求关联相关的 API 接口契约。

## 接口列表

### 1. 模块管理接口

#### GET /api/pm/modules
获取模块列表（含版本和需求信息）

**Request**:
```
GET /api/pm/modules?include_deleted=false
```

**Response**:
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "用户管理",
      "key": "user_management",
      "data_type": "object",
      "required": true,
      "description": "...",
      "create_version": "2.1.0",
      "version_record": [
        {
          "version": "2.1.0",
          "operator": "张三",
          "time": "2026-07-08T10:30:00Z",
          "change_detail": "修改了描述字段"
        }
      ],
      "demand_relation": [
        {
          "demand_id": "REQ-001",
          "demand_name": "用户注册需求",
          "doc_link": "https://docs.example.com/req-001"
        }
      ],
      "created_at": "2026-07-01T00:00:00Z",
      "updated_at": "2026-07-08T10:30:00Z"
    }
  ]
}
```

#### POST /api/pm/modules
创建模块

**Request**:
```json
{
  "name": "用户管理",
  "key": "user_management",
  "data_type": "object",
  "required": true,
  "description": "...",
  "demand_relation": [
    {
      "demand_id": "REQ-001",
      "demand_name": "用户注册需求",
      "doc_link": "https://docs.example.com/req-001"
    }
  ]
}
```

**Response**:
```json
{
  "data": {
    "id": "uuid",
    "name": "用户管理",
    "key": "user_management",
    "create_version": "2.1.0",
    "version_record": [
      {
        "version": "2.1.0",
        "operator": "张三",
        "time": "2026-07-08T10:30:00Z",
        "change_detail": "初始创建"
      }
    ],
    "demand_relation": [...],
    "created_at": "2026-07-08T10:30:00Z",
    "updated_at": "2026-07-08T10:30:00Z"
  }
}
```

#### PUT /api/pm/modules/:id
编辑模块

**Request**:
```json
{
  "name": "用户管理（更新）",
  "description": "更新后的描述",
  "demand_relation": [
    {
      "demand_id": "REQ-001",
      "demand_name": "用户注册需求",
      "doc_link": "https://docs.example.com/req-001"
    },
    {
      "demand_id": "REQ-002",
      "demand_name": "用户登录需求",
      "doc_link": "https://docs.example.com/req-002"
    }
  ]
}
```

**Response**:
```json
{
  "data": {
    "id": "uuid",
    "name": "用户管理（更新）",
    "version_record": [
      {
        "version": "2.1.0",
        "operator": "张三",
        "time": "2026-07-08T10:30:00Z",
        "change_detail": "初始创建"
      },
      {
        "version": "2.2.0",
        "operator": "张三",
        "time": "2026-07-08T11:00:00Z",
        "change_detail": "修改了名称、描述字段；新增需求关联 REQ-002"
      }
    ],
    "updated_at": "2026-07-08T11:00:00Z"
  }
}
```

#### DELETE /api/pm/modules/:id
软删除模块

**Response**:
```json
{
  "data": {
    "id": "uuid",
    "is_deleted": true,
    "deleted_at": "2026-07-08T11:00:00Z"
  }
}
```

#### POST /api/pm/modules/:id/copy
复制模块

**Request**:
```json
{
  "copy_demands": true
}
```

**Response**:
```json
{
  "data": {
    "id": "new-uuid",
    "name": "用户管理（复制）",
    "create_version": "2.2.0",
    "version_record": [
      {
        "version": "2.2.0",
        "operator": "张三",
        "time": "2026-07-08T11:00:00Z",
        "change_detail": "从模块 user_management 复制创建"
      }
    ],
    "demand_relation": [...]
  }
}
```

### 2. 功能管理接口

与模块接口结构相同，路径为 `/api/pm/functions`，额外字段 `module_id`。

### 3. 参数管理接口

与模块接口结构相同，路径为 `/api/pm/parameters`，额外字段 `function_id`。

### 4. 版本履历导出接口

#### GET /api/pm/modules/:id/version-history/export
导出模块版本履历为 CSV

**Response**: `Content-Type: text/csv`
```csv
version,operator,time,change_detail
2.1.0,张三,2026-07-08T10:30:00Z,初始创建
2.2.0,张三,2026-07-08T11:00:00Z,修改了名称、描述字段
```

### 5. 思维导图数据接口

#### GET /api/pm/architecture/mindmap
获取思维导图树形数据

**Response**:
```json
{
  "data": {
    "id": "root",
    "name": "产品架构",
    "children": [
      {
        "id": "module-uuid",
        "name": "用户管理",
        "type": "module",
        "children": [
          {
            "id": "function-uuid",
            "name": "用户注册",
            "type": "function",
            "children": [
              {
                "id": "parameter-uuid",
                "name": "用户名",
                "type": "parameter"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

## 错误码定义

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | INVALID_KEY | key 格式不合法 |
| 400 | DUPLICATE_KEY | key 已存在 |
| 400 | INVALID_DATA_TYPE | data_type 不在枚举范围内 |
| 404 | MODULE_NOT_FOUND | 模块不存在 |
| 404 | FUNCTION_NOT_FOUND | 功能不存在 |
| 404 | PARAMETER_NOT_FOUND | 参数不存在 |
| 409 | MODULE_HAS_FUNCTIONS | 模块下存在功能，不能删除 |
| 409 | FUNCTION_HAS_PARAMETERS | 功能下存在参数，不能删除 |

## 通用响应格式

### 成功响应

```json
{
  "data": { ... }
}
```

### 错误响应

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": { ... }
  }
}
```

## 数据验证规则

### 创建/编辑请求

| 字段 | 必填 | 类型 | 约束 |
|------|------|------|------|
| name | 是 | string | 1-100 字符 |
| key | 是 | string | 字母/数字/下划线，1-50 字符 |
| data_type | 是 | string | string/number/boolean/array/object |
| required | 是 | boolean | - |
| description | 否 | string | 最大 500 字符 |
| demand_relation | 否 | array | 每项包含 demand_id/demand_name/doc_link |

### 版本号规则

- 自动回填当前工作台版本
- 若工作台版本为空，使用系统当前版本
- 若系统版本也为空，使用默认值 "1.0.0"