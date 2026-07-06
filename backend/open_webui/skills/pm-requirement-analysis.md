---
name: 需求分析流程
description: 分析需求条目，给出分类建议、优先级建议和潜在冲突分析
version: 1.0.0
author: PM Workflow Platform
tools:
  - pm_entry_tool.list_entries
  - pm_entry_tool.get_entry
  - pm_entry_tool.update_entry
  - pm_ai_tool.analyze_entry
  - pm_relation_tool.list_relations
  - pm_relation_tool.create_relation
---

# 需求分析流程

## 目标
对项目中的需求条目进行系统性分析，提供分类、优先级和冲突建议。

## 前置条件
- 用户已创建 PM 项目（project_id）
- 项目中已存在需求条目

## 步骤

### 步骤 1: 收集需求
1. 使用 `pm_entry_tool.list_entries` 列出项目中的所有需求条目
2. 使用 `pm_entry_tool.get_entry` 获取每个需求条目的详细内容
3. 记录需求的标题、描述、当前状态

### 步骤 2: AI 分析
1. 使用 `pm_ai_tool.analyze_entry` 对每个需求条目进行分析
2. 分析维度：
   - 分类建议（功能/性能/安全/体验）
   - 优先级建议（P0-P3）
   - 潜在冲突识别
   - 依赖关系建议

### 步骤 3: 关系分析
1. 使用 `pm_relation_tool.list_relations` 查看现有关系
2. 识别需求之间的依赖、包含、冲突关系
3. 使用 `pm_relation_tool.create_relation` 创建建议的关系（需用户确认）

### 步骤 4: 生成报告
1. 汇总所有需求的分析结果
2. 生成结构化的分析报告，包含：
   - 需求分类统计
   - 优先级分布
   - 冲突列表及解决建议
   - 依赖关系图（文本描述）

### 步骤 5: 更新需求
1. 询问用户是否接受分析结果
2. 使用 `pm_entry_tool.update_entry` 更新需求的分类和优先级
3. 更新需求的状态（如从 "draft" 改为 "analyzed"）

## 用户确认点
- [ ] 步骤 2 完成后：确认 AI 分析结果
- [ ] 步骤 3 完成后：确认关系创建
- [ ] 步骤 5 开始前：确认更新内容

## 输出
- 需求分析报告
- 更新后的需求条目
- 新创建的关系记录
