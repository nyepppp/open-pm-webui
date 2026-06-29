# PM 工作流平台 - API 设计

## 基于 Agent Native Actions

**版本**: v1.0  
**日期**: 2026-06-27

---

## 1. Action 命名规范

```
{模块}.{操作}

模块命名:
- project          # 项目
- workflow         # 工作流
- version          # 版本
- relation         # 关系/追溯
- requirement      # 需求收集
- competitor       # 竞品分析
- roadmap          # 产品路线图
- prd              # PRD 编辑
- prd-check        # PRD 检查
- prototype        # 原型走查
- parameter        # 参数清单
- prototype-prompt # 原型提示词
- testcase         # 测试用例
- project-init     # 立项
- schedule         # 排期
- meeting          # 评审纪要
- risk             # 风险管控
- deliverable      # 交付物料
- acceptance       # 验收
- issue            # 问题闭环
- report           # 数据分析
- retrospective    # 版本复盘
- iteration        # 优化迭代
- training         # 培训素材
- manual           # 操作手册
- faq              # FAQ
- presentation     # 宣讲材料
- agent            # Agent 核心
- setting          # 设置
```

---

## 2. 通用响应格式

```typescript
// 成功响应
interface SuccessResponse<T> {
  success: true;
  data: T;
  meta?: {
    total?: number;
    page?: number;
    pageSize?: number;
  };
}

// 错误响应
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

type ApiResponse<T> = SuccessResponse<T> | ErrorResponse;
```

---

## 3. 核心模块 API

### 3.1 Project 模块

#### project.create
```typescript
// actions/project/create.ts
import { defineAction } from "@agent-native/core/action";
import { z } from "zod";

export default defineAction({
  description: "创建新项目",
  schema: z.object({
    name: z.string().min(1).max(100).describe("项目名称"),
    description: z.string().optional().describe("项目描述"),
    type: z.enum(["prd", "competitor", "general"]).default("general"),
    templateId: z.string().optional().describe("模板ID"),
  }),
  http: { method: "POST" },
  run: async ({ name, description, type, templateId }, ctx) => {
    // 实现...
    return { id: "proj-xxx", name, type, status: "active" };
  },
});
```

#### project.list
```typescript
export default defineAction({
  description: "获取项目列表",
  schema: z.object({
    status: z.enum(["active", "archived", "deleted"]).optional(),
    type: z.string().optional(),
    search: z.string().optional(),
    page: z.number().default(1),
    pageSize: z.number().default(20),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ status, type, search, page, pageSize }) => {
    // 实现...
    return { items: [], total: 0 };
  },
});
```

#### project.get
```typescript
export default defineAction({
  description: "获取项目详情",
  schema: z.object({
    id: z.string().describe("项目ID"),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ id }) => {
    // 实现...
    return { id, name, description, type, status };
  },
});
```

#### project.update
```typescript
export default defineAction({
  description: "更新项目",
  schema: z.object({
    id: z.string(),
    name: z.string().optional(),
    description: z.string().optional(),
    status: z.string().optional(),
  }),
  http: { method: "POST" },
  run: async ({ id, ...data }) => {
    // 实现...
    return { id, ...data };
  },
});
```

#### project.delete
```typescript
export default defineAction({
  description: "删除项目（进入回收站）",
  schema: z.object({
    id: z.string(),
    permanent: z.boolean().default(false).describe("是否永久删除"),
  }),
  http: { method: "POST" },
  needsApproval: (args) => args.permanent,
  run: async ({ id, permanent }) => {
    // 实现...
    return { id, deleted: true };
  },
});
```

#### project.export
```typescript
export default defineAction({
  description: "导出项目",
  schema: z.object({
    id: z.string(),
    includeFiles: z.boolean().default(true),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ id, includeFiles }) => {
    // 实现...
    return { downloadUrl: "/path/to/export.zip" };
  },
});
```

#### project.import
```typescript
export default defineAction({
  description: "导入项目",
  schema: z.object({
    file: z.string().describe("项目文件路径"),
  }),
  http: { method: "POST" },
  run: async ({ file }) => {
    // 实现...
    return { id: "proj-xxx", name: "导入的项目" };
  },
});
```

---

### 3.2 Workflow 模块

