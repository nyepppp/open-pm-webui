<script lang="ts">
	import { versions, filteredVersions, versionSearchQuery, setVersionSearchQuery, setCurrentVersion } from '$lib/stores/pm/versionStore';
	import type { Version } from '$lib/apis/pm/types';

	// Props
	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		onSelect?: (version: Version) => void;
		projectId?: string;
	}

	let { isOpen = false, onClose, onSelect, projectId = '' }: Props = $props();

	let searchInput: HTMLInputElement | null = $state(null);

	function handleSelect(version: Version) {
		setCurrentVersion(version);
		onSelect?.(version);
		onClose?.();
	}

	function handleSearch(event: Event) {
		const target = event.target as HTMLInputElement;
		setVersionSearchQuery(target.value);
	}

	function getVersionLabelColor(label?: string): string {
		switch (label) {
			case 'milestone': return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300';
			case 'release': return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
			case 'review': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
			default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
		}
	}

	function formatDate(timestamp: number): string {
		return new Date(timestamp * 1000).toLocaleDateString('zh-CN', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-20"
		onclick={() => onClose?.()}
		role="dialog"
		aria-modal="true"
		aria-label="版本选择器"
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between mb-3">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">选择版本</h3>
					<button
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						onclick={() => onClose?.()}
						aria-label="关闭版本选择器"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Search -->
				<div class="relative">
					<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<input
						ref={searchInput}
						type="text"
						placeholder="搜索版本号或描述..."
						class="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
						value={$versionSearchQuery}
						oninput={handleSearch}
						aria-label="搜索版本"
					/>
				</div>
			</div>

			<!-- Version List -->
			<div class="max-h-96 overflow-y-auto" role="listbox" aria-label="版本列表">
				{#if $filteredVersions.length === 0}
					<div class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
						<svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						<p class="text-sm">没有找到匹配的版本</p>
					</div>
				{:else}
					<div class="divide-y divide-gray-100 dark:divide-gray-700">
						{#each $filteredVersions as version (version.id)}
							<button
								class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
								onclick={() => handleSelect(version)}
								role="option"
								aria-label="版本 {(version.versionNumber ?? version.version_number)}，{(version.description || '无描述')}">
							>
								<div class="flex-shrink-0" aria-hidden="true">
									<div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
										<svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
										</svg>
									</div>
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2">
										<span class="text-sm font-medium text-gray-900 dark:text-gray-100">
											{(version.versionNumber ?? version.version_number)}
										</span>
										{#if version.label}
											<span class="px-2 py-0.5 text-xs rounded-full {getVersionLabelColor(version.label)}">
												{version.label === 'milestone' ? '里程碑' : version.label === 'release' ? '发布' : '评审'}
											</span>
										{/if}
									</div>
									<p class="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
										{version.description || '无描述'}
									</p>
									<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
										{formatDate(version.createdAt ?? version.created_at)}
									</p>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
				<button
					class="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
					onclick={() => {/* TODO: Implement version creation */}}
					aria-label="创建新版本"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					创建新版本
				</button>
			</div>
		</div>
	</div>
{/if}
