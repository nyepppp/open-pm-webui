# PM 工作流平台 - 数据库设计

## 基于 Drizzle ORM + SQLite

**版本**: v1.0  
**日期**: 2026-06-27

---

## 1. 核心表

### 1.1 项目表 (projects)

```typescript
import { table, text, integer, json } from "@agent-native/core/db/schema";

export const projects = table("projects", {
  id: text("id").primaryKey(),
  name: text("name").notNull().unique(),
  description: text("description"),
  type: text("type").notNull(), // "prd" | "competitor" | "general"
  status: text("status").notNull().default("active"), // "active" | "archived" | "deleted"
  config: json("config"), // { apiProvider, apiKey?, model?, baseUrl? }
  templateId: text("template_id"),
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
  deletedAt: integer("deleted_at"), // 软删除
});
```

**索引**:
- `idx_projects_status` on `status`
- `idx_projects_type` on `type`

---

### 1.2 项目模板表 (project_templates)

```typescript
export const projectTemplates = table("project_templates", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  type: text("type").notNull(),
  description: text("description"),
  defaultModules: json("default_modules").notNull(), // string[]
  defaultDocs: json("default_docs"), // { name, type }[]
  workflowTemplate: json("workflow_template"), // WorkflowStep[]
  isBuiltin: integer("is_builtin").default(1), // 0 | 1
  createdAt: integer("created_at").notNull(),
});
```

---

### 1.3 版本表 (versions)

```typescript
export const versions = table("versions", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  versionNumber: text("version_number").notNull(), // "v1.0"
  label: text("label"), // "milestone" | "release" | "review"
  description: text("description").notNull(),
  snapshotPath: text("snapshot_path").notNull(),
  createdBy: text("created_by"),
  createdAt: integer("created_at").notNull(),
});
```

**索引**:
- `idx_versions_project_id` on `project_id`
- `idx_versions_version_number` on `project_id`, `version_number`

---

### 1.4 工作流表 (workflows)

```typescript
export const workflows = table("workflows", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  templateId: text("template_id"),
  status: text("status").notNull().default("draft"), // "draft" | "active" | "completed" | "archived"
  steps: json("steps").notNull(), // WorkflowStep[]
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});
```

**WorkflowStep 结构**:

```typescript
interface WorkflowStep {
  id: string;
  name: string;
  category: string; // "planning" | "design" | "management" | "acceptance" | "review" | "enablement"
  status: "pending" | "in_progress" | "completed" | "blocked" | "skipped";
  deliverables: string[]; // 关联文档/表格 ID
  aiExtractedData?: any;
  manualData?: any;
  nextSteps: string[];
  order: number;
  isCustom: boolean;
  createdAt: number;
  completedAt?: number;
}
```

---

### 1.5 实体表 (entities)

```typescript
export const entities = table("entities", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  type: text("type").notNull(), // "requirement" | "module" | "feature" | "parameter" | "document" | "version" | "operation"
  name: text("name").notNull(),
  moduleId: text("module_id"),
  featureId: text("feature_id"),
  metadata: json("metadata"),
  createdAt: integer("created_at").notNull(),
});
```

**索引**:
- `idx_entities_project_id` on `project_id`
- `idx_entities_type` on `type`

---

### 1.6 关系表 (relations)

```typescript
export const relations = table("relations", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  entityAId: text("entity_a_id").notNull().references(() => entities.id),
  entityBId: text("entity_b_id").notNull().references(() => entities.id),
  relationType: text("relation_type").notNull(), // "contains" | "references" | "derives" | "modifies" | "conflicts"
  confidence: integer("confidence"), // 0-100
  confirmed: integer("confirmed").notNull().default(0), // 0 | 1
  createdBy: text("created_by"), // "ai" | "user"
  createdAt: integer("created_at").notNull(),
});
```

