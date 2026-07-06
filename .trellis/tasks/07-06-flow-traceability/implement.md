# 流程图溯源功能 - 执行计划

## 1. 任务分解

### Phase 1: 数据层扩展 (Day 1-2)
- [ ] 1.1 扩展 `FlowchartNode` 和 `FlowchartData` 类型定义
- [ ] 1.2 创建 `NodeTraceability` 接口
- [ ] 1.3 更新后端数据库 Schema（新增溯源表）
- [ ] 1.4 实现溯源相关 API（绑定/解绑/查询）

### Phase 2: 核心功能实现 (Day 3-5)
- [ ] 2.1 扩展 `DynamicNode.svelte` 组件（显示绑定状态）
- [ ] 2.2 创建 `EntityBindingPanel.svelte` 组件
- [ ] 2.3 扩展 `NodeConfigPanel.svelte`（集成溯源绑定）
- [ ] 2.4 创建 `TraceabilitySidebar.svelte` 组件
- [ ] 2.5 实现节点绑定/解绑逻辑

### Phase 3: 思维导图视图 (Day 6-7)
- [ ] 3.1 扩展 `PMMindMap.svelte`（支持流程图数据）
- [ ] 3.2 实现视图切换功能
- [ ] 3.3 思维导图节点点击事件（展开侧边栏）

### Phase 4: 导出功能 (Day 8)
- [ ] 4.1 集成 `xlsx` 库
- [ ] 4.2 实现表格导出逻辑
- [ ] 4.3 添加导出按钮和下载功能

### Phase 5: 测试与优化 (Day 9-10)
- [ ] 5.1 单元测试
- [ ] 5.2 集成测试
- [ ] 5.3 性能优化
- [ ] 5.4 代码审查

## 2. 详细执行步骤

### Step 1.1: 扩展类型定义

**文件**: `src/lib/apis/pm/types.ts`

```typescript
// 在 FlowchartNode 的 data 中添加 traceability 字段
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
    traceability?: NodeTraceability; // NEW
  };
}

// 新增溯源接口
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

### Step 1.2: 后端数据库 Schema

**文件**: `backend/open_webui/pm/migrations/XXX_add_flowchart_traceability.py`

```python
# 创建溯源表
# 见 design.md 中的 SQL 定义
```

### Step 1.3: 后端 API 实现

**文件**: `backend/open_webui/pm/routers/flowchart.py`

新增端点：
- `POST /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/{nodeId}/bind`
- `DELETE /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/{nodeId}/bind`
- `GET /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/{nodeId}/traceability`
- `POST /api/pm/projects/{projectId}/flowcharts/{flowchartId}/nodes/batch-bind`
- `GET /api/pm/projects/{projectId}/flowcharts/{flowchartId}/export`

### Step 2.1: 扩展 DynamicNode 组件

**文件**: `src/lib/components/pm/flowchart/DynamicNode.svelte`

修改内容：
- 读取 `data.traceability` 字段
- 根据绑定类型显示不同图标（PRD/模块/功能/参数）
- 绑定后节点边框颜色变化

### Step 2.2: 创建 EntityBindingPanel

**文件**: `src/lib/components/pm/flowchart/EntityBindingPanel.svelte`

功能：
- 实体类型选择下拉框
- 实体列表搜索和选择
- 版本选择
- 绑定/解绑按钮

### Step 2.3: 扩展 NodeConfigPanel

**文件**: `src/lib/components/pm/flowchart/NodeConfigPanel.svelte`

修改内容：
- 添加"溯源绑定"标签页
- 集成 EntityBindingPanel
- 显示当前绑定状态

### Step 2.4: 创建 TraceabilitySidebar

**文件**: `src/lib/components/pm/flowchart/TraceabilitySidebar.svelte`

功能：
- 节点基本信息展示
- 绑定实体详情
- 版本历史
- 关联参数列表

### Step 3.1: 扩展 PMMindMap

**文件**: `src/lib/components/pm/PMMindMap.svelte`

修改内容：
- 支持接收流程图数据
- 将流程图节点转换为思维导图节点
- 点击节点触发侧边栏

### Step 4.1: 集成 xlsx 库

**命令**: 
```bash
npm install xlsx --save
```

**文件**: `src/lib/utils/exportFlowchart.ts`

功能：
- 将流程图数据转换为表格
- 生成 CSV/Excel 文件
- 触发浏览器下载

## 3. 验证命令

### 3.1 类型检查
```bash
npm run check
```

### 3.2 构建测试
```bash
npm run build
```

### 3.3 后端测试
```bash
cd backend
pytest tests/pm/test_flowchart_traceability.py -v
```

## 4. 回滚计划

### 4.1 数据库回滚
```sql
-- 删除溯源表
DROP TABLE IF EXISTS flowchart_node_traceability;
```

### 4.2 代码回滚
- 使用 git revert 回滚到上一个版本
- 或者手动删除新增的文件和修改

## 5. 风险缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| @xyflow/svelte API 变更 | 高 | 封装节点组件，隔离底层变化 |
| 数据库迁移失败 | 高 | 先备份数据，使用事务执行迁移 |
| 性能问题 | 中 | 使用虚拟化，懒加载溯源信息 |
| 兼容性问题 | 中 | 向后兼容，未绑定节点正常显示 |

## 6. 交付物清单

### 6.1 新增文件
- `src/lib/components/pm/flowchart/EntityBindingPanel.svelte`
- `src/lib/components/pm/flowchart/TraceabilitySidebar.svelte`
- `src/lib/components/pm/flowchart/ViewToggle.svelte`
- `src/lib/stores/pm/flowchartStore.ts`
- `src/lib/utils/exportFlowchart.ts`
- `backend/open_webui/pm/migrations/XXX_add_flowchart_traceability.py`
- `backend/open_webui/pm/routers/flowchart_traceability.py`

### 6.2 修改文件
- `src/lib/apis/pm/types.ts`
- `src/lib/components/pm/PMFlowchartEditor.svelte`
- `src/lib/components/pm/PMMindMap.svelte`
- `src/lib/components/pm/flowchart/DynamicNode.svelte`
- `src/lib/components/pm/flowchart/NodeConfigPanel.svelte`
- `src/lib/components/pm/flowchart/CustomEdge.svelte`

## 7. 验收检查点

### 7.1 功能检查
- [ ] 节点可以绑定到 PRD/模块/功能/参数
- [ ] 绑定后节点显示正确图标
- [ ] 思维导图视图正常展示
- [ ] 侧边栏显示正确信息
- [ ] 导出表格包含所有字段

### 7.2 性能检查
- [ ] 100 个节点加载 < 1s
- [ ] 导出 100 条记录 < 500ms

### 7.3 兼容性检查
- [ ] 现有流程图数据正常加载
- [ ] 未绑定节点正常显示
