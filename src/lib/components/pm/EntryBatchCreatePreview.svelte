<script lang="ts">
	// D43/D46: 批量写入预览卡片组件
	// AI 调用 pm_entry_batch_create_preview 后，前端检测响应并渲染本组件。
	// 用户确认后 dispatch('confirm')，取消则 dispatch('cancel')。
	// 视觉规范严格对齐现有 PM 组件：bg-white dark:bg-gray-900 + border + rounded-lg + divide-y + amber 警告 + btn-primary/btn-secondary。

	import { createEventDispatcher } from 'svelte';

	export let preview: {
		preview: Array<{
			index: number;
			title: string;
			content_preview: string;
			data_keys?: string[];
		}>;
		will_create_count: number;
		warnings: string[];
		confirm_tool?: string;
		module_type?: string;
	};

	const dispatch = createEventDispatcher();
</script>

<div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-4 my-2">
	<div class="flex items-center justify-between mb-3">
		<h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
			批量写入预览（{preview.will_create_count} 条）
		</h4>
		<span class="text-xs text-gray-500 dark:text-gray-400">确认后真实写入</span>
	</div>

	{#if preview.warnings?.length}
		<div
			class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md p-2 mb-3"
		>
			{#each preview.warnings as w}
				<p class="text-xs text-amber-700 dark:text-amber-400">⚠ {w}</p>
			{/each}
		</div>
	{/if}

	<div class="divide-y divide-gray-100 dark:divide-gray-800 max-h-60 overflow-y-auto">
		{#each preview.preview as item}
			<div class="py-2">
				<div class="text-sm font-medium text-gray-900 dark:text-gray-100">{item.title}</div>
				{#if item.content_preview}
					<div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.content_preview}</div>
				{/if}
				{#if item.data_keys?.length}
					<div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
						字段: {item.data_keys.join(', ')}
					</div>
				{/if}
			</div>
		{/each}
	</div>

	<div class="flex justify-end gap-2 mt-3">
		<button class="btn-secondary text-sm" on:click={() => dispatch('cancel')}>取消</button>
		<button class="btn-primary text-sm" on:click={() => dispatch('confirm')}>确认写入</button>
	</div>
</div>
