<script lang="ts">
	import { getImpactAnalysis } from '$lib/apis/pm/relation';
	import type { ModuleType } from '$lib/apis/pm/types';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		entityId?: string;
		entityType?: string;
		projectId?: string;
	}

	let { isOpen = false, onClose, entityId = '', entityType = '', projectId = '' }: Props = $props();

	let upstream = $state<{ entityId: string; entityType: string; relationType: string }[]>([]);
	let downstream = $state<{ entityId: string; entityType: string; relationType: string }[]>([]);
	let loading = $state(false);
	let error = $state('');

	$effect(() => {
		if (isOpen && entityId && projectId) {
			loadImpact();
		}
	});

	async function loadImpact() {
		loading = true;
		error = '';
		try {
			const response = await getImpactAnalysis(projectId, entityId);
			if (response.success && response.data) {
				upstream = response.data.upstream;
				downstream = response.data.downstream;
			} else {
				error = response.error || '加载影响分析失败';
			}
		} catch (e) {
			error = '加载影响分析时出错';
		} finally {
			loading = false;
		}
	}

	function getRelationLabel(type: string): string {
		const labels: Record<string, string> = {
			contains: '包含',
			references: '引用',
			derives: '派生',
			modifies: '修改',
			conflicts: '冲突'
		};
		return labels[type] || type;
	}

	function getRelationColor(type: string): string {
		const colors: Record<string, string> = {
			contains: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
			references: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
			derives: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
			modifies: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
			conflicts: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
		};
		return colors[type] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={() => onClose?.()}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<svg class="w-5 h-5 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
						</svg>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">影响分析</h2>
					</div>
					<button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" onclick={() => onClose?.()}>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					查看此条目的上游依赖和下游影响
				</p>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto p-6">
				{#if loading}
					<div class="flex items-center justify-center py-12">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
					</div>
				{:else if error}
					<div class="text-center py-8">
						<p class="text-sm text-red-500 dark:text-red-400">{error}</p>
					</div>
				{:else}
					<!-- Upstream -->
					<div class="mb-6">
						<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
							<svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
							</svg>
							上游依赖 ({upstream.length})
						</h3>
						{#if upstream.length === 0}
							<p class="text-sm text-gray-400 dark:text-gray-500 pl-6">无上游依赖</p>
						{:else}
							<div class="space-y-2 pl-6">
								{#each upstream as item}
									<div class="flex items-center gap-2 p-2 bg-blue-50 dark:bg-blue-900/10 rounded-lg">
										<span class="px-2 py-0.5 text-xs rounded-full {getRelationColor(item.relationType)}">
											{getRelationLabel(item.relationType)}
										</span>
										<span class="text-sm text-gray-700 dark:text-gray-300">{item.entityType}</span>
										<span class="text-xs text-gray-400 dark:text-gray-500 truncate">{item.entityId}</span>
									</div>
								{/each}
							</div>
						{/if}
					</div>

					<!-- Downstream -->
					<div>
						<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
							<svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
							</svg>
							下游影响 ({downstream.length})
						</h3>
						{#if downstream.length === 0}
							<p class="text-sm text-gray-400 dark:text-gray-500 pl-6">无下游影响</p>
						{:else}
							<div class="space-y-2 pl-6">
								{#each downstream as item}
									<div class="flex items-center gap-2 p-2 bg-red-50 dark:bg-red-900/10 rounded-lg">
										<span class="px-2 py-0.5 text-xs rounded-full {getRelationColor(item.relationType)}">
											{getRelationLabel(item.relationType)}
										</span>
										<span class="text-sm text-gray-700 dark:text-gray-300">{item.entityType}</span>
										<span class="text-xs text-gray-400 dark:text-gray-500 truncate">{item.entityId}</span>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
