<script lang="ts">
	import { onMount } from 'svelte';
	import { getEntryVersions, getEntryVersion } from '$lib/apis/pm/version';
	import type { EntryVersion } from '$lib/apis/pm/types';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';

	interface Props {
		projectId: string;
		entryId: string;
		onClose?: () => void;
		onRestore?: (version: EntryVersion) => void;
	}

	let { projectId, entryId, onClose, onRestore }: Props = $props();

	let versions = $state<EntryVersion[]>([]);
	let loading = $state(true);
	let oldVersionId = $state<string>('');
	let newVersionId = $state<string>('');
	let oldContent = $state<string>('');
	let newContent = $state<string>('');
	let oldVersionNumber = $state<string>('');
	let newVersionNumber = $state<string>('');
	let comparing = $state(false);
	let oldMetadata = $state<Record<string, unknown>>({});
	let newMetadata = $state<Record<string, unknown>>({});
	let metadataDiff = $state<{ field: string; old: unknown; new: unknown }[]>([]);
	let diffLines = $state<{ type: string; oldNum: number; newNum: number; text: string }[]>([]);

	$effect(() => {
		loadVersions();
	});

	async function loadVersions() {
		loading = true;
		try {
			const result = await getEntryVersions(projectId, entryId);
			versions = (result || []).sort((a, b) => (b.createdAt ?? b.created_at) - (a.createdAt ?? a.created_at));
			if (versions.length >= 2) {
				oldVersionId = versions[1].id;
				newVersionId = versions[0].id;
			} else if (versions.length === 1) {
				newVersionId = versions[0].id;
			}
		} catch (e: any) {
			console.warn('[PMVersionComparePanel] load failed:', e?.message);
			versions = [];
		} finally {
			loading = false;
		}
	}

	async function runCompare() {
		if (!oldVersionId || !newVersionId) {
			toast.warning('请选择两个版本进行对比');
			return;
		}
		comparing = true;
		try {
			const [oldV, newV] = await Promise.all([
				getEntryVersion(projectId, entryId, oldVersionId),
				getEntryVersion(projectId, entryId, newVersionId)
			]);
			oldContent = stripHtml(oldV.content || '');
			newContent = stripHtml(newV.content || '');
			oldVersionNumber = oldV.versionNumber ?? oldV.version_number ?? '';
			newVersionNumber = newV.versionNumber ?? newV.version_number ?? '';
			diffLines = computeDiff(oldContent, newContent);
			
			// Compute metadata diff
			oldMetadata = (oldV.entry_metadata || {}) as Record<string, unknown>;
			newMetadata = (newV.entry_metadata || {}) as Record<string, unknown>;
			metadataDiff = computeMetadataDiff(oldMetadata, newMetadata);
		} catch (e: any) {
			toast.error(e?.message || '获取版本内容失败');
		} finally {
			comparing = false;
		}
	}

	function stripHtml(html: string): string {
		try {
			const div = document.createElement('div');
			div.innerHTML = html;
			return div.textContent || div.innerText || html;
		} catch {
			return html;
		}
	}

	function computeDiff(oldText: string, newText: string) {
		const oldLines = oldText.split('\n');
		const newLines = newText.split('\n');
		const result: { type: 'unchanged' | 'added' | 'removed'; oldNum: number; newNum: number; text: string }[] = [];

		// Simple LCS-based diff
		const m = oldLines.length;
		const n = newLines.length;

		// Build LCS table
		const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
		for (let i = 1; i <= m; i++) {
			for (let j = 1; j <= n; j++) {
				if (oldLines[i - 1] === newLines[j - 1]) {
					dp[i][j] = dp[i - 1][j - 1] + 1;
				} else {
					dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
				}
			}
		}

		// Backtrack to produce diff
		const raw: { type: 'unchanged' | 'added' | 'removed'; text: string }[] = [];
		let i = m, j = n;
		while (i > 0 || j > 0) {
			if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
				raw.push({ type: 'unchanged', text: oldLines[i - 1] });
				i--; j--;
			} else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
				raw.push({ type: 'added', text: newLines[j - 1] });
				j--;
			} else {
				raw.push({ type: 'removed', text: oldLines[i - 1] });
				i--;
			}
		}
		raw.reverse();

		let oldNum = 0, newNum = 0;
		for (const line of raw) {
			if (line.type === 'unchanged') {
				oldNum++; newNum++;
				result.push({ type: 'unchanged', oldNum, newNum, text: line.text });
			} else if (line.type === 'removed') {
				oldNum++;
				result.push({ type: 'removed', oldNum, newNum: 0, text: line.text });
			} else {
				newNum++;
				result.push({ type: 'added', oldNum: 0, newNum, text: line.text });
			}
		}

		return result;
	}

	function computeMetadataDiff(oldMeta: Record<string, unknown>, newMeta: Record<string, unknown>) {
		const result: { field: string; old: unknown; new: unknown }[] = [];
		const allKeys = new Set([...Object.keys(oldMeta), ...Object.keys(newMeta)]);
		for (const key of allKeys) {
			const oldVal = oldMeta[key];
			const newVal = newMeta[key];
			if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
				result.push({ field: key, old: oldVal, new: newVal });
			}
		}
		return result;
	}

	function formatValue(val: unknown): string {
		if (val === undefined || val === null) return '-';
		if (typeof val === 'string') return val || '-';
		if (typeof val === 'number' || typeof val === 'boolean') return String(val);
		if (Array.isArray(val)) return val.join(', ') || '-';
		return JSON.stringify(val);
	}

	function handleRestore() {
		const v = versions.find(v => v.id === newVersionId);
		if (v) onRestore?.(v);
	}

	function formatTime(ts: number): string {
		try { return dayjs(ts > 1e15 ? ts / 1e6 : ts > 1e12 ? ts : ts * 1e3).format('MM-DD HH:mm'); } catch { return ''; }
	}