#### workflow.create
```typescript
export default defineAction({
  description: "创建工作流",
  schema: z.object({
    projectId: z.string(),
    name: z.string().default("默认工作流"),
    templateId: z.string().optional(),
  }),
  http: { method: "POST" },
  run: async ({ projectId, name, templateId }) => {
    // 实现...
    return { id: "wf-xxx", projectId, name, steps: [] };
  },
});
```

#### workflow.get
```typescript
export default defineAction({
  description: "获取工作流详情",
  schema: z.object({
    id: z.string(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ id }) => {
    // 实现...
    return { id, name, steps: [] };
  },
});
```

#### workflow.step.update
```typescript
export default defineAction({
  description: "更新工作流步骤",
  schema: z.object({
    workflowId: z.string(),
    stepId: z.string(),
    status: z.enum(["pending", "in_progress", "completed", "blocked", "skipped"]).optional(),
    data: z.any().optional(), // 步骤数据
    nextSteps: z.array(z.string()).optional(),
  }),
  http: { method: "POST" },
  run: async ({ workflowId, stepId, status, data, nextSteps }) => {
    // 实现...
    return { workflowId, stepId, updated: true };
  },
});
```

#### workflow.step.add
```typescript
export default defineAction({
  description: "添加工作流步骤",
  schema: z.object({
    workflowId: z.string(),
    step: z.object({
      name: z.string(),
      category: z.string(),
      deliverables: z.array(z.string()).optional(),
    }),
    position: z.number().optional(), // 插入位置
  }),
  http: { method: "POST" },
  run: async ({ workflowId, step, position }) => {
    // 实现...
    return { workflowId, stepId: "step-xxx", added: true };
  },
});
```

#### workflow.step.remove
```typescript
export default defineAction({
  description: "删除工作流步骤",
  schema: z.object({
    workflowId: z.string(),
    stepId: z.string(),
  }),
  http: { method: "POST" },
  needsApproval: true,
  run: async ({ workflowId, stepId }) => {
    // 实现...
    return { workflowId, stepId, removed: true };
  },
});
```

#### workflow.next
```typescript
export default defineAction({
  description: "获取建议的下一步",
  schema: z.object({
    workflowId: z.string(),
    currentStepId: z.string().optional(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ workflowId, currentStepId }) => {
    // 实现...
    return { suggestions: [] };
  },
});
```

---

### 3.3 Versioning 模块

#### version.create
```typescript
export default defineAction({
  description: "创建版本",
  schema: z.object({
    projectId: z.string(),
    versionNumber: z.string().regex(/^v\d+\.\d+$/),
    description: z.string(),
    label: z.string().optional(),
  }),
  http: { method: "POST" },
  run: async ({ projectId, versionNumber, description, label }) => {
    // 实现...
    return { id: "ver-xxx", projectId, versionNumber };
  },
});
```

#### version.list
```typescript
export default defineAction({
  description: "获取版本列表",
  schema: z.object({
    projectId: z.string(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ projectId }) => {
    // 实现...
    return { items: [] };
  },
});
```

#### version.compare
```typescript
export default defineAction({
  description: "对比两个版本",
  schema: z.object({
    versionA: z.string(),
    versionB: z.string(),
    entityType: z.string().optional(), // "document" | "requirement" | "parameter"
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ versionA, versionB, entityType }) => {
    // 实现...
    return { diff: [] };
  },
});
```

#### version.rollback
```typescript
export default defineAction({
  description: "回滚到指定版本",
  schema: z.object({
    id: z.string(),
  }),
  http: { method: "POST" },
  needsApproval: true,
  run: async ({ id }) => {
    // 实现...
    return { newVersionId: "ver-xxx", message: "已回滚并创建新版本" };
  },
});
```

---

### 3.4 Traceability 模块

#### relation.create
```typescript
export default defineAction({
  description: "创建实体关联",
  schema: z.object({
    projectId: z.string(),
    entityAId: z.string(),
    entityBId: z.string(),
    relationType: z.enum(["contains", "references", "derives", "modifies", "conflicts"]),
    confirmed: z.boolean().default(true),
  }),
  http: { method: "POST" },
  run: async ({ projectId, entityAId, entityBId, relationType, confirmed }) => {
    // 实现...
    return { id: "rel-xxx", created: true };
  },
});
```

