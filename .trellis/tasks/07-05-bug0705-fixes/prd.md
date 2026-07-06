# Fix bug0705 - 8 UI/功能问题修复

## Goal

修复 GitHub Issue #22 中报告的 8 个 UI/功能问题，涵盖日历同步、模块融合、弹窗失效、版本创建、下拉数据等。

## Source

- GitHub Issue: nyepppp/open-pm-webui#22
- Vibe Annotations 采集于 localhost:5173

## Issue Breakdown

| # | 页面 | 问题 | 子任务 |
|---|------|------|--------|
| 1 | /calendar | 日程未展示同步的 schedule 和 roadmap 内容 | 07-05-calendar-sync |
| 2 | /pm/... (首页) | 参数配置应与产品架构融合，支持切换视图，产品架构用思维导图 | 07-05-param-arch-merge |
| 3 | /pm/.../acceptance | 点击"新建"没有效果，没有新增内容弹窗 | 07-05-acceptance-risk-modal |
| 4 | /pm/.../prd | "创建新版本"按钮功能失效 | 07-05-prd-version-create |
| 5 | /pm/.../requirement | 新增模块的归属问题 | 07-05-requirement-module-placement |
| 6 | /pm/.../risk | 新增功能失效，没有新增内容弹窗 | 07-05-acceptance-risk-modal |
| 7 | /pm/.../testcase | 关联需求下拉没有打通需求数据 | 07-05-testcase-relation-dropdowns |
| 8 | /pm/.../testcase | 关联功能/需求下拉没有展示版本信息 | 07-05-testcase-relation-dropdowns |

## Acceptance Criteria

- [ ] 所有 8 个 issue 中描述的问题均被修复
- [ ] 每个子任务独立可验证
- [ ] 不引入新的回归问题
