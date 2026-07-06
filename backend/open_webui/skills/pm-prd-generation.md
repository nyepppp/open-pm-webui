---
name: PRD 生成流程
description: 基于需求生成完整 PRD 文档，包含概述、背景、目标、功能需求、非功能需求、附录等章节
version: 1.0.0
author: PM Workflow Platform
tools:
  - pm_entry_tool.list_entries
  - pm_entry_tool.get_entry
  - pm_entry_tool.create_entry
  - pm_entry_tool.update_entry
  - pm_ai_tool.generate_prd
  - pm_ai_tool.check_entry
---

# PRD 生成流程

## 目标
根据用户提供的项目需求，生成结构化的 PRD（产品需求文档）。

## 前置条件
- 用户已创建 PM 项目（project_id）
- 用户已提供需求描述或已创建需求条目

## 步骤

### 步骤 1: 收集需求
1. 使用 `pm_entry_tool.list_entries` 列出项目中的需求条目（module_type="requirement"）
2. 如果需求条目不足，询问用户补充需求描述
3. 使用 `pm_entry_tool.get_entry` 获取每个需求条目的详细内容

### 步骤 2: 分析需求
1. 对收集到的需求进行分类（功能/性能/安全/体验）
2. 识别需求之间的依赖关系和潜在冲突
3. 确定需求的优先级（P0-P3）

### 步骤 3: 生成 PRD
1. 使用 `pm_ai_tool.generate_prd` 基于分析结果生成 PRD 内容
2. PRD 结构必须包含：
   - 概述（产品定位、目标用户）
   - 背景（市场分析、竞品分析）
   - 目标（业务目标、用户目标）
   - 功能需求（按模块组织）
   - 非功能需求（性能、安全、可用性）
   - 附录（术语表、参考文档）

### 步骤 4: 质量检查
1. 使用 `pm_ai_tool.check_entry` 对生成的 PRD 进行质量检查
2. 检查维度：完整性、一致性、可测试性
3. 根据检查结果提出修改建议

### 步骤 5: 保存 PRD
1. 询问用户确认 PRD 内容
2. 使用 `pm_entry_tool.create_entry` 创建 PRD 条目（module_type="prd"）
3. 将 PRD 内容保存到条目的 content 字段

## 用户确认点
- [ ] 步骤 2 完成后：确认需求分类和优先级
- [ ] 步骤 3 完成后：确认 PRD 大纲
- [ ] 步骤 5 开始前：确认最终 PRD 内容

## 输出
- 结构化的 PRD 文档（Markdown 格式）
- PRD 条目 ID（保存到 PM 系统后）
- 质量检查报告
