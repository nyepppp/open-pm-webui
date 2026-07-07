# 产品架构页面重构 - 技术设计

## Architecture

### 组件结构

```
ArchitecturePage (+page.svelte)
├── ArchitectureHeader
│   ├── Title: 产品架构
│   ├── VersionSelector (复用现有)
│   └── TabBar: 思维导图 | 表格
├── MindMapView (新组件)
│   └── ECharts Tree (只读)
└── ArchitectureTable (新组件)
    ├── ModuleRow (可展开)
    │   ├── FeatureRow (可展开)
    │   │   └── ParameterRow
    │   └── FeatureRow...
    └── ModuleRow...
```

### 数据流

```
architectureStore (现有)
  ├── aggregatedTree: Module[] → 驱动表格和思维导图
  ├── mindmapNodes: MindMapNode[] → 废弃，改用 aggregatedTree 生成
  └── parameterEntries: Parameter[] → 用于参数详情

表格编辑 → 更新 API → 刷新 Store → 自动同步思维导图
```

## Data Model

### Module (模块)
```typescript
interface Module {
  id: string;
  name: string;
  description?: string;
  features: Feature[];
  versionId?: string;
  order: number;
}
```

### Feature (功能)
```typescript
interface Feature {
  id: string;
  moduleId: string;
  name: string;
  description?: string;
  parameters: Parameter[];
  versionId?: string;
  order: number;
}
```

### Parameter (参数)
```typescript
interface Parameter {
  id: string;
  featureId: string;
  name: string;
  key: string;
  type: 'input' | 'output' | 'config';
  dataType: 'string' | 'number' | 'boolean' | 'object' | 'array';
  defaultValue?: string;
  required: boolean;
  description?: string;
  versionId?: string;
  sourceDocument?: string;
  relatedRequirements?: string[];
  order: number;
}
```

## Key Decisions

### 1. ECharts vs 其他方案
- **选择 ECharts Tree**：轻量、性能好、中文文档完善
- **替代方案**：D3.js（太重）、自研 SVG（工作量大）

### 2. 表格实现
- **选择原生 HTML Table + Svelte**：灵活可控
- **不选择第三方表格库**：避免引入额外依赖，保持轻量
- **树形展开**：使用 CSS 缩进 + 展开/收起按钮

### 3. 数据同步
- 表格编辑后调用 API 保存
- 保存成功后刷新 Store
- Store 更新后自动重新生成思维导图数据
- 使用 Svelte 5 `$effect` 实现自动同步

## API 契约

### 现有 API（复用）
- `getEntries(token, projectId, 'parameter')` - 获取参数列表
- `createEntry(token, projectId, data)` - 创建条目
- `updateEntry(token, entryId, data)` - 更新条目
- `deleteEntry(token, entryId)` - 删除条目

### 新增 API（如需）
- `getArchitectureData(token, projectId)` - 获取结构化架构数据
- `saveArchitectureData(token, projectId, data)` - 保存架构数据

## Compatibility

- 保持现有路由 `/pm/[projectId]/architecture`
- 保持版本选择器功能
- 保持 AI 助手按钮
- 向后兼容现有参数条目数据格式

## Rollback

- 保留旧版 `+page.svelte` 作为备份
- 新组件开发完成后替换
- 如遇问题可快速回滚
