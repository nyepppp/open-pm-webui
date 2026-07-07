<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { toast } from 'svelte-sonner';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Folder from '$lib/components/icons/Folder.svelte';
	import Document from '$lib/components/icons/Document.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
	import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let onSelect: (data: any) => void = () => {};
	export let onClose: () => void = () => {};

	interface Project {
		id: string;
		name: string;
		description?: string;
		status: string;
	}

	interface Module {
		id: string;
		name: string;
		module_type: string;
		status: string;
	}

	interface Entry {
		id: string;
		title: string;
		module_type: string;
		status: string;
		priority?: string;
		content?: string;
		current_version_number?: string;
		version?: number;
	}

	let projects: Project[] = [];
	let modules: Module[] = [];
	let entries: Entry[] = [];
	let selectedProject: Project | null = null;
	let selectedModule: Module | null = null;
	let searchQuery = '';
	let loading = false;
	let currentView: 'projects' | 'modules' | 'entries' = 'projects';

	// Fetch projects on mount
	onMount(async () => {
		await fetchProjects();
	});

	async function fetchProjects() {
		loading = true;
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/pm/projects`, {
				headers: {
					Authorization: `Bearer ${localStorage.token}`
				}
			});
			if (!response.ok) throw new Error('Failed to fetch projects');
			const data = await response.json();
			projects = data.projects || [];
		} catch (error) {
			toast.error('Failed to fetch projects');
			console.error(error);
		} finally {
			loading = false;
		}
	}

	async function fetchModules(projectId: string) {
		loading = true;
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/pm/projects/${projectId}/modules`, {
				headers: {
					Authorization: `Bearer ${localStorage.token}`
				}
			});
			if (!response.ok) throw new Error('Failed to fetch modules');
			const data = await response.json();
			modules = data.modules || [];
		} catch (error) {
			toast.error('Failed to fetch modules');
			console.error(error);
		} finally {
			loading = false;
		}
	}

	async function fetchEntries(projectId: string, moduleId?: string) {
		loading = true;
		try {
			let url = `${WEBUI_API_BASE_URL}/pm/projects/${projectId}/entries`;
			if (moduleId) {
				url += `?module_id=${moduleId}`;
			}
			const response = await fetch(url, {
				headers: {
					Authorization: `Bearer ${localStorage.token}`
				}
			});
			if (!response.ok) throw new Error('Failed to fetch entries');
			const data = await response.json();
			entries = data.entries || [];
		} catch (error) {
			toast.error('Failed to fetch entries');
			console.error(error);
		} finally {
			loading = false;
		}
	}

	function selectProject(project: Project) {
		selectedProject = project;
		currentView = 'modules';
		fetchModules(project.id);
	}

	function selectModule(module: Module) {
		selectedModule = module;
		currentView = 'entries';
		fetchEntries(selectedProject!.id, module.id);
	}

	function selectEntry(entry: Entry) {
		const pmData = {
			projectId: selectedProject?.id,
			projectName: selectedProject?.name,
			moduleId: selectedModule?.id,
			moduleName: selectedModule?.name,
			entryId: entry.id,
			entryTitle: entry.title,
			moduleType: entry.module_type,
			status: entry.status,
			priority: entry.priority,
			content: entry.content
		};
		onSelect(pmData);
		show = false;
	}

	function goBack() {
		if (currentView === 'entries') {
			currentView = 'modules';
			selectedModule = null;
			entries = [];
		} else if (currentView === 'modules') {
			currentView = 'projects';
			selectedProject = null;
			modules = [];
		}
	}

	function close() {
		show = false;
		onClose();
	}

	$: filteredProjects = projects.filter(p => 
		p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
		p.description?.toLowerCase().includes(searchQuery.toLowerCase())
	);

	$: filteredModules = modules.filter(m =>
		m.name.toLowerCase().includes(searchQuery.toLowerCase())
	);

	$: filteredEntries = entries.filter(e =>
		e.title.toLowerCase().includes(searchQuery.toLowerCase())
	);
</script>

