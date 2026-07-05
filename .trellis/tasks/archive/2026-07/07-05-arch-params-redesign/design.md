# Design: 产品架构图重设计 & 参数配置重构

## Architecture Overview

### 新页面结构

```
/pm/[projectId]/architecture
├── Tab Bar: [架构图] [参数详情]
├── 架构图 Tab
│   └── PMMindMap (重用现有组件，增强节点语义)
└── 参数详情 Tab
    ├── 左侧面板: ModuleFeatureTree (新组件)
    └── 右侧面板: ParameterTable (重构现有 table 逻辑)
```

### 路由变更

| 变更 | 前 | 后 |
|------|-----|-----|
| 路由 | `/pm/[projectId]/product-architecture` 和 `/pm/[projectId]/parameter` | `/pm/[projectId]/architecture` |
| moduleType | 两个独立值 | 前端页面内聚合，后端 API 仍用原 moduleType |
| 侧边栏 | 两个入口（planning + review） | 一个入口（design 分类） |

### 数据流

```
参数条目 (parameter API)
  │
  ├─→ 自动聚合: moduleName/featureName → 模块/功能节点
  │
  ├─→ 参数详情 Tab: 左侧树 + 右侧参数表
  │
架构图条目 (product-architecture API)
  │
  ├─→ 手动补充的模块/功能节点
  │
  └─→ 架构图 Tab: 合并展示自动聚合 + 手动补充节点
```

## Component Design

### 1. ArchitecturePage (新 Svelte 组件)

位置: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`

职责:
- 管理 Tab 切换状态
- 加载 parameter 和 product-architecture 两套数据
- 提供跨 Tab 导航方法（架构图→参数详情的模块/功能定位）
- 传递共享的模块/功能聚合数据给两个 Tab

关键状态:
```typescript
let activeTab = $state<'mindmap' | 'params'>('mindmap');
let navigateToModule = $state<string | null>(null);  // 跨 Tab 导航目标
let navigateToFeature = $state<string | null>(null);
```

### 2. PMMindMap (增强现有组件)

变更点:
- 节点类型语义映射: root→产品, branch→模块, leaf→功能
- 新增节点数据来源标识: `metadata.source = 'auto' | 'manual'`
- auto 节点不可手动删除，manual 节点可删除
- manual 节点视觉上显示"规划中"标记（虚线边框或 badge）
- 节点点击时调用父组件的跨 Tab 导航方法

### 3. ModuleFeatureTree (新组件)

位置: `src/lib/components/pm/ModuleFeatureTree.svelte`

职责:
- 从参数条目 + 手动补充节点聚合出模块→功能树
- 渲染树形导航，支持选中/展开/折叠
- 支持新增模块/功能节点（添加到 product-architecture API）
- 支持重命名/删除手动补充的节点
- 选中功能节点后触发右侧参数表过滤

数据结构:
```typescript
interface TreeModule {
  name: string;
  source: 'auto' | 'manual';
  features: TreeFeature[];
}

