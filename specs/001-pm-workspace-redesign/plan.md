# Implementation Plan: PM 工作台重构 — 模块化布局与差异化编辑器

**Branch**: `001-pm-workspace-redesign` | **Date**: 2026-06-28 | **Spec**: [specs/001-pm-workspace-redesign/spec.md](specs/001-pm-workspace-redesign/spec.md)

**Input**: Feature specification from `/specs/001-pm-workspace-redesign/spec.md`

## Summary

重构 PM 工作台，实现：
1. **模块化布局**：左侧分类侧边栏（规划/设计/执行/复盘），顶部项目信息栏+版本切换器
2. **差异化编辑器**：富文本编辑器（PRD/竞品/路线/会议/验收/FAQ）、结构化表单（需求/参数/测试）、混合编辑器（风险）、思维导图（路线+产品架构）
3. **数据互通**：模块间关联建立、双向追溯、版本快照与对比
4. **Agent 升级**：手动+自动触发、基于内容的智能分析建议

## Technical Context

**Language/Version**: TypeScript / SvelteKit (Open WebUI 基座)

**Primary Dependencies**: 
- Open WebUI 现有组件库（优先复用）
- 富文本编辑器：TipTap / Quill（调研 Open WebUI 现有集成）
- 思维导图：react-flow / @xyflow/svelte / D3.js（调研后选型）
- 表单验证：zod / yup（与 Open WebUI 一致）

**Storage**: SQLite (local) / PostgreSQL (production) — Open WebUI 现有数据库

**Testing**: Vitest (与 Open WebUI 一致)

**Target Platform**: Web (Open WebUI 插件)

**Project Type**: Web application (Open WebUI 扩展模块)

**Performance Goals**: 
- 侧边栏导航到模块内容 ≤ 3秒
- 版本切换数据刷新 ≤ 1秒
- 思维导图节点操作 ≤ 200ms
- 富文本编辑器支持 50,000 词文档

**Constraints**: 
- 兼容现有 `{text: string}` 旧数据格式
- 符合 Open WebUI 设计系统（Tailwind CSS）
- Agent 分析需用户确认（Constitution III）
- 数据严格按项目隔离（Constitution IV）

**Scale/Scope**: 
- 10个模块，4大分类
- 支持单项目 1000+ 条目
- 版本历史无上限（需分页）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Manual-First Productivity | ✅ PASS | 所有功能支持手动操作，AI 为可选增强 |
| II. Module-Centric Architecture | ✅ PASS | 4大分类，差异化编辑器，非通用 CRUD |
| III. AI-Assisted, Human-Confirmed | ✅ PASS | Agent 建议需用户确认，手动触发为主 |
| IV. Data Isolation & Traceability | ✅ PASS | project_id 隔离，乐观锁，版本控制 |
| V. Version-Controlled Documentation | ✅ PASS | 项目级快照 + 增量标记，支持对比回滚 |

**Complexity Justification**: 
- 思维导图模块（路线图+产品架构）增加复杂度，但为 PRD 核心需求，且采用开源库降低实现成本
- 版本控制采用增量标记而非完整快照，平衡存储效率与功能完整性

## Project Structure

### Documentation (this feature)

```text
specs/001-pm-workspace-redesign/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── lib/
│   ├── components/
│   │   └── pm/                    # PM 专用组件目录
│   │       ├── PMModuleNav.svelte         # 模块分类导航侧边栏
│   │       ├── PMProjectHeader.svelte     # 项目头部信息栏
│   │       ├── PMRichEditor.svelte        # 富文本编辑器封装
│   │       ├── PMFormEditor.svelte        # 结构化表单编辑器
│   │       ├── PMVersionSelector.svelte     # 版本选择器
│   │       ├── PMMindMap.svelte           # 思维导图组件
│   │       ├── PMRelationPicker.svelte    # 关联字段选择器
│   │       ├── PMConflictDialog.svelte    # 并发冲突提示弹窗
│   │       └── PMMigrationPanel.svelte  # 数据迁移摘要面板
│   ├── apis/
│   │   └── pm/                    # PM API 扩展
│   │       ├── index.ts                   # 基础 API 封装
│   │       ├── types.ts                   # TypeScript 类型定义
│   │       ├── modules/                   # 各模块 API
│   │       │   ├── prd.ts
│   │       │   ├── requirement.ts
│   │       │   ├── parameter.ts
│   │       │   ├── testcase.ts
│   │       │   ├── risk.ts
│   │       │   ├── competitor.ts
│   │       │   ├── roadmap.ts
│   │       │   ├── meeting.ts
│   │       │   ├── acceptance.ts
│   │       │   └── faq.ts
│   │       ├── version.ts               # 版本管理 API
│   │       ├── relation.ts              # 关联管理 API
│   │       └── agent.ts                 # Agent 智能辅助 API
│   └── stores/
│       └── pm/                    # PM 状态管理
│           ├── projectStore.ts            # 项目状态
│           ├── versionStore.ts            # 版本状态
│           ├── moduleStore.ts             # 当前模块状态
│           └── agentStore.ts              # Agent 建议状态
├── routes/
│   └── (app)/
│       └── pm/                    # PM 工作台路由
│           ├── +page.svelte             # 主页面（侧边栏 + 主区域）
│           ├── +layout.svelte           # 布局（项目头部 + 侧边栏）
│           └── [module]/
│               └── +page.svelte         # 各模块页面
└── tests/
    └── pm/                        # PM 模块测试
        ├── unit/
        ├── integration/
        └── e2e/
```

