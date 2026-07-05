# Open WebUI Agent 接入功能 - 技术设计

**日期**: 2026-07-04
**状态**: 规划中

---

## 1. 系统架构

### 1.1 整体集成架构

```
┌──────────────────────────────────────────────────────────────────┐
│                      Open WebUI 前端 (Svelte)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────────┐ │
│  │ Chat UI  │ │ Workspace│ │ Knowledge│ │  Tool/Skill/Prompt  │ │
│  │ 对话界面  │ │ 工作空间  │ │  RAG     │ │     管理界面        │ │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └──────────┬──────────┘ │
│        └─────────────┴─────────────┴─────────────────┘            │
│                          │                                        │
│                    tool_ids / skill_ids                           │
│                    chat/completions API                           │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Open WebUI 后端 (Python)                       │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              chat_completion() 处理器                      │    │
│  │  1. 解析 model → 路由到 Ollama / OpenAI-compatible        │    │
│  │  2. 解析 tool_ids → 加载 Tool 函数                         │    │
│  │  3. task model 识别意图 → 选择 Tool callable               │    │
│  │  4. 执行 Tool → 结果注入对话                                │    │
│  │  5. 流式返回 → SSE / Socket.IO                             │    │
│  └──────────────────────────┬───────────────────────────────┘    │
│                             │                                    │
│  ┌──────────────────────────┼───────────────────────────────┐    │
│  │                     PM Tool 层                             │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │    │
│  │  │Project │ │Require-│ │  PRD   │ │Param-  │ │Test-   │ │    │
│  │  │ Tool   │ │ment    │ │  Tool  │ │eter    │ │case    │ │    │
│  │  │        │ │ Tool   │ │        │ │ Tool   │ │ Tool   │ │    │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ │    │
│  │      └──────────┴──────────┴──────────┴──────────┘      │    │
│  │                         │ HTTP                           │    │
│  └─────────────────────────┼────────────────────────────────┘    │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   PM API 后端 (/api/v1/pm/...)               │ │
│  │  project / requirement / prd / parameter / testcase / ...    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                            │                                     │
│  ┌─────────────────────────┼─────────────────────────────────┐  │
│  │                   SQLite / PostgreSQL                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流：对话 → PM 操作

```
用户消息: "帮我看看项目X有哪些需求"
    │
    ▼
Chat Completions API (tool_ids: ["pm_requirement_tool"])
    │
    ▼
chat_completion() → task model 意图识别
    │
    ▼
选择 Tool: pm_list_requirements(project_id="X")
    │
    ▼
Tool 内部: HTTP GET /api/v1/pm/projects/X/requirements
    │
    ▼
PM API → DB 查询 → 返回需求列表
    │
    ▼
Tool 格式化结果为 Markdown 表格
    │
    ▼
__event_emitter__ 流式推送到前端
    │
    ▼
AI 总结 + 用户看到结果
```

### 1.3 数据流：表单确认导入

```
用户消息: "创建一个新需求：用户登录功能"
    │
    ▼
Tool: pm_create_requirement(project_id, title="用户登录功能")
    │
    ▼
__event_call__({
    "type": "confirmation",
    "data": {
        "title": "确认创建需求",
        "message": "将在项目X中创建需求：\n- 标题：用户登录功能\n- 优先级：P2（默认）\n- 分类：未指定\n\n确认创建？"
    }
})
    │
    ├── 用户确认 → HTTP POST /api/v1/pm/projects/X/requirements → 返回创建结果
    │
    └── 用户取消 → __event_emitter__ notification: "已取消创建"