#### relation.list
```typescript
export default defineAction({
  description: "获取关联列表",
  schema: z.object({
    projectId: z.string(),
    entityId: z.string().optional(),
    relationType: z.string().optional(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ projectId, entityId, relationType }) => {
    // 实现...
    return { items: [] };
  },
});
```

#### relation.impact
```typescript
export default defineAction({
  description: "影响分析",
  schema: z.object({
    entityId: z.string(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ entityId }) => {
    // 实现...
    return { affectedEntities: [] };
  },
});
```

#### relation.trace
```typescript
export default defineAction({
  description: "追溯链路",
  schema: z.object({
    entityId: z.string(),
    direction: z.enum(["upstream", "downstream", "both"]).default("both"),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ entityId, direction }) => {
    // 实现...
    return { chain: [] };
  },
});
```

---

## 4. 业务模块 API

### 4.1 需求收集

#### requirement.create
```typescript
export default defineAction({
  description: "创建需求",
  schema: z.object({
    projectId: z.string(),
    title: z.string(),
    description: z.string().optional(),
    priority: z.enum(["p0", "p1", "p2", "p3"]).default("p2"),
    tags: z.array(z.string()).default([]),
    category: z.string().optional(),
  }),
  http: { method: "POST" },
  run: async (args) => {
    // 实现...
    return { id: "req-xxx", ...args };
  },
});
```

#### requirement.import
```typescript
export default defineAction({
  description: "从 Excel 导入需求",
  schema: z.object({
    projectId: z.string(),
    file: z.string().describe("Excel 文件路径"),
  }),
  http: { method: "POST" },
  run: async ({ projectId, file }) => {
    // 实现...
    return { imported: 10, items: [] };
  },
});
```

#### requirement.analyze
```typescript
export default defineAction({
  description: "AI 分析需求分类",
  schema: z.object({
    projectId: z.string(),
  }),
  http: { method: "POST" },
  readOnly: true,
  run: async ({ projectId }) => {
    // 实现...
    return { categories: [], suggestions: [] };
  },
});
```

---

### 4.2 PRD 编辑

#### prd.create
```typescript
export default defineAction({
  description: "创建 PRD",
  schema: z.object({
    projectId: z.string(),
    title: z.string(),
    template: z.string().default("standard"),
  }),
  http: { method: "POST" },
  run: async ({ projectId, title, template }) => {
    // 实现...
    return { id: "prd-xxx", projectId, title, sections: [] };
  },
});
```

#### prd.update
```typescript
export default defineAction({
  description: "更新 PRD",
  schema: z.object({
    id: z.string(),
    content: z.string().optional(),
    sections: z.array(z.any()).optional(),
  }),
  http: { method: "POST" },
  run: async ({ id, content, sections }) => {
    // 实现...
    return { id, updated: true };
  },
});
```

#### prd.generate
```typescript
export default defineAction({
  description: "AI 生成 PRD 初稿",
  schema: z.object({
    projectId: z.string(),
    requirements: z.array(z.string()).optional(),
    prompt: z.string().optional(),
  }),
  http: { method: "POST" },
  readOnly: true,
  run: async ({ projectId, requirements, prompt }) => {
    // 实现...
    return { draft: "# PRD 初稿\n..." };
  },
});
```

#### prd.export
```typescript
export default defineAction({
  description: "导出 PRD",
  schema: z.object({
    id: z.string(),
    format: z.enum(["markdown", "html", "docx"]).default("markdown"),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ id, format }) => {
    // 实现...
    return { downloadUrl: "/path/to/export.md" };
  },
});
```

---

### 4.3 PRD 检查

#### prd-check.run
```typescript
export default defineAction({
  description: "执行 PRD 检查",
  schema: z.object({
    prdId: z.string(),
    level: z.enum(["l1", "l2", "l3", "l4"]).default("l2"),
  }),
  http: { method: "POST" },
  run: async ({ prdId, level }) => {
    // 实现...
    return { checks: [], passed: 0, failed: 0 };
  },
});
```

#### prd-check.list
```typescript
export default defineAction({
  description: "获取检查结果",
  schema: z.object({
    prdId: z.string(),
    status: z.string().optional(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ prdId, status }) => {
    // 实现...
    return { items: [] };
  },
});
```

---

### 4.4 参数清单

