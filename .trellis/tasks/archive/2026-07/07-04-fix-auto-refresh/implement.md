# Implementation Plan: 修复页面自动刷新bug

## Ordered Checklist

### 1. 修复版本检测逻辑 (src/routes/+layout.svelte 第160-168行)

**Before:**
```javascript
if (
    ($WEBUI_VERSION !== null && version !== $WEBUI_VERSION) ||
    ($WEBUI_DEPLOYMENT_ID !== null && deploymentId !== $WEBUI_DEPLOYMENT_ID)
) {
    await unregisterServiceWorkers();
    location.href = location.href;
    return;
}
```

**After:**
```javascript
// Only refresh if we already have a version/deploymentId set (not initial load)
const hasVersion = $WEBUI_VERSION !== null && $WEBUI_VERSION !== undefined;
const hasDeploymentId = $WEBUI_DEPLOYMENT_ID !== null && $WEBUI_DEPLOYMENT_ID !== undefined;

if ((hasVersion && version !== $WEBUI_VERSION) ||
    (hasDeploymentId && deploymentId !== $WEBUI_DEPLOYMENT_ID)) {
    await unregisterServiceWorkers();
    location.href = location.href;
    return;
}
```

### 2. 修复 Token 过期跳转 (src/routes/+layout.svelte 第762-779行)

**Before:**
```javascript
const checkTokenExpiry = async () => {
    const exp = $user?.expires_at;
    const now = Math.floor(Date.now() / 1000);

    if (!exp) {
        return;
    }

    if (now >= exp - TOKEN_EXPIRY_BUFFER) {
        const res = await userSignOut();
        user.set(null);
        localStorage.removeItem('token');
        location.href = res?.redirect_url ?? '/auth';
    }
};
```

**After:**
```javascript
const checkTokenExpiry = async () => {
    const exp = $user?.expires_at;
    const now = Math.floor(Date.now() / 1000);

    if (!exp) {
        return;
    }

    if (now >= exp - TOKEN_EXPIRY_BUFFER) {
        const res = await userSignOut();
        user.set(null);
        localStorage.removeItem('token');
        goto(res?.redirect_url ?? '/auth');
    }
};
```

### 3. 验证 `goto` 导入

确认 `goto` 已经在文件顶部导入：
```javascript
import { goto } from '$app/navigation';
```

### 4. 测试验证

- [ ] 首次加载页面，确认不自动刷新
- [ ] 保持页面打开5分钟，确认无自动刷新
- [ ] 模拟 token 过期，确认使用 `goto` 导航

## Validation Commands

```bash
# 启动开发服务器
npm run dev

# 或者构建生产版本
npm run build
```

## Risky Files

- `src/routes/+layout.svelte` - 主布局文件，影响整个应用

## Rollback Points

如果需要回滚，恢复 `src/routes/+layout.svelte` 中的以下修改：
1. 版本检测逻辑（第160-168行）
2. Token 过期跳转逻辑（第762-779行）

## Follow-up Checks

- [ ] 代码审查确认
- [ ] 手动测试通过
- [ ] 无 TypeScript 错误
- [ ] 无 ESLint 警告
