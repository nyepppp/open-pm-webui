# PM工作台溯源下拉列表新增版本信息展示 - 技术设计

## 背景

当前PM工作台中所有溯源（Trace）相关的下拉选择组件仅显示溯源名称，用户无法直观区分同名但不同版本的溯源。需要在所有溯源下拉列表中增加版本信息展示。

## 技术现状分析

### 前端技术栈
- **框架**: Svelte 5 (使用 `$props`, `$state`, `$derived` 等新语法)
- **样式**: Tailwind CSS
- **类型**: TypeScript

### 涉及组件分析

通过代码分析，发现以下组件涉及溯源/实体的下拉选择功能：

#### 1. `PMRelationPicker.svelte` (主要组件)
- **路径**: `src/lib/components/pm/PMRelationPicker.svelte`
- **功能**: 关联条目选择器，支持下拉搜索选择
- **当前展示**: 仅显示 `item.title`
- **数据接口**: `ModuleEntry` (包含 `version` 字段)
- **修改点**: 
  - 下拉列表项展示: 第217-218行 `{item.title}` → 增加版本号
  - 选中后回显: 第124行 `{selectedItem.title}` → 增加版本号

#### 2. `PMDataSelector.svelte` (数据选择器)
- **路径**: `src/lib/components/pm/PMDataSelector.svelte`
- **功能**: 项目/模块/条目三级选择器
- **当前展示**: 仅显示条目标题
- **数据接口**: 自定义 `Entry` 接口 (无版本字段)
- **修改点**: 需要确认后端API是否返回版本字段

#### 3. `PMAnnotationLinkDialog.svelte` (批注关联对话框)
- **路径**: `src/lib/components/pm/PMAnnotationLinkDialog.svelte`
- **功能**: 批注关联条目选择
- **当前展示**: 仅显示 `entry.title`
- **修改点**: 第169行展示区域

#### 4. `EntityBindingPanel.svelte` (实体绑定面板)
- **路径**: `src/lib/components/pm/flowchart/EntityBindingPanel.svelte`
- **功能**: 流程图节点实体绑定
- **当前展示**: 仅显示 `entity.title || entity.name`
- **修改点**: 第124行展示区域

### 数据模型

```typescript
// ModuleEntry 接口 (来自 src/lib/apis/pm/types.ts)
interface ModuleEntry {
  id: string;
  projectId: string;
  moduleType: ModuleType;
  title: string;
  content?: string;
  data?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  versionId?: string;
  status: ModuleStatus;
  priority?: Priority;
  currentVersionNumber?: string;  // ← 版本号字段
  branchName?: string;
  createdAt: number;
  updatedAt: number;
  version: number; // optimistic lock
}
```

**关键发现**: `ModuleEntry` 接口已包含 `currentVersionNumber` 字段，可用于展示版本信息。

## 设计方案

### 展示格式

统一格式: `{title} (v{currentVersionNumber})`

示例:
- `需求分析文档 (v1.2)`
- `用户登录功能 (v2.0)`

### 修改范围

| 组件 | 文件路径 | 修改内容 | 优先级 |
|------|---------|---------|--------|
| PMRelationPicker | `src/lib/components/pm/PMRelationPicker.svelte` | 下拉选项 + 选中回显 | 高 |
| PMDataSelector | `src/lib/components/pm/PMDataSelector.svelte` | 条目列表展示 | 中 |
| PMAnnotationLinkDialog | `src/lib/components/pm/PMAnnotationLinkDialog.svelte` | 条目列表展示 | 中 |
| EntityBindingPanel | `src/lib/components/pm/flowchart/EntityBindingPanel.svelte` | 实体列表展示 | 中 |

### 实现细节

#### 1. 版本号获取逻辑

```typescript
function getDisplayTitle(item: ModuleEntry): string {
  const version = item.currentVersionNumber || item.version?.toString();
  if (version) {
    return `${item.title} (v${version})`;
  }
  return item.title;
}
```

#### 2. 搜索兼容性

搜索功能应继续基于原始 `title` 进行匹配，而不是展示文本。当前代码已实现此逻辑，无需修改。

#### 3. 样式调整

版本号部分使用较小字号和次要颜色，避免喧宾夺主：

```html
<span class="text-sm font-medium text-gray-900 dark:text-gray-100">
  {item.title}
</span>
<span class="text-xs text-gray-500 dark:text-gray-400 ml-1">
  (v{item.currentVersionNumber || item.version})
</span>
```

## 兼容性考虑

1. **向后兼容**: 如果某些条目没有版本号，仅显示标题，不影响功能
2. **数据一致性**: 使用 `currentVersionNumber` 字段，该字段已在 `ModuleEntry` 接口中定义
3. **表单提交**: 仅修改展示文本，不影响底层数据结构和表单提交逻辑

## 验收标准

- [ ] `PMRelationPicker` 下拉选项和选中回显均展示版本号
- [ ] `PMDataSelector` 条目列表展示版本号
- [ ] `PMAnnotationLinkDialog` 条目列表展示版本号
- [ ] `EntityBindingPanel` 实体列表展示版本号
- [ ] 版本号展示格式统一为 `(v{version})`
- [ ] 无版本号的条目仅显示标题，不显示异常
- [ ] 搜索功能正常工作
