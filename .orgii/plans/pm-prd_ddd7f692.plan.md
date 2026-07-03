# PM 工作台重构：按 PRD 规范实现

## Context

当前实现与 `docs/prd/PM-Workflow-Platform-PRD-v1.0.md` 的差距：

1. **`/pm` 直接跳转 `/pm/prd`** — 应该是项目工作台首页（项目列表+工作流概览）
2. **模块页面只有简单 CRUD 列表** — 缺少版本管理、溯源、PRD检查、参数提取等核心功能
3. **PRD 页面不是编辑器** — 当前是卡片列表，PRD 应该是富文档编辑器（章节结构、嵌入参数、检查）
4. **版本信息缺失** — 版本切换应占小区域（类似面包屑旁的下拉），不是整行 header
5. **Agent 未打通** — 需要调研 OpenWebUI 的 chat/模型机制后再适配
6. **未打通 OpenWebUI** — 笔记、搜索、工作空间需要集成

## Approach

### Step 1: `/pm` 工作台首页 — 项目列表 + 选择

按 PRD §5.2 路由定义，`/pm` 应显示项目列表页面。

- 改 `pm/+page.svelte`：移除自动跳转，改为项目列表
- 使用 OpenWebUI Notes 风格的卡片列表展示项目
- 每个项目卡片：名称、描述、类型标签、最后更新时间
- 新建项目按钮（弹出简易表单：名称+描述+类型）
- 点击项目进入 `/pm/{projectId}` 工作台

**路由变化**：
- `/pm` → 项目列表页
- `/pm/{projectId}` → 项目工作台（含模块导航）
- `/pm/{projectId}/{module}` → 模块内容页

### Step 2: 项目工作台 `/pm/{projectId}` — 模块导航 + 版本切换

按 PRD §5.1 布局：
- 顶部：项目名 + 版本下拉（小区域，不占整行）+ 设置按钮
- 左侧：已在 OpenWebUI 侧边栏中（已实现）
- 主内容：工作流概览/快捷入口

**版本切换**：
- 在页面顶部标题栏右侧放一个小型版本选择器（下拉按钮，类似面包屑旁的标签）
- 默认显示 `v1.0`，点击展开版本列表
- 不占大区域，不使用全宽 header

### Step 3: 模块页面重构 — 按 PRD 各模块数据模型实现

**核心思路**：不同模块有不同的交互模式，不能全是简单的卡片列表。

| 模块 | PRD 交互模式 | 实现优先级 |
|------|-------------|-----------|
| PRD | 富文档编辑器（章节结构、嵌入参数、检查） | P0 |
| 需求管理 | 表格（优先级、状态、标签） | P0 |
| 参数配置 | 表格（参数名、类型、默认值、来源PRD） | P0 |
| 测试用例 | 表格（场景、步骤、预期结果） | P1 |
| 竞品分析 | 对比矩阵 | P1 |
| 产品路线图 | 甘特图/时间轴 | P2 |
| 风险分析 | 风险矩阵 | P2 |
| 其他 | 简单列表+编辑 | P2 |

**P0 实现细节**：

#### PRD 模块（`/pm/{projectId}/prd`）
- 列表页：PRD 文档卡片列表（同 Notes 风格）
- 点击进入编辑页 `/pm/{projectId}/prd/{docId}`：
  - 左侧：章节大纲（可拖拽排序）
  - 中间：富文本编辑器（PMRichEditor）
  - 右侧：PRD 检查结果面板（可折叠）
  - 顶部：版本号标签 + 保存按钮

#### 需求管理（`/pm/{projectId}/requirement`）
- 表格视图：ID、标题、优先级(P0-P3)、状态、来源、标签
- 支持内联编辑优先级和状态
- 筛选：按优先级、状态、来源

#### 参数配置（`/pm/{projectId}/parameter`）
- 表格视图：参数名、key、类型(input/output/config)、数据类型、默认值、来源PRD
- 支持从 PRD 提取参数（按钮触发 AI 提取，暂用占位）

### Step 4: 版本管理 — 小区域切换

按用户要求"版本等信息占小区域切换"：
- 不使用 PMProjectHeader 全宽 header
- 在模块页面顶部标题栏右侧放置版本标签按钮
- 点击展开版本下拉列表（创建新版本、切换版本、查看版本历史）
- 当前版本高亮显示

### Step 5: Agent 适配性调研（暂不实现）

用户明确说"Agent功能要和其他工具打通，适配性需要调研再进行实现"：
- 调研 OpenWebUI 的 chat 机制（models、Ollama、OpenAI API）
- 调研 OpenWebUI 的 tools/skills 机制
- 产出调研报告，确定 PM Agent 如何与 OpenWebUI 的 AI 能力集成
- 本次不实现 Agent 代码

### Step 6: 打通 OpenWebUI 笔记、搜索、工作空间

- **笔记打通**：PM 文档可导出为 Note（使用 OpenWebUI 的 `createNewNote` API）
- **搜索打通**：PM 条目通过 OpenWebUI 的搜索机制可检索（后续实现，需要后端支持）
- **工作空间打通**：PM 参数清单可导出为 Workspace knowledge base 条目

**最小可行实现**：
- PRD 文档页面添加"导出为笔记"按钮
- 参数清单页面添加"导出到工作空间"按钮

## Key Files

| 文件 | 改动 |
|------|------|
| `src/routes/(app)/pm/+page.svelte` | 项目列表页（替换自动跳转） |
| `src/routes/(app)/pm/+layout.svelte` | 项目工作台布局（含版本选择器） |
| `src/routes/(app)/pm/[module]/+page.svelte` | 重写为按模块类型分派不同视图 |
| `src/routes/(app)/pm/[projectId]/+layout.svelte` | 新增：项目级布局（含版本切换） |
| `src/routes/(app)/pm/[projectId]/+page.svelte` | 新增：项目工作台首页 |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | 新增：模块内容页 |
| `src/lib/components/pm/PMVersionSelector.svelte` | 重构为小型下拉版本选择器 |
| `src/lib/components/pm/PMRichEditor.svelte` | 已修复，待集成到 PRD 编辑器 |
| `src/lib/apis/pm/index.ts` | 扩展 API（关联关系、导出等） |

## Risks & Open Questions

1. **路由重构风险**：从 `/pm/[module]` 改为 `/pm/[projectId]/[module]` 是 breaking change，需要同步更新侧边栏导航链接
2. **后端 API 完整性**：当前后端只有基础的 CRUD API，版本对比、溯源、PRD检查等 API 尚未实现，前端需要先做 UI 框架 + mock 数据
3. **Agent 集成时机**：用户要求先调研再实现，Agent 功能不纳入本次实现范围
4. **表格组件**：OpenWebUI 没有内置的表格组件，需求管理和参数配置需要引入或自建表格组件
