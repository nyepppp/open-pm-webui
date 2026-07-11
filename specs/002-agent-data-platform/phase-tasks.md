# 分阶段 Task 清单（P0→P4，coding-ready）

**关联**: `roadmap.md`（几步走）、`architecture.md`（接口规范）、`data-model.md`（数据模型）、`spec.md`（需求）、`design-principles.md`（准则）

> 本文档把每个 Phase 拆成**可独立交付、可独立测试**的 task 清单。每个 task 给出：
> - **规格（Spec）**：接口形态（TS / Pydantic / 数据结构 / 外部库 API 参考），供 AI 直接落地，**不含实现代码**。
> - **验收标准（AC）**：可核验的完成条件。
> - **依赖 / OUT**：前置 task 与本期禁区。
>
> 所有 task 严格收敛在 `design-principles.md` §0 的 IN-SCOPE，禁止扩散。

---

## 全局约定（所有 Phase 共用）

| 项 | 约定 |
|----|------|
| 技能载体 | 一切能力 = `SkillContract`（注册表条目）或 `pm_*` Tool，不得散落硬编码 |
| 落库真相源 | 产物必须经 `outputContract` 校验后写回 `ModuleEntry` |
| 隔离 | 所有实体带 `projectId`，跨项目查询 PROHIBITED（宪法原则 IV） |
| 确认门 | 写操作必走 `requires_confirm=True`（宪法原则 III） |
| 命名 | skill id 用 kebab-case（如 `prd-generation`）；Tool 名 `pm_<noun>` |
| 接口演进 | Skill 契约与 PM API 各自版本化（宪法 Data Compatibility） |
| 数据形态 | `SkillContract` / `NormalizedEntry` / `SkillInvocation` / `KnowledgeChunk` 等均为 **Pydantic `BaseModel`**（与 Timbal 结构化输出对齐） |
| **术语划界（重要）** | Timbal 自带 `Skills`/`Tools`/`Agents`/`Workflows` 原语，**不等于**本项目的 `SkillContract` 通用模块。本项目的「skill」是 registry 概念，可底层复用 Timbal `Tool`/`Workflow` 承载，但命名与职责必须区分，禁止混用 |

---

## Phase 0 — 技能基座（Skill Foundation）【P0】

**目标**：建立「技能即通用模块」骨架，使 skill 可用户指定、可被 Agent 自主选择。

### P0-T1 · 升级 `BaseSkill` 为通用模块骨架

**Spec**
- 在 `backend/open_webui/pm/skills/base.py` 的 `BaseSkill` 增加字段：
```python
class BaseSkill:
    id: str                      # kebab-case，如 "prd-generation"
    name: str
    description: str
    category: Literal["analysis","generation","extraction","workflow"]
    input_schema: Optional[dict]        # JSON Schema
    output_contract: dict               # JSON Schema，必须可落回 ModuleEntry
    invocation: Literal["explicit","autonomous","both"]
    requires_confirm: bool              # 写操作必为 True
    methodology_ref: Optional[str]      # 关联 SKILL.md 路径
```
- 抽象方法保留 `build_user_message` / `parse_response`；新增 `validate_output(raw) -> bool`（按 `output_contract` 校验）。

**AC**
- [ ] 现有 `PRDGenerationSkill` / `RequirementAnalysisSkill` / `RequirementReviewSkill` 在不改行为的前提下补齐新字段。
- [ ] `validate_output` 对符合 `output_contract` 的产物返回 True，否则抛 `ContractViolationError`。
- [ ] 单测：3 个既有技能字段补全后，`validate_output` 对样例产物通过。

**依赖**：无 ｜ **OUT**：不改 `ModuleEntry` 主结构。

---

### P0-T2 · 统一技能注册表（registry）

**Spec**
- 扩展 `backend/open_webui/pm/skills/__init__.py`，注册表同时容纳：
  - 可执行类技能 → `method_ref`（Python 类导入路径）
  - 方法论技能 → `methodology_ref`（SKILL.md 路径）+ `output_contract`
- 注册表 API（函数签名，非实现）：
```python
def register_skill(contract: SkillContract) -> None: ...
def get_skill(skill_id: str) -> SkillContract: ...
def list_skills(invocation: Optional[str] = None) -> list[SkillContract]: ...
def resolve_by_command(cmd: str) -> Optional[SkillContract]: ...  # "/pm-<id>" -> contract
```
- 注册表摘要结构（供 Pipeline 注入）：
```typescript
interface SkillRegistrySummary { id: string; description: string; invocation: 'explicit'|'autonomous'|'both'; category: string }
```

