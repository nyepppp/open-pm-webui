# 新增功能：流程图

## Goal

为 PM 工作空间新增"流程图"模块，支持产品梳理需求流程时绘制可视化流程图，并将流程图中涉及出入参的节点与下游"参数清单"模块进行关联，实现需求流程与参数的双向追溯。

## Background

当前 PM 工作空间已支持需求管理、参数配置、测试用例、产品路线图等多个模块。技术团队期望在梳理需求流程时，能够同时产出流程图，并且流程图中涉及输入/输出参数的节点需要与"参数清单"模块进行关联，以便在参数清单中追溯参数来源的节点。

## Requirements

### 功能需求

1. **流程图模块**
   - 在 PM 工作空间导航中新增"流程图"模块
   - 支持创建、编辑、删除流程图条目
   - 每个流程图条目包含：标题、描述、流程图数据（节点和连线）

2. **流程图编辑器（类 Draw.io 体验）**
   - 基于 `@xyflow/svelte` 库实现可视化流程图编辑
   - **支持自定义节点类型**：用户可自由定义节点类型、形状、颜色、图标
   - **支持自定义连线样式**：实线、虚线、箭头样式等
   - 支持拖拽添加节点到画布
   - 支持节点之间的连线
   - 支持节点属性编辑：名称、类型、描述、样式
   - 支持节点的输入/输出参数配置
   - 提供节点模板库（开始、处理、判断、结束等预设模板）
   - 支持节点复制、粘贴、删除
   - 支持画布网格对齐、自动吸附

3. **节点与参数关联**
   - 流程图节点可配置输入参数和输出参数
   - 参数从现有"参数清单"模块中选择关联
   - 节点参数变更时同步更新参数清单中的关联关系

4. **参数清单反向追溯**
   - 在参数清单中显示参数关联的流程图节点信息
   - 格式：`参数 → 需求-流程图-节点名称`
   - 点击可跳转至对应流程图和节点

5. **流程图展示**
   - 支持流程图的查看模式（只读）
   - 支持流程图的缩放、平移
   - 节点高亮显示参数关联状态

### 非功能需求

- 流程图数据以 JSON 格式存储在 ModuleEntry 的 data 字段中
- 保持与现有 PM 模块一致的数据结构和 API 风格
- 支持版本管理（与现有版本系统兼容）
- **双向同步**：节点参数变更时同步更新参数清单；参数清单中参数被删除时，流程图节点中的关联也应同步移除

## Acceptance Criteria

- [ ] PM 工作空间导航栏中出现"流程图"模块入口
- [ ] 可以创建、编辑、删除流程图条目
- [ ] 流程图编辑器支持拖拽添加节点和连线
- [ ] 节点可以配置输入/输出参数并与参数清单关联
- [ ] 参数清单中显示关联的流程图节点信息（格式：参数 → 需求-流程图-节点名称）
- [ ] 流程图支持查看模式，可缩放和平移
- [ ] 流程图数据正确持久化，刷新页面后数据不丢失
- [ ] 与现有版本管理系统兼容

## Technical Notes

- 前端框架：Svelte 5 + SvelteKit
- 流程图库：@xyflow/svelte (已存在于 package.json 依赖中)
- 数据存储：复用现有 ModuleEntry 结构，流程图数据存储在 data.flowchart 字段
- 节点数据结构参考：
  ```
  {
    nodes: [
      {
        id: string,
        type: string, // 用户自定义类型，如 'start' | 'process' | 'decision' | 'end' | 'custom-xxx'
        position: { x: number, y: number },
        data: {
          label: string,
          description?: string,
          // 节点样式（自定义）
          style?: {
            backgroundColor?: string,
            borderColor?: string,
            borderWidth?: number,
            borderRadius?: number,
            width?: number,
            height?: number,
            icon?: string, // 图标名称或URL
            shape?: 'rectangle' | 'rounded' | 'circle' | 'diamond' | 'ellipse'
          },
          inputs?: string[], // 参数ID列表
          outputs?: string[] // 参数ID列表
        }
      }
    ],
    edges: [
      {
        id: string,
        source: string,
        target: string,
        label?: string,
        // 连线样式（自定义）
        style?: {
          stroke?: string,
          strokeWidth?: number,
          strokeDasharray?: string, // 实线/虚线
          animated?: boolean
        }
      }
    ],
    // 节点类型定义（用户自定义）
    nodeTypes?: {
      [typeName: string]: {
        label: string,
        defaultStyle: { /* 默认样式 */ },
        icon?: string,
        description?: string
      }
    }
  }
  ```

## Out of Scope

- 流程图的自动布局算法
- 流程图的导出为图片/PDF
- 复杂的工作流引擎集成
- 实时协作编辑
- 子流程（嵌套流程图）

## Open Questions

- ✅ 流程图节点类型是否需要自定义扩展？**→ 是，支持类 Draw.io 的自定义节点**
- ✅ 是否需要支持子流程（嵌套流程图）？**→ 暂时不需要**
- ✅ 参数关联是单向还是双向同步？**→ 双向同步**
