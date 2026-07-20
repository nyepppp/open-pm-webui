# Implementation Plan: 产品架构页面缺陷修复与交互重构

**Branch**: `[005-arch-bugfix-redesign]` | **Date**: 2026-07-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-arch-bugfix-redesign/spec.md`

## Summary

修复产品架构页面多个操作失效 Bug 并重构交互设计。核心工作包括：
1. 修复操作按钮失效、新增模块卡死、更新条目失败等阻塞性 Bug
2. 统一表格组件为 ArchitectureTable，删除 ModuleTable 及其依赖的 architecture store
3. 修复思维导图层级结构（项目→模块→功能），修正根节点显示
4. 将参数新建改为批量新建表单（all-or-nothing 提交策略）
5. 修复"创建版本"列不显示版本信息、"关联需求"交互不清晰
6. 移除页面顶部"选择版本"和"AI"按钮

## Technical Context

**Language/Version**: TypeScript + SvelteKit (Open WebUI 现有架构)

**Primary Dependencies**: 
- SvelteKit (前端框架)
- Tailwind CSS (样式系统)
- AntV G6 (思维导图渲染)
- svelte-sonner (toast 通知)

**Storage**: SQLite (本地) / PostgreSQL (生产) via Open WebUI ORM

**Testing**: Playwright (E2E) + Vitest (单元测试)

**Target Platform**: Web浏览器 (桌面 + 移动端响应式)

**Project Type**: Web application (Open WebUI 扩展)

**Performance Goals**: 
- 操作按钮响应 < 200ms
- 批量新建 5 条参数 < 3s
- 思维导图渲染 < 2s (100个节点)
- 编辑后数据刷新 < 1s

**Constraints**: 
- 单用户工作台，无需并发控制
- 必须兼容 Open WebUI 现有设计系统
- 删除 ModuleTable 需确保无其他组件引用其导出

**Scale/Scope**: 
- 单项目内模块/功能/参数条目，预计 < 1000 条
- 涉及 15+ 组件文件修改/删除

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Manual-First Productivity | ✅ PASS | 所有修复和批量新建均支持纯手动操作，不依赖 AI |
| II. Module-Centric Architecture | ✅ PASS | 统一 ArchitectureTable 符合模块差异化原则 |
| III. AI-Assisted, Human-Confirmed | ✅ PASS | 移除 AI 按钮符合此原则（AI 非必需） |
| IV. Data Isolation & Traceability | ✅ PASS | 版本信息修复增强追溯能力 |
| V. Version-Controlled Documentation | ✅ PASS | 创建版本列修复直接支持版本控制可见性 |

**Result**: All gates PASS. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/005-arch-bugfix-redesign/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── routes/(app)/pm/[projectId]/architecture/
│   └── +page.svelte                    # 主页面（修改：移除版本选择器/AI按钮，统一表格组件）
├── lib/components/pm/architecture/
│   ├── ArchitectureTable.svelte        # 保留：主表格组件（修复操作按钮、版本显示、需求交互）
│   ├── MindMapView.svelte              # 修改：修正层级结构，根节点显示项目名称
│   ├── NodeDetailModal.svelte          # 修改：显示版本和描述信息
│   ├── EditItemModal.svelte            # 修改：修复数据提交逻辑
│   ├── ModuleForm.svelte               # 修改：修复版本信息、需求关联交互
│   ├── AddFeatureModal.svelte          # 可能修改或删除
│   ├── BatchParameterForm.svelte       # 新增：批量参数新建表单
│   ├── VersionHistoryPopover.svelte    # 保留
│   ├── DemandRelationModal.svelte      # 保留
│   ├── DemandRelationTag.svelte        # 保留
│   ├── ModuleCard.svelte               # 评估是否删除（ModuleTable 相关）
│   ├── ModuleFeatureManager.svelte     # 评估是否删除（ModuleTable 相关）
│   ├── ModuleFeatureTree.svelte        # 评估是否删除（ModuleTable 相关）
│   ├── ArchitectureError.svelte        # 保留
│   ├── ArchitectureLoading.svelte      # 保留
│   └── ArchitectureTabBar.svelte       # 保留
├── lib/stores/pm/
│   ├── architectureStore.ts            # 保留：主数据 store（修复 createVersion 映射）
│   └── architecture.ts                 # 删除：ModuleTable 依赖的旧 store
├── lib/models/pm/
│   └── architecture.ts                 # 评估：Module/Function/Parameter 模型定义
├── lib/apis/pm/
│   ├── index.ts                        # 保留：API 调用（修复 updateEntry 签名）
│   └── modules/                        # 保留
└── lib/components/pm/
    └── PMVersionSelector.svelte        # 评估：版本选择器组件（页面不再引用）
```

**Structure Decision**: 采用 Single project 结构，所有修改集中在 `src/lib/components/pm/architecture/` 和 `src/routes/(app)/pm/[projectId]/architecture/` 目录下。

## Complexity Tracking

> No Constitution violations. Table left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
