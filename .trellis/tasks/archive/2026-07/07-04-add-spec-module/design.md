# SPEC 模块 — 技术设计

## 架构概述

SPEC 模块复用现有 PM 模块架构，`editorType: 'rich'`，通过 `moduleConfig` 注册。核心新增：
1. 模板选择流程（创建时）
2. 术语参考面板（编辑时，新组件）
3. SPEC 分类（metadata 扩展）
4. 追溯关联（复用 PMRelationPicker）

## 数据模型

### ModuleType 扩展
```typescript
// types.ts 新增
| 'spec'
```

### Metadata Schema
```typescript
interface SpecMetadata {
  specCategory: 'functional' | 'prototype';  // R2 分类
  role?: 'template';                          // R6 模板标记
  relatedRequirements?: string[];             // R5 关联需求 entry IDs
  relatedParameters?: string[];               // R5 关联参数 entry IDs
}
```

### 内置模板数据结构
```typescript
interface SpecTemplate {
  id: string;
  name: string;
  category: 'functional' | 'prototype';
  content: string;  // 富文本 HTML
  isBuiltIn: boolean;
}
```

内置模板硬编码在 `src/lib/components/pm/specTemplates.ts` 中。

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/lib/components/pm/specTemplates.ts` | 内置模板定义 + 术语数据 |
| `src/lib/components/pm/PMSpecTemplateDialog.svelte` | 模板选择对话框 |
| `src/lib/components/pm/PMSpecGlossaryPanel.svelte` | 术语参考侧边面板 |

## 修改文件

| 文件 | 修改内容 |
|------|---------|
| `src/lib/apis/pm/types.ts` | ModuleType 新增 `'spec'` |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | moduleConfig 新增 spec；创建流程增加模板选择；卡片视图增加分类 badge 和关联 badge；编辑 drawer 增加分类选择、关联选择器、术语面板 |
| `src/routes/(app)/pm/[projectId]/+page.svelte` | moduleGroups 设计分组新增 spec；svgIcons 新增图标；moduleLabels 新增 |
| `src/routes/(app)/pm/[projectId]/+layout.svelte` | moduleLabels 新增 spec |

## 组件设计

### PMSpecTemplateDialog
- Props: `{ open, onSelect(template: SpecTemplate | null), customTemplates: ModuleEntry[] }`
- 展示内置模板和自定义模板卡片列表
- 每个模板卡片显示：名称、分类标签、内容摘要
- 点击选择，onSelect 返回模板对象（null = 空白）
- 样式：居中对话框，grid 布局展示模板卡片

### PMSpecGlossaryPanel
- Props: `{ visible, editor: Editor | null }`
- 三个 tab：布局排版、文字排版、色彩系统
- 每个 tab 下是术语条目列表
- 术语条目：术语名（中/英）+ 一句话定义 + 插入按钮
- 点击插入按钮：向 TipTap editor 插入格式化文本
- 面板宽度固定 280px，右侧吸附，可折叠

### 术语数据
从 `D:\产品文档\模板\原型_SPEC` 提取核心术语，精简为每个维度 15-20 个高频术语：

```
布局排版：Layout, Composition, Visual Hierarchy, Grid, Container, Gutter, 
         Sidebar, Card Grid, Dashboard, Breakpoint, Responsive Design, 
         Flexbox, CSS Grid, Positioning, Z-index, Overflow...

文字排版：Typography, Font, Serif, Sans-Serif, Monospace, Tracking, 
         Kerning, Leading, Alignment, Baseline, X-height, PX, EM, 
         REM, Font Fallback...

色彩系统：Hue, Saturation, Lightness, Alpha, RGB, Hex, HSL, OKLCH, 
          Palette, Color Scale, Primary Color, Semantic Color, 
          Design Tokens, Contrast Ratio, WCAG...
```

## 交互流程

### 创建 SPEC
```
点击"新建" 
  → 弹出 PMSpecTemplateDialog
    → 选择分类（功能/前端原型）
    → 选择模板（内置/自定义/空白）
  → 创建 entry，content 填充模板内容
  → 打开编辑 drawer
```

### 编辑 SPEC
```
打开编辑 drawer
  → 左侧：PMRichEditor（富文本）
  → 右侧（如果分类是前端原型）：PMSpecGlossaryPanel
  → drawer 顶部：分类下拉框、关联选择器
```

### 模板管理
```
点击"模板管理"按钮
  → 打开模板 drawer
  → 列表：内置模板（灰显不可编辑）+ 自定义模板（可编辑/删除）
  → "新建模板"按钮
    → 填写名称、分类、富文本内容
    → 保存为 metadata.role='template' 的 entry
```

## 兼容性

- 新增 moduleType `'spec'` 不影响现有模块
- metadata 新字段是可选的，旧 entry 不受影响
- PMRichEditor 无需修改（模板内容通过 props 传入）
- PMRelationPicker 无需修改（直接复用）

## 风险

1. `+page.svelte` 已有 2300+ 行，新增 SPEC 逻辑会进一步膨胀 — 但这是现有架构的固有问题，本次不做重构
2. 术语面板与编辑器的布局交互（面板展开时编辑器需自适应宽度）— 使用 flex 布局解决
