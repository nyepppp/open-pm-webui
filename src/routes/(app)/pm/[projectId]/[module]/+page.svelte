<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';
	import { getEntries, createEntry, deleteEntry, updateEntry, getEntry } from '$lib/apis/pm/index';
	import { currentVersion } from '$lib/stores/pm/versionStore';
	import { createNewNote } from '$lib/apis/notes/index';
	import type { ModuleType, ModuleStatus, Priority, PRDSection } from '$lib/apis/pm/types';

	let projectId = $derived($page.params.projectId);
	let moduleType = $derived($page.params.module as ModuleType);

	const moduleConfig: Record<string, { name: string; editorType: 'rich' | 'table'; tableColumns?: { key: string; label: string; width?: string }[] }> = {
		requirement: { name: '需求管理', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-20' }, { key: 'title', label: '标题' },
			{ key: 'source', label: '来源', width: 'w-20' }, { key: 'category', label: '分类', width: 'w-24' },
			{ key: 'status', label: '状态', width: 'w-20' }, { key: 'updatedAt', label: '更新', width: 'w-28' }
		]},
		parameter: { name: '参数配置', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-20' }, { key: 'title', label: '参数名' },
			{ key: 'paramKey', label: 'Key', width: 'w-28' }, { key: 'paramType', label: '类型', width: 'w-20' },
			{ key: 'dataType', label: '数据类型', width: 'w-20' }, { key: 'defaultValue', label: '默认值', width: 'w-24' },
			{ key: 'status', label: '状态', width: 'w-20' }
		]},
		testcase: { name: '测试用例', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-20' }, { key: 'title', label: '用例标题' },
			{ key: 'caseType', label: '类型', width: 'w-20' }, { key: 'scenario', label: '场景', width: 'w-28' },
			{ key: 'status', label: '状态', width: 'w-20' }, { key: 'updatedAt', label: '更新', width: 'w-28' }
		]},
		prd: { name: 'PRD 文档', editorType: 'rich' },
		risk: { name: '风险分析', editorType: 'rich' },
		competitor: { name: '竞品分析', editorType: 'rich' },
		roadmap: { name: '产品路线图', editorType: 'rich' },
		meeting: { name: '会议纪要', editorType: 'rich' },
		acceptance: { name: '验收报告', editorType: 'rich' },
		faq: { name: 'FAQ', editorType: 'rich' },
		'product-architecture': { name: '产品架构', editorType: 'rich' }
	};

	let config = $derived(moduleConfig[moduleType] || { name: '未知模块', editorType: 'rich' });
	let entries = $state<any[]>([]);
	let isLoading = $state(true);
	let query = $state('');
	let showNewForm = $state(false);
	let newTitle = $state('');
	let newContent = $state('');
	let newPriority = $state<Priority>('p2');
	let newStatus = $state<ModuleStatus>('draft');
	let newParamKey = $state('');
	let newParamType = $state<'input' | 'output' | 'config'>('config');
	let newDataType = $state<'string' | 'number' | 'boolean' | 'object' | 'array'>('string');
	let newDefaultValue = $state('');
	let newCaseType = $state<'functional' | 'boundary' | 'exception' | 'performance'>('functional');
	let newScenario = $state('');
	let newSource = $state<'manual' | 'excel' | 'agent'>('manual');
	let newCategory = $state('');

	async function loadEntries() { isLoading = true; try { const token = localStorage.token || ''; entries = await getEntries(token, projectId, moduleType); } catch { entries = []; } finally { isLoading = false; } }
	onMount(() => { loadEntries(); });
	$effect(() => { moduleType; showNewForm = false; loadEntries(); });

	async function handleCreate() {
		if (!newTitle.trim()) return;
		try {
			const token = localStorage.token || '';
			const data: Record<string, unknown> = { module_type: moduleType, title: newTitle, content: newContent || undefined, status: newStatus, priority: newPriority };
			if (moduleType === 'parameter') data.data = { key: newParamKey, paramType: newParamType, dataType: newDataType, defaultValue: newDefaultValue };
			else if (moduleType === 'testcase') data.data = { caseType: newCaseType, scenario: newScenario };
			else if (moduleType === 'requirement') data.data = { source: newSource, category: newCategory };
			await createEntry(token, projectId, data);
			resetForm(); await loadEntries(); toast.success('创建成功');
		} catch (e: any) { toast.error(e.message || '创建失败'); }
	}
	function resetForm() { newTitle = ''; newContent = ''; newPriority = 'p2'; newStatus = 'draft'; newParamKey = ''; newParamType = 'config'; newDataType = 'string'; newDefaultValue = ''; newCaseType = 'functional'; newScenario = ''; newSource = 'manual'; newCategory = ''; showNewForm = false; }
	async function handleDelete(entryId: string) { try { const token = localStorage.token || ''; await deleteEntry(token, entryId); await loadEntries(); toast.success('删除成功'); } catch (e: any) { toast.error(e.message || '删除失败'); } }
	async function handleExportToNote(entry: any) { try { const token = localStorage.token || ''; await createNewNote(token, { title: `[PM] ${entry.title}`, data: { content: { md: entry.content || '', html: '', json: null } }, meta: null, access_grants: [] }); toast.success('已导出为笔记'); } catch (e: any) { toast.error(e.message || '导出失败'); } }
	function handleExportToWorkspace() { toast.info('导出到工作空间功能开发中'); }

	let filteredEntries = $derived(query ? entries.filter(e => e.title.toLowerCase().includes(query.toLowerCase())) : entries);
	function formatTime(ts: number): string { try { return dayjs(ts / 1_000_000).fromNow(); } catch { return ''; } }
	function getEntryData(entry: any, key: string): string { return (entry.data || entry.metadata || {})[key] ?? ''; }

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
	const sourceMap: Record<string, { l: string; c: string }> = {
		manual: { l: '手动', c: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
		excel: { l: 'Excel', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		agent: { l: 'AI', c: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' }
	};
	const paramTypeMap: Record<string, { l: string; c: string }> = {
		input: { l: '输入', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		output: { l: '输出', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		config: { l: '配置', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' }
	};
	const caseTypeMap: Record<string, { l: string; c: string }> = {
		functional: { l: '功能', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		boundary: { l: '边界', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
		exception: { l: '异常', c: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' },
		performance: { l: '性能', c: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' }
	};
	const INACTIVE = 'bg-gray-100 dark:bg-gray-700 text-gray-500';
	let isTableView = $derived(config.editorType === 'table');
	function prioBtnCls(p: string) { return newPriority === p ? (prioMap[p]?.c || '') : INACTIVE; }
	function srcBtnCls(s: string) { return newSource === s ? (sourceMap[s]?.c || '') : INACTIVE; }
	function ptBtnCls(pt: string) { return newParamType === pt ? (paramTypeMap[pt]?.c || '') : INACTIVE; }
	function ctBtnCls(ct: string) { return newCaseType === ct ? (caseTypeMap[ct]?.c || '') : INACTIVE; }

	// PRD inline editor
	let editingEntryId = $state<string | null>(null);
	let editingEntry = $state<any>(null);
	let editingSections = $state<PRDSection[]>([]);
	let editingActiveSection = $state<string>('');
	let editingDocTitle = $state('');
	let editingDocStatus = $state<ModuleStatus>('draft');
	const defaultSections: PRDSection[] = [
		{ id: '1', type: 'overview', title: '概述', content: '', parameters: [], order: 0 },
		{ id: '2', type: 'background', title: '背景', content: '', parameters: [], order: 1 },
		{ id: '3', type: 'goal', title: '目标', content: '', parameters: [], order: 2 },
		{ id: '4', type: 'requirement', title: '需求', content: '', parameters: [], order: 3 },
		{ id: '5', type: 'non_functional', title: '非功能需求', content: '', parameters: [], order: 4 },
		{ id: '6', type: 'appendix', title: '附录', content: '', parameters: [], order: 5 }
	];
	const sectionTypeLabels: Record<string, string> = { overview: '概述', background: '背景', goal: '目标', requirement: '需求', non_functional: '非功能', appendix: '附录' };
	async function openPrdEditor(entryId: string) {
		try { const token = localStorage.token || ''; editingEntry = await getEntry(token, entryId); editingDocTitle = editingEntry.title; editingDocStatus = editingEntry.status || 'draft'; const data = editingEntry.data || editingEntry.metadata || {}; editingSections = data.sections?.length ? data.sections : [...defaultSections]; editingActiveSection = editingSections[0]?.id || ''; editingEntryId = entryId; }
		catch (e: any) { toast.error(e.message || '加载文档失败'); }
	}
	function closePrdEditor() { editingEntryId = null; editingEntry = null; editingSections = []; editingActiveSection = ''; }
	async function savePrdDoc() {
		if (!editingEntryId) return;
		try { const token = localStorage.token || ''; await updateEntry(token, editingEntryId, { title: editingDocTitle, status: editingDocStatus, data: { sections: editingSections } }); toast.success('文档已保存'); await loadEntries(); }
		catch (e: any) { toast.error(e.message || '保存失败'); }
	}
	let activeSection = $derived(editingSections.find(s => s.id === editingActiveSection) ?? null);
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>{config.name}</div>
				<div class="text-lg font-medium text-gray-500">{filteredEntries.length}</div>
			</div>
			<div class="flex w-full justify-end gap-1.5">
				{#if !showNewForm}
					<button class="px-2 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black transition font-medium text-sm flex items-center" onclick={() => { showNewForm = true; }}>
						<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
						<div class="ml-1 text-xs">新建</div>
					</button>
				{/if}
			</div>
		</div>
	</div>

	<div class="py-2 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30">
		<div class="px-3.5 flex flex-1 items-center w-full space-x-2 py-0.5 pb-2">
			<div class="flex flex-1 items-center">
				<div class="self-center ml-1 mr-3"><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></div>
				<input class="w-full text-sm py-1 rounded-r-xl outline-hidden bg-transparent" bind:value={query} placeholder="搜索..." />
				{#if query}<button class="p-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-900 transition" onclick={() => { query = ''; }} aria-label="清除"><svg class="size-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>{/if}
			</div>
		</div>

		{#if showNewForm}
			<div class="px-3.5 pb-3">
				<div class="border border-gray-200 dark:border-gray-700 rounded-2xl p-3 space-y-2">
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="标题" bind:value={newTitle} onkeydown={(e) => { if (e.key === 'Enter' && newTitle.trim()) handleCreate(); }} />
					<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" placeholder="内容（可选）" rows="2" bind:value={newContent}></textarea>
					<div class="flex items-center gap-2">
						<span class="text-xs text-gray-500">优先级：</span>
						{#each ['p0','p1','p2','p3'] as p}
							<button class="px-1.5 py-0.5 text-xs rounded transition {prioBtnCls(p)}" onclick={() => { newPriority = p as Priority; }}>{prioMap[p].l}</button>
						{/each}
					</div>
					{#if moduleType === 'parameter'}
						<div class="flex items-center gap-2">
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="参数 Key" bind:value={newParamKey} />
							<div class="flex items-center gap-1">
								{#each ['input', 'output', 'config'] as pt}
									<button class="px-1.5 py-0.5 text-xs rounded transition {ptBtnCls(pt)}" onclick={() => { newParamType = pt as any; }}>{paramTypeMap[pt].l}</button>
								{/each}
							</div>
						</div>
						<div class="flex items-center gap-2">
							<select class="text-sm px-2 py-1 bg-gray-50 dark:bg-gray-850 border-0 rounded-lg outline-hidden" bind:value={newDataType}>
								{#each ['string', 'number', 'boolean', 'object', 'array'] as dt}<option value={dt}>{dt}</option>{/each}
							</select>
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="默认值" bind:value={newDefaultValue} />
						</div>
					{:else if moduleType === 'testcase'}
						<div class="flex items-center gap-1">
							<span class="text-xs text-gray-500">用例类型：</span>
							{#each ['functional', 'boundary', 'exception', 'performance'] as ct}
								<button class="px-1.5 py-0.5 text-xs rounded transition {ctBtnCls(ct)}" onclick={() => { newCaseType = ct as any; }}>{caseTypeMap[ct].l}</button>
							{/each}
						</div>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="测试场景" bind:value={newScenario} />
					{:else if moduleType === 'requirement'}
						<div class="flex items-center gap-2">
							<div class="flex items-center gap-1">
								<span class="text-xs text-gray-500">来源：</span>
								{#each ['manual', 'excel', 'agent'] as s}
									<button class="px-1.5 py-0.5 text-xs rounded transition {srcBtnCls(s)}" onclick={() => { newSource = s as any; }}>{sourceMap[s].l}</button>
								{/each}
							</div>
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="分类" bind:value={newCategory} />
						</div>
					{/if}
					<div class="flex justify-end gap-2">
						<button class="px-3 py-1.5 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={resetForm}>取消</button>
						<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-50" onclick={handleCreate} disabled={!newTitle.trim()}>创建</button>
					</div>
				</div>
			</div>
		{/if}

		{#if isLoading}
			<div class="flex items-center justify-center py-12"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div></div>
		{:else if filteredEntries.length === 0}
			<div class="py-12 text-center">
				<p class="text-sm text-gray-500 dark:text-gray-400">{query ? '没有找到匹配的条目' : `还没有${config.name}条目`}</p>
				{#if !query && !showNewForm}<button class="mt-3 px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-xl transition" onclick={() => { showNewForm = true; }}>创建第一个条目</button>{/if}
			</div>
		{:else if isTableView}
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead><tr class="border-b border-gray-100 dark:border-gray-800">
						{#if config.tableColumns}{#each config.tableColumns as col (col.key)}<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase {col.width || ''}">{col.label}</th>{/each}{/if}
						<th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-24">操作</th>
					</tr></thead>
					<tbody>{#each filteredEntries as entry (entry.id)}
						<tr class="border-b border-gray-50 dark:border-gray-850/30 hover:bg-gray-50 dark:hover:bg-gray-850 transition">
							{#if config.tableColumns}{#each config.tableColumns as col (col.key)}
								<td class="px-4 py-2.5 {col.width || ''}">
									{#if col.key === 'priority'}
										<span class="px-1.5 py-0.5 rounded text-xs {prioMap[entry.priority]?.c || prioMap.p2.c}">{prioMap[entry.priority]?.l || 'P2'}</span>
									{:else if col.key === 'title'}
										<span class="font-medium text-gray-900 dark:text-gray-100 max-w-xs truncate block">{entry.title}</span>
									{:else if col.key === 'status'}
										<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || statusMap.draft.c}">{statusMap[entry.status]?.l || '草稿'}</span>
									{:else if col.key === 'updatedAt'}
										<span class="text-gray-500 whitespace-nowrap">{formatTime(entry.updated_at || entry.updatedAt)}</span>
									{:else if col.key === 'source'}
										{@const src = getEntryData(entry, 'source')}
										<span class="px-1.5 py-0.5 rounded text-xs {sourceMap[src]?.c || INACTIVE}">{sourceMap[src]?.l || src || '-'}</span>
									{:else if col.key === 'category'}
										<span class="text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'category') || '-'}</span>
									{:else if col.key === 'paramKey'}
										<code class="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded font-mono">{getEntryData(entry, 'key') || '-'}</code>
									{:else if col.key === 'paramType'}
										{@const pt = getEntryData(entry, 'paramType')}
										<span class="px-1.5 py-0.5 rounded text-xs {paramTypeMap[pt]?.c || INACTIVE}">{paramTypeMap[pt]?.l || pt || '-'}</span>
									{:else if col.key === 'dataType'}
										<span class="text-xs text-gray-600 dark:text-gray-400 font-mono">{getEntryData(entry, 'dataType') || '-'}</span>
									{:else if col.key === 'defaultValue'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'defaultValue') || '-'}</span>
									{:else if col.key === 'caseType'}
										{@const ct = getEntryData(entry, 'caseType')}
										<span class="px-1.5 py-0.5 rounded text-xs {caseTypeMap[ct]?.c || INACTIVE}">{caseTypeMap[ct]?.l || ct || '-'}</span>
									{:else if col.key === 'scenario'}
										<span class="text-gray-600 dark:text-gray-400 truncate block max-w-28">{getEntryData(entry, 'scenario') || '-'}</span>
									{/if}
								</td>
							{/each}{/if}
							<td class="px-4 py-2.5 text-right"><div class="flex items-center justify-end gap-1">
								{#if moduleType === 'parameter'}
									<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title="导出到工作空间" onclick={() => handleExportToWorkspace()}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg></button>
								{/if}
								<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title="导出为笔记" onclick={() => handleExportToNote(entry)}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm0 5.25h.007v.008H3.75V12zm0 5.25h.007v.008H3.75V17.25z" /></svg></button>
								<button class="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition" title="删除" onclick={() => handleDelete(entry.id)}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg></button>
							</div></td>
						</tr>
					{/each}</tbody>
				</table>
			</div>
		{:else}
			<div class="px-2.5 py-1 gap-1.5 flex flex-col">{#each filteredEntries as entry (entry.id)}
				<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
				<div class="flex cursor-pointer w-full px-3.5 py-1.5 border border-gray-50 dark:border-gray-850/30 bg-transparent dark:hover:bg-gray-850 hover:bg-white rounded-2xl transition group" role="button" tabindex="0" onclick={() => { if (moduleType === 'prd') openPrdEditor(entry.id); }} onkeydown={(e) => { if (e.key === 'Enter' && moduleType === 'prd') openPrdEditor(entry.id); }}>
					<div class="w-full flex flex-col justify-between"><div class="flex-1">
						<div class="flex items-center gap-2 self-center justify-between">
							<div class="text-sm font-medium capitalize flex-1 w-full line-clamp-1">{entry.title}</div>
							<div class="flex shrink-0 items-center text-xs gap-2">
								{#if entry.priority}<span class="px-1.5 py-0.5 rounded text-xs {prioMap[entry.priority]?.c || ''}">{prioMap[entry.priority]?.l || ''}</span>{/if}
								<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || statusMap.draft.c}">{statusMap[entry.status]?.l || '草稿'}</span>
								{#if moduleType === 'parameter' && getEntryData(entry, 'paramType')}
									{@const pt = getEntryData(entry, 'paramType')}
									<span class="px-1.5 py-0.5 rounded text-xs {paramTypeMap[pt]?.c || ''}">{paramTypeMap[pt]?.l || ''}</span>
								{:else if moduleType === 'testcase' && getEntryData(entry, 'caseType')}
									{@const ct = getEntryData(entry, 'caseType')}
									<span class="px-1.5 py-0.5 rounded text-xs {caseTypeMap[ct]?.c || ''}">{caseTypeMap[ct]?.l || ''}</span>
								{:else if moduleType === 'requirement' && getEntryData(entry, 'source')}
									{@const src = getEntryData(entry, 'source')}
									<span class="px-1.5 py-0.5 rounded text-xs {sourceMap[src]?.c || ''}">{sourceMap[src]?.l || ''}</span>
								{/if}
								<span class="text-gray-500">{formatTime(entry.updated_at || entry.updatedAt)}</span>
								{#if moduleType === 'parameter'}
									<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition opacity-0 group-hover:opacity-100" title="导出到工作空间" onclick={(e) => { e.stopPropagation(); handleExportToWorkspace(); }}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg></button>
								{/if}
								<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition opacity-0 group-hover:opacity-100" title="导出为笔记" onclick={(e) => { e.stopPropagation(); handleExportToNote(entry); }}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm0 5.25h.007v.008H3.75V12zm0 5.25h.007v.008H3.75V17.25z" /></svg></button>
								<button class="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition opacity-0 group-hover:opacity-100" title="删除" onclick={(e) => { e.stopPropagation(); handleDelete(entry.id); }}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg></button>
							</div>
						</div>
						{#if entry.content}<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">{entry.content}</div>{/if}
					</div></div>
				</div>
			{/each}</div>
		{/if}
	</div>
</div>

<!-- PRD Inline Editor -->
{#if moduleType === 'prd' && editingEntryId}
	<div class="fixed inset-0 z-50 bg-white dark:bg-gray-900 flex flex-col">
		<div class="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700">
			<div class="flex items-center gap-3">
				<button class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition" onclick={closePrdEditor} title="返回"><svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg></button>
				<input type="text" class="text-sm font-medium bg-transparent border-0 outline-none flex-1 max-w-md text-gray-900 dark:text-gray-100" bind:value={editingDocTitle} placeholder="文档标题" />
				<span class="px-2 py-0.5 text-xs rounded {statusMap[editingDocStatus]?.c || statusMap.draft.c}">{statusMap[editingDocStatus]?.l || '草稿'}</span>
			</div>
			<div class="flex items-center gap-2">
				<select class="text-xs px-2 py-1 bg-gray-50 dark:bg-gray-800 border-0 rounded-lg outline-hidden" bind:value={editingDocStatus}>{#each ['draft', 'review', 'approved', 'archived'] as s}<option value={s}>{statusMap[s]?.l || s}</option>{/each}</select>
				<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg font-medium" onclick={savePrdDoc}>保存</button>
				<button class="px-3 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg" onclick={() => handleExportToNote(editingEntry)}>导出为笔记</button>
			</div>
		</div>
		<div class="flex flex-1 overflow-hidden">
			<div class="w-56 flex-shrink-0 border-r border-gray-100 dark:border-gray-800 overflow-y-auto p-3">
				<div class="text-xs font-semibold text-gray-500 uppercase mb-2">章节大纲</div>
				<div class="space-y-0.5">
					{#each editingSections as sec (sec.id)}
						<button class="w-full flex items-center gap-2 px-2.5 py-2 text-sm rounded-lg transition text-left {editingActiveSection === sec.id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-medium' : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'}" onclick={() => { editingActiveSection = sec.id; }}>
							<span class="w-5 h-5 rounded text-[10px] flex items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-500 flex-shrink-0">{sec.order + 1}</span>
							<span class="truncate">{sec.title || sectionTypeLabels[sec.type] || sec.type}</span>
						</button>
					{/each}
				</div>
				<button class="w-full mt-3 px-2.5 py-2 text-xs rounded-lg border border-dashed border-gray-300 dark:border-gray-700 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition" onclick={() => { const ns: PRDSection = { id: Date.now().toString(), type: 'appendix', title: '新章节', content: '', parameters: [], order: editingSections.length }; editingSections = [...editingSections, ns]; editingActiveSection = ns.id; }}>+ 添加章节</button>
			</div>
			<div class="flex-1 overflow-y-auto p-6">
				{#if activeSection}
					<div class="max-w-3xl mx-auto">
						<div class="flex items-center gap-2 mb-4">
							<span class="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-800 text-gray-500">{sectionTypeLabels[activeSection.type] || activeSection.type}</span>
							<input type="text" class="flex-1 text-lg font-semibold bg-transparent border-0 outline-none text-gray-900 dark:text-gray-100" bind:value={activeSection.title} oninput={(e) => { const idx = editingSections.findIndex(s => s.id === activeSection.id); if (idx >= 0) { editingSections[idx] = { ...editingSections[idx], title: (e.target as HTMLInputElement).value }; editingSections = [...editingSections]; } }} />
							{#if editingSections.length > 1}
								<button class="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition" title="删除章节" onclick={() => { editingSections = editingSections.filter(s => s.id !== activeSection.id); if (editingActiveSection === activeSection.id) editingActiveSection = editingSections[0]?.id || ''; }}><svg class="w-4 h-4 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg></button>
							{/if}
						</div>
						<textarea class="w-full min-h-[60vh] text-sm leading-relaxed bg-transparent border-0 outline-none resize-none text-gray-800 dark:text-gray-200 font-mono" placeholder="在此编写章节内容..." bind:value={activeSection.content} oninput={(e) => { const idx = editingSections.findIndex(s => s.id === activeSection.id); if (idx >= 0) { editingSections[idx] = { ...editingSections[idx], content: (e.target as HTMLTextAreaElement).value }; editingSections = [...editingSections]; } }}></textarea>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
