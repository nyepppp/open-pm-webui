# Design: 修复 Roadmap 页面 SVG 点击和日程同步功能

## 变更范围

### 文件
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

### 具体位置
- 第 1736-1738 行：SVG 按钮 `pointer-events-none` 修复
- 第 894-959 行：`syncSingleToCalendar()` 函数优化

## 技术方案

### 1. SVG 点击修复

**问题**: SVG 元素设置了 `pointer-events-none`，阻止了点击事件传播到父级 `<button>`

**修复**: 移除 `pointer-events-none` 类

```diff
- <svg class="size-3.5 text-gray-400 pointer-events-none" ...>
+ <svg class="size-3.5 text-gray-400" ...>
```

### 2. 日程同步功能优化

**当前问题**:
1. 部分错误只打印 console，用户无感知
2. `d` 变量引用的是 `entry.data || entry.metadata`，但后续修改 `d.calendarEventId` 不会生效（因为 `d` 是副本）
3. 同步状态无法直观感知

**修复方案**:

#### 2.1 修复数据引用问题
```typescript
// 当前（有问题）
const d = entry.data || entry.metadata || {};
// ...
if (d.calendarEventId) {  // 这里检查的是副本，不是原始数据

// 修复后
const entryData = entry.data || {};
const d = { ...entryData };  // 创建副本用于读取
```

#### 2.2 增强错误处理
- 所有 API 调用失败都应有 toast 提示
- 添加更详细的错误信息

#### 2.3 同步状态可视化
- 已同步条目：按钮图标变为蓝色
- 未同步条目：保持灰色

## 兼容性

- 无破坏性变更
- 所有改动向后兼容

## 测试计划

1. 点击"同步到日程"按钮，确认弹出日历选择
2. 未登录时点击，确认提示"未登录"
3. 没有日历时点击，确认提示"没有可用日历"
4. 同步成功后，确认按钮变为蓝色
5. 再次点击已同步条目，确认提示是否覆盖
