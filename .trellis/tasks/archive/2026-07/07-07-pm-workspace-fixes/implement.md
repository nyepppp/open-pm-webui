# PM工作台交互与UI修复 - 执行计划

## 执行顺序

```
Phase 1: 基础修复（导航 + 按钮）
├── Step 1: 修复导航切换无响应
└── Step 2: 修复"添加功能"按钮

Phase 2: 性能优化
├── Step 3: 添加 resize 防抖
├── Step 4: 优化 MindMapCanvas 渲染
└── Step 5: 实现虚拟滚动

Phase 3: UI 增强
├── Step 6: 补充卡片信息（版本、更新时间、溯源）
└── Step 7: 实现添加功能弹窗

Phase 4: 验证
├── Step 8: 性能测试
└── Step 9: 功能测试
```

## Step 1: 修复导航切换无响应

**文件**: `src/routes/(app)/pm/[projectId]/+page.svelte`

**修改**:
1. 检查 `goto` 导入是否正确
2. 在按钮点击事件中添加 `event.preventDefault()`
3. 添加 fallback 导航逻辑

**验证**:
- [ ] 点击模块入口能正确跳转
- [ ] 返回后页面状态正确

## Step 2: 修复"添加功能"按钮

**文件**: 
- `src/lib/components/pm/architecture/ModuleCard.svelte`
- `src/lib/components/pm/architecture/ModuleFeatureManager.svelte`

**修改**:
1. 检查 `onAddFeature` 回调传递链
2. 确保 `ModuleFeatureManager` 正确传递 `onAddFeature` 到 `ModuleCard`
3. 添加弹窗触发逻辑

**验证**:
- [ ] 点击"添加功能"按钮弹出弹窗
- [ ] 弹窗显示当前模块名

## Step 3: 添加 Resize 防抖

**文件**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`

**修改**:
```typescript
// 添加防抖函数
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// 替换原有 resize 监听
$effect(() => {
  const debouncedResize = debounce(() => {
    if (window.innerWidth < 768 && !treeCollapsed) treeCollapsed = true;
  }, 200);
  
  window.addEventListener('resize', debouncedResize);
  return () => window.removeEventListener('resize', debouncedResize);
});
```

**验证**:
- [ ] 快速调整窗口大小不会频繁触发重渲染

## Step 4: 优化 MindMapCanvas 渲染

**文件**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`

**修改**:
1. 移除 `{#key $aggregatedTree}`
2. 使用 `$effect` 监听数据变化并增量更新
3. 添加 `shouldComponentUpdate` 逻辑

**验证**:
- [ ] 数据更新时 Canvas 不重新创建
- [ ] 节点位置正确更新

## Step 5: 实现虚拟滚动

**文件**: 
- `src/lib/components/pm/architecture/ModuleFeatureManager.svelte`
- `src/lib/components/pm/architecture/ModuleCard.svelte` (可选)

**修改**:
1. 计算视口内可见模块
2. 只渲染可见模块 + 缓冲区
3. 监听滚动事件更新渲染范围

**验证**:
- [ ] 100 个模块下滚动流畅
- [ ] 帧率 > 30fps

## Step 6: 补充卡片信息

**文件**: `src/lib/components/pm/architecture/ModuleCard.svelte`

**修改**:
1. 添加版本信息展示
2. 添加更新时间展示
3. 添加溯源入口

**验证**:
- [ ] 卡片显示版本号
- [ ] 卡片显示更新时间
- [ ] 点击溯源入口跳转

## Step 7: 实现添加功能弹窗

**文件**:
- `src/lib/components/pm/architecture/AddFeatureModal.svelte` (NEW)
- `src/lib/components/pm/architecture/ModuleFeatureManager.svelte`

**修改**:
1. 创建弹窗组件（复用 `src/lib/components/common/Modal.svelte`）
2. 弹窗规格：
   - 使用 `size='md'`（宽度 42rem）
   - 遵循项目 Modal 的 focus trap 和 ESC 关闭规范
   - 标题："添加功能 - [模块名]"
3. 实现参数动态添加/删除
4. 参数字段：名称（必填）、类型（选填，默认 string）、描述（选填）、默认值（选填）
5. 集成到 ModuleFeatureManager

**验证**:
- [ ] 弹窗显示正确
- [ ] 弹窗使用项目统一的 Modal 组件
- [ ] 参数可动态添加/删除
- [ ] 提交后功能正确添加

## Step 8: 性能测试

**测试项**:
- [ ] 页面加载时间 < 2s
- [ ] 滚动帧率 > 30fps
- [ ] 内存占用 < 100MB

## Step 9: 功能测试

**测试项**:
- [ ] 导航切换正常
- [ ] 添加功能正常
- [ ] 卡片信息正确
- [ ] 弹窗交互正常

## Rollback Points

| Step | 回滚文件 | 回滚命令 |
|------|----------|----------|
| Step 1 | `+page.svelte` | `git checkout -- src/routes/(app)/pm/[projectId]/+page.svelte` |
| Step 2 | `ModuleCard.svelte`, `ModuleFeatureManager.svelte` | `git checkout -- src/lib/components/pm/architecture/` |
| Step 3-5 | `+page.svelte` | `git checkout -- src/routes/(app)/pm/[projectId]/architecture/+page.svelte` |
| Step 6-7 | `ModuleCard.svelte`, `AddFeatureModal.svelte` | `git checkout -- src/lib/components/pm/architecture/` |

## 验证命令

```bash
# 构建检查
npm run build

# TypeScript 检查
npm run check

# 性能测试（Chrome DevTools）
# 1. 打开 Performance 面板
# 2. 录制滚动操作
# 3. 检查帧率 > 30fps
```