**AC**
- [ ] `register_skill` 拒绝重复的 `id`（`ContractConflictError`）。
- [ ] `list_skills(invocation='autonomous')` 仅返回 `invocation in ('autonomous','both')` 的技能。
- [ ] `resolve_by_command('/pm-prd-generation')` 返回对应 contract；非法命令返回 `None`。
- [ ] 既有 3 个技能在启动时自动注册。

**依赖**：P0-T1 ｜ **OUT**：不实现具体业务 skill。

---

### P0-T3 · 显式调用入口（`/pm-<id>` 路由）

**Spec**
- 在 `backend/open_webui/pm/intent.py` 增加命令识别：
```python
EXPLICIT_PATTERN = r"^/pm-([a-z0-9-]+)\s*(.*)$"
def parse_explicit_command(text: str) -> Optional[ExplicitCmd]: ...
# ExplicitCmd { skill_id: str, raw_args: str }
```
- 显式调用流程（状态机）：`解析 → registry.resolve → 运行 → output_contract 校验 → SkillInvocation(pending) → 确认门 → 落库 ModuleEntry → SkillInvocation(confirmed)`。

**AC**
- [ ] 输入 `/pm-prd-generation 围绕登录优化` 正确解析 `skill_id='prd-generation'`、`raw_args` 非空。
- [ ] 未注册 id（如 `/pm-xxx`）返回「技能不存在」提示，不触发调用。
- [ ] 调用链在落库前生成 `SkillInvocation` 记录且 `mode='explicit'`、`status='pending'`。

**依赖**：P0-T1, P0-T2 ｜ **OUT**：Agent 自主选择逻辑（属 P4）。

---

### P0-T4 · 确认门与 `SkillInvocation` 记录

**Spec**
- 复用 `backend/open_webui/pm/actions.py` 的 `ACTION_REGISTRY` + `requires_confirm`。
- `SkillInvocation`（Pydantic `BaseModel`，见 `data-model.md`）持久化接口：
```python
def record_invocation(inv: SkillInvocation) -> str: ...       # 返回 id
def confirm_invocation(inv_id: str, by: str) -> None: ...    # 落库 ModuleEntry
def reject_invocation(inv_id: str, by: str) -> None: ...
```

**AC**
- [ ] `requires_confirm=True` 的技能，未确认前不写 `ModuleEntry`。
- [ ] 确认后 `SkillInvocation.status` 转为 `confirmed` 且 `confirmedBy` 非空。
- [ ] 拒绝后 `status='rejected'`，不产生 `ModuleEntry` 写入。

**依赖**：P0-T1, P0-T3 ｜ **OUT**：可观测链路（属 P4）。

---

### P0-T5 · 支撑结构存储层（落库机制）

**Spec**
- 明确三个支撑结构的落库方式（此前文档只定义 shape，未定义存储）：
  - **`SkillInvocation`**：独立审计表 `pm_skill_invocations`（字段同 `data-model.md` 的 `SkillInvocation`）；用于审计与 P4 观测。
  - **`NormalizedEntry`**：**缓存表** `pm_normalized_entries`，键 `(entryId, version)`，存 `standardizedFields` + `normalizedAt`；用于 P1 幂等与回退，**非主数据**。
  - **`KnowledgeChunk`**：**不**在本项目独立持久化，统一推入 Open WebUI **Knowledge 集合**（见 P3-T4）；本结构仅作传输形态。
- Pydantic `BaseModel` 定义，供序列化与 Timbal 步骤间传递。

**AC**
- [ ] `pm_skill_invocations` 表可写入/按 `runId`/`projectId` 查询。
- [ ] `pm_normalized_entries` 以 `(entryId, version)` 为唯一键，重复写幂等。
- [ ] `KnowledgeChunk` 仅作为推入 Knowledge 的传输对象，无独立存储表。

**依赖**：P0-T4 ｜ **OUT**：主数据模型变更。

---

### P0-T6 · 前端技能面板（显式调用第二条路径）

