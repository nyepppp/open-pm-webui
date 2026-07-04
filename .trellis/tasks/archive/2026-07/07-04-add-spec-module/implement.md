# SPEC 模块 — 实施计划

## 实施顺序

### Step 1: 类型注册与模块配置
**文件**: `src/lib/apis/pm/types.ts`, `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`, `src/routes/(app)/pm/[projectId]/+page.svelte`, `src/routes/(app)/pm/[projectId]/+layout.svelte`
- [ ] `ModuleType` 新增 `'spec'`
- [ ] `moduleConfig` 新增 `spec: { name: 'SPEC 规范', editorType: 'rich' }`
- [ ] `moduleGroups` 设计分组新增 spec 条目
- [ ] `moduleLabels` 新增 `'spec': 'SPEC 规范'`
- [ ] `svgIcons` 新增 spec 图标（使用文档/规范相关图标）
- **验证**: 刷新页面，侧边栏和仪表盘出现 SPEC 入口，点击进入空列表页

### Step 2: SPEC 创建流程 + 分类
**文件**: `+page.svelte`, `src/lib/components/pm/specTemplates.ts`
- [ ] 创建 `specTemplates.ts`，定义 `SpecTemplate` 接口和内置模板数据
- [ ] 创建 `PMSpecTemplateDialog.svelte` 组件
- [ ] 修改 `handleCreate`：当 `moduleType === 'spec'` 时，先弹出模板选择对话框
- [ ] 模板选择后，将模板 content 作为 entry 的 content 创建
- [ ] 创建/编辑 drawer 中增加分类下拉框（功能 SPEC / 前端原型 SPEC）
- [ ] 分类存储到 `metadata.specCategory`
- **验证**: 新建 SPEC 时弹出模板选择，选择后编辑器填充模板内容

### Step 3: 卡片列表展示
**文件**: `+page.svelte`
- [ ] SPEC 卡片视图中显示分类标签（功能=蓝色，前端原型=紫色）
- [ ] 分类标签从 `entry.metadata?.specCategory` 读取
- [ ] 未设置分类时显示"未分类"
- **验证**: SPEC 列表中每个卡片显示分类标签

### Step 4: 术语参考面板
**文件**: `src/lib/components/pm/specTemplates.ts`, `src/lib/components/pm/PMSpecGlossaryPanel.svelte`, `+page.svelte`
- [ ] 在 `specTemplates.ts` 中定义术语数据（布局排版/文字排版/色彩系统各 15-20 条）
- [ ] 创建 `PMSpecGlossaryPanel.svelte` 组件（tab 切换 + 术语列表 + 插入按钮）
- [ ] 编辑 drawer 中：当 specCategory === 'prototype' 时显示术语面板
- [ ] 术语面板与编辑器并排布局（flex），面板可折叠
- [ ] 点击术语插入：通过 editor instance 调用 `editor.chain().focus().insertContent()`
- **验证**: 编辑前端原型 SPEC 时右侧显示术语面板，点击可插入术语

### Step 5: 追溯关联
**文件**: `+page.svelte`
- [ ] 编辑 drawer 中增加"关联需求"和"关联参数"两个 PMRelationPicker
- [ ] 关联选择后存储到 `metadata.relatedRequirements` / `metadata.relatedParameters`
- [ ] 卡片列表上显示关联数量 badge
- **验证**: SPEC 条目可关联需求和参数，卡片显示关联数量

### Step 6: 自定义模板管理
**文件**: `+page.svelte`
- [ ] SPEC 页面顶部增加"模板管理"按钮
- [ ] 点击打开模板列表 drawer
- [ ] 模板列表：内置模板（只读）+ 自定义模板（可编辑/删除）
- [ ] 新建模板：名称 + 分类 + 富文本内容 → 保存为 `metadata.role: 'template'` 的 entry
- [ ] PMSpecTemplateDialog 中加载自定义模板列表
- **验证**: 可创建自定义模板，新建 SPEC 时可看到并选择自定义模板

## 验证命令

```bash
# 类型检查
npx svelte-check --tsconfig ./tsconfig.json

# 开发服务器
npm run dev
```

## 回滚点

每个 Step 完成后应可独立验证。如果某 Step 出问题，回滚该 Step 的文件修改即可。

## 风险文件

- `+page.svelte`（2300+ 行）— 修改量最大，需小心避免影响其他模块
