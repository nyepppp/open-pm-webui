# 流程图溯源功能 - 技术设计文档

## 1. 架构概述

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Svelte 5)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Flowchart   │  │ Mind Map    │  │ Traceability        │ │
│  │ Editor      │  │ View        │  │ Sidebar             │ │
│  │             │  │             │  │                     │ │
│  │ ┌─────────┐│  │ ┌─────────┐│  │ ┌─────────────────┐ │ │
│  │ │ XYFlow  ││  │ │ XYFlow  ││  │ │ Node Detail     │ │ │
│  │ │ Nodes   ││  │ │ Tree    ││  │ │ Entity Binding  │ │ │
│  │ │ Edges   ││  │ │ Layout  ││  │ │ Version History │ │ │
│  │ └─────────┘│  │ └─────────┘│  │ └─────────────────┘ │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────┬───────────┘ │
│         │                │                   │             │
│         └────────────────┴───────────────────┘              │
│                        │                                   │
│              ┌─────────┴─────────┐                         │
│              │   FlowchartStore  │                         │
│              │   (Svelte Store)   │                         │
│              └─────────┬─────────┘                         │
└──────────────────────┼───────────────────────────────────────┘
                       │
                       │ API Calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Flowchart   │  │ Module      │  │ Version             │ │
│  │ API         │  │ Entry API   │  │ API                 │ │
│  │             │  │             │  │                     │ │
│  │ CRUD ops    │  │ getEntries  │  │ getVersions         │ │
│  │ with trace  │  │ query       │  │ getVersionHistory   │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────┬───────────┘ │
│         │                │                   │             │
│         └────────────────┴───────────────────┘              │
│                        │                                   │
│              ┌─────────┴─────────┐                         │
│              │   Database Layer   │                         │
│              │   (SQLite/PostgreSQL)                        │
│              └────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 2. 数据模型设计

### 2.1 扩展 FlowchartNode 数据模型

```typescript
// src/lib/apis/pm/types.ts

export interface FlowchartNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    description?: string;
    style?: Partial<NodeStyle>;
    inputParams?: string[];
    outputParams?: string[];
    // NEW: 溯源绑定信息
    traceability?: NodeTraceability;
  };
}

export interface NodeTraceability {
  entityType: 'prd' | 'module' | 'feature' | 'parameter' | 'none';
  entityId: string;
  entityName: string;
  versionId?: string;
  versionNumber?: string;
  boundAt: number;
  boundBy?: string;
}
```

### 2.2 数据库 Schema 扩展

```sql
-- 流程图节点溯源表
CREATE TABLE flowchart_node_traceability (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    flowchart_id TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('prd', 'module', 'feature', 'parameter', 'none')),
    entity_id TEXT NOT NULL,
    entity_name TEXT,
    version_id TEXT,
    version_number TEXT,
    bound_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    bound_by TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (flowchart_id) REFERENCES flowcharts(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_traceability_flowchart ON flowchart_node_traceability(flowchart_id);
CREATE INDEX idx_traceability_node ON flowchart_node_traceability(node_id);
CREATE INDEX idx_traceability_entity ON flowchart_node_traceability(entity_type, entity_id);
```

## 3. API 设计

### 3.1 新增 API 端点

```typescript
// 绑定节点到实体
POST /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/{nodeId}/bind
Request: {
  entityType: 'prd' | 'module' | 'feature' | 'parameter',
  entityId: string,
  versionId?: string
}
Response: { success: boolean, data: NodeTraceability }

// 解绑节点
DELETE /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/{nodeId}/bind
Response: { success: boolean }

// 获取节点的溯源信息
GET /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/{nodeId}/traceability
Response: { success: boolean, data: NodeTraceability }

// 批量绑定节点
POST /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/batch-bind
Request: {
  nodeIds: string[],
  entityType: 'prd' | 'module' | 'feature' | 'parameter',
  entityId: string
}
Response: { success: boolean, data: NodeTraceability[] }

// 导出流程图为表格
GET /api/pm/projects/{projectId}/flowcharts/{flowchartId}/export
Query: { format: 'csv' | 'xlsx' }
Response: Blob (file download)
```

## 4. 组件设计

### 4.1 组件架构

```
PMFlowchartEditor.svelte (主编辑器)
├── SvelteFlow (画布)
│   ├── DynamicNode.svelte (节点 - 扩展溯源显示)
│   └── CustomEdge.svelte (连线)
├── NodeConfigPanel.svelte (节点配置 - 扩展溯源绑定)
│   └── EntityBindingPanel.svelte (实体绑定面板 - NEW)
├── TraceabilitySidebar.svelte (溯源侧边栏 - NEW)
│   ├── NodeDetailView.svelte
│   ├── EntityBindingView.svelte
│   └── VersionHistoryView.svelte
└── FlowchartToolbar.svelte (工具栏 - 扩展视图切换)
    └── ViewToggle.svelte (流程图/思维导图切换 - NEW)

PMMindMap.svelte (思维导图视图 - 复用现有)
└── (使用现有组件，扩展节点点击事件)

TraceabilityExport.svelte (导出组件 - NEW)
```

