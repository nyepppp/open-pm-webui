<script lang="ts">
  /**
   * OperationPreviewModal - AI 操作预览弹窗（Bug 9 / v10）
   *
   * 在 AI agent 提议 create / update / delete 操作时弹出，
   * 展示 before/after diff（D94），让用户确认后再执行。
   *
   * - create: 只展示 after（新字段值），绿色"确认创建"
   * - update: 展示 before → after 每个字段对比，黄色"确认更新"
   * - delete: 展示 before（被删除条目的内容摘要），红色"确认删除"
   */

  export interface OperationPreviewData {
    type: 'create' | 'update' | 'delete';
    module_type: string;
    entry_id?: string;
    entry_title?: string;
    before?: Record<string, unknown>;
    after?: Record<string, unknown>;
    is_dangerous: boolean;
    message?: string;
    confirmation_token?: string;
  }

  interface Props {
    isOpen?: boolean;
    operation?: OperationPreviewData | null;
    onconfirm?: (op: OperationPreviewData) => void;
    oncancel?: (op: OperationPreviewData) => void;
  }

  let {
    isOpen = false,
    operation = null,
    onconfirm,
    oncancel
  }: Props = $props();

  // Styling per operation type
  const typeConfig = $derived(
    operation
      ? {
          create: {
            label: '创建条目',
            color: 'green',
            border: 'border-green-300',
            bg: 'bg-green-50',
            headerBg: 'bg-green-100',
            iconColor: 'text-green-600',
            btnClass: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
            icon: 'M12 4v16m8-8H4'
          },
          update: {
            label: '更新条目',
            color: 'yellow',
            border: 'border-yellow-300',
            bg: 'bg-yellow-50',
            headerBg: 'bg-yellow-100',
            iconColor: 'text-yellow-600',
            btnClass: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
            icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z'
          },
          delete: {
            label: '删除条目',
            color: 'red',
            border: 'border-red-300',
            bg: 'bg-red-50',
            headerBg: 'bg-red-100',
            iconColor: 'text-red-600',
            btnClass: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
            icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16'
          }
        }[operation.type]
      : null
  );

  // Collect all field keys from before+after for diff rendering
  const diffFields = $derived.by(() => {
    if (!operation) return [];
    const before = operation.before || {};
    const after = operation.after || {};
    const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
    // Skip noisy internal fields
    const skipKeys = new Set(['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'version_number']);
    return Array.from(keys)
      .filter((k) => !skipKeys.has(k))
      .sort();
  });

  function formatValue(v: unknown): string {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'string') return v.length > 200 ? v.slice(0, 200) + '…' : v;
    if (typeof v === 'object') return JSON.stringify(v, null, 2).slice(0, 400);
    return String(v);
  }

  function handleConfirm() {
    if (operation) onconfirm?.(operation);
  }

  function handleCancel() {
    if (operation) oncancel?.(operation);
  }
</script>

{#if isOpen && operation && typeConfig}
  <div
    class="fixed inset-0 bg-gray-900 bg-opacity-60 overflow-y-auto h-full w-full z-50"
    role="dialog"
    aria-modal="true"
    aria-labelledby="op-preview-title"
  >
    <div class="flex items-center justify-center min-h-screen px-4 py-6">
      <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full {typeConfig.border} border-2 max-h-[90vh] flex flex-col">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200 {typeConfig.headerBg} rounded-t-lg">
          <div class="flex items-center gap-3">
            <div class="flex-shrink-0">
              <svg class="h-6 w-6 {typeConfig.iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={typeConfig.icon} />
              </svg>
            </div>
            <h3 id="op-preview-title" class="text-lg font-semibold text-gray-900">
              {typeConfig.label} · 预览确认
            </h3>
          </div>
        </div>

        <!-- Body (scrollable) -->
        <div class="px-6 py-4 overflow-y-auto flex-1">
          {#if operation.message}
            <p class="text-sm text-gray-700 mb-4">{operation.message}</p>
          {/if}

          <!-- Entry meta info -->
          <div class="bg-gray-100 rounded-md p-3 text-sm space-y-1 mb-4">
            {#if operation.entry_title}
              <div class="flex justify-between gap-3">
                <span class="text-gray-500 flex-shrink-0">条目标题:</span>
                <span class="font-medium text-gray-900 text-right">{operation.entry_title}</span>
              </div>
            {/if}
            <div class="flex justify-between gap-3">
              <span class="text-gray-500 flex-shrink-0">模块类型:</span>
              <span class="font-medium text-gray-900">{operation.module_type}</span>
            </div>
            {#if operation.entry_id}
              <div class="flex justify-between gap-3">
                <span class="text-gray-500 flex-shrink-0">条目 ID:</span>
                <span class="font-mono text-xs text-gray-600 break-all">{operation.entry_id}</span>
              </div>
            {/if}
          </div>

          <!-- Danger warning for delete -->
          {#if operation.is_dangerous}
            <div class="mb-4 p-3 bg-red-100 border border-red-200 rounded-md">
              <p class="text-xs text-red-700">
                <strong>警告:</strong> 此操作不可撤销。删除的数据将无法恢复。
              </p>
            </div>
          {/if}

          <!-- Diff section -->
          {#if diffFields.length > 0}
            <div class="mb-2">
              <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {operation.type === 'create' ? '将创建的字段' : operation.type === 'delete' ? '将被删除的字段' : '字段变更对比'}
              </h4>
              <div class="border border-gray-200 rounded-md divide-y divide-gray-100">
                {#each diffFields as field (field)}
                  {@const beforeVal = operation.before?.[field]}
                  {@const afterVal = operation.after?.[field]}
                  {@const changed = operation.type === 'update' && beforeVal !== afterVal}
                  <div class="px-3 py-2 grid grid-cols-12 gap-2 items-start text-xs">
                    <div class="col-span-3 font-mono text-gray-600 break-all">{field}</div>
                    {#if operation.type !== 'create'}
                      <div class="col-span-4 text-gray-500 break-words">
                        {#if changed}<span class="line-through">{formatValue(beforeVal)}</span>{:else}{formatValue(beforeVal)}{/if}
                      </div>
                      <div class="col-span-1 text-center text-gray-400">{#if changed}→{/if}</div>
                      <div class="col-span-4 {changed ? 'text-green-700 font-medium bg-green-50 -mx-1 px-1 rounded' : 'text-gray-900'} break-words">
                        {formatValue(afterVal)}
                      </div>
                    {:else}
                      <div class="col-span-9 text-gray-900 break-words">
                        {formatValue(afterVal)}
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
          {:else if operation.type === 'delete'}
            <div class="text-xs text-gray-500 italic">无字段详情可展示（仅条目元信息）。</div>
          {/if}
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-end gap-3 border-t border-gray-200">
          <button
            class="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            onclick={handleCancel}
          >
            取消
          </button>
          <button
            class="px-4 py-2 rounded-md text-sm font-medium text-white {typeConfig.btnClass} focus:outline-none focus:ring-2 focus:ring-offset-2"
            onclick={handleConfirm}
          >
            确认{typeConfig.label}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
