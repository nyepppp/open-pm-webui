<script lang="ts">
  import { onMount } from 'svelte';
  import { architectureStore, activeModules, activeFunctions, activeParameters } from '$lib/stores/pm/architecture';
  import ModuleTable from '$lib/components/pm/architecture/ModuleTable.svelte';
  import MindMapView from '$lib/components/pm/architecture/MindMapView.svelte';
  import ModuleForm from '$lib/components/pm/architecture/ModuleForm.svelte';
  import type { Module, Function, Parameter } from '$lib/models/pm/architecture';

  let activeTab: 'table' | 'mindmap' = 'table';
  let showCreateModal = false;
  let createEntityType: 'module' | 'function' | 'parameter' = 'module';

  // Use reactive declarations for store subscriptions
  let modules: Module[] = [];
  let functionsList: Function[] = [];
  let parametersList: Parameter[] = [];
  
  // Subscribe to stores
  $: modules = $activeModules || [];
  $: functionsList = $activeFunctions || [];
  $: parametersList = $activeParameters || [];

  onMount(() => {
    architectureStore.loadAll();
  });

  function handleCreateModule() {
    createEntityType = 'module';
    showCreateModal = true;
  }

  function handleCreateFunction() {
    createEntityType = 'function';
    showCreateModal = true;
  }

  function handleCreateParameter() {
    createEntityType = 'parameter';
    showCreateModal = true;
  }

  function handleSubmit(event: CustomEvent) {
    const data = event.detail;
    
    if (createEntityType === 'module') {
      architectureStore.createModule(data);
    } else if (createEntityType === 'function') {
      architectureStore.createFunction(data);
    } else {
      architectureStore.createParameter(data);
    }
    
    showCreateModal = false;
  }

  function handleCancel() {
    showCreateModal = false;
  }
</script>

<div class="w-full h-full p-4">
  <!-- Tab Navigation -->
  <div class="mb-4">
    <div class="border-b border-gray-200">
      <nav class="-mb-px flex space-x-8">
        <button
          class="{activeTab === 'table' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
          on:click={() => activeTab = 'table'}
        >
          表格视图
        </button>
        <button
          class="{activeTab === 'mindmap' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
          on:click={() => activeTab = 'mindmap'}
        >
          思维导图
        </button>
      </nav>
    </div>
  </div>

  <!-- Content -->
  <div class="mt-4">
    {#if activeTab === 'table'}
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-bold text-gray-900">产品架构模块</h2>
          <div class="space-x-2">
            <button
              class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-sm"
              on:click={handleCreateModule}
            >
              新增模块
            </button>
            <button
              class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-sm"
              on:click={handleCreateFunction}
            >
              新增功能
            </button>
            <button
              class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded text-sm"
              on:click={handleCreateParameter}
            >
              新增参数
            </button>
          </div>
        </div>
        
        <ModuleTable />
      </div>
    {:else}
      <MindMapView />
    {/if}
  </div>
</div>

<!-- Create Modal -->
{#if showCreateModal}
  <ModuleForm
    entityType={createEntityType}
    isOpen={showCreateModal}
    isEdit={false}
    on:submit={handleSubmit}
    on:cancel={handleCancel}
  />
{/if}