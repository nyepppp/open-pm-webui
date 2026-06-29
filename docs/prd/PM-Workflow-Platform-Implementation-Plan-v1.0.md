# PM 工作流平台 - 实施计划

## 基于 Agent Native 框架

**版本**: v1.0  
**日期**: 2026-06-27

---

## 1. 技术栈确认

| 层级 | 技术 | 版本 |
|------|------|------|
| 框架 | Agent Native | latest |
| 前端 | React + Vite + React Router | 18+ / 7+ |
| UI 组件 | Ant Design | 5.x |
| 状态管理 | React Query (TanStack Query) | 5.x |
| ORM | Drizzle | latest |
| 数据库 | SQLite (本地) / PostgreSQL (生产) | 3.x / 15+ |
| 语言 | TypeScript | 5.x |
| AI SDK | OpenAI / Anthropic SDK | latest |
| 构建 | Vite | 5.x |

---

## 2. 开发环境准备

### 2.1 初始化 Agent Native 项目

```bash
# 创建项目
npx @agent-native/core@latest create pm-workflow-platform --template chat

# 进入目录
cd pm-workflow-platform

# 安装依赖
pnpm install

# 安装 UI 库
pnpm add antd @ant-design/icons

# 安装图表库
pnpm add echarts @echarts/react

# 安装工具库
pnpm add dayjs lodash-es

# 安装类型定义
pnpm add -D @types/lodash-es
```

### 2.2 项目结构

```
pm-workflow-platform/
├── actions/                    # Actions
│   ├── project/
│   ├── workflow/
│   ├── version/
│   ├── relation/
│   ├── requirement/
│   ├── competitor/
│   ├── roadmap/
│   ├── prd/
│   ├── prd-check/
│   ├── prototype/
│   ├── parameter/
│   ├── prototype-prompt/
│   ├── testcase/
│   ├── project-init/
│   ├── schedule/
│   ├── meeting/
│   ├── risk/
│   ├── deliverable/
│   ├── acceptance/
│   ├── issue/
│   ├── report/
│   ├── retrospective/
│   ├── iteration/
│   ├── training/
│   ├── manual/
│   ├── faq/
│   ├── presentation/
│   ├── agent/
│   └── setting/
│
├── app/                        # React 前端
│   ├── routes/                # 页面路由
│   │   ├── _index.tsx         # 项目列表
│   │   ├── projects.$id.tsx   # 项目工作台
│   │   ├── projects.$id.workflow.tsx
│   │   ├── projects.$id.requirements.tsx
│   │   ├── projects.$id.competitors.tsx
│   │   ├── projects.$id.roadmap.tsx
│   │   ├── projects.$id.prd.tsx
│   │   ├── projects.$id.prd.$docId.tsx
│   │   ├── projects.$id.prd.$docId.check.tsx
│   │   ├── projects.$id.prototype.tsx
│   │   ├── projects.$id.parameters.tsx
│   │   ├── projects.$id.testcases.tsx
│   │   ├── projects.$id.schedule.tsx
│   │   ├── projects.$id.meetings.tsx
│   │   ├── projects.$id.risks.tsx
│   │   ├── projects.$id.deliverables.tsx
│   │   ├── projects.$id.acceptance.tsx
│   │   ├── projects.$id.issues.tsx
│   │   ├── projects.$id.versions.tsx
│   │   ├── projects.$id.traceability.tsx
│   │   ├── projects.$id.documents.tsx
│   │   └── settings.tsx
│   │
│   ├── components/            # 业务组件
│   │   ├── ProjectList/
│   │   ├── WorkflowBoard/
│   │   ├── RequirementTable/
│   │   ├── CompetitorMatrix/
│   │   ├── RoadmapGantt/
│   │   ├── PRDEditor/
│   │   ├── PRDCheckPanel/
│   │   ├── PrototypeViewer/
│   │   ├── ParameterTable/
│   │   ├── TestcaseTable/
│   │   ├── ScheduleGantt/
│   │   ├── MeetingList/
│   │   ├── RiskMatrix/
│   │   ├── DeliverableChecklist/
│   │   ├── AcceptancePanel/
│   │   ├── IssueTracker/
│   │   ├── VersionManager/
│   │   ├── RelationGraph/
│   │   ├── DocumentCenter/
│   │   ├── AgentChatSurface/
│   │   ├── TraceabilityPanel/
│   │   └── Layout/
│   │
│   ├── hooks/                 # 自定义 Hooks
│   ├── utils/                 # 工具函数
│   ├── types/                 # 类型定义
│   └── styles/                # 全局样式
│
├── server/                     # Nitro API
│   └── routes/
│
├── db/                         # 数据库
│   ├── schema.ts              # 表定义
│   ├── migrations/            # 迁移文件
│   └── seed.ts                # 种子数据
│
├── .agents/                    # Agent Skills
│   └── skills/
│       ├── prd-generation/
│       ├── requirement-analysis/
│       ├── competitor-research/
│       ├── prototype-check/
│       ├── parameter-extract/
│       ├── testcase-generate/
│       ├── version-compare/
│       ├── relation-suggest/
│       └── workflow-suggest/
│
├── AGENTS.md                   # Agent 指令
├── data/                       # 本地数据
│   └── app.db
│
└── docs/                       # 文档
    └── prd/
```

