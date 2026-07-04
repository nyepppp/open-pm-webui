# 跨模块流转编排

**父任务**: 07-04-open-webui-agent-integration
**日期**: 2026-07-04
**状态**: 规划中

---

## Goal

实现 PM 模块间的数据流转编排，使需求文档可拆分为固定格式的参数（模块+参数），并支持一键从需求->PRD->参数->测试用例的链式流转，所有流转通过 AI 对话触发和确认。

## Requirements

### R1: 需求->参数拆解

- 需求条目可一键拆解为参数列表
- 拆解格式：参数名 + 英文 Key + 数据类型 + 所属模块 + 来源需求
- AI 自动识别需求中的参数信息，生成参数清单草案
- 用户确认后批量创建参数条目
- 自动建立需求->参数关联关系

### R2: 需求->PRD 流转

- 选择一组需求 -> AI 生成 PRD 大纲
- 大纲中引用需求内容，保持溯源关联
- PRD 创建后自动建立需求->PRD 关联

### R3: PRD->参数提取

- 从 PRD 内容自动提取参数（字段名、类型、默认值）
- 与需求拆解的参数合并/去重
- 自动建立 PRD->参数关联

### R4: 参数->测试用例生成

- 基于参数清单自动生成测试用例
- 每个参数至少生成一条边界测试 + 一条正常值测试
- 自动建立参数->测试用例关联

### R5: 流转编排引擎

- 定义流转模板（flow_template）：指定输入模块、输出模块、转换规则
- 流转模板存储为 entries（module_type = "flow_template"）
- 预置流转模板：requirement_to_parameter, requirement_to_prd, prd_to_parameter, parameter_to_testcase, full_chain

### R6: Open WebUI Tool 注册

| Tool callable | 描述 |
|---------------|------|
| pm_flow_execute | 执行流转模板（含确认） |
| pm_flow_list_templates | 列出可用流转模板 |
| pm_flow_create_template | 创建自定义流转模板 |
| pm_flow_preview | 预览流转结果（不写入） |

### R7: 流转 Skill

full_chain 完整流转 Skill：选择需求 -> 预览 -> 确认 -> 逐步执行 -> 展示关联图谱

## Dependencies

- 依赖 07-04-pm-backend-api：需新增 flow 执行 API
- 依赖 07-04-pm-tool-registration：新增 flow Tool callable
- 依赖 07-04-pm-form-confirmation-import：流转每步需确认
- 依赖 07-04-pm-quality-check-engine：PRD 生成后可自动触发质量检查

## Acceptance Criteria

- [ ] 需求可一键拆解为参数列表
- [ ] 需求->PRD 流转正常工作
- [ ] PRD->参数提取流转正常工作
- [ ] 参数->测试用例流转正常工作
- [ ] full_chain 一键流转可在对话中触发
- [ ] 每步流转有用户确认
- [ ] 自动建立跨模块关联关系
- [ ] 流转结果可通过 pm_flow_preview 预览
