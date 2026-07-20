# Tasks: 产品架构模块版本溯源与需求关联

**Feature**: 004-arch-module-version-demand
**Date**: 2026-07-08
**Branch**: `004-arch-module-version-demand`

---

## Dependencies

```text
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (US4) → Phase 7 (US5) → Phase 8 (Polish)
```

**并行机会**:
- Phase 3 (US1) 和 Phase 4 (US2) 的部分任务可并行（数据模型独立）
- Phase 6 (US4) 思维导图可与 Phase 5 (US3) 表格视图并行开发

---

## Phase 1: Setup

**Goal**: 项目初始化和基础设施准备

- [x] T001 [P] 创建 PM 模块目录结构 `src/lib/components/pm/architecture/`
- [x] T002 [P] 创建 API 目录 `src/lib/apis/pm/`
- [x] T003 [P] 创建数据模型目录 `src/lib/models/pm/`
- [x] T004 [P] 创建状态管理目录 `src/lib/stores/pm/`
- [x] T005 [P] 创建路由目录 `src/routes/pm/architecture/`
- [x] T006 [P] 安装思维导图依赖 `npm install @antv/g6`

---

## Phase 2: Foundational

**Goal**: 数据库迁移和共享组件

- [x] T007 创建数据库迁移脚本 `migrations/004_arch_module_version_demand.sql`
- [x] T008 [P] 创建共享数据模型 `src/lib/models/pm/architecture.ts`
- [x] T009 [P] 创建通用表格组件 `src/lib/components/pm/shared/DataTable.svelte`
- [x] T010 [P] 创建确认弹窗组件 `src/lib/components/pm/shared/ConfirmModal.svelte`
- [x] T011 创建 API 基础层 `src/lib/apis/pm/architecture.ts`
- [x] T012 创建状态管理 Store `src/lib/stores/pm/architecture.ts`

---

## Phase 3: User Story 1 - 模块/功能/参数统一版本溯源

**Goal**: 实现版本溯源核心功能
**Priority**: P1
**Independent Test**: 创建模块/功能/参数后，检查 create_version 自动绑定，编辑后 version_record 追加记录

- [ ] T013 [P] [US1] 创建 Module 数据模型（含 create_version, version_record, demand_relation）
- [ ] T014 [P] [US1] 创建 Function 数据模型（含 create_version, version_record, demand_relation）
- [ ] T015 [P] [US1] 创建 Parameter 数据模型（含 create_version, version_record, demand_relation）
- [ ] T016 [US1] 实现版本自动回填逻辑（新增条目时自动设置 create_version）
- [ ] T017 [US1] 实现版本履历追加逻辑（编辑条目时自动追加 version_record）
- [ ] T018 [US1] 实现父子版本独立逻辑（父模块修改不影响子条目）
- [ ] T019 [US1] 创建 Module API 端点（GET/POST/PUT/DELETE）
- [ ] T020 [US1] 创建 Function API 端点（GET/POST/PUT/DELETE）
- [ ] T021 [US1] 创建 Parameter API 端点（GET/POST/PUT/DELETE）
- [ ] T022 [US1] 创建版本履历导出 API 端点（CSV 格式）

---

## Phase 4: User Story 2 - 条目与需求的多对多关联管理

**Goal**: 实现需求关联功能
**Priority**: P1
**Independent Test**: 在表格或弹窗中绑定/解绑需求，检查需求标签展示

- [x] T023 [P] [US2] 创建需求关联标签组件 `src/lib/components/pm/architecture/DemandRelationTag.svelte`
- [x] T024 [P] [US2] 创建需求关联弹窗组件 `src/lib/components/pm/architecture/DemandRelationModal.svelte`
- [ ] T025 [US2] 实现需求绑定逻辑（支持手动录入和下拉选择）
- [ ] T026 [US2] 实现需求解绑逻辑（单独解绑和批量清空）
- [ ] T027 [US2] 实现需求标签展示（表格视图和详情弹窗）
- [ ] T028 [US2] 实现需求关联数据持久化（API 层）

---

## Phase 5: User Story 3 - 表格视图改版与统一操作

**Goal**: 改版表格视图，统一操作列
**Priority**: P1
**Independent Test**: 打开表格视图，检查列顺序、版本履历浮窗、操作按钮

- [x] T029 [P] [US3] 创建表格视图组件 `src/lib/components/pm/architecture/ModuleTable.svelte`
- [x] T030 [P] [US3] 实现固定列顺序（名称 → 类型/KEY → 数据类型 → 必填 → 创建版本 → 版本履历 → 关联需求 → 描述 → 操作）
- [x] T031 [P] [US3] 创建版本履历悬浮浮窗组件 `src/lib/components/pm/architecture/VersionHistoryPopover.svelte`
- [ ] T032 [US3] 实现浮窗展示逻辑（最近 20 条记录 + 查看更多按钮）
- [x] T033 [US3] 实现 CSV 导出功能（前端生成 Blob 下载）
- [x] T034 [US3] 实现操作列统一按钮（编辑、新增下级、删除、复制、查看溯源详情）
- [x] T035 [US3] 实现"新增下级"按钮显隐控制（模块→功能，功能→参数，参数→无）
- [x] T036 [US3] 创建新增/编辑弹窗组件 `src/lib/components/pm/architecture/ModuleForm.svelte`
- [x] T037 [US3] 实现弹窗内创建版本只读展示
- [x] T038 [US3] 实现弹窗内需求关联管理（新增/解绑）