{#if show}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		on:click={close}
	>
		<div 
			class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden"
			on:click|stopPropagation
			in:fly={{ y: 20, duration: 200 }}
		>
			<!-- Header -->
			<div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
				<div class="flex items-center gap-2">
					{#if currentView !== 'projects'}
						<button
							on:click={goBack}
							class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
						>
							<ChevronLeft className="size-5" />
						</button>
					{/if}
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
						{#if currentView === 'projects'}
							选择项目
						{:else if currentView === 'modules'}
							选择模块
						{:else}
							选择条目
						{/if}
					</h2>
				</div>
				<button
					on:click={close}
					class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
				>
					<XMark className="size-5" />
				</button>
			</div>

			<!-- Breadcrumb -->
			{#if currentView !== 'projects'}
				<div class="px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800">
					<div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
						<span class="font-medium">{selectedProject?.name}</span>
						{#if selectedModule}
							<ChevronRight className="size-4" />
							<span class="font-medium">{selectedModule?.name}</span>
						{/if}
					</div>
				</div>
			{/if}

			<!-- Search -->
			<div class="p-4 border-b border-gray-200 dark:border-gray-800">
				<div class="relative">
					<svg class="absolute left-3 top-1/2 -translate-y-1/2 size-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<input
						type="text"
						placeholder="搜索..."
						bind:value={searchQuery}
						class="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-800 border border-transparent rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
					/>
				</div>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto p-4">
				{#if loading}
					<div class="flex items-center justify-center py-8">
						<Spinner className="size-8" />
					</div>
				{:else if currentView === 'projects'}
					{#if filteredProjects.length === 0}
						<div class="text-center py-8 text-gray-500">
							暂无项目
						</div>
					{:else}
						<div class="space-y-2">
							{#each filteredProjects as project}
								<button
									on:click={() => selectProject(project)}
									class="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
								>
									<div class="shrink-0">
										<Folder className="size-8 text-blue-500" />
									</div>
									<div class="flex-1 min-w-0">
										<div class="font-medium text-gray-900 dark:text-white truncate">
											{project.name}
										</div>
										{#if project.description}
											<div class="text-sm text-gray-500 truncate">
												{project.description}
											</div>
										{/if}
									</div>
									<ChevronRight className="size-5 text-gray-400" />
								</button>
							{/each}
						</div>
					{/if}
				{:else if currentView === 'modules'}
					{#if filteredModules.length === 0}
						<div class="text-center py-8 text-gray-500">
							暂无模块
						</div>
					{:else}
						<div class="space-y-2">
							{#each filteredModules as module}
								<button
									on:click={() => selectModule(module)}
									class="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
								>
									<div class="shrink-0">
										<Document className="size-8 text-green-500" />
									</div>
									<div class="flex-1 min-w-0">
										<div class="font-medium text-gray-900 dark:text-white truncate">
											{module.name}
										</div>
										<div class="text-sm text-gray-500">
											{module.module_type}
										</div>
									</div>
									<ChevronRight className="size-5 text-gray-400" />
								</button>
							{/each}
						</div>
					{/if}
				{:else if currentView === 'entries'}
					{#if filteredEntries.length === 0}
						<div class="text-center py-8 text-gray-500">
							暂无条目
						</div>
					{:else}
						<div class="space-y-2">
							{#each filteredEntries as entry}
								<button
									on:click={() => selectEntry(entry)}
									class="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
								>
									<div class="flex-1 min-w-0">
										<div class="font-medium text-gray-900 dark:text-white truncate">
											{entry.title}
											{#if entry.current_version_number || entry.version}
												<span class="text-xs text-gray-500 ml-1">(v{entry.current_version_number || entry.version})</span>
											{/if}
										</div>
										<div class="flex items-center gap-2 mt-1">
											<span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
												{entry.module_type}
											</span>
											<span class="text-xs text-gray-500">
												{entry.status}
											</span>
											{#if entry.priority}
												<span class="text-xs text-purple-600">
													{entry.priority}
												</span>
											{/if}
										</div>
									</div>
								</button>
							{/each}
						</div>
					{/if}
				{/if}
			</div>
		</div>
	</div>
{/if}
