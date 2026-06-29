# PM 工作流平台 - 产品需求文档（PRD）

## 基于 Agent Native 框架

**版本**: v1.0  
**日期**: 2026-06-27  
**作者**: AI 协作  
**状态**: 草案  

---

## 1. 产品概述

### 1.1 产品定位

面向产品经理的 AI 工作流平台，覆盖从需求收集到复盘迭代的完整产品生命周期。平台以**手动操作为主路径**，AI 为增强辅助，确保即使 AI 功能不可用时，平台仍是完整可用的 PM 工具。

### 1.2 核心原则

| 原则 | 说明 |
|------|------|
| **手动优先** | 所有功能必须支持纯手动操作，AI 只是加速器 |
| **AI 增强** | AI 辅助生成、分析、建议，但需用户确认 |
| **项目隔离** | 数据严格按项目隔离，不穿透 |
| **版本可控** | 所有文档支持版本管理，可对比回滚 |
| **关系可追溯** | 需求-功能-参数-文档之间建立关联关系 |
| **流程建议** | 工作流为建议性，不强制顺序，随时可调整 |

### 1.3 技术约束

- **框架**: Agent Native（`@agent-native/core`）
- **前端**: React + Vite + React Router
- **数据库**: SQLite（本地）/ PostgreSQL（生产）
- **ORM**: Drizzle
- **AI**: OpenAI/Claude/本地模型（用户自配置 API Key）
- **存储**: 本地文件系统 + SQL

---

## 2. 系统架构

### 2.1 Agent Native 架构映射

```
┌─────────────────────────────────────────────────────────────┐
│                        UI 层 (React)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ 项目列表 │ │ 文档编辑 │ │ 表格编辑 │ │ 流程看板 │          │
│  │ 表格视图 │ │ 富文本  │ │ 参数清单 │ │ 甘特图  │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
│       └─────────────┴─────────────┴─────────┘                │
│                    ↓ AgentChatSurface                       │
│              ┌─────────────┐                                │
│              │ AI 助手面板 │ ← 浮动/侧边栏                  │
│              └─────────────┘                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent 循环层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ AGENTS.md   │  │  Skills     │  │   Actions (28个)    │ │
│  │ 指令系统    │  │  技能库     │  │   业务操作          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层 (SQL + 文件)                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐   │
│  │ SQLite  │  │ 文件系统 │  │ settings│  │ app_state   │   │
│  │ 业务数据│  │ 文档附件│  │ 配置    │  │ 导航状态   │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心文件结构

```
pm-workflow-platform/
├── actions/                    # 28 个业务 Action
│   ├── project/               # Project 模块
│   ├── workflow/              # Workflow 模块
│   ├── versioning/            # Versioning 模块
│   ├── traceability/          # Traceability 模块
│   ├── requirement/           # 需求收集
│   ├── competitor/            # 竞品分析
│   ├── roadmap/               # 产品路线图
│   ├── prd/                   # PRD 编辑+检查
│   ├── prototype/             # 原型走查+提示词
│   ├── parameter/             # 参数清单
│   ├── testcase/              # 测试用例
│   ├── schedule/              # 排期
│   ├── meeting/               # 评审纪要
│   ├── risk/                  # 风险管控
│   ├── deliverable/           # 交付物料
│   ├── acceptance/            # 验收文档
│   ├── issue/                 # 问题闭环
│   ├── report/                # 数据分析
│   ├── retrospective/         # 版本复盘
│   ├── iteration/             # 优化迭代
│   ├── training/              # 培训素材
│   ├── manual/                # 操作手册
│   ├── faq/                   # FAQ
│   ├── presentation/          # 宣讲材料
│   └── agent/                 # Agent 核心
│
├── app/                       # React 前端
│   ├── routes/               # 页面路由
│   ├── components/           # 业务组件
│   └── root.tsx              # 应用外壳
│
├── server/                    # Nitro API 服务
│   └── routes/               # 自定义路由
│
├── .agents/                   # Agent Skills
│   └── skills/
│       ├── prd-generation/   # PRD 生成技能
│       ├── requirement-analysis/  # 需求分析
│       ├── competitor-research/     # 竞品调研
│       ├── prototype-check/        # 原型走查
│       └── ...
│
├── AGENTS.md                  # Agent 指令
├── data/
│   └── app.db                 # SQLite 数据库
└── docs/
    └── prd/                   # 需求文档
```

---

## 3. 核心模块定义

### 3.1 Agent 模块

**定位**: AI 能力调度器，所有 AI 功能的统一入口。

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `agent.chat` | 通用对话 | `{ message, context? }` | POST | false |
| `agent.intent` | 意图识别 | `{ message }` | POST | true |
| `agent.skill.call` | 调用 Skill | `{ skillId, parameters }` | POST | false |
| `agent.config` | 配置 API Key | `{ provider, apiKey }` | POST | false |
| `agent.status` | 检查 AI 状态 | `{}` | GET | true |

**Skills**:

```markdown
# .agents/skills/prd-generation/SKILL.md

