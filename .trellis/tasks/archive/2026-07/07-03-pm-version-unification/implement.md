# PM模块版本信息统一 - 执行计划

## 执行步骤

### 步骤1：Bug 1 — Auto-create entry version on entry creation

**目标**：创建条目时自动创建初始 v1 entry version。

**具体任务**：
1. `routers/pm.py` — `create_entry` endpoint：在 auto-entity try/except 之后添加 auto-version try/except
   - `PMEntryVersionForm(entry_id, project_id, module_type, version_number='v1', content, entry_metadata, change_summary='Initial version')`
   - `await PMEntryVersions.insert_new_version(user.id, version_form, db=db)`
   - 非阻塞：try/except + warning log
2. `routers/pm.py` — `create_entry` response：enrich 返回的 PMEntryModel with `current_version_number='v1'`
3. `models/pm.py` — `PMEntryModel`：添加 `current_version_number: Optional[str] = None` 和 `branch_name: Optional[str] = None`

**验收**：AC-1.1, AC-1.2, AC-1.3

### 步骤2：Bug 2 — Link entry versions to project versions

**目标**：project version snapshot 创建时正确设置 `project_version_id`，查询时使用该列。

**具体任务**：
1. `routers/pm.py` — `create_project_version_snapshot`：`PMEntryVersionForm` 使用 `project_version_id=version_id` 替代 metadata 嵌入
2. `routers/pm.py` — `get_project_version_entries`：使用 `PMEntryVersions.get_versions_by_project_version_id` 替代 JSON 字段扫描
3. `models/pm.py` — 新增 `PMEntryVersions.get_versions_by_project_version_id` 静态方法
4. `models/pm.py` — 新增 `PMEntryVersions.get_latest_version_by_entry_id` 静态方法
5. `models/pm.py` — 添加 `PMEntryVersions = PMEntryVersions()` 单例

**验收**：AC-2.1, AC-2.2

### 步骤3：Bug 3 — Unify version info column

**目标**：所有表格模块统一显示版本信息列。

**具体任务**：
1. `+page.svelte` — `moduleConfig` tableColumns：
   - requirement, parameter, testcase, prototype, schedule：添加 `{ key: 'currentVersionNumber', label: '版本', width: 'w-20' }` 在 status 列之前
   - roadmap：将 `versionId` 替换为 `currentVersionNumber`
2. `+page.svelte` — 表格渲染：添加 `currentVersionNumber` 列的渲染逻辑（版本号 + 分支指示器）
3. `+page.svelte` — 移除硬编码的"版本"列（table header 中的独立 th）
4. `routers/pm.py` — `get_entries`：enrich 返回的 entries with `current_version_number` 和 `branch_name`

**验收**：AC-3.1, AC-3.2, AC-3.3

### 步骤4：验证

**验证命令**：
- 后端：确认 `create_entry` 自动创建 v1 entry version
- 后端：确认 `create_project_version_snapshot` 设置 `project_version_id`
- 后端：确认 `get_project_version_entries` 使用新查询
- 前端：确认所有表格模块显示版本列
- 前端：确认版本列在 status 列之前

## 依赖关系

```
步骤1 (auto-version) ─┐
步骤2 (version link) ──┼── 步骤3 (UI column) ── 步骤4 (验证)
步骤1 需要 PMEntryModel 新字段 ─┘
```

## 回滚策略

- 所有修改为增量性，无 schema 迁移
- 回滚：git revert 3 个文件 (routers/pm.py, models/pm.py, +page.svelte)
- Auto-version 创建为非阻塞，失败不影响 entry 创建

## 修改文件清单

- `backend/open_webui/models/pm.py` — PMEntryModel 新字段、PMEntryVersions 新方法 + 单例
- `backend/open_webui/routers/pm.py` — create_entry auto-version、get_entries enrichment、get_project_version_entries 修复、create_project_version_snapshot 修复
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` — moduleConfig 版本列 + 渲染逻辑
