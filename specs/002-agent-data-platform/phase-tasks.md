# 分阶段 Task 清单（P0→P4，coding-ready）

**关联**: `roadmap.md`（几步走）、`architecture.md`（接口规范）、`data-model.md`（数据模型）、`spec.md`（需求）、`design-principles.md`（准则）

> 本文档把每个 Phase 拆成**可独立交付、可独立测试**的 task 清单。每个 task 给出：
> - **规格（Spec）**：接口形态（TS / Pydantic / 数据结构），供 AI 直接落地，**不含实现代码**。
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
- `SkillInvocation`（数据模型见 `data-model.md`）持久化接口：
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

### P0 退出标准

- [ ] `SkillContract` 全字段 schema 定义完成并通过单测（P0-T1/T2）。
- [ ] `/pm-<id>` 显式调用跑通：解析→运行→校验→确认→落库→记录（P0-T3/T4）。
- [ ] 与现有 `skills/base.py` / `skills/__init__.py` / `intent.py` / `actions.py` 对齐，无行为回归。
- [ ] 防扩散检查单通过（无 OUT-OF-SCOPE 能力混入）。

---

## Phase 1 — 数据流水线（On-demand Pipeline）【P1】

**目标**：Agent 调用时，Timbal 工作流对当前 project 数据做采集→清洗→标准化，产出供 Tool / RAG 使用的规范化数据。

### P1-T1 · Timbal 内嵌集成规格

**Spec**
- Timbal 作为库嵌入 `backend/open_webui/pm/`，仅承载确定性 Workflow。
- Workflow 定义格式（yaml/json，规格）：
```yaml
workflow: standardize_project
steps:
  - collect:    { source: module_entry, filter: { project_id: "$project_id" } }
  - clean:      { rules: [trim, drop_empty, fill_defaults] }
  - standardize:{ target: NormalizedEntry, schema: normalized_entry_schema }
  - dual_output:{ tools: pm_query, knowledge: chunk_and_index }
```
- 触发协议：由 Pipeline 在每次 Agent 请求时「唤醒一次」（非常驻），传入 `project_id`。

**AC**
- [ ] Workflow 定义可被 Timbal 加载并解析。
- [ ] 触发入口接受 `project_id` 参数，且**每次 Agent 请求仅唤醒一次**。
- [ ] 不引入常驻后台进程（OUT：实时事件驱动）。

**依赖**：P0（需 `project_id` 注入）｜ **OUT**：定时批处理。

---

### P1-T2 · 标准化变换规则（`ModuleEntry` → `NormalizedEntry`）

**Spec**
- 清洗规则（确定性、可单测）：
  - `trim`：去首尾空白；`drop_empty`：剔除空字段；`fill_defaults`：缺省 `status`/`priority` 补默认。
- 映射规则（规格）：`ModuleEntry` 字段 → `NormalizedEntry.standardizedFields`：
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
- 回退策略：Workflow 中途失败 → 返回「未标准化原始数据 + notice」，绝不静默返回半标准化数据。
- 幂等键存储：`NormalizedEntry` 以 `(entryId, version)` 为缓存键。

**AC**
- [ ] 注入一个会抛错的清洗步骤，系统回退到原始 `ModuleEntry` 并附 notice。
- [ ] 正常完成后再次触发，直接命中缓存键、不再重算。

**依赖**：P1-T2 ｜ **OUT**：跨项目标准化。

---

### P1-T4 · 双轨输出骨架

**Spec**
- 结构数据 → `pm_*` Tool 返回 `NormalizedEntry` 列表（精查）。
- 文档数据 → `KnowledgeChunk` 分块（见 `data-model.md`），带 `source` 引用。
- 输出接口（规格）：
```python
def output_structured(entries: list[NormalizedEntry]) -> list[dict]: ...
def output_knowledge(chunks: list[KnowledgeChunk]) -> None: ...  # 入 Knowledge
```

**AC**
- [ ] 结构输出可被 `pm_*` Tool 消费（P3 打通）。
- [ ] 文档分块每个带可重建的 `source = /pm/{projectId}/{moduleType}/{entryId}`。

**依赖**：P1-T2 ｜ **OUT**：RAG 检索实现（属 P3）。

---

### P1 退出标准

- [ ] 「被唤醒 → 跑完 → 双轨输出」一次性生命周期定义清楚并通过集成验证（P1-T1~T4）。
- [ ] 幂等与失败回退单测通过（P1-T2/T3）。
- [ ] 明确不实现实时/定时触发（防扩散）。

---

## Phase 2 — 方法论融合（pm-skills Integration）【P2】

**目标**：将 68 个 `SKILL.md` 作为方法论知识层接入；为 Top-10 高价值技能定义输出契约。

### P2-T1 · `SKILL.md` 入库与检索规范

**Spec**
- 索引结构（本地索引或 Knowledge）：
```typescript
interface MethodologyIndex {
  skillId: string;          // 对应 SkillContract.id
  skillMdPath: string;      // 如 /skills/pm-skills/opportunity-solution-tree/SKILL.md
  title: string; summary: string; tags: string[];
}
```
- 检索：按 `tags` / `summary` 语义或关键词匹配，返回 Top-K 方法论供 prompt 注入。

**AC**
- [ ] 68 个 `SKILL.md` 可批量解析出 `MethodologyIndex` 条目。
- [ ] 给定关键词（如「机会解决方案树」）能召回对应 SKILL.md。

**依赖**：P0-T2 ｜ **OUT**：转写为 Python 类。

---

### P2-T2 · Top-10 高价值技能输出契约