```

---

## 2. PM Tool 设计

### 2.1 Tool 注册方式

Open WebUI Tool 通过 Python `content` + OpenAPI `specs` 注册：

```python
# 通过 POST /api/v1/tools/create 注册
{
    "id": "pm_requirement_tool",
    "name": "PM 需求管理",
    "content": "<Python source code>",    # Tool 类定义
    "specs": [<OpenAPI function schemas>] # 函数签名
}
```

### 2.2 Tool 类结构

每个 PM 模块对应一个 Tool 类，包含多个 callable 函数：

```python
class Tools:
    def __init__(self):
        self.valves = self.Valves()

    class Valves(BaseModel):
        PM_API_BASE_URL: str = "http://localhost:8080/api/v1/pm"
        PM_API_KEY: str = ""

    # --- 需求管理 ---
    async def pm_list_requirements(
        self,
        project_id: str,
        status: str = "open",
        priority: str = "",
        page: int = 1,
        page_size: int = 20,
        __event_emitter__=None,
    ) -> str:
        """
        列出项目的需求列表
        :param project_id: 项目ID
        :param status: 需求状态 (open/in_progress/resolved/closed)
        :param priority: 优先级筛选 (p0/p1/p2/p3)
        :param page: 页码
        :param page_size: 每页数量
        :return: 需求列表（Markdown 表格）
        """
        ...

    async def pm_create_requirement(
        self,
        project_id: str,
        title: str,
        description: str = "",
        priority: str = "p2",
        __event_emitter__=None,
        __event_call__=None,
    ) -> str:
        """
        创建新需求（需用户确认）
        :param project_id: 项目ID
        :param title: 需求标题
        :param description: 需求描述
        :param priority: 优先级 (p0/p1/p2/p3)
        :return: 创建结果
        """
        # 确认流程
        if __event_call__:
            confirmed = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认创建需求",
                    "message": f"标题: {title}\n优先级: {priority}\n描述: {description or '(无)'}"
                }
            })
            if not confirmed:
                return "用户取消了创建操作"
        ...
```

### 2.3 Tool 分组规划

| Tool ID | 模块 | 函数数量 | 核心函数 |
|---------|------|----------|----------|
| `pm_project_tool` | 项目管理 | 8 | create, list, get, update, delete, archive, export, import |
| `pm_workflow_tool` | 工作流 | 6 | create, get, update, step_update, next, progress |
| `pm_version_tool` | 版本管理 | 6 | create, list, get, switch, compare, rollback |
| `pm_relation_tool` | 关系追溯 | 6 | create, list, delete, confirm, impact, suggest |
| `pm_requirement_tool` | 需求收集 | 6 | create, list, get, update, analyze, import |
| `pm_competitor_tool` | 竞品分析 | 4 | create, list, analyze, research |
| `pm_roadmap_tool` | 路线图 | 4 | create, list, update, gantt |
| `pm_prd_tool` | PRD 编辑 | 7 | create, get, update, generate, export, import, section_update |
| `pm_prd_check_tool` | PRD 检查 | 4 | run, list, update, report |
| `pm_parameter_tool` | 参数清单 | 6 | create, list, get, update, extract, import |
| `pm_testcase_tool` | 测试用例 | 4 | create, list, generate, execute |
| `pm_schedule_tool` | 排期 | 4 | create, list, gantt, update |
| `pm_risk_tool` | 风险管控 | 4 | create, list, update, matrix |
| `pm_deliverable_tool` | 交付物料 | 3 | create, list, check |
| `pm_acceptance_tool` | 验收 | 3 | create, list, check |
| `pm_issue_tool` | 问题闭环 | 4 | create, list, update, link |
| **合计** | | **79** | |

### 2.4 Tool 与 PM API 的映射

每个 Tool 函数内部调用对应的 PM API 端点：

| Tool 函数 | HTTP 调用 |
|-----------|----------|
| `pm_list_requirements(project_id)` | `GET /api/v1/pm/projects/{project_id}/requirements` |
| `pm_create_requirement(project_id, ...)` | `POST /api/v1/pm/projects/{project_id}/requirements` |
| `pm_parameter_extract(prd_id)` | `POST /api/v1/pm/prds/{prd_id}/extract-parameters` |

---

## 3. PM Skill 设计

### 3.1 Skill 注册方式

Skill 是 Markdown 格式的指令集，通过 `POST /api/v1/skills/create` 注册：

```json
{
    "id": "pm-prd-generation",
    "name": "PM PRD 生成",
    "content": "<Markdown instructions>",
    "access_control": null
}
```

### 3.2 核心 Skill 定义

#### Skill 1: PM PRD 生成流程

```markdown
---
name: pm-prd-generation
description: PM PRD 文档生成全流程
---

## PRD 生成流程

当用户需要生成 PRD 时，按以下步骤执行：

1. **确认项目上下文**: 调用 `pm_project_get` 获取当前项目信息
2. **收集需求**: 调用 `pm_list_requirements` 获取已有需求
3. **选择模板**: 询问用户选择 PRD 模板（标准/简洁/详细）
4. **生成大纲**: 基于需求生成 PRD 章节大纲，展示给用户确认
5. **逐章节填充**: 按确认后的大纲，逐章节生成内容
6. **提取参数**: 调用 `pm_parameter_extract` 从生成的 PRD 中提取参数
7. **创建关联**: 调用 `pm_relation_create` 建立需求-PRD-参数的关联
8. **最终确认**: 展示完整 PRD，用户确认后调用 `pm_prd_create` 写入
```

#### Skill 2: PM 需求分析流程

```markdown
---
name: pm-requirement-analysis
description: PM 需求分析和分类流程
---