**Spec**
- SvelteKit 前端从注册表摘要（`SkillRegistrySummary[]`）渲染技能面板；用户点击 → 触发与 `/pm-<id>` **等价**的显式调用。
- 前端↔后端契约（规格）：
```typescript
// 前端请求体（显式调用）
interface SkillInvokeRequest {
  project_id: string;
  skill_id: string;        // 来自面板选择或命令解析
  args?: Record<string, unknown>;
}
// 后端响应：建议态草稿（待确认）
interface SkillDraftResponse {
  invocation_id: string;   // 对应 SkillInvocation.id
  output: Record<string, unknown>;  // 经 output_contract 校验
  requires_confirm: boolean;
}
```

**AC**
- [ ] 面板列出当前 project 下 `invocation in ('explicit','both')` 的技能。
- [ ] 点击与输入 `/pm-<id>` 走同一后端解析/调用路径，产物一致。
- [ ] 草稿以「待确认」态呈现，确认前不落库。

**依赖**：P0-T2, P0-T3 ｜ **OUT**：自主选择的 UI（属 P4）。

---

### P0 退出标准

- [ ] `SkillContract` 全字段 schema 定义完成并通过单测（P0-T1/T2）。
- [ ] `/pm-<id>` 与面板两条显式路径均跑通：解析→运行→校验→确认→落库→记录（P0-T3/T4/T6）。
- [ ] 支撑结构存储层定义完成（P0-T5）。
- [ ] 与现有 `skills/base.py` / `skills/__init__.py` / `intent.py` / `actions.py` 对齐，无行为回归。
- [ ] 防扩散检查单通过（无 OUT-OF-SCOPE 能力混入）。

---

## Phase 1 — 数据流水线（On-demand Pipeline）【P1】

**目标**：Agent 调用时，Timbal 工作流对当前 project 数据做采集→清洗→标准化，产出供 Tool / RAG 使用的规范化数据。

### P1-T1 · Timbal 内嵌集成规格（已对齐真实 API）

**Spec**
- **嵌入方式**：作为 Python 库 `import`，**禁止**用 `timbal start` 起独立服务（违反原则 VI / OUT-OF-SCOPE）。
- **真实 API 参考形态**（规格级，AI 据此落地）：
```python
from timbal import Workflow
from timbal.state import get_run_context

async def collect(project_id: str) -> list[ModuleEntry]: ...        # 采集当前 project
async def clean(entries: list[ModuleEntry]) -> list[ModuleEntry]: ...# 去噪/补默认/校验
async def standardize(entries: list[ModuleEntry]) -> list[NormalizedEntry]: ...
async def dual_output(norm: list[NormalizedEntry]) -> PipelineResult: ...

wf = (
    Workflow(name="standardize_project")
    .step(collect, project_id=lambda: get_run_context().params["project_id"])
    .step(clean, entries=lambda: get_run_context().step_span("collect").output)
    .step(standardize, entries=lambda: get_run_context().step_span("clean").output)
    .step(dual_output, norm=lambda: get_run_context().step_span("standardize").output)
)

result = await wf(project_id=pid).collect()
# result.output: PipelineResult | result.status.code: "success"|"error"|"cancelled"
```
- 触发：由 Pipeline 在每次 Agent 请求时**唤醒一次**（非常驻），传入 `project_id`。
- **术语划界**：本工作流是 Timbal `Workflow` 原语；步骤函数若需复用 Open WebUI 能力，可包装为 Timbal `Tool`，但我们的 `SkillContract` 注册表概念不依赖 Timbal。

**AC**
- [ ] `Workflow` 能被后端 `import` 并组装、运行（不依赖 `timbal start`）。
- [ ] 步骤间通过 `get_run_context().step_span("<name>").output` 正确传值。
- [ ] `result.status.code == "error"` 时能被上层捕获并触发回退（见 P1-T3）。
- [ ] 每次 Agent 请求仅唤醒一次，不常驻后台。

**依赖**：P0（需 `project_id` 注入）｜ **OUT**：独立 Timbal 微服务、实时事件驱动、定时批处理。

---

### P1-T2 · 标准化变换规则（`ModuleEntry` → `NormalizedEntry`）

**Spec**
- 清洗规则（确定性、可单测）：
  - `trim`：去首尾空白；`drop_empty`：剔除空字段；`fill_defaults`：缺省 `status`/`priority` 补默认。
