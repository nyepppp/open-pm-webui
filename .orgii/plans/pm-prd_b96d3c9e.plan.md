# PM 模块交互修复 & PRD 对齐

## Context

用户反馈了 11 个 Vibe Annotations 问题，核心是当前 PM 模块的交互和 PRD 定义严重不对齐。当前实现把所有模块都做成"条目列表 + 通用富文本编辑"，但 PRD 定义了差异化的交互模式。

PRD 定义的关键交互模式（`docs/prd/PM-Workflow-Platform-PRD-v1.0.md`）：
- **需求管理** → 表格 + 溯源（关联需求-功能-参数-文档）
- **竞品分析** → 竞品对比矩阵（表格+文档），不是富文本
- **产品路线图** → 甘特图/时间轴可视化，不是富文本
- **PRD** → 富文本编辑器 + 章节大纲
- **参数配置** → 参数清单表格 + 来源/所属模块/功能字段
- **测试用例** → 表格 + 溯源（关联需求/参数）
- **会议纪要** → 纪要列表
- **风险分析** → 风险矩阵可视化
- **产品架构** → 思维导图/关系图
- **FAQ** → 问题/答案对应表单，不是富文本
- **验收报告** → 验收检查面板
- **版本管理** → 切换版本、对比、回滚

## 当前问题清单

| # | 页面 | 问题 | PRD 定义 |
|---|------|------|----------|
| 1 | competitor | 新建后应自动进入编辑 | 竞品对比矩阵 |
| 2 | faq | 表单应为问题/描述对应，可溯源 | FAQ 问答对 |
| 3 | 项目工作台 | 版本不支持切换 | version.switch |
| 4 | meeting等 | 需要返回工作台首页/上一页按钮 | 导航栏 |
| 5 | sidebar | 去掉 PM 展开子菜单 | — |
| 6 | parameter | 少了参数来源、所属模块-功能 | moduleId, featureId, sourceDocument |
| 7 | prd | 大纲不支持自动识别文档内容 | — |
| 8 | product-architecture | 应该是思维导图模式 | RelationGraph/MindMap |
| 9 | requirement | 不支持编辑、看不到描述 | 表格+溯源 |
| 10 | roadmap | 不应该是富文本 | 甘特图/时间轴 |
| 11 | testcase | 应该可以溯源 | 关联需求/参数 |

## Approach

### Step 1: 修改模块配置 — 按PRD定义区分交互类型

当前 `moduleConfig` 只有 `rich` 和 `table` 两种。按 PRD 定义，需要增加 `form`、`mindmap`、`gantt` 类型：

```
requirement   → table (保持，但增加描述列和编辑/溯源)
parameter     → table (保持，但增加来源/模块/功能列)
testcase      → table (保持，但增加溯源关联)
prd           → rich (保持)
faq           → form (问题/答案对，非富文本)
competitor    → form (竞品+分析矩阵)
meeting       → rich (会议纪要，保持富文本)
risk          → form (概率/影响/措施)
roadmap       → gantt (甘特图/时间轴，暂降级为表格)
acceptance    → form (验收检查项)
product-architecture → mindmap (思维导图，暂降级为占位)
```

### Step 2: FAQ 模块 — 问题/答案表单

- 新建表单：问题 + 答案 + 受众 + 关联功能（溯源）
- 列表：问题/答案对显示，点击展开编辑
- 不再使用通用富文本编辑器

### Step 3: 竞品分析 — 竞品+矩阵

- 新建表单：竞品名称 + URL + 描述
- 新建后自动进入编辑模式（Annotation #1 要求）
- 编辑视图：竞品信息 + 分析维度矩阵表格

### Step 4: 参数配置 — 补充字段

- 表格增加列：来源(sourceDocument)、所属模块(moduleId)、所属功能(featureId)
- 新建表单增加对应输入项

### Step 5: 需求管理 — 编辑+描述+溯源