## 需求分析流程

当用户需要分析需求时，按以下步骤执行：

1. **获取需求列表**: 调用 `pm_list_requirements` 获取项目所有需求
2. **分类建议**: 基于需求内容建议分类和优先级
3. **关联建议**: 调用 `pm_relation_suggest` 建议需求间关联
4. **拆分建议**: 建议是否需要将大需求拆分为子需求
5. **确认**: 用户确认分析结果后更新需求属性
```

#### Skill 3: PM 参数提取流程

```markdown
---
name: pm-parameter-extraction
description: 从 PRD/需求文档提取参数并建立关联
---

## 参数提取流程

1. **选择来源**: 确认从哪个 PRD 或需求文档提取参数
2. **提取参数**: 调用 `pm_parameter_extract` 自动提取
3. **展示预览**: 以表格形式展示提取的参数清单
4. **用户确认**: 用户确认/修改参数
5. **写入参数**: 调用 `pm_parameter_create` 写入
6. **建立关联**: 调用 `pm_relation_create` 建立 PRD-参数关联
```

---

## 4. PM 提示词设计

### 4.1 提示词模板

#### 提示词 1: 产品经理助手

```markdown
---
name: pm-assistant
description: 专业产品经理 AI 助手
---

你是产品经理的 AI 助手，帮助用户完成产品工作流的各个环节。

## 核心规则
1. 所有建议都是建议性的，不强制用户执行
2. 生成内容后，提示用户确认和修改
3. 操作前询问用户，尤其是修改和删除操作
4. 始终读取当前项目上下文再回答

## 可用工具
- 项目管理: pm_project_*
- 需求管理: pm_requirement_*
- PRD 管理: pm_prd_*
- 参数管理: pm_parameter_*
- 测试用例: pm_testcase_*
- 关系追溯: pm_relation_*
- 工作流: pm_workflow_*

## 上下文感知
- 始先确认当前项目 ID
- 使用 pm_project_get 了解项目信息
- 基于项目上下文提供相关建议
```

#### 提示词 2: 需求评审专家

```markdown
---
name: pm-review-expert
description: 需求评审和 PRD 质量检查专家
---

你是需求评审专家，专注于 PRD 质量检查和需求完整性分析。

## 检查维度
1. 内容完整性：需求描述是否充分
2. 逻辑一致性：需求之间是否有矛盾
3. 可测试性：需求是否可验证
4. 关联完整性：需求是否关联了参数和用例

## 工作方式
1. 调用 pm_prd_check_run 执行自动检查
2. 分析检查结果，给出专业建议
3. 调用 pm_relation_suggest 建议补充关联
4. 输出改进建议，用户确认后执行
```

---

## 5. Knowledge 集成设计

### 5.1 PM → Knowledge Base 流程

```
PM 条目数据
    │
    ▼
导出为 Markdown / 纯文本
    │
    ▼
POST /api/v1/knowledge/create → 创建 PM 项目知识库
    │
    ▼
POST /api/v1/knowledge/{id}/file/add → 添加文档文件
    │
    ▼
