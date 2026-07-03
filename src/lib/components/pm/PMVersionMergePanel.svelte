<script lang="ts">
	import { onMount } from 'svelte';
	import { getEntryVersions, getBranches, createMerge, resolveMergeConflict, completeMerge } from '$lib/apis/pm/version';
	import type { EntryVersion, VersionBranch, VersionMerge, ConflictItem } from '$lib/apis/pm/types';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';

	interface Props {
		projectId: string;
		entryId: string;
		onClose?: () => void;
		onMerged?: () => void;
	}

	let { projectId, entryId, onClose, onMerged }: Props = $props();

	let branches = $state<VersionBranch[]>([]);
	let versions = $state<EntryVersion[]>([]);
	let loading = $state(true);
	let selectedBranchId = $state<string>('');
	let mergeResult = $state<VersionMerge | null>(null);
	let merging = $state(false);
	let step = $state<'select' | 'conflicts' | 'done'>('select');

	$effect(() => {
		loadData();
	});

	async function loadData() {
		loading = true;
		try {
			const [b, v] = await Promise.all([
				getBranches(projectId, entryId),
				getEntryVersions(projectId, entryId)
			]);
			branches = (b || []).filter((br: VersionBranch) => br.status === 'active');
			versions = v || [];
		} catch (e: any) {
			console.warn('[PMVersionMergePanel] load failed:', e?.message);
		} finally {
			loading = false;
		}
	}

	async function startMerge() {
		if (!selectedBranchId) return;
		merging = true;
		try {
			const result = await createMerge(projectId, entryId, { branchId: selectedBranchId });
			mergeResult = result;
			if (result.conflicts.length === 0) {
				// No conflicts, auto-merge
				await completeMerge(projectId, entryId, result.id);
				step = 'done';
				toast.success('合并完成（无冲突）');
				onMerged?.();
			} else {
				step = 'conflicts';
			}
		} catch (e: any) {
			toast.error(e?.message || '启动合并失败');
		} finally {
			merging = false;
		}
	}

	async function handleResolveConflict(index: number, resolution: 'source' | 'target') {
		if (!mergeResult) return;
		try {
			mergeResult = await resolveMergeConflict(projectId, entryId, mergeResult.id, {
				conflictIndex: index,
				resolution
			});
		} catch (e: any) {
			toast.error(e?.message || '解决冲突失败');
		}
	}

	async function handleBatchResolve(resolution: 'source' | 'target') {
		if (!mergeResult) return;
		const unresolved = mergeResult.conflicts
			.map((c, i) => ({ conflict: c, index: i }))
			.filter(({ conflict }) => conflict.resolution === null);
		for (const { index } of unresolved) {
			try {
				mergeResult = await resolveMergeConflict(projectId, entryId, mergeResult.id, {
					conflictIndex: index,
					resolution
				});
			} catch (e: any) {
				toast.error(e?.message || '批量解决失败');
				break;
			}
		}
	}

	async function handleCompleteMerge() {
		if (!mergeResult) return;
		merging = true;
		try {
			await completeMerge(projectId, entryId, mergeResult.id);
			step = 'done';
			toast.success('合并完成');
			onMerged?.();
		} catch (e: any) {
			toast.error(e?.message || '合并完成失败');
		} finally {
			merging = false;
		}
	}

	function formatValue(val: unknown): string {
		if (val === null || val === undefined) return '-';
		if (typeof val === 'string') return val.length > 150 ? val.slice(0, 150) + '...' : val;
		return JSON.stringify(val);
	}

	function formatTime(ts: number): string {
		try { return dayjs(ts > 1e15 ? ts / 1e6 : ts > 1e12 ? ts : ts * 1e3).format('MM-DD HH:mm'); } catch { return ''; }
	}

	function allConflictsResolved(): boolean {
		if (!mergeResult) return false;
		return mergeResult.conflicts.every(c => c.resolution !== null);
	}
</script>

