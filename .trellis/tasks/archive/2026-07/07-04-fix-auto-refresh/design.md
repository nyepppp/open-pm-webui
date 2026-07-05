# Design: 修复页面自动刷新bug

## Architecture

修改集中在 `src/routes/+layout.svelte` 文件，涉及两个核心修复点：

1. **版本检测逻辑** (第160-168行)
2. **Token 过期检查** (第762-779行)

## Data Flow

### 版本检测修复前
```
Socket Connect → 获取 version/deploymentId → 与 store 对比 → 不同则刷新
```

### 版本检测修复后
```
Socket Connect → 获取 version/deploymentId → 检查 store 值是否为 null → 
  ├─ 是 null（首次）：更新 store，不刷新
  └─ 非 null 且不同：注销 SW，刷新页面
```

### Token 过期修复前
```
Timer (15s) → 检查 token 过期 → location.href 跳转
```

### Token 过期修复后
```
Timer (15s) → 检查 token 过期 → goto('/auth') 客户端导航
```

## Compatibility

- 版本检测修复：向后兼容，不改变正常版本更新时的刷新行为
- Token 过期修复：使用 SvelteKit 的 `goto`，需要确保 `goto` 在 `checkTokenExpiry` 的上下文中可用

## Trade-offs

### 方案A（初始化保护）vs 方案B（完全移除自动刷新）

| 方案 | 优点 | 缺点 |
|------|------|------|
| A（初始化保护） | 修复首次加载刷新；保留版本更新自动刷新 | 版本更新时仍可能打断用户工作 |
| B（完全移除） | 用户完全控制刷新时机 | 用户可能使用过时代码，导致不一致 |

选择方案A，因为：
1. 问题报告的是"无故自动刷新"，而非版本更新刷新
2. 首次加载时的刷新是时序问题，修复后不再出现
3. 版本更新时的自动刷新是预期行为，确保用户总是使用最新代码

## Rollback

如果修复导致问题，可以：
1. 回滚 `src/routes/+layout.svelte` 的修改
2. 或者将版本检测逻辑恢复为原来的简单比较

## 测试策略

1. **首次加载测试**：清除缓存后首次访问，确认不自动刷新
2. **版本更新测试**：模拟版本变化，确认仍然自动刷新
3. **Token 过期测试**：模拟 token 过期，确认使用 `goto` 导航而非 `location.href`
4. **长时间保持测试**：保持页面打开5分钟，确认无自动刷新
