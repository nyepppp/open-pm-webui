# Feature Specification: PM 工作台重构 — 模块化布局与差异化编辑器

**Feature Branch**: `001-pm-workspace-redesign`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "1.当前可以看见一些需求了。但是所有功能都是和PRD一模一样的。并且布局没有根据分类进行区分。 2.请如果是文本类的都是富文本编辑框；如果是表单，则使用表单进行设计，如果是思维导图.. 3.严格按照需求文档进行设计。 4.当前布局很怪异。可以在侧边栏以功能模块为菜单，小功能则放在子菜单。数据互通。 5.版本、项目控制可以放在侧边栏控制全部内容，版本。 6.Agent逻辑设计比较简单，可以先思考一下如何做的更好 再进行实施"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 侧边栏分类导航 (Priority: P1)

作为产品经理，我希望通过左侧边栏按业务分类浏览所有功能模块，而不是平铺的10个标签页。

**Why this priority**: 当前所有10个模块平铺为标签页，布局混乱，无法体现业务分类逻辑。分类导航是重构的基础，直接影响后续所有模块的可用性。

**Independent Test**: 打开PM工作台页面，侧边栏应显示4大分类（规划/设计/执行/复盘），点击分类可展开/折叠子菜单，选中模块后主区域显示对应编辑器。

**Acceptance Scenarios**:

1. **Given** 用户进入PM工作台，**When** 页面加载完成，**Then** 左侧显示分类侧边栏，包含：规划类（PRD文档、需求池、竞品分析、路线图）、设计类（参数清单、测试用例）、执行类（风险问题、会议纪要）、复盘类（验收复盘、FAQ/培训）
2. **Given** 用户点击"规划类"分类，**When** 分类展开，**Then** 显示PRD文档、需求池、竞品分析、路线图4个子菜单项
3. **Given** 用户点击"PRD文档"子菜单，**When** 选中该模块，**Then** 主区域显示PRD富文本编辑器，侧边栏高亮当前选中项

---

### User Story 2 - 差异化表单与编辑器 (Priority: P1)

作为产品经理，我希望不同模块使用适合其业务特性的编辑器：PRD等文档类使用富文本编辑器，参数清单等数据类使用结构化表单。

**Why this priority**: 当前所有模块共用同一个表单（标题+优先级+文本内容），没有区分各模块的业务特性，导致数据录入体验差、无法做结构化分析。

**Independent Test**: 分别打开PRD文档、参数清单、风险问题三个模块，验证各自使用不同的编辑器类型和字段结构。

**Acceptance Scenarios**:

1. **Given** 用户打开"PRD文档"模块，**When** 创建新条目，**Then** 表单包含：标题、版本、状态（下拉）、富文本内容区、附件上传区
2. **Given** 用户打开"参数清单"模块，**When** 创建新条目，**Then** 表单包含：模块、功能、字段名、类型（下拉：string/number/boolean/object/array）、必填（开关）、默认值、枚举值、说明、来源PRD（关联选择）
3. **Given** 用户打开"风险问题"模块，**When** 创建新条目，**Then** 表单包含：标题、风险等级（下拉）、概率（滑块/百分比）、影响范围、负责人、应对方案、截止时间、富文本描述区

---

### User Story 3 - 项目头部信息栏与版本控制 (Priority: P1)

作为产品经理，我希望在页面顶部看到当前项目信息和版本切换器，方便在不同版本间切换工作。

**Why this priority**: 当前缺少项目上下文展示，用户不知道自己正在编辑哪个项目的哪个版本。版本切换是版本快照与对比功能的前提。

**Independent Test**: 打开任意模块，顶部显示项目名称、当前版本号、版本切换下拉框；切换版本后，所有模块数据自动刷新到新版本。

**Acceptance Scenarios**:

1. **Given** 用户进入PM工作台，**When** 页面加载，**Then** 顶部信息栏显示：项目名称、当前版本（如 v1.2）、版本切换下拉框
2. **Given** 用户点击版本切换下拉框，**When** 选择另一个版本，**Then** 主区域数据自动刷新为该版本内容，侧边栏保持当前选中模块不变
3. **Given** 用户切换版本后，**When** 在不同模块间导航，**Then** 所有模块均显示新版本的数据

