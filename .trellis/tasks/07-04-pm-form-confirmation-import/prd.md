# 表单确认与数据导入

**父任务**: 07-04-open-webui-agent-integration  
**日期**: 2026-07-04  
**状态**: 规划中

---

## Goal

实现 PM Tool 的表单确认流程（`__event_call__` 确认 + `input` 收集）和数据导入功能，使 AI 生成内容经用户确认后写入 PM 系统。

## Requirements

### R1: 简单确认流程

写入操作（create/update/delete）执行前，通过 `__event_call__` 的 `confirmation` 类型请求用户确认：

```python
confirmed = await __event_call__({
    "type": "confirmation",
    "data": {
        "title": "确认创建需求",
        "message": "标题: 用户登录\n优先级: P2\n\n确认创建？"
    }
})
if not confirmed:
    return "用户取消了操作"
```

### R2: 参数收集流程

复杂创建操作通过多次 `input` 逐步收集参数 + 最终 `confirmation` 确认：

```python
# 步骤1: 收集标题
title_result = await __event_call__({
    "type": "input",
    "data": {"title": "需求标题", "message": "请输入需求标题", "placeholder": "例如：用户登录功能"}
})
# 步骤2: 收集优先级
priority_result = await __event_call__({
    "type": "input",
    "data": {"title": "优先级", "message": "请选择优先级（P0-P3）", "placeholder": "P2"}
})
# 步骤3: 最终确认
confirmed = await __event_call__({
    "type": "confirmation",
    "data": {"title": "确认创建", "message": f"标题: {title}\n优先级: {priority}\n确认？"}
})
```

### R3: 预览确认流程

AI 生成内容（PRD、参数清单等）先展示，用户确认后调用写入 Tool：

```python
# AI 生成内容
content = "生成的 PRD 内容..."
# 展示给用户
await __event_emitter__({"type": "message", "data": {"content": content}})
# 确认后写入
confirmed = await __event_call__({
    "type": "confirmation",
    "data": {"title": "确认写入 PRD", "message": "以上 PRD 内容将写入项目。确认？"}
})
if confirmed:
    await pm_prd_create(project_id, title, content)
```

### R4: 数据导入

- 支持从 Knowledge Base 选择 PM 文档数据导入
- 支持从 Excel/CSV 文件导入（调用 `pm_import` Tool）
- 导入前展示预览数据（行数、列名、示例行）
- 导入前通过 `confirmation` 确认

### R5: Native Mode 兼容

- 所有确认流程需兼容 Native Function Calling Mode
- Native Mode 下不使用 `message` 事件，只使用 `status` + `confirmation`/`input`
- 结果通过 return value 返回

## Dependencies

- 依赖 `07-04-pm-tool-registration`：确认流程是 Tool callable 函数的一部分
- 依赖 `07-04-pm-backend-api`：导入 API 端点需先完善

## Acceptance Criteria

- [ ] 写入操作（create/update/delete）有 confirmation 确认步骤
- [ ] 复杂表单支持 input 逐步收集参数
- [ ] AI 生成内容有预览确认步骤
- [ ] 数据导入有预览 + 确认步骤
- [ ] 所有确认流程兼容 Native Mode
- [ ] 用户取消操作后不写入数据