</script>

<div class="fixed inset-0 z-50 bg-white dark:bg-gray-900 flex flex-col">
	<!-- Header -->
	<div class="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center gap-2">
			<button class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition" onclick={onClose}>
				<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
			</button>
			<h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">版本比较</h2>
		</div>
		{#if diffLines.length > 0}
			<button class="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition" onclick={handleRestore}>
				恢复到 {newVersionNumber}
			</button>
		{/if}
	</div>

	<!-- Version selectors -->
	<div class="flex items-center gap-4 px-4 py-3 border-b border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-850">
		<div class="flex items-center gap-2 flex-1">
			<span class="text-xs text-red-500 font-medium">旧版</span>
			<select class="flex-1 text-xs px-2 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg outline-none" bind:value={oldVersionId}>
				<option value="">选择旧版本</option>
				{#each versions as v (v.id)}
					{#if v.id !== newVersionId}
						<option value={v.id}>{(v.versionNumber ?? v.version_number)} — {(v.changeSummary ?? v.change_summary) || formatTime(v.createdAt ?? v.created_at)}</option>
					{/if}
				{/each}
			</select>
		</div>
		<svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
		<div class="flex items-center gap-2 flex-1">
			<span class="text-xs text-green-600 font-medium">新版</span>
			<select class="flex-1 text-xs px-2 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg outline-none" bind:value={newVersionId}>
				<option value="">选择新版本</option>
				{#each versions as v (v.id)}
					{#if v.id !== oldVersionId}
						<option value={v.id}>{(v.versionNumber ?? v.version_number)} — {(v.changeSummary ?? v.change_summary) || formatTime(v.createdAt ?? v.created_at)}</option>
					{/if}
				{/each}
			</select>
		</div>
		<button
			class="px-3 py-1.5 text-xs bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-40"
			onclick={runCompare}
			disabled={!oldVersionId || !newVersionId || comparing}
		>
			{comparing ? '加载中...' : '比较'}
		</button>
	</div>

	<!-- Diff content -->
	<div class="flex-1 overflow-auto">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
			</div>
		{:else if versions.length < 2}
			<div class="text-center py-12">
				<p class="text-sm text-gray-500">至少需要 2 个版本才能比较</p>
				<p class="text-xs text-gray-400 mt-1">保存文档后会自动创建版本快照</p>
			</div>
		{:else if diffLines.length > 0}
			<div class="font-mono text-xs leading-5">
				{#each diffLines as line (`${line.type}-${line.oldNum}-${line.newNum}-${line.text}`)}
					<div class="flex {line.type === 'added' ? 'bg-green-50 dark:bg-green-900/20' : line.type === 'removed' ? 'bg-red-50 dark:bg-red-900/20' : ''}">
						<span class="w-10 text-right pr-2 text-gray-400 select-none flex-shrink-0 {line.type === 'added' ? 'text-green-500' : line.type === 'removed' ? 'text-red-500' : ''}">{line.type === 'removed' ? line.oldNum : line.type === 'added' ? line.newNum : line.oldNum}</span>
						<span class="w-5 text-center select-none flex-shrink-0 {line.type === 'added' ? 'text-green-600' : line.type === 'removed' ? 'text-red-600' : 'text-gray-300'}">{line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}</span>
						<span class="flex-1 whitespace-pre-wrap break-all {line.type === 'added' ? 'text-green-800 dark:text-green-300' : line.type === 'removed' ? 'text-red-800 dark:text-red-300' : 'text-gray-700 dark:text-gray-300'}">{line.text || ' '}</span>
					</div>
				{/each}
			</div>
			{#if metadataDiff.length > 0}
				<div class="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4">
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">元数据变更</h3>
					<div class="space-y-1">
						{#each metadataDiff as diff}
							<div class="flex items-center gap-2 text-xs">
								<span class="font-medium text-gray-700 dark:text-gray-300 w-24">{diff.field}</span>
								<span class="text-red-600 dark:text-red-400 line-through flex-1 truncate">{formatValue(diff.old)}</span>
								<span class="text-green-600 dark:text-green-400 flex-1 truncate">{formatValue(diff.new)}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{:else}
			<div class="text-center py-12">
				<p class="text-sm text-gray-500">选择两个版本后点击"比较"按钮</p>
			</div>
		{/if}
	</div>
</div>