---

### User Story 4 - 数据互通与追溯 (Priority: P2)

作为产品经理，我希望在不同模块间建立关联关系，例如参数清单可以关联到PRD文档的某个章节。

**Why this priority**: 产品管理的核心价值之一是追溯能力——需求从哪里来、参数对应哪个PRD章节、测试用例验证哪个需求。数据互通是实现追溯的基础。

**Independent Test**: 在参数清单中创建条目时，可以选择关联到已有的PRD文档；在PRD文档中查看时，能看到关联的参数清单条目。

**Acceptance Scenarios**:

1. **Given** 用户在"参数清单"模块创建条目，**When** 填写"来源PRD"字段，**Then** 下拉框显示当前项目中所有PRD文档列表，选中后建立关联
2. **Given** 用户在"测试用例"模块创建条目，**When** 填写"关联需求"字段，**Then** 下拉框显示当前项目中所有需求池条目
3. **Given** 用户在"PRD文档"模块查看某章节，**When** 查看关联信息，**Then** 显示该章节被哪些参数、测试用例引用

---

### User Story 5 - Agent 智能辅助升级 (Priority: P3)

作为产品经理，我希望 AI Agent 能基于当前模块内容智能生成建议，而不仅仅是生成提示词。

**Why this priority**: 当前Agent逻辑简单，只是生成提示词。升级后Agent应能理解上下文、分析内容、提供 actionable 建议。

**Independent Test**: 在PRD文档中编写内容后，Agent能分析PRD完整性并给出改进建议；在风险模块中，Agent能基于已有内容识别潜在风险。

**Acceptance Scenarios**:

1. **Given** 用户在PRD文档模块编写了一段内容，**When** 触发Agent分析，**Then** Agent返回：缺失的章节、逻辑不完整的部分、可补充的细节建议
2. **Given** 用户在风险问题模块已有几条风险记录，**When** 触发Agent分析，**Then** Agent基于历史数据和当前项目上下文，识别可能被遗漏的风险点
3. **Given** 用户在需求池模块，**When** 触发Agent分析，**Then** Agent建议需求与测试用例的自动关联，并提示用户确认

---

### Edge Cases

- What happens when a module has no entries yet? → Show empty state with a "Create First Entry" button
- What happens when switching versions while editing unsaved changes? → Prompt user to save or discard
- What happens when a referenced PRD is deleted? → Show "[已删除的PRD]" with option to re-link or keep as-is
- What happens when the rich text editor fails to load? → Fall back to plain text textarea with a warning
- What happens when there are 100+ versions? → Version dropdown supports search/filter

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 支持左侧分类侧边栏，将10个模块按4大业务分类组织（规划/设计/执行/复盘）
- **FR-002**: 系统 MUST 支持侧边栏分类的展开/折叠交互
- **FR-003**: 系统 MUST 支持点击子菜单切换主区域编辑器，URL同步更新
- **FR-004**: PRD文档、竞品分析、路线图、会议纪要、验收复盘、FAQ/培训模块 MUST 使用富文本编辑器
- **FR-005**: 需求池、参数清单、测试用例模块 MUST 使用结构化表单
- **FR-006**: 风险问题模块 MUST 使用富文本+表单混合编辑器
- **FR-007**: 每个模块的表单字段 MUST 根据PRD文档中的字段设计实现差异化
- **FR-008**: 系统 MUST 在顶部显示项目信息栏：项目名称、当前版本、版本切换器
- **FR-009**: 版本切换 MUST 同步刷新所有模块数据，保持当前选中模块不变
- **FR-010**: 系统 MUST 支持模块间的数据关联（如参数清单关联PRD文档）
- **FR-011**: 系统 MUST 在关联字段中提供下拉选择器，显示可关联的目标模块条目
- **FR-012**: Agent MUST 能基于当前模块内容进行分析并给出建议
- **FR-013**: Agent 生成的建议 MUST 标记为"待确认"状态，需用户确认后才生效
- **FR-014**: Agent 分析 MUST 支持手动触发（每个模块提供"AI分析"按钮）和自动触发（保存后自动分析、可配置定时分析）两种模式
- **FR-015**: 系统 MUST 兼容现有 `{text: string}` 格式的旧数据
- **FR-016**: 系统 MUST 支持新字段的默认值填充，确保旧数据在新表单中正常显示
- **FR-017**: 路线图模块 MUST 支持思维导图视图，展示产品路线、里程碑、关键需求的层级关系
- **FR-018**: 思维导图 MUST 支持节点的增删改、拖拽调整、折叠展开
- **FR-019**: 思维导图数据 MUST 可与富文本编辑模式双向同步，用户可自由切换视图
- **FR-020**: 新增"产品架构"思维导图模块，用于梳理产品功能架构、模块依赖关系
- **FR-021**: 产品架构思维导图 MUST 支持从现有模块（PRD、参数、需求）自动提取节点数据