- 映射规则（规格）：`ModuleEntry` 字段 → `NormalizedEntry.standardizedFields`（Pydantic `BaseModel`）：
```typescript
interface NormalizedEntry {
  entryId: string; projectId: string; moduleType: ModuleType;
  standardizedFields: Record<string, unknown>;
  version: string; normalizedAt: number;
}
```
- 幂等定义：键 `(entryId, version)`，同键重复标准化结果字节一致。

**AC**
- [ ] 清洗对脏数据（含空白/空值）产出确定结果，单测覆盖 3 类脏数据。
- [ ] 同 `(entryId, version)` 跑两次，输出哈希一致（幂等）。
- [ ] 映射后 `standardizedFields` 可由 `output_contract` 消费。

**依赖**：P1-T1 ｜ **OUT**：语义重写/增强。

---

### P1-T3 · 失败回退与幂等保障

**Spec**
- 回退策略：Workflow 中途失败（`result.status.code != "success"`）→ 返回「未标准化原始数据 + notice」，绝不静默返回半标准化数据。
- 幂等键存储：`NormalizedEntry` 以 `(entryId, version)` 写入 P0-T5 的缓存表。

**AC**
- [ ] 注入一个会抛错的清洗步骤，系统回退到原始 `ModuleEntry` 并附 notice。
- [ ] 正常完成后再次触发，直接命中缓存键、不再重算。

**依赖**：P1-T2, P0-T5 ｜ **OUT**：跨项目标准化。

---

### P1-T4 · 双轨输出骨架

**Spec**
- 结构数据 → `pm_*` Tool 返回 `NormalizedEntry` 列表（精查，见 P3-T1）。
- 文档数据 → `KnowledgeChunk` 分块（见 `data-model.md`），带 `source` 引用，推入 Knowledge（见 P3-T4）。
- `PipelineResult`（Pydantic）作为末步合并输出：
```python
class PipelineResult(BaseModel):
    structured: list[NormalizedEntry]
    knowledge_pushed: int
```

**AC**
- [ ] 结构输出可被 `pm_*` Tool 消费（P3 打通）。
- [ ] 文档分块每个带可重建的 `source = /pm/{projectId}/{moduleType}/{entryId}`。

**依赖**：P1-T2, P0-T5 ｜ **OUT**：RAG 检索实现（属 P3）。

---

### P1 退出标准

- [ ] 「被唤醒 → 跑完 → 双轨输出」一次性生命周期定义清楚并通过集成验证（P1-T1~T4）。
- [ ] 幂等与失败回退单测通过（P1-T2/T3）。
- [ ] 明确不实现实时/定时触发（防扩散）。

---

## Phase 2 — 方法论融合（pm-skills Integration）【P2】

**目标**：将 68 个 `SKILL.md` 作为方法论知识层接入；为 Top-10 高价值技能定义输出契约。

### P2-T1a · `SKILL.md` 批量解析与入库

**Spec**
- 批量解析 68 个 `SKILL.md` 为 `MethodologyIndex` 条目（本地索引或 Knowledge）：
```typescript
interface MethodologyIndex {
  skillId: string;          // 对应 SkillContract.id
  skillMdPath: string;
  title: string; summary: string; tags: string[];
}
```
- 入库方式：写入索引表 / 或作为 Knowledge 文档（与 P3-T4 集合区分：方法论集合 vs 项目文档集合）。

**AC**
- [ ] 68 个 `SKILL.md` 可批量解析出 `MethodologyIndex` 条目，无遗漏/失败。
- [ ] 索引可持久化并支持按 `skillId` 查询。

**依赖**：P0-T2 ｜ **OUT**：转写为 Python 类。

---

### P2-T1b · 方法论检索接口

**Spec**
- 检索函数（按 `tags` / `summary` 匹配，返回 Top-K）：
```python
def retrieve_methodology(query: str, top_k: int = 5) -> list[MethodologyIndex]: ...
```

**AC**
- [ ] 给定关键词（如「机会解决方案树」）能召回对应 `SKILL.md`。
- [ ] 返回结果含 `skillMdPath`，可供 prompt 注入。

**依赖**：P2-T1a ｜ **OUT**：无。

---

### P2-T2a · 输出契约模板与校验工具

