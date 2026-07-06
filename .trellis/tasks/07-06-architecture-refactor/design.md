# 技术设计 - 产品架构模块-功能-参数层级重构

## Architecture

### 组件结构

```
architecture/+page.svelte (重构后)
├── ArchitectureHeader (新增)
│   ├── VersionSelector (复用 PMVersionSelector)
│   └── Breadcrumb (新增)
├── ModuleFeatureTree (增强)
│   ├── ModuleNode (新增)
│   │   ├── FeatureNode (新增)
│   │   └── AddFeatureButton (新增)
│   └── AddModuleButton (新增)
└── ParameterPanel (新增)
    ├── ParameterToolbar (新增)
    │   ├── SearchFilter (新增)
    │   └── BulkActions (新增)
    ├── ParameterTable (增强)
    │   ├── ParameterRow (新增)
    │   └── RequirementTrace (新增)
    └── ParameterForm (新增/增强)
        ├── BasicFields (新增)
        └── RequirementSelector (新增)
```

### 数据流

```
+page.svelte
├── architectureStore (增强)
│   ├── parameterEntries: ModuleEntry[]
│   ├── archEntries: ModuleEntry[]
│   ├── aggregatedTree: TreeModule[]
│   ├── mindmapNodes: MindMapNode[]
│   └── selectedVersion: Version | null
├── versionStore (复用)
│   └── versions: Version[]
└── relationStore (新增)
    └── parameterRequirements: Map<paramId, requirementId[]>
```

## Key Decisions

### 1. 页面布局

**决策：采用三栏布局**
- 左栏：模块-功能导航树（固定宽度 280px）
- 中栏：参数列表（自适应宽度）
- 右栏：参数详情/编辑（可选，抽屉式）

**理由：**
- 符合用户"从左到右"的操作习惯
- 导航树固定宽度保证稳定性
- 参数列表为主要操作区域，需要足够空间

### 2. 版本切换

**决策：版本切换时重新加载数据**
- 选择版本后，重新调用 API 获取该版本的架构数据
- 版本信息存储在 URL query 参数中（`?version=v1.2.0`）

**理由：**
- 保证数据一致性
- 支持通过 URL 直接访问特定版本
- 便于分享和书签

### 3. 需求文档溯源

**决策：通过 relation API 建立参数与需求文档的关联**
- 使用现有的 `relation` 模块建立 `parameter` 和 `requirement`/`prd` 之间的关联
- 关联关系存储在 `relations` 表中
- 前端通过 `getRelationList` 获取关联信息

**理由：**
- 复用现有的溯源基础设施
- 支持双向查询（从参数查需求，从需求查参数）
- 与 traceability 页面保持一致

### 4. 状态管理

**决策：使用 Svelte 5 runes 管理状态**
- 继续使用 `$state`, `$derived`, `$effect` 管理组件状态
- 全局状态使用 Svelte stores
- 局部状态使用组件内 runes

## Data Contracts

### API 接口

```typescript
// 获取参数列表（支持版本过滤）
GET /api/projects/:projectId/entries?moduleType=parameter&versionId=:versionId

// 获取模块-功能树
GET /api/projects/:projectId/entries?moduleType=product-architecture&versionId=:versionId

// 获取参数的关联需求文档
GET /api/projects/:projectId/relations?sourceType=parameter&targetType=requirement&sourceId=:paramId

// 创建参数-需求文档关联
POST /api/projects/:projectId/relations
Body: {
  sourceType: 'parameter',
  sourceId: string,
  targetType: 'requirement',
  targetId: string,
  relationType: 'derives'
}

// 删除参数-需求文档关联
DELETE /api/projects/:projectId/relations/:relationId
```

### 组件 Props

```typescript
// ModuleFeatureTree Props
interface ModuleFeatureTreeProps {
  modules: TreeModule[];
  selectedModule: string | null;
  selectedFeature: string | null;
  onSelect: (module: string, feature?: string) => void;
  onAddModule: (name: string) => void;
  onAddFeature: (moduleName: string, featureName: string) => void;
  onDeleteModule: (name: string) => void;
  onDeleteFeature: (moduleName: string, featureName: string) => void;
  versionInfo?: VersionInfo; // 新增
}

// ParameterTable Props
interface ParameterTableProps {
  entries: ModuleEntry[];
  projectId: string;
  filterModule?: string | null;
  filterFeature?: string | null;
  onDataChange?: () => void;
  versionId?: string | null; // 新增
}

// ParameterRow Props
interface ParameterRowProps {
  entry: ModuleEntry;
  requirements: Requirement[]; // 关联的需求文档
  onEdit: (entry: ModuleEntry) => void;
  onDelete: (entryId: string) => void;
  onLinkRequirement: (paramId: string, requirementIds: string[]) => void;
}

// RequirementSelector Props
interface RequirementSelectorProps {
  projectId: string;
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  multiSelect?: boolean;
}
```

## Compatibility

### 向后兼容
- 现有的参数配置模块保持可用
- 数据模型不变，仅前端展示方式调整
- API 接口保持兼容

### 数据迁移
- 无需数据迁移
- 新增的关联关系通过现有 relation API 存储

## Rollback Plan

1. 回滚 `architecture/+page.svelte` 到原始版本
2. 回滚 `ParameterTable.svelte` 到原始版本
3. 回滚 `ModuleFeatureTree.svelte` 到原始版本
4. 删除新增的组件文件

## Performance Considerations

- 模块-功能树数据量通常不大（< 100 个节点），可直接渲染
- 参数列表可能较大，需要虚拟滚动（如果 > 1000 条）
- 需求文档选择器需要支持搜索和分页
- 版本切换时需要显示加载状态
