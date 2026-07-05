# 修复页面自动刷新bug

## Goal

修复 GitHub Issue #17 中报告的"页面会自己刷新，影响使用"的问题。用户在使用 PM 工作台时，页面会无故自动刷新，打断工作流程。

## Background

通过代码审查，在 `src/routes/+layout.svelte` 中发现以下可能导致自动刷新的机制：

1. **版本检测自动刷新** (第160-168行)：当 Socket 连接成功后，如果检测到服务器版本或部署ID发生变化，会强制刷新页面 (`location.href = location.href`)
2. **Token 过期检查** (第762-779行)：每15秒检查一次 token 是否过期，过期后重定向到登录页 (`location.href = res?.redirect_url ?? '/auth'`)
3. **触摸下拉刷新** (第894-915行)：在移动设备上，从导航栏下拉会触发页面刷新 (`location.reload()`)

## Requirements

### R1: 修复版本检测导致的自动刷新
- 当 `$WEBUI_VERSION` 或 `$WEBUI_DEPLOYMENT_ID` 为 `null`（首次初始化）时，不触发刷新
- 只在它们已经有值且发生变化时才刷新
- 保留 Service Worker 注销逻辑

### R2: 修复 Token 过期检查导致的页面跳转
- Token 过期时不应使用 `location.href` 强制跳转
- 应使用 SvelteKit 的 `goto` 进行客户端导航
- 保留用户当前的工作状态（如未保存的表单数据）

### R3: 保留必要的刷新功能
- 触摸下拉刷新功能在移动设备上是有意为之，应保留
- 但应限制触发区域，避免误触

## Acceptance Criteria

- [ ] 首次加载时（`$WEBUI_VERSION` 或 `$WEBUI_DEPLOYMENT_ID` 为 `null`）不触发自动刷新
- [ ] 版本变化时（非首次）仍然自动刷新，确保用户总是使用最新代码
- [ ] Token 过期时使用客户端导航 (`goto`) 而非强制页面跳转
- [ ] 页面不再无故自动刷新，用户工作流程不被打断
- [ ] 触摸下拉刷新功能仍然可用，但只在明确的导航区域触发
- [ ] 修复后手动测试确认：保持页面打开5分钟，不应出现自动刷新

## Notes

### 相关代码位置

1. **版本检测刷新** (`src/routes/+layout.svelte` 第160-168行):
```javascript
if (
    ($WEBUI_VERSION !== null && version !== $WEBUI_VERSION) ||
    ($WEBUI_DEPLOYMENT_ID !== null && deploymentId !== $WEBUI_DEPLOYMENT_ID)
) {
    await unregisterServiceWorkers();
    location.href = location.href;  // ← 问题所在
    return;
}
```

2. **Token 过期跳转** (`src/routes/+layout.svelte` 第762-779行):
```javascript
const checkTokenExpiry = async () => {
    // ...
    if (now >= exp - TOKEN_EXPIRY_BUFFER) {
        const res = await userSignOut();
        user.set(null);
        localStorage.removeItem('token');
        location.href = res?.redirect_url ?? '/auth';  // ← 问题所在
    }
};
```

3. **Token 检查定时器** (`src/routes/+layout.svelte` 第1008-1012行):
```javascript
tokenTimer = setInterval(checkTokenExpiry, 15000);  // 每15秒检查
```

### 修复方案（方案A：初始化保护）

- 版本检测逻辑添加初始化保护：如果 `$WEBUI_VERSION === null` 或 `$WEBUI_DEPLOYMENT_ID === null`，说明是首次加载，不触发刷新
- Token 过期：使用 `goto('/auth')` 替代 `location.href`，保留 SPA 体验
- 考虑在刷新前保存用户当前状态（如表单数据、滚动位置等）

## Out of Scope

- 不修改后端 API 行为
- 不修改 Socket.IO 连接逻辑
- 不修改触摸下拉刷新的核心交互（只限制触发区域）
