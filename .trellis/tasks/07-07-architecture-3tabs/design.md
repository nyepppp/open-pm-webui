# 技术设计文档

## 架构

当前架构页面 (`architecture/+page.svelte`) 是一个单一页面，展示模块/功能树和参数表格。

需要重构为3个Tab页：

```
architecture/+page.svelte
├── Tab 1: 思维导图 (PMMindMap - 只读)
├── Tab 2: 模块/功能管理 (ModuleFeatureManager - 新增)
└── Tab 3: 参数表格 (ParameterTable - 现有)
```

## 组件设计

### 1. ArchitectureTabBar (已有)

已有组件，用于切换Tab页。需要扩展支持3个Tab。

### 2. ModuleFeatureManager (新增)

**Props:**
```typescript
interface Props {
  modules: TreeModule[];  // 来自 aggregatedTree
  projectId: string;
  onAddModule: (name: string) => void;
  onAddFeature: (moduleName: string, featureName: string) => void;
  onDeleteModule: (name: string) => void;
  onDeleteFeature: (moduleName: string, featureName: string) => void;
  onUpdateDescription: (moduleName: string, featureName: string | null, description: string) => void;
}
```

**功能：**
- 展示模块列表，每个模块可展开查看功能列表
- 每个模块/功能显示描述信息
- 支持编辑描述（inline editing）
- 支持添加/删除模块和功能

### 3. PMMindMap (已有)

已有组件，需要配置为只读模式。

## 数据流

```
architectureStore (已有)
├── parameterEntries → ModuleFeatureTree, ParameterTable
├── aggregatedTree → ModuleFeatureManager
└── mindmapNodes → PMMindMap
```

## API设计

### 添加模块
```typescript
async function handleAddModule(name: string) {
  const token = localStorage.token || '';
  const updatedNodes = await addManualModule(token, projectId, name, $mindmapNodes, $editingEntryId);
  await saveArchitectureEntry(token, projectId, $editingEntryId, updatedNodes, $archEntries[0]?.data);
  await loadData(projectId);
}
```

### 添加功能
```typescript
async function handleAddFeature(moduleName: string, featureName: string) {
  const token = localStorage.token || '';
  const updatedNodes = await addManualFeature(token, projectId, moduleName, featureName, $mindmapNodes, $editingEntryId);
  await saveArchitectureEntry(token, projectId, $editingEntryId, updatedNodes, $archEntries[0]?.data);
  await loadData(projectId);
}
```

### 更新描述
```typescript
async function handleUpdateDescription(moduleName: string, featureName: string | null, description: string) {
  // 找到对应的 entry，更新 data.description
  const entry = $archEntries.find(e => e.data?.moduleName === moduleName && e.data?.featureName === featureName);
  if (entry) {
    await updateEntry(token, entry.id, {
      data: { ...entry.data, description }
    });
    await loadData(projectId);
  }
}
```

## 状态管理

使用现有的 `architectureStore`，不需要新增store。

## 响应式设计

- 移动端：Tab页横向滚动或垂直堆叠
- 桌面端：水平Tab导航

## 兼容性

- 保持现有参数表格功能不变
- 版本选择器在所有Tab页都可见
