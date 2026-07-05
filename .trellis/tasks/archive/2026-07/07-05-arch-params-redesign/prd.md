# 产品架构图重设计 & 参数配置重构

## Goal

将当前独立的"产品架构"模块和"参数配置"模块合并为一个统一页面，用 Tab 切换查看：
- **架构图 Tab**：思维导图形式展示模块→功能的层级关系，关联版本、描述信息
- **参数详情 Tab**：从"参数为主体"改为"模块→功能→参数"三级层级结构，对齐其他模块的功能

合并后用户可以在同一页面从宏观（架构总览）切换到微观（参数配置），消除两个独立模块之间的割裂感。

## Background

### 当前产品架构模块 (product-architecture)
- 侧边栏导航位于 `review` 分类，路径 `/pm/product-architecture`
- 编辑器类型为 `mindmap`，使用 `@xyflow/svelte` (SvelteFlow) 渲染思维导图
- 节点类型：root / branch / leaf / dependency
- 节点数据：`MindMapNode` (id, label, type, position, metadata, moduleRef)
- 支持架构同步（从其他模块自动提取节点）
- 字段：architectureType, techStack, autoExtracted

### 当前参数配置模块 (parameter)
- 侧边栏导航位于 `planning` 分类，路径 `/pm/parameter`
- 编辑器类型为 `table`，表格列表展示所有参数条目
- 每条条目的主题是"参数"本身（key, paramType, dataType 等）
- 已有 moduleName / featureName 字段但交互上是 flat table
- 字段：key, moduleName(combobox), featureName(combobox, dependsOn moduleName), paramType, dataType, required, defaultValue, description

### 问题
1. 架构图不关联模块→功能层级，只有 root/branch/leaf，缺乏业务语义
2. 参数配置以"参数"为主体，难以按模块/功能维度查看和组织
3. 两个模块割裂在不同分类和路由，用户需来回切换
4. 架构图和参数信息没有对齐，无法从架构图直接查看对应参数

## Requirements

### R1: 合并路由和导航
- 将 `product-architecture` 和 `parameter` 合并为一个统一路由 `/pm/architecture`
- 侧边栏导航合并为一个入口，放在 `design` 分类，label "产品架构"，icon "Layers"
- 页面顶部用 Tab 组件切换"架构图"和"参数详情"两个视图
- 原 `/pm/product-architecture` 和 `/pm/parameter` 路径从侧边栏移除

### R2: 架构图 Tab 重设计
- 思维导图节点承载业务语义：
  - 第一层（root）：产品名称
  - 第二层（branch）：**模块**（如用户管理、支付系统）
  - 第三层（leaf）：**功能**（如登录注册、支付退款）
  - 每个节点展示关联信息：版本号、描述、状态
- **节点数据来源**：
  - 默认从参数条目的 `moduleName`/`featureName` 字段自动聚合生成模块和功能节点
  - 允许手动添加无参数的模块/功能节点（标记为"规划中"状态，视觉上区分）
  - 自动聚合的节点不可手动删除（删除需先删除对应参数条目），手动补充的节点可自由增删
- 架构图节点可点击导航到参数详情 Tab（自动过滤到该模块/功能）
- 保留架构同步功能（从其他模块自动提取更新）
- 保留版本过滤功能

### R3: 参数详情 Tab 重构交互
- 交互方式从 flat table 改为左侧树 + 右侧列表的双栏布局：
  - 左侧面板：模块→功能树形导航，选中功能节点后右侧展示该功能的参数列表
  - 右侧面板：参数表格/列表，展示当前选中功能下的所有参数
  - 左侧面板可折叠，小屏时自动折叠为顶部下拉选择器
- 左侧树节点支持增删改（新增模块/功能、重命名、删除）
- 支持按模块/功能快速筛选和定位
- 保留所有参数字段（key, paramType, dataType, required, defaultValue, description）
- 新增/编辑参数时仍然选择所属模块和功能

### R4: 跨 Tab 对齐
- 架构图中的模块/功能节点与参数详情中的模块/功能对齐
- 架构图点击节点 → 切到参数详情 Tab 并自动聚焦到该模块/功能
- 参数详情中新增参数并填写新模块/功能时 → 架构图自动聚合出对应节点
- 手动补充的模块/功能节点在参数详情 Tab 的左侧树中也可见（标记"规划中"）

## Acceptance Criteria

- [ ] AC1: 合并后的页面通过单一路由访问，Tab 切换架构图和参数详情视图
- [ ] AC2: 架构图 Tab 的节点层级为 产品→模块→功能，每个节点展示版本和描述
- [ ] AC3: 参数详情 Tab 以模块→功能→参数三级结构展示，不再以参数为 flat 主体
- [ ] AC4: 点击架构图节点可导航到参数详情 Tab 的对应模块/功能筛选
- [ ] AC5: 侧边栏导航合并为一个入口，原 `parameter` 和 `product-architecture` 入口移除
- [ ] AC6: 原有的架构同步、版本过滤、参数 CRUD 功能完整保留
- [ ] AC7: 数据模型向后兼容——旧数据可正常加载和展示

## Technical Notes

- 前端合并为单路由 `/pm/architecture`，后端保持 `parameter` 和 `product-architecture` 两个独立 moduleType 不变
- 页面内同时调用两套 API，架构图 Tab 使用 `product-architecture` API，参数详情 Tab 使用 `parameter` API
- 架构图的自动聚合节点从参数条目的 `moduleName`/`featureName` 字段实时计算得出
- 手动补充的模块/功能节点仍存储在 `product-architecture` 条目的 data 中
- 数据完全向后兼容，旧数据无需迁移
