<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';
	import { getVersions, createVersion } from '$lib/apis/pm/index';
	import { setCurrentVersion, versions, currentVersion } from '$lib/stores/pm/versionStore';
	import type { Version } from '$lib/apis/pm/types';

	let projectId = $derived($page.params.projectId);
	let isLoading = $state(true);
	let showCreateForm = $state(false);
	let newVersionNumber = $state('');
	let newVersionLabel = $state<'milestone' | 'release' | 'review' | undefined>(undefined);
	let newVersionDesc = $state('');

	const labelLabels: Record<string, { l: string; c: string }> = {
		milestone: { l: '里程碑', c: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' },
		release: { l: '发布', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		review: { l: '评审', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' }
	};

	async function loadVersions() {
		isLoading = true;
		try {
			const token = localStorage.token || '';
			const vList = await getVersions(token, projectId);
			if (Array.isArray(vList)) {
				versions.set(vList);
				if (vList.length > 0 && !$currentVersion) {
					setCurrentVersion(vList[0]);
				}
			}
		} catch { versions.set([]); }
		finally { isLoading = false; }
	}

	onMount(() => { loadVersions(); });

	async function handleCreate() {
		if (!newVersionNumber.trim()) return;
		try {
			const token = localStorage.token || '';
			await createVersion(token, projectId, {
				version_number: newVersionNumber,
				label: newVersionLabel || undefined,
				description: newVersionDesc || ''
			});
			newVersionNumber = '';
			newVersionLabel = undefined;
			newVersionDesc = '';
			showCreateForm = false;
			await loadVersions();
			toast.success('版本创建成功');
		} catch (e: any) { toast.error(e.message || '创建失败'); }
	}

	let sortedVersions = $derived([...$versions].sort((a, b) => b.createdAt - a.createdAt));
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>版本管理</div>
				<div class="text-lg font-medium text-gray-500">{sortedVersions.length}</div>
			</div>
			<div class="flex justify-end gap-1.5">
				{#if !showCreateForm}
					<button class="px-2 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black transition font-medium text-sm flex items-center" onclick={() => { showCreateForm = true; }}>
						<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
						<div class="ml-1 text-xs">创建版本</div>
					</button>
				{/if}
			</div>
		</div>
	</div>

	<div class="py-2 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30">
		{#if showCreateForm}
			<div class="px-3.5 pb-3">
				<div class="border border-gray-200 dark:border-gray-700 rounded-2xl p-3 space-y-2">
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="版本号 (如 v1.0)" bind:value={newVersionNumber} onkeydown={(e) => { if (e.key === 'Enter' && newVersionNumber.trim()) handleCreate(); }} />
					<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" placeholder="版本描述（可选）" rows="2" bind:value={newVersionDesc}></textarea>
					<div class="flex items-center gap-2">
						<span class="text-xs text-gray-500">标签：</span>
						{#each [['milestone', '里程碑'], ['release', '发布'], ['review', '评审']] as [val, label]}
							<button class="px-2 py-1 text-xs rounded-lg transition {newVersionLabel === val ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}" onclick={() => { newVersionLabel = val as any; }}>{label}</button>
						{/each}
						<button class="px-2 py-1 text-xs rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-400" onclick={() => { newVersionLabel = undefined; }}>无标签</button>
					</div>
					<div class="flex justify-end gap-2">
						<button class="px-3 py-1.5 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={() => { showCreateForm = false; newVersionNumber = ''; newVersionDesc = ''; }}>取消</button>
						<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-50" onclick={handleCreate} disabled={!newVersionNumber.trim()}>创建</button>
					</div>
				</div>
			</div>
		{/if}

		{#if isLoading}
			<div class="flex items-center justify-center py-12"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div></div>
		{:else if sortedVersions.length === 0}
			<div class="py-12 text-center">
				<svg class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6 6.878V6a2.25 2.25 0 012.25-2.25h7.5A2.25 2.25 0 0118 6v.878m-12 0c.235-.083.487-.128.75-.128h10.5c.263 0 .515.045.75.128m-12 0A2.25 2.25 0 004.5 9v.878m13.5-3A2.25 2.25 0 0119.5 9v.878m0 0a2.246 2.246 0 00-.75-.128H5.25c-.263 0-.515.045-.75.128m15 0A2.25 2.25 0 0121 12v6a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 18v-6c0-1.243.673-2.324 1.673-2.878" /></svg>
				<p class="text-sm text-gray-500 dark:text-gray-400">还没有版本</p>
				{#if !showCreateForm}
					<button class="mt-3 px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-xl transition" onclick={() => { showCreateForm = true; }}>创建第一个版本</button>
				{/if}
			</div>
		{:else}
			<div class="px-2.5 py-1 gap-1.5 flex flex-col">
				{#each sortedVersions as v (v.id)}
					<div class="flex cursor-pointer w-full px-3.5 py-2 border border-gray-50 dark:border-gray-850/30 bg-transparent dark:hover:bg-gray-850 hover:bg-white rounded-2xl transition group">
						<div class="w-full flex items-center justify-between">
							<div class="flex items-center gap-3">
								<span class="text-sm font-semibold text-gray-900 dark:text-gray-100">{v.versionNumber}</span>
								{#if v.label}
									<span class="px-1.5 py-0.5 text-xs rounded {labelLabels[v.label]?.c || ''}">{labelLabels[v.label]?.l || v.label}</span>
								{/if}
								{#if v.description}
									<span class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 max-w-xs">{v.description}</span>
								{/if}
							</div>
							<div class="flex items-center gap-2 text-xs">
								<span class="text-gray-500 dark:text-gray-400">{dayjs(v.createdAt / 1_000_000).format('YYYY-MM-DD HH:mm')}</span>
								<button class="px-2 py-1 text-xs rounded-lg {($currentVersion?.id === v.id) ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-600'} transition" onclick={() => { setCurrentVersion(v); toast.success(`已切换到 ${v.versionNumber}`); }}>
									{($currentVersion?.id === v.id) ? '当前版本' : '切换'}
								</button>
								<!-- Placeholder for compare/rollback -->
								<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition opacity-0 group-hover:opacity-100" title="版本对比（开发中）" onclick={() => { toast.info('版本对比功能开发中'); }}>
									<svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" /></svg>
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
