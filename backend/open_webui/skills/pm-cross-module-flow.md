---
name: 跨模块流转编排
description: 执行 PM 模块间的数据流转编排，支持需求→PRD→参数→测试用例的链式流转
version: 1.0.0
author: PM Workflow Platform
tools:
  - pm_flow_tool.list_templates
  - pm_flow_tool.preview_flow
  - pm_flow_tool.execute_flow
  - pm_flow_tool.create_template
  - pm_entry_tool.list_entries
  - pm_entry_tool.get_entry
  - pm_relation_tool.list_relations
---

# 跨模块流转编排

## 目标
实现 PM 模块间的数据流转编排，支持一键从需求→PRD→参数→测试用例的链式流转。

## 前置条件
- 用户已创建 PM 项目（project_id）
- 项目中已存在源模块条目（如需求）

## 预置流转模板

### 1. 需求→参数拆解 (requirement_to_parameter)
- **输入**: requirement 条目
- **输出**: parameter 条目列表
- **步骤**:
  1. 获取需求内容
  2. AI 提取参数
  3. 创建参数条目
  4. 建立需求→参数关联

### 2. 需求→PRD (requirement_to_prd)
- **输入**: requirement 条目列表
- **输出**: prd 条目
- **步骤**:
  1. 获取需求列表
  2. 分析需求
  3. AI 生成 PRD
  4. 创建 PRD 条目
  5. 建立需求→PRD 关联

### 3. PRD→参数提取 (prd_to_parameter)
- **输入**: prd 条目
- **输出**: parameter 条目列表
- **步骤**:
  1. 获取 PRD 内容
  2. AI 提取参数
  3. 合并去重
  4. 创建参数条目
  5. 建立 PRD→参数关联

### 4. 参数→测试用例 (parameter_to_testcase)
- **输入**: parameter 条目列表
- **输出**: testcase 条目列表
- **步骤**:
  1. 获取参数列表
  2. AI 生成测试用例
  3. 创建测试用例条目
  4. 建立参数→测试用例关联

### 5. 完整流转链 (full_chain)
- **输入**: requirement 条目
- **输出**: prd + parameter + testcase 条目
- **步骤**:
  1. 执行 requirement_to_prd
  2. 执行 prd_to_parameter
  3. 执行 parameter_to_testcase

## 步骤

### 步骤 1: 选择流转模板
1. 使用 `pm_flow_tool.list_templates` 列出可用模板
2. 选择要执行的流转模板

### 步骤 2: 预览流转
1. 使用 `pm_flow_tool.preview_flow` 预览流转结果
2. 查看预计输出和步骤

### 步骤 3: 执行流转
1. 使用 `pm_flow_tool.execute_flow` 执行流转
2. 确认后逐步执行每个步骤
3. 查看执行结果

### 步骤 4: 查看关联
1. 使用 `pm_relation_tool.list_relations` 查看新创建的关联
2. 验证流转结果

## 用户确认点
- [ ] 步骤 2 完成后：确认预览结果
- [ ] 步骤 3 开始前：确认执行流转

## 输出
- 流转执行报告
- 新创建的条目列表
- 跨模块关联关系
