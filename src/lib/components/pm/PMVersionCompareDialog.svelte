<script lang="ts">
	import { compareVersions } from '$lib/apis/pm/version';
	import type { Version } from '$lib/apis/pm/types';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		versionA?: Version;
		versionB?: Version;
		projectId?: string;
	}

	let { isOpen = false, onClose, versionA, versionB, projectId = '' }: Props = $props();

	let diff = $state<{
		added: unknown[];
		modified: { entityId: string; entityType: string; changes: { field: string; old: unknown; new: unknown }[] }[];
		deleted: unknown[];
	} | null>(null);
	let loading = $state(false);
	let error = $state('');

	$effect(() => {
		if (isOpen && versionA && versionB && projectId) {
			loadDiff();
		}
	});

	async function loadDiff() {
		if (!versionA || !versionB || !projectId) return;
		loading = true;
		error = '';
		try {
			const data = await compareVersions(projectId, versionA.id, versionB.id);
			if (data && data.diff) {
				diff = data.diff;
			} else {
				diff = { added: [], modified: [], deleted: [] };
			}
		} catch (e) {
			error = '加载对比时出错';
			console.error(e);
		} finally {
			loading = false;
		}
	}

	function formatDate(timestamp: number): string {
		return new Date(timestamp * 1000).toLocaleDateString('zh-CN', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={() => onClose?.()}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
						版本对比
					</h2>
					<button
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						onclick={() => onClose?.()}
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<div class="flex items-center gap-4 mt-3">
					<div class="flex-1 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
						<div class="text-sm font-medium text-blue-700 dark:text-blue-300">{(versionA?.versionNumber ?? versionA?.version_number) || '版本 A'}</div>
						<div class="text-xs text-blue-500 dark:text-blue-400 mt-1">{versionA ? formatDate(versionA.createdAt ?? versionA.created_at) : ''}</div>
					</div>
					<svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
					</svg>
					<div class="flex-1 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
						<div class="text-sm font-medium text-green-700 dark:text-green-300">{(versionB?.versionNumber ?? versionB?.version_number) || '版本 B'}</div>
						<div class="text-xs text-green-500 dark:text-green-400 mt-1">{versionB ? formatDate(versionB.createdAt ?? versionB.created_at) : ''}</div>
					</div>
				</div>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto p-6">
				{#if loading}
					<div class="flex items-center justify-center py-12">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
						<span class="ml-3 text-sm text-gray-500 dark:text-gray-400">加载对比中...</span>
					</div>
				{:else if error}
					<div class="text-center py-12">
						<svg class="w-12 h-12 mx-auto mb-3 text-red-300 dark:text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<p class="text-sm text-red-500 dark:text-red-400">{error}</p>
					</div>
				{:else if diff}
					<!-- Stats -->
					<div class="grid grid-cols-3 gap-4 mb-6">
						<div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
							<div class="text-2xl font-bold text-green-600 dark:text-green-400">{diff.added.length}</div>
							<div class="text-sm text-green-700 dark:text-green-300 mt-1">新增</div>
						</div>
						<div class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 text-center">
							<div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{diff.modified.length}</div>
							<div class="text-sm text-yellow-700 dark:text-yellow-300 mt-1">修改</div>
						</div>
						<div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
							<div class="text-2xl font-bold text-red-600 dark:text-red-400">{diff.deleted.length}</div>
							<div class="text-sm text-red-700 dark:text-red-300 mt-1">删除</div>
						</div>
					</div>

					<!-- Changes -->
					<div class="space-y-4">
						<!-- Added -->
						{#if diff.added.length > 0}
							<div>
								<h3 class="text-sm font-medium text-green-700 dark:text-green-300 mb-2 flex items-center gap-2">
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
									</svg>
									新增条目 ({diff.added.length})
								</h3>
								<div class="space-y-2">
									{#each diff.added as item}
										<div class="p-3 bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-200 dark:border-green-800">
											<pre class="text-xs text-green-700 dark:text-green-300 overflow-auto">{JSON.stringify(item, null, 2)}</pre>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Modified -->
						{#if diff.modified.length > 0}
							<div>
								<h3 class="text-sm font-medium text-yellow-700 dark:text-yellow-300 mb-2 flex items-center gap-2">
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
									修改条目 ({diff.modified.length})
								</h3>
								<div class="space-y-2">
									{#each diff.modified as item}
										<div class="p-3 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg border border-yellow-200 dark:border-yellow-800">
											<div class="text-xs font-medium text-yellow-800 dark:text-yellow-200 mb-2">
												{item.entityType} · {item.entityId}
											</div>
											{#each item.changes as change}
												<div class="grid grid-cols-2 gap-2 text-xs mt-1">
													<div class="p-2 bg-red-50 dark:bg-red-900/20 rounded">
														<div class="text-red-600 dark:text-red-400 font-medium">旧值</div>
														<div class="text-red-500 dark:text-red-300 mt-1">{JSON.stringify(change.old)}</div>
													</div>
													<div class="p-2 bg-green-50 dark:bg-green-900/20 rounded">
														<div class="text-green-600 dark:text-green-400 font-medium">新值</div>
														<div class="text-green-500 dark:text-green-300 mt-1">{JSON.stringify(change.new)}</div>
													</div>
												</div>
											{/each}
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Deleted -->
						{#if diff.deleted.length > 0}
							<div>
								<h3 class="text-sm font-medium text-red-700 dark:text-red-300 mb-2 flex items-center gap-2">
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
									删除条目 ({diff.deleted.length})
								</h3>
								<div class="space-y-2">
									{#each diff.deleted as item}
										<div class="p-3 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800">
											<pre class="text-xs text-red-700 dark:text-red-300 overflow-auto">{JSON.stringify(item, null, 2)}</pre>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						{#if diff.added.length === 0 && diff.modified.length === 0 && diff.deleted.length === 0}
							<div class="text-center py-8">
								<svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
								<p class="text-sm text-gray-500 dark:text-gray-400">两个版本内容相同，无差异</p>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
