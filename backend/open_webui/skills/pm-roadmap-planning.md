---
name: 产品路线图规划
description: 帮助用户规划和管理工作路线图，包括节点创建、AI 排期建议和冲突检测
version: 1.0.0
author: PM Workflow Platform
tools:
  - pm_roadmap_tool.list_roadmap_nodes
  - pm_roadmap_tool.create_roadmap_node
  - pm_roadmap_tool.update_roadmap_node
  - pm_roadmap_tool.suggest_schedule
  - pm_roadmap_tool.detect_conflicts
  - pm_entry_tool.list_entries
---

# 产品路线图规划

## 目标
帮助用户创建和管理产品路线图，包括里程碑、功能和发布计划。

## 前置条件
- 用户已创建 PM 项目（project_id）
- 项目中已存在需求条目（可选，用于 AI 排期）

## 步骤

### 步骤 1: 查看现有路线图
1. 使用 `pm_roadmap_tool.list_roadmap_nodes` 列出项目中的所有路线图节点
2. 了解当前的路线图状态

### 步骤 2: 创建路线图节点
1. 使用 `pm_roadmap_tool.create_roadmap_node` 创建新节点
2. 节点类型选择：
   - `milestone`：里程碑（关键时间点）
   - `feature`：功能（具体功能开发）
   - `release`：发布（版本发布计划）
3. 设置开始日期和结束日期
4. 设置依赖关系（可选）

### 步骤 3: AI 排期建议
1. 使用 `pm_roadmap_tool.suggest_schedule` 获取 AI 排期建议
2. AI 会分析需求列表和优先级，自动建议排期
3. 查看建议的工期和开始/结束时间

### 步骤 4: 冲突检测
1. 使用 `pm_roadmap_tool.detect_conflicts` 检测依赖冲突
2. 查看冲突列表和详细信息
3. 使用 `pm_roadmap_tool.update_roadmap_node` 调整节点日期解决冲突

### 步骤 5: 更新节点状态
1. 使用 `pm_roadmap_tool.update_roadmap_node` 更新节点状态
2. 状态流转：planning → in_progress → completed → cancelled

## 用户确认点
- [ ] 步骤 2 开始前：确认节点类型和日期
- [ ] 步骤 3 完成后：确认 AI 排期建议
- [ ] 步骤 5 开始前：确认更新内容

## 输出
- 路线图节点列表
- AI 排期建议报告
- 冲突检测报告
- 更新后的路线图
