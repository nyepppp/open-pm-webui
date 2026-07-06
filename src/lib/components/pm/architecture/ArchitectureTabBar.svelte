<script lang="ts">
	interface Props {
		activeTab: 'mindmap' | 'params';
		onTabChange?: (tab: 'mindmap' | 'params') => void;
	}

	let { activeTab = 'mindmap', onTabChange }: Props = $props();

	function handleClick(tab: 'mindmap' | 'params') {
		onTabChange?.(tab);
	}
</script>

<div class="flex items-center gap-1">
	<button
		class="px-4 py-1.5 text-sm font-medium rounded-lg transition-colors {activeTab === 'mindmap'
			? 'bg-blue-600 text-white'
			: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
		onclick={() => handleClick('mindmap')}
	>
		架构图
	</button>
	<button
		class="px-4 py-1.5 text-sm font-medium rounded-lg transition-colors {activeTab === 'params'
			? 'bg-blue-600 text-white'
			: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
		onclick={() => handleClick('params')}
	>
		模块详情
	</button>
</div>
