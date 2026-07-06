# PM引用功能执行计划

## 执行概览

本任务在 MessageInput.svelte 中集成 PM 数据引用功能，包括添加引用按钮、集成 PM 数据选择器、实现引用插入逻辑。

## 依赖关系

```
B1.1 添加 PM 引用按钮 (MessageInput.svelte)
    ↓
B1.2 集成 PM 数据选择器 (PMDataSelector.svelte)
    ↓
B1.3 实现引用插入逻辑 (引用数据格式 + 展示)
    ↓
B1.4 质量检查和验证
```

## 详细步骤

### B1.1: 在 MessageInput.svelte 的 IntegrationsMenu 旁添加 PM 引用按钮

**目标**: 在聊天输入框的 IntegrationsMenu 按钮旁添加 PM 引用按钮

**文件**: `src/lib/components/chat/MessageInput.svelte`

**具体修改**:
1. 在 script 部分添加状态变量：
   ```typescript
   let showPMDataSelector = false;
   ```

2. 在 IntegrationsMenu 按钮旁（line 1754-1770 区域）添加 PM 引用按钮：
   - 使用 Tooltip 包裹
   - 使用 SVG 图标（文件夹/项目图标）
   - 点击时设置 `showPMDataSelector = true`
   - 仅在 `showPMWorkbenchButton` 为 true 时显示

3. 导入 PMDataSelector 组件（line 107 附近）：
   ```svelte
   import PMDataSelector from '../pm/PMDataSelector.svelte';
   ```

**验证点**:
- [ ] 按钮在 PM Workbench 启用时显示
- [ ] 按钮样式与现有工具按钮一致
- [ ] 点击按钮后 showPMDataSelector 变为 true

---

### B1.2: 创建/集成 PM 数据选择器

**目标**: 在 MessageInput.svelte 中集成 PMDataSelector 组件

**文件**: `src/lib/components/chat/MessageInput.svelte`

**具体修改**:
1. 在 template 部分添加 PMDataSelector 组件（建议在文件底部，form 标签内或外）：
   ```svelte
   <PMDataSelector
     show={showPMDataSelector}
     onSelect={(data) => {
       // 将选中的 PM 数据转换为引用格式
       const pmRef = {
         id: `pm-${data.projectId}-${data.entryId}`,
         name: data.entryTitle,
         type: 'pm-entry',
         status: 'processed',
         url: `/pm/${data.projectId}`,
         data: {
           projectId: data.projectId,
           projectName: data.projectName,
           moduleId: data.moduleId,
           moduleName: data.moduleName,
           entryId: data.entryId,
           entryTitle: data.entryTitle,
           moduleType: data.moduleType,
           status: data.status,
           priority: data.priority,
           content: data.content
         }
       };
       
       // 避免重复添加
       if (!files.find((f) => f.id === pmRef.id)) {
         files = [...files, pmRef];
       }
       
       showPMDataSelector = false;
     }}
     onClose={() => {
       showPMDataSelector = false;
     }}
   />
   ```

**验证点**:
- [ ] PMDataSelector 弹窗正确显示
- [ ] 可以浏览项目 → 模块 → 条目三级结构
- [ ] 选择条目后数据正确返回
- [ ] 弹窗关闭后 showPMDataSelector 变为 false

---

### B1.3: 实现引用插入逻辑

**目标**: 将选中的 PM 数据以引用格式插入到对话上下文

**文件**: `src/lib/components/chat/MessageInput.svelte`

**具体修改**:
1. 修改文件展示区域（lines 1355-1448），确保 `type: 'pm-entry'` 的项能正确展示：
   - 在 `{#each files as file, fileIdx}` 循环中处理 `type === 'pm-entry'`
   - 或者使用现有的 FileItem 组件展示（如果 FileItem 支持）

2. 检查 FileItem 组件是否支持 `type: 'pm-entry'`：
   - 如果不支持，考虑创建 PMReferenceItem 组件
   - 或者在 FileItem 中添加对 pm-entry 的支持

3. 确保引用数据在发送消息时被正确传递：
   - 现有的 `onChange` 回调已经包含 `files` 数组
   - 确保 PM 引用数据在 `files` 数组中

**验证点**:
- [ ] 引用标签显示在输入框上方
- [ ] 标签显示条目标题和项目/模块信息
- [ ] 点击删除按钮可以移除引用
- [ ] 发送消息时引用数据被包含在消息中

---

### B1.4: 质量检查和验证

**验证清单**:
- [ ] **功能验证**:
  - [ ] PM 引用按钮在 PM Workbench 启用时显示
  - [ ] 点击按钮打开 PM 数据选择器
  - [ ] 可以在选择器中浏览项目/模块/条目
  - [ ] 选择条目后引用标签显示在输入框上方
  - [ ] 引用标签显示正确的条目标题
  - [ ] 可以删除引用标签
  - [ ] 发送消息时引用数据被正确传递

- [ ] **UI/UX 验证**:
  - [ ] 按钮样式与现有工具按钮一致
  - [ ] 引用标签样式与文件标签一致
  - [ ] 暗色模式正常显示
  - [ ] 响应式布局正常

- [ ] **兼容性验证**:
  - [ ] 与现有文件上传功能兼容
  - [ ] 与现有工具选择功能兼容
  - [ ] 与 `#` 命令 suggestion 系统兼容
  - [ ] 与消息发送流程兼容

- [ ] **边界情况**:
  - [ ] 重复引用同一条目时只显示一个
  - [ ] 选择器关闭后再次打开状态正确
  - [ ] 无 PM 数据时选择器显示空状态

## 回滚方案

如果需要回滚：
1. 恢复 MessageInput.svelte 到修改前状态
2. 保留 PMDataSelector.svelte（不影响现有功能）
3. 重新构建项目验证

## 风险文件

- `src/lib/components/chat/MessageInput.svelte` - 核心文件，修改需谨慎
- `src/lib/components/pm/PMDataSelector.svelte` - 复用现有组件

## 验证命令

```bash
# 构建前端
npm run build

# 或者开发模式
npm run dev
```

## 完成标准

- [ ] 所有验证点通过
- [ ] 代码审查通过
- [ ] 无新引入的 LSP 错误
- [ ] 功能在本地环境验证通过
