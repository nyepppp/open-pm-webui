<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getProject, getVersions } from '$lib/apis/pm/index';
	import { setCurrentProject, currentProject } from '$lib/stores/pm/projectStore';
	import { setCurrentVersion, currentVersion, versions } from '$lib/stores/pm/versionStore';
	import type { Project, Version } from '$lib/apis/pm/types';

	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
	let projectId = $derived($page.params.projectId);
	let showVersionDropdown = $state(false);
	let project = $state<Project | null>(null);

	async function loadProject() {
		if (!projectId) return;
		try {
			const token = localStorage.token || '';
			project = await getProject(token, projectId);
			setCurrentProject(project);
			const versionList = await getVersions(token, projectId);
			if (versionList?.length > 0) {
				setCurrentVersion(versionList[0]);
			}
		} catch {
			project = null;
		}
	}

	onMount(() => { loadProject(); });

	$effect(() => {
		projectId;
		loadProject();
	});

	function selectVersion(v: Version) {
		setCurrentVersion(v);
		showVersionDropdown = false;
	}

	function createNewVersion() {
		showVersionDropdown = false;
		// TODO: implement version creation
	}
</script>

<svelte:head>
	<title>{project?.name || '项目'} - PM 工作台</title>
</svelte:head>

{#if project}
	<div class="flex flex-col h-full w-full">
		<!-- Compact top bar: project name + version selector -->
		<div class="flex items-center justify-between px-4 lg:px-6 py-2 border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
			<div class="flex items-center gap-3 min-w-0">
				<button class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition" onclick={() => goto('/pm')} title="返回项目列表">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
					</svg>
				</button>
				<h1 class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{project.name}</h1>
				<span class="text-xs text-gray-400 hidden sm:inline">{project.description}</span>
			</div>
			<div class="flex items-center gap-2 flex-shrink-0">
				<!-- Version selector - compact dropdown -->
				<div class="relative">
					<button
						class="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition"
						onclick={() => { showVersionDropdown = !showVersionDropdown; }}
					>
						<svg class="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
						</svg>
						<span class="font-medium text-gray-700 dark:text-gray-300">{$currentVersion?.versionNumber || 'v1.0'}</span>
						<svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
						</svg>
					</button>
					{#if showVersionDropdown}
						<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
						<div role="menu" class="absolute right-0 top-full mt-1 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 z-50" onclick={(e) => e.stopPropagation()}>
							<div class="p-2 max-h-64 overflow-y-auto">
								{#if $versions.length === 0}
									<div class="px-3 py-2 text-xs text-gray-500">暂无版本</div>
								{:else}
									{#each $versions as v (v.id)}
										<button
											class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition {$currentVersion?.id === v.id ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'}"
											onclick={() => selectVersion(v)}
										>
											<span class="font-medium">{v.versionNumber}</span>
											{#if v.label}
												<span class="px-1 py-0.5 text-[10px] rounded {v.label === 'milestone' ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' : v.label === 'release' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' : 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400'}">{v.label}</span>
											{/if}
										</button>
									{/each}
								{/if}
							</div>
							<div class="border-t border-gray-100 dark:border-gray-700 p-2">
								<button class="w-full flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition" onclick={createNewVersion}>
									<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
									创建新版本
								</button>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Content -->
		<div class="flex-1 overflow-auto">
			{@render children?.()}
		</div>
	</div>
{/if}

{#if showVersionDropdown}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div role="presentation" class="fixed inset-0 z-40" onclick={() => { showVersionDropdown = false; }}></div>
{/if}
