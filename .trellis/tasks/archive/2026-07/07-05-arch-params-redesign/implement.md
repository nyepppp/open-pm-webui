# Implement: 产品架构图重设计 & 参数配置重构

## Execution Checklist

### Phase 1: 类型与导航基础设施

- [ ] **1.1** 更新 `ModuleType` 类型，新增 `'architecture'`
  - 文件: `src/lib/apis/pm/types.ts`
  - 在 `ModuleType` union 中添加 `| 'architecture'`

- [ ] **1.2** 更新侧边栏导航
  - 文件: `src/lib/stores/pm/moduleStore.ts`
  - `planning` 分类移除 `parameter` 入口
  - `design` 分类新增 `{ id: 'architecture', label: '产品架构', icon: 'Layers', category: 'design', path: '/pm/architecture' }`
  - `review` 分类移除 `product-architecture` 入口

- [ ] **1.3** 更新 moduleEditorConfig
  - 文件: `src/lib/components/pm/moduleFields.ts`
  - 新增 `architecture` 条目: `editorType: 'mixed'`, `label: '产品架构'`, `category: 'design'`
  - 保留 `parameter` 和 `product-architecture` 的 field config 不变

- [ ] **1.4** 验证: 侧边栏导航正确显示，点击可跳转

### Phase 2: 新路由与页面框架

- [ ] **2.1** 创建新路由页面
  - 文件: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`
  - 页面结构: Tab bar + 两个 Tab 内容区域
  - 加载 parameter 和 product-architecture 两套数据
  - 管理 `activeTab`、`navigateToModule`、`navigateToFeature` 状态

- [ ] **2.2** 旧路由重定向
  - 在现有 `[module]` 路由中，当 moduleType 为 `parameter` 或 `product-architecture` 时，redirect 到 `/pm/[projectId]/architecture`
  - 文件: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 顶部添加 redirect 逻辑

- [ ] **2.3** 验证: 访问旧 URL 自动跳转到新路由，Tab 切换正常

### Phase 3: 架构图 Tab 增强

- [ ] **3.1** 增强节点聚合逻辑
  - 在 ArchitecturePage 中实现 `aggregateModuleFeatureTree` 函数
  - 从 parameter 条目自动聚合模块/功能
  - 从 product-architecture 条目读取手动补充节点
  - 合并两者生成完整的节点树

- [ ] **3.2** 增强 PMMindMap 组件
  - 文件: `src/lib/components/pm/PMMindMap.svelte`
  - 新增 Props: `aggregatedNodes` (自动聚合节点), `onNavigate` (跨 Tab 导航回调)
  - 节点语义映射: root=产品, branch=模块, leaf=功能
  - auto 节点显示实线边框，manual 节点显示虚线边框 + "规划中" badge
  - auto 节点删除按钮隐藏，manual 节点可删除
  - 节点点击触发 `onNavigate` 而非直接跳转路由

- [ ] **3.3** 验证: 架构图正确显示产品→模块→功能层级，auto/manual 节点视觉区分，节点点击触发导航

### Phase 4: 参数详情 Tab 重构

- [ ] **4.1** 创建 ModuleFeatureTree 组件
  - 文件: `src/lib/components/pm/ModuleFeatureTree.svelte`
  - Props: `modules: TreeModule[]`, `selectedModule`, `selectedFeature`, `onSelect`, `onAddModule`, `onAddFeature`, `onRename`, `onDelete`
  - 渲染模块→功能树形列表
  - 支持选中高亮、展开/折叠
  - 支持右键或操作按钮：新增模块/功能、重命名、删除
  - manual 节点显示"规划中"标记

- [ ] **4.2** 提取参数表格逻辑
  - 文件: `src/lib/components/pm/ParameterTable.svelte`
  - 从现有 `+page.svelte` 中提取参数相关的表格渲染、CRUD、行内编辑逻辑
  - Props: `entries`, `projectId`, `filterModule`, `filterFeature`
  - 新增参数时自动填充当前 filterModule/filterFeature

- [ ] **4.3** 组装参数详情 Tab
  - 左侧: ModuleFeatureTree
  - 右侧: ParameterTable
  - 左侧面板可折叠（小屏时默认折叠为下拉选择器）
  - 响应式断点: < 768px 时左侧面板折叠

- [ ] **4.4** 验证: 参数详情 Tab 正确显示三级结构，CRUD 功能正常，折叠响应式正确

### Phase 5: 跨 Tab 对齐与集成

- [ ] **5.1** 跨 Tab 导航
  - 架构图节点点击 → 设置 navigateToModule/navigateToFeature → 切到参数详情 Tab
  - 参数详情 Tab 检测导航目标 → 自动选中左侧树节点 → 过滤右侧参数表

- [ ] **5.2** 数据同步
  - 参数详情 Tab 新增参数（含新 moduleName/featureName）→ 通知架构图 Tab 刷新聚合数据
  - 参数详情 Tab 删除最后一个某模块/功能下的参数 → 架构图自动聚合节点消失

- [ ] **5.3** 手动节点管理
  - 架构图 Tab 添加手动模块/功能节点 → 调用 product-architecture API 保存
  - 参数详情 Tab 左侧树可见手动节点（标记"规划中"）

- [ ] **5.4** 验证: 完整的跨 Tab 导航流程，数据增删同步正确

### Phase 6: 清理与回归

- [ ] **6.1** 确认旧功能保留
  - 架构同步功能正常
  - 版本过滤正常
  - 参数 flowchart 关联正常
  - 参数搜索/筛选/排序正常

- [ ] **6.2** 更新 moduleConfig
  - 文件: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
  - 新增 `architecture` 的 moduleConfig 条目（指向新页面或 redirect）

- [ ] **6.3** 最终验证: 所有 AC 通过

## Validation Commands

```bash
# 类型检查
npx svelte-check --tsconfig ./tsconfig.json

# Lint
npx eslint src/lib/components/pm/ModuleFeatureTree.svelte src/lib/components/pm/ParameterTable.svelte src/routes/\(app\)/pm/\[projectId\]/architecture/+page.svelte

# 开发服务器启动验证
npm run dev
```

## Risky Files / Rollback Points

| 文件 | 风险 | 回滚策略 |
|------|------|----------|
| `moduleStore.ts` | 导航变更影响全局侧边栏 | git checkout 恢复 |
| `PMMindMap.svelte` | 增强可能破坏现有架构图功能 | Props 默认值保持向后兼容 |
| `[module]/+page.svelte` | 已有 2000+ 行，添加 redirect 逻辑需谨慎 | 仅在 onMount 中添加条件 redirect |
| `types.ts` | ModuleType 变更影响所有模块 | 仅新增值，不删除旧值 |

## Follow-up Checks

- [ ] 旧 URL `/pm/{id}/parameter` 和 `/pm/{id}/product-architecture` 正确 redirect
- [ ] 无参数的空项目，架构图 Tab 和参数详情 Tab 不报错
- [ ] 大量参数（100+）时左侧树和参数表性能可接受
- [ ] 暗色模式下视觉区分 auto/manual 节点清晰
