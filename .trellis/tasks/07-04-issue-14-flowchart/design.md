# 流程图模块技术设计

## Architecture

### 模块定位

新增 `flowchart` 模块类型，与现有 14 个模块（prd, requirement, parameter, testcase, risk, competitor, roadmap, meeting, acceptance, faq, product-architecture, prototype, schedule, requirement-boundary）并列。

### 数据流

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Flowchart      │────▶│  ModuleEntry    │────▶│  Backend API    │
│  Editor (Svelte)│     │  (data.flowchart)│     │  (REST)         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         │                                               │
         │                    ┌─────────────────┐      │
         └───────────────────▶│  Parameter      │◀─────┘
                                │  Module         │
                                └─────────────────┘
```

### 核心数据结构

#### FlowchartData (存储在 ModuleEntry.data.flowchart)

```typescript
interface FlowchartData {
  nodes: FlowchartNode[];
  edges: FlowchartEdge[];
  viewport?: { x: number; y: number; zoom: number };
  // 用户自定义节点类型定义库
  nodeTypes?: Record<string, CustomNodeType>;
}

// 自定义节点类型定义
interface CustomNodeType {
  label: string;
  defaultStyle: NodeStyle;
  icon?: string;
  description?: string;
}

// 节点样式
interface NodeStyle {
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  borderRadius?: number;
  width?: number;
  height?: number;
  icon?: string;
  shape?: 'rectangle' | 'rounded' | 'circle' | 'diamond' | 'ellipse';
}

interface FlowchartNode {
  id: string;
  type: string; // 用户自定义类型名称
  position: { x: number; y: number };
  data: {
    label: string;
    description?: string;
    // 节点样式（覆盖默认样式）
    style?: Partial<NodeStyle>;
    // 参数关联（引用关联方案）
    inputParams?: string[];  // 参数ID列表
    outputParams?: string[]; // 参数ID列表
  };
}

interface FlowchartEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: 'default' | 'conditional';
  // 连线样式
  style?: EdgeStyle;
}

interface EdgeStyle {
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string; // 实线/虚线
  animated?: boolean;
}
```

### 组件架构

```
FlowchartModule
├── FlowchartEditor          # 主编辑器容器
│   ├── FlowchartCanvas      # SvelteFlow 画布
│   │   ├── CustomNode       # 动态节点渲染器（根据 type 渲染不同形状）
│   │   │   ├── RectangleNode    # 矩形（默认）
│   │   │   ├── RoundedNode      # 圆角矩形
│   │   │   ├── CircleNode       # 圆形
│   │   │   ├── DiamondNode      # 菱形
│   │   │   └── EllipseNode      # 椭圆
│   │   └── CustomEdge       # 支持样式的自定义连线
│   ├── NodePanel            # 节点工具栏（预设模板 + 自定义类型）
│   ├── NodeConfigPanel      # 节点属性配置面板
│   │   ├── StyleEditor         # 样式编辑器（颜色、边框、大小）
│   │   └── ParameterSelector   # 参数选择器（关联参数清单）
│   ├── NodeTypeManager      # 节点类型管理器（创建/编辑自定义类型）
│   └── FlowchartToolbar     # 工具栏（保存、导出、缩放、网格）
└── FlowchartViewer          # 只读查看模式
```

### API 设计

复用现有 PM 模块 API，无需新增接口：

- `GET /projects/{projectId}/modules/flowchart` - 获取流程图列表
- `POST /projects/{projectId}/modules/flowchart` - 创建流程图
- `GET /projects/{projectId}/modules/flowchart/{id}` - 获取单个流程图
- `PUT /projects/{projectId}/modules/flowchart/{id}` - 更新流程图
- `DELETE /projects/{projectId}/modules/flowchart/{id}` - 删除流程图

### 参数关联方案（双向同步）

采用 **引用关联 + 双向同步**：

1. 节点通过 `inputParams` 和 `outputParams` 存储参数 ID 列表
2. **参数清单 → 流程图**：参数清单模块通过反向索引查询关联的节点
3. **流程图 → 参数清单**：节点参数变更时，通过 API 同步更新参数清单中的关联关系
4. **双向同步机制**：
   - 当节点添加/移除参数关联时，更新参数清单中的 `flowchartRefs` 字段
   - 当参数被删除时，触发流程图数据清理（移除被删除参数的关联）
   - 同步通过后端 API 事务保证一致性

### 状态管理

- 使用 Svelte 5 runes 管理本地状态
- 流程图数据变更时自动触发 auto-save（30秒间隔，与现有 PRD 编辑器一致）
- 节点位置变更实时更新（debounce 200ms）

### 兼容性

- 新增 `flowchart` 到 `ModuleType` 联合类型
- 在 `moduleConfig` 中新增 flowchart 配置
- 不影响现有模块功能

## Rollback

- 删除新增的 flowchart 模块类型和相关组件即可回滚
- 数据保留在数据库中，重新添加模块后可恢复
