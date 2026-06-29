# PM 模块开发者指南

> 如何扩展和维护 PM 工作台的模块系统

## 架构概览

```
src/
├── lib/
│   ├── components/pm/          # UI 组件
│   ├── apis/pm/                # API 层
│   │   ├── modules/            # 各模块 API
│   │   ├── index.ts            # HTTP 客户端
│   │   ├── types.ts            # TypeScript 类型
│   │   ├── agent.ts            # Agent API + 错误分类
│   │   ├── version.ts          # 版本管理 API
│   │   └── relation.ts         # 关联管理 API
│   └── stores/pm/              # Svelte stores
├── routes/(app)/pm/            # 路由页面
└── docs/pm-workspace.md        # 用户文档
```

## 添加新模块

### 1. 定义类型

在 `src/lib/apis/pm/types.ts` 中：

```typescript
// 1. 添加到 ModuleType 联合类型
export type ModuleType = 'prd' | ... | 'your-module';

// 2. 定义模块特定接口
export interface YourModule {
  field1: string;
  field2?: number;
}

// 3. 如有新状态，更新 ModuleStatus
```

### 2. 创建模块 API

在 `src/lib/apis/pm/modules/` 下创建 `your-module.ts`：

```typescript
import { getList, getOne, create, update, remove } from '../index';
import type { ModuleEntry, ApiResponse, PaginatedResponse } from '../types';

export function getYourModuleEntries(projectId: string, versionId?: string) {
  return getList<ModuleEntry>(`/projects/${projectId}/modules/your-module`,
    versionId ? { versionId } : undefined);
}

export function createYourModuleEntry(projectId: string, data: Partial<ModuleEntry>) {
  return create<ModuleEntry>(`/projects/${projectId}/modules/your-module`, data);
}
// ... 其他 CRUD 方法
```

### 3. 定义表单字段

在 `src/lib/components/pm/moduleFields.ts` 中：

```typescript
export const yourModuleFields: FieldConfig[] = [
  { name: 'title', label: '标题', type: 'text', required: true, placeholder: '输入标题' },
  { name: 'status', label: '状态', type: 'select', required: true, options: ['草稿', '评审中'] },
];

// 在 moduleEditorTypes 中映射编辑器类型
export const moduleEditorTypes = {
  ...existingTypes,
  'your-module': 'form'  // 'rich' | 'form' | 'mixed' | 'mindmap'
};

// 在 getModuleFields 中添加 case
export function getModuleFields(moduleType: string): FieldConfig[] {
  switch (moduleType) {
    // ... existing cases
    case 'your-module': return yourModuleFields;
  }
}
```

### 4. 添加到导航分类

在 `src/lib/stores/pm/moduleStore.ts` 的 `moduleCategories` 中添加：

```typescript
{
  id: 'planning', // 或其他分类
  label: '规划',
  icon: 'Map',
  modules: [
    // ... 现有模块
    { id: 'your-module', label: '你的模块', icon: 'FileText', path: '/pm/your-module' }
  ]
}
```

### 5. 路由自动生效

`src/routes/(app)/pm/[module]/+page.svelte` 使用动态路由，新模块自动获得页面。

## 编辑器类型选择

| 编辑器 | 适用场景 | 组件 |
|--------|---------|------|
| `rich` | 文档型内容（PRD、竞品分析等） | `PMRichEditor.svelte` |
| `form` | 结构化数据（需求、参数、测试用例） | `PMFormEditor.svelte` |
| `mixed` | 表单 + 描述（风险） | `PMMixedEditor.svelte` |
| `mindmap` | 可视化层级（路线图、产品架构） | `PMMindMap.svelte` |

## Store 开发规范

所有 PM stores 位于 `src/lib/stores/pm/`：

- **命名**: `{domain}Store.ts`（如 `projectStore.ts`）
- **导出**: writable store + derived stores + action 函数
- **模式**: 参考 `agentStore.ts` 的错误处理模式

```typescript
// 典型 store 结构
export const items = writable<Item[]>([]);
export const loading = writable<boolean>(false);
export const error = writable<string | null>(null);

export const itemCount = derived(items, $items => $items.length);

export function setItems(newItems: Item[]) { items.set(newItems); }
export function setItemLoading(l: boolean) { loading.set(l); }
export function setItemError(e: string | null) { error.set(e); }
```

## API 层规范

- 使用 `src/lib/apis/pm/index.ts` 中的通用 CRUD 函数
- 所有 API 函数返回 `ApiResponse<T>` 类型
- 错误分类参考 `agent.ts` 的 `classifyAIError` 模式

## 性能注意事项

1. **列表渲染**: 超过 100 条目时使用虚拟滚动（见 `PMItemEditor.svelte`）
2. **富文本**: 大文档（>50,000 字符）自动防抖、禁用历史
3. **思维导图**: 超过 200 节点启用视口过滤
4. **图片/附件**: 按项目隔离存储于 `data/projects/{projectId}/`

## 错误处理模式

1. **组件级**: try-catch + 降级 UI（参考 `PMRichEditor` 的 fallback textarea）
2. **API 级**: 错误分类 + 用户友好消息（参考 `agent.ts` 的 `classifyAIError`）
3. **Store 级**: error store + 组件自动响应

## 无障碍规范

- 所有 `<button>` 必须有 `aria-label`（图标按钮必须）
- 对话框必须 `role="dialog"` + `aria-modal="true"`
- 列表必须 `role="list"` / `role="listbox"`
- 导航区域需要键盘支持（参考 `PMModuleNav` 的 keydown 处理）
- 装饰性 SVG 添加 `aria-hidden="true"`
