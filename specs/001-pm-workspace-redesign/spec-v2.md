# Feature Specification: PM 工作台增强 v2 — 版本完善·模块统一·溯源交互·日程打通

**Feature Branch**: `002-pm-enhancement-v2`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: "1.所有功能下的条目需要直接显示对应版本更加直观；2.版本功能需要更完善；版本比较；合并；分支等功能；并嵌入到对应页面里去；3.产品模块的富文本功能需要同步一下，有的功能RPD模块有其他的也需要有，导入文档功能应该是导入文档文本操作而不是导入章节操作；目录应该是直接识别对应文章的目录而不是自己有目录；4.日程功能还是没有和我的产品工作目录打通，需要你这里；5.整体功能框架已经差不多了，需要丰富完善一下信息和接入；6.docs/prd还有很多功能还没有实现；7.看有没有openwebui自带的组件直接往里面塞入的；8.有的模块的甘特图需要同步一下，功能模块要统一；9.思维导图功能在网上找一下开源的组件避免开发过长，还有产品架构那个东西好像；10.溯源功能有点问题。不知道如何关联。能否在溯源界面可以直接关联上的操作，然后点击对应块还能查看详情。连线就可以把数据给调整了"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 条目版本直显 (Priority: P1)

作为产品经理，我希望在任意模块的条目列表/卡片中直接看到每个条目的版本号，无需点进详情。

**Why this priority**: 当前版本号隐藏在条目详情内，列表视图无法快速区分同一文档的不同版本，严重影响多版本并行工作时的辨识效率。

**Acceptance Scenarios**:

1. **Given** 用户打开任意模块条目列表，**When** 页面加载完成，**Then** 每个条目卡片/行显示版本徽章（version 字段）
2. **Given** 条目有多个版本历史，**When** 用户查看列表，**Then** 当前版本徽章为蓝色实心，历史版本为灰色描边
3. **Given** 用户点击版本徽章，**When** 弹出版本历史下拉，**Then** 显示该条目的所有历史版本列表，可快速切换查看

---

### User Story 2 - 版本比较·合并·分支 (Priority: P1)

作为产品经理，我希望在文档编辑页面内直接使用版本比较、合并和分支功能。

**Why this priority**: 当前只有基础的创建/切换/回滚，缺少比较（diff）、合并（merge）和分支（branch），无法支撑版本并行开发场景。

**Acceptance Scenarios**:

1. **Given** 用户在文档编辑页面，**When** 点击"版本比较"按钮，**Then** 在页面内展开左右对比面板，差异部分高亮显示
2. **Given** 用户查看版本比较结果，**When** 点击某处差异，**Then** 可以选择"保留旧版"/"保留新版"/"手动编辑"来处理冲突
3. **Given** 用户在某个版本上，**When** 点击"创建分支"，**Then** 从当前版本创建独立分支，分支内编辑不影响主线
4. **Given** 用户在分支上工作，**When** 点击"合并到主线"，**Then** 系统自动检测冲突并展示合并界面，无冲突则自动合并
5. **Given** 版本比较面板中，**When** 用户查看结构化数据差异，**Then** 以表格形式展示字段级差异

---

### User Story 3 - 富文本统一 & 文档导入 & 自动目录 (Priority: P1)

作为产品经理，我希望所有富文本模块拥有统一编辑能力；导入文档时导入完整文本而非章节；目录自动从标题层级生成。

**Why this priority**: 各模块富文本能力不一致；文档导入按章节不符合直觉；目录手动维护增加不必要工作量。

**Acceptance Scenarios**:

1. **Given** 用户打开任意富文本编辑器模块，**When** 查看工具栏，**Then** 与 PRD 模块完全一致
2. **Given** 用户点击"导入文档"，**When** 上传 .docx/.md 文件，**Then** 完整文本导入编辑器，保留格式
3. **Given** 用户在富文本中使用 H1-H3 标题，**When** 编辑内容，**Then** 侧边目录面板自动从标题生成目录树
4. **Given** 目录已生成，**When** 用户修改标题，**Then** 目录实时更新

---

### User Story 4 - 日程与产品工作目录打通 (Priority: P2)

作为产品经理，我希望 PM 工作台中的排期/里程碑数据能自动同步到 OpenWebUI 日历系统。

**Why this priority**: 排期和里程碑是 PM 日常核心，当前日程系统和 PM 工作完全割裂。

**Acceptance Scenarios**:

