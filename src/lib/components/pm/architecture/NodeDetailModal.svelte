<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { Module, Function, Parameter, VersionRecord, DemandRelation } from '$lib/models/pm/architecture';

  export let nodeData: any;
  export let onClose: () => void;

  const dispatch = createEventDispatcher();

  let entity: Module | Function | Parameter | undefined;
  let entityType: string;

  $: {
    if (nodeData) {
      entity = nodeData.data;
      entityType = nodeData.type;
    }
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('zh-CN');
  }

  function handleClose() {
    onClose();
  }

  function getTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      module: '模块',
      function: '功能',
      parameter: '参数'
    };
    return labels[type] || type;
  }
</script>

{#if entity}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-[600px] shadow-lg rounded-md bg-white max-h-[80vh] overflow-y-auto">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">节点详情</h3>
        <button
          class="text-gray-400 hover:text-gray-600"
          on:click={handleClose}
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- 基础元信息 -->
      <div class="mb-6">
        <h4 class="text-md font-medium text-gray-900 mb-3">基础元信息</h4>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <span class="text-sm font-medium text-gray-700">条目名称：</span>
            <span class="text-sm text-gray-600">{entity.name}</span>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">类型：</span>
            <span class="text-sm text-gray-600">{getTypeLabel(entityType)}</span>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">唯一 KEY：</span>
            <span class="text-sm text-gray-600">{entity.key}</span>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">数据类型：</span>
            <span class="text-sm text-gray-600">{entity.data_type}</span>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">是否必填：</span>
            <span class="text-sm text-gray-600">{entity.required ? '是' : '否'}</span>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">创建版本：</span>
            <span class="text-sm text-gray-600">{entity.create_version}</span>
          </div>
          <div class="col-span-2">
            <span class="text-sm font-medium text-gray-700">描述：</span>
            <span class="text-sm text-gray-600">{entity.description || '无'}</span>
          </div>
        </div>
      </div>

      <!-- 版本溯源板块 -->
      <div class="mb-6">
        <h4 class="text-md font-medium text-gray-900 mb-3">版本溯源</h4>
        <div class="space-y-2">
          {#each entity.version_record.slice(-5) as record}
            <div class="border rounded-lg p-3 bg-gray-50">
              <div class="flex justify-between items-start">
                <div class="text-sm font-medium text-gray-900">
                  版本 {record.version}
                </div>
                <div class="text-xs text-gray-500">
                  {formatDate(record.time)}
                </div>
              </div>
              <div class="text-sm text-gray-600 mt-1">
                <span class="font-medium">操作人：</span>{record.operator}
              </div>
              <div class="text-sm text-gray-600">
                <span class="font-medium">变更说明：</span>{record.change_detail}
              </div>
            </div>
          {/each}
          {#if entity.version_record.length === 0}
            <div class="text-sm text-gray-500 text-center py-4">暂无版本记录</div>
          {/if}
        </div>
      </div>

      <!-- 关联需求板块 -->
      <div class="mb-6">
        <h4 class="text-md font-medium text-gray-900 mb-3">关联需求</h4>
        <div class="flex flex-wrap gap-2">
          {#each entity.demand_relation as demand}
            <a
              href={demand.doc_link}
              target="_blank"
              class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
            >
              {demand.demand_id} - {demand.demand_name}
            </a>
          {/each}
          {#if entity.demand_relation.length === 0}
            <div class="text-sm text-gray-500">暂无关联需求</div>
          {/if}
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex space-x-3">
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
          on:click={() => {
            // TODO: Navigate to table view and locate this item
            handleClose();
          }}
        >
          跳转至表格视图
        </button>
        <button
          class="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors text-sm"
          on:click={() => {
            // TODO: Copy entity info to clipboard
            handleClose();
          }}
        >
          复制条目信息
        </button>
      </div>
    </div>
  </div>
{/if}