# 功能: 测试用例新增关联模块

## Goal

在测试用例表单中新增"关联模块"字段，使测试用例可以关联到具体的模块。

## Requirements

- 批注 #20: 新增关联模块
- 选择器: `div[class="border border-gray-200 dark:border-gray-700 rounded-2xl p-3 space-y-2"]`（测试用例表单）
- 页面路径: `/pm/{projectId}/testcase`

## Acceptance Criteria

- [ ] 测试用例创建/编辑表单新增"关联模块"字段
- [ ] 关联模块为可选项（可选已有模块或手动输入）
- [ ] 测试用例列表/详情中显示关联的模块信息
