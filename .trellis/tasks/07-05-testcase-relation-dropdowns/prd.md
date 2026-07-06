# 测试用例关联需求/版本下拉未打通

## Goal

修复测试用例页面中"关联需求"和"关联功能"下拉框未展示相关版本信息的问题。

## Context

- **当前实现**: 在 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 中：
  - `loadRelatedEntries()` 函数（第239行）在 testcase 模块时会加载 `requirementEntries` 和 `parameterEntries`
  - 新建表单中"关联需求"下拉（第1234-1239行）使用 `requirementEntries` 数据
  - "关联参数"下拉（第1240-1245行）使用 `parameterEntries` 数据
  - "关联功能"下拉（第1247-1251行）使用 `featureOptions`
- **Issue 报告**:
  - Issue #7: "关联需求"下拉没有打通需求数据
  - Issue #8: 下拉没有展示相关的版本信息
- **代码分析**:
  - 需求数据的加载逻辑存在，`requirementEntries` 应该有数据
  - 下拉选项中显示了 `[P2] title (id前6位)` 格式，但没有显示版本号
  - 版本信息需要从 entry 的 `currentVersionNumber` 或 `versionId` 获取并展示

## Requirements

1. "关联需求"下拉正确显示需求条目列表
2. 每个需求选项中显示版本号信息
3. "关联功能"下拉正确显示功能列表
4. 功能选项中关联版本号信息

## Acceptance Criteria

- [ ] "关联需求"下拉显示需求条目（含标题和版本号）
- [ ] "关联功能"下拉显示功能列表（含版本信息）
- [ ] 下拉数据从对应模块正确加载
