<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getProject, getVersions, createVersion } from '$lib/apis/pm/index';
	import { setCurrentProject, currentProject } from '$lib/stores/pm/projectStore';
	import { setCurrentVersion, currentVersion, versions } from '$lib/stores/pm/versionStore';
	import { showSidebar } from '$lib/stores';
	import type { Project, Version } from '$lib/apis/pm/types';

	const moduleLabels: Record<string, string> = {
		prd: 'PRD 文档', requirement: '需求管理', roadmap: '产品路线图',
		parameter: '参数配置', 'product-architecture': '产品架构', competitor: '竞品分析',
		testcase: '测试用例', risk: '风险分析', meeting: '会议纪要',
		acceptance: '验收报告', faq: 'FAQ'
	};

	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
	let projectId = $derived($page.params.projectId);
	let showVersionDropdown = $state(false);
	let project = $state<Project | null>(null);
	let apiStatus = $state<'idle' | 'loading' | 'success' | 'error'>('idle');
	let newVersionNumber = $state('');
	let showNewVersionForm = $state(false);

	async function loadProject() {
		if (!projectId) return;
		apiStatus = 'loading';
		try {
			const token = localStorage.token || '';
			project = await getProject(token, projectId);
			setCurrentProject(project);
			const versionList = await getVersions(token, projectId);
			if (versionList?.length > 0) {
				setCurrentVersion(versionList[0]);
			}
			apiStatus = 'success';
		} catch {
			project = null;
			apiStatus = 'error';
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

	async function createNewVersion() {
		if (!newVersionNumber.trim()) return;
		try {
			const token = localStorage.token || '';
			const v = await createVersion(token, projectId, { version_number: newVersionNumber });
			setCurrentVersion(v);
			newVersionNumber = '';
			showNewVersionForm = false;
			showVersionDropdown = false;
			toast.success(`版本 ${v.versionNumber} 创建成功`);
		} catch (e: any) {
			toast.error(e.message || '创建版本失败');
		}
	}
</script>

<svelte:head>
	<title>{project?.name || '项目'} - PM 工作台</title>
</svelte:head>

{#if project}
	<div
		class="flex flex-col h-full w-full transition-width duration-200 ease-in-out {$showSidebar
			? 'md:max-w-[calc(100%-var(--sidebar-width))]'
			: ''} max-w-full"
	>
		<!-- Compact top bar: project name + version selector -->
		<div class="flex items-center justify-between px-4 lg:px-6 py-2 border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
			<div class="flex items-center gap-2 min-w-0">
				<!-- Home button -->
				<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition text-gray-500 hover:text-gray-700 dark:hover:text-gray-300" onclick={() => goto('/pm')} title="返回首页">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" />
					</svg>
				</button>
				<!-- Breadcrumb -->
				<svg class="w-3 h-3 text-gray-300 dark:text-gray-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
				<button class="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 truncate transition" onclick={() => goto(`/pm/${projectId}`)}>{project.name}</button>
				{#if $page.params.module}
					<svg class="w-3 h-3 text-gray-300 dark:text-gray-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
					<span class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{moduleLabels[$page.params.module] || $page.params.module}</span>
				{:else}
					<svg class="w-3 h-3 text-gray-300 dark:text-gray-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
					<span class="text-sm font-medium text-gray-900 dark:text-gray-100">工作台</span>
				{/if}
				<span class="text-xs text-gray-400 hidden sm:inline">{project.description}</span>
				<!-- API status dot -->
				<span class="w-2 h-2 rounded-full flex-shrink-0 {apiStatus === 'success' ? 'bg-green-400' : apiStatus === 'error' ? 'bg-red-400' : apiStatus === 'loading' ? 'bg-yellow-400 animate-pulse' : 'bg-gray-300'}" title={apiStatus === 'success' ? 'API 连接正常' : apiStatus === 'error' ? 'API 连接失败' : apiStatus === 'loading' ? '连接中...' : ''}></span>
			</div>
			<div class="flex items-center gap-2 flex-shrink-0">
				<!-- Back button -->
				<button class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition text-gray-500 hover:text-gray-700 dark:hover:text-gray-300" onclick={() => { if (window.history.length > 1) window.history.back(); else goto(`/pm/${projectId}`); }} title="返回上一步">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
				</button>
				<!-- Version selector - compact dropdown -->
				<div class="relative">
					<button
						class="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition"
						onclick={() => { showVersionDropdown = !showVersionDropdown; showNewVersionForm = false; }}
					>
						<svg class="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
						</svg>
						<span class="font-medium text-gray-700 dark:text-gray-300">{$currentVersion?.versionNumber || $currentVersion?.version_number || 'v1.0'}</span>
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
											<span class="font-medium">{v.versionNumber || v.version_number}</span>
											{#if v.label}
												<span class="px-1 py-0.5 text-[10px] rounded {v.label === 'milestone' ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' : v.label === 'release' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' : 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400'}">{v.label}</span>
											{/if}
										</button>
									{/each}
								{/if}
							</div>
							<div class="border-t border-gray-100 dark:border-gray-700 p-2">
								{#if showNewVersionForm}
									<div class="flex gap-1.5">
										<input type="text" class="flex-1 text-xs px-2 py-1.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-600 rounded-lg outline-hidden focus:ring-1 focus:ring-blue-500" placeholder="版本号 (如 v1.1)" bind:value={newVersionNumber} onkeydown={(e) => { if (e.key === 'Enter') createNewVersion(); }} />
										<button class="px-2 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition" onclick={createNewVersion}>创建</button>
									</div>
								{:else}
									<button class="w-full flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition" onclick={() => { showNewVersionForm = true; }}>
										<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
										创建新版本
									</button>
								{/if}
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
