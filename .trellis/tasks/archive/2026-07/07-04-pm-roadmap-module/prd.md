# 产品路线图模块

**父任务**: 07-04-open-webui-agent-integration  
**日期**: 2026-07-04  
**状态**: 规划中

---

## Goal

实现产品路线图模块（Roadmap），包括甘特图视图、节点 CRUD、依赖管理、AI 排期建议和进度追踪，并注册为 Open WebUI Tool 使 AI 可通过对话操作路线图。

## Requirements

### R1: 路线图数据模型

- 路线图节点（RoadmapNode）：里程碑、功能、发布三种类型
- 每个节点有名称、类型、状态、开始/结束日期、依赖关系、排序
- 节点关联到项目和版本
- 数据通过统一 entries 机制存储（module_type = "roadmap"）

### R2: 甘特图视图

- 前端实现甘特图组件（基于 Svelte + Canvas/SVG）
- 支持拖拽调整日期
- 支持依赖箭头连线
- 支持按状态/类型筛选
- 支持缩放（日/周/月视图）

### R3: AI 排期建议

- AI 分析需求列表和优先级，自动建议排期
- 检测依赖冲突和资源瓶颈
- 基于历史数据预测工期
- 通过 `pm_ai_tool.suggest_schedule` callable 实现

### R4: Open WebUI Tool 注册

| Tool callable | 描述 |
|---------------|------|
| `pm_roadmap_create_node` | 创建路线图节点 |
| `pm_roadmap_list_nodes` | 列出项目路线图 |
| `pm_roadmap_update_node` | 更新节点状态/日期 |
| `pm_roadmap_suggest_schedule` | AI 排期建议 |
| `pm_roadmap_detect_conflicts` | 检测依赖冲突 |

### R5: 进度追踪

- 路线图节点状态自动同步（与关联的 entries 状态联动）
- 项目整体进度百分比统计
- 通过 `pm_workflow_tool.progress` callable 查询

## Dependencies

- 依赖 `07-04-pm-backend-api`：需新增 roadmap 相关 API 端点
- 依赖 `07-04-pm-tool-registration`：Tool 注册框架已有，新增 roadmap Tool
- 依赖 `07-04-pm-skill-prompt-registration`：新增排期 Skill

## Acceptance Criteria

- [ ] 路线图节点 CRUD 通过 entries API 实现
- [ ] 甘特图组件渲染正确，支持拖拽和依赖连线
- [ ] AI 排期建议 Tool callable 可正常调用
- [ ] 依赖冲突检测可正常工作
- [ ] 进度统计与关联 entries 状态同步
