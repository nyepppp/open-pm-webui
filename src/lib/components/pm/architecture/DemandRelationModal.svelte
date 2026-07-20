<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { DemandRelation } from '$lib/models/pm/architecture';

  export let isOpen = false;
  export let existingDemands: DemandRelation[] = [];

  const dispatch = createEventDispatcher();

  let demandId = '';
  let demandName = '';
  let docLink = '';
  let error = '';

  function handleSubmit() {
    if (!demandId.trim()) {
      error = '需求编号不能为空';
      return;
    }
    if (!demandName.trim()) {
      error = '需求名称不能为空';
      return;
    }

    const newDemand: DemandRelation = {
      demand_id: demandId.trim(),
      demand_name: demandName.trim(),
      doc_link: docLink.trim()
    };

    dispatch('add', newDemand);
    resetForm();
    isOpen = false;
  }

  function handleCancel() {
    resetForm();
    isOpen = false;
    dispatch('cancel');
  }

  function resetForm() {
    demandId = '';
    demandName = '';
    docLink = '';
    error = '';
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      handleCancel();
    }
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
       on:keydown={handleKeydown}>
    <div class="relative top-20 mx-auto p-5 border w-[500px] shadow-lg rounded-md bg-white">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">关联需求</h3>
        <button
          class="text-gray-400 hover:text-gray-600"
          on:click={handleCancel}
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {#if error}
        <div class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      {/if}

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            需求编号 <span class="text-red-500">*</span>
          </label>
          <input
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="如：REQ-001"
            bind:value={demandId}
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            需求名称 <span class="text-red-500">*</span>
          </label>
          <input
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="如：用户注册需求"
            bind:value={demandName}
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            文档链接
          </label>
          <input
            type="url"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://docs.example.com/req-001"
            bind:value={docLink}
          />
        </div>
      </div>

      <div class="flex justify-end mt-6 space-x-3">
        <button
          class="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors"
          on:click={handleCancel}
        >
          取消
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          on:click={handleSubmit}
        >
          保存
        </button>
      </div>
    </div>
  </div>
{/if}