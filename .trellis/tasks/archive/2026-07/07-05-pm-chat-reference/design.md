# PM引用功能技术设计

## 架构概述

在聊天输入框（MessageInput.svelte）中集成 PM 数据引用功能，允许用户通过按钮或 `#` 命令触发 PM 数据选择器，选择后将 PM 数据作为特殊引用插入到对话上下文中。

## 组件边界

```
MessageInput.svelte (主容器)
├── InputMenu (文件上传等)
├── IntegrationsMenu (工具/技能选择)
├── PMDataSelector (新增：PM数据选择器弹窗)
│   ├── 项目列表视图
│   ├── 模块列表视图
│   └── 条目列表视图
└── 引用展示区域 (输入框上方标签)
```

## 数据流

```
用户点击 PM 引用按钮
    ↓
打开 PMDataSelector (showPMDataSelector = true)
    ↓
用户选择项目 → 模块 → 条目
    ↓
PMDataSelector.onSelect() 返回 PM 数据对象
    ↓
MessageInput 将 PM 数据转换为引用格式
    ↓
添加到 files 数组 (type: 'pm-entry')
    ↓
引用标签展示在输入框上方
    ↓
发送消息时，引用数据随消息一起发送
```

## 数据契约

### PM 引用数据结构

```typescript
interface PMReference {
  id: string;           // 唯一标识：pm-{projectId}-{entryId}
  type: 'pm-entry';     // 固定类型
  name: string;          // 显示名称（条目标题）
  status: 'processed';   // 固定状态
  url: string;           // 链接 /pm/{projectId}
  data: {
    projectId: string;
    projectName: string;
    moduleId: string;
    moduleName: string;
    entryId: string;
    entryTitle: string;
    moduleType: string;
    status: string;
    priority?: string;
    content?: string;
  }
}
```

### 与现有系统的兼容性

- PM 引用作为 `files` 数组中的特殊项，与图片、文件等并列
- 使用现有的 `FileItem` 组件展示（已支持 `type: 'pm-entry'`）
- 发送消息时，PM 引用数据会被包含在 `files` 中传递到后端

## 引用格式

当 PM 引用被插入到消息中时，格式如下：

```
[PM引用: {条目标题}]
项目: {项目名称}
模块: {模块名称}
类型: {模块类型}
状态: {状态}
优先级: {优先级}
内容摘要: {内容前200字}
```

## 状态管理

### MessageInput.svelte 新增状态

```typescript
let showPMDataSelector = false;  // 控制选择器显示/隐藏
```

### 引用生命周期

1. **添加引用**：用户选择条目 → 添加到 `files` 数组 → 展示标签
2. **删除引用**：用户点击标签上的删除按钮 → 从 `files` 数组移除
3. **发送消息**：引用数据随 `files` 一起发送
4. **消息展示**：后端/前端展示时解析引用数据

## UI 设计

### 按钮位置

在 IntegrationsMenu 按钮旁添加 PM 引用按钮：

```
[InputMenu] | [IntegrationsMenu] [PM引用按钮] | [工具标签] | [发送按钮]
```

### 按钮样式

- 圆形按钮，与现有工具按钮风格一致
- 图标：文件夹/项目图标（使用现有 SVG 或 FontAwesome）
- Tooltip："引用 PM 数据"

### 引用标签展示

在输入框上方的文件列表区域展示：
- 标签样式：蓝色背景，显示条目标题
- 点击删除：右上角显示 X 按钮
- 信息展示：hover 时显示完整信息

## 与现有代码的集成点

### MessageInput.svelte 修改点

1. **导入 PMDataSelector**（line 107）：
   ```svelte
   import PMDataSelector from '../pm/PMDataSelector.svelte';
   ```

2. **添加状态**（在 script 部分）：
   ```typescript
   let showPMDataSelector = false;
   ```

3. **添加按钮**（IntegrationsMenu 旁，line 1754-1770 区域）：
   - 在 `showPMWorkbenchButton` 条件下添加按钮
   - 点击设置 `showPMDataSelector = true`

4. **添加 PMDataSelector 组件**（在 template 部分）：
   ```svelte
   <PMDataSelector
     show={showPMDataSelector}
     onSelect={(data) => {
       // 将 PM 数据转换为引用格式并添加到 files
     }}
     onClose={() => {
       showPMDataSelector = false;
     }}
   />
   ```

5. **修改文件展示逻辑**（lines 1355-1448）：
   - 确保 `type: 'pm-entry'` 的项能正确展示
   - 可能需要自定义 PM 引用的展示样式

### PMDataSelector.svelte

复用现有组件，无需修改。

## 兼容性考虑

### 与现有 suggestion 系统的兼容性

现有的 `#` 命令 suggestion handler（lines 1049-1067）已经支持 `type === 'pm'`：

```typescript
} else if (type === 'pm') {
  const pmRef = {
    id: `pm-${data.projectId}${data.id ? '-' + data.id : ''}`,
    name: data.name,
    type: data.type === 'pm-project' ? 'pm-project' : 'pm-entry',
    // ...
  };
  files = [...files, pmRef];
}
```

需要确保新的 PM 引用按钮和 `#` 命令生成的引用数据结构一致。

### 与 FileItem 组件的兼容性

检查 `FileItem` 组件是否支持 `type: 'pm-entry'`：
- 如果不支持，需要修改 FileItem 或创建专门的 PMReferenceItem 组件
- 或者复用 FileItem 的 `type: 'file'` 但添加特殊标记

## 风险评估

### 风险1：FileItem 组件不支持 PM 引用
- **影响**：引用无法正常展示
- **缓解**：先检查 FileItem 组件，必要时扩展或创建新组件

### 风险2：消息发送时引用数据丢失
- **影响**：PM 引用无法到达后端
- **缓解**：验证 `files` 数组的传递逻辑，确保引用数据完整传递

### 风险3：与现有 suggestion 系统冲突
- **影响**：`#` 命令和按钮两种方式生成的引用格式不一致
- **缓解**：统一引用数据结构，确保两种方式的兼容性

## 回滚方案

如果出现问题，可以通过以下方式回滚：
1. 移除 PM 引用按钮（恢复 MessageInput.svelte）
2. 保留 PMDataSelector 组件（不影响现有功能）
3. 移除引用展示逻辑（恢复文件展示区域）

## 性能考虑

- PMDataSelector 组件在打开时才加载数据（懒加载）
- 项目/模块/条目数据通过 API 获取，需要处理加载状态
- 引用数据量不大，不会影响消息发送性能
