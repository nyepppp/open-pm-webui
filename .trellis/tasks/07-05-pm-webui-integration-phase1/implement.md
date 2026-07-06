# Implementation Plan: PM工作台集成Open WebUI对话系统（第一阶段）

## Phase 1: PM 数据 API 层 (A)

### A1: 扩展 PM API
- [ ] **A1.1**: 在 `backend/open_webui/models/pm.py` 添加 PMAnnotation 模型
  - 文件: `backend/open_webui/models/pm.py`
  - 新增: `PMAnnotation` 类
  - 新增: `PMAnnotationForm` Pydantic 模型
  - 新增: `PMAnnotations` CRUD 操作类

- [ ] **A1.2**: 在 `backend/open_webui/routers/pm.py` 添加标注 API 路由
  - 新增: `GET /pm/annotations` - 查询标注列表
  - 新增: `POST /pm/annotations` - 创建标注
  - 新增: `GET /pm/annotations/{annotation_id}` - 获取单个标注
  - 新增: `PUT /pm/annotations/{annotation_id}` - 更新标注
  - 新增: `DELETE /pm/annotations/{annotation_id}` - 删除标注
  - 新增: `GET /pm/entries/{entry_id}/annotations` - 获取条目标注
  - 新增: `POST /pm/entries/{entry_id}/generate-annotation` - 生成标注文本

- [ ] **A1.3**: 数据库迁移
  - 创建 Alembic 迁移文件
  - 新增 `pm_annotation` 表

### A2: 数据关联和引用
- [ ] **A2.1**: 实现条目与标注的关联查询
  - 在 `PMEntries` 类中添加 `get_entry_annotations` 方法
  - 在 `PMAnnotations` 类中添加 `get_by_entry_id` 方法

- [ ] **A2.2**: 实现标注内容格式化
  - 支持 Markdown 格式
  - 支持模板变量替换

## Phase 2: AI 工具/技能封装 (C)

### C1: 封装 PM 数据查询工具
- [ ] **C1.1**: 创建 `backend/open_webui/tools/pm_annotation_tool.py`
  - `generate_annotation`: 基于条目数据生成标注文本
  - `save_annotation`: 保存标注到数据库
  - `list_annotations`: 查询标注列表
  - `copy_annotation`: 复制标注内容

- [ ] **C1.2**: 增强 `backend/open_webui/tools/pm_entry_tool.py`
  - 添加 `get_entry_with_annotations` 方法
  - 添加 `search_entries_fulltext` 方法

### C2: 封装标注生成工具
- [ ] **C2.1**: 实现标注文本生成逻辑
  - 基于条目数据生成结构化文本
  - 支持多种标注类型（原型、需求、SPEC）
  - 支持自定义格式模板

- [ ] **C2.2**: 实现一键复制功能
  - 生成带格式文本（Markdown）
  - 支持复制到剪贴板

### C3: 注册工具到 Open WebUI
- [ ] **C3.1**: 在 `backend/open_webui/tools/__init__.py` 注册新工具
- [ ] **C3.2**: 测试工具在对话中的调用

## Phase 3: 对话入口改造 (B)

### B1: 对话输入框集成
- [ ] **B1.1**: 在 `src/lib/components/chat/MessageInput.svelte` 添加 PM 工具按钮
  - 添加 "引用 PM 数据" 按钮
  - 点击打开 PM 数据选择器

- [ ] **B1.2**: 创建 `src/lib/components/pm/PMAnnotationSelector.svelte`
  - 项目选择器
  - 模块类型过滤
  - 条目列表
  - 搜索功能

### B2: 对话消息展示
- [ ] **B2.1**: 创建 `src/lib/components/pm/PMDataCard.svelte`
  - 条目摘要卡片
  - 详情展开
  - 复制按钮

- [ ] **B2.2**: 在消息渲染中集成 PM 数据卡片
  - 修改 `src/lib/components/chat/Messages.svelte`
  - 支持渲染 PM 数据引用

### B3: 对话历史持久化
- [ ] **B3.1**: 修改消息存储逻辑
  - 在消息元数据中保存 PM 引用信息
  - 支持历史对话中重新加载引用

## Validation Commands

### Backend
```bash
# Run database migration
python -m alembic upgrade head

# Test PM API
curl http://localhost:8080/api/v1/pm/annotations

# Test tool registration
python -c "from open_webui.tools.pm_annotation_tool import Tools; print('OK')"
```

### Frontend
```bash
# Build frontend
npm run build

# Run tests
npm run test
```

### Integration
```bash
# Start development server
npm run dev

# Test chat with PM tools
# 1. Open chat
# 2. Click PM tool button
# 3. Select entry
# 4. Verify reference in chat
```

## Risky Files

1. `backend/open_webui/models/pm.py` - Core data model, changes affect all PM features
2. `backend/open_webui/routers/pm.py` - API routes, changes affect frontend
3. `src/lib/components/chat/MessageInput.svelte` - Critical chat component
4. `backend/open_webui/tools/__init__.py` - Tool registry

## Rollback Points

1. **Before A1.3 (Migration)**: Can rollback by reverting model changes
2. **Before C3.1 (Tool Registration)**: Can rollback by removing tool file
3. **Before B1.1 (Frontend Changes)**: Can rollback by reverting frontend changes

## Follow-up Checks

- [ ] All new API endpoints return correct data format
- [ ] Tools are registered and callable in chat
- [ ] Frontend components render correctly
- [ ] Copy-to-clipboard works for annotations
- [ ] Database migration is reversible