---

## 3. 阶段划分

### Phase 1: 核心框架 (2 周)

**目标**: 搭建 Agent Native 框架，实现 Project 和 Agent 核心功能

**任务清单**:

| # | 任务 | 工时 | 依赖 |
|---|------|------|------|
| 1.1 | 初始化 Agent Native 项目 | 1d | - |
| 1.2 | 配置 Drizzle ORM 和表结构 | 2d | 1.1 |
| 1.3 | 实现项目创建/列表/切换 | 2d | 1.2 |
| 1.4 | 实现项目数据隔离 | 1d | 1.3 |
| 1.5 | 配置 AI 接口和 Agent 基础 | 2d | 1.1 |
| 1.6 | 实现 AI 对话功能 | 2d | 1.5 |
| 1.7 | 前端项目列表页面 | 2d | 1.3 |
| 1.8 | 测试和修复 | 2d | 1.6 |

**交付物**:
- 可创建/切换项目
- AI 对话可用
- 基础框架稳定

---

### Phase 2: PRD 核心闭环 (2 周)

**目标**: 实现 PRD 编辑、检查、参数清单完整闭环

**任务清单**:

| # | 任务 | 工时 | 依赖 |
|---|------|------|------|
| 2.1 | PRD 编辑器（富文本） | 3d | Phase 1 |
| 2.2 | PRD 章节管理 | 2d | 2.1 |
| 2.3 | PRD AI 生成初稿 | 2d | 2.1 |
| 2.4 | PRD 检查规则库 | 3d | 2.1 |
| 2.5 | PRD 检查执行 | 2d | 2.4 |
| 2.6 | 参数清单表格 | 2d | Phase 1 |
| 2.7 | 参数提取（AI） | 2d | 2.6 |
| 2.8 | 参数嵌入 PRD | 1d | 2.1, 2.6 |
| 2.9 | 测试和修复 | 3d | 2.7 |

**交付物**:
- PRD 完整编辑
- 多级检查规则
- 参数清单管理
- PRD-参数联动

---

### Phase 3: 规划类模块 (2 周)

**目标**: 实现需求收集、竞品分析、产品路线图

**任务清单**:

| # | 任务 | 工时 | 依赖 |
|---|------|------|------|
| 3.1 | 需求收集表格 | 2d | Phase 1 |
| 3.2 | Excel 导入/导出 | 2d | 3.1 |
| 3.3 | 需求 AI 分析分类 | 2d | 3.1 |
| 3.4 | 竞品对比矩阵 | 3d | Phase 1 |
| 3.5 | AI 竞品调研 | 2d | 3.4 |
| 3.6 | 产品路线图（甘特图） | 3d | Phase 1 |
| 3.7 | 路线图拖拽编辑 | 2d | 3.6 |
| 3.8 | 测试和修复 | 2d | 3.7 |

**交付物**:
- 需求收集模块
- 竞品分析模块
- 产品路线图

---

### Phase 4: 版本与追溯 (2 周)

**目标**: 实现版本管理、关系追溯、工作流

**任务清单**:

| # | 任务 | 工时 | 依赖 |
|---|------|------|------|
| 4.1 | 版本创建和快照 | 2d | Phase 1 |
| 4.2 | 版本对比（diff） | 3d | 4.1 |
| 4.3 | 版本回滚 | 2d | 4.1 |
| 4.4 | 关系建模 | 2d | Phase 1 |
| 4.5 | 关系自动关联（AI） | 2d | 4.4 |
| 4.6 | 影响分析 | 2d | 4.4 |
| 4.7 | 关系可视化 | 3d | 4.4 |
| 4.8 | 工作流引擎 | 2d | Phase 1 |
| 4.9 | 工作流看板 | 2d | 4.8 |
| 4.10 | 测试和修复 | 2d | 4.9 |

**交付物**:
- 版本管理完整
- 关系追溯可用
- 工作流看板

---

### Phase 5: 项目管理 + 落地验收 (2 周)

**目标**: 实现管理类和验收类模块

**任务清单**:

| # | 任务 | 工时 | 依赖 |
|---|------|------|------|
| 5.1 | 立项表单 | 1d | Phase 1 |
| 5.2 | 排期甘特图 | 2d | Phase 1 |
| 5.3 | 评审纪要 | 2d | Phase 1 |
| 5.4 | 风险管控 | 2d | Phase 1 |
| 5.5 | 交付物料清单 | 2d | Phase 1 |
| 5.6 | 验收文档 | 2d | Phase 2 |
| 5.7 | 问题闭环跟踪 | 3d | Phase 2 |
| 5.8 | 测试和修复 | 2d | 5.7 |

**交付物**:
- 立项/排期/评审/风险/交付
- 验收/问题闭环

---

