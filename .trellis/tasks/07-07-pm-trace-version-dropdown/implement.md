# PM工作台溯源下拉列表新增版本信息展示 - 执行计划

## 执行步骤

### Step 1: 修改 PMRelationPicker.svelte
- **文件**: `src/lib/components/pm/PMRelationPicker.svelte`
- **修改内容**:
  1. 添加 `getDisplayTitle` 辅助函数
  2. 修改下拉列表项展示（第217-218行）
  3. 修改选中后回显展示（第124行）
- **预计耗时**: 10分钟

### Step 2: 修改 PMDataSelector.svelte
- **文件**: `src/lib/components/pm/PMDataSelector.svelte`
- **修改内容**:
  1. 确认 `Entry` 接口是否有版本字段
  2. 如有，添加版本展示逻辑
  3. 修改条目列表展示（第320-322行）
- **预计耗时**: 10分钟

### Step 3: 修改 PMAnnotationLinkDialog.svelte
- **文件**: `src/lib/components/pm/PMAnnotationLinkDialog.svelte`
- **修改内容**:
  1. 添加版本展示逻辑
  2. 修改条目列表展示（第169行）
- **预计耗时**: 10分钟

### Step 4: 修改 EntityBindingPanel.svelte
- **文件**: `src/lib/components/pm/flowchart/EntityBindingPanel.svelte`
- **修改内容**:
  1. 添加版本展示逻辑
  2. 修改实体列表展示（第124行）
- **预计耗时**: 10分钟

### Step 5: 验证与测试
- **验证内容**:
  1. TypeScript类型检查通过
  2. 各组件渲染正常
  3. 版本号展示格式正确
  4. 无版本号的条目展示正常
  5. 搜索功能不受影响
- **预计耗时**: 15分钟

## 风险与回滚

### 风险点
1. **数据字段缺失**: 某些接口返回的数据可能不包含 `currentVersionNumber` 字段
   - **缓解**: 使用 `item.currentVersionNumber || item.version?.toString()` 进行降级处理

2. **样式冲突**: 版本号添加后可能导致布局变化
   - **缓解**: 使用 `text-xs` 小字号，保持原有布局

### 回滚方案
- 所有修改均为展示层修改，不涉及数据逻辑
- 回滚时只需还原修改的展示文本即可
- 建议保留原始代码注释，便于快速回滚

## 验证命令

```bash
# TypeScript类型检查
npm run check

# 或
npx svelte-check

# 构建测试
npm run build
```

## 完成标准

- [ ] 所有4个组件均已修改
- [ ] TypeScript类型检查通过
- [ ] 版本号展示格式统一
- [ ] 无版本号的条目展示正常
- [ ] 搜索功能正常工作
