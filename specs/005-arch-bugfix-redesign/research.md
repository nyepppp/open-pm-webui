# Research: 产品架构页面缺陷修复与交互重构

**Date**: 2026-07-10
**Feature**: specs/005-arch-bugfix-redesign

## Research Findings

### 1. 双 API 层与双 Store 冲突（核心根因）

**发现**: 项目中存在两套完全独立的 API 和数据存储层：

| 层级 | 旧系统 (ModuleTable 使用) | 新系统 (+page.svelte 使用) |
|------|--------------------------|---------------------------|
| API | `src/lib/apis/pm/architecture.ts` — RESTful 专用端点 (`/api/pm/modules`, `/api/pm/functions`, `/api/pm/parameters`) | `src/lib/apis/pm/index.ts` — 通用 Entry 端点 (`/api/pm/projects/{id}/entries`) |
| Store | `src/lib/stores/pm/architecture.ts` — `architectureStore` (Svelte writable) | `src/lib/stores/pm/architectureStore.ts` — `architectureHierarchy` (derived) |
| 模型 | `src/lib/models/pm/architecture.ts` — Module/Function/Parameter | `src/lib/apis/pm/types.ts` — ModuleEntry |

**核心问题**: `ArchitectureTable.svelte` 虽然接收 `+page.svelte` 传入的 `modules` props，但内部直接订阅了旧 store (`$activeModules`, `$activeFunctions`, `$activeParameters`)，完全忽略了父组件传入的数据。这导致：
- `+page.svelte` 通过 `architectureStore` (新系统) 加载数据并传给 `ArchitectureTable`
- `ArchitectureTable` 忽略传入数据，使用旧 `architectureStore` 的数据
- 两套 store 互不通信，操作在旧 store 上执行，新 store 不感知变更

**决策**: 统一使用旧系统 (`architecture.ts` API + `architecture.ts` store)，因为：
1. 旧系统 API 有专用端点，功能更完整（CRUD、soft delete、copy、version export）
2. 旧系统 store 有完整的操作方法（createModule, updateModule, softDelete 等）
3. 旧系统模型更精确（Module/Function/Parameter 独立类型）
4. 新系统只是将通用 Entry 包装为 ArchModule，丢失了原始数据粒度

**替代方案**: 使用新系统 — 被否决，因为新系统 `architectureStore.ts` 的 `convertToArchModules` 生成合成 ID（如 `mod-0`, `feat-0-1`），无法用于 API 调用。

**影响**: 需要删除 `architectureStore.ts` 中与架构相关的代码，将 `+page.svelte` 改为直接使用旧 `architectureStore`。

### 2. 操作按钮失效根因

**发现**: `ArchitectureTable.svelte` 的操作流程：
- 编辑/新增按钮 → 设置状态变量 (`editModalOpen`, `editEntityType` 等) → 打开 `ModuleForm` 弹窗
- `ModuleForm` 提交 → dispatch `submit` 事件 → `handleEditSubmit` / `handleAddChildSubmit` 调用旧 `architectureStore` 方法
- 旧 `architectureStore` 调用 `architecture.ts` API

**问题**: 
1. `ArchitectureTable.svelte` 同时接收 props (`modules`, `onEdit`, `onDelete`, `onAdd`) 并使用旧 store — 双数据源导致操作后 props 和 store 不同步
2. `+page.svelte` 的 `handleTableEdit` 函数使用 `updateEntry` (新系统 API)，但 `ArchitectureTable` 调用的是旧 store 的 `updateModule` (旧系统 API) — 两个 API 端点不同，可能一个有效一个无效
3. `handleEditSubmit` 中调用 `architectureStore.updateModule(editEntity.id!, data, changeDetail)` — 如果旧 API 端点不存在或返回错误，操作就会失败

**决策**: `ArchitectureTable` 应完全通过旧 store 操作数据，不再使用 props 回调。`+page.svelte` 不再传入 `onEdit`/`onDelete`/`onAdd` 回调。

### 3. 思维导图根节点修复

**发现**: `MindMapView.svelte` 中根节点硬编码为：
```typescript
nodes.push({
  id: 'root',
  data: { name: '产品架构', type: 'root' },
  style: { fill: '#E8F5E8', stroke: '#52C41A' }
});
```

**修复方案**: 
- 添加 `projectName` prop，默认值为项目名称
- `+page.svelte` 通过 `getProject` API 获取项目名称后传入
- 降级方案：从路由参数 `projectId` 无法直接获取名称，需异步调用

**决策**: 添加 `projectName` prop 到 `MindMapView`，在 `+page.svelte` 中通过 `getProject` API 获取后传入。

### 4. 创建版本列不显示

**发现**: `ArchitectureTable.svelte` 中"创建版本"列的显示逻辑：
```html
<td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
  {module.createVersion || module.versionId || '-'}
</td>
```

旧 store 的 `Module` 类型定义（在 `src/lib/models/pm/architecture.ts`）包含 `create_version` 字段（snake_case），而模板使用 `createVersion`（camelCase）。这可能是字段名不匹配导致显示为空。

**决策**: 修复字段名映射，确保 store 数据与模板使用一致的字段名。

### 5. 版本选择器和 AI 按钮移除影响

**发现**: `+page.svelte` 中 `showVersionSelector` 和 `selectedVersion` 仅用于：
- 控制版本选择器弹窗显示
- 页面标题旁显示当前版本标签

移除后不会影响其他功能，但 `PMVersionSelector` 组件仍可保留在代码库中供后续使用。

**决策**: 仅移除 `+page.svelte` 中的按钮和版本选择器弹窗，不删除 `PMVersionSelector` 组件文件。

### 6. 需删除的组件

以下组件仅被 `ModuleTable.svelte` 或旧 store 的衍生功能使用，随 ModuleTable 删除后无引用：

| 文件 | 原因 |
|------|------|
| `ModuleTable.svelte` | FR-010 指定删除 |
| `ModuleCard.svelte` | 仅 ModuleTable 引用 |
| `ModuleFeatureManager.svelte` | 仅 ModuleTable 引用 |
| `ModuleFeatureTree.svelte` | 仅 ModuleFeatureManager 引用 |
| `ArchitectureTabBar.svelte` | 评估后决定是否保留 |

需要进一步检查这些组件的引用关系。
