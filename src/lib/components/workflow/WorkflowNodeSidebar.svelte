<script lang="ts">
	import { getAllNodeTypes, getNodeCategories, type NodeTypeDefinition } from './nodes';

	interface Props {
		onNodeSelect?: (nodeType: NodeTypeDefinition) => void;
		searchQuery?: string;
	}

	let { onNodeSelect, searchQuery = '' }: Props = $props();

	const nodeTypes = getAllNodeTypes();
	const categories = getNodeCategories();

	let expandedCategories = $state<Set<string>>(new Set(categories));
	let draggedNodeType = $state<NodeTypeDefinition | null>(null);

	function toggleCategory(category: string) {
		const newExpanded = new Set(expandedCategories);
		if (newExpanded.has(category)) {
			newExpanded.delete(category);
		} else {
			newExpanded.add(category);
		}
		expandedCategories = newExpanded;
	}

	function getNodesByCategory(category: string): NodeTypeDefinition[] {
		return nodeTypes.filter(node => node.category === category);
	}

	function handleDragStart(e: DragEvent, nodeType: NodeTypeDefinition) {
		draggedNodeType = nodeType;
		if (e.dataTransfer) {
			e.dataTransfer.setData('application/json', JSON.stringify(nodeType));
			e.dataTransfer.effectAllowed = 'copy';
		}
	}

	function handleDragEnd() {
		draggedNodeType = null;
	}

	function handleNodeClick(nodeType: NodeTypeDefinition) {
		onNodeSelect?.(nodeType);
	}

	function filterNodes(nodes: NodeTypeDefinition[]): NodeTypeDefinition[] {
		if (!searchQuery.trim()) return nodes;
		const query = searchQuery.toLowerCase();
		return nodes.filter(
			node =>
				node.label.toLowerCase().includes(query) ||
				node.description.toLowerCase().includes(query) ||
				node.type.toLowerCase().includes(query)
		);
	}
</script>

<div class="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col h-full">
	<!-- Header -->
	<div class="p-4 border-b border-gray-200 dark:border-gray-700">
		<h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">节点库</h2>
		<p class="text-xs text-gray-500 dark:text-gray-400">拖拽节点到画布</p>
	</div>

	<!-- Categories -->
	<div class="flex-1 overflow-y-auto">
		{#each categories as category}
			{@const categoryNodes = filterNodes(getNodesByCategory(category))}
			{#if categoryNodes.length > 0}
				<div class="border-b border-gray-200 dark:border-gray-700 last:border-b-0">
					<button
						class="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
						onclick={() => toggleCategory(category)}
					>
						<span class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
							{category}
						</span>
						<svg
							class="w-4 h-4 text-gray-400 transition-transform {expandedCategories.has(category) ? 'rotate-180' : ''}"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
						</svg>
					</button>

					{#if expandedCategories.has(category)}
						<div class="px-2 pb-2 space-y-1">
							{#each categoryNodes as nodeType (nodeType.type)}
								<div
									class="flex items-center gap-3 p-2 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group"
									draggable={true}
									on:dragstart={(e) => handleDragStart(e, nodeType)}
									on:dragend={handleDragEnd}
									onclick={() => handleNodeClick(nodeType)}
									role="button"
									tabindex="0"
									onkeydown={(e) => {
										if (e.key === 'Enter' || e.key === ' ') {
											e.preventDefault();
											handleNodeClick(nodeType);
										}
									}}
								>
									<div
										class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
										style="background-color: {nodeType.color}"
									>
										{nodeType.label.charAt(0)}
									</div>
									<div class="flex-1 min-w-0">
										<p class="text-sm font-medium text-gray-900 dark:text-white truncate">
											{nodeType.label}
										</p>
										<p class="text-xs text-gray-500 dark:text-gray-400 truncate">
											{nodeType.description}
										</p>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		{/each}
	</div>
</div>
