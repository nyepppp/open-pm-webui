# Open WebUI Agent 接入功能

**Issue**: #15  
**日期**: 2026-07-04  
**状态**: 规划中

---

## Goal

将 PM 工作流平台的所有模块通过 Open WebUI 的对话界面接入，使用户可以通过自然语言对话完成 PM 工作流的各项操作，包括数据查询、条目创建、模块关联、表单确认导入、质量检查、跨模块流转等，并将常见流程固化为 Open WebUI 的 Tool / Skill / 提示词。

## Background

当前项目是基于 Open WebUI 的 PM 工作流平台（fork 自 open-webui/open-webui）。PRD v1.0 定义了 28 个业务 Action，覆盖需求收集、PRD 编辑、参数清单、测试用例等完整 PM 生命周期。Agent 适配性调研（PM-Agent-Adaptability-Research.md）已确认 Open WebUI 的 Tool / Skill / Knowledge 机制天然适配 PM 模块集成。

### 已有代码基础

| 组件 | 文件 | 现状 |
|------|------|------|
| PM 后端 API | `backend/open_webui/routers/pm.py` | 45 个路由，覆盖 Projects/Entries/Versions/Relations/Agent |
| PM 前端 API | `src/lib/apis/pm/` | 20 个文件，含模块化 API + Agent Tools + Agent Chat |
| 前端 Agent Tools | `src/lib/apis/pm/agentTools.ts` | 5 个 Tool 函数 + 9 个 Skill 配置（TS 前端版） |
| 前端 Agent Chat | `src/lib/apis/pm/agentChat.ts` | Agent 对话 API 封装 |

**关键区分**：前端 TS Agent 系统是内置 Agent Chat 界面，本任务需桥接到 Open WebUI 标准 Tool/Skill/Prompt 体系（Python callable），两种机制共存。

## Requirements

### R1: PM 模块注册为 Open WebUI Tool

- 所有 PM 业务 Action 注册为 Open WebUI Tool 的 Python callable 函数
- Tool 按 PM 模块分组（12 个 Tool 类，约 55 个 callable）
- 每个 Tool 有正确的 OpenAPI 参数签名 + Valves 配置
- 支持 __event_emitter__ 状态推送 + __event_call__ 用户确认

### R2: 对话框检测和引入模块数据

- AI 自动检测用户意图与 PM 模块的关联
- 返回数据以结构化 Markdown 展示
- 支持跨模块数据查询

### R3: 模块关联与流转

- 需求→参数拆解（AI 自动识别参数信息）
- 跨模块流转编排（需求→PRD→参数→测试用例一键流转）
- 关联自动建立 + AI 建议关联

### R4: AI 对话框选择导入

- 所有 PM 模块支持对话选择导入
- 支持 Knowledge Base / Excel / CSV 导入
- 导入前预览确认

### R5: 表单输出与确认导入

- 写入操作前 confirmation 确认
- 复杂表单 input 逐步收集
- AI 生成内容预览确认后写入
- 兼容 Native Function Calling Mode

### R6: 流程固化为 Tool / Skill / 提示词

- 12 个 PM Tool 类注册
- 5+ 个 PM Skill 注册（PRD 生成、需求分析、参数提取、质量检查、完整流转）
- 2+ 个 PM 提示词注册

### R7: 产品路线图模块

- 甘特图视图 + 节点 CRUD + 依赖管理
- AI 排期建议 + 依赖冲突检测
- 进度追踪与 entries 状态联动

### R8: AI 质量检查引擎

- PRD 4 级检查（L1-L4）+ 规则引擎
- 检查结果交互式展示 + AI 修复建议
- 规则动态可配置

## Constraints

1. **手动优先**: 所有功能必须支持纯手动操作，AI 只是加速器
2. **项目隔离**: Tool 调用必须传递 project_id
3. **Open WebUI 兼容**: 不修改核心代码，只通过扩展机制集成
4. **License 合规**: 保留 Open WebUI branding
5. **双 Agent 共存**: 前端 TS Agent + Open WebUI Python Tool 共存不冲突

## Subtask Decomposition

| # | 子任务 | 交付物 | 依赖 | 预估 |
|---|--------|--------|------|------|
| 1 | pm-backend-api | PM API 完善 + Agent Tool API 扩展 | 无 | 3天 |
| 2 | pm-tool-registration | 12 个 Python Tool 类 (~55 callable) | #1 | 4天 |
| 3 | pm-skill-prompt-registration | 5+ Skill + 2+ 提示词 | #2 | 2天 |
| 4 | pm-form-confirmation-import | confirmation/input 流 + 数据导入 | #2 + #1 | 2天 |
| 5 | pm-roadmap-module | 甘特图 + AI 排期 + 冲突检测 | #1 + #2 | 4天 |
| 6 | pm-quality-check-engine | 4级检查 + 规则引擎 + AI 修复 | #2 + #4 | 4天 |
| 7 | pm-cross-module-flow | 流转引擎 + 5 个预置流转模板 | #2 + #4 + #6 | 3天 |
| 8 | pm-knowledge-e2e | Knowledge 导出 + E2E 验证 | 全部 | 2天 |

### 依赖关系

```
#1 pm-backend-api
    |
    +---> #2 pm-tool-registration
    |         |
    |         +---> #3 pm-skill-prompt-registration
    |         +---> #4 pm-form-confirmation-import
    |         |         |
    |         +---> #5 pm-roadmap-module (还需 #1)
    |         +---> #6 pm-quality-check-engine (还需 #4)
    |         |         |
    |         +---> #7 pm-cross-module-flow (还需 #4 + #6)
    |                   |
全部完成 -----------> #8 pm-knowledge-e2e
```

## Acceptance Criteria

- [ ] 12 个 PM Tool 类注册到 Open WebUI
- [ ] AI 能根据用户意图自动调用对应 Tool
- [ ] 写入操作有确认步骤
- [ ] 5+ Skill 和 2+ 提示词可通过 $ 和 / 命令引用
- [ ] 路线图甘特图可用 + AI 排期建议工作
- [ ] PRD 4 级检查引擎可用
- [ ] 跨模块流转（full_chain）可在对话中一键触发
- [ ] PM 条目可导出到 Knowledge Base
- [ ] 8 个 E2E 场景验证通过
- [ ] 项目隔离验证通过

## Notes

- 调研来源：Open WebUI 官方文档、Context7 文档库、PM-Agent-Adaptability-Research.md
- Open WebUI Function 类型：Tool（可调用函数）、Pipe（自定义模型）、Filter（请求拦截）、Action（消息按钮）
- __event_call__ 支持 confirmation 和 input 两种类型
- Functions 存储在数据库中，通过 exec() 动态加载
- 前端 TS Agent（agentTools.ts）和 Python Tool 共存
