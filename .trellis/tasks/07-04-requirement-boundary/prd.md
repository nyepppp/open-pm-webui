# 需求边界表单模块 Agent 接入

**父任务**: 07-04-open-webui-agent-integration
**日期**: 2026-07-04
**状态**: 实现中

---

## Goal

将需求边界（requirement-boundary）模块接入 Agent Tool 体系，使 AI 可通过对话管理需求边界条目（场景、功能、使用方式、预期效果、关联需求/参数）。

## Background

前端已有需求边界模块定义（`moduleFields.ts` 的 `requirementBoundaryFields`），包含 6 个字段：scenario、function、usage、expectedEffect、relatedRequirements、relatedParameters。前端使用表格视图（editorType: 'table'）。当前无后端 Tool callable 覆盖此模块。

## Requirements

### R1: 需求边界 CRUD Tool

在现有 `pm_entry_tool.py` 中添加需求边界专用 callable，或创建独立 tool。由于需求边界使用通用 entries API（module_type="requirement-boundary"），无需新路由端点。

| Callable | 描述 |
|----------|------|
| `list_requirement_boundaries` | 列出项目的需求边界条目 |
| `create_requirement_boundary` | 创建需求边界条目（需确认） |
| `update_requirement_boundary` | 更新需求边界条目（需确认） |

### R2: 字段映射

PM entry 的 `data` 字段存储需求边界结构化数据：

```python
data = {
    "scenario": "用户登录场景",
    "function": "支持手机号+验证码登录",
    "usage": "用户打开App→点击登录→输入手机号→获取验证码→登录成功",
    "expectedEffect": "3秒内完成登录流程",
    "relatedRequirements": "req_id_1,req_id_2",
    "relatedParameters": "param_id_1"
}
```

### R3: 确认流程

创建和更新操作使用 `__event_call__` 确认，展示场景和功能摘要。

## Acceptance Criteria

- [ ] `list_requirement_boundaries` callable 可返回需求边界列表
- [ ] `create_requirement_boundary` callable 支持所有 6 个字段 + 确认
- [ ] `update_requirement_boundary` callable 支持部分更新 + 确认
- [ ] 数据通过 entries API 存储（module_type="requirement-boundary"）
