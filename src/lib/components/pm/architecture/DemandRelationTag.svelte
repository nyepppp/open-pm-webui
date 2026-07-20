<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { DemandRelation } from '$lib/models/pm/architecture';

  export let demands: DemandRelation[] = [];
  export let readonly = false;

  const dispatch = createEventDispatcher();

  function handleTagClick(demand: DemandRelation) {
    if (demand.doc_link) {
      window.open(demand.doc_link, '_blank');
    }
  }

  function handleRemove(demandId: string) {
    dispatch('remove', demandId);
  }

  function handleAdd() {
    dispatch('add');
  }
</script>

<div class="flex flex-wrap gap-2">
  {#each demands as demand}
    <div
      class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer transition-colors"
      on:click={() => handleTagClick(demand)}
    >
      <span class="mr-1">{demand.demand_id}</span>
      <span class="text-xs text-blue-600">{demand.demand_name}</span>
      {#if !readonly}
        <button
          class="ml-2 text-blue-600 hover:text-blue-800 focus:outline-none"
          on:click|stopPropagation={() => handleRemove(demand.demand_id)}
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      {/if}
    </div>
  {/each}
  
  {#if !readonly}
    <button
      class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
      on:click={handleAdd}
    >
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      添加需求
    </button>
  {/if}
</div>