#### parameter.create
```typescript
export default defineAction({
  description: "创建参数",
  schema: z.object({
    projectId: z.string(),
    name: z.string(),
    key: z.string(),
    paramType: z.enum(["input", "output", "config"]),
    dataType: z.enum(["string", "number", "boolean", "object", "array"]),
    required: z.boolean().default(true),
    moduleId: z.string().optional(),
    featureId: z.string().optional(),
    flowNode: z.string().optional(),
    description: z.string().optional(),
  }),
  http: { method: "POST" },
  run: async (args) => {
    // 实现...
    return { id: "param-xxx", ...args };
  },
});
```

#### parameter.extract
```typescript
export default defineAction({
  description: "从 PRD 提取参数",
  schema: z.object({
    prdId: z.string(),
  }),
  http: { method: "POST" },
  readOnly: true,
  run: async ({ prdId }) => {
    // 实现...
    return { extracted: [], suggestions: [] };
  },
});
```

#### parameter.config
```typescript
export default defineAction({
  description: "生成配置清单",
  schema: z.object({
    projectId: z.string(),
    moduleId: z.string().optional(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ projectId, moduleId }) => {
    // 实现...
    return { config: {} };
  },
});
```

---

### 4.5 原型走查

#### prototype.screen.upload
```typescript
export default defineAction({
  description: "上传原型截图",
  schema: z.object({
    projectId: z.string(),
    file: z.string(),
    name: z.string(),
  }),
  http: { method: "POST" },
  run: async ({ projectId, file, name }) => {
    // 实现...
    return { id: "screen-xxx", projectId, name };
  },
});
```

#### prototype.analyze
```typescript
export default defineAction({
  description: "AI 分析原型",
  schema: z.object({
    screenId: z.string(),
  }),
  http: { method: "POST" },
  readOnly: true,
  run: async ({ screenId }) => {
    // 实现...
    return { issues: [], suggestions: [] };
  },
});
```

---

### 4.6 测试用例

#### testcase.generate
```typescript
export default defineAction({
  description: "AI 生成测试用例",
  schema: z.object({
    prdId: z.string(),
    parameterId: z.string().optional(),
  }),
  http: { method: "POST" },
  readOnly: true,
  run: async ({ prdId, parameterId }) => {
    // 实现...
    return { testcases: [] };
  },
});
```

---

### 4.7 风险管控

#### risk.create
```typescript
export default defineAction({
  description: "创建风险",
  schema: z.object({
    projectId: z.string(),
    description: z.string(),
    probability: z.number().min(1).max(5),
    impact: z.number().min(1).max(5),
    measures: z.string().optional(),
    owner: z.string().optional(),
  }),
  http: { method: "POST" },
  run: async (args) => {
    // 实现...
    return { id: "risk-xxx", level: "medium", ...args };
  },
});
```

#### risk.matrix
```typescript
export default defineAction({
  description: "获取风险矩阵",
  schema: z.object({
    projectId: z.string(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ projectId }) => {
    // 实现...
    return { matrix: [] };
  },
});
```

---

### 4.8 问题闭环

#### issue.create
```typescript
export default defineAction({
  description: "创建问题",
  schema: z.object({
    projectId: z.string(),
    title: z.string(),
    description: z.string(),
    source: z.enum(["review", "test", "acceptance", "user_feedback", "manual"]),
    priority: z.enum(["p0", "p1", "p2", "p3"]).default("p2"),
    requirementId: z.string().optional(),
    testcaseId: z.string().optional(),
  }),
  http: { method: "POST" },
  run: async (args) => {
    // 实现...
    return { id: "issue-xxx", status: "new", ...args };
  },
});
```

#### issue.link
```typescript
export default defineAction({
  description: "关联需求",
  schema: z.object({
    issueId: z.string(),
    requirementId: z.string(),
  }),
  http: { method: "POST" },
  run: async ({ issueId, requirementId }) => {
    // 实现...
    return { linked: true };
  },
});
```

---

### 4.9 Agent 核心

#### agent.chat
```typescript
export default defineAction({
  description: "与 AI 助手对话",
  schema: z.object({
    message: z.string(),
    context: z.any().optional(), // 当前上下文
    threadId: z.string().optional(),
  }),
  http: { method: "POST" },
  readOnly: true,
  run: async ({ message, context, threadId }) => {
    // 实现...
    return { response: "", actions: [] };
  },
});
```