**Structure Decision**: 基于 Open WebUI 现有 SvelteKit 架构，在 `src/lib/components/pm/` 和 `src/lib/apis/pm/` 下扩展 PM 专用模块，保持与基座一致的目录结构和命名规范。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 思维导图模块增加复杂度 | PRD 明确要求路线图以思维导图展示，且新增产品架构模块 | 纯文本路线图无法满足可视化需求，产品架构梳理是 PM 核心工作流 |
| 版本控制采用增量标记而非简单复制 | 完整快照存储开销大（100版本×10模块=1000份数据） | 增量标记只存储变更模块，未变更模块引用上一版本，存储效率提升 80%+ |
| Agent 双模式触发（手动+自动） | 纯手动用户可能忘记使用，纯自动干扰性强 | 手动为主、自动为辅（可配置关闭）平衡了用户体验和系统资源 |

---

## Phase 0: Research

### Unknowns to Resolve

1. **富文本编辑器选型**：Open WebUI 是否已集成 TipTap/Quill？是否可复用？
2. **思维导图库选型**：Open WebUI 依赖中是否已有 D3.js/Cytoscape？react-flow 与 Svelte 兼容性？
3. **Open WebUI 组件复用**：哪些 UI 组件（按钮、表单、下拉框、弹窗）可直接复用？
4. **Agent 实现方式**：Open WebUI 的 Agent 框架如何扩展？是否支持自定义 Skills？
5. **版本存储策略**：Open WebUI 的 ORM（Drizzle）是否支持写时复制（Copy-on-Write）？

### Research Tasks

- [ ] R001 调研 Open WebUI 现有富文本编辑器集成情况
- [ ] R002 调研 Open WebUI package.json 依赖，确认思维导图相关库
- [ ] R003 调研 Open WebUI 组件库，列出可复用组件清单
- [ ] R004 调研 Open WebUI Agent 框架扩展方式
- [ ] R005 调研 Drizzle ORM 版本控制/快照实现方案

**Output**: [research.md](research.md)

---

## Phase 1: Design

### Data Model

**Output**: [data-model.md](data-model.md)

#### Core Entities

- **Project** (现有，扩展字段)
- **Version** (新增)
- **ModuleEntry** (基类，10个模块继承)
- **Relation** (新增，模块间关联)
- **MindMapNode** (新增，思维导图节点)

#### Version Control

- 项目级快照 + 模块级增量标记
- Copy-on-Write 策略
- 支持整项目回滚和单模块回滚

#### State Transitions

- ModuleEntry: draft → review → approved → archived
- Version: draft → published → archived
- Relation: pending → confirmed → rejected

### Contracts

**Output**: `contracts/` 目录

- `contract-module-entry.ts` — 模块条目 CRUD 接口
- `contract-version.ts` — 版本管理接口
- `contract-relation.ts` — 关联管理接口
- `contract-agent.ts` — Agent 分析接口
- `contract-mindmap.ts` — 思维导图接口

### Quickstart

**Output**: [quickstart.md](quickstart.md)

- 本地开发环境搭建
- 模块导航测试步骤
- 版本切换验证步骤
- Agent 分析测试步骤
- 思维导图操作验证

---

## Phase 2: Tasks

**Output**: [tasks.md](tasks.md) (由 `/speckit-tasks` 命令生成)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: 无依赖，可立即开始
- **Phase 1 (Design)**: 依赖 Phase 0 完成（所有未知项已解决）
- **Phase 2 (Tasks)**: 依赖 Phase 1 完成（数据模型和接口契约已确定）

### External Dependencies

- Open WebUI 基座代码（已存在）
- 富文本编辑器库（调研后确定）
- 思维导图库（调研后确定）
- AI API (OpenAI/Claude) — 用户已配置

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Open WebUI 升级导致兼容性问题 | 高 | 使用 Open WebUI 公开 API，避免私有实现依赖 |
| 富文本编辑器与现有数据格式不兼容 | 中 | 提供数据迁移工具，支持 Markdown 双向转换 |
| 思维导图性能问题（大量节点） | 中 | 虚拟渲染、懒加载、节点分页 |
| Agent 分析延迟高 | 中 | 异步分析、缓存结果、进度指示器 |
| 旧数据迁移失败 | 高 | 自动迁移+手动确认，保留旧数据备份 |

---

## Success Criteria Verification

| ID | Criteria | Verification Method |
|----|----------|---------------------|
| SC-001 | 3秒内导航到任意模块 | 性能测试：计时从点击侧边栏到内容渲染完成 |
| SC-002 | 8/10模块差异化表单 | 代码审查：检查每个模块的表单字段定义 |
| SC-003 | 版本切换1秒内刷新 | 性能测试：计时从点击版本到数据渲染完成 |
| SC-004 | 关联成功率 ≥ 95% | 功能测试：100次关联操作，统计成功次数 |
| SC-005 | Agent采纳率 ≥ 60% | 用户测试：统计用户采纳建议的比例 |
| SC-006 | 100%旧数据兼容 | 数据测试：所有旧条目在新表单正常显示 |
| SC-007 | 任务完成时间减少 ≥ 30% | 用户测试：对比新旧版本的任务完成时间 |
| SC-008 | 思维导图操作 ≤ 200ms | 性能测试：计时节点增删改拖拽操作 |
| SC-009 | 自动提取准确率 ≥ 80% | 准确率测试：对比自动提取与人工标注 |