**索引**:
- `idx_relations_project_id` on `project_id`
- `idx_relations_entity_a` on `entity_a_id`
- `idx_relations_entity_b` on `entity_b_id`

---

## 2. 规划类表

### 2.1 需求表 (requirements)

```typescript
export const requirements = table("requirements", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  versionId: text("version_id").references(() => versions.id),
  title: text("title").notNull(),
  description: text("description"),
  source: text("source").default("manual"), // "manual" | "excel" | "agent"
  priority: text("priority").default("p2"), // "p0" | "p1" | "p2" | "p3"
  status: text("status").default("open"), // "open" | "in_progress" | "resolved" | "closed"
  tags: json("tags").default("[]"),
  category: text("category"),
  moduleId: text("module_id"), // 所属模块
  featureId: text("feature_id"), // 所属功能
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});
```

**索引**:
- `idx_requirements_project_id` on `project_id`
- `idx_requirements_status` on `status`
- `idx_requirements_priority` on `priority`

---

### 2.2 竞品表 (competitors)

```typescript
export const competitors = table("competitors", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  url: text("url"),
  description: text("description"),
  logo: text("logo"), // 图片路径
  createdAt: integer("created_at").notNull(),
});
```

### 2.3 竞品分析表 (competitor_analysis)

```typescript
export const competitorAnalysis = table("competitor_analysis", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  competitorId: text("competitor_id").notNull().references(() => competitors.id),
  dimension: text("dimension").notNull(), // 分析维度
  ourProduct: text("our_product"),
  competitorProduct: text("competitor_product"),
  analysis: text("analysis"),
  score: integer("score"), // 评分 1-5
  createdAt: integer("created_at").notNull(),
});
```

### 2.4 路线图节点表 (roadmap_nodes)

```typescript
export const roadmapNodes = table("roadmap_nodes", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  versionId: text("version_id").references(() => versions.id),
  name: text("name").notNull(),
  type: text("type").notNull(), // "milestone" | "feature" | "release"
  status: text("status").default("planned"), // "planned" | "in_progress" | "completed" | "delayed"
  startDate: integer("start_date"),
  endDate: integer("end_date"),
  dependencies: json("dependencies").default("[]"), // string[]
  order: integer("order").notNull(),
  createdAt: integer("created_at").notNull(),
});
```

---

## 3. 需求设计类表

### 3.1 PRD 文档表 (prd_documents)

```typescript
export const prdDocuments = table("prd_documents", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  versionId: text("version_id").references(() => versions.id),
  title: text("title").notNull(),
  content: text("content").notNull(), // Markdown/JSON
  sections: json("sections").notNull(), // PRDSection[]
  status: text("status").default("draft"), // "draft" | "review" | "approved" | "archived"
  template: text("template").default("standard"),
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});
```

### 3.2 PRD 章节嵌入参数表 (prd_embedded_parameters)

```typescript
export const prdEmbeddedParameters = table("prd_embedded_parameters", {
  id: text("id").primaryKey(),
  prdId: text("prd_id").notNull().references(() => prdDocuments.id),
  sectionId: text("section_id").notNull(),
  parameterId: text("parameter_id").notNull().references(() => parameters.id),
  position: integer("position"), // 在章节中的位置
  createdAt: integer("created_at").notNull(),
});
```

### 3.3 PRD 检查表 (prd_checks)

```typescript
export const prdChecks = table("prd_checks", {
  id: text("id").primaryKey(),
  prdId: text("prd_id").notNull().references(() => prdDocuments.id),
  level: text("level").notNull(), // "l1" | "l2" | "l3" | "l4"
  ruleId: text("rule_id").notNull(),
  ruleDescription: text("rule_description").notNull(),
  status: text("status").default("pending"), // "pending" | "pass" | "fail" | "ignored"
  location: text("location"), // 问题位置
  suggestion: text("suggestion"),
  createdAt: integer("created_at").notNull(),
});
```