**Spec**
- 定义契约编写模板（JSON Schema 片段）与可复用校验器：
```python
def validate_contract(schema: dict) -> bool: ...          # JSON Schema 合法
def contract_matches_module(schema: dict, module_type: str) -> bool: ...  # 可落回 ModuleEntry
```
- 所有契约 `required` 至少含 `title` / `content`（或 `data`），且字段映射到 `ModuleEntry`。

**AC**
- [ ] 校验器对合法/非法 JSON Schema 正确返回 True/False。
- [ ] 校验器能识别「无法落回 ModuleEntry」的契约并拒绝。

**依赖**：P0-T1 ｜ **OUT**：无。

---

### P2-T2b · Top-10 高价值技能输出契约（分批交付）

**Spec**
- 为 Top-10（建议：prd-generation、requirement-analysis、requirement-review、opportunity-solution-tree、user-story-map、kano、jtbd、competitive-analysis、roadmap-planning、risk-assessment）各定义 `output_contract`（JSON Schema），**必须描述可落回 `ModuleEntry` 的形状**。
- 建议分批：每批 2–3 个契约，独立评审。
- 契约示例：
```json
{
  "type": "object",
  "required": ["title", "content"],
  "properties": {
    "title": { "type": "string" },
    "content": { "type": "string" },
    "data": { "type": "object", "properties": { "risks": { "type": "array" } } }
  }
}
```

**AC**
- [ ] 10 个契约均通过 P2-T2a 校验器（合法 + 可落回 ModuleEntry）。
- [ ] 每个契约可映射到一个 `moduleType`。
- [ ] 长尾 58 个仅作知识检索，无强制 `output_contract`（OUT：全量转写）。

**依赖**：P2-T2a ｜ **OUT**：68 个全转 Python。

---

### P2-T3 · skill ↔ `SKILL.md` 绑定关系表

**Spec**
- 绑定表（数据，可入 registry）：
```typescript
interface SkillMethodologyBinding {
  skillId: string; methodologyRef: string; outputContractId: string;
  isTopValue: boolean;   // Top-10 = true，长尾 = false
}
```

**AC**
- [ ] 10 个 Top 技能均有 `methodologyRef` + `outputContractId` 绑定。
- [ ] 注册表 `get_skill(id)` 能同时返回 `methodology_ref` 与 `output_contract`。

**依赖**：P2-T1a, P2-T2b ｜ **OUT**：无。

---

### P2 退出标准

- [ ] `SKILL.md` 入库可检索（P2-T1a/T1b）。
- [ ] Top-10 契约定义且经校验器验证、可落回 `ModuleEntry`（P2-T2a/T2b）。
- [ ] 绑定关系表建立，注册表可联动查询（P2-T3）。
- [ ] 长尾未强转（防扩散）。

---

## Phase 3 — 双轨供给打通（Dual-track Supply）【P2，可与 P2 并行】

**目标**：结构数据经 `pm_*` Tools 精查，文档类经 Knowledge RAG；Pipeline 自动注入 `project_id` / `tool_ids`。

### P3-T0 · 前置：当前项目上下文绑定（工作台↔对话）

**Spec**
- 定义「用户当前打开的项目」如何传入 Agent 请求（此前文档悬空）：
  - 机制：PM 工作台打开 project 时，将 `project_id` 绑定到当前对话会话（会话元数据 `chat.session.project_id`，或前端在 chat 请求体携带 `project_id`）。
  - 后端在请求入口读取 `project_id` 并注入 Pipeline（见 P3-T3）。
  - 未绑定 → Agent 进入 general mode，autonomous 技能禁用（见 spec.md Edge Case）。
- 接口契约：
```typescript
interface ChatRequestContext {
  chat_id: string;
  project_id?: string;   // 绑定后必有；未绑定则缺省
}
```

**AC**
- [ ] 工作台打开项目后，对话请求自动携带/可解析出 `project_id`。
- [ ] 未绑定项目时，Pipeline 注入仅含 `invocation='explicit'` 技能，autonomous 禁用。
- [ ] 跨项目 `project_id` 不会被错误绑定到他人会话（隔离）。

**依赖**：P0-T2 ｜ **OUT**：无。

---

### P3-T1 · Tool 精查接口清单