interface TreeFeature {
  name: string;
  source: 'auto' | 'manual';
  paramCount: number;
}
```

### 4. ParameterTable (从现有页面提取重构)

位置: `src/lib/components/pm/ParameterTable.svelte`

职责:
- 接收过滤条件（moduleName, featureName）
- 渲染当前选中功能下的参数列表
- 保留现有参数 CRUD、行内编辑、flowchart 关联等功能
- 新增参数时自动填充当前选中的 moduleName/featureName

## Data Aggregation Logic

核心聚合函数，同时用于架构图和参数详情左侧树：

```typescript
function aggregateModuleFeatureTree(
  parameterEntries: ModuleEntry[],
  architectureEntries: ModuleEntry[]
): TreeModule[] {
  // 1. 从 parameter 条目提取 moduleName→featureName 映射
  const autoModules = new Map<string, Set<string>>();
  for (const entry of parameterEntries) {
    const d = entry.data || {};
    const mod = d.moduleName as string;
    const feat = d.featureName as string;
    if (mod) {
      if (!autoModules.has(mod)) autoModules.set(mod, new Set());
      if (feat) autoModules.get(mod)!.add(feat);
    }
  }

  // 2. 从 product-architecture 条目提取手动补充的模块/功能
  const manualModules = new Map<string, Set<string>>();
  for (const entry of architectureEntries) {
    const d = entry.data || {};
    const nodes = d.nodes as MindMapNode[] | undefined;
    if (nodes) {
      for (const node of nodes) {
        if (node.type === 'branch' && node.metadata?.source === 'manual') {
          if (!manualModules.has(node.label)) manualModules.set(node.label, new Set());
        }
        if (node.type === 'leaf' && node.metadata?.source === 'manual') {
          const parent = nodes.find(n => n.id === node.parentId);
          if (parent) {
            if (!manualModules.has(parent.label)) manualModules.set(parent.label, new Set());
            manualModules.get(parent.label)!.add(node.label);
          }
        }
      }
    }
  }

  // 3. 合并：auto 为主，manual 补充不存在的
  const allModules = new Map(autoModules);
  for (const [mod, feats] of manualModules) {
    if (!allModules.has(mod)) allModules.set(mod, new Set());
    for (const f of feats) allModules.get(mod)!.add(f);
  }

  // 4. 转为 TreeModule[]
  return [...allModules.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, features]) => ({
      name,
      source: autoModules.has(name) ? 'auto' : 'manual',
      features: [...features].sort().map(f => ({
        name: f,
        source: (autoModules.get(name)?.has(f) ? 'auto' : 'manual'),
        paramCount: parameterEntries.filter(e =>
          (e.data?.moduleName === name) && (e.data?.featureName === f)
        ).length
      }))
    }));
}
```

## Cross-Tab Navigation

架构图节点点击 → 参数详情 Tab 的流程：

1. 用户点击架构图的模块/功能节点
2. `PMMindMap` 触发 `onnavigate` 事件，payload: `{ moduleName, featureName }`
3. `ArchitecturePage` 接收事件，设置 `navigateToModule`/`navigateToFeature`，切换 `activeTab = 'params'`
4. `ModuleFeatureTree` 检测到 `navigateToModule` 变化，自动选中对应节点并展开
5. `ParameterTable` 根据选中的功能过滤参数列表

## Sidebar Navigation Changes

`src/lib/stores/pm/moduleStore.ts`:

```diff
  // planning 分类
  modules: [
    { id: 'prd', ... },
    { id: 'requirement', ... },
-   { id: 'parameter', label: '参数', icon: 'Settings', category: 'planning', path: '/pm/parameter' },
    { id: 'requirement-boundary', ... },
    { id: 'flowchart', ... },
  ]
  // design 分类
  modules: [
    { id: 'testcase', ... },
    { id: 'risk', ... },
    { id: 'competitor', ... },
+   { id: 'architecture', label: '产品架构', icon: 'Layers', category: 'design', path: '/pm/architecture' },
    { id: 'prototype', ... },
  ]
  // review 分类
  modules: [
    { id: 'acceptance', ... },
    { id: 'faq', ... },
-   { id: 'product-architecture', label: '产品架构', icon: 'Layers', category: 'review', path: '/pm/product-architecture' },
    { id: 'spec', ... },
  ]
```

`src/lib/components/pm/moduleFields.ts`:

- 新增 `architecture` 的 `moduleEditorConfig` 条目，editorType 为 `'mixed'`（因为包含 mindmap + table）
- 保留 `parameter` 和 `product-architecture` 的 field config 供内部使用

## Backward Compatibility

- 旧路由 `/pm/[projectId]/product-architecture` 和 `/pm/[projectId]/parameter` 通过 SvelteKit redirect 指向新路由
- `ModuleType` 类型保留 `'parameter'` 和 `'product-architecture'`，新增 `'architecture'`
- 旧数据通过相同的 API 正常加载，无需迁移
- 现有 `+page.svelte` 中 `moduleConfig` 的 `parameter` 和 `product-architecture` 条目保留（兼容直接 URL 访问）

## Key Trade-offs

| 决策 | 取舍 |
|------|------|
| 前端合并、后端不变 | 短期低风险，但长期两套数据源的复杂度仍在 |
| 自动聚合 + 手动补充 | 灵活性好，但需要清晰的 UI 区分 auto/manual 节点 |
| 左侧树 + 右侧列表 | 大屏体验好，但移动端需要折叠处理 |