### 4.2 关键组件接口

```typescript
// EntityBindingPanel.svelte
interface EntityBindingPanelProps {
  nodeId: string;
  projectId: string;
  currentBinding?: NodeTraceability;
  onBind: (binding: NodeTraceability) => void;
  onUnbind: () => void;
}

// TraceabilitySidebar.svelte
interface TraceabilitySidebarProps {
  nodeId: string;
  projectId: string;
  nodeData: FlowchartNode['data'];
  onClose: () => void;
}

// ViewToggle.svelte
interface ViewToggleProps {
  currentView: 'flowchart' | 'mindmap';
  onToggle: (view: 'flowchart' | 'mindmap') => void;
}
```

## 5. 状态管理

### 5.1 FlowchartStore 扩展

```typescript
// src/lib/stores/pm/flowchartStore.ts

interface FlowchartState {
  // 现有字段
  nodes: FlowchartNode[];
  edges: FlowchartEdge[];
  viewport: { x: number; y: number; zoom: number };
  
  // 新增字段
  traceability: Map<string, NodeTraceability>; // nodeId -> traceability
  selectedNodeId: string | null;
  viewMode: 'flowchart' | 'mindmap';
}

interface FlowchartActions {
  // 现有方法
  addNode: (node: FlowchartNode) => void;
  updateNode: (id: string, updates: Partial<FlowchartNode>) => void;
  deleteNode: (id: string) => void;
  
  // 新增方法
  bindNode: (nodeId: string, binding: NodeTraceability) => void;
  unbindNode: (nodeId: string) => void;
  batchBindNodes: (nodeIds: string[], binding: NodeTraceability) => void;
  setViewMode: (mode: 'flowchart' | 'mindmap') => void;
}
```

## 6. 外部组件选型

### 6.1 思维导图渲染

| 组件 | 版本 | 用途 | 选择理由 |
|------|------|------|---------|
| @xyflow/svelte | ^0.1.0 | 流程图/思维导图渲染 | 项目已使用，API 熟悉 |
| d3-hierarchy | ^3.1.0 | 树形布局计算 | 轻量，用于思维导图自动布局 |

### 6.2 表格导出

| 库 | 版本 | 用途 | 选择理由 |
|---|------|------|---------|
| xlsx | ^0.18.0 | Excel 导出 | 纯前端，无需后端参与 |

## 7. 交互设计

### 7.1 节点绑定流程

```
用户操作: 右键点击节点
    │
    ▼
┌─────────────────┐
│ 上下文菜单      │
│ ├─ 编辑节点     │
│ ├─ 绑定实体     │  ← 用户选择
│ ├─ 解绑实体     │
│ └─ 删除节点     │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 实体选择对话框   │
│ ├─ 类型下拉:    │
│ │   [PRD ▼]    │
│ ├─ 实体列表:    │
│ │   □ PRD-001   │
│ │   □ PRD-002   │
│ │   □ PRD-003   │
│ └─ 版本选择:    │
│     [v1.0 ▼]   │
└─────────────────┘
    │
    ▼
确认绑定 → 节点显示绑定图标
```

### 7.2 思维导图切换

```
用户操作: 点击工具栏切换按钮
    │
    ▼
┌─────────────────┐
│   流程图视图    │  ← 当前
│   思维导图视图  │
└─────────────────┘
    │
    ▼
自动转换节点布局:
  - 根节点居中
  - 子节点按层级展开
  - 绑定实体的节点显示图标
    │
    ▼
渲染思维导图 (使用 d3-hierarchy 计算布局)
```

## 8. 性能优化

### 8.1 渲染优化
- 使用 `Svelte 5` 的 `$derived` 和 `$effect` 进行精细化响应式更新
- 思维导图节点超过 100 个时启用虚拟化
- 节点绑定信息懒加载，仅在 hover 或 click 时查询

### 8.2 数据优化
- 溯源信息缓存到 `FlowchartStore`，避免重复 API 调用
- 批量绑定使用批量 API，减少请求次数
- 导出时流式生成表格，避免内存溢出

## 9. 错误处理

### 9.1 边界情况
- **实体被删除**: 节点显示"实体已删除"警告，保留绑定记录
- **版本不存在**: 自动切换到最新版本，提示用户
- **循环绑定**: 后端校验，返回错误信息
- **权限不足**: 禁用绑定操作，显示只读提示

### 9.2 降级策略
- API 不可用: 使用本地缓存数据，禁用绑定功能
- 导出失败: 提供 CSV 格式备选方案

## 10. 测试策略

### 10.1 单元测试
- FlowchartStore 状态管理测试
- 节点绑定/解绑逻辑测试
- 思维导图布局算法测试

### 10.2 集成测试
- 端到端绑定流程测试
- 导出功能测试
- 视图切换测试

### 10.3 性能测试
- 100+ 节点流程图加载时间
- 导出大数据量表格性能