### 3.4 检查规则库表 (check_rules)

```typescript
export const checkRules = table("check_rules", {
  id: text("id").primaryKey(),
  level: text("level").notNull(),
  category: text("category").notNull(), // "content_existence" | "logic_completeness" | "consistency" | "ux_heuristic" | "accessibility" | "security"
  description: text("description").notNull(),
  checkType: text("check_type").notNull(),
  example: text("example"), // 示例
  isBuiltin: integer("is_builtin").default(1),
  createdAt: integer("created_at").notNull(),
});
```

### 3.5 原型截图表 (prototype_screens)

```typescript
export const prototypeScreens = table("prototype_screens", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  imagePath: text("image_path").notNull(),
  annotations: json("annotations").default("[]"), // Annotation[]
  checkStatus: text("check_status").default("pending"),
  createdAt: integer("created_at").notNull(),
});
```

**Annotation 结构**:

```typescript
interface Annotation {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
  type: "circle" | "rect" | "arrow";
  color: string;
}
```

### 3.6 原型检查表 (prototype_checks)

```typescript
export const prototypeChecks = table("prototype_checks", {
  id: text("id").primaryKey(),
  screenId: text("screen_id").notNull().references(() => prototypeScreens.id),
  checkItemId: text("check_item_id").notNull(),
  status: text("status").default("pending"), // "pending" | "pass" | "fail" | "na"
  issue: text("issue"),
  annotationId: text("annotation_id"),
  createdAt: integer("created_at").notNull(),
});
```

### 3.7 参数表 (parameters)

```typescript
export const parameters = table("parameters", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(), // 中文名称
  key: text("key").notNull(), // 英文标识
  moduleId: text("module_id"), // 所属模块
  featureId: text("feature_id"), // 所属功能
  paramType: text("param_type").notNull(), // "input" | "output" | "config"
  dataType: text("data_type").notNull(), // "string" | "number" | "boolean" | "object" | "array"
  required: integer("required").default(1), // 0 | 1
  defaultValue: text("default_value"),
  description: text("description"),
  flowNode: text("flow_node"), // 流程节点
  sourceDocument: text("source_document"), // 来源 PRD ID
  version: text("version"), // 引入版本
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});
```

### 3.8 原型提示词表 (prototype_prompts)

```typescript
export const prototypePrompts = table("prototype_prompts", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  featureId: text("feature_id"),
  name: text("name").notNull(),
  prompt: text("prompt").notNull(),
  template: text("template"),
  createdAt: integer("created_at").notNull(),
});
```

### 3.9 测试用例表 (testcases)

```typescript
export const testcases = table("testcases", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  moduleId: text("module_id"),
  featureId: text("feature_id"),
  scenario: text("scenario").notNull(),
  precondition: text("precondition"),
  steps: text("steps").notNull(),
  inputData: text("input_data"),
  expectedResult: text("expected_result").notNull(),
  priority: text("priority").default("p2"),
  caseType: text("case_type").default("functional"),
  requirementId: text("requirement_id").references(() => requirements.id),
  parameterId: text("parameter_id").references(() => parameters.id),
  status: text("status").default("pending"),
  actualResult: text("actual_result"),
  executedAt: integer("executed_at"),
  createdAt: integer("created_at").notNull(),
});
```

---

## 4. 项目管理类表

### 4.1 立项表 (project_init)

```typescript
export const projectInit = table("project_init", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id).unique(),
  background: text("background"),
  goal: text("goal"),
  scope: text("scope"),
  stakeholders: json("stakeholders").default("[]"), // { name, role, responsibility }[]
  resources: json("resources").default("[]"), // { type, description }[]
  timeline: text("timeline"),
  budget: text("budget"),
  risks: json("risks").default("[]"),
  content: text("content"), // 完整立项书内容
  status: text("status").default("draft"),
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});
```

### 4.2 排期任务表 (schedule_tasks)

