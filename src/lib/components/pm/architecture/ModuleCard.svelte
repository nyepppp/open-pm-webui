<script lang="ts">
	import type { TreeModule, TreeFeature } from '$lib/stores/pm/architectureStore';

	interface Props {
		module: TreeModule;
		selected?: boolean;
		expanded?: boolean;
		selectedFeature?: string | null;
		onSelect?: () => void;
		onFeatureSelect?: (featureName: string) => void;
		onAddFeature?: () => void;
		onDelete?: () => void;
		onEditDescription?: () => void;
		description?: string;
	}

	let {
		module,
		selected = false,
		expanded = false,
		selectedFeature = null,
		onSelect,
		onFeatureSelect,
		onAddFeature,
		onDelete,
		onEditDescription,
		description = '暂无描述'
	}: Props = $props();
</script>

<div class="group relative">
	<!-- Module Card -->
	<div
		class="relative bg-white dark:bg-gray-800 rounded-xl border-2 cursor-pointer overflow-hidden will-change-transform {selected 
			? 'border-blue-500 shadow-lg shadow-blue-100 dark:shadow-blue-900/20' 
			: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md'}"
		onclick={(e) => {
			// Only trigger if clicking the card itself, not child buttons
			if (e.target === e.currentTarget || (e.target as HTMLElement).closest('.card-content')) {
				onSelect?.();
			}
		}}
		role="button"
		tabindex="0"
		onkeydown={(e) => e.key === 'Enter' && onSelect?.()}
	>
		<!-- Source Badge -->
		<div class="absolute top-3 right-3 pointer-events-none">
			{#if module.source === 'manual'}
				<span class="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400">
					规划中
				</span>
			{:else}
				<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400">
					自动
				</span>
			{/if}
		</div>

		<!-- Card Content -->
		<div class="p-4 card-content">
			<!-- Header -->
			<div class="flex items-center gap-3 mb-2">
				<div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
					<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
					</svg>
				</div>
				<div class="flex-1 min-w-0">
					<h3 class="text-base font-semibold text-gray-900 dark:text-white truncate">
						{module.name}
					</h3>
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
								{module.features.length} 个功能
							</p>
												{#if module.versionId}
													<p class="text-xs text-blue-500 dark:text-blue-400 mt-0.5">
														版本: {module.versionId}
													</p>
												{/if}
				</div>
			</div>

			<!-- Meta Info -->
			<div class="flex items-center gap-2 mb-2">
				<span class="text-xs text-gray-500 dark:text-gray-400">
					来源: {module.source === 'auto' ? '自动识别' : '手动添加'}
				</span>
				<span class="text-gray-300 dark:text-gray-600">|</span>
				<span class="text-xs text-gray-500 dark:text-gray-400">
					{module.features.reduce((sum, f) => sum + f.paramCount, 0)} 参数
				</span>
				{#if module.updatedAt}
					<span class="text-gray-300 dark:text-gray-600">|</span>
					<span class="text-xs text-gray-500 dark:text-gray-400">
						更新: {new Date(module.updatedAt).toLocaleDateString()}
					</span>
				{/if}
			</div>

			<!-- Description -->
			<p class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-3">
				{description}
			</p>

			<!-- Actions -->
			<div class="flex items-center gap-2">
				<button
					class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
					onclick={(e) => { e.stopPropagation(); onEditDescription?.(); }}
				>
					编辑描述
				</button>
				{#if module.source === 'manual'}
					<button
						class="text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors"
						onclick={(e) => { e.stopPropagation(); onDelete?.(); }}
					>
						删除
					</button>
				{/if}
			</div>
		</div>

		<!-- Expand Indicator -->
		{#if module.features.length > 0}
			<div class="px-4 py-2 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-100 dark:border-gray-700 flex items-center justify-center">
				<svg 
					class="w-4 h-4 text-gray-400 transition-transform duration-200 {expanded ? 'rotate-180' : ''}" 
					fill="none" 
					stroke="currentColor" 
					viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</div>
		{/if}
	</div>

	<!-- Feature Cards (Expanded) -->
	{#if expanded && module.features.length > 0}
		<div class="mt-2 ml-4 space-y-2">
			{#each module.features as feature}
				<button
					class="w-full text-left bg-white dark:bg-gray-800 rounded-lg border transition-all duration-200 cursor-pointer {selectedFeature === feature.name 
						? 'border-blue-400 shadow-md shadow-blue-50 dark:shadow-blue-900/10' 
						: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
					onclick={() => onFeatureSelect?.(feature.name)}
				>
					<div class="p-3">
						<div class="flex items-center gap-2">
							<div class="w-8 h-8 rounded-md bg-green-100 dark:bg-green-900/30 flex items-center justify-center shrink-0">
								<svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
								</svg>
							</div>
							<div class="flex-1 min-w-0">
								<h4 class="text-sm font-medium text-gray-900 dark:text-white truncate">
									{feature.name}
								</h4>
								<div class="flex items-center gap-2 mt-0.5">
									{#if feature.source === 'manual'}
										<span class="text-xs text-orange-500 dark:text-orange-400">规划中</span>
									{/if}
									<span class="text-xs text-gray-400">{feature.paramCount} 参数</span>
								</div>
							</div>
						</div>
					</div>
				</button>
			{/each}

			<!-- Add Feature Button -->
			<button
				class="w-full py-2 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700 text-gray-400 hover:text-blue-600 hover:border-blue-300 dark:hover:border-blue-700 transition-all duration-200 text-sm"
				onclick={(e) => { e.stopPropagation(); onAddFeature?.(); }}
			>
				+ 添加功能
			</button>
		</div>
	{/if}
</div>
