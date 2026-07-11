# 分阶段实施路线图（几步走）

**关联准则**: `design-principles.md`
**原则**: 每阶段独立可测、可演示；不假设后续阶段已完成；严格 IN-SCOPE，不在本期扩散（见 design-principles §0）。

---

## 总览

```
Phase 0  技能基座      → 通用 skill 模块 + 注册表 + 双调用
   │
Phase 1  数据流水线    → Timbal 内嵌 + 按需标准化 + 双轨输出骨架
   │
Phase 2  方法论融合 ┐
Phase 3  双轨供给   ┝ 可并行
Phase 4  自主编排    → Agent 串联多 skill + 确认门 + 可观测
```

---

## Phase 0 — 技能基座（Skill Foundation）【P0 最高优先级】

- **目标**：建立「技能即通用模块」骨架，使 skill 可用户指定、可被 Agent 自主选择。
- **关键交付物（文档/规格，非代码）**：
  - `SkillContract` 契约规范（见 `architecture.md` §4.1）
  - 技能注册表数据结构（通用模块元数据）
  - 意图 → 技能路由规则（用户显式 vs Agent 自主的判定边界）
- **依赖**：无（地基）。
- **退出标准**：注册表 schema 定义完成；双调用判定规则写明；与现有 `skills/__init__.py`、`intent.py`、`skills/base.py` 对齐。
- **OUT**：不实现具体业务 skill，不做流水线。

---

## Phase 1 — 数据流水线（On-demand Pipeline）【P1】

- **目标**：Agent 调用时，Timbal 工作流对当前 project 数据做采集 → 清洗 → 标准化，产出可供 Tool / RAG 使用的规范化数据。
- **关键交付物**：
  - Timbal 内嵌集成规格（Workflow 定义格式、触发协议）
  - 标准化变换规则（`ModuleEntry` → `NormalizedEntry`）
  - 双轨输出骨架（Tool 返回结构 + Knowledge 分块映射，见 `data-model.md`）
- **依赖**：Phase 0（需要 project_id 注入与技能上下文）。
- **退出标准**：定义清楚「被唤醒 → 跑完 → 回流」的一次性生命周期；明确幂等与失败回退。
- **OUT**：不做实时存盘触发；不做定时批处理。

---

## Phase 2 — 方法论融合（pm-skills Integration）【P2】

- **目标**：将 68 个 `SKILL.md` 作为方法论知识层接入；为 Top-10 高价值技能定义输出契约。
- **关键交付物**：
  - `SKILL.md` 入库与检索规范（Knowledge 或本地索引）
  - Top-10 技能输出契约（JSON Schema，可落回 ModuleEntry）
  - skill 与 `SKILL.md` 的绑定关系表
- **依赖**：Phase 0（注册表）、Phase 1（标准化后数据供方法论消费）。
- **OUT**：不转写全部 68 个为 Python；长尾仅作知识检索。

---

## Phase 3 — 双轨供给打通（Dual-track Supply）【P2，可与 P2 并行】

- **目标**：结构数据经 `pm_*` Tools 精查，文档类经 Knowledge RAG；Pipeline 自动注入 `project_id` / `tool_ids`。
- **关键交付物**：
  - Tool 精查接口清单（扩展现有 `tools.py` 的 Input schema）
  - Knowledge 同步与引用规范（含来源引用，满足宪法 VI RAG 要求）
  - Pipeline 注入契约
- **依赖**：Phase 1（规范化数据）。
- **OUT**：不做语义重排 / 重训练。

---

## Phase 4 — 自主编排（Autonomous Workflow）【P3】

- **目标**：Agent 依据上下文自主选择并串联多个 skill，形成工作流；保留确认门与可观测。
- **关键交付物**：
  - 多 skill 编排协议（顺序 / 条件 / 并行）
  - 确认门与回退策略
  - 调用链路观测 / 日志规范
- **依赖**：Phase 2 + Phase 3。
- **OUT**：不做跨项目编排；不做长期记忆。

---

## 优先级与依赖矩阵

| 阶段 | 优先级 | 依赖 | 是否并行 |
|------|--------|------|----------|
| P0 技能基座 | P0 | — | — |
| P1 数据流水线 | P1 | P0 | — |
| P2 方法论融合 | P2 | P0, P1 | 可与 P3 并行 |
| P3 双轨供给 | P2 | P1 | 可与 P2 并行 |
| P4 自主编排 | P3 | P2, P3 | — |

---

## 防扩散检查清单（每阶段交付前核对）

- [ ] 是否引入了 OUT-OF-SCOPE 中的任何能力？
- [ ] 新增能力是否为「通用 skill 模块」或「`pm_*` Tool」之一？
- [ ] 产物是否都能落回 `ModuleEntry`？
- [ ] 是否保持了 `project_id` 隔离与人工确认门？
