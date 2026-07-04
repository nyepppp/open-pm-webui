# AI 质量检查引擎

**父任务**: 07-04-open-webui-agent-integration
**日期**: 2026-07-04
**状态**: 规划中

---

## Goal

实现 PM 文档质量检查引擎，支持 PRD 4 级检查（内容完整性、逻辑一致性、UX 启发式、安全性），规则引擎可配置扩展，检查结果通过 Open WebUI Tool callable 在对话中交互式展示和修复。

## Requirements

### R1: 4 级 PRD 检查体系

| 级别 | 类别 | 检查项示例 |
|------|------|-----------|
| L1 内容存在性 | content_existence | 概述是否存在、目标是否定义、非功能需求是否列出 |
| L2 逻辑完整性 | logic_completeness | 需求是否有优先级、参数是否有默认值、是否有验收标准 |
| L3 UX 启发式 | ux_heuristic | 是否考虑错误处理、是否有加载状态、是否考虑移动端 |
| L4 安全性 | security | 是否有输入验证、是否有权限控制、是否有敏感数据处理 |

### R2: 规则引擎

- 每条规则有 rule_id、level、category、description、check_type
- 规则存储在 entries（module_type = "check_rule"）或配置文件
- 支持动态添加/修改规则（不需要改代码）
- 每条规则返回：pass / fail / ignored / pending

### R3: 检查结果交互

- 检查结果以结构化 Markdown 展示（按级别分组、按严重性排序）
- 失败项附带修改建议（AI 生成）
- 用户可通过 __event_call__ 选择：接受建议/忽略/手动修改

### R4: Open WebUI Tool 注册

| Tool callable | 描述 |
|---------------|------|
| pm_check_run | 执行指定级别的检查 |
| pm_check_list_results | 列出检查结果 |
| pm_check_update_status | 更新检查项状态 |
| pm_check_suggest_fix | AI 生成修复建议 |
| pm_check_rules | 查看规则库 |

### R5: 检查 Skill

PRD 质量检查全流程 Skill：选择 PRD -> 执行检查 -> 展示结果 -> 逐项修复 -> 重新检查

## Dependencies

- 依赖 07-04-pm-backend-api：需新增 check 相关 API
- 依赖 07-04-pm-tool-registration：新增 check Tool callable
- 依赖 07-04-pm-form-confirmation-import：修复建议需确认流程

## Acceptance Criteria

- [ ] L1-L4 四级检查规则定义完成（>=30 条规则）
- [ ] 规则引擎支持动态配置
- [ ] 检查执行 API 端点正常工作
- [ ] Tool callable 可在对话中调用检查
- [ ] 检查结果以 Markdown 格式展示
- [ ] AI 修复建议可通过确认流程写入
