<script lang="ts">
	import { SvelteFlow, Controls, Background, type Node, type Edge } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import { getTraceability } from '$lib/apis/pm/relation';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		entityId?: string;
		projectId?: string;
	}

	let { isOpen = false, onClose, entityId = '', projectId = '' }: Props = $props();

	let loading = $state(false);
	let error = $state('');
	let direction = $state<'both' | 'upstream' | 'downstream'>('both');

	let flowNodes = $state<Node[]>([]);
	let flowEdges = $state<Edge[]>([]);

	$effect(() => {
		if (isOpen && entityId && projectId) {
			loadTraceability();
		}
	});

	async function loadTraceability() {
		loading = true;
		error = '';
		try {
			const response = await getTraceability(projectId, entityId, direction);
			if (response.success && response.data) {
				buildGraph(response.data.chain);
			} else {
				error = response.error || '加载追溯链路失败';
			}
		} catch (e) {
			error = '加载追溯链路时出错';
		} finally {
			loading = false;
		}
	}

	function buildGraph(chain: { entityId: string; entityType: string; relationType: string; depth: number }[]) {
		const nodes: Node[] = [];
		const edges: Edge[] = [];

		chain.forEach((item, index) => {
			const yOffset = index * 100;
			const isRoot = index === 0;

			nodes.push({
				id: item.entityId,
				position: { x: 250 + (item.depth * 200), y: yOffset },
				data: { label: `${item.entityType} (${item.entityId.substring(0, 8)}...)` },
				style: {
					background: isRoot ? '#dbeafe' : item.depth > 0 ? '#dcfce7' : '#fef3c7',
					borderColor: isRoot ? '#3b82f6' : item.depth > 0 ? '#22c55e' : '#eab308',
					borderWidth: 2,
					borderRadius: 8,
					padding: '8px 16px',
					fontSize: 13,
					color: '#1f2937',
					minWidth: 140,
					textAlign: 'center'
				}
			});

			if (index > 0) {
				edges.push({
					id: `e-${chain[index - 1].entityId}-${item.entityId}`,
					source: chain[index - 1].entityId,
					target: item.entityId,
					label: item.relationType,
					style: { stroke: '#9ca3af', strokeWidth: 2 },
					type: 'smoothstep'
				});
			}
		});

		flowNodes = nodes;
		flowEdges = edges;
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={() => onClose?.()}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl h-[80vh] overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
						</svg>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">追溯链路</h2>
					</div>
					<button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" onclick={() => onClose?.()}>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Direction Selector -->
				<div class="flex gap-2 mt-3">
					{#each ['both', 'upstream', 'downstream'] as dir}
						<button
							class="px-3 py-1.5 text-xs rounded-lg transition-colors {direction === dir ? 'bg-purple-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
							onclick={() => { direction = dir as typeof direction; loadTraceability(); }}
						>
							{dir === 'both' ? '双向' : dir === 'upstream' ? '上游' : '下游'}
						</button>
					{/each}
				</div>
			</div>

			<!-- Graph -->
			<div class="flex-1 relative">
				{#if loading}
					<div class="flex items-center justify-center h-full">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
						<span class="ml-3 text-sm text-gray-500 dark:text-gray-400">加载链路中...</span>
					</div>
				{:else if error}
					<div class="flex items-center justify-center h-full">
						<p class="text-sm text-red-500 dark:text-red-400">{error}</p>
					</div>
				{:else if flowNodes.length === 0}
					<div class="flex items-center justify-center h-full">
						<p class="text-sm text-gray-500 dark:text-gray-400">暂无追溯链路数据</p>
					</div>
				{:else}
					<SvelteFlow nodes={flowNodes} edges={flowEdges} fitView nodesDraggable={false} minZoom={0.3} maxZoom={2}>
						<Background patternColor="#e5e7eb" gap={20} />
						<Controls />
					</SvelteFlow>
				{/if}
			</div>
		</div>
	</div>
{/if}
