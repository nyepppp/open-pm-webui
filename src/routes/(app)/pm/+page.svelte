<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';
	import { getProjects, createProject, deleteProject, updateProject, getVersions } from '$lib/apis/pm/index';
	import type { Project } from '$lib/apis/pm/types';

	let projects = $state<Project[]>([]);
	let projectVersionMap = $state<Record<string, string>>({});
	let isLoading = $state(true);
	let query = $state('');
	let showNewForm = $state(false);
	let newProjectName = $state('');
	let newProjectDesc = $state('');
	let newProjectType = $state<'prd' | 'competitor' | 'general'>('general');

	let isCreating = $state(false);

	// Inline edit state
	let editingProjectId = $state<string | null>(null);
	let editName = $state('');
	let editDesc = $state('');
	let isSaving = $state(false);

	async function loadProjects() {
		isLoading = true;
		try {
			const token = localStorage.token || '';
			projects = await getProjects(token);
			// Defensive dedup: filter out any duplicate project IDs
			const seen = new Set<string>();
			projects = projects.filter(p => {
				if (seen.has(p.id)) return false;
				seen.add(p.id);
				return true;
			});
			// Load current version for each project
			const versionEntries = await Promise.all(
				projects.map(async (p) => {
					try {
						const versions = await getVersions(token, p.id);
						const latest = versions?.[0];
						return [p.id, latest?.versionNumber || latest?.version_number || ''] as [string, string];
					} catch {
						return [p.id, ''] as [string, string];
					}
				})
			);
			projectVersionMap = Object.fromEntries(versionEntries);
		} catch {
			projects = [];
			projectVersionMap = {};
		} finally {
			isLoading = false;
		}
	}

	onMount(() => { loadProjects(); });

	async function handleCreate() {
		if (!newProjectName.trim() || isCreating) return;
		isCreating = true;
		try {
			const token = localStorage.token || '';
			await createProject(token, { name: newProjectName, description: newProjectDesc || undefined });
			newProjectName = '';
			newProjectDesc = '';
			showNewForm = false;
			await loadProjects();
			toast.success('项目创建成功');
		} catch (e: any) {
			const msg = e?.message || '';
			const statusCode = e?.status;
			if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('fetch')) {
				toast.error('无法连接服务器，请检查后端是否已启动');
			} else if (statusCode === 409) {
				toast.error(`项目名 "${newProjectName}" 已存在，请使用其他名称`);
			} else {
				toast.error(msg || '创建失败');
			}
		} finally {
			isCreating = false;
		}
	}

	function startEdit(project: Project) {
		editingProjectId = project.id;
		editName = project.name;
		editDesc = project.description || '';
	}

	function cancelEdit() {
		editingProjectId = null;
		editName = '';
		editDesc = '';
	}

	async function saveEdit() {
		if (!editingProjectId || isSaving) return;
		isSaving = true;
		try {
			const token = localStorage.token || '';
			await updateProject(token, editingProjectId, { name: editName, description: editDesc });
			editingProjectId = null;
			await loadProjects();
			toast.success('项目已更新');
		} catch (e: any) {
			const statusCode = e?.status;
			if (statusCode === 409) {
				toast.error(`项目名 "${editName}" 已被其他项目占用`);
			} else {
				toast.error(e.message || '更新失败');
			}
		} finally {
			isSaving = false;
		}
	}

	function handleDelete(project: Project) {
		deleteTarget = project;
		showDeleteConfirm = true;
	}

	let filteredProjects = $derived(
		query
			? projects.filter(p => p.name.toLowerCase().includes(query.toLowerCase()) || p.description?.toLowerCase().includes(query.toLowerCase()))
			: projects
	);

	let deleteTarget = $state<Project | null>(null);
	let showDeleteConfirm = $state(false);

	async function doDelete() {
		if (!deleteTarget) return;
		try {
			const token = localStorage.token || '';
			await deleteProject(token, deleteTarget.id);
			await loadProjects();
			toast.success('项目已删除');
		} catch (e: any) {
			toast.error(e.message || '删除失败');
		}
		showDeleteConfirm = false;
		deleteTarget = null;
	}

	const typeLabels: Record<string, string> = {
		prd: 'PRD 项目',
		competitor: '竞品分析',
		general: '通用项目'
	};

	import { normalizeTs, formatDate, formatDateTime } from '$lib/utils/pmTimeUtils';

	function formatTime(ts: unknown): string {
		const ms = normalizeTs(ts);
		if (ms == null) return '';
		try { return dayjs(ms).fromNow(); } catch { return ''; }
	}
</script>

<svelte:head>
	<title>PM 工作台</title>
</svelte:head>

