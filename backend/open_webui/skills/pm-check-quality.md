---
name: PRD 质量检查
description: 对 PRD 文档执行 4 级质量检查（内容存在性、逻辑完整性、UX 启发式、安全性），生成修复建议
version: 1.0.0
author: PM Workflow Platform
tools:
  - pm_check_tool.run_check
  - pm_check_tool.list_results
  - pm_check_tool.update_status
  - pm_check_tool.suggest_fix
  - pm_check_tool.list_rules
  - pm_entry_tool.get_entry
---

# PRD 质量检查

## 目标
对 PRD 文档执行系统化的质量检查，确保文档的完整性、一致性和可测试性。

## 前置条件
- 用户已创建 PM 项目（project_id）
- 项目中已存在 PRD 条目（module_type="prd"）

## 检查级别

### L1: 内容存在性
检查 PRD 文档是否包含所有必需章节：
- 概述
- 目标
- 功能需求
- 非功能需求
- 背景
- 附录/术语表

### L2: 逻辑完整性
检查需求是否完整：
- 每个需求是否有优先级
- 每个需求是否有验收标准
- 参数是否有默认值
- 需求之间是否有矛盾
- 边界条件是否明确

### L3: UX 启发式
检查 UX 设计是否完善：
- 错误处理方案
- 加载状态
- 移动端适配
- 无障碍访问
- 性能指标

### L4: 安全性
检查安全设计：
- 输入验证
- 权限控制
- 敏感数据处理
- 审计日志

## 步骤

### 步骤 1: 选择 PRD
1. 使用 `pm_entry_tool.list_entries` 列出项目中的 PRD 条目
2. 选择要检查的 PRD

### 步骤 2: 执行检查
1. 使用 `pm_check_tool.run_check` 执行检查
2. 指定检查级别（默认 L1-L4）
3. 等待检查结果

### 步骤 3: 查看结果
1. 使用 `pm_check_tool.list_results` 查看检查结果
2. 按级别和类别分组查看
3. 关注失败的检查项

### 步骤 4: 获取修复建议
1. 对失败的检查项，使用 `pm_check_tool.suggest_fix` 获取 AI 修复建议
2. 查看具体的修改建议

### 步骤 5: 修复和重新检查
1. 根据建议修改 PRD
2. 使用 `pm_check_tool.run_check` 重新检查
3. 对比检查得分

## 用户确认点
- [ ] 步骤 2 开始前：确认检查级别
- [ ] 步骤 5 开始前：确认修复内容

## 输出
- 质量检查报告（含得分）
- 失败的检查项列表
- AI 修复建议
- 修复后的重新检查结果