**Spec**
- 扩展 `backend/open_webui/pm/tools.py`，新增精查 Tool（Pydantic Input）：
```python
class PMSkillInvokeInput(BaseModel):
    project_id: str
    skill_id: str
    args: Optional[dict] = None

class PMEntryStandardizedQueryInput(BaseModel):
    project_id: str
    module_type: Optional[str] = None
    filters: Optional[dict] = None
```
- Tool 实现调用 P1 的标准化结果（**Agent 每次请求触发一次标准化**，与 P1 一致，非"按 tool 调用才标准化"的懒加载）。

**AC**
- [ ] `pm_skill_invoke` 按 `skill_id` 触发对应 `SkillContract`，返回 `output_contract` 校验后产物。
- [ ] `pm_entry_standardized_query` 返回 `NormalizedEntry` 列表，受 `project_id` 隔离。
- [ ] 跨 `project_id` 查询被拒（SC-005）。

**依赖**：P1（标准化数据）、P3-T0 ｜ **OUT**：语义重排。

---

### P3-T2 · Knowledge 同步与引用规范

**Spec**
- 同步：文档类 `ModuleEntry` → 切分 → `KnowledgeChunk`（带 `source`）→ 入 Knowledge（见 P3-T4）。
- 同步触发：Agent 调用时按需（复用 P1 唤醒），非实时。
- 引用规范：检索返回必须带 `source`，Agent 回答须 surface 引用（满足宪法 VI RAG）。

**AC**
- [ ] 文档类 entry 切分后每个 chunk `source` 可重建到精确 `ModuleEntry`。
- [ ] RAG 回答 100% 带 ≥1 个 `source` 引用（SC-004）。

**依赖**：P1-T4, P2-T1a ｜ **OUT**：重训练/微调。

---

### P3-T3 · Pipeline 注入契约

**Spec**
- 每次 Agent 请求自动注入（规格，见 `architecture.md` §4.4）：
```typescript
interface PipelineInjection {
  project_id: string;
  tool_ids: string[];        // 含 pm_* 工具
  knowledge_ids: string[];   // 绑定项目的知识库（见 P3-T4）
  skill_registry_summary: SkillRegistrySummary[];
}
```
- 注入时机：请求进入编排层时，从 P3-T0 的会话上下文取 `project_id`。

**AC**
- [ ] 对话绑定项目时，注入含正确 `project_id` 与 `tool_ids`。
- [ ] 未绑定项目时，`skill_registry_summary` 仅含 `invocation='explicit'` 技能（P3-T0）。
- [ ] 注入字段为空或缺失时，Agent 进入 general mode，不报错。

**依赖**：P0-T2, P3-T0 ｜ **OUT**：跨项目注入。

---

### P3-T4 · 每项目 Knowledge 集合管理

**Spec**
- 为每个 project 创建并绑定**一个** Open WebUI Knowledge 集合（项目文档集合，区别于 P2-T1a 的方法论集合）。
- 管理动作（函数签名，非实现）：
```python
def ensure_project_knowledge(project_id: str) -> str: ...   # 创建/返回 collection id
def sync_to_knowledge(project_id: str, chunks: list[KnowledgeChunk]) -> int: ...  # upsert
def unbind_project_knowledge(project_id: str) -> None: ...  # 项目删除时清理
```
- `knowledge_ids`（P3-T3）即本集合 id，与 `project_id` 绑定。

**AC**
- [ ] 项目首次使用 Agent 时自动创建并绑定 Knowledge 集合。
- [ ] `sync_to_knowledge` 幂等 upsert（同 chunk 重复同步不重复）。
- [ ] 项目删除时集合被清理，无孤儿数据。

**依赖**：P3-T2, P3-T0 ｜ **OUT**：无。

---

### P3 退出标准

- [ ] 当前项目上下文绑定打通，无项目绑定时安全降级（P3-T0）。
- [ ] 结构数据经 `pm_*` Tool 精查可用（P3-T1）。
- [ ] 文档数据经 Knowledge RAG 且带引用（P3-T2）。
- [ ] Pipeline 注入契约落地（P3-T3）；每项目 Knowledge 集合可管理（P3-T4）。

---

## Phase 4 — 自主编排（Autonomous Workflow）【P3】

**目标**：Agent 依据上下文自主选择并串联多个 skill，保留确认门与可观测。

### P4-T1 · 多 skill 编排协议

**Spec**
- 编排原语（规格，可用 Timbal `Workflow` 或 Agent 内置）：
```typescript
type Step =
  | { type: 'skill'; skillId: string; args?: dict }
  | { type: 'condition'; expr: string; then: Step[]; else?: Step[] }
  | { type: 'parallel'; branches: Step[][] }
```
- Agent 依据上下文产出 `Plan = Step[]`，逐 step 执行，每步走通用模块校验+确认门。