<!-- Delete confirm -->
{#if showDeleteConfirm && deleteTarget}
	<div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center" onclick={() => { showDeleteConfirm = false; deleteTarget = null; }}>
		<div class="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-sm mx-4 shadow-xl" onclick={(e) => e.stopPropagation()}>
			<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">确认删除？</h3>
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">将删除项目 <span class="font-semibold">{deleteTarget.name}</span></p>
			<div class="flex justify-end gap-2">
				<button class="px-4 py-2 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={() => { showDeleteConfirm = false; deleteTarget = null; }}>取消</button>
				<button class="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition" onclick={doDelete}>删除</button>
			</div>
		</div>
	</div>
{/if}

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<!-- Header -->
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>PM 工作台</div>
				<div class="text-lg font-medium text-gray-500 dark:text-gray-500">
					{filteredProjects.length}
				</div>
			</div>
			<div class="flex w-full justify-end gap-1.5">
				{#if !showNewForm}
					<button
						class="px-2 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black transition font-medium text-sm flex items-center"
						onclick={() => { showNewForm = true; }}
					>
						<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
						</svg>
						<div class="ml-1 text-xs">新建项目</div>
					</button>
				{/if}
			</div>
		</div>
	</div>

	<!-- Main card -->
	<div class="py-2 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30">
		<!-- Search -->
		<div class="px-3.5 flex flex-1 items-center w-full space-x-2 py-0.5 pb-2">
			<div class="flex flex-1 items-center">
				<div class="self-center ml-1 mr-3">
					<svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>
				<input
					class="w-full text-sm py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={query}
					placeholder="搜索项目..."
				/>
				{#if query}
					<button class="p-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-900 transition" onclick={() => { query = ''; }}>
						<svg class="size-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				{/if}
			</div>
		</div>

		<!-- New project form -->
		{#if showNewForm}
			<div class="px-3.5 pb-3">
				<div class="border border-gray-200 dark:border-gray-700 rounded-2xl p-3 space-y-2">
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="项目名称" bind:value={newProjectName} onkeydown={(e) => { if (e.key === 'Enter' && newProjectName.trim()) handleCreate(); }} />
					<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" placeholder="项目描述（可选）" rows="2" bind:value={newProjectDesc}></textarea>
					<div class="flex items-center gap-2">
						<span class="text-xs text-gray-500">类型：</span>
						{#each [['general', '通用项目'], ['prd', 'PRD 项目'], ['competitor', '竞品分析']] as [val, label]}
							<button class="px-2 py-1 text-xs rounded-lg transition {newProjectType === val ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}" onclick={() => { newProjectType = val as any; }}>{label}</button>
						{/each}
					</div>
					<div class="flex justify-end gap-2">
						<button class="px-3 py-1.5 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={() => { showNewForm = false; newProjectName = ''; newProjectDesc = ''; }}>取消</button>
						<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-50" onclick={handleCreate} disabled={!newProjectName.trim() || isCreating}>{isCreating ? '创建中...' : '创建'}</button>
					</div>
				</div>
			</div>
		{/if}

		<!-- Project list -->
		{#if isLoading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div>
			</div>
		{:else if filteredProjects.length === 0}
			<div class="py-12 text-center">
				<svg class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9z" />
				</svg>
				<p class="text-sm text-gray-500 dark:text-gray-400">{query ? '没有找到匹配的项目' : '还没有项目'}</p>
				{#if !query && !showNewForm}
					<button class="mt-3 px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-xl transition" onclick={() => { showNewForm = true; }}>创建第一个项目</button>
				{/if}
			</div>
		{:else}
			<div class="px-2.5 py-1 gap-1.5 flex flex-col">
				{#each filteredProjects as project (project.id)}
					{#if editingProjectId === project.id}
						<!-- Inline edit mode -->
						<div class="w-full px-3.5 py-2.5 border border-blue-200 dark:border-blue-800 bg-blue-50/30 dark:bg-blue-900/10 rounded-2xl">
							<input type="text" class="w-full text-sm px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 mb-2" placeholder="项目名称" bind:value={editName} />
							<textarea class="w-full text-sm px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none mb-2" placeholder="项目描述" rows="2" bind:value={editDesc}></textarea>
							<div class="flex justify-end gap-2">
								<button class="px-3 py-1.5 text-xs rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={cancelEdit}>取消</button>
								<button class="px-3 py-1.5 text-xs bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-50" onclick={saveEdit} disabled={!editName.trim() || isSaving}>{isSaving ? '保存中...' : '保存'}</button>
							</div>
						</div>
					{:else}
						<a href="/pm/{project.id}" class="flex cursor-pointer w-full px-3.5 py-1.5 border border-gray-50 dark:border-gray-850/30 bg-transparent dark:hover:bg-gray-850 hover:bg-white rounded-2xl transition group">
							<div class="w-full flex flex-col justify-between">
								<div class="flex-1">
									<div class="flex items-center gap-2 self-center justify-between">
										<div class="text-sm font-medium capitalize flex-1 w-full line-clamp-1">{project.name}</div>
										<div class="flex shrink-0 items-center text-xs gap-2">
											<span class="px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">{typeLabels[project.type] || project.type}</span>
											{#if projectVersionMap[project.id]}
												<span class="px-1.5 py-0.5 rounded text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">{projectVersionMap[project.id]}</span>
											{/if}
											{#if normalizeTs(project.createdAt) != null}
												<span class="text-gray-400 dark:text-gray-500" title={formatDateTime(project.createdAt)}>创建于 {formatDate(project.createdAt)}</span>
											{/if}
											{#if normalizeTs(project.updatedAt) != null}
												<span class="text-gray-500 dark:text-gray-400">{formatTime(project.updatedAt)}</span>
											{/if}
											<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition opacity-0 group-hover:opacity-100" title="编辑" onclick={(e) => { e.preventDefault(); e.stopPropagation(); startEdit(project); }}>
												<svg class="size-3.5 text-gray-400 hover:text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
												</svg>
											</button>
											<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition opacity-0 group-hover:opacity-100" title="删除" onclick={(e) => { e.preventDefault(); e.stopPropagation(); handleDelete(project); }}>
												<svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
												</svg>
											</button>
										</div>
									</div>
									{#if project.description}
										<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">{project.description}</div>
									{/if}
								</div>
							</div>
						</a>
					{/if}
				{/each}
			</div>
		{/if}
	</div>
</div>
