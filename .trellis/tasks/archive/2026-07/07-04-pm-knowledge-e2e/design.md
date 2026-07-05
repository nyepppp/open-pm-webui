# Knowledge 集成与端到端验证 - 技术设计

**日期**: 2026-07-04  
**状态**: 规划中

---

## 1. PM → Knowledge Base 导出

### 1.1 导出流程

```
PM 项目页面 → "导出到知识库" 按钮
    │
    ▼
前端调用: POST /api/v1/pm/knowledge/export
    │
    ▼
后端处理:
    1. 查询项目所有条目（需求、PRD、参数、测试用例等）
    2. 每个 PM 模块导出为一个 Markdown 文件
    3. 检查是否已有该项目的 Knowledge base
       - 无 → POST /api/v1/knowledge/create 创建
       - 有 → 复用现有 Knowledge base
    4. 对每个导出文件:
       - 新文件 → POST /api/v1/knowledge/{id}/file/add
       - 已有文件 → DELETE 旧文件 + ADD 新文件（全量替换）
    5. 返回导出结果（文件数、Knowledge base ID）
```

### 1.2 导出格式

每个 PM 模块生成一个结构化 Markdown 文件：

```markdown
# 项目: {项目名称} - 需求列表

| ID | 标题 | 优先级 | 状态 | 分类 | 创建时间 |
|----|------|--------|------|------|----------|
| req-001 | 用户登录 | P1 | 进行中 | 功能 | 2026-07-01 |
| req-002 | 密码重置 | P2 | 待处理 | 功能 | 2026-07-02 |

---

## 需求详情: req-001 用户登录

**描述**: 支持邮箱+密码登录方式
**优先级**: P1
**状态**: 进行中
**关联参数**: param-001 (登录邮箱), param-002 (登录密码)
**关联测试用例**: tc-001, tc-002
```

### 1.3 增量更新策略

```
PM 条目变更（创建/更新/删除）
    │
    ▼
后端标记: knowledge_status = 'dirty'
    │
    ▼
用户下次点击"同步知识库" → 只刷新 dirty 的文件
    │
    ▼
同步完成 → knowledge_status = 'synced'
```

| 字段 | 说明 |
|------|------|
| `knowledge_status` | PM 项目表新增字段：`synced` / `dirty` / `none` |
| `knowledge_base_id` | 关联的 Open WebUI Knowledge base ID |

### 1.4 API 端点

```
POST /api/v1/pm/projects/{project_id}/knowledge/export
  → 导出项目所有条目到 Knowledge base

POST /api/v1/pm/projects/{project_id}/knowledge/sync
  → 增量同步 dirty 条目

GET /api/v1/pm/projects/{project_id}/knowledge/status
  → 查询同步状态
```

---

## 2. Knowledge 检索集成

### 2.1 对话中引用 Knowledge

用户在 Chat 中通过 `#` 命令选择 PM 项目 Knowledge base：

```
用户: "帮我看看 #PM-项目A 项目有哪些未完成的需求"
           ↑ 选择 Knowledge base
```

AI 使用 RAG 检索 Knowledge 中的 PM 文档内容，结合 Tool 调用获取最新数据。

### 2.2 来源标注

Knowledge 检索结果通过 `__event_emitter__` 的 `citation` 事件标注来源：

```python
await __event_emitter__({
    "type": "citation",
    "data": {
        "document": ["PM-项目A-需求列表.md"],
        "metadata": [{"source": "requirement", "id": "req-001"}],
        "content": "..."
    }
})
```

---

## 3. 端到端验证方案

### 3.1 验证环境

- Docker Compose 部署完整 Open WebUI + PM 后端
- 至少配置一个 AI 模型（Ollama 或 OpenAI-compatible）
- 创建测试项目 + 预置测试数据

### 3.2 场景验证脚本

使用 pytest + httpx 编写自动化验证：

```python
# test_e2e_agent.py

async def test_requirement_query(client, project_id):
    """场景2: 需求列表查询"""
    response = await client.post("/api/chat/completions", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "项目X有哪些需求？"}],
        "tool_ids": ["pm_requirement_tool"]
    })
    # 验证 AI 调用了 pm_list_requirements
    # 验证返回内容包含需求表格

async def test_requirement_create_with_confirmation(client, project_id):
    """场景3: 需求创建（含确认）"""
    # 模拟 __event_call__ confirmation 流程
    ...

async def test_prd_generation_skill(client, project_id):
    """场景4: PRD 生成 Skill"""
    ...

async def test_parameter_extraction(client, prd_id):
    """场景5: 参数提取"""
    ...

async def test_relation_creation(client, project_id):
    """场景6: 关联建立"""
    ...

async def test_knowledge_retrieval(client, knowledge_id):
    """场景7: Knowledge 检索"""
    ...

async def test_excel_import(client, project_id):
    """场景8: 数据导入"""
    ...
```

### 3.3 集成回归检查

```python
# test_integration.py

async def test_all_tools_callable(client):
    """验证所有 16 个 Tool 可正常调用"""
    tools = await client.get("/api/v1/tools/")
    pm_tools = [t for t in tools if t["id"].startswith("pm_")]
    assert len(pm_tools) == 16

async def test_all_skills_available(client):
    """验证 3 个 Skill 可正常触发"""
    skills = await client.get("/api/v1/skills/")
    pm_skills = [s for s in skills if s["id"].startswith("pm-")]
    assert len(pm_skills) >= 3

async def test_project_isolation(client, project_a, project_b):
    """验证项目隔离"""
    # 在项目 A 对话中查询，不应返回项目 B 数据
    ...
```

---

## 4. 文件结构变更

```
backend/open_webui/
├── routers/
│   └── pm/
│       └── knowledge.py               # 新增：Knowledge 导出 API
├── utils/
│   └── pm_knowledge_export.py         # 新增：PM → Markdown 导出工具
tests/
└── e2e/
    ├── test_e2e_agent.py               # 新增：8 个端到端场景测试
    └── test_integration.py            # 新增：集成回归测试
```

---

## 5. 风险与缓解

| 风险 | 缓解 |
|------|------|
| Knowledge 导出大项目时 token 消耗高 | 分模块导出，按需选择模块 |
| RAG 检索精度不足 | 优化 Markdown 结构化标签，增加 metadata |
| E2E 测试依赖 AI 模型可用性 | Mock 模式：拦截 Tool 调用返回预设结果 |
| Open WebUI API 变更 | Knowledge API 已稳定（v0.3+），低风险 |
