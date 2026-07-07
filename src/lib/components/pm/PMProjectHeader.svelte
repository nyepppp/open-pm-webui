<script lang="ts">
	import { currentProject, currentProjectName } from '$lib/stores/pm/projectStore';
	import { currentVersion, versionCount } from '$lib/stores/pm/versionStore';

	// Props
	interface Props {
		projectId?: string;
		onVersionClick?: () => void;
		onMenuClick?: () => void;
	}

	let { projectId = '', onVersionClick, onMenuClick }: Props = $props();

	// Use project name from store or fallback
	let displayName = $derived($currentProjectName || '未命名项目');
	let currentVersionNumber = $derived($currentVersion?.versionNumber ?? $currentVersion?.version_number ?? 'v1.0');
	let totalVersions = $derived($versionCount || 1);
</script>

<header class="pm-project-header flex items-center justify-between px-4 lg:px-6 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700" role="banner" aria-label="项目头部">
	<!-- Left: Menu Toggle + Project Info -->
	<div class="flex items-center gap-3">
		<!-- Mobile Menu Toggle -->
		<button
			class="lg:hidden p-2 -ml-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
			onclick={() => onMenuClick?.()}
			aria-label="打开菜单"
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
			</svg>
		</button>

		<div class="flex items-center gap-2">
			<div class="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0" aria-hidden="true">
				<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
				</svg>
			</div>
			<div class="min-w-0">
				<h1 class="text-base lg:text-lg font-semibold text-gray-900 dark:text-gray-100 leading-tight truncate">
					{displayName}
				</h1>
				<p class="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">
					项目管理工作台
				</p>
			</div>
		</div>
	</div>

	<!-- Right: Version Info + Actions -->
	<div class="flex items-center gap-2 lg:gap-3">
		<!-- Version Badge -->
		<button
			class="flex items-center gap-1.5 lg:gap-2 px-2 lg:px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
			onclick={() => onVersionClick?.()}
			title="点击切换版本"
			aria-label="切换版本，当前版本 {currentVersionNumber}，共 {totalVersions} 个版本"
		>
			<svg class="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
			</svg>
			<span class="font-medium text-gray-700 dark:text-gray-300 hidden sm:inline">{currentVersionNumber}</span>
			<span class="text-xs text-gray-500 dark:text-gray-400 hidden md:inline">({totalVersions} 个版本)</span>
			<svg class="w-3 h-3 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
			</svg>
		</button>

		<!-- Settings -->
		<button
			class="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
			title="设置"
			aria-label="项目设置"
		>
			<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.756-.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.756.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.426-1.756 2.924-1.756 3.35 0zM15 12a3 3 0 11-6 0 3 3 0 016 0z" />
			</svg>
		</button>
	</div>
</header>