1. **Given** 用户在路线图创建里程碑并设置日期，**When** 保存后，**Then** 自动在日历中创建事件
2. **Given** 用户在风险模块设置截止日期，**When** 保存后，**Then** 自动在日历中创建提醒事件
3. **Given** 用户在日历查看 PM 事件，**When** 点击事件，**Then** 跳转到 PM 模块对应条目
4. **Given** 用户在 PM 工作台，**When** 查看侧边栏，**Then** 显示本周日程概览

---

### User Story 5 - 整体功能完善与接入 (Priority: P2)

作为产品经理，我希望各模块表单字段更完整、数据关联更紧密。

**Why this priority**: 框架已搭建，但字段定义不够完整，关联关系未打通。

**Acceptance Scenarios**:

1. **Given** 用户在竞品分析模块，**When** 编辑条目，**Then** 表单包含分析维度表格（维度/我方/竞品/结论）
2. **Given** 用户在 FAQ 模块，**When** 编辑条目，**Then** 答案字段使用富文本编辑器
3. **Given** 用户在任意关联字段，**When** 点击选择器，**Then** 显示当前项目其他模块条目

---

### User Story 6 - PRD 文档未实现功能 (Priority: P2)

作为产品经理，我希望 PRD 文档中定义的功能完整实现，包括 PRD 检查、排期甘特图等。

**Acceptance Scenarios**:

1. **Given** PRD 定义了 6 大类 20+ 模块，**When** 用户查看侧边栏，**Then** 所有模块均可访问
2. **Given** 用户打开 PRD 检查面板，**When** 执行检查，**Then** 按 L1-L4 级别运行检查规则
3. **Given** 用户打开排期模块，**When** 创建任务，**Then** 显示甘特图视图

---

### User Story 7 - 复用 OpenWebUI 自带组件 (Priority: P2)

作为开发者，我希望尽可能复用 OpenWebUI 已有组件。

**Acceptance Scenarios**:

1. **Given** PM 模块需要日历功能，**When** 实现日程集成，**Then** 复用 CalendarView、CalendarEventModal
2. **Given** PM 模块需要文件上传，**When** 实现附件功能，**Then** 复用已有文件上传组件

---

### User Story 8 - 甘特图统一 & 功能模块统一 (Priority: P2)

作为产品经理，我希望所有甘特图模块使用统一组件，功能模块交互模式一致。

**Acceptance Scenarios**:

1. **Given** 用户打开路线图，**When** 切换到时间线视图，**Then** 显示甘特图
2. **Given** 路线图和排期使用同一甘特图组件，**When** 对比交互，**Then** 操作完全一致

---

### User Story 9 - 思维导图开源组件 & 产品架构 (Priority: P2)

作为产品经理，我希望思维导图使用成熟开源组件，产品架构模块可视化展示功能层级。

**Acceptance Scenarios**:

1. **Given** 用户打开路线图思维导图视图，**When** 编辑节点，**Then** 支持增删改、拖拽、折叠展开
2. **Given** 用户打开产品架构模块，**When** 查看默认视图，**Then** 显示功能层级思维导图
3. **Given** 思维导图数据，**When** 切换到富文本视图，**Then** 节点层级转换为标题列表

---

### User Story 10 - 溯源交互增强 (Priority: P1)

作为产品经理，我希望在溯源关系图中直接通过连线创建关联，点击节点查看详情并编辑。

**Why this priority**: 当前溯源图只读，关联只能通过表单创建，工作流断裂。连线即创建关联是直觉操作。

**Acceptance Scenarios**:

