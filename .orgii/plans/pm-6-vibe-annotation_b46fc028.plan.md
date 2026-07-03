# PM 模块增强 — 新功能 + 6 项 Vibe Annotation 修复

## Context

当前 PM 模块已有 11 个子模块（prd, requirement, parameter, testcase, risk, competitor, roadmap, meeting, acceptance, faq, product-architecture），但缺少原型/UI 设计稿管理和排期功能。日历系统已有独立页面 `/calendar` 和完整 API（`createCalendarEvent`）。版本页面存在 "Invalid Date" 显示问题。工作台模块卡片上显示了项目级版本号（v1.1），但用户要求移除——版本应该是文档级别的，不是项目级别的。

## Approach

### 一、新功能：原型/UI 设计稿管理模块

1. **在 `ModuleType` 中新增 `prototype` 类型**
2. **在 `moduleConfig` 中添加 prototype 配置**：editorType 为混合模式——支持导入图片/文件包（附件列表）+ 评审结果（富文本）
3. **在工作台 `moduleGroups` 中添加原型模块入口**：放在"设计"分组，位于"产品架构"和"竞品分析"之间
4. **在 `[module]/+page.svelte` 中实现 prototype 视图**：
   - 表格视图：显示名称、类型（图片/文件包/评审记录）、状态、更新时间
   - 创建表单：标题 + 类型选择（image/package/review）+ 文件上传（图片/文件包类型时）+ 富文本编辑（评审记录类型时）
   - 编辑器：图片类型显示预览 + 评审记录类型显示富文本
5. **添加 SVG icon** 用于工作台卡片

### 二、新功能：项目排期模块

1. **在 `ModuleType` 中新增 `schedule` 类型**
2. **在 `moduleConfig` 中添加 schedule 配置**：editorType 为 `table`，包含甘特图视图
3. **在工作台 `moduleGroups` 中添加排期模块入口**：放在"执行"分组
4. **复用现有甘特图逻辑**：schedule 模块使用与 roadmap 相同的甘特图渲染，但字段不同（任务名、负责人、开始/结束日期、进度、里程碑标记）
5. **添加 SVG icon**

### 三、Vibe Annotation 修复

#### Annotation #1 — 日程关联路线图
**路径**: `/calendar` 侧边栏 → "日程 Personal Scheduled Tasks"
**问题**: 产品路线图节点应该可以同步到日程
**方案**: 
- 在 roadmap 模块的表格操作区增加"同步到日程"按钮
- 点击后弹出选择器：选择日程类型（里程碑/功能发布/评审），确认后调用 `createCalendarEvent` API 创建日历事件
- 日历事件标题格式：`{项目名}-{节点名称}-{功能}-{进程状态}`
- 如果路线图节点是时间范围（有 startDate 和 endDate），则创建多天事件（all_day=true, start_at=startDate, end_at=endDate）

#### Annotation #2 — 路线图同步到日程按钮
**路径**: `/pm/{projectId}/roadmap` → 路线图表格头部
**问题**: 需要增加"同步到日程"按钮
**方案**:
- 在路线图表格头部（"创建"按钮旁）增加"📅 同步到日程"按钮
- 点击后打开批量同步面板：列出所有路线图节点，每个节点前有复选框，可选择日程类型
- 确认后批量调用 `createCalendarEvent` 创建事件
- 需要导入 `createCalendarEvent`, `getCalendars` from `$lib/apis/calendar`

#### Annotation #3 — 模块页面 500 错误
**路径**: `/pm/{projectId}` → 点击 PRD 文档等模块卡片
**问题**: 点击模块卡片后页面显示 500
**方案**: 
- 检查 `[module]/+page.svelte` 的 `loadEntries` 函数，确认 API 调用不会因 projectId 或 moduleType 格式问题导致 500
- 添加更好的错误处理：catch 中显示具体错误信息而非空白页面
- 在 `onMount` 中验证 projectId 存在性

#### Annotation #4 — 版本是文档级别，不是项目级别
**路径**: `/pm/{projectId}` → 模块卡片上的 "v1.1" 标签
**问题**: 当前每个模块卡片都显示项目当前版本号（v1.1），但版本应该是文档级别的——每个文档有自己的版本历史，项目不需要显示版本
**方案**:
- 移除模块卡片上的版本号 `<span>`（Annotation #5 的 "v1.1" 标签）
- 移除状态卡片区的"版本"卡片（改为仅保留在版本管理页面入口）
- 版本信息保留在：文档编辑器内（PRD 工具栏的版本选择器）、版本管理页面、路线图节点的版本字段

#### Annotation #5 — 移除所有模块卡片上的 "v1.1" 标签
**路径**: 同 #4
**方案**: 直接移除 `[projectId]/+page.svelte` 中模块卡片描述旁的版本 `<span>`

#### Annotation #6 — 版本页面 "Invalid Date"
**路径**: `/pm/{projectId}/versions`
**问题**: 版本列表显示 "Invalid Date"，看不到版本信息
**方案**:
- 当前代码 `dayjs(v.createdAt / 1_000_000).format(...)` — 如果 `createdAt` 是秒级时间戳（如 Python 的 `time.time()`），除以 1_000_000 会得到极小值导致 Invalid Date
- 修复：检测 `createdAt` 的量级——如果 < 1e12 则为秒级（直接用），如果 < 1e15 则为毫秒级（直接用），否则为微秒级（除以 1_000）
- 同样修复 `sortedVersions` 排序中的时间戳处理

## Key Files

| 文件 | 修改内容 |
|------|----------|
| `src/lib/apis/pm/types.ts` | 新增 `prototype` 和 `schedule` 到 ModuleType；新增 Prototype/Schedule 接口 |
| `src/routes/(app)/pm/[projectId]/+page.svelte` | #4 移除版本卡片；#5 移除模块卡片版本标签；新增 prototype/schedule 模块入口 |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | 新增 prototype/schedule 的 moduleConfig；#2 路线图同步到日程按钮；#3 错误处理改进 |
| `src/routes/(app)/pm/[projectId]/versions/+page.svelte` | #6 修复 Invalid Date 时间戳解析 |
| `src/lib/apis/pm/index.ts` | 无需修改（prototype/schedule 复用现有 entry API） |
| `src/lib/components/layout/Sidebar.svelte` | 无需修改（日历已有独立入口） |

## Risks & Open Questions

1. **日历 API 依赖**：同步到日程需要 `createCalendarEvent` 和 `getCalendars`，需要确认日历功能已启用（`enable_calendar` 配置）。如果未启用，按钮应隐藏或提示。
2. **500 错误根因**：Annotation #3 提到页面 500，可能是后端 API 问题而非前端问题。前端能做的是添加更好的错误处理和降级显示。
3. **prototype 文件上传**：当前 PM entry 模型只有 `content`（字符串）和 `data`（JSON），没有文件附件字段。图片/文件包导入需要：要么使用 OpenWebUI 已有的文件上传 API，要么将文件 URL 存入 `data.attachments`。需要确认文件上传方案。
4. **排期甘特图复用**：schedule 模块的甘特图可以复用 roadmap 的 SVG 渲染逻辑，但字段映射不同。需要在 moduleConfig 中定义字段映射或抽取甘特图为独立组件。
5. **时间戳格式**：Invalid Date 的根因是后端返回的 `createdAt` 格式不确定。需要实际查看 API 返回数据确认是秒级、毫秒级还是微秒级。