### Phase 6: 复盘迭代 + 赋能协作 (1 周)

**目标**: 实现复盘迭代和赋能协作模块

**任务清单**:

| # | 任务 | 工时 | 依赖 |
|---|------|------|------|
| 6.1 | 数据分析报告 | 2d | Phase 1 |
| 6.2 | 版本复盘 | 2d | Phase 4 |
| 6.3 | 优化迭代方案 | 2d | Phase 4 |
| 6.4 | 培训素材 | 1d | Phase 1 |
| 6.5 | 操作手册 | 1d | Phase 1 |
| 6.6 | FAQ | 1d | Phase 1 |
| 6.7 | 宣讲材料 | 1d | Phase 1 |

**交付物**:
- 复盘迭代模块
- 赋能协作模块

---

### Phase 7: 测试优化 (1 周)

**目标**: 测试、优化、文档

**任务清单**:

| # | 任务 | 工时 |
|---|------|------|
| 7.1 | 单元测试 | 2d |
| 7.2 | 集成测试 | 2d |
| 7.3 | 性能优化 | 2d |
| 7.4 | 文档完善 | 1d |
| 7.5 | Bug 修复 | 2d |

---

## 4. 总时间表

```
Phase 1: 核心框架          ████████░░░░░░░░░░░░  2周
Phase 2: PRD 核心闭环       ████████░░░░░░░░░░░░  2周
Phase 3: 规划类模块         ████████░░░░░░░░░░░░  2周
Phase 4: 版本与追溯         ████████░░░░░░░░░░░░  2周
Phase 5: 管理+验收          ████████░░░░░░░░░░░░  2周
Phase 6: 复盘+赋能          ████░░░░░░░░░░░░░░░░  1周
Phase 7: 测试优化           ████░░░░░░░░░░░░░░░░  1周
────────────────────────────────────────────────
总计: 12 周 (3 个月)
```

---

## 5. 关键里程碑

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1 | 第 2 周末 | 可创建项目，AI 对话可用 |
| M2 | 第 4 周末 | PRD 完整闭环可用 |
| M3 | 第 6 周末 | 规划类模块完成 |
| M4 | 第 8 周末 | 版本+追溯+工作流可用 |
| M5 | 第 10 周末 | 管理+验收闭环 |
| M6 | 第 11 周末 | 全部模块完成 |
| M7 | 第 12 周末 | 稳定版本发布 |

---

## 6. 风险和对策

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| Agent Native 框架限制 | 中 | 高 | 提前验证框架能力，必要时自定义扩展 |
| AI 接口不稳定 | 中 | 中 | 完善的 fallback 机制，手动路径优先 |
| 需求变更 | 高 | 中 | 模块化设计，降低耦合 |
| 性能问题 | 中 | 中 | 提前设计索引，定期性能测试 |
| 数据丢失 | 低 | 高 | 自动备份，导出导入功能 |

---

## 7. 团队配置

| 角色 | 人数 | 职责 |
|------|------|------|
| 前端开发 | 2 | React 组件、页面、交互 |
| 后端开发 | 1 | Actions、数据库、AI 集成 |
| 产品 | 1 | 需求确认、验收 |
| UI 设计 | 1 | 界面设计、交互优化 |

---

## 8. 验收标准

### 8.1 整体标准

| # | 验收项 | 标准 |
|---|--------|------|
| 1 | 手动可用 | 关闭 AI 后，所有功能 100% 可用 |
| 2 | AI 增强 | 配置 API Key 后，AI 辅助功能正常工作 |
| 3 | 项目隔离 | 项目 A 数据在项目 B 中不可见 |
| 4 | 版本管理 | 支持创建、对比、回滚版本 |
| 5 | 关系追溯 | 支持双向追溯和影响分析 |
| 6 | 数据导出 | 所有表格支持 Excel 导出 |
| 7 | 离线可用 | 本地 SQLite，无需网络 |

### 8.2 性能标准

| 指标 | 目标 |
|------|------|
| 首屏加载 | < 3s |
| Action 响应 | < 500ms |
| AI 首字响应 | < 3s |
| 表格渲染 | < 100 行/100ms |
| 关系图节点 | < 100 个/500ms |

---

## 9. 交付清单

### 9.1 代码

- [ ] Agent Native 项目完整代码
- [ ] 28 个 Actions 实现
- [ ] 前端页面和组件
- [ ] 数据库迁移脚本

### 9.2 文档

- [x] PRD 文档
- [x] 数据库设计文档
- [x] API 设计文档
- [ ] 部署文档
- [ ] 用户手册

### 9.3 测试

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 性能测试报告

---

## 10. 后续迭代

### V1.1 (后续)

- [ ] 团队协作功能
- [ ] 实时同步
- [ ] 更多 AI 模型支持
- [ ] 移动端适配
- [ ] 插件系统

### V1.2 (后续)

- [ ] 多项目管理仪表盘
- [ ] 数据可视化增强
- [ ] 自动化工作流
- [ ] 集成第三方工具（Jira、飞书等）

---

**文档结束**
