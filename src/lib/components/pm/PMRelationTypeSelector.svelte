<script lang="ts">
	import type { RelationType } from '$lib/apis/pm/types';

	interface Props {
		onSelect?: (relationType: RelationType) => void;
		onCancel?: () => void;
		position?: { x: number; y: number };
	}

	let { onSelect, onCancel, position }: Props = $props();

	const relationTypes: { type: RelationType; label: string; color: string; description: string }[] = [
		{ type: 'contains', label: '包含', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300', description: 'A 包含 B' },
		{ type: 'references', label: '引用', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', description: 'A 引用 B' },
		{ type: 'derives', label: '派生', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300', description: 'A 派生自 B' },
		{ type: 'modifies', label: '修改', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300', description: 'A 修改了 B' },
		{ type: 'conflicts', label: '冲突', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300', description: 'A 与 B 冲突' }
	];

	function handleSelect(type: RelationType) {
		onSelect?.(type);
	}
</script>

{#if position}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="fixed inset-0 z-50" onclick={onCancel}></div>
	<div
		class="fixed z-50 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden w-48"
		style="left: {position.x}px; top: {position.y}px;"
	>
		<div class="px-3 py-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-850">
			<span class="text-xs font-semibold text-gray-600 dark:text-gray-400">选择关系类型</span>
		</div>
		<div class="py-1">
			{#each relationTypes as rt (rt.type)}
				<button
					class="w-full text-left px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors flex items-center gap-2"
					onclick={() => handleSelect(rt.type)}
				>
					<span class="px-1.5 py-0.5 text-[10px] rounded {rt.color}">{rt.label}</span>
					<span class="text-[10px] text-gray-400">{rt.description}</span>
				</button>
			{/each}
		</div>
	</div>
{/if}
