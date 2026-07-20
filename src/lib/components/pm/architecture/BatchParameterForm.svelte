<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  let {
    isOpen = false,
    functionId = '',
    functionName = '',
    onsubmit,
    oncancel
  }: {
    isOpen?: boolean;
    functionId?: string;
    functionName?: string;
    onsubmit?: (data: any) => void;
    oncancel?: () => void;
  } = $props();

  const dispatch = createEventDispatcher();

  interface ParameterRow {
    name: string;
    key: string;
    data_type: string;
    required: boolean;
    description: string;
  }

  const dataTypes = ['string', 'number', 'boolean', 'object', 'array'];

  let rows: ParameterRow[] = $state([
    { name: '', key: '', data_type: 'string', required: false, description: '' },
    { name: '', key: '', data_type: 'string', required: false, description: '' },
    { name: '', key: '', data_type: 'string', required: false, description: '' }
  ]);

  $effect(() => {
    if (isOpen) {
      rows = [
        { name: '', key: '', data_type: 'string', required: false, description: '' },
        { name: '', key: '', data_type: 'string', required: false, description: '' },
        { name: '', key: '', data_type: 'string', required: false, description: '' }
      ];
    }
  });

  const validRows = $derived(rows.filter(r => r.name.trim() !== ''));
  const canSubmit = $derived(validRows.length > 0);

  function addRow() {
    rows = [...rows, { name: '', key: '', data_type: 'string', required: false, description: '' }];
  }

  function removeRow(index: number) {
    rows = rows.filter((_, i) => i !== index);
  }

  function handleCancel() {
    isOpen = false;
    oncancel?.();
  }

  function handleSubmit() {
    if (!canSubmit) return;
    // Emit the valid rows for parent to handle API calls
    onsubmit?.({
      functionId,
      parameters: validRows.map(r => ({
        name: r.name,
        key: r.key || r.name.toLowerCase().replace(/\s+/g, '_'),
        data_type: r.data_type,
        required: r.required,
        description: r.description,
        function_id: functionId
      }))
    });
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-10 mx-auto p-5 border w-[700px] shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">
          批量添加参数 — {functionName}
        </h3>
        <button
          class="text-gray-400 hover:text-gray-600"
          onclick={handleCancel}
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="space-y-3">
        {#each rows as row, i}
          <div class="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
            <div class="flex-1 grid grid-cols-4 gap-2">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">名称 *</label>
                <input
                  type="text"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="参数名称"
                  bind:value={row.name}
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">KEY</label>
                <input
                  type="text"
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="自动生成"
                  bind:value={row.key}
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">数据类型</label>
                <select
                  class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                  bind:value={row.data_type}
                >
                  {#each dataTypes as type}
                    <option value={type}>{type}</option>
                  {/each}
                </select>
              </div>
              <div class="flex items-end gap-3">
                <div class="flex items-center">
                  <input
                    type="checkbox"
                    class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    bind:checked={row.required}
                  />
                  <span class="ml-1 text-xs text-gray-600">必填</span>
                </div>
                {#if rows.length > 1}
                  <button
                    class="text-red-400 hover:text-red-600 p-1"
                    title="删除此行"
                    onclick={() => removeRow(i)}
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.818L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>

      <button
        class="mt-3 text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
        onclick={addRow}
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加更多行
      </button>

      <div class="flex justify-end mt-6 space-x-3">
        <button
          class="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors"
          onclick={handleCancel}
        >
          取消
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={!canSubmit}
          onclick={handleSubmit}
        >
          添加 {validRows.length} 个参数
        </button>
      </div>
    </div>
  </div>
{/if}