#### agent.intent
```typescript
export default defineAction({
  description: "识别用户意图",
  schema: z.object({
    message: z.string(),
  }),
  http: { method: "POST" },
  readOnly: true,
  run: async ({ message }) => {
    // 实现...
    return { intent: "prd_generate", confidence: 0.95 };
  },
});
```

#### agent.config
```typescript
export default defineAction({
  description: "配置 AI",
  schema: z.object({
    provider: z.enum(["openai", "anthropic", "local"]),
    apiKey: z.string().optional(),
    model: z.string().optional(),
    baseUrl: z.string().optional(),
  }),
  http: { method: "POST" },
  needsApproval: true,
  run: async ({ provider, apiKey, model, baseUrl }) => {
    // 实现...
    return { configured: true };
  },
});
```

---

## 5. 设置模块

#### setting.get
```typescript
export default defineAction({
  description: "获取设置",
  schema: z.object({
    key: z.string(),
  }),
  http: { method: "GET" },
  readOnly: true,
  run: async ({ key }) => {
    // 实现...
    return { key, value: null };
  },
});
```

#### setting.set
```typescript
export default defineAction({
  description: "设置配置",
  schema: z.object({
    key: z.string(),
    value: z.any(),
  }),
  http: { method: "POST" },
  run: async ({ key, value }) => {
    // 实现...
    return { key, value };
  },
});
```

---

## 6. 前端调用示例

### 6.1 React Query

```typescript
import { useActionQuery, useActionMutation } from "@agent-native/core/client";

// 查询项目列表
function useProjects(status?: string) {
  return useActionQuery("project.list", { status, page: 1, pageSize: 20 });
}

// 创建项目
function useCreateProject() {
  return useActionMutation("project.create");
}

// 使用
function ProjectList() {
  const { data, isLoading } = useProjects("active");
  const createProject = useCreateProject();
  
  const handleCreate = () => {
    createProject.mutate({ name: "新项目", type: "general" });
  };
  
  return (
    <div>
      {data?.items.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
      <button onClick={handleCreate}>创建项目</button>
    </div>
  );
}
```

### 6.2 直接调用

```typescript
import { callAction } from "@agent-native/core/client";

// 直接调用 action
const result = await callAction("project.get", { id: "proj-xxx" });
console.log(result.data);
```

### 6.3 Agent 交互

```typescript
import { sendToAgentChat } from "@agent-native/core/client";

// 发送消息给 Agent
function handleAskAgent() {
  sendToAgentChat("帮我生成一份登录功能的 PRD");
}
```

---

## 7. HTTP 端点

所有 Action 自动暴露为 HTTP 端点：

```
POST /_agent-native/actions/project.create
GET  /_agent-native/actions/project.list
GET  /_agent-native/actions/project.get?id=xxx
POST /_agent-native/actions/project.update
POST /_agent-native/actions/project.delete
POST /_agent-native/actions/project.export
POST /_agent-native/actions/project.import

POST /_agent-native/actions/prd.create
POST /_agent-native/actions/prd.update
GET  /_agent-native/actions/prd.get?id=xxx
POST /_agent-native/actions/prd.generate
GET  /_agent-native/actions/prd.export?id=xxx&format=markdown

POST /_agent-native/actions/prd-check.run
GET  /_agent-native/actions/prd-check.list?prdId=xxx

POST /_agent-native/actions/agent.chat
POST /_agent-native/actions/agent.config

... 其他 Action 同理
```

---

## 8. 错误码

| 错误码 | 说明 | HTTP 状态 |
|--------|------|-----------|
| `NOT_FOUND` | 资源不存在 | 404 |
| `VALIDATION_ERROR` | 参数校验失败 | 400 |
| `UNAUTHORIZED` | 未授权 | 401 |
| `FORBIDDEN` | 禁止访问 | 403 |
| `CONFLICT` | 资源冲突 | 409 |
| `INTERNAL_ERROR` | 内部错误 | 500 |
| `AI_UNAVAILABLE` | AI 服务不可用 | 503 |
| `PROJECT_NOT_FOUND` | 项目不存在 | 404 |
| `VERSION_EXISTS` | 版本已存在 | 409 |
| `RELATION_EXISTS` | 关联已存在 | 409 |

---

**文档结束**
