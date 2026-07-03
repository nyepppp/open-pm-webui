# Data Model: PM 工作台增强 v2

**Created**: 2026-06-29

---

## 1. 新增实体

### 1.1 EntryVersion（条目版本）

每个条目每次保存时创建一个版本快照。

```typescript
interface EntryVersion {
  id: string;                    // 主键
  entryId: string;               // 关联的模块条目 ID
  projectId: string;             // 项目 ID（用于查询隔离）
  moduleType: string;            // 模块类型（prd, requirement 等）
  versionNumber: string;         // 版本号（v1.0, v1.1）
  content: string;               // TipTap JSON 内容快照
  metadata: Record<string, any>; // 表单字段快照（title, status, priority 等结构化数据）
  parentId: string | null;       // 上一版本 ID
  branchName: string;            // 分支名（默认 "main"）
  changeSummary: string;         // 变更摘要
  createdBy: string;             // 创建者
  createdAt: number;             // 创建时间戳
}
```

**索引**:
- `idx_entry_versions_entry_id` on `entry_id, created_at DESC`
- `idx_entry_versions_branch` on `entry_id, branch_name`

### 1.2 VersionBranch（版本分支）

```typescript
interface VersionBranch {
  id: string;                    // 主键
  projectId: string;             // 项目 ID
  entryId: string;               // 关联条目 ID
  name: string;                  // 分支名
  sourceVersionId: string;       // 从哪个版本分叉
  status: 'active' | 'merged' | 'archived';
  mergedToVersionId: string | null; // 合并到主线的版本 ID
  createdAt: number;
  updatedAt: number;
}
```

### 1.3 VersionMerge（版本合并）

```typescript
interface VersionMerge {
  id: string;                    // 主键
  branchId: string;              // 关联分支
  sourceVersionId: string;       // 分支最新版本
  targetVersionId: string;       // 主线目标版本
  conflicts: ConflictItem[];     // 冲突列表
  status: 'pending' | 'resolved' | 'auto_merged';
  resolvedBy: string | null;
  mergedAt: number | null;
  createdAt: number;
}

interface ConflictItem {
  path: string;                  // 内容路径（如 "content.paragraphs[3]" 或 "metadata.status"）
  type: 'content' | 'metadata'; // 冲突类型
  sourceValue: any;              // 分支值
  targetValue: any;              // 主线值
  resolution: 'source' | 'target' | 'manual' | null;
  resolvedValue: any | null;
}
```

### 1.4 ScheduleSync（日程同步）

```typescript
interface ScheduleSync {
  id: string;                    // 主键
  pmEntityType: string;          // 'roadmap' | 'risk' | 'schedule'
  pmEntityId: string;            // PM 条目 ID
  pmProjectId: string;           // PM 项目 ID
  calendarEventId: string;       // OpenWebUI 日历事件 ID
  calendarId: string;            // 日历 ID
  syncStatus: 'synced' | 'pending' | 'failed';
  lastSyncedAt: number;
  createdAt: number;
}
```

---

## 2. 修改的实体

### 2.1 ModuleEntry（已有，新增字段）

```typescript
// 在现有 ModuleEntry 基础上新增：
interface ModuleEntry {
  // ...existing fields...
  currentVersionId: string | null;  // 当前版本 ID（指向 EntryVersion）
  currentVersionNumber: string;     // 当前版本号（冗余，用于列表快速显示）
  branchName: string;               // 当前分支（默认 "main"）
}
```

---

## 3. 溯源图交互数据流

### 3.1 TraceLink 操作

```typescript
// 连线创建关联（溯源图中拖拽连线）
interface TraceLinkCreate {
  sourceEntityId: string;
  sourceEntityType: string;      // 模块类型
  targetEntityId: string;
  targetEntityType: string;
  relationType: 'contains' | 'references' | 'derives' | 'modifies' | 'conflicts';
  confidence: number;            // 100（手动创建）
  confirmed: true;               // 手动创建默认已确认
}

// 溯源图节点数据（扩展当前 PMTraceabilityGraph）
interface TraceNode extends Node {
  data: {
    entityId: string;
    entityType: string;
    entityTitle: string;
    moduleType: string;
    versionNumber: string;
  };
}

// 溯源图边数据（扩展当前 Edge）
interface TraceEdge extends Edge {
  data: {
    relationId: string;
    relationType: string;
    confirmed: boolean;
    confidence: number;
  };
}
```

---

## 4. 甘特图数据格式

### 4.1 GanttTask（统一格式）

```typescript
interface GanttTask {
  id: string;
  name: string;
  start: string;                 // ISO date string
  end: string;                   // ISO date string
  progress: number;              // 0-100
  dependencies: string;          // 逗号分隔的依赖 ID
  custom_class?: string;         // CSS 类名（用于样式区分）
  // PM 扩展字段
  pmEntityType: string;
  pmEntityId: string;
  status: string;
}
```

---

## 5. 思维导图数据格式

### 5.1 MindMapData（与 mind-elixir 兼容）

```typescript
interface MindMapData {
  nodeData: {
    id: string;
    topic: string;
    children: MindMapData[];
    style?: Record<string, any>;
    // PM 扩展
    pmEntityType?: string;
    pmEntityId?: string;
  };
  linkData?: any[];
}
```

---

## 6. 数据库迁移

### 6.1 新增表

- `pm_entry_versions` — EntryVersion
- `pm_version_branches` — VersionBranch  
- `pm_version_merges` — VersionMerge
- `pm_schedule_syncs` — ScheduleSync

### 6.2 修改表

- `pm_module_entries` — 新增 `current_version_id`, `current_version_number`, `branch_name` 列

### 6.3 数据迁移

- 现有条目自动创建初始 EntryVersion（versionNumber: "v1.0", branchName: "main"）