**AC**
- [ ] Agent 能为「分析风险并生成 PRD」类请求产出含 2+ step 的 `Plan`。
- [ ] 顺序 / 条件 / 并行三种 step 均能执行且各自走 `output_contract` 校验。
- [ ] 跨项目 step 被拒（原则 IV）。

**依赖**：P2, P3 ｜ **OUT**：跨项目编排、长期记忆。

---

### P4-T2 · 确认门与回退策略

**Spec**
- 每个写 step 必须经 `requires_confirm`；多 step 中任一步被拒 → 整链回退到已确认态，不部分落库。
- **边界决策（需评审确认）**：已确认 step 的产物默认「已生效、只允许往前补」，不自动连带撤销；如需撤销由用户显式触发。
- 自主调用每步 `SkillInvocation.chosenReason` 必填。

**AC**
- [ ] 链中第 2 步被拒，第 1 步已确认数据保留、第 3 步不执行。
- [ ] 自主模式每步回显 `skillId` + `chosenReason`（SC-002）。

**依赖**：P0-T4, P4-T1 ｜ **OUT**：自动跳过确认。

---

### P4-T3 · 调用链路观测 / 日志规范

**Spec**
- 观测结构（规格）：
```typescript
interface OrchestrationTrace {
  runId: string; projectId: string;
  steps: { skillId: string; mode: string; status: string; reason?: string; outputRef?: string }[];
  createdAt: number;
}
```
- 每次多 step 编排产生一条 `OrchestrationTrace`，step 数与执行一致。

**AC**
- [ ] 一次多 step 编排产生完整 `OrchestrationTrace`，step 数与执行一致。
- [ ] trace 可按 `runId` / `projectId` 检索（见 P4-T4）。

**依赖**：P4-T1 ｜ **OUT**：实时可视化面板（可后续）。

---

### P4-T4 · 观测数据持久化与查询 API

**Spec**
- `OrchestrationTrace` 持久化（复用 P0-T5 审计存储思路，独立表 `pm_orchestration_traces`）：
```python
def record_trace(trace: OrchestrationTrace) -> str: ...
def get_trace(run_id: str) -> Optional[OrchestrationTrace]: ...
def list_traces(project_id: str, limit: int = 50) -> list[OrchestrationTrace]: ...
```

**AC**
- [ ] trace 可写入并按 `runId` / `projectId` 查询。
- [ ] 查询结果与 P4-T3 产生的 trace 一致。

**依赖**：P4-T3 ｜ **OUT**：无。

---

### P4 退出标准

- [ ] 多 skill 自主编排跑通，含顺序/条件/并行（P4-T1）。
- [ ] 确认门与回退正确（P4-T2）。
- [ ] 调用链路可观测且可查询（P4-T3/T4）。
- [ ] 无跨项目/无长期记忆（防扩散）。

---

## 跨 Phase 依赖矩阵

| Task | 依赖 | Phase | 可并行 |
|------|------|-------|--------|
| P0-T1~T6 | — | P0 | T1→T2→T3/T4→T5/T6 |
| P1-T1~T4 | P0 | P1 | T1→T2→T3/T4 |
| P2-T1a/T1b, T2a/T2b, T3 | P0 | P2 | 可与 P3 并行 |
| P3-T0, T1~T4 | P1, P3-T0 | P3 | 可与 P2 并行 |
| P4-T1~T4 | P2, P3 | P4 | 串 |

**关键路径**：P0 → P1 → (P2 ∥ P3) → P4

---

## 防扩散检查单（每个 task 交付前核对）

- [ ] 是否引入 `design-principles.md` §0 OUT-OF-SCOPE 中的能力？
- [ ] 新增能力是否为「`SkillContract` 通用模块」或「`pm_*` Tool」之一？
- [ ] 产物是否都能落回 `ModuleEntry`？
- [ ] 是否保持 `project_id` 隔离与人工确认门？
- [ ] 接口是否规格级（TS/Pydantic/外部库 API 参考），未夹带实现代码？
- [ ] 是否混淆了本项目 `SkillContract` 与 Timbal 的 `Skills`/`Tools` 原语？
