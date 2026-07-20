# Skill Invocation Contract

**Date**: 2026-07-11
**Feature**: PM Skills Integration (003)

---

## Overview

定义工作流调用 pm-skills 的接口契约。

---

## Request

### Explicit Invocation

```typescript
interface SkillInvokeRequest {
  project_id: string;
  skill_id: string;        // 格式: "pm-skills/<command-id>"
  args?: Record<string, unknown>;
}
```

### Workflow Binding

```typescript
interface WorkflowSkillBinding {
  workflow_id: string;
  skill_id: string;        // 格式: "pm-skills/<command-id>"
  input_bindings: Record<string, string>;   // 映射工作流输入到 skill 输入
  output_bindings: Record<string, string>; // 映射 skill 输出到工作流输出
}
```

---

## Response

```typescript
interface SkillInvokeResponse {
  invocation_id: string;
  skill_id: string;
  status: 'pending' | 'confirmed' | 'rejected' | 'failed';
  output?: Record<string, unknown>;
  requires_confirm: boolean;
  error?: string;
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| SKILL_NOT_FOUND | skill_id 不存在于注册表 |
| SKILL_DISABLED | skill 存在但未启用 |
| INVALID_INPUT | 输入参数不符合 inputSchema |
| OUTPUT_VALIDATION_FAILED | 输出不符合 outputContract |
| PROJECT_NOT_BOUND | 未绑定 project_id |