**Spec**
- 为 Top-10（建议：prd-generation、requirement-analysis、requirement-review、opportunity-solution-tree、user-story-map、kano、jtbd、competitive-analysis、roadmap-planning、risk-assessment）各定义 `output_contract`（JSON Schema），**必须描述可落回 `ModuleEntry` 的形状**（title/content/data/metadata）。
- 契约示例（规格）：
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
- [ ] 10 个契约均通过 JSON Schema 合法性校验。
- [ ] 每个契约可映射到一个 `moduleType`（如 risk-assessment → `spec` 或 `feature`）。
- [ ] 长尾 58 个仅作知识检索，无强制 `output_contract`（OUT：全量转写）。

**依赖**：P0-T1, P2-T1 ｜ **OUT**：68 个全转 Python。

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

**依赖**：P2-T1, P2-T2 ｜ **OUT**：无。

---

### P2 退出标准

- [ ] `SKILL.md` 入库可检索（P2-T1）。
- [ ] Top-10 契约定义且可落回 `ModuleEntry`（P2-T2）。
- [ ] 绑定关系表建立，注册表可联动查询（P2-T3）。
- [ ] 长尾未强转（防扩散）。

---

## Phase 3 — 双轨供给打通（Dual-track Supply）【P2，可与 P2 并行】

**目标**：结构数据经 `pm_*` Tools 精查，文档类经 Knowledge RAG；Pipeline 自动注入 `project_id` / `tool_ids`。

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
- Tool 实现调用 P1 的标准化结果（懒加载：Agent 调用时才标准化）。

**AC**
- [ ] `pm_skill_invoke` 按 `skill_id` 触发对应 `SkillContract`，返回 `output_contract` 校验后产物。
- [ ] `pm_entry_standardized_query` 返回 `NormalizedEntry` 列表，受 `project_id` 隔离。
- [ ] 跨 `project_id` 查询被拒（SC-005）。

**依赖**：P1（标准化数据）｜ **OUT**：语义重排。

---

### P3-T2 · Knowledge 同步与引用规范

**Spec**
- 同步：文档类 `ModuleEntry` → 切分 → `KnowledgeChunk`（带 `source`）→ 入 Knowledge。
- 同步触发：Agent 调用时按需（复用 P1 唤醒），非实时。
- 引用规范：检索返回必须带 `source`，Agent 回答须 surface 引用（满足宪法 VI RAG）。

**AC**
- [ ] 文档类 entry 切分后每个 chunk `source` 可重建到精确 `ModuleEntry`。
- [ ] RAG 回答 100% 带 ≥1 个 `source` 引用（SC-004）。

**依赖**：P1-T4, P2-T1 ｜ **OUT**：重训练/微调。

---

### P3-T3 · Pipeline 注入契约

**Spec**
- 每次 Agent 请求自动注入（规格，见 `architecture.md` §4.4）：
```typescript
interface PipelineInjection {
  project_id: string;
  tool_ids: string[];        // 含 pm_* 工具
  knowledge_ids: string[];   // 绑定项目的知识库
  skill_registry_summary: SkillRegistrySummary[];
}
```
- 注入时机：请求进入编排层时，从当前打开项目取 `project_id`。

**AC**
- [ ] 对话绑定项目时，注入含正确 `project_id` 与 `tool_ids`。
- [ ] 未绑定项目时，`skill_registry_summary` 仅含 `invocation='explicit'` 技能， autonomous 技能禁用（见 spec.md Edge Case）。
- [ ] 注入字段为空或缺失时，Agent 进入 general mode，不报错。

**依赖**：P0-T2, P3-T1 ｜ **OUT**：跨项目注入。

---

### P3 退出标准

- [ ] 结构数据经 `pm_*` Tool 精查可用（P3-T1）。
- [ ] 文档数据经 Knowledge RAG 且带引用（P3-T2）。
- [ ] Pipeline 注入契约落地，无项目绑定时安全降级（P3-T3）。

---

## Phase 4 — 自主编排（Autonomous Workflow）【P3】

**目标**：Agent 依据上下文自主选择并串联多个 skill，保留确认门与可观测。

### P4-T1 · 多 skill 编排协议

**Spec**
- 编排原语（规格，Timbal Workflow 或 Agent 内置）：
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
- 日志落库，供审计与排障。

**AC**
- [ ] 一次多 step 编排产生完整 `OrchestrationTrace`，step 数与执行一致。
- [ ] trace 可按 `runId` / `projectId` 检索。

**依赖**：P4-T1 ｜ **OUT**：实时可视化面板（可后续）。

---

### P4 退出标准

- [ ] 多 skill 自主编排跑通，含顺序/条件/并行（P4-T1）。
- [ ] 确认门与回退正确（P4-T2）。
- [ ] 调用链路可观测（P4-T3）。
- [ ] 无跨项目/无长期记忆（防扩散）。

---

## 跨 Phase 依赖矩阵

| Task | 依赖 | Phase | 可并行 |
|------|------|-------|--------|
| P0-T1~T4 | — | P0 | 串 |
| P1-T1~T4 | P0 | P1 | 串 |
| P2-T1~T3 | P0 | P2 | 可与 P3 并行 |
| P3-T1~T3 | P1 | P3 | 可与 P2 并行 |
| P4-T1~T3 | P2, P3 | P4 | 串 |

**关键路径**：P0 → P1 → (P2 ∥ P3) → P4

---

## 防扩散检查单（每个 task 交付前核对）

- [ ] 是否引入 `design-principles.md` §0 OUT-OF-SCOPE 中的能力？
- [ ] 新增能力是否为「`SkillContract` 通用模块」或「`pm_*` Tool」之一？
- [ ] 产物是否都能落回 `ModuleEntry`？
- [ ] 是否保持 `project_id` 隔离与人工确认门？
- [ ] 接口是否规格级（TS/Pydantic 形态），未夹带实现代码？
