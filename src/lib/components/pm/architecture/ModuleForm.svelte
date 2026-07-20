<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { Module, Function, Parameter, DemandRelation } from '$lib/models/pm/architecture';
  import DemandRelationTag from './DemandRelationTag.svelte';
  import DemandRelationModal from './DemandRelationModal.svelte';

  export let entityType: 'module' | 'function' | 'parameter';
  export let entity: Partial<Module | Function | Parameter> = {};
  export let isOpen = false;
  export let isEdit = false;

  const dispatch = createEventDispatcher();

  let formData = {
    name: entity.name || '',
    key: entity.key || '',
    data_type: entity.data_type || 'string',
    required: entity.required !== undefined ? entity.required : true,
    description: entity.description || '',
    create_version: entity.create_version || '',
    demand_relation: entity.demand_relation || []
  };

  let showDemandModal = false;
  let error = '';

  $: if (isOpen) {
    formData = {
      name: entity.name || '',
      key: entity.key || '',
      data_type: entity.data_type || 'string',
      required: entity.required !== undefined ? entity.required : true,
      description: entity.description || '',
      create_version: entity.create_version || '',
      demand_relation: entity.demand_relation || []
    };
  }

  function handleSubmit() {
    if (!formData.name.trim()) {
      error = '名称不能为空';
      return;
    }
    if (!formData.key.trim()) {
      error = 'KEY 不能为空';
      return;
    }

    dispatch('submit', {
      ...formData,
      demand_relation: formData.demand_relation
    });
    
    isOpen = false;
    error = '';
  }

  function handleCancel() {
    isOpen = false;
    error = '';
    dispatch('cancel');
  }

  function handleAddDemand(event: CustomEvent<DemandRelation>) {
    formData.demand_relation = [...formData.demand_relation, event.detail];
  }

  function handleRemoveDemand(event: CustomEvent<string>) {
    formData.demand_relation = formData.demand_relation.filter(
      d => d.demand_id !== event.detail
    );
  }

  function handleClearDemands() {
    formData.demand_relation = [];
  }

  const dataTypes = ['string', 'number', 'boolean', 'array', 'object'];
</script>

{#if isOpen}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-10 mx-auto p-5 border w-[600px] shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">
          {isEdit ? '编辑' : '新增'}
          {entityType === 'module' ? '模块' : entityType === 'function' ? '功能' : '参数'}
        </h3>
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
            名称 <span class="text-red-500">*</span>
          </label>
          <input
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入名称"
            bind:value={formData.name}
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            KEY <span class="text-red-500">*</span>
          </label>
          <input
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="请输入 KEY"
            bind:value={formData.key}
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            数据类型 <span class="text-red-500">*</span>
          </label>
          <select
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            bind:value={formData.data_type}
          >
            {#each dataTypes as type}
              <option value={type}>{type}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            是否必填
          </label>
          <div class="flex items-center">
            <input
              type="checkbox"
              class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              bind:checked={formData.required}
            />
            <span class="ml-2 text-sm text-gray-600">必填</span>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            描述
          </label>
          <textarea
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="3"
            placeholder="请输入描述"
            bind:value={formData.description}
          ></textarea>
        </div>

        {#if isEdit}
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              创建版本
            </label>
            <input
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500"
              value={formData.create_version}
              disabled
            />
            <p class="text-xs text-gray-500 mt-1">创建版本不可修改</p>
          </div>
        {/if}

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            关联需求
          </label>
          <DemandRelationTag
            demands={formData.demand_relation}
            on:remove={handleRemoveDemand}
            on:add={() => showDemandModal = true}
          />
          {#if formData.demand_relation.length > 0}
            <button
              class="mt-2 text-red-600 hover:text-red-800 text-sm"
              on:click={handleClearDemands}
            >
              清空所有需求
            </button>
          {/if}
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

<DemandRelationModal
  isOpen={showDemandModal}
  on:add={handleAddDemand}
  on:cancel={() => showDemandModal = false}
/>