### Key Entities *(include if feature involves data)*

- **Project**: 项目根实体，包含名称、描述、类型、状态等
- **Version**: 版本快照，包含版本号、标签、描述、快照路径
- **ModuleEntry**: 模块条目基类，包含id、projectId、moduleType、title、content、metadata、versionId
- **Relation**: 实体关联，包含entityAId、entityBId、relationType、confidence、confirmed
- **PRDDocument**: PRD文档条目，继承ModuleEntry，额外包含sections、status、template
- **Parameter**: 参数清单条目，继承ModuleEntry，额外包含key、moduleId、featureId、paramType、dataType、required、defaultValue
- **Testcase**: 测试用例条目，继承ModuleEntry，额外包含scenario、precondition、steps、expectedResult、caseType
- **Risk**: 风险问题条目，继承ModuleEntry，额外包含probability、impactScope、owner、measures、deadline
- **MindMapNode**: 思维导图节点，包含id、projectId、parentId、label、type（"root"|"branch"|"leaf"）、position、metadata、moduleRef（关联到具体模块条目）

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可以在3秒内通过侧边栏导航到任意模块（从打开页面到模块内容显示）
- **SC-002**: 10个模块中至少8个模块拥有差异化的表单字段（非统一的标题+优先级+文本）
- **SC-003**: 版本切换后，所有模块数据在1秒内刷新完成
- **SC-004**: 模块间关联建立的成功率 ≥ 95%（关联字段正确显示可选目标）
- **SC-005**: Agent建议的采纳率 ≥ 60%（用户觉得建议有价值并采纳）
- **SC-006**: 旧数据迁移后，100%的旧条目在新表单中可正常显示和编辑
- **SC-007**: 用户在PM工作台的平均任务完成时间比旧版本减少 ≥ 30%
- **SC-008**: 思维导图节点操作响应时间 ≤ 200ms（增删改、拖拽、折叠展开）
- **SC-009**: 产品架构思维导图的自动提取准确率 ≥ 80%（从PRD/参数/需求中提取的节点与人工标注一致）

---

## Assumptions

- Open WebUI 已提供或可以集成富文本编辑器（如 TipTap、Quill 等）
- 后端 API 可以扩展以支持新的差异化字段（优先前端兼容处理）
- 用户接受在重构期间可能出现短暂的数据格式转换期
- 侧边栏分类逻辑固定为4大类，不开放用户自定义分类
- Agent 智能分析基于 OpenAI/Claude API，用户已配置 API Key

---

## 思维导图设计决策

**决策**: 采用 B + C 方案

### 方案B：路线图模块思维导图视图

- 路线图模块默认以思维导图形式展示产品路线、里程碑、关键需求的层级关系
- 思维导图支持节点的增删改、拖拽调整、折叠展开
- 思维导图数据可与富文本编辑模式双向同步，用户可自由切换视图
- 节点类型：根节点（产品目标）→ 分支节点（里程碑）→ 叶子节点（关键需求/功能点）

### 方案C：新增"产品架构"思维导图模块

- 新增独立的"产品架构"模块，归类到"规划类"下
- 用于梳理产品功能架构、模块依赖关系、技术栈选型等
- 支持从现有模块（PRD、参数、需求）自动提取节点数据
- 节点类型：根节点（产品）→ 模块节点（功能模块）→ 功能节点（具体功能点）→ 依赖节点（技术依赖/外部服务）

### 思维导图通用能力

- 支持多种布局模式：层级树状、径向、自由布局
- 支持节点样式自定义：颜色、图标、进度条
- 支持导出为图片/PDF/Markdown
- 支持多人协作编辑（未来扩展）

