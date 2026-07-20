# Implementation Plan: 产品架构模块版本溯源与需求关联

**Branch**: `[004-arch-module-version-demand]` | **Date**: 2026-07-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-arch-module-version-demand/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

为产品架构模块（模块/功能/参数）增加版本溯源与需求关联能力。核心功能包括：
1. 三级条目统一增加 `create_version`、`version_record`、`demand_relation` 字段
2. 表格视图改版，新增版本履历悬浮浮窗（支持 CSV 导出）和关联需求标签
3. 思维导图只读浏览与节点详情弹窗
4. 新增/编辑弹窗统一逻辑，支持创建版本自动回填和需求关联管理
5. 存量数据兼容迁移

## Technical Context

**Language/Version**: TypeScript + SvelteKit (Open WebUI 现有架构)

**Primary Dependencies**: 
- SvelteKit (前端框架)
- Tailwind CSS (样式系统)
- SQLite/PostgreSQL (数据库)
- AntV G6 或 D3.js (思维导图渲染)

**Storage**: SQLite (本地) / PostgreSQL (生产) via Open WebUI ORM

**Testing**: Playwright (E2E) + Vitest (单元测试)

**Target Platform**: Web浏览器 (桌面 + 移动端响应式)

**Project Type**: Web application (Open WebUI 扩展)

**Performance Goals**: 
- 版本履历浮窗加载 < 500ms
- 表格视图渲染 < 1s (100条数据)
- 思维导图渲染 < 2s (100个节点)

**Constraints**: 
- 单用户工作台，无需并发控制
- 必须兼容 Open WebUI 现有设计系统
- API 需保持向后兼容

**Scale/Scope**: 
- 单项目内模块/功能/参数条目，预计 < 1000 条
- 版本履历单条目预计 < 100 条

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 检查项

| 原则 | 状态 | 说明 |
|------|------|------|
| I. Manual-First Productivity | ✅ | 所有操作支持纯手动完成，无需 AI 辅助 |
| II. Module-Centric Architecture | ✅ | 功能围绕产品架构模块组织，符合业务语义 |
| III. AI-Assisted, Human-Confirmed | ✅ | 无 AI 自动修改，所有操作需用户确认 |
| IV. Data Isolation & Traceability | ✅ | 版本履历和需求关联实现完整追溯 |
| V. Version-Controlled Documentation | ✅ | 每个条目支持版本快照和变更历史 |

### 技术约束检查

| 约束 | 状态 | 说明 |
|------|------|------|
| Frontend: SvelteKit | ✅ | 沿用现有架构 |
| Backend: Open WebUI API | ✅ | 扩展现有 API 层 |
| Database: SQLite/PostgreSQL | ✅ | 使用 JSON 字段存储数组 |
| Styling: Tailwind CSS | ✅ | 符合设计系统 |

### 数据兼容性

| 要求 | 状态 | 说明 |
|------|------|------|
| 存量数据迁移 | ✅ | 默认填充 create_version = 1.0.0 |
| 新旧字段兼容 | ✅ | 新字段有默认值，API 支持新旧结构 |

### 性能约束

| 要求 | 状态 | 说明 |
|------|------|------|
| 表格 1000+ 行虚拟滚动 | ⚠️ | 当前数据量 < 1000，暂不实现，后续迭代 |
| 模块切换 < 500ms | ✅ | 单表查询 + JSON 解析 |

## Project Structure

### Documentation (this feature)

```text
specs/004-arch-module-version-demand/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── api-contracts.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── lib/
│   ├── components/
│   │   └── pm/
│   │       ├── architecture/
│   │       │   ├── ModuleTable.svelte      # 表格视图
│   │       │   ├── ModuleForm.svelte       # 新增/编辑弹窗
│   │       │   ├── VersionHistoryPopover.svelte  # 版本履历浮窗
│   │       │   ├── DemandRelationTag.svelte      # 需求关联标签
│   │       │   ├── MindMapView.svelte      # 思维导图视图
│   │       │   └── NodeDetailModal.svelte  # 节点详情弹窗
│   │       └── shared/
│   │           ├── DataTable.svelte        # 通用表格组件
│   │           └── ConfirmModal.svelte     # 确认弹窗
│   ├── apis/
│   │   └── pm/
│   │       └── architecture.ts             # API 层
│   ├── models/
│   │   └── pm/
│   │       └── architecture.ts             # 数据模型
│   └── stores/
│       └── pm/
│           └── architecture.ts             # 状态管理
├── routes/
│   └── pm/
│       └── architecture/
│           ├── +page.svelte                # 主页面
│           └── +page.server.ts             # 服务端加载
└── migrations/
    └── 004_arch_module_version_demand.sql  # 数据库迁移
```

**Structure Decision**: 采用 Option 2 (Web application)，前后端分离结构。PM 相关组件统一放在 `src/lib/components/pm/` 下，API 层在 `src/lib/apis/pm/`，符合项目 Constitution 的 Code Organization 要求。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 无 | - | - |

## 设计决策

### 1. 版本履历存储

**Decision**: 内嵌 JSON 数组

**Rationale**: 
- 版本履历与条目强关联，读多写少
- 单用户场景，无并发问题
- 避免 JOIN 查询，性能更优

### 2. 需求关联存储

**Decision**: 内嵌 JSON 数组

**Rationale**:
- 需求关联数量通常 < 10 条
- 无需跨表查询需求详情（仅存储引用信息）
- 简单高效

### 3. 思维导图渲染

**Decision**: AntV G6

**Rationale**:
- 开箱即用的树形布局
- 支持只读模式配置
- 与 React/Vue/Svelte 集成良好

### 4. CSV 导出

**Decision**: 前端生成

**Rationale**:
- 数据量可控（内嵌 JSON 数组）
- 无需后端 API 变更
- 使用标准 Blob API，兼容性好

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| JSON 字段查询性能 | 中 | 数据量 < 1000 条，暂无需索引；后续可添加 GIN 索引 |
| 存量数据迁移失败 | 高 | 迁移前备份；测试环境验证；分批执行 |
| 思维导图性能 | 中 | 节点数 > 100 时启用虚拟渲染；只读模式减少交互计算 |
| API 向后兼容 | 高 | 新字段有默认值；旧客户端忽略未知字段 |

## 下一步

1. 运行 `/speckit-tasks` 生成任务列表
2. 按任务列表执行实现
3. 完成后运行测试验证