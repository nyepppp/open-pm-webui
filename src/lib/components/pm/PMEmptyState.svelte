<script lang="ts">
	import { goto } from '$app/navigation';

	// Props
	interface Props {
		moduleName: string;
		moduleIcon?: string;
		description?: string;
		createPath?: string;
		showCreateButton?: boolean;
	}

	let {
		moduleName,
		moduleIcon = '📄',
		description = '此模块暂无内容，开始创建第一个条目吧',
		createPath,
		showCreateButton = true
	}: Props = $props();

	function handleCreate() {
		if (createPath) {
			goto(createPath);
		}
	}
</script>

<div class="pm-empty-state flex flex-col items-center justify-center min-h-[400px] p-8">
	<!-- Icon -->
	<div class="relative mb-6">
		<div class="w-24 h-24 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
			<span class="text-5xl">{moduleIcon}</span>
		</div>
		<!-- Decorative elements -->
		<div class="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
			<svg class="w-4 h-4 text-blue-500 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
		</div>
	</div>

	<!-- Text -->
	<h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
		{moduleName} 暂无内容
	</h3>
	<p class="text-sm text-gray-500 dark:text-gray-400 text-center max-w-sm mb-6">
		{description}
	</p>

	<!-- Create Button -->
	{#if showCreateButton}
		<button
			class="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors shadow-sm hover:shadow-md"
			onclick={handleCreate}
			aria-label="创建第一个{moduleName}条目"
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			创建第一个条目
		</button>
	{/if}

	<!-- Quick tips -->
	<div class="mt-8 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg max-w-md">
		<h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
			💡 快速提示
		</h4>
		<ul class="space-y-1.5 text-xs text-gray-500 dark:text-gray-400">
			<li class="flex items-start gap-2">
				<span class="text-blue-500 dark:text-blue-400 mt-0.5">•</span>
				<span>点击上方按钮创建新条目</span>
			</li>
			<li class="flex items-start gap-2">
				<span class="text-blue-500 dark:text-blue-400 mt-0.5">•</span>
				<span>使用侧边栏切换不同功能模块</span>
			</li>
			<li class="flex items-start gap-2">
				<span class="text-blue-500 dark:text-blue-400 mt-0.5">•</span>
				<span>版本切换器在页面顶部</span>
			</li>
		</ul>
	</div>
</div>
