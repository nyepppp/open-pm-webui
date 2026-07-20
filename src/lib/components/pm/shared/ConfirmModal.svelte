<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let title = '确认';
  export let message = '确定要执行此操作吗？';
  export let confirmText = '确认';
  export let cancelText = '取消';
  export let type: 'danger' | 'warning' | 'info' = 'warning';

  const dispatch = createEventDispatcher();

  function handleConfirm() {
    dispatch('confirm');
  }

  function handleCancel() {
    dispatch('cancel');
  }

  const typeClasses = {
    danger: 'bg-red-600 hover:bg-red-700',
    warning: 'bg-yellow-600 hover:bg-yellow-700',
    info: 'bg-blue-600 hover:bg-blue-700'
  };
</script>

<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
  <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
    <div class="mt-3 text-center">
      <h3 class="text-lg leading-6 font-medium text-gray-900">{title}</h3>
      <div class="mt-2 px-7 py-3">
        <p class="text-sm text-gray-500">{message}</p>
      </div>
      <div class="items-center px-4 py-3">
        <button
          class="{typeClasses[type]} text-white font-bold py-2 px-4 rounded mr-2"
          on:click={handleConfirm}
        >
          {confirmText}
        </button>
        <button
          class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
          on:click={handleCancel}
        >
          {cancelText}
        </button>
      </div>
    </div>
  </div>
</div>