Chat 中引用 Knowledge base → AI 自动检索 PM 文档
```

### 5.2 数据同步策略

| 策略 | 说明 |
|------|------|
| 按需导出 | 用户手动触发 PM 条目导出到 Knowledge |
| 增量更新 | PM 条目更新时，标记 Knowledge 中对应文件需刷新 |
| 项目知识库 | 每个 PM 项目对应一个 Knowledge base |

---

## 6. 关键技术决策

### 6.1 为什么选择 Tool 而非 Pipe Function

| 方案 | 优势 | 劣势 | 决策 |
|------|------|------|------|
| **Tool** | AI 自动判断调用、OpenAPI specs 标准化、`__event_call__` 支持确认 | 需要后端 API | ✅ 选择 |
| Pipe Function | 可自定义模型行为 | 不适合 CRUD 操作、无确认机制 | ❌ |
| Filter Function | 可拦截请求注入上下文 | 只能修改请求/响应，不能新增功能 | 辅助 |
| Action Function | 消息下方按钮 | 触发方式受限 | 辅助 |

### 6.2 表单确认方案

- **简单确认**: `__event_call__` 的 `confirmation` 类型 → 是/否
- **参数收集**: `__event_call__` 的 `input` 类型 → 文本输入
- **复杂表单**: 多次 `input` 调用逐步收集 + 最终 `confirmation` 确认
- **预览确认**: AI 生成内容 → Markdown 展示 → `confirmation` 确认写入

### 6.3 项目隔离方案

- Tool Valves 配置 `PM_API_BASE_URL`
- 每个 Tool 函数强制要求 `project_id` 参数
- PM API 后端验证 `project_id` 权限
- Tool 不缓存跨项目数据

---

## 7. 文件结构

```
backend/open_webui/
├── routers/
│   └── pm/                          # PM API 路由（已有）
│       ├── project.py
│       ├── requirement.py
│       ├── prd.py
│       ├── parameter.py
│       └── ...
├── tools/                           # PM Tool 定义（新增）
│   ├── pm_project_tool.py
│   ├── pm_requirement_tool.py
│   ├── pm_prd_tool.py
│   ├── pm_parameter_tool.py
│   ├── pm_testcase_tool.py
│   ├── pm_workflow_tool.py
│   ├── pm_relation_tool.py
│   └── ...
└── skills/                          # PM Skill 定义（新增）
    ├── pm_prd_generation.md
    ├── pm_requirement_analysis.md
    └── pm_parameter_extraction.md
```

---

## 8. 兼容性与风险

### 8.1 Open WebUI 升级兼容

- Tool / Skill / Prompt 通过 API 注册，不修改核心代码
- 升级 Open WebUI 后 Tool 仍在数据库中保留
- 需注意 Open WebUI API 版本变更

### 8.2 性能风险

- 16 个 Tool 注册 × 平均 5 函数 = ~79 个 callable → task model 意图识别可能延迟
- 缓解：按模块分组 Tool，对话中只加载当前项目相关的 Tool（`tool_ids` 限定）

### 8.3 安全风险

- Tool 内调用 PM API 需鉴权（API Key via Valves）
- `project_id` 参数防注入
- 确认机制防止误操作
+page.svelte (PRD Editor Page)
├── PMRichEditor.svelte (Rich Text Editor)
│   ├── PMTableOfContents.svelte (TOC Sidebar - left)
│   └── PMAnnotationPanel.svelte (Annotation Sidebar - right)
└── ...
```

## 变更范围

### 1. PRD 章节侧边栏移除

**影响文件：**
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**需要移除的代码：**
- `editingSections` state
- `editingActiveSection` state  
- `defaultSections` constant
- `sectionTypeLabels` constant
- `switchPrdSection()` function
- PRD 章节侧边栏的 Svelte 模板（第1816-1839行）
- PRD 保存逻辑中的 sections 处理
- `openEntryEditor` 中的 PRD sections 初始化

**数据格式变更：**
- 当前 PRD 数据格式：`{ sections: PRDSection[], versionId: string }`
- 新 PRD 数据格式：直接使用 `content` 字段，不再分章节存储
- 向后兼容：读取时如果存在 sections，合并为 content

### 2. 批注功能增强

**影响文件：**
- `src/lib/components/pm/PMAnnotationPanel.svelte`
- `src/lib/components/pm/PMRichEditor.svelte`

**PMAnnotationPanel 增强：**
- 保持现有 UI 结构
- 确保 `onAnnotationClick` 正确滚动到编辑器位置
- 确保 `onAiModify` 可以编辑批注内容
- 确保 `onAnnotationRemove` 可以删除批注

**PMRichEditor 调整：**
- 批注面板通过 `annotationPanelVisible` 状态控制显示
- 批注数据通过 props 传入，通过 `onAnnotationsChange` 回调更新
- 选择文本时显示浮动"批注"按钮
- 点击批注列表项时滚动到对应位置

## 数据流

### 批注数据流
```
User selects text → clicks "批注" button
  → PMRichEditor.addAnnotation()
  → creates EntryAnnotation
  → onAnnotationsChange([...annotations, newAnnotation])
  → Parent component updates state
  → PMAnnotationPanel re-renders with new list

User clicks annotation in panel
  → onAnnotationClick(annotation)
  → editor.commands.setTextSelection()
  → editor.commands.scrollIntoView()
```

## 兼容性

- PRD 数据格式变更需要向后兼容：读取旧数据时合并 sections
- 批注功能不影响现有数据结构
- TOC 目录功能不受影响

## 回滚策略

- 所有变更都是前端 UI 层面
- 数据格式变更支持向后兼容读取
- 如需回滚，恢复代码即可，数据不受影响