- 表格增加描述列（description）
- 行点击可展开编辑
- 溯源：关联需求→功能→参数→文档

### Step 6: 测试用例 — 溯源关联

- 表格增加溯源列：关联需求ID、关联参数ID
- 新建表单增加溯源输入

### Step 7: 产品路线图 — 改为表格（降级实现）

- PRD 定义为甘特图，但当前无甘特图组件
- 降级为表格视图：节点名、类型(milestone/feature/release)、状态、开始/结束日期、依赖
- 后续可替换为甘特图组件

### Step 8: 产品架构 — 占位（降级实现）

- PRD 定义为思维导图，当前无对应组件
- 降级为富文本编辑器 + 提示"后续支持思维导图模式"
- 保留当前富文本编辑功能

### Step 9: 项目工作台 — 版本切换 + 导航

- 版本下拉支持切换：选择版本后刷新当前页面数据
- 模块页面顶栏增加"返回工作台"按钮
- PRD 大纲自动识别：暂不做（需要 AI 能力），保留手动章节

### Step 10: 侧边栏 — 去掉 PM 展开子菜单

- 当前 PM 工作台按钮点击展开子菜单，用户要求去掉
- 改为简单链接，点击直接跳转 `/pm`
- 去掉 `pmNavOpen`/`pmModuleGroups` 等展开逻辑

### Step 11: API 响应状态监控面板

- 在项目 layout 中增加 API 请求状态指示器
- 显示最近的 API 请求/响应状态（loading/success/error）
- 轻量实现：用 toast 或顶栏小状态条

## Key Files

1. **`src/routes/(app)/pm/[projectId]/[module]/+page.svelte`** — 主要改动文件
   - 重构 `moduleConfig`，按 PRD 区分交互类型
   - 为 `form` 类型模块添加专用新建/编辑表单
   - FAQ: 问题/答案表单
   - 竞品: 竞品+矩阵表单，新建后自动进入编辑
   - 参数: 补充来源/模块/功能字段
   - 需求: 增加描述列和编辑能力
   - 测试用例: 增加溯源字段
   - 路线图: 改为表格视图

2. **`src/lib/components/layout/Sidebar.svelte`** — 去掉 PM 展开子菜单
   - 移除 `pmNavOpen`、`pmNavAutoOpened`、`pmModuleGroups`
   - PM 工作台改为简单 `<a href="/pm">` 链接

3. **`src/routes/(app)/pm/[projectId]/+layout.svelte`** — 版本切换 + 导航
   - 版本选择后实际切换数据
   - 添加 API 状态监控指示器

4. **`src/lib/apis/pm/types.ts`** — 补充类型定义
   - FAQ: `question`, `answer`, `audience`, `relatedFeatures`
   - Parameter: `sourceDocument`, `moduleId`, `featureId`
   - Requirement: `description`, `userRole`, `expectedBenefit`
   - Testcase: `requirementId`, `parameterId`

5. **`backend/open_webui/models/pm.py`** — 补充字段（可选，当前 data JSON 字段已足够存储）

## Risks & Open Questions

1. **甘特图和思维导图组件缺失**：PRD 定义 roadmap 为甘特图、product-architecture 为思维导图，但项目当前无对应组件。降级为表格/富文本是临时方案。
2. **溯源关系**：PRD 定义了完整的 Traceability 模块（entities + relations 表），但当前后端只有 pm_entry 表。溯源关联暂存在 entry.data JSON 中，后续需迁移到独立关系表。
3. **版本切换**：PRD 定义了 version.switch + version.snapshotPath，当前后端版本表只有基础字段，切换版本暂只影响显示状态，不实际加载快照数据。
4. **PRD 大纲自动识别**：需要 AI 能力分析文档内容生成大纲，当前先保留手动章节管理。
5. **范围控制**：本计划聚焦于"交互类型对齐 PRD"和"修复用户反馈的 11 个问题"，不涉及 AI 集成、工作流、PRD 检查等高级功能。