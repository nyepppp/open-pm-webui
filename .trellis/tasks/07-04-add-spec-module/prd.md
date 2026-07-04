# 新增 SPEC 规范文档模块

## Goal

在 PM 工作台中新增 SPEC（规范文档）模块，作为需求文档和参数配置的下游文档，支持规范追溯、分类管理、模板系统和 AI 可读结构化内容。

## Background

### Issue 来源
GitHub Issue #12

### 现有代码结构
- 统一模块页面：`src/routes/(app)/pm/[projectId]/[module]/+page.svelte`，模块配置通过 `moduleConfig` 字典驱动
- 侧边栏导航在 `[projectId]/+page.svelte` 的 `moduleGroups` 中定义，按规划/设计/执行/复盘/边界分组
- 类型定义在 `src/lib/apis/pm/types.ts`，`ModuleType` 联合类型需扩展
- 数据模型 `ModuleEntry` 已有 `moduleType`、`title`、`content`、`metadata`、`versionId` 等通用字段
- 富文本编辑器 `PMRichEditor` 基于 TipTap
- 关联选择器 `PMRelationPicker` 已存在

### SPEC 术语参考
本地目录 `D:\产品文档\模板\原型_SPEC` 包含前端原型设计规范模板：
- 布局排版.md — 视觉设计规范（布局基础、栅格系统、页面布局模式、响应式、前端布局工程）
- 文字排版.md — Typography 规范（字体分类、文本布局、字形解剖、数字排版度量、渲染术语）
- 色彩系统.md — Color System 规范（色彩基础、色彩表示法、色彩架构、色彩工程、无障碍、视觉效果）

### 架构决策
- SPEC 无子层级，一个 SPEC 就是一个完整页面规范
- SPEC 内部按分类区分（功能 SPEC / 前端原型 SPEC），分类存储在 metadata 中
- 编辑交互：富文本自由编辑 + 术语参考卡片侧边面板（可勾选插入术语条目）
- 追溯关联：复用 PMRelationPicker，关联需求和参数
- 自定义模板：复用 entry 存储（metadata.role: 'template'），内置 2 个模板

## Requirements

### R1: SPEC 模块注册与导航
- 在 `moduleConfig` 中新增 `spec` 条目，`editorType: 'rich'`
- 在 `ModuleType` 联合类型中新增 `'spec'`
- 在侧边栏 `moduleGroups` 的"设计"分组中添加 SPEC 入口
- 在仪表盘 `moduleLabels` 中添加 `'spec': 'SPEC 规范'`
- 在 `svgIcons` 中添加 spec 图标

### R2: SPEC 分类
- SPEC 条目支持分类：功能 SPEC、前端原型 SPEC
- 分类存储在 entry 的 `metadata.specCategory` 中，值为 `'functional' | 'prototype'`
- 卡片列表视图中显示分类标签（功能 SPEC 用蓝色，前端原型 SPEC 用紫色）
- 创建/编辑时通过下拉框选择分类

### R3: SPEC 模板系统
- 新建 SPEC 时弹出模板选择对话框，展示内置模板和自定义模板
- 内置模板（硬编码）：
  - 功能 SPEC 模板：概述 → 需求追溯 → 功能规格（输入/处理逻辑/输出/异常处理）→ 验收标准
  - 前端原型 SPEC 模板：设计规范追溯 → 页面结构 → 交互规格 → 组件规格 → 响应式策略
- 自定义模板：存储为 `moduleType: 'spec'` + `metadata.role: 'template'` 的 entry
- 选择模板后自动填充富文本内容到编辑器
- 可选"空白"跳过模板

### R4: 术语参考卡片面板
- 编辑 SPEC（前端原型 SPEC 分类）时，右侧显示术语参考面板
- 面板按维度分 tab：布局排版、文字排版、色彩系统
- 每个术语条目显示：术语名（中英文）、简要定义
- 点击术语条目可插入到编辑器光标位置（插入格式：**术语名 (English)**：定义）
- 面板可折叠/展开，不影响编辑区域

### R5: 追溯关联
- SPEC 编辑 drawer 中增加"关联需求"和"关联参数"两个关联选择器
- 复用 `PMRelationPicker` 组件
- 关联数据存储在 `metadata.relatedRequirements: string[]` 和 `metadata.relatedParameters: string[]`
- SPEC 卡片列表上显示关联数量 badge

### R6: 自定义模板管理
- SPEC 模块页面顶部"模板管理"按钮，打开模板列表 drawer
- 模板列表展示内置模板（不可编辑）和自定义模板（可编辑/删除）
- 创建自定义模板：填写名称、分类、富文本内容
- 自定义模板本质是 `metadata.role: 'template'` 的 entry，复用现有 CRUD

## Acceptance Criteria

- [ ] PM 工作台侧边栏"设计"分组中出现 SPEC 规范入口
- [ ] 仪表盘显示 SPEC 模块卡片和条目计数
- [ ] 可创建 SPEC 文档，创建时选择分类和模板
- [ ] 内置模板选择后自动填充富文本内容
- [ ] 前端原型 SPEC 编辑时右侧显示术语参考面板
- [ ] 术语参考面板支持按维度切换，点击插入到编辑器
- [ ] SPEC 条目可关联需求文档和参数配置
- [ ] SPEC 卡片列表显示分类标签和关联数量 badge
- [ ] 自定义模板可创建、编辑、删除
- [ ] 新建 SPEC 时可选择自定义模板

## Out of Scope

- AI 自动推荐关联（后续 AI 功能）
- 跨项目模板共享
- 模板版本管理
- 模板导入/导出
- 子 SPEC 层级
- SPEC 自动生成（后续 AI 功能）
