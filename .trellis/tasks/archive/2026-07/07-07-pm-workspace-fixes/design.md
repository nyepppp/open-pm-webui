# PM工作台交互与UI修复 - 技术设计

## Architecture

### 组件关系图

```
+page.svelte (architecture)
├── ArchitectureTabBar
├── MindMapCanvas (tab: mindmap)
├── ModuleFeatureTree (tab: modules/params)
└── ModuleFeatureManager (tab: modules)
    ├── ModuleCard[]
    │   └── Feature list
    │       └── "+ 添加功能" button
    └── AddFeatureModal (NEW)
        └── ParameterForm[]
```

### 数据流

```
architectureStore (Svelte store)
    ├── aggregatedTree$ → ModuleFeatureTree, ModuleFeatureManager
    ├── mindmapNodes$ → MindMapCanvas
    └── parameterEntries$ → ParameterTable
```

## Technical Decisions

### TD1: 导航修复 (Issue 1)

**问题**: `goto` 导航可能因 SvelteKit 的 SPA 导航机制失效

**方案**:
- 检查 `goto` 导入是否正确：`import { goto } from '$app/navigation'`
- 添加 `event.preventDefault()` 防止默认行为
- 备选：使用 `window.location.href = mod.href` 作为 fallback

### TD2: 性能优化 (Issue 2)

**问题**: 50-100 模块下页面卡顿

**根因分析**:
1. **MindMapCanvas 重渲染**: `{#key $aggregatedTree}` 导致每次数据变化都重新创建 Canvas
2. **Resize 事件**: 无防抖，频繁触发重计算
3. **大量 DOM 节点**: 100 模块 × 平均 5 功能 = 500+ DOM 节点
4. **固定高度**: `h-[calc(100vh-200px)]` 导致滚动容器嵌套

**优化策略**:

| 优化点 | 方案 | 预期效果 |
|--------|------|----------|
| MindMapCanvas | 移除 `{#key}`，使用 `$effect` 监听数据变化并增量更新 | 减少 80% 重渲染 |
| Resize | 添加 200ms 防抖 | 减少 90% 重计算 |
| DOM 节点 | 虚拟滚动（Virtual Scroll） | 只渲染视口内节点 |
| 固定高度 | 使用 `flex-1` 替代固定计算 | 减少布局重算 |

**虚拟滚动实现**:
- 使用 `svelte-virtual` 或自定义实现
- 每个模块卡片高度固定（约 200px）
- 视口内渲染：可视区域 / 200px + 缓冲区（上下各 3 个）

### TD3: 卡片信息补充 (Issue 3)

**信息来源**:
- **版本归属**: `module.versionId` → 查询 `versionStore` 获取版本号
- **更新时间**: `module.updatedAt` (来自 `TreeModule`)
- **溯源入口**: 显示关联数量，点击跳转溯源页面

**卡片布局**:

```
┌─────────────────────────────────────┐
│ [来源标签] 模块名称                    │
│ 版本: v1.2.3  |  更新时间: 2小时前    │
│ 描述文本...                          │
│ [溯源: 3条关联]                      │
└─────────────────────────────────────┘
```

### TD4: 添加功能弹窗 (Issue 4)

**弹窗组件**: 复用项目已有的 `Modal.svelte`（`src/lib/components/common/Modal.svelte`）
- 使用 `size='md'`（宽度 42rem）
- 遵循项目 Modal 的 focus trap 和 ESC 关闭规范

**弹窗内容**:
```
┌─────────────────────────────────────┐
│ 添加功能 - [模块名]                   │
├─────────────────────────────────────┤
│ 功能名称: [________________]        │
│                                     │
│ 参数列表:                            │
│ ┌─────────────────────────────────┐ │
│ │ 参数名  类型   描述    [删除]    │ │
│ │ [____] [strin] [____] [X]       │ │
│ └─────────────────────────────────┘ │
│ [+ 添加参数]                        │
│                                     │
│ [取消]        [确认添加]            │
└─────────────────────────────────────┘
```

**参数字段**:
- 参数名 (key): string, required
- 类型 (type): select [string, number, boolean, object, array], optional, default: string
- 描述 (description): string, optional
- 默认值 (defaultValue): string, optional
- 是否必填 (required): 0 | 1, optional, default: 0

## Data Contracts

### TreeModule (现有)
```typescript
interface TreeModule {
  name: string;
  source: 'auto' | 'manual';
  features: TreeFeature[];
  versionId?: string;        // NEW: 版本归属
  updatedAt?: number;        // NEW: 更新时间
  createdAt?: number;        // NEW: 创建时间
}

interface TreeFeature {
  name: string;
  source: 'auto' | 'manual';
  paramCount: number;
  parameters?: Parameter[];   // NEW: 参数列表
}
```

### AddFeaturePayload (NEW)
```typescript
interface AddFeaturePayload {
  moduleName: string;
  featureName: string;
  parameters: Parameter[];
}
```

### 版本信息来源
- **来源**: `selectedVersion` from architecture page (`+page.svelte`)
- **类型**: `{ id: string; versionNumber: string; label?: string } | null`
- **传递**: 通过 props 从 `+page.svelte` → `ModuleFeatureManager` → `ModuleCard`
- **显示**: 当前选中的版本号，如 `v1.2.3`

## Compatibility

- **Svelte 5 Runes**: 使用 `$state`, `$derived`, `$effect` 等新特性
- **Tailwind CSS**: 保持现有样式类命名规范
- **Modal 组件**: 复用 `src/lib/components/common/Modal.svelte`

## Rollback Plan

1. 所有修改在独立分支进行
2. 关键优化（如虚拟滚动）添加 feature flag，可快速关闭
3. 保留原 `ModuleCard.svelte` 作为备份

## Risk Assessment

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 虚拟滚动引入 bug | 中 | 中 | 添加 fallback 到普通滚动 |
| 弹窗与现有 Modal 冲突 | 低 | 中 | 使用项目统一 Modal 组件 |
| 性能优化不达预期 | 中 | 高 | 分阶段优化，先易后难 |
