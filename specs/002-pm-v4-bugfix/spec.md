# Feature Specification: PM v4 Bug 修复 & 体验优化

**Feature Branch**: `002-pm-v4-bugfix`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User feedback from Vibe annotations (18 items) + verbal report: rich text editors blank/can't type; import page no content; version badges should be read-only creation-version only (not inline version management); project data isolation broken (sees other project data); compare button non-responsive; parameter module needs Module→Feature→Parameter cascade; product-architecture should show mindmap; prototype module broken; roadmap "今天" marker misaligned; schedule "新建" form fields mismatch; style issues across filter bar, status badges, version badges.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 富文本编辑器可编辑 (Priority: P0)

作为产品经理，我希望在 PRD 文档、竞品分析等模块中可以正常输入和编辑富文本内容，而不是空白无法输入。

**Why this priority**: 编辑器是所有文档模块的核心，无法输入意味着整个模块功能不可用。

**Independent Test**: 打开任意项目的 PRD 文档，新建或点击已有条目，验证富文本编辑器可以正常输入、格式化、保存。

**Acceptance Scenarios**:

1. **Given** 用户打开 PRD 模块，**When** 新建一个文档条目，**Then** 富文本编辑器加载并可正常输入文字
2. **Given** 用户点击已有 PRD 文档条目，**When** 编辑器加载完成，**Then** 原有内容正确显示且可继续编辑
3. **Given** 用户在编辑器中输入内容，**When** 等待自动保存或手动保存，**Then** 内容正确保存到后端
4. **Given** 用户导入 Word 文档，**When** 导入完成后，**Then** 内容在编辑器中正确渲染显示

---

### User Story 2 - 版本徽章只读显示创建版本 (Priority: P0)

作为产品经理，我希望条目列表中的版本徽章仅显示该条目是在哪个版本创建的（只读），而不是可点击的版本管理入口。

**Why this priority**: 用户明确说"我不需要在这个行管理版本 我只用看我是哪个版本创建的这个就行"。

**溯源**: Vibe annotation #3 "这个应该是外面的版本，更改一下 且不可编辑"; 用户口述确认

**Independent Test**: 打开任意模块的表格/卡片视图，验证版本列显示为只读文本标签而非可点击按钮。

**Acceptance Scenarios**:

1. **Given** 用户查看条目列表，**When** 查看版本列，**Then** 版本显示为只读文本标签（如 `v1.0`），不可点击
2. **Given** 条目有版本信息，**When** 显示版本标签，**Then** 标签样式为蓝色小标签，与状态标签风格一致
3. **Given** 条目无版本信息，**When** 显示版本列，**Then** 显示为 "-"

---

### User Story 3 - 项目数据隔离 (Priority: P0)

作为产品经理，我希望每个项目的数据完全隔离，切换项目时不会看到其他项目的条目或版本数据。

**Why this priority**: 数据泄露是核心数据正确性问题。

**溯源**: Vibe annotation #2 "好像没有和其他项目做 隔离 刚刚新建项目发现有其他项目数据"

**根因**: `versionStore.ts` 使用全局 Svelte writable store，切换项目时不清空

**Independent Test**: 创建两个项目，在项目 A 添加条目，切换到项目 B 验证看不到项目 A 的数据。

**Acceptance Scenarios**:

1. **Given** 用户在项目 A 添加了条目，**When** 切换到项目 B，**Then** 项目 B 不显示项目 A 的条目
2. **Given** 用户在项目 A 创建了版本，**When** 切换到项目 B，**Then** 版本筛选只显示项目 B 的版本
3. **Given** 用户切换项目，**When** 模块页面加载，**Then** 全局 versionStore 清空并重新加载

---

### User Story 4 - 版本比较功能可用 (Priority: P1)

作为产品经理，我希望点击"比较"按钮后可以选择两个版本，左右并排展示内容差异（红绿 diff）。

**溯源**: Vibe annotation #5 "点击无响应，应该可以选择内容，然后左右展示更迭内容"

**Independent Test**: 打开有版本历史的条目，点击"比较"按钮，验证并排差异展示。

**Acceptance Scenarios**:

1. **Given** 用户点击"比较"按钮，**When** 面板展开，**Then** 显示版本选择器
2. **Given** 用户选择了两个版本，**When** 差异计算完成，**Then** 左右并排展示，红绿 diff
3. **Given** 比较面板已打开，**When** 用户滚动左侧，**Then** 右侧同步滚动

---

### User Story 5 - 参数配置模块级联结构 (Priority: P1)

作为产品经理，我希望参数配置模块采用"模块→功能→参数"三级级联结构。

**溯源**: Vibe annotation #6 #7 — "应该是模块-功能-参数。模块应该是首要的，且可以选择已有模块/功能"

**Independent Test**: 新建参数时先选模块再选功能再填参数。

**Acceptance Scenarios**:

1. **Given** 用户新建参数条目，**When** 查看录入表单，**Then** 有"所属模块"下拉（可选择已有模块）
2. **Given** 用户选择了模块，**When** 查看"所属功能"下拉，**Then** 仅显示该模块下的功能
3. **Given** 参数列表展示，**When** 查看表格，**Then** 按"模块 > 功能"分组展示

