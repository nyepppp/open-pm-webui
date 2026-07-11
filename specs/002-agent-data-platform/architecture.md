# 架构文档：Agent 与数据平台

**关联**: `design-principles.md`（准则）、`roadmap.md`（几步走）、`spec.md` + `data-model.md`（需求）

> 本文档描述分层架构、技能即通用模块设计、数据流水线生命周期与接口规范（规格级，**非实现代码**）。所有接口供后续 AI coding 直接落地。

---

## 1. 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│ 用户触点（已完成=绿）                                          │
│  · PM 工作台（表单/富文本/流程图/架构图/SPEC）                  │
│  · Open WebUI 对话框                                          │
│  关键：两者共享同一 project_id → Agent 自动感知"当前项目"       │
└───────────────────────────────┬─────────────────────────────┘
                                 │ project_id 共享
┌───────────────────────────────▼─────────────────────────────┐
│ 编排层：Open WebUI 原生 Agent + Pipeline                       │
│  · Pipeline 自动注入 project_id / tool_ids / knowledge_ids     │
│  · 不引入 Timbal 编排（保持宪法原则 VI 纯净）                  │
└───────────────────────────────┬─────────────────────────────┘
                                 │
┌───────────────────────────────▼─────────────────────────────┐
│ 技能层：通用 skill 模块（registry）+ pm-skills 方法论          │
│  · 通用模块：id/name/desc/outputContract/invocation           │
│  · 双调用：用户指定(/pm-<id>) | Agent 自主选择                 │
│  · 方法论：68 个 SKILL.md（知识 + 输出契约约束）              │
└──────────────┬───────────────────────────────┬──────────────┘
               │ 确定性流水线                      │ 喂入 prompt
┌──────────────▼───────────────────────────────┐               │
│ 工作流引擎：Timbal（内嵌，仅确定性脏活）        │               │
│  采集 → 清洗 → 标准化 → 双轨输出               │               │
└──────────────┬───────────────────────────────┘               │
               │                                               │
┌──────────────▼──────────────────┐  ┌────────────────────────▼┐
│ 双轨供给                          │  │ Knowledge（RAG 语义召回） │
│  · 结构数据 → pm_* Tools 精查     │  │  · 文档类(PRD/会议/竞品)  │
│  · 文档数据 → Knowledge 分块      │  │  · 响应带来源引用         │
└──────────────┬──────────────────┘  └────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│ 统一数据底座：ModuleEntry（project_id 隔离 + 版本 + 关联）     │
│ 一切真相源；产物经 outputContract 落回                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 技能即通用模块（关键设计）

### 2.1 注册表条目结构（SkillContract）
见 §4.1。注册表同时容纳：
- 可执行类技能（如现有 `PRDGenerationSkill`、`RequirementAnalysisSkill`）→ 填 `methodRef`
- 方法论技能（pm-skills 的 `SKILL.md`）→ 填 `methodologyRef` + `outputContract`

### 2.2 双调用流程

**显式（用户指定）**
```
用户输入 /pm-<id> [args]
  → intent.py 识别命令 → 注册表查 id
  → 确定性强调用 skill
  → 产出经 outputContract 校验 → action 确认门(requires_confirm)
  → 落回 ModuleEntry
```

**自主（Agent 自主选择）**
```
Pipeline 收集上下文(project_id + 对话 + 注册表描述摘要)
  → Agent 对注册表技能打分/匹配
  → 选择最匹配 skill 并调用
  → 【必须】回显所选 skill id + 选择理由（透明性）
  → 产出经 outputContract 校验 → 确认门 → 落库
```

### 2.3 与现有代码对齐
- `skills/base.py` 的 `BaseSkill` 已是通用骨架（id/name/description/system_prompt/build_user_message/parse_response）。**升级点**：新增 `outputContract` + `invocation` 字段即符合通用模块。
- `skills/__init__.py` 的 registry 扩展为统一注册表（容纳方法论技能）。
- `intent.py` 负责显式命令识别；自主选择交给 Agent。
- `actions.py` 的 `ACTION_REGISTRY` 已是确认门，skill 写操作复用。

---

## 3. 数据流水线生命周期（按需拉取）

```
Agent 被调用（非实时常驻）
  → Pipeline 注入 project_id
  → 唤醒 Timbal Workflow（一次性）
       1. 采集：读取当前 project 的 ModuleEntry
       2. 清洗：去噪 / 补默认 / 校验完整性
       3. 标准化：映射为 NormalizedEntry（见 data-model.md）
  → 双轨输出：
       · 结构数据 → pm_* Tool 返回（精查）
       · 文档数据 → Knowledge 分块（带来源引用）
  → 回流：Agent 基于规范化数据推理，
          产物经 outputContract 落回 ModuleEntry
```

**要点**：非实时常驻；**幂等**（同一 project 多次跑结果一致）；失败回退到「未标准化原始数据 + 提示」。

---

## 4. 接口规范（规格级，供 AI coding）

### 4.1 SkillContract（TypeScript 接口，规格级）

```typescript
interface SkillContract {
  id: string;                                  // 唯一，如 "prd-generation"
  name: string;                                // 展示名
  description: string;                         // 供 Agent 检索 & 用户选择
  category: 'analysis' | 'generation' | 'extraction' | 'workflow';
  inputSchema?: Record<string, unknown>;       // JSON Schema（可选）
  outputContract: Record<string, unknown>;     // JSON Schema，必须可落回 ModuleEntry
  methodRef?: string;                          // 可执行 Python 类全路径（可选）
  methodologyRef?: string;                     // 关联 SKILL.md 路径（可选）
  invocation: 'explicit' | 'autonomous' | 'both';
  requiresConfirm: boolean;                    // 写操作必须为 true
}
```

### 4.2 Tool 输入（扩展现有 `tools.py` 的 Pydantic Input）

复用 `PMEntryCreateInput` / `PMEntryUpdateInput` / `PMEntryQueryInput` 等；新增：

```python
class PMSkillInvokeInput(BaseModel):
    project_id: str = Field(..., description="Project ID")
    skill_id: str = Field(..., description="Skill contract id")
    args: Optional[dict] = Field(None, description="参数化输入，符合 skill.inputSchema")
```

### 4.3 Knowledge 同步契约

`ModuleEntry` → 文档分块：

```typescript
interface KnowledgeChunk {
  entryId: string;
  projectId: string;
  moduleType: string;
  title: string;
  content: string;
  version: string;
  source: string;   // 引用：/pm/{projectId}/{moduleType}/{entryId}
}
```

### 4.4 Pipeline 注入契约

注入字段（每次 Agent 请求）：

```typescript
interface PipelineInjection {
  project_id: string;
  tool_ids: string[];        // 含 pm_* 工具
  knowledge_ids: string[];   // 绑定项目的知识库
  skill_registry_summary: { id: string; description: string; invocation: string }[];
}
```

---

## 5. 与既有模块对齐小结

| 现有模块 | 角色 | 本期升级点 |
|----------|------|-----------|
| `skills/base.py` | 通用 skill 骨架 | 加 `outputContract` + `invocation` |
| `skills/__init__.py` | 技能 registry | 扩展为统一注册表（含方法论技能） |
| `intent.py` | 显式命令识别 | 识别 `/pm-<id>` 双调用入口 |
| `tools.py` | Tool Input schema | 加 `PMSkillInvokeInput` |
| `actions.py` | 确认门 | skill 写操作复用 `requires_confirm` |
| `ModuleEntry` | 数据底座 | 加 `NormalizedEntry` 视图与 `SkillInvocation` 记录 |