## 任务：PRD 生成

当用户需要生成 PRD 时，按以下步骤执行：

1. 询问用户产品背景和目标
2. 根据项目类型选择 PRD 模板
3. 生成 PRD 大纲
4. 逐章节填充内容
5. 提示用户修改确认
```

### 3.2 Project 模块

**定位**: 数据隔离单元，所有数据的上下文根节点。

**数据模型**:

```typescript
// Drizzle Schema
import { table, text, integer, json } from "@agent-native/core/db/schema";

export const projects = table("projects", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description"),
  type: text("type").notNull(), // "prd" | "competitor" | "general"
  status: text("status").notNull().default("active"), // "active" | "archived" | "deleted"
  config: json("config"), // API Key, 模板配置等
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});

export const projectTemplates = table("project_templates", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  type: text("type").notNull(),
  defaultModules: json("default_modules").notNull(),
  defaultDocs: json("default_docs"),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `project.create` | 创建项目 | `{ name, type, templateId? }` | POST | false |
| `project.list` | 项目列表 | `{ status? }` | GET | true |
| `project.get` | 项目详情 | `{ id }` | GET | true |
| `project.update` | 更新项目 | `{ id, name?, description? }` | POST | false |
| `project.delete` | 删除项目 | `{ id }` | POST | false |
| `project.archive` | 归档项目 | `{ id }` | POST | false |
| `project.restore` | 恢复项目 | `{ id }` | POST | false |
| `project.export` | 导出项目 | `{ id }` | GET | false |
| `project.import` | 导入项目 | `{ file }` | POST | false |
| `project.switch` | 切换项目 | `{ id }` | POST | false |

**约束条件**:
- 项目名全局唯一，重复时自动追加序号
- 删除项目进入回收站，30 天可恢复
- 项目数据目录：`data/projects/{projectId}/`

### 3.3 Product Workflow 模块

**定位**: 流程协作框架，建议性流程，灵活可调。

**数据模型**:

```typescript
export const workflows = table("workflows", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  name: text("name").notNull(),
  templateId: text("template_id"),
  status: text("status").notNull().default("draft"),
  steps: json("steps").notNull(), // WorkflowStep[]
  createdAt: integer("created_at").notNull(),
});

// WorkflowStep 结构
interface WorkflowStep {
  id: string;
  name: string;
  category: string; // "planning" | "design" | "management" | "acceptance" | "review" | "enablement"
  status: "pending" | "in_progress" | "completed" | "blocked" | "skipped";
  deliverables: string[]; // 关联的文档/表格 ID
  aiExtractedData?: any; // AI 提取的数据
  manualData?: any; // 手动修改的数据
  nextSteps: string[]; // 建议的下一步
  order: number;
  isCustom: boolean; // 是否用户自定义添加
}
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `workflow.create` | 创建工作流 | `{ projectId, templateId? }` | POST | false |
| `workflow.get` | 工作流详情 | `{ id }` | GET | true |
| `workflow.update` | 更新工作流 | `{ id, steps }` | POST | false |
| `workflow.step.update` | 更新步骤 | `{ workflowId, stepId, status, data? }` | POST | false |
| `workflow.step.add` | 添加步骤 | `{ workflowId, step, position? }` | POST | false |
| `workflow.step.remove` | 删除步骤 | `{ workflowId, stepId }` | POST | false |
| `workflow.step.move` | 移动步骤 | `{ workflowId, stepId, newOrder }` | POST | false |
| `workflow.next` | 获取建议下一步 | `{ workflowId, currentStepId }` | GET | true |
| `workflow.progress` | 进度统计 | `{ id }` | GET | true |

**核心特性**:
- 步骤无强制依赖，纯建议性
- 支持随时新增、删除、修改步骤
- AI 提取数据后，用户确认再进入下一步
- 支持跳转到任意步骤修改数据

### 3.4 Versioning 模块

**定位**: 版本控制中枢，快照 + 对比 + 回滚。

**数据模型**:

```typescript
export const versions = table("versions", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  versionNumber: text("version_number").notNull(), // "v1.0"
  label: text("label"), // "milestone" | "release" | "review"
  description: text("description").notNull(),
  snapshotPath: text("snapshot_path").notNull(), // 快照目录
  createdBy: text("created_by"),
  createdAt: integer("created_at").notNull(),
});