---

### User Story 6 - 产品架构模块显示思维导图 (Priority: P1)

**溯源**: Vibe annotation #8 — "这个应该是看思维导图，项目-模块（版本号）-功能（版本号）支持多版本"

**Independent Test**: 打开产品架构模块，验证显示思维导图。

**Acceptance Scenarios**:

1. **Given** 用户打开产品架构模块，**When** 页面加载完成，**Then** 显示思维导图视图
2. **Given** 思维导图已显示，**When** 点击节点，**Then** 可展开编辑内容

---

### User Story 7 - 原型模块功能可用 (Priority: P1)

**溯源**: Vibe annotation #9 — "这个不行，功能用不了"

**Independent Test**: 打开原型模块，新建条目，验证可添加描述和查看。

**Acceptance Scenarios**:

1. **Given** 用户打开原型模块，**When** 点击新建，**Then** 显示录入表单（名称、类型、描述）
2. **Given** 用户创建条目，**When** 点击条目，**Then** 可查看和编辑详情

---

### User Story 8 - 路线图"今天"标记对齐 (Priority: P2)

**溯源**: Vibe annotation #15 — "这个没有和今天时间对应上"

**Independent Test**: 打开路线图甘特图，验证"今天"标记位置。

**Acceptance Scenarios**:

1. **Given** 甘特图视图已打开，**When** 查看时间轴，**Then** "今天"红色竖线在当前日期位置

---

### User Story 9 - 排期新建表单与列对应 (Priority: P2)

**溯源**: Vibe annotation #16 — "怎么新增表单和列不对应，需要新增内容"

**Independent Test**: 打开排期模块新建，验证表单包含所有表格列字段。

**Acceptance Scenarios**:

1. **Given** 用户点击排期"新建"，**When** 查看表单，**Then** 包含：任务名称、负责人、开始/结束日期、进度、里程碑、优先级、状态

---

### User Story 10 - 样式优化 (Priority: P2)

**溯源**: Vibe annotation #10 #11 #12 — "样式都要调整一下"

**Independent Test**: 打开需求管理模块，检查筛选栏、标签样式。

**Acceptance Scenarios**:

1. **Given** 用户查看需求管理列表，**When** 查看筛选栏，**Then** 筛选项排列整齐，样式统一
2. **Given** 用户查看表格行，**When** 查看标签，**Then** 大小、圆角、内边距统一

---

### User Story 11 - 日程同步到 OpenWebUI (Priority: P2)

**溯源**: Vibe annotation #14 — "同步不了openwebui的日程里面去"

**Independent Test**: 路线图节点点击同步，验证事件出现在日程中。

**Acceptance Scenarios**:

1. **Given** 路线图节点有日期，**When** 点击同步，**Then** 创建日程事件

---

### Edge Cases

- PRD 内容为空时编辑器显示 placeholder
- 版本号为空时只读标签显示 "-"
- 项目切换时有未保存内容应提示
- 日程同步重复点击的处理

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: PMRichEditor MUST 正确加载 TipTap 并允许输入（修复空白问题）
- **FR-002**: 条目列表版本徽章 MUST 为只读文本标签，显示创建版本号
- **FR-003**: 项目切换 MUST 清空 versionStore 并重新加载
- **FR-004**: loadEntries MUST 仅加载当前 projectId 条目
- **FR-005**: 版本比较按钮 MUST 可点击展开差异面板
- **FR-006**: 参数模块 MUST 支持模块→功能→参数级联
- **FR-007**: 产品架构 MUST 默认显示思维导图
- **FR-008**: 原型模块 MUST 支持新建/编辑/查看
- **FR-009**: 路线图"今天"标记 MUST 与当前日期对齐
- **FR-010**: 排期新建表单 MUST 与表格列完全对应
- **FR-011**: 标签样式 MUST 统一
- **FR-012**: 路线图/排期 MUST 支持同步到 OpenWebUI 日程
- **FR-013**: 文档导入内容 MUST 在编辑器中正确渲染

### Key Entities

- **Entry**: 增加 `createdVersionNumber` 字段
- **Parameter Entry**: data 中 `moduleName` + `featureName` 构成级联

---

## Success Criteria

- **SC-001**: 所有富文本编辑器可正常输入、编辑、保存
- **SC-002**: 版本徽章为只读标签，无下拉交互
- **SC-003**: 切换项目后数据完全隔离
- **SC-004**: 版本比较面板正常显示红绿 diff
- **SC-005**: 参数模块支持三级级联
- **SC-006**: 产品架构显示思维导图
- **SC-007**: 路线图"今天"标记位置正确
- **SC-008**: 排期新建表单包含所有字段

---

## Assumptions

- TipTap 空白可能与 Svelte 5 + TipTap 时序有关
- 版本徽章从可交互改为只读，移除 PMVersionHistoryDropdown 在列表中的使用
- 参数级联数据来源于已有条目聚合
- 产品架构复用 PMMindMap 组件
- 日程同步复用 `createCalendarEvent` API
