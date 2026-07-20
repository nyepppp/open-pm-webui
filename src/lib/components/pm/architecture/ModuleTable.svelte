<script lang="ts">
  import { onMount } from 'svelte';
  import { architectureStore, activeModules, activeFunctions, activeParameters } from '$lib/stores/pm/architecture';
  import { versions } from '$lib/stores/pm/versionStore';
  import VersionHistoryPopover from './VersionHistoryPopover.svelte';
  import DemandRelationTag from './DemandRelationTag.svelte';
  import type { Module, Function, Parameter } from '$lib/models/pm/architecture';

  let selectedEntity: { type: 'module' | 'function' | 'parameter'; id: string } | null = null;
  let showVersionHistory = false;

  $: modules = $activeModules;
  $: functions = $activeFunctions;
  $: parameters = $activeParameters;

  const columns = [
    { key: 'name', label: '名称' },
    { key: 'key', label: '类型 / KEY' },
    { key: 'data_type', label: '数据类型' },
    { key: 'required', label: '必填' },
    { key: 'create_version', label: '创建版本' },
    { key: 'version_record', label: '版本履历' },
    { key: 'demand_relation', label: '关联需求' },
    { key: 'description', label: '描述' }
  ];

  function handleVersionHistoryClick(entityType: 'module' | 'function' | 'parameter', id: string) {
    selectedEntity = { type: entityType, id };
    showVersionHistory = true;
  }

  function handleCloseVersionHistory() {
    showVersionHistory = false;
    selectedEntity = null;
  }

  function getEntityName(entityType: string, id: string): string {
    let entity: Module | Function | Parameter | undefined;
    if (entityType === 'module') {
      entity = modules.find(m => m.id === id);
    } else if (entityType === 'function') {
      entity = functions.find(f => f.id === id);
    } else {
      entity = parameters.find(p => p.id === id);
    }
    return entity?.name || '未知';
  }

  function getVersionName(versionId: string): string {
    if (!versionId) return '-';
    const version = $versions.find(v => v.id === versionId);
    return version?.versionNumber || version?.version_number || versionId;
  }

  onMount(() => {
    architectureStore.loadAll();
  });
</script>

<div class="w-full">
  <div class="mb-4 flex justify-between items-center">
    <h2 class="text-2xl font-bold text-gray-900">产品架构模块</h2>
    <button
      class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      on:click={() => {/* TODO: Open create modal */}}
    >
      新增模块
    </button>
  </div>

  <!-- Modules Table -->
  <div class="mb-8">
    <h3 class="text-lg font-medium text-gray-700 mb-2">模块</h3>
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            {#each columns as column}
              <th scope="col" class="px-6 py-3">{column.label}</th>
            {/each}
            <th scope="col" class="px-6 py-3">操作</th>
          </tr>
        </thead>
        <tbody>
          {#each modules as module}
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50">
              <td class="px-6 py-4">{module.name}</td>
              <td class="px-6 py-4">{module.key}</td>
              <td class="px-6 py-4">{module.data_type}</td>
              <td class="px-6 py-4">{module.required ? '是' : '否'}</td>
              <td class="px-6 py-4">{getVersionName(module.create_version)}</td>
              <td class="px-6 py-4">
                <button
                  class="text-blue-600 hover:text-blue-800 text-sm"
                  on:click={() => handleVersionHistoryClick('module', module.id)}
                >
                  查看履历 ({module.version_record.length})
                </button>
              </td>
              <td class="px-6 py-4">
                <DemandRelationTag demands={module.demand_relation} readonly />
              </td>
              <td class="px-6 py-4">{module.description || '-'}</td>
              <td class="px-6 py-4">
                <div class="flex space-x-2">
                  <button class="text-blue-600 hover:text-blue-800 text-sm">编辑</button>
                  <button class="text-green-600 hover:text-green-800 text-sm">新增下级</button>
                  <button class="text-red-600 hover:text-red-800 text-sm">删除</button>
                  <button class="text-purple-600 hover:text-purple-800 text-sm">复制</button>
                  <button class="text-gray-600 hover:text-gray-800 text-sm">溯源详情</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Functions Table -->
  <div class="mb-8">
    <h3 class="text-lg font-medium text-gray-700 mb-2">功能</h3>
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            {#each columns as column}
              <th scope="col" class="px-6 py-3">{column.label}</th>
            {/each}
            <th scope="col" class="px-6 py-3">操作</th>
          </tr>
        </thead>
        <tbody>
          {#each functions as func}
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50">
              <td class="px-6 py-4">{func.name}</td>
              <td class="px-6 py-4">{func.key}</td>
              <td class="px-6 py-4">{func.data_type}</td>
              <td class="px-6 py-4">{func.required ? '是' : '否'}</td>
              <td class="px-6 py-4">{getVersionName(func.create_version)}</td>
              <td class="px-6 py-4">
                <button
                  class="text-blue-600 hover:text-blue-800 text-sm"
                  on:click={() => handleVersionHistoryClick('function', func.id)}
                >
                  查看履历 ({func.version_record.length})
                </button>
              </td>
              <td class="px-6 py-4">
                <DemandRelationTag demands={func.demand_relation} readonly />
              </td>
              <td class="px-6 py-4">{func.description || '-'}</td>
              <td class="px-6 py-4">
                <div class="flex space-x-2">
                  <button class="text-blue-600 hover:text-blue-800 text-sm">编辑</button>
                  <button class="text-green-600 hover:text-green-800 text-sm">新增下级</button>
                  <button class="text-red-600 hover:text-red-800 text-sm">删除</button>
                  <button class="text-purple-600 hover:text-purple-800 text-sm">复制</button>
                  <button class="text-gray-600 hover:text-gray-800 text-sm">溯源详情</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Parameters Table -->
  <div class="mb-8">
    <h3 class="text-lg font-medium text-gray-700 mb-2">参数</h3>
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            {#each columns as column}
              <th scope="col" class="px-6 py-3">{column.label}</th>
            {/each}
            <th scope="col" class="px-6 py-3">操作</th>
          </tr>
        </thead>
        <tbody>
          {#each parameters as param}
            <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50">
              <td class="px-6 py-4">{param.name}</td>
              <td class="px-6 py-4">{param.key}</td>
              <td class="px-6 py-4">{param.data_type}</td>
              <td class="px-6 py-4">{param.required ? '是' : '否'}</td>
              <td class="px-6 py-4">{getVersionName(param.create_version)}</td>
              <td class="px-6 py-4">
                <button
                  class="text-blue-600 hover:text-blue-800 text-sm"
                  on:click={() => handleVersionHistoryClick('parameter', param.id)}
                >
                  查看履历 ({param.version_record.length})
                </button>
              </td>
              <td class="px-6 py-4">
                <DemandRelationTag demands={param.demand_relation} readonly />
              </td>
              <td class="px-6 py-4">{param.description || '-'}</td>
              <td class="px-6 py-4">
                <div class="flex space-x-2">
                  <button class="text-blue-600 hover:text-blue-800 text-sm">编辑</button>
                  <button class="text-red-600 hover:text-red-800 text-sm">删除</button>
                  <button class="text-purple-600 hover:text-purple-800 text-sm">复制</button>
                  <button class="text-gray-600 hover:text-gray-800 text-sm">溯源详情</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>

{#if showVersionHistory && selectedEntity}
  <VersionHistoryPopover
    entityType={selectedEntity.type}
    entityId={selectedEntity.id}
    onClose={handleCloseVersionHistory}
  />
{/if}