export const versionRefs = table("version_refs", {
  id: text("id").primaryKey(),
  currentVersionId: text("current_version_id").notNull(),
  referencedVersionId: text("referenced_version_id").notNull(),
  entityType: text("entity_type").notNull(), // "document" | "requirement" | "parameter"
  entityId: text("entity_id").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `version.create` | 创建版本 | `{ projectId, versionNumber, description }` | POST | false |
| `version.list` | 版本列表 | `{ projectId }` | GET | true |
| `version.get` | 版本详情 | `{ id }` | GET | true |
| `version.switch` | 切换版本 | `{ id }` | POST | false |
| `version.compare` | 版本对比 | `{ versionA, versionB, entityType? }` | GET | true |
| `version.rollback` | 版本回滚 | `{ id }` | POST | false |
| `version.ref.create` | 创建跨版本引用 | `{ currentVersionId, referencedVersionId, entityType, entityId }` | POST | false |
| `version.autoSave` | 自动保存草稿 | `{ projectId, data }` | POST | false |

### 3.5 Traceability 模块

**定位**: 关系网络中枢，双向追溯 + 影响分析。

**数据模型**:

```typescript
export const entities = table("entities", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  type: text("type").notNull(), // "requirement" | "module" | "feature" | "parameter" | "document" | "version" | "operation"
  name: text("name").notNull(),
  moduleId: text("module_id"), // 所属模块
  featureId: text("feature_id"), // 所属功能
  metadata: json("metadata"),
});

export const relations = table("relations", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  entityAId: text("entity_a_id").notNull(),
  entityBId: text("entity_b_id").notNull(),
  relationType: text("relation_type").notNull(), // "contains" | "references" | "derives" | "modifies" | "conflicts"
  confidence: integer("confidence"), // 0-100, AI 建议的置信度
  confirmed: integer("confirmed").notNull().default(0), // 0=待确认, 1=已确认
  createdBy: text("created_by"), // "ai" | "user"
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `relation.create` | 创建关联 | `{ projectId, entityA, entityB, type, confirmed? }` | POST | false |
| `relation.list` | 关联列表 | `{ projectId, entityId? }` | GET | true |
| `relation.delete` | 删除关联 | `{ id }` | POST | false |
| `relation.confirm` | 确认 AI 建议 | `{ id }` | POST | false |
| `relation.impact` | 影响分析 | `{ entityId }` | GET | true |
| `relation.trace` | 追溯链路 | `{ entityId, direction }` | GET | true |
| `relation.suggest` | AI 建议关联 | `{ projectId, entityId }` | GET | true |
| `relation.graph` | 关系图数据 | `{ projectId, filters? }` | GET | true |

---

## 4. 业务模块定义

### 4.1 规划类

#### 4.1.1 需求收集 (requirement)

**数据模型**:

```typescript
export const requirements = table("requirements", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  title: text("title").notNull(),
  description: text("description"),
  source: text("source"), // "manual" | "excel" | "agent"
  priority: text("priority").default("p2"), // "p0" | "p1" | "p2" | "p3"
  status: text("status").default("open"), // "open" | "in_progress" | "resolved" | "closed"
  tags: json("tags").default("[]"),
  category: text("category"), // 分类标签
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `requirement.create` | 创建需求 | `{ projectId, title, description, priority? }` | POST | false |
| `requirement.list` | 需求列表 | `{ projectId, filters? }` | GET | true |
| `requirement.get` | 需求详情 | `{ id }` | GET | true |
| `requirement.update` | 更新需求 | `{ id, ... }` | POST | false |
| `requirement.delete` | 删除需求 | `{ id }` | POST | false |
| `requirement.import` | Excel 导入 | `{ projectId, file }` | POST | false |
| `requirement.export` | Excel 导出 | `{ projectId }` | GET | false |
| `requirement.analyze` | AI 分析分类 | `{ projectId }` | POST | true |

#### 4.1.2 竞品分析 (competitor)

**数据模型**:

```typescript
export const competitors = table("competitors", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  name: text("name").notNull(),
  url: text("url"),
  description: text("description"),
  createdAt: integer("created_at").notNull(),
});

export const competitorAnalysis = table("competitor_analysis", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  competitorId: text("competitor_id").notNull(),
  dimension: text("dimension").notNull(), // 分析维度
  ourProduct: text("our_product"), // 我方产品
  competitorProduct: text("competitor_product"), // 竞品
  analysis: text("analysis"), // 分析结论
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `competitor.create` | 添加竞品 | `{ projectId, name, url? }` | POST | false |
| `competitor.list` | 竞品列表 | `{ projectId }` | GET | true |
| `competitor.analyze` | 填写分析 | `{ competitorId, dimension, data }` | POST | false |
| `competitor.research` | AI 调研 | `{ competitorId }` | POST | true |
| `competitor.export` | 导出矩阵 | `{ projectId }` | GET | false |

#### 4.1.3 产品路线图 (roadmap)

**数据模型**:

```typescript
export const roadmapNodes = table("roadmap_nodes", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  versionId: text("version_id"), // 关联版本
  name: text("name").notNull(),
  type: text("type").notNull(), // "milestone" | "feature" | "release"
  status: text("status").default("planned"), // "planned" | "in_progress" | "completed" | "delayed"
  startDate: integer("start_date"),
  endDate: integer("end_date"),
  dependencies: json("dependencies").default("[]"), // 依赖节点 ID
  order: integer("order").notNull(),
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `roadmap.create` | 创建节点 | `{ projectId, name, type, dates }` | POST | false |
| `roadmap.list` | 节点列表 | `{ projectId }` | GET | true |
| `roadmap.update` | 更新节点 | `{ id, ... }` | POST | false |
| `roadmap.reorder` | 调整顺序 | `{ id, newOrder }` | POST | false |
| `roadmap.gantt` | 甘特图数据 | `{ projectId }` | GET | true |

---

### 4.2 需求设计类

#### 4.2.1 PRD 编辑 (prd)

**数据模型**:

```typescript
export const prdDocuments = table("prd_documents", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  versionId: text("version_id"), // 关联版本
  title: text("title").notNull(),
  content: text("content").notNull(), // Markdown/JSON 格式
  sections: json("sections").notNull(), // PRDSection[]
  status: text("status").default("draft"), // "draft" | "review" | "approved" | "archived"
  template: text("template").default("standard"), // 模板类型
  createdAt: integer("created_at").notNull(),
  updatedAt: integer("updated_at").notNull(),
});

interface PRDSection {
  id: string;
  type: "overview" | "background" | "goal" | "requirement" | "non_functional" | "appendix";
  title: string;
  content: string;
  parameters: string[]; // 嵌入的参数 ID
  order: number;
}
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `prd.create` | 创建 PRD | `{ projectId, title, template? }` | POST | false |
| `prd.get` | PRD 详情 | `{ id }` | GET | true |
| `prd.update` | 更新内容 | `{ id, content, sections }` | POST | false |
| `prd.section.update` | 更新章节 | `{ prdId, sectionId, content }` | POST | false |
| `prd.section.add` | 添加章节 | `{ prdId, section, position? }` | POST | false |
| `prd.section.remove` | 删除章节 | `{ prdId, sectionId }` | POST | false |
| `prd.parameter.embed` | 嵌入参数 | `{ prdId, sectionId, parameterId }` | POST | false |
| `prd.generate` | AI 生成初稿 | `{ projectId, requirements }` | POST | true |
| `prd.export` | 导出 | `{ id, format }` | GET | false |
| `prd.import` | 导入 | `{ projectId, file }` | POST | false |

#### 4.2.2 PRD 检查 (prd-check)

**数据模型**:

```typescript
export const prdChecks = table("prd_checks", {
  id: text("id").primaryKey(),
  prdId: text("prd_id").notNull(),
  level: text("level").notNull(), // "l1" | "l2" | "l3" | "l4"
  ruleId: text("rule_id").notNull(),
  ruleDescription: text("rule_description").notNull(),
  status: text("status").default("pending"), // "pending" | "pass" | "fail" | "ignored"
  location: text("location"), // 问题位置
  suggestion: text("suggestion"), // 修改建议
  createdAt: integer("created_at").notNull(),
});

export const checkRules = table("check_rules", {
  id: text("id").primaryKey(),
  level: text("level").notNull(),
  category: text("category").notNull(), // "content_existence" | "logic_completeness" | "consistency" | "ux_heuristic" | "accessibility" | "security"
  description: text("description").notNull(),
  checkType: text("check_type").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `prd-check.run` | 执行检查 | `{ prdId, level }` | POST | false |
| `prd-check.list` | 检查结果 | `{ prdId }` | GET | true |
| `prd-check.update` | 更新状态 | `{ id, status }` | POST | false |
| `prd-check.ignore` | 忽略检查项 | `{ id }` | POST | false |
| `prd-check.rules` | 规则库 | `{ level? }` | GET | true |
| `prd-check.report` | 检查报告 | `{ prdId }` | GET | false |

#### 4.2.3 原型走查 (prototype)

**数据模型**:

```typescript
export const prototypeScreens = table("prototype_screens", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  name: text("name").notNull(),
  imagePath: text("image_path").notNull(),
  annotations: json("annotations").default("[]"), // 标注数据
  createdAt: integer("created_at").notNull(),
});

export const prototypeChecks = table("prototype_checks", {
  id: text("id").primaryKey(),
  screenId: text("screen_id").notNull(),
  checkItemId: text("check_item_id").notNull(),
  status: text("status").default("pending"), // "pending" | "pass" | "fail" | "na"
  issue: text("issue"), // 问题描述
  annotationId: text("annotation_id"), // 关联标注
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `prototype.screen.upload` | 上传截图 | `{ projectId, file, name }` | POST | false |
| `prototype.screen.list` | 截图列表 | `{ projectId }` | GET | true |
| `prototype.annotation.add` | 添加标注 | `{ screenId, x, y, text }` | POST | false |
| `prototype.check.run` | 走查检查 | `{ screenId, checklist? }` | POST | false |
| `prototype.check.list` | 走查结果 | `{ screenId }` | GET | true |
| `prototype.analyze` | AI 分析 | `{ screenId }` | POST | true |

#### 4.2.4 参数清单 (parameter)

**数据模型**:

```typescript
export const parameters = table("parameters", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
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
  sourceDocument: text("source_document"), // 来源 PRD
  version: text("version"), // 引入版本
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `parameter.create` | 创建参数 | `{ projectId, ... }` | POST | false |
| `parameter.list` | 参数列表 | `{ projectId, filters? }` | GET | true |
| `parameter.get` | 参数详情 | `{ id }` | GET | true |
| `parameter.update` | 更新参数 | `{ id, ... }` | POST | false |
| `parameter.delete` | 删除参数 | `{ id }` | POST | false |
| `parameter.extract` | 从 PRD 提取 | `{ prdId }` | POST | true |
| `parameter.import` | Excel 导入 | `{ projectId, file }` | POST | false |
| `parameter.export` | Excel 导出 | `{ projectId }` | GET | false |
| `parameter.config` | 生成配置清单 | `{ projectId, moduleId? }` | GET | false |

#### 4.2.5 原型提示词 (prototype-prompt)

**数据模型**:

```typescript
export const prototypePrompts = table("prototype_prompts", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  featureId: text("feature_id"), // 关联功能
  name: text("name").notNull(),
  prompt: text("prompt").notNull(), // Midscene 提示词
  template: text("template"), // 模板类型
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `prototype-prompt.create` | 创建提示词 | `{ projectId, name, prompt }` | POST | false |
| `prototype-prompt.list` | 提示词列表 | `{ projectId }` | GET | true |
| `prototype-prompt.generate` | AI 生成 | `{ featureId, description }` | POST | true |
| `prototype-prompt.template` | 模板库 | `{}` | GET | true |

#### 4.2.6 测试用例 (testcase)

**数据模型**:

```typescript
export const testcases = table("testcases", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  moduleId: text("module_id"),
  featureId: text("feature_id"),
  scenario: text("scenario").notNull(),
  precondition: text("precondition"),
  steps: text("steps").notNull(),
  inputData: text("input_data"),
  expectedResult: text("expected_result").notNull(),
  priority: text("priority").default("p2"), // "p0" | "p1" | "p2" | "p3"
  caseType: text("case_type").default("functional"), // "functional" | "boundary" | "exception" | "performance"
  requirementId: text("requirement_id"),
  parameterId: text("parameter_id"),
  status: text("status").default("pending"), // "pending" | "passed" | "failed" | "blocked"
  createdAt: integer("created_at").notNull(),
});
```

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `testcase.create` | 创建用例 | `{ projectId, ... }` | POST | false |
| `testcase.list` | 用例列表 | `{ projectId, filters? }` | GET | true |
| `testcase.generate` | AI 生成 | `{ prdId, parameterId? }` | POST | true |
| `testcase.execute` | 执行记录 | `{ id, status, actualResult? }` | POST | false |
| `testcase.export` | 导出 | `{ projectId }` | GET | false |

---

### 4.3 项目管理类

#### 4.3.1 立项 (project-init)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `project-init.create` | 创建立项书 | `{ projectId, data }` | POST | false |
| `project-init.get` | 立项书详情 | `{ projectId }` | GET | true |
| `project-init.update` | 更新立项书 | `{ projectId, data }` | POST | false |

#### 4.3.2 排期 (schedule)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `schedule.create` | 创建任务 | `{ projectId, name, dates, dependencies? }` | POST | false |
| `schedule.list` | 任务列表 | `{ projectId }` | GET | true |
| `schedule.gantt` | 甘特图数据 | `{ projectId }` | GET | true |
| `schedule.update` | 更新任务 | `{ id, ... }` | POST | false |

#### 4.3.3 评审纪要 (meeting)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `meeting.create` | 创建纪要 | `{ projectId, data }` | POST | false |
| `meeting.list` | 纪要列表 | `{ projectId }` | GET | true |
| `meeting.update` | 更新纪要 | `{ id, data }` | POST | false |

#### 4.3.4 风险管控 (risk)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `risk.create` | 创建风险 | `{ projectId, description, probability, impact }` | POST | false |
| `risk.list` | 风险列表 | `{ projectId }` | GET | true |
| `risk.update` | 更新风险 | `{ id, status, measures? }` | POST | false |
| `risk.matrix` | 风险矩阵 | `{ projectId }` | GET | true |

#### 4.3.5 上线交付物料 (deliverable)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `deliverable.create` | 创建清单 | `{ projectId, template? }` | POST | false |
| `deliverable.list` | 交付物列表 | `{ projectId }` | GET | true |
| `deliverable.check` | 勾选完成 | `{ id, status }` | POST | false |
| `deliverable.report` | 完成度报告 | `{ projectId }` | GET | true |

---

### 4.4 落地验收类

#### 4.4.1 验收文档 (acceptance)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `acceptance.create` | 创建验收 | `{ projectId, prdId? }` | POST | false |
| `acceptance.list` | 检查项列表 | `{ projectId }` | GET | true |
| `acceptance.check` | 执行检查 | `{ id, status }` | POST | false |
| `acceptance.report` | 生成报告 | `{ projectId }` | GET | false |

#### 4.4.2 问题闭环记录 (issue)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `issue.create` | 创建问题 | `{ projectId, description, source, priority }` | POST | false |
| `issue.list` | 问题列表 | `{ projectId, filters? }` | GET | true |
| `issue.update` | 更新状态 | `{ id, status, solution? }` | POST | false |
| `issue.link` | 关联需求 | `{ issueId, requirementId }` | POST | false |

---

### 4.5 复盘迭代类

#### 4.5.1 数据分析报告 (report)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `report.create` | 创建报告 | `{ projectId, data }` | POST | false |
| `report.list` | 报告列表 | `{ projectId }` | GET | true |
| `report.import` | 导入数据 | `{ projectId, file }` | POST | false |

#### 4.5.2 版本复盘 (retrospective)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `retrospective.create` | 创建复盘 | `{ projectId, versionId }` | POST | false |
| `retrospective.get` | 复盘详情 | `{ id }` | GET | true |
| `retrospective.update` | 更新复盘 | `{ id, data }` | POST | false |
| `retrospective.summary` | 数据汇总 | `{ projectId, versionId }` | GET | true |

#### 4.5.3 优化迭代方案 (iteration)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `iteration.create` | 创建方案 | `{ projectId, data }` | POST | false |
| `iteration.list` | 方案列表 | `{ projectId }` | GET | true |
| `iteration.link-roadmap` | 关联路线图 | `{ iterationId, roadmapNodeId }` | POST | false |

---

### 4.6 赋能协作类

#### 4.6.1 培训素材 (training)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `training.create` | 创建大纲 | `{ projectId, data }` | POST | false |
| `training.get` | 素材详情 | `{ id }` | GET | true |
| `training.generate` | AI 生成 | `{ projectId, features }` | POST | true |

#### 4.6.2 操作手册 (manual)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `manual.create` | 创建手册 | `{ projectId, data }` | POST | false |
| `manual.get` | 手册详情 | `{ id }` | GET | true |
| `manual.update` | 更新手册 | `{ id, data }` | POST | false |

#### 4.6.3 FAQ (faq)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `faq.create` | 创建 FAQ | `{ projectId, question, answer, category? }` | POST | false |
| `faq.list` | FAQ 列表 | `{ projectId, search? }` | GET | true |
| `faq.import` | 从问题导入 | `{ projectId, issueId }` | POST | false |

#### 4.6.4 宣讲材料 (presentation)

**Action 列表**:

| Action | 描述 | Schema | HTTP | ReadOnly |
|--------|------|--------|------|----------|
| `presentation.create` | 创建材料 | `{ projectId, data }` | POST | false |
| `presentation.get` | 材料详情 | `{ id }` | GET | true |
| `presentation.generate` | AI 生成 | `{ projectId, features }` | POST | true |

---

## 5. UI 设计规范

### 5.1 布局结构

```
┌─────────────────────────────────────────────────────────────┐
│  顶部导航栏                                                    │
│  [项目选择 ▼] [工作流] [文档中心] [版本] [设置]               │
├──────────┬──────────────────────────────┬───────────────────┤
│          │                              │                   │
│  左侧导航 │      主内容区                 │   右侧面板        │
│          │                              │                   │
│  [一级菜单]│                              │  [追溯面板]      │
│  规划类   │    表格/文档/图表             │  [AI 助手]       │
│  需求设计类│                              │  [属性面板]      │
│  项目管理类│                              │                   │
│  落地验收类│                              │                   │
│  复盘迭代类│                              │                   │
│  赋能协作类│                              │                   │
│          │                              │                   │
└──────────┴──────────────────────────────┴───────────────────┘
```

### 5.2 页面路由

| 路由 | 页面 | 组件 |
|------|------|------|
| `/` | 项目列表 | `ProjectListPage` |
| `/projects/:id` | 项目工作台 | `ProjectWorkspace` |
| `/projects/:id/workflow` | 工作流看板 | `WorkflowBoard` |
| `/projects/:id/requirements` | 需求收集 | `RequirementTable` |
| `/projects/:id/competitors` | 竞品分析 | `CompetitorMatrix` |
| `/projects/:id/roadmap` | 产品路线图 | `RoadmapGantt` |
| `/projects/:id/prd` | PRD 列表 | `PRDList` |
| `/projects/:id/prd/:docId` | PRD 编辑 | `PRDEditor` |
| `/projects/:id/prd/:docId/check` | PRD 检查 | `PRDCheckPanel` |
| `/projects/:id/prototype` | 原型走查 | `PrototypeViewer` |
| `/projects/:id/parameters` | 参数清单 | `ParameterTable` |
| `/projects/:id/testcases` | 测试用例 | `TestcaseTable` |
| `/projects/:id/schedule` | 排期 | `ScheduleGantt` |
| `/projects/:id/meetings` | 评审纪要 | `MeetingList` |
| `/projects/:id/risks` | 风险管控 | `RiskMatrix` |
| `/projects/:id/deliverables` | 交付物料 | `DeliverableChecklist` |
| `/projects/:id/acceptance` | 验收文档 | `AcceptancePanel` |
| `/projects/:id/issues` | 问题闭环 | `IssueTracker` |
| `/projects/:id/versions` | 版本管理 | `VersionManager` |
| `/projects/:id/traceability` | 关系图 | `RelationGraph` |
| `/projects/:id/documents` | 文档中心 | `DocumentCenter` |
| `/settings` | 设置 | `SettingsPage` |

### 5.3 组件清单

| 组件 | 类型 | 说明 |
|------|------|------|
| `ProjectListPage` | 页面 | 项目卡片列表 |
| `ProjectWorkspace` | 页面 | 项目工作台首页 |
| `WorkflowBoard` | 页面 | 流程看板，步骤卡片 |
| `RequirementTable` | 表格 | 需求收集表格 |
| `CompetitorMatrix` | 表格+文档 | 竞品对比矩阵 |
| `RoadmapGantt` | 可视化 | 时间轴/甘特图 |
| `PRDEditor` | 编辑器 | 富文本编辑器 |
| `PRDCheckPanel` | 面板 | 检查结果列表 |
| `PrototypeViewer` | 查看器 | 图片+标注层 |
| `ParameterTable` | 表格 | 参数清单表格 |
| `TestcaseTable` | 表格 | 测试用例表格 |
| `ScheduleGantt` | 可视化 | 任务甘特图 |
| `MeetingList` | 列表 | 纪要列表 |
| `RiskMatrix` | 可视化 | 风险矩阵图 |
| `DeliverableChecklist` | 表格 | 交付清单勾选 |
| `AcceptancePanel` | 面板 | 验收检查 |
| `IssueTracker` | 表格 | 问题跟踪 |
| `VersionManager` | 页面 | 版本列表+对比 |
| `RelationGraph` | 可视化 | 关系网络图 |
| `DocumentCenter` | 页面 | 文件浏览器 |
| `AgentChatSurface` | 组件 | AI 聊天面板 |
| `TraceabilityPanel` | 面板 | 右侧追溯面板 |

---

## 6. 数据流设计

### 6.1 核心数据流

```
用户操作
    │
    ├─→ 前端组件 ──→ useActionMutation ──→ Action ──→ Drizzle ORM ──→ SQLite
    │                                                    │
    │                                                    └─→ 变更事件 ──→ SSE
    │                                                           │
    └─← 自动刷新 ←── useActionQuery ←── React Query 缓存 ←─────┘
```

### 6.2 Agent 数据流

```
用户消息
    │
    ├─→ AgentChatSurface
    │
    ├─→ Agent 循环
    │       ├─→ 读取 AGENTS.md 指令
    │       ├─→ 匹配 Skills
    │       ├─→ 读取 application_state（导航上下文）
    │       └─→ 决策调用 Actions
    │
    └─← 返回结果 ←── Action 执行 ←── 数据库读写
```

### 6.3 状态同步

```typescript
// 客户端订阅
import { useDbSync } from "@agent-native/core/client";

function App() {
  const queryClient = useQueryClient();
  useDbSync({ queryClient }); // SSE + 轮询回退
  
  return <Router />;
}

// 导航状态写入
import { useApplicationState } from "@agent-native/core/client";

function ProjectPage({ projectId }) {
  const [, setNavigation] = useApplicationState("navigation");
  
  useEffect(() => {
    setNavigation({ view: "project", projectId });
  }, [projectId]);
}
```

---

## 7. AI 集成设计

### 7.1 Agent 指令 (AGENTS.md)

```markdown
# AGENTS.md - PM 工作流平台 Agent 指令

## 角色
你是产品经理的 AI 助手，帮助用户完成产品工作流的各个环节。

## 核心规则
1. 所有建议都是建议性的，不强制用户执行
2. 生成内容后，提示用户确认和修改
3. 操作前询问用户，尤其是修改和删除操作
4. 记住用户的偏好和项目上下文

## 能力范围
- PRD 生成和检查
- 竞品分析调研
- 需求分类和优先级建议
- 原型走查分析
- 参数提取和配置
- 测试用例生成
- 流程建议
- 版本对比分析
- 关系关联建议

## 上下文感知
- 始终读取 navigation 状态了解用户当前视图
- 使用 view-screen action 获取当前页面详情
- 基于项目上下文提供相关建议

## 安全规则
- 删除操作需要确认
- 批量操作需要确认
- 跨项目操作禁止
```

### 7.2 Skills 定义

```
.agents/skills/
├── prd-generation/
│   └── SKILL.md          # PRD 生成技能
├── requirement-analysis/
│   └── SKILL.md          # 需求分析技能
├── competitor-research/
│   └── SKILL.md          # 竞品调研技能
├── prototype-check/
│   └── SKILL.md          # 原型走查技能
├── parameter-extract/
│   └── SKILL.md          # 参数提取技能
├── testcase-generate/
│   └── SKILL.md          # 测试用例生成技能
├── version-compare/
│   └── SKILL.md          # 版本对比技能
├── relation-suggest/
│   └── SKILL.md          # 关系建议技能
└── workflow-suggest/
    └── SKILL.md          # 流程建议技能
```

### 7.3 API Key 配置

```typescript
// settings 表存储
export const aiConfig = {
  provider: "openai" | "anthropic" | "local",
  apiKey: string,
  model: string,
  baseUrl?: string, // 本地模型地址
};
```

---

## 8. 安全与权限

### 8.1 数据隔离

| 层级 | 机制 |
|------|------|
| 项目隔离 | 所有表都有 `project_id` 字段，查询自动过滤 |
| 文件隔离 | 文件存储在 `data/projects/{projectId}/` |
| 版本隔离 | 版本快照独立存储 |

### 8.2 Action 权限

| Action | 权限控制 |
|--------|---------|
| 读取类 | `readOnly: true`，自动审计 |
| 写入类 | `needsApproval: false`，但删除操作需二次确认 |
| AI 配置 | `needsApproval: true`，涉及 API Key |
| 导入导出 | `toolCallable: false`，禁止 iframe 调用 |

### 8.3 审计日志

```typescript
// 自动审计配置
audit: {
  target: (args, result) => ({ type: "project", id: args.projectId }),
  summary: (args) => `修改项目 ${args.projectId}`,
  onRead: false,
  enabled: true,
  recordInputs: true,
}
```

---

## 9. 实施计划

### 9.1 阶段划分

| 阶段 | 周期 | 内容 | 交付物 |
|------|------|------|--------|
| **Phase 1** | 2 周 | 核心框架 + Project + Agent | 可创建项目，AI 对话可用 |
| **Phase 2** | 2 周 | PRD 编辑 + 检查 + 参数清单 | PRD 完整闭环 |
| **Phase 3** | 2 周 | 需求收集 + 竞品分析 + 原型 | 规划类模块完成 |
| **Phase 4** | 2 周 | 版本管理 + 追溯 + 工作流 | 核心能力完整 |
| **Phase 5** | 2 周 | 项目管理类 + 落地验收类 | 管理闭环 |
| **Phase 6** | 1 周 | 复盘迭代 + 赋能协作 | 全部模块完成 |
| **Phase 7** | 1 周 | 测试 + 优化 + 文档 | 稳定版本 |

### 9.2 依赖关系

```
Phase 1 (核心)
    │
    ├─→ Phase 2 (PRD)
    │       │
    │       ├─→ Phase 3 (规划)
    │       │
    │       └─→ Phase 4 (版本+追溯)
    │               │
    │               ├─→ Phase 5 (管理+验收)
    │               │
    │               └─→ Phase 6 (复盘+赋能)
    │                       │
    │                       └─→ Phase 7 (测试)
    │
    └─→ 所有阶段依赖 Project + Agent
```

---

## 10. 验收标准

### 10.1 整体标准

| # | 验收项 | 标准 |
|---|--------|------|
| 1 | 手动可用 | 关闭 AI 后，所有功能 100% 可用 |
| 2 | AI 增强 | 配置 API Key 后，AI 辅助功能正常工作 |
| 3 | 项目隔离 | 项目 A 数据在项目 B 中不可见 |
| 4 | 版本管理 | 支持创建、对比、回滚版本 |
| 5 | 关系追溯 | 支持双向追溯和影响分析 |
| 6 | 数据导出 | 所有表格支持 Excel 导出 |
| 7 | 离线可用 | 本地 SQLite，无需网络 |

### 10.2 模块验收

详见各模块边界定义中的验收标准。

---

## 附录

### A. 术语表

| 术语 | 说明 |
|------|------|
| Action | Agent Native 的可执行操作，TypeScript 函数 |
| Skill | Agent 的复用行为指南，Markdown 文件 |
| AGENTS.md | Agent 的始终生效指令 |
| Drizzle | TypeScript ORM |
| SSE | Server-Sent Events，实时推送 |
| PRD | Product Requirements Document，产品需求文档 |
| 走查 | 对原型进行逐项检查 |

### B. 参考文档

- Agent Native 文档: https://www.agent-native.com/docs
- Drizzle ORM: https://orm.drizzle.team
- React Router: https://reactrouter.com

---

**文档结束**