---

## Phase 6: User Story 4 - 思维导图只读浏览与节点详情

**Goal**: 实现思维导图只读浏览
**Priority**: P2
**Independent Test**: 切换至思维导图视图，检查节点渲染、点击弹窗、交互限制

- [x] T039 [P] [US4] 创建思维导图视图组件 `src/lib/components/pm/architecture/MindMapView.svelte`
- [x] T040 [P] [US4] 实现树形数据转换（模块→功能→参数）
- [x] T041 [US4] 配置 AntV G6 只读模式（禁止拖拽、编辑、新增、删除）
- [x] T042 [US4] 实现节点点击事件（弹出详情弹窗）
- [x] T043 [US4] 创建节点详情弹窗组件 `src/lib/components/pm/architecture/NodeDetailModal.svelte`
- [x] T044 [US4] 实现详情弹窗四个分区（基础元信息、版本溯源、关联需求、操作按钮）
- [x] T045 [US4] 实现 Tab 切换（思维导图/表格）

---

## Phase 7: User Story 5 - 存量数据兼容与迁移

**Goal**: 存量数据平滑迁移
**Priority**: P2
**Independent Test**: 执行迁移脚本，检查 create_version 填充，首次编辑生成版本记录

- [x] T046 [US5] 创建数据迁移脚本 `migrations/004_arch_module_version_demand.sql`
- [x] T047 [US5] 实现存量数据默认值填充（create_version = '1.0.0', version_record = [], demand_relation = []）
- [ ] T048 [US5] 实现首次编辑触发版本记录生成逻辑
- [ ] T049 [US5] 创建迁移验证测试

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: 完善和跨功能优化

- [ ] T050 [P] 实现软删除逻辑（is_deleted + deleted_at）
- [ ] T051 [P] 实现复制条目逻辑（全新 create_version，可选复制 demand_relation）
- [ ] T052 [P] 实现版本号为空时的默认处理（系统版本 → '1.0.0'）
- [ ] T053 添加 API 向后兼容处理（旧客户端忽略未知字段）
- [x] T054 创建主页面 `src/routes/pm/architecture/+page.svelte`
- [x] T055 创建服务端加载 `src/routes/pm/architecture/+page.server.ts`
- [ ] T056 性能优化（版本履历浮窗加载 < 500ms）
- [ ] T057 添加错误处理和边界情况处理
- [ ] T058 编写 E2E 测试（Playwright）
- [ ] T059 编写单元测试（Vitest）

---

## Implementation Strategy

### MVP 范围

**最小可用产品**：User Story 1（版本溯源）+ User Story 3（表格视图改版）

- 核心功能：创建/编辑模块、功能、参数时自动记录版本
- 基础 UI：表格视图展示版本信息
- 不包含：需求关联、思维导图、存量迁移

### 增量交付

1. **Wave 1** (P1): US1 + US3 → 核心版本溯源 + 表格视图
2. **Wave 2** (P1): US2 → 需求关联管理
3. **Wave 3** (P2): US4 → 思维导图浏览
4. **Wave 4** (P2): US5 → 存量数据迁移
5. **Wave 5**: Polish → 软删除、复制、性能优化、测试

### 并行执行建议

- **前端团队**：T029-T038（表格视图 + 弹窗）
- **后端团队**：T013-T022（数据模型 + API）
- **独立开发**：T039-T045（思维导图，依赖后端 API 但可 mock 数据）

---

## Task Summary

| 类别 | 数量 |
|------|------|
| 总任务数 | 59 |
| Setup 阶段 | 6 |
| Foundational 阶段 | 6 |
| US1 (版本溯源) | 10 |
| US2 (需求关联) | 6 |
| US3 (表格视图) | 10 |
| US4 (思维导图) | 7 |
| US5 (存量迁移) | 4 |
| Polish 阶段 | 10 |
| 可并行任务 | 23 |

---

## File Paths Reference

```text
src/
├── lib/
│   ├── components/
│   │   └── pm/
│   │       ├── architecture/
│   │       │   ├── ModuleTable.svelte
│   │       │   ├── ModuleForm.svelte
│   │       │   ├── VersionHistoryPopover.svelte
│   │       │   ├── DemandRelationTag.svelte
│   │       │   ├── DemandRelationModal.svelte
│   │       │   ├── MindMapView.svelte
│   │       │   └── NodeDetailModal.svelte
│   │       └── shared/
│   │           ├── DataTable.svelte
│   │           └── ConfirmModal.svelte
│   ├── apis/
│   │   └── pm/
│   │       └── architecture.ts
│   ├── models/
│   │   └── pm/
│   │       └── architecture.ts
│   └── stores/
│       └── pm/
│           └── architecture.ts
├── routes/
│   └── pm/
│       └── architecture/
│           ├── +page.svelte
│           └── +page.server.ts
└── migrations/
    └── 004_arch_module_version_demand.sql
```