```typescript
export const scheduleTasks = table("schedule_tasks", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  description: text("description"),
  assignee: text("assignee"),
  startDate: integer("start_date"),
  endDate: integer("end_date"),
  progress: integer("progress").default(0), // 0-100
  status: text("status").default("pending"), // "pending" | "in_progress" | "completed" | "delayed"
  dependencies: json("dependencies").default("[]"), // string[]
  milestone: integer("milestone").default(0), // 0 | 1
  order: integer("order").notNull(),
  createdAt: integer("created_at").notNull(),
});
```

### 4.3 评审纪要表 (meeting_notes)

```typescript
export const meetingNotes = table("meeting_notes", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  title: text("title").notNull(),
  type: text("type").default("review"), // "review" | "standup" | "planning" | "retrospective"
  date: integer("date").notNull(),
  attendees: json("attendees").default("[]"),
  agenda: json("agenda").default("[]"), // { topic, conclusion, actionItems }[]
  content: text("content"), // 完整纪要内容
  actionItems: json("action_items").default("[]"), // { item, assignee, deadline, status }[]
  risks: json("risks").default("[]"),
  createdAt: integer("created_at").notNull(),
});
```

### 4.4 风险表 (risks)

```typescript
export const risks = table("risks", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  description: text("description").notNull(),
  probability: integer("probability").notNull(), // 1-5
  impact: integer("impact").notNull(), // 1-5
  level: text("level").notNull(), // "high" | "medium" | "low" (自动计算)
  measures: text("measures"), // 应对措施
  owner: text("owner"),
  status: text("status").default("identified"), // "identified" | "assessing" | "mitigated" | "closed"
  source: text("source").default("manual"), // "manual" | "meeting" | "agent"
  createdAt: integer("created_at").notNull(),
});
```

### 4.5 交付物料表 (deliverables)

```typescript
export const deliverables = table("deliverables", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  type: text("type").notNull(), // "document" | "config" | "code" | "test_report"
  description: text("description"),
  status: text("status").default("pending"), // "pending" | "in_progress" | "completed" | "na"
  owner: text("owner"),
  dueDate: integer("due_date"),
  completedAt: integer("completed_at"),
  order: integer("order").notNull(),
  createdAt: integer("created_at").notNull(),
});
```

---

## 5. 落地验收类表

### 5.1 验收表 (acceptance)

```typescript
export const acceptance = table("acceptance", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  prdId: text("prd_id").references(() => prdDocuments.id),
  versionId: text("version_id").references(() => versions.id),
  name: text("name").notNull(),
  status: text("status").default("in_progress"), // "in_progress" | "passed" | "failed" | "conditional"
  conclusion: text("conclusion"),
  createdAt: integer("created_at").notNull(),
});
```

### 5.2 验收检查项表 (acceptance_items)

```typescript
export const acceptanceItems = table("acceptance_items", {
  id: text("id").primaryKey(),
  acceptanceId: text("acceptance_id").notNull().references(() => acceptance.id),
  name: text("name").notNull(),
  description: text("description"),
  criteria: text("criteria"), // 验收标准
  status: text("status").default("pending"), // "pending" | "passed" | "failed" | "na"
  evidence: text("evidence"), // 验收证据
  issueId: text("issue_id").references(() => issues.id),
  order: integer("order").notNull(),
  createdAt: integer("created_at").notNull(),
});
```

### 5.3 问题表 (issues)

```typescript
export const issues = table("issues", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  title: text("title").notNull(),
  description: text("description"),
  source: text("source").notNull(), // "review" | "test" | "acceptance" | "user_feedback" | "manual"
  priority: text("priority").default("p2"), // "p0" | "p1" | "p2" | "p3"
  severity: text("severity").default("medium"), // "critical" | "high" | "medium" | "low"
  status: text("status").default("new"), // "new" | "assigned" | "in_progress" | "fixed" | "verified" | "closed" | "rejected"
  assignee: text("assignee"),
  solution: text("solution"),
  requirementId: text("requirement_id").references(() => requirements.id),
  testcaseId: text("testcase_id").references(() => testcases.id),
  createdAt: integer("created_at").notNull(),
  resolvedAt: integer("resolved_at"),
});
```

