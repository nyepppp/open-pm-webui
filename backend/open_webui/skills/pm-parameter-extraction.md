---
name: 参数提取流程
description: 从 PRD 或需求文档中提取关键参数，包括参数名、类型、默认值、描述等
version: 1.0.0
author: PM Workflow Platform
tools:
  - pm_entry_tool.list_entries
  - pm_entry_tool.get_entry
  - pm_entry_tool.create_entry
  - pm_ai_tool.extract_parameters
  - pm_import_export_tool.extract_parameters
---

# 参数提取流程

## 目标
从 PRD 或需求文档中提取结构化的参数配置，用于开发、测试和部署。

## 前置条件
- 用户已创建 PM 项目（project_id）
- 项目中已存在 PRD 或需求条目

## 步骤

### 步骤 1: 选择源文档
1. 使用 `pm_entry_tool.list_entries` 列出项目中的 PRD 和需求条目
2. 询问用户选择要提取参数的源文档
3. 使用 `pm_entry_tool.get_entry` 获取选中文档的详细内容

### 步骤 2: 提取参数
1. 使用 `pm_ai_tool.extract_parameters` 对文档内容进行 AI 参数提取
2. 提取的参数字段：
   - name: 参数显示名称
   - key: 参数键名（英文）
   - type: 数据类型（string/int/bool/float/list/dict）
   - defaultValue: 默认值
   - description: 参数说明
   - module: 所属模块

### 步骤 3: 验证参数
1. 展示提取的参数列表
2. 询问用户确认每个参数的正确性
3. 允许用户添加、修改或删除参数

### 步骤 4: 保存参数
1. 使用 `pm_entry_tool.create_entry` 创建参数条目（module_type="parameter"）
2. 每个参数创建一个独立的条目
3. 或使用 `pm_import_export_tool.import_entries` 批量导入参数

### 步骤 5: 建立关系
1. 使用 `pm_relation_tool.create_relation` 建立参数与源文档的关系
2. 关系类型："derives"（派生自）

## 用户确认点
- [ ] 步骤 1 完成后：确认源文档选择
- [ ] 步骤 3 完成后：确认参数列表
- [ ] 步骤 5 完成后：确认关系创建

## 输出
- 结构化的参数列表（JSON）
- 参数条目（保存到 PM 系统）
- 参数与文档的关系记录
