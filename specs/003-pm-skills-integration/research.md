# Research: PM Skills Integration

**Date**: 2026-07-11
**Feature**: PM Skills Integration (003)
**Status**: Complete

---

## Clarifications Resolved

### Q1: pm-skills 技能映射方式
**Decision**: 参考现有产品的 skill 导入方式，并在工作流中绑定对应的 skill。
**Rationale**: Open WebUI 已有 skill 导入模块，复用现有机制最符合架构一致性。
**Alternatives considered**: 手动逐个映射（工作量太大），自动同步（缺乏控制）。

### Q2: pm-skills 技能内容存储位置
**Decision**: 全量本地存储到 `backend/open_webui/pm/skills/pm-skills/`。
**Rationale**: 避免网络依赖，确保稳定性；作为项目版本管理的一部分。
**Alternatives considered**: 远程按需加载（网络依赖），本地缓存（增加复杂度）。

### Q3: pm-skills 版本更新策略
**Decision**: 固定版本不更新，管理员手动操作。
**Rationale**: 稳定性优先，避免自动更新引入破坏性变更。
**Alternatives considered**: 自动跟随上游（风险高），手动审核更新（增加工作量）。

### Q4: 工作流调用 pm-skills 的方式
**Decision**: 通过 Skill ID 引用。
**Rationale**: 最清晰、最可维护，符合"技能即通用模块"原则。
**Alternatives considered**: 命令别名映射（增加解析层），直接嵌入内容（失去模块化）。

### Q5: 链式技能调用的上下文传递方式
**Decision**: 显式输出绑定。
**Rationale**: 数据流清晰可追踪，符合"技能即通用模块"原则。
**Alternatives considered**: 隐式上下文传递（容易出错），统一上下文池（增加复杂性）。

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Skill Storage | Local files | Avoid network dependency, version controlled |
| Skill Invocation | Skill ID via registry | Clear, maintainable, consistent with architecture |
| Workflow Engine | Timbal (embedded Python library) | `pip install timbal` → `import timbal`. Workflows defined via `Workflow().step()` API. NOT `timbal start` (independent service prohibited by Constitution) |
| Context Passing | Explicit binding | Data flow traceability, testability |
| Version Strategy | Fixed, manual update | Stability, control |

---

## Integration Points

1. **Timbal Workflow Engine** (embedded Python library):
   - `pip install timbal` as dependency
   - Workflows defined via `Workflow().step()` API
   - Executed within Open WebUI Python backend (`async/await`)
   - NOT `timbal start` — independent service prohibited by Constitution
2. **Open WebUI Skill Registry**: pm-skills registered as external skill modules
3. **Open WebUI Agent/Pipeline**: auto-injects relevant pm-skills based on context
4. **ModuleEntry**: pm-skills output persists to existing data model

---

## Risk Analysis

| Risk | Mitigation |
|------|-----------|
| Timbal misused as service | Developers may accidentally use `timbal start` | Document clearly: `import timbal` only, NEVER `timbal start` |
| Skill ID conflicts | Namespace prefix (`pm-skills/`) |
| Performance degradation | Local storage, caching |
| Context passing errors | Explicit binding, validation |
