<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  /**
   * ConfirmationModal - Agent Operation Confirmation Dialog
   *
   * Displays a confirmation dialog for dangerous agent-initiated operations
   * (delete, overwrite). Used in the PM workspace agent flow.
   *
   * Features:
   * - Shows operation details (type, target module, entry)
   * - Highlights dangerous operations with warning styling
   * - Supports "Allow all in this session" toggle
   * - Emits confirm/cancel events with confirmation_id
   */

  interface ConfirmationData {
    confirmation_id: string;
    operation: string;
    module_type: string;
    entry_id?: string;
    entry_title?: string;
    message: string;
  }

  let {
    isOpen = false,
    confirmation,
    allowAll = false,
    onconfirm,
    oncancel,
    onallowallchange
  }: {
    isOpen?: boolean;
    confirmation?: ConfirmationData | null;
    allowAll?: boolean;
    onconfirm?: (confirmationId: string, allowAll: boolean) => void;
    oncancel?: (confirmationId: string) => void;
    onallowallchange?: (allowAll: boolean) => void;
  } = $props();

  function handleConfirm() {
    if (confirmation?.confirmation_id) {
      onconfirm?.(confirmation.confirmation_id, allowAll);
    }
  }

  function handleCancel() {
    if (confirmation?.confirmation_id) {
      oncancel?.(confirmation.confirmation_id);
    }
  }

  function handleAllowAllChange(e: Event) {
    const target = e.target as HTMLInputElement;
    allowAll = target.checked;
    onallowallchange?.(allowAll);
  }

  // Determine if this is a dangerous operation
  const isDangerous = $derived(
    confirmation?.operation === 'delete' || confirmation?.operation === 'overwrite'
  );

  // Styling based on operation type
  const modalClasses = $derived(
    isDangerous
      ? 'border-red-300 bg-red-50'
      : 'border-yellow-300 bg-yellow-50'
  );

  const confirmButtonClasses = $derived(
    isDangerous
      ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
      : 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500'
  );

  const iconSvg = $derived(
    isDangerous
      ? `<svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>`
      : `<svg class="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>`
  );
</script>

{#if isOpen && confirmation}
  <div class="fixed inset-0 bg-gray-900 bg-opacity-60 overflow-y-auto h-full w-full z-50"
       role="dialog"
       aria-modal="true"
       aria-labelledby="confirm-title">
    <div class="flex items-center justify-center min-h-screen px-4">
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full {modalClasses} border-2">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center gap-3">
            <div class="flex-shrink-0">
              {@html iconSvg}
            </div>
            <h3 id="confirm-title" class="text-lg font-semibold text-gray-900">
              {isDangerous ? '危险操作确认' : '操作确认'}
            </h3>
          </div>
        </div>

        <!-- Body -->
        <div class="px-6 py-4">
          <p class="text-sm text-gray-700 mb-3">
            {confirmation.message}
          </p>

          <!-- Operation details -->
          <div class="bg-gray-100 rounded-md p-3 text-sm space-y-1">
            <div class="flex justify-between">
              <span class="text-gray-500">操作类型:</span>
              <span class="font-medium {isDangerous ? 'text-red-600' : 'text-gray-900'}">
                {confirmation.operation}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">目标模块:</span>
              <span class="font-medium text-gray-900">{confirmation.module_type}</span>
            </div>
            {#if confirmation.entry_title}
              <div class="flex justify-between">
                <span class="text-gray-500">条目:</span>
                <span class="font-medium text-gray-900">{confirmation.entry_title}</span>
              </div>
            {/if}
            {#if confirmation.entry_id}
              <div class="flex justify-between">
                <span class="text-gray-500">条目ID:</span>
                <span class="font-mono text-xs text-gray-600">{confirmation.entry_id}</span>
              </div>
            {/if}
          </div>

          <!-- Warning for dangerous ops -->
          {#if isDangerous}
            <div class="mt-3 p-3 bg-red-100 border border-red-200 rounded-md">
              <p class="text-xs text-red-700">
                <strong>警告:</strong> 此操作不可撤销。删除的数据将无法恢复。
              </p>
            </div>
          {/if}

          <!-- Allow all toggle -->
          <div class="mt-4 flex items-center">
            <input
              type="checkbox"
              id="allow-all"
              checked={allowAll}
              onchange={handleAllowAllChange}
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label for="allow-all" class="ml-2 text-sm text-gray-600">
              本次会话中允许所有非危险操作（删除/覆盖仍需确认）
            </label>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-end gap-3">
          <button
            class="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700
                   hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            onclick={handleCancel}
          >
            取消
          </button>
          <button
            class="px-4 py-2 rounded-md text-sm font-medium text-white
                   {confirmButtonClasses} focus:outline-none focus:ring-2 focus:ring-offset-2"
            onclick={handleConfirm}
          >
            确认{confirmation.operation}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
