# 技术设计：流程图功能问题排查与修复

## 边界与范围

本次修复聚焦于流程图页面（`/pm/{id}/flowchart`）的以下三个问题域：
1. 画布形状渲染逻辑
2. Excalidraw 容器与右侧面板的集成
3. 实体绑定按钮的 API 调用与数据处理

## 架构概览

```
FlowchartPage
├── ExcalidrawContainer (画布容器)
│   ├── ExcalidrawCanvas (核心画布)
│   └── App-toolbar (工具栏)
└── RightPanel (右侧面板 - 当前为独立组件)
    ├── NodeConfig (节点配置)
    ├── Traceability (溯源绑定)
    └── EntityButtons (PRD/模块/功能/参数)
```

## 问题分析

### 问题 1：形状渲染始终为矩形

**根因假设**：
- 形状选择器的值未正确传递到 Excalidraw 的元素创建逻辑
- `excalidrawDataConverter.ts` 中的类型转换逻辑有缺陷（LSP 报错显示该文件有语法错误）
- 形状类型枚举值与 Excalidraw 内部类型不匹配

**排查路径**：
1. 检查形状选择器的 `onChange` 事件处理
2. 检查元素创建时的 `type` 字段赋值
3. 检查 `excalidrawDataConverter.ts` 的转换逻辑（文件有 LSP 错误）

### 问题 2：右侧面板未融入 Excalidraw

**根因假设**：
- 右侧面板作为独立 `div` 浮层渲染，未使用 Excalidraw 的扩展 API
- 缺少 `renderTopRightUI` 或 `renderSidebar` 等 Excalidraw 钩子
- 面板层级（z-index）或定位问题导致被画布遮挡

**排查路径**：
1. 检查 Excalidraw 组件的 props 是否包含自定义渲染钩子
2. 检查右侧面板的 CSS 定位和层级
3. 确认是否应使用 Excalidraw 的 `renderTopRightUI` 替代独立面板

### 问题 3：实体按钮无响应

**根因假设**：
- `flowchart.ts` API 文件有类型错误（LSP 报错显示参数数量不匹配）
- API 端点或查询参数不正确
- 实体数据为空或查询条件有误
- 按钮点击事件未正确绑定

**排查路径**：
1. 检查 `flowchart.ts` 的 API 函数签名与调用
2. 检查按钮的 `onClick` 处理函数
3. 检查 API 响应数据和错误处理
4. 验证实体查询的参数（项目 ID 等）

## 数据流

### 形状创建流程
```
用户选择形状 → 状态更新 → 鼠标点击画布 → 创建 ExcalidrawElement
                                                  ↓
                                        type 字段赋值（此处可能出错）
                                                  ↓
                                        Excalidraw 渲染引擎
```

### 实体绑定流程
```
用户点击按钮 → 调用 API (flowchart.ts) → 后端查询 → 返回实体列表
                                                  ↓
                                        错误处理或空数据处理（此处可能出错）
                                                  ↓
                                        更新 UI 显示列表
```

## 兼容性

- 修复需兼容当前 Excalidraw 版本
- 不破坏现有流程图的保存/加载功能
- 保持与项目其他页面的路由参数一致性

## 回滚策略

- 所有修改集中在流程图相关文件
- 回滚时恢复以下文件即可：
  - `src/lib/utils/excalidrawDataConverter.ts`
  - `src/lib/apis/pm/modules/flowchart.ts`
  - 流程图页面组件文件