---

## 6. 复盘迭代类表

### 6.1 数据报告表 (data_reports)

```typescript
export const dataReports = table("data_reports", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  description: text("description"),
  data: json("data"), // 导入的数据
  charts: json("charts").default("[]"), // 图表配置
  content: text("content"), // 报告内容
  createdAt: integer("created_at").notNull(),
});
```

### 6.2 复盘表 (retrospectives)

```typescript
export const retrospectives = table("retrospectives", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  versionId: text("version_id").references(() => versions.id),
  title: text("title").notNull(),
  goalAchievement: text("goal_achievement"), // 目标达成度
  processReview: text("process_review"), // 过程回顾
  problemAnalysis: json("problem_analysis").default("[]"), // { problem, cause, solution }[]
  lessons: json("lessons").default("[]"), // { lesson, category }[]
  improvements: json("improvements").default("[]"), // { improvement, priority }[]
  content: text("content"), // 完整复盘内容
  createdAt: integer("created_at").notNull(),
});
```

### 6.3 迭代方案表 (iterations)

```typescript
export const iterations = table("iterations", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  background: text("background"),
  goals: json("goals").default("[]"),
  requirements: json("requirements").default("[]"), // 关联需求 ID
  roadmapNodeId: text("roadmap_node_id").references(() => roadmapNodes.id),
  expectedEffect: text("expected_effect"),
  riskAssessment: text("risk_assessment"),
  content: text("content"),
  status: text("status").default("draft"),
  createdAt: integer("created_at").notNull(),
});
```

---

## 7. 赋能协作类表

### 7.1 培训素材表 (training_materials)

```typescript
export const trainingMaterials = table("training_materials", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  outline: json("outline").notNull(), // { title, content, notes }[]
  slides: json("slides").default("[]"), // 幻灯片内容
  createdAt: integer("created_at").notNull(),
});
```

### 7.2 操作手册表 (manuals)

```typescript
export const manuals = table("manuals", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  featureId: text("feature_id"),
  content: text("content").notNull(), // 手册内容
  screenshots: json("screenshots").default("[]"), // { placeholder, imagePath? }[]
  createdAt: integer("created_at").notNull(),
});
```

### 7.3 FAQ 表 (faqs)

```typescript
export const faqs = table("faqs", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  question: text("question").notNull(),
  answer: text("answer").notNull(),
  category: text("category"),
  keywords: json("keywords").default("[]"),
  source: text("source").default("manual"), // "manual" | "issue"
  issueId: text("issue_id").references(() => issues.id),
  viewCount: integer("view_count").default(0),
  createdAt: integer("created_at").notNull(),
});
```

### 7.4 宣讲材料表 (presentations)

```typescript
export const presentations = table("presentations", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id),
  name: text("name").notNull(),
  outline: json("outline").notNull(), // { title, keyPoints, data }[]
  content: text("content"),
  createdAt: integer("created_at").notNull(),
});
```

---

## 8. 系统表

### 8.1 设置表 (settings)

```typescript
export const settings = table("settings", {
  key: text("key").primaryKey(),
  value: text("value"), // JSON 字符串
  updatedAt: integer("updated_at").notNull(),
});
```

**常用设置项**:

| Key | 说明 |
|-----|------|
| `ai.provider` | AI 提供商 |
| `ai.api_key` | API Key（加密存储）|
| `ai.model` | 模型名称 |
| `ai.base_url` | 本地模型地址 |
| `ui.theme` | UI 主题 |
| `ui.language` | 语言 |
| `auto_save_interval` | 自动保存间隔（秒）|
| `max_versions` | 最大版本数 |

