# Research: 产品架构模块版本溯源与需求关联

**Feature**: 004-arch-module-version-demand
**Date**: 2026-07-08

## 技术决策

### 1. 版本履历存储方式

**Decision**: 内嵌 JSON 数组存储在模块/功能/参数表中

**Rationale**:
- 版本履历与条目是强关联的"写少读多"数据，内嵌存储避免 JOIN 查询
- 单用户工作台场景，无需担心并发写入冲突
- JSON 数组格式天然支持顺序存储和追加操作
- 符合项目 Constitution 中 "Version-Controlled Documentation" 原则

**Alternatives considered**:
- 独立表存储：支持更复杂查询，但增加 JOIN 开销，本场景过度设计
- 混合模式：增加复杂度，当前数据量无需此优化

### 2. 前端技术栈

**Decision**: SvelteKit + Tailwind CSS（沿用 Open WebUI 现有架构）

**Rationale**:
- 项目 Constitution 明确指定 Frontend 为 SvelteKit
- 表格视图、弹窗、思维导图均可使用现有组件库
- Tailwind CSS 设计系统已集成

### 3. 思维导图渲染

**Decision**: 使用 AntV G6 或 D3.js 进行只读树形渲染

**Rationale**:
- AntV G6 提供更开箱即用的树形布局
- D3.js 更灵活但配置复杂度高
- 只读模式限制了交互复杂度，G6 的 `enableZoom`/`enableDrag` 配置即可满足

### 4. CSV 导出实现

**Decision**: 前端生成 CSV Blob，触发浏览器下载

**Rationale**:
- 版本履历数据量可控（内嵌 JSON 数组），前端处理无需后端 API
- 使用标准 `Blob` + `URL.createObjectURL` 方案，兼容现代浏览器
- CSV 格式简单通用，无需第三方库

### 5. 软删除实现

**Decision**: 增加 `is_deleted` 布尔字段 + `deleted_at` 时间戳

**Rationale**:
- 最小侵入式方案，不影响现有查询逻辑（增加 WHERE 条件即可）
- 保留完整数据便于后续归档检索功能
- 符合项目 Constitution 中数据隔离原则

## 待确认事项

- [x] 版本履历存储方式 → 内嵌 JSON 数组
- [x] 导出格式 → CSV
- [x] 并发编辑 → 单用户，无需处理
- [x] 软删除策略 → 标记删除，完整保留
- [x] 数据量边界 → 浮窗展示最近 20 条