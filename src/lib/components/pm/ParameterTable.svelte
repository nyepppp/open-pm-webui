<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { createEntry, deleteEntry, updateEntry } from '$lib/apis/pm/index';
	import type { ModuleEntry, ModuleStatus, Priority } from '$lib/apis/pm/types';

	interface Props {
		entries: ModuleEntry[];
		projectId: string;
		filterModule?: string | null;
		filterFeature?: string | null;
		onDataChange?: () => void;
	}

	let {
		entries = [],
		projectId = '',
		filterModule = null,
		filterFeature = null,
		onDataChange
	}: Props = $props();

	// Filter entries by selected module/feature
	let filteredEntries = $derived.by(() => {
		let result = entries;
		if (filterModule) {
			result = result.filter(e => (e.data?.moduleName as string) === filterModule);
		}
		if (filterFeature) {
			result = result.filter(e => (e.data?.featureName as string) === filterFeature);
		}
		return result;
	});

	// New parameter form
	let showNewForm = $state(false);
	let newTitle = $state('');
	let newParamKey = $state('');
	let newParamType = $state<'input' | 'output' | 'config'>('config');
	let newDataType = $state<'string' | 'number' | 'boolean' | 'object' | 'array'>('string');
	let newDefaultValue = $state('');
	let newHasDefaultValue = $state(false);
	let newParamRequired = $state(true);
	let newParamDescription = $state('');
	let newModuleName = $state('');
	let newFeatureName = $state('');

	// Pre-fill module/feature from filter
	$effect(() => {
		if (filterModule && !newModuleName) newModuleName = filterModule;
		if (filterFeature && !newFeatureName) newFeatureName = filterFeature;
	});

	// Module/feature options from all entries
	let moduleOptions = $derived([...new Set(entries.map(e => (e.data?.moduleName as string || '')).filter(Boolean))].sort());
	let featureOptionsForModule = $derived(newModuleName ? [...new Set(entries.filter(e => (e.data?.moduleName as string) === newModuleName).map(e => (e.data?.featureName as string || '')).filter(Boolean))].sort() : []);

	// Edit drawer
	let showEditDrawer = $state(false);
	let editEntry = $state<ModuleEntry | null>(null);
	let editTitle = $state('');
	let editStatus = $state<ModuleStatus>('draft');
	let editPriority = $state<Priority>('p2');

	// Status/priority maps
	const statusMap: Record<string, { l: string; c: string }> = {
		draft: { l: '草稿', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' },
		review: { l: '评审中', c: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
		approved: { l: '已批准', c: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		archived: { l: '已归档', c: 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500' }
	};
	const prioMap: Record<string, { l: string; c: string }> = {
		p0: { l: 'P0', c: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' },
		p1: { l: 'P1', c: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400' },
		p2: { l: 'P2', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		p3: { l: 'P3', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' }
	};
	const paramTypeMap: Record<string, { l: string; c: string }> = {
		input: { l: '输入', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		output: { l: '输出', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		config: { l: '配置', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' }
	};

	function getEntryData(entry: ModuleEntry, key: string): string {
		return (entry.data || entry.metadata || {})[key] ?? '';
	}

	async function handleCreate() {
		if (!newTitle.trim()) return;
		try {
			const token = localStorage.token || '';
			await createEntry(token, projectId, {
				module_type: 'parameter',
				title: newTitle,
				status: 'draft',
				priority: 'p2',
				data: {
					key: newParamKey,
					paramType: newParamType,
					dataType: newDataType,
					defaultValue: newHasDefaultValue ? newDefaultValue : '',
					hasDefaultValue: newHasDefaultValue ? 1 : 0,
					required: newParamRequired ? 1 : 0,
					description: newParamDescription,
					moduleName: newModuleName,
					featureName: newFeatureName
				}
			});
			resetForm();
			onDataChange?.();
			toast.success('创建成功');
		} catch (e: any) {
			toast.error(e.message || '创建失败');
		}
	}

	function resetForm() {
		newTitle = '';
		newParamKey = '';
		newParamType = 'config';
		newDataType = 'string';
		newDefaultValue = '';
		newHasDefaultValue = false;
		newParamRequired = true;
		newParamDescription = '';
		newModuleName = filterModule || '';
		newFeatureName = filterFeature || '';
		showNewForm = false;
	}

	async function handleDelete(entryId: string) {
		try {
			const token = localStorage.token || '';
			await deleteEntry(token, entryId);
			onDataChange?.();
			toast.success('删除成功');
		} catch (e: any) {
			toast.error(e.message || '删除失败');
		}
	}

	function openEditDrawer(entry: ModuleEntry) {
		editEntry = entry;
		editTitle = entry.title || '';
		editStatus = entry.status || 'draft';
		editPriority = entry.priority || 'p2';
		showEditDrawer = true;
	}

	async function saveEditDrawer() {
		if (!editEntry) return;
		try {
			const token = localStorage.token || '';
			await updateEntry(token, editEntry.id, {
				title: editTitle,
				status: editStatus,
				priority: editPriority,
				data: { ...(editEntry.data || {}) }
			});
			showEditDrawer = false;
			editEntry = null;
			onDataChange?.();
			toast.success('更新成功');
		} catch (e: any) {
			toast.error(e.message || '更新失败');
		}
	}
</script>

<div class="flex flex-col h-full">
	<!-- Header bar -->
	<div class="flex items-center gap-2 mb-3">
		<div class="text-sm text-gray-500 dark:text-gray-400">
			{filteredEntries.length} 个参数
			{#if filterModule}<span class="ml-1">· {filterModule}</span>{/if}
			{#if filterFeature}<span> / {filterFeature}</span>{/if}
		</div>
		<div class="flex-1"></div>
		<button
			class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
			onclick={() => { showNewForm = true; newModuleName = filterModule || ''; newFeatureName = filterFeature || ''; }}
		>
			+ 添加参数
		</button>
	</div>

	<!-- New parameter form -->
	{#if showNewForm}
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-3 border border-gray-200 dark:border-gray-700">
			<div class="grid grid-cols-2 md:grid-cols-3 gap-3">
				<div>
					<label class="block text-xs text-gray-500 mb-1">参数名 *</label>
					<input type="text" class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newTitle} placeholder="参数名称">
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">Key</label>
					<input type="text" class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newParamKey} placeholder="参数标识符">
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">所属模块</label>
					<input type="text" list="module-options" class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newModuleName} placeholder="选择或输入模块名">
					<datalist id="module-options">
						{#each moduleOptions as opt}
							<option value={opt} />
						{/each}
					</datalist>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">所属功能</label>
					<input type="text" list="feature-options" class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newFeatureName} placeholder="选择或输入功能名">
					<datalist id="feature-options">
						{#each featureOptionsForModule as opt}
							<option value={opt} />
						{/each}
					</datalist>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">参数类型</label>
					<select class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newParamType}>
						<option value="config">配置参数</option>
						<option value="input">输入参数</option>
						<option value="output">输出参数</option>
					</select>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">数据类型</label>
					<select class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newDataType}>
						<option value="string">string</option>
						<option value="number">number</option>
						<option value="boolean">boolean</option>
						<option value="object">object</option>
						<option value="array">array</option>
					</select>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">默认值</label>
					<input type="text" class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newDefaultValue} placeholder="默认值">
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">说明</label>
					<input type="text" class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={newParamDescription} placeholder="参数用途说明">
				</div>
			</div>
			<div class="flex gap-2 mt-3">
				<button class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg" onclick={handleCreate}>创建</button>
				<button class="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg" onclick={resetForm}>取消</button>
			</div>
		</div>
	{/if}

	<!-- Parameter list -->
	{#if filteredEntries.length === 0}
		<div class="flex items-center justify-center h-32 text-gray-400 dark:text-gray-500 text-sm">
			{#if filterModule || filterFeature}
				该功能下暂无参数
			{:else}
				暂无参数，点击"添加参数"开始
			{/if}
		</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-gray-200 dark:border-gray-700">
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">参数名</th>
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Key</th>
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">类型</th>
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">数据类型</th>
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">默认值</th>
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">必填</th>
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">说明</th>
						<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">状态</th>
						<th class="px-3 py-2 text-right text-xs font-medium text-gray-500">操作</th>
					</tr>
				</thead>
				<tbody>
					{#each filteredEntries as entry (entry.id)}
						<tr class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
							<td class="px-3 py-2 font-medium text-gray-900 dark:text-white">{entry.title}</td>
							<td class="px-3 py-2 text-gray-600 dark:text-gray-400 font-mono text-xs">{getEntryData(entry, 'key')}</td>
							<td class="px-3 py-2">
								<span class="px-1.5 py-0.5 rounded text-xs {paramTypeMap[getEntryData(entry, 'paramType')]?.c || ''}">{paramTypeMap[getEntryData(entry, 'paramType')]?.l || getEntryData(entry, 'paramType')}</span>
							</td>
							<td class="px-3 py-2 text-gray-600 dark:text-gray-400">{getEntryData(entry, 'dataType')}</td>
							<td class="px-3 py-2 text-gray-600 dark:text-gray-400 text-xs">{getEntryData(entry, 'defaultValue') || '-'}</td>
							<td class="px-3 py-2 text-gray-600 dark:text-gray-400">{getEntryData(entry, 'required') === '1' || getEntryData(entry, 'required') === 1 ? '是' : '否'}</td>
							<td class="px-3 py-2 text-gray-600 dark:text-gray-400 max-w-[200px] truncate">{getEntryData(entry, 'description') || '-'}</td>
							<td class="px-3 py-2">
								<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || ''}">{statusMap[entry.status]?.l || entry.status}</span>
							</td>
							<td class="px-3 py-2 text-right">
								<button class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 mr-2" onclick={() => openEditDrawer(entry)}>编辑</button>
								<button class="text-xs text-red-600 hover:text-red-800 dark:text-red-400" onclick={() => handleDelete(entry.id)}>删除</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<!-- Edit drawer -->
{#if showEditDrawer && editEntry}
	<div class="fixed inset-0 z-50 bg-black/30" onclick={() => { showEditDrawer = false; editEntry = null; }}>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-xl p-6 overflow-y-auto"
			onclick={(e) => e.stopPropagation()}
		>
			<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">编辑参数</h3>
			<div class="space-y-3">
				<div>
					<label class="block text-xs text-gray-500 mb-1">参数名</label>
					<input type="text" class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={editTitle}>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">状态</label>
					<select class="w-full px-2 py-1.5 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800" bind:value={editStatus}>
						<option value="draft">草稿</option>
						<option value="review">评审中</option>
						<option value="approved">已批准</option>
						<option value="archived">已归档</option>
					</select>
				</div>
				<div>
					<label class="block text-xs text-gray-500 mb-1">优先级</label>
					<div class="flex gap-1">
						{#each ['p0', 'p1', 'p2', 'p3'] as p}
							<button
								class="px-2 py-1 text-xs rounded {editPriority === p ? (prioMap[p]?.c || '') : 'bg-gray-100 dark:bg-gray-800 text-gray-500'}"
								onclick={() => { editPriority = p as Priority; }}
							>{prioMap[p]?.l || p}</button>
						{/each}
					</div>
				</div>
			</div>
			<div class="flex gap-2 mt-6">
				<button class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg" onclick={saveEditDrawer}>保存</button>
				<button class="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg" onclick={() => { showEditDrawer = false; editEntry = null; }}>取消</button>
			</div>
		</div>
	</div>
{/if}