### 8.2 应用状态表 (application_state)

```typescript
export const applicationState = table("application_state", {
  key: text("key").primaryKey(),
  value: text("value"), // JSON 字符串
  updatedAt: integer("updated_at").notNull(),
});
```

**常用状态**:

| Key | 说明 |
|-----|------|
| `navigation` | 当前导航状态 |
| `current_project` | 当前项目 ID |
| `current_version` | 当前版本 ID |
| `draft_prd` | PRD 草稿 |
| `selected_entities` | 选中的实体 |

### 8.3 审计日志表 (audit_logs)

```typescript
export const auditLogs = table("audit_logs", {
  id: text("id").primaryKey(),
  action: text("action").notNull(),
  targetType: text("target_type").notNull(),
  targetId: text("target_id").notNull(),
  userEmail: text("user_email"),
  orgId: text("org_id"),
  caller: text("caller").notNull(), // "tool" | "frontend" | "http" | "cli" | "mcp" | "a2a"
  inputs: text("inputs"), // JSON
  result: text("result"), // JSON
  threadId: text("thread_id"),
  turnId: text("turn_id"),
  createdAt: integer("created_at").notNull(),
});
```

---

## 9. 关系图

```
projects (1)
    │
    ├─→ versions (N)
    ├─→ workflows (N)
    ├─→ entities (N)
    ├─→ requirements (N)
    ├─→ competitors (N)
    │   └─→ competitor_analysis (N)
    ├─→ roadmap_nodes (N)
    ├─→ prd_documents (N)
    │   ├─→ prd_embedded_parameters (N) → parameters
    │   └─→ prd_checks (N)
    ├─→ prototype_screens (N)
    │   └─→ prototype_checks (N)
    ├─→ parameters (N)
    ├─→ prototype_prompts (N)
    ├─→ testcases (N)
    ├─→ project_init (1)
    ├─→ schedule_tasks (N)
    ├─→ meeting_notes (N)
    ├─→ risks (N)
    ├─→ deliverables (N)
    ├─→ acceptance (N)
    │   └─→ acceptance_items (N)
    ├─→ issues (N)
    ├─→ data_reports (N)
    ├─→ retrospectives (N)
    ├─→ iterations (N)
    ├─→ training_materials (N)
    ├─→ manuals (N)
    ├─→ faqs (N)
    └─→ presentations (N)

entities (N) ←→ relations (N) → entities (N)
```

---

## 10. 索引汇总

| 表名 | 索引名 | 字段 | 类型 |
|------|--------|------|------|
| projects | idx_projects_status | status | 普通 |
| projects | idx_projects_type | type | 普通 |
| versions | idx_versions_project_id | project_id | 普通 |
| versions | idx_versions_version_number | project_id, version_number | 唯一 |
| requirements | idx_requirements_project_id | project_id | 普通 |
| requirements | idx_requirements_status | status | 普通 |
| requirements | idx_requirements_priority | priority | 普通 |
| entities | idx_entities_project_id | project_id | 普通 |
| entities | idx_entities_type | type | 普通 |
| relations | idx_relations_project_id | project_id | 普通 |
| relations | idx_relations_entity_a | entity_a_id | 普通 |
| relations | idx_relations_entity_b | entity_b_id | 普通 |
| prd_documents | idx_prd_project_id | project_id | 普通 |
| prd_documents | idx_prd_status | status | 普通 |
| parameters | idx_parameters_project_id | project_id | 普通 |
| parameters | idx_parameters_module | module_id | 普通 |
| parameters | idx_parameters_feature | feature_id | 普通 |
| testcases | idx_testcases_project_id | project_id | 普通 |
| issues | idx_issues_project_id | project_id | 普通 |
| issues | idx_issues_status | status | 普通 |
| issues | idx_issues_priority | priority | 普通 |

---

**文档结束**