1. **Given** 用户在溯源关系图，**When** 从节点 A 拖拽连线到节点 B，**Then** 弹出关系类型选择器，选择后创建关联
2. **Given** 用户在溯源关系图，**When** 单击节点，**Then** 右侧弹出详情面板可查看和编辑
3. **Given** 用户在溯源关系图，**When** 右键连线，**Then** 弹出菜单：修改关系类型、删除、影响分析
4. **Given** 用户在溯源关系图，**When** 双击节点，**Then** 跳转到条目所在模块编辑页面
5. **Given** 用户在溯源图创建关联，**When** 切换到模块表单，**Then** 关联字段已自动更新

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 所有模块条目列表 MUST 显示版本徽章，当前版本蓝色实心、历史版本灰色描边
- **FR-002**: 版本徽章 MUST 支持点击展开版本历史下拉
- **FR-003**: 文档编辑页面 MUST 内嵌版本比较面板（左右对比视图）
- **FR-004**: 版本比较 MUST 支持结构化数据的字段级差异展示
- **FR-005**: 系统 MUST 支持版本分支创建
- **FR-006**: 系统 MUST 支持分支合并回主线，自动检测冲突
- **FR-007**: 所有富文本模块 MUST 拥有与 PRD 一致的工具栏和功能
- **FR-008**: 文档导入 MUST 导入完整文本（.docx/.md/.txt），非章节拆分
- **FR-009**: 富文本编辑器 MUST 支持自动目录生成（从 H1-H6 标题）
- **FR-010**: 目录 MUST 实时更新
- **FR-011**: 路线图/排期里程碑 MUST 自动同步到 OpenWebUI 日历
- **FR-012**: 风险截止日期 MUST 自动同步到日历
- **FR-013**: 日历 PM 事件 MUST 支持点击跳转回 PM 模块
- **FR-014**: PM 工作台 MUST 显示日程概览
- **FR-015**: 各模块表单字段 MUST 对照 PRD 补全
- **FR-016**: 竞品分析 MUST 增加分析维度表格
- **FR-017**: FAQ 答案 MUST 使用富文本编辑器
- **FR-018**: MUST 复用 OpenWebUI 日历组件和文件上传组件
- **FR-019**: 路线图和排期 MUST 使用统一甘特图组件（frappe-gantt）
- **FR-020**: 甘特图 MUST 支持拖拽、缩放、依赖关系
- **FR-021**: 思维导图 MUST 使用成熟开源组件（mind-elixir）
- **FR-022**: 产品架构 MUST 支持思维导图视图
- **FR-023**: 溯源图 MUST 支持拖拽连线创建关联
- **FR-024**: 溯源图单击节点 MUST 弹出详情面板
- **FR-025**: 溯源图右键连线 MUST 弹出上下文菜单
- **FR-026**: 溯源图双击节点 MUST 跳转模块编辑页
- **FR-027**: 溯源连线创建关联后表单 MUST 自动更新

### Key Entities

- **EntryVersion**: 条目级版本 — entryId, versionNumber, content, metadata, createdAt, createdBy, parentId, branchName
- **VersionBranch**: 版本分支 — id, projectId, name, sourceVersionId, status, createdAt
- **VersionMerge**: 合并记录 — id, branchId, targetVersionId, conflicts, status, mergedAt
- **ScheduleSync**: 日程同步 — id, pmEntityType, pmEntityId, calendarEventId, syncStatus, lastSyncedAt
- **TraceLink**: 溯源连线 — sourceEntityId, targetEntityId, relationType, confidence, confirmed

---

## Success Criteria *(mandatory)*

- **SC-001**: 100% 模块条目列表显示版本徽章
- **SC-002**: 版本比较支持 5 种内容类型结构化 diff
- **SC-003**: 分支创建和合并 3 秒内完成
- **SC-004**: 所有富文本模块工具栏与 PRD 差异为 0
- **SC-005**: .docx 导入格式保留率 ≥ 85%
- **SC-006**: 目录同步延迟 ≤ 500ms
- **SC-007**: PM-日历双向同步成功率 ≥ 99%
- **SC-008**: 50+ 任务甘特图渲染 ≤ 1 秒
- **SC-009**: 思维导图操作响应 ≤ 200ms
- **SC-010**: 溯源连线创建关联 2 秒内完成
- **SC-011**: 节点详情面板加载 ≤ 500ms

---

## Assumptions

- frappe-gantt 已安装，可直接用于甘特图
- @xyflow/svelte 保留用于溯源关系图，思维导图引入 mind-elixir
- OpenWebUI 日历系统可复用（CalendarView、CalendarEventModal、后端 API）
- mammoth 已安装，可用于 .docx 解析
- 版本模型为条目级版本（per-entry）

---

## Clarifications

### Session 2026-06-29

- **Q1**: 版本粒度 → **A**: 条目级版本（per-entry），版本徽章显示该条目当前版本号
- **Q2**: 思维导图库 → **A**: 引入 mind-elixir（MIT、vanilla JS、拖拽/折叠/主题/导出），@xyflow/svelte 保留用于溯源图
- **Q3**: 甘特图 → **A**: 使用 frappe-gantt 封装 PMGanttChart.svelte 共享组件
- **Q4**: 日程集成 → **A**: 复用 OpenWebUI 日历 API，data 字段存储 PM 关联信息
- **Q5**: 文档导入 → **A**: .docx 用 mammoth→HTML→TipTap；.md 用 marked 解析；整篇注入非章节拆分
- **Q6**: 目录生成 → **A**: 监听 TipTap update 事件提取 headings 构建 PMTableOfContents.svelte
