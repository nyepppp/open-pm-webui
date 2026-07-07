<script lang="ts">
	import { onMount } from 'svelte';
	import { getEntryVersions, switchEntryVersion } from '$lib/apis/pm/version';
	import type { EntryVersion } from '$lib/apis/pm/types';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';

	interface Props {
		projectId: string;
		entryId: string;
		currentVersionNumber?: string;
		onVersionSwitch?: (version: EntryVersion) => void;
		readonly?: boolean;
	}

	let { projectId, entryId, currentVersionNumber, onVersionSwitch, readonly = false }: Props = $props();

	let open = $state(false);
	let versions = $state<EntryVersion[]>([]);
	let loading = $state(false);

	async function loadVersions() {
		if (versions.length > 0) return; // already loaded
		loading = true;
		try {
			const token = localStorage.token || '';
			const result = await getEntryVersions(projectId, entryId);
			versions = result || [];
		} catch (e: any) {
			console.warn('[PMVersionHistoryDropdown] load failed:', e?.message);
			versions = [];
		} finally {
			loading = false;
		}
	}

	function toggle() {
		if (!open) loadVersions();
		open = !open;
	}

	async function handleSwitch(version: EntryVersion) {
		try {
			await switchEntryVersion(projectId, entryId, version.id);
			onVersionSwitch?.(version);
			open = false;
			toast.success(`已切换到 ${version.versionNumber || version.version_number}`);
		} catch (e: any) {
			toast.error(e?.message || '切换版本失败');
		}
	}

	function formatTime(ts: number): string {
		try { return dayjs(ts > 1e15 ? ts / 1e6 : ts > 1e12 ? ts : ts * 1e3).fromNow(); } catch { return ''; }
	}
</script>

{#if readonly}
	<span class="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded-full {currentVersionNumber ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-400'}">
		{currentVersionNumber || '-'}
	</span>
{:else}
<div class="relative inline-block">
	<button
		class="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-semibold rounded-full transition-colors {currentVersionNumber ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400 border border-gray-300 dark:border-gray-600'}"
		onclick={toggle}
		title="查看版本历史"
	>
		{currentVersionNumber || 'v1.0'}
		<svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7" /></svg>
	</button>

	{#if open}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="fixed inset-0 z-40" onclick={() => { open = false; }}></div>
		<div class="absolute left-0 top-full mt-1 z-50 w-64 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
			<div class="px-3 py-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-850">
				<span class="text-xs font-semibold text-gray-600 dark:text-gray-400">版本历史</span>
			</div>
			<div class="max-h-60 overflow-y-auto">
				{#if loading}
					<div class="flex items-center justify-center py-6">
						<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
					</div>
				{:else if versions.length === 0}
					<div class="px-3 py-4 text-xs text-gray-400 text-center">暂无版本历史</div>
				{:else}
					{#each versions as v (v.id)}
						<button
							class="w-full text-left px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors {(v.versionNumber ?? v.version_number) === currentVersionNumber ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
							onclick={() => handleSwitch(v)}
						>
							<div class="flex items-center justify-between">
								<span class="text-xs font-medium {(v.versionNumber ?? v.version_number) === currentVersionNumber ? 'text-blue-700 dark:text-blue-300' : 'text-gray-800 dark:text-gray-200'}">{v.versionNumber ?? v.version_number}</span>
								<span class="text-[10px] text-gray-400">{formatTime(v.createdAt ?? v.created_at)}</span>
							</div>
							{#if v.changeSummary ?? v.change_summary}
								<p class="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">{v.changeSummary ?? v.change_summary}</p>
							{/if}
							{#if (v.branchName ?? v.branch_name) && (v.branchName ?? v.branch_name) !== 'main'}
								<span class="inline-block mt-0.5 px-1.5 py-0 text-[9px] bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-300 rounded-full">{v.branchName ?? v.branch_name}</span>
							{/if}
						</button>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>
{/if}
