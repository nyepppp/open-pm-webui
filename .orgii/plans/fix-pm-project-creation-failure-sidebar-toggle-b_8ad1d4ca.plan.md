# Fix: PM 项目创建失败 & 侧边栏 PM 工作台无法收起

## Context

两个 Bug 均位于 PM 模块：

1. **项目创建失败**：点击"创建"按钮后，API 请求 URL 拼接错误，导致 404
2. **PM 工作台按钮无法收起**：在 PM 路由下，点击侧边栏"PM 工作台"按钮后子菜单立即重新展开

## Approach

### Bug 1: 创建项目失败 — API URL 双重前缀

**根因**：`src/lib/apis/pm/index.ts:3` 中 `PM_API_BASE` 定义为 `${WEBUI_API_BASE_URL}/api/v1/pm`，而 `WEBUI_API_BASE_URL` 已经是 `http://localhost:8080/api/v1`（见 `constants.ts:8`）。最终请求 URL 变成 `http://localhost:8080/api/v1/api/v1/pm/projects`，双重 `/api/v1` 导致 404。

**修复**：将 `PM_API_BASE` 改为 `${WEBUI_API_BASE_URL}/pm`（去掉多余的 `/api/v1`）。

### Bug 2: PM 工作台按钮无法收起 — 响应式语句冲突

**根因**：`Sidebar.svelte:134` 有响应式语句 `$: if (isPmRoute && !pmNavOpen) { pmNavOpen = true; }`。当用户在 PM 路由下点击按钮将 `pmNavOpen` 设为 `false` 时，该响应式语句立即触发，将 `pmNavOpen` 重置为 `true`，导致无法收起。

**修复**：移除该响应式语句中的自动展开逻辑。改为在首次进入 PM 路由时自动展开一次（通过追踪"是否已自动展开过"），之后用户的手动收起/展开操作不再被覆盖。具体方案：添加一个 `pmNavAutoOpened` 标记，仅在从未自动展开过且当前在 PM 路由时自动展开一次：

```js
let pmNavAutoOpened = false;
$: if (isPmRoute && !pmNavAutoOpened) { pmNavOpen = true; pmNavAutoOpened = true; }
```

这样用户在 PM 路由下手动收起后，`pmNavAutoOpened` 已经为 `true`，响应式语句不再强制重新展开。

## Key Files

1. **`src/lib/apis/pm/index.ts`** (line 3)
   - 将 `const PM_API_BASE = \`${WEBUI_API_BASE_URL}/api/v1/pm\`` 改为 `const PM_API_BASE = \`${WEBUI_API_BASE_URL}/pm\``

2. **`src/lib/components/layout/Sidebar.svelte`** (lines 82, 134)
   - 在 `let pmNavOpen = false;` 后添加 `let pmNavAutoOpened = false;`
   - 将 `$: if (isPmRoute && !pmNavOpen) { pmNavOpen = true; }` 改为 `$: if (isPmRoute && !pmNavAutoOpened) { pmNavOpen = true; pmNavAutoOpened = true; }`

## Risks & Open Questions

- Bug 1 的修复假设后端 PM API 路径为 `/api/v1/pm/projects`（即 `WEBUI_API_BASE_URL` 提供 `/api/v1`，PM 模块只需追加 `/pm`）。如果后端实际路径不是这样（例如后端使用了自定义路由前缀），需要确认后端实际注册的路由。可通过浏览器 DevTools Network 面板查看失败的请求 URL 来确认。
- Bug 2 的方案在用户从 PM 路由导航到非 PM 路由再返回时，`pmNavAutoOpened` 保持 `true`，不会再次自动展开。这是合理的 UX 行为——用户已经知道在 PM 区域了，不需要每次重复展开。