<div class="fixed inset-0 z-50 bg-white dark:bg-gray-900 flex flex-col">
	<!-- Header -->
	<div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center gap-2">
			<button class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition" onclick={onClose}>
				<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
			</button>
			<h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">版本合并</h2>
		</div>
	</div>

	<!-- Content -->
	<div class="flex-1 overflow-y-auto p-4">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
			</div>
		{:else if step === 'select'}
			<div class="max-w-lg mx-auto">
				<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">选择要合并的分支</h3>
				<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">将分支内容合并回主线（main）。系统会自动检测冲突。</p>

				{#if branches.length === 0}
					<div class="text-center py-8">
						<p class="text-sm text-gray-500">没有活跃的分支可以合并</p>
						<p class="text-xs text-gray-400 mt-1">请先创建分支后再进行合并操作</p>
					</div>
				{:else}
					<div class="space-y-2 mb-4">
						{#each branches as br (br.id)}
							<button
								class="w-full text-left p-3 rounded-xl border-2 transition {selectedBranchId === br.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
								onclick={() => { selectedBranchId = br.id; }}
							>
								<div class="flex items-center justify-between">
									<div>
										<span class="text-sm font-medium text-gray-900 dark:text-gray-100">{br.name}</span>
										<span class="ml-2 px-1.5 py-0.5 text-[10px] bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-300 rounded-full">活跃</span>
									</div>
									<span class="text-[10px] text-gray-400">{formatTime(br.createdAt)}</span>
								</div>
							</button>
						{/each}
					</div>

					<div class="flex justify-end">
						<button
							class="px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-40"
							onclick={startMerge}
							disabled={!selectedBranchId || merging}
						>
							{merging ? '检测冲突中...' : '开始合并'}
						</button>
					</div>
				{/if}
			</div>

		{:else if step === 'conflicts' && mergeResult}
			<div class="max-w-2xl mx-auto">
				<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">冲突解决</h3>
				<p class="text-xs text-gray-500 dark:text-gray-400 mb-2">检测到 {mergeResult.conflicts.length} 处冲突，请逐一选择保留哪个版本。</p>
				<div class="flex gap-2 mb-4">
					<button class="px-3 py-1.5 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition" onclick={() => handleBatchResolve('source')}>全部采用分支</button>
					<button class="px-3 py-1.5 text-xs bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition" onclick={() => handleBatchResolve('target')}>全部采用主线</button>
				</div>

				<div class="space-y-3 mb-4">
					{#each mergeResult.conflicts as conflict, i (i)}
						<div class="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
							<div class="px-3 py-2 bg-gray-50 dark:bg-gray-850 border-b border-gray-200 dark:border-gray-700">
								<div class="flex items-center justify-between">
									<span class="text-xs font-medium text-gray-700 dark:text-gray-300">
										{conflict.type === 'content' ? '内容冲突' : '字段冲突'}
									</span>
									<span class="text-[10px] font-mono text-gray-400">{conflict.path}</span>
								</div>
							</div>
							<div class="p-3 space-y-2">
								<div class="flex gap-2">
									<!-- Source (branch) -->
									<button
										class="flex-1 text-left p-2 rounded-lg border-2 transition {conflict.resolution === 'source' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'}"
										onclick={() => handleResolveConflict(i, 'source')}
									>
										<div class="text-[10px] font-medium text-gray-500 mb-1">分支值 {conflict.resolution === 'source' ? '✓' : ''}</div>
										<div class="text-xs text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap break-all">{formatValue(conflict.sourceValue)}</div>
									</button>
									<!-- Target (main) -->
									<button
										class="flex-1 text-left p-2 rounded-lg border-2 transition {conflict.resolution === 'target' ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'}"
										onclick={() => handleResolveConflict(i, 'target')}
									>
										<div class="text-[10px] font-medium text-gray-500 mb-1">主线值 {conflict.resolution === 'target' ? '✓' : ''}</div>
										<div class="text-xs text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap break-all">{formatValue(conflict.targetValue)}</div>
									</button>
								</div>
							</div>
						</div>
					{/each}
				</div>

				<div class="flex justify-end gap-2">
					<button class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition" onclick={() => { step = 'select'; mergeResult = null; }}>返回</button>
					<button
						class="px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-40"
						onclick={handleCompleteMerge}
						disabled={!allConflictsResolved() || merging}
					>
						{merging ? '合并中...' : '完成合并'}
					</button>
				</div>
			</div>

		{:else if step === 'done'}
			<div class="flex flex-col items-center justify-center py-16">
				<svg class="w-16 h-16 text-green-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
				<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">合并完成</h3>
				<p class="text-sm text-gray-500 mb-4">分支内容已成功合并到主线</p>
				<button class="px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition" onclick={onClose}>关闭</button>
			</div>
		{/if}
	</div>
</div>
