<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let columns: { key: string; label: string; width?: string }[] = [];
  export let data: any[] = [];
  export let loading = false;

  const dispatch = createEventDispatcher();

  function handleRowClick(row: any) {
    dispatch('rowClick', row);
  }

  function handleActionClick(action: string, row: any) {
    dispatch('action', { action, row });
  }
</script>

<div class="w-full overflow-x-auto">
  <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
    <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
      <tr>
        {#each columns as column}
          <th scope="col" class="px-6 py-3" style={column.width ? `width: ${column.width}` : ''}>
            {column.label}
          </th>
        {/each}
        <th scope="col" class="px-6 py-3">操作</th>
      </tr>
    </thead>
    <tbody>
      {#if loading}
        <tr>
          <td colspan={columns.length + 1} class="px-6 py-4 text-center">加载中...</td>
        </tr>
      {:else if data.length === 0}
        <tr>
          <td colspan={columns.length + 1} class="px-6 py-4 text-center">暂无数据</td>
        </tr>
      {:else}
        {#each data as row, index}
          <tr
            class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
            on:click={() => handleRowClick(row)}
          >
            {#each columns as column}
              <td class="px-6 py-4">{row[column.key] || '-'}</td>
            {/each}
            <td class="px-6 py-4">
              <button
                class="text-blue-600 hover:text-blue-900 mr-2"
                on:click={() => handleActionClick('edit', row)}
              >
                编辑
              </button>
              <button
                class="text-red-600 hover:text-red-900"
                on:click={() => handleActionClick('delete', row)}
              >
                删除
              </button>
            </td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>