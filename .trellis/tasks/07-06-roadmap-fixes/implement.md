# Implement: 修复 Roadmap 页面 SVG 点击和日程同步功能

## 执行计划

### 步骤 1: 修复 SVG 点击问题
- **文件**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- **行号**: 第 1737 行
- **操作**: 移除 `pointer-events-none` 类
- **验证**: 点击按钮能触发 onclick 事件

### 步骤 2: 优化 syncSingleToCalendar 函数
- **文件**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- **行号**: 第 894-959 行
- **操作**:
  1. 修复数据引用问题（确保检查的是原始 entry.data）
  2. 增强错误处理（所有路径都有 toast 提示）
  3. 添加同步状态视觉反馈

### 步骤 3: 验证
- 构建项目，确保无编译错误
- 测试点击功能

## 详细修改

### 修改 1: SVG 按钮 (第 1737 行)

```diff
- <svg class="size-3.5 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75v7.5a2.25 2.25 0 002.25 2.25h13.5A2.25 2.25 0 0021 26.25v-7.5M3 9h18M3 9l9-6 9 6" /></svg>
+ <svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75v7.5a2.25 2.25 0 002.25 2.25h13.5A2.25 2.25 0 0021 26.25v-7.5M3 9h18M3 9l9-6 9 6" /></svg>
```

### 修改 2: 同步按钮添加状态样式 (第 1736 行)

```diff
- <button class="p-1 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition" title="同步到日程" onclick={() => syncSingleToCalendar(entry)}>
+ <button class="p-1 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition" title={(entry.data?.calendarEventId || entry.metadata?.calendarEventId) ? '已同步到日程' : '同步到日程'} onclick={() => syncSingleToCalendar(entry)}>
```

### 修改 3: syncSingleToCalendar 函数优化 (第 894-959 行)

主要修复：
1. 使用 `entry.data` 直接检查 `calendarEventId`，而不是副本
2. 所有错误路径都有 toast 提示
3. 增强日志记录

## 回滚方案

所有修改都是非破坏性的，可以直接 git revert 回滚。

## 验证命令

```bash
# 构建检查
npm run build

# 或开发服务器
npm run dev
```