---

## Clarifications

### Session 2026-06-28

- **Q1**: Agent 建议的触发方式 → **A**: 手动触发为主，自动触发为辅（Option B）
  - 每个模块提供"AI分析"按钮供手动触发
  - 支持自动触发模式：保存后自动分析、可配置定时分析
  - 自动触发模式默认关闭，用户可在设置中开启
  - 符合 Constitution "AI-Assisted, Human-Confirmed" 原则：用户始终掌控何时接收AI建议

- **Q2**: 并发编辑冲突处理 → **A**: 乐观锁（版本号/时间戳），最后写入优先 + 冲突提示（Option A）
  - 每个 ModuleEntry 条目 MUST 包含 `version` 字段（整数，每次保存递增）和 `updatedAt` 时间戳
  - 保存时前端 MUST 携带当前条目的 `version`，后端检测是否匹配
  - 版本不匹配时，后端 MUST 返回 409 Conflict，前端显示冲突提示："该条目已被其他用户修改，请选择：覆盖 / 合并 / 放弃"
  - 用户选择"合并"时，前端 MUST 展示差异对比（diff view），用户手动选择保留哪些变更
  - 用户选择"覆盖"时，后端 MUST 接受新数据并递增 version
  - 思维导图模块的节点编辑 MUST 同样遵循乐观锁机制
  - 符合 Constitution "Data Isolation & Traceability" 原则：版本控制确保数据一致性

- **Q3**: 版本快照粒度 → **A**: 项目级快照 + 模块级增量标记（Option B）
  - 版本快照为项目级：每次创建版本时，记录整个项目的版本号（如 v1.0 → v1.1）
  - 增量标记机制：只复制有变更的模块数据，未变更模块引用上一版本的同模块数据
  - 版本元数据 MUST 包含：版本号、创建时间、创建人、变更模块列表（含变更摘要）
  - 版本对比时，系统 MUST 能展示跨模块的变更影响（如 PRD 修改后，关联的参数清单也显示受影响）
  - 版本回滚 MUST 支持整项目回滚或单模块回滚（用户可选择）
  - 版本数据存储 MUST 采用写时复制（Copy-on-Write）策略，避免重复存储未变更数据
  - 符合 Constitution "Version-Controlled Documentation" 原则：支持快照、对比、回滚

- **Q4**: 思维导图库选型 → **A**: 优先调研 Open WebUI 现有依赖，无则引入开源库（Option C → A）
  - 第一步：调研 Open WebUI 现有依赖（package.json）中是否已包含思维导图相关库（如 D3.js、Cytoscape.js 等可用于力导向图/层级图）
  - 第二步：检查 Open WebUI 组件库中是否已有树形图、层级图、流程图等可复用组件
  - 第三步：若 Open WebUI 无现成组件，引入开源思维导图库（推荐：react-flow、@xyflow/svelte、gojs-evaluation 等）
  - 选型标准：Svelte 兼容、支持拖拽/缩放/自定义节点、MIT/Apache 协议、社区活跃
  - 避免重复引入功能重叠的库，优先复用 Open WebUI 已有依赖

- **Q5**: 旧数据迁移策略 → **A**: 自动迁移 + 手动确认（Option B）
  - 首次访问模块时，系统 MUST 自动检测该模块是否存在旧格式数据（`{text: string}`）
  - 检测到旧数据时，系统 MUST 自动转换为新格式，并填充默认值（title 从 text 提取前50字符，priority 默认 P2，status 默认 open）
  - 迁移完成后，系统 MUST 显示迁移摘要：迁移条目数、字段映射情况、需要用户确认的异常项
  - 用户 MUST 能在迁移摘要页面查看和修正迁移结果（如调整标题、补充必填字段）
  - 用户确认修正后，数据 MUST 以新格式持久化存储，旧数据保留为备份（30天后自动清理）
  - 迁移失败时（如 text 内容无法解析），系统 MUST 标记该条目为"待处理"，用户可手动编辑或删除
  - 迁移过程 MUST 可中断和恢复，不影响其他模块的正常使用
  - 符合 Constitution "Manual-First Productivity" 原则：用户始终掌控数据迁移结果
