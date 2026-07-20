<script lang="ts">
  import { onMount } from 'svelte';
  import { architectureStore, activeModules, activeFunctions, activeParameters } from '$lib/stores/pm/architecture';
  import { versions } from '$lib/stores/pm/versionStore';
  import type { Module, Function, Parameter, VersionRecord } from '$lib/models/pm/architecture';
  import { generateVersionRecord } from '$lib/apis/pm/architecture';

  export let entityType: 'module' | 'function' | 'parameter';
  export let entityId: string;
  export let onClose: () => void;

  let entity: Module | Function | Parameter | undefined;
  let showAllRecords = false;
  const RECORDS_PER_PAGE = 20;

  $: {
    if (entityType === 'module') {
      entity = $activeModules.find(m => m.id === entityId);
    } else if (entityType === 'function') {
      entity = $activeFunctions.find(f => f.id === entityId);
    } else {
      entity = $activeParameters.find(p => p.id === entityId);
    }
  }

  function getVersionName(versionId: string): string {
    if (!versionId) return '-';
    const version = $versions.find(v => v.id === versionId);
    return version?.versionNumber || version?.version_number || versionId;
  }

  function exportToCSV() {
    if (!entity) return;
    
    const headers = ['version', 'operator', 'time', 'change_detail'];
    const rows = entity.version_record.map(record => [
      getVersionName(record.version),
      record.operator,
      record.time,
      record.change_detail
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(field => `"${field}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${entity.name}_version_history.csv`;
    link.click();
  }

  function getVisibleRecords(): VersionRecord[] {
    if (!entity) return [];
    if (showAllRecords) return entity.version_record;
    return entity.version_record.slice(-RECORDS_PER_PAGE);
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('zh-CN');
  }
</script>

{#if entity}
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
    <div class="relative top-20 mx-auto p-5 border w-[600px] shadow-lg rounded-md bg-white max-h-[80vh] overflow-y-auto">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-medium text-gray-900">版本履历</h3>
        <button
          class="text-gray-400 hover:text-gray-600"
          on:click={onClose}
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="mb-4">
        <div class="text-sm text-gray-600 mb-2">
          <span class="font-medium">条目名称：</span>{entity.name}
        </div>
        <div class="text-sm text-gray-600 mb-2">
          <span class="font-medium">创建版本：</span>{getVersionName(entity.create_version)}
        </div>
        <div class="text-sm text-gray-600">
          <span class="font-medium">总变更次数：</span>{entity.version_record.length}
        </div>
      </div>

      <div class="mb-4">
        <button
          class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-sm"
          on:click={exportToCSV}
        >
          导出 CSV
        </button>
      </div>

      <div class="space-y-3">
        {#each getVisibleRecords() as record}
          <div class="border rounded-lg p-3 bg-gray-50">
            <div class="flex justify-between items-start mb-2">
              <div class="text-sm font-medium text-gray-900">
                版本 {getVersionName(record.version)}
              </div>
              <div class="text-xs text-gray-500">
                {formatDate(record.time)}
              </div>
            </div>
            <div class="text-sm text-gray-600 mb-1">
              <span class="font-medium">操作人：</span>{record.operator}
            </div>
            <div class="text-sm text-gray-600">
              <span class="font-medium">变更说明：</span>{record.change_detail}
            </div>
          </div>
        {/each}
      </div>

      {#if entity.version_record.length > RECORDS_PER_PAGE && !showAllRecords}
        <div class="mt-4 text-center">
          <button
            class="text-blue-600 hover:text-blue-800 text-sm font-medium"
            on:click={() => showAllRecords = true}
          >
            查看更多 ({entity.version_record.length - RECORDS_PER_PAGE} 条)
          </button>
        </div>
      {/if}

      {#if showAllRecords}
        <div class="mt-4 text-center">
          <button
            class="text-blue-600 hover:text-blue-800 text-sm font-medium"
            on:click={() => showAllRecords = false}
          >
            收起
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}