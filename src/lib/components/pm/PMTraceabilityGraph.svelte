<script lang="ts">
	import { SvelteFlow, Controls, Background, type Node, type Edge, type Connection } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import { getTraceability } from '$lib/apis/pm/relation';
	import { createRelation, deleteRelation } from '$lib/apis/pm/relation';
	import PMRelationTypeSelector from './PMRelationTypeSelector.svelte';
	import type { RelationType } from '$lib/apis/pm/types';
	import { toast } from 'svelte-sonner';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		entityId?: string;
		projectId?: string;
		onNavigate?: (moduleType: string, entryId: string) => void;
		entries?: { id: string; currentVersionNumber?: string; data?: Record<string, unknown> }[];
	}

	let { isOpen = false, onClose, entityId = '', projectId = '', onNavigate, entries = [] }: Props = $props();

	let loading = $state(false);
	let error = $state('');
	let direction = $state<'both' | 'upstream' | 'downstream'>('both');
	let relationFilter = $state<string>('all');
	let flowNodes = $state<Node[]>([]);
	let flowEdges = $state<Edge[]>([]);
	let allNodes = $state<Node[]>([]);
	let allEdges = $state<Edge[]>([]);
	let showRelationSelector = $state(false);
	let pendingConnection = $state<{ source: string; target: string } | null>(null);

	const relationLabels: Record<string, string> = {
		contains: '包含', references: '引用', derives: '派生', modifies: '修改', conflicts: '冲突'
	};

	const entityTypeLabels: Record<string, string> = {
		prd: 'PRD', requirement: '需求', prototype: '原型', schedule: '日程',
		roadmap: '路线图', faq: 'FAQ', risk: '风险', competitor: '竞品',
		parameter: '参数', testcase: '用例'
	};

	const entityTypeColors: Record<string, { bg: string; border: string }> = {
		prd: { bg: '#dbeafe', border: '#3b82f6' },
		requirement: { bg: '#dcfce7', border: '#22c55e' },
		prototype: { bg: '#f3e8ff', border: '#a855f7' },
		schedule: { bg: '#fef3c7', border: '#eab308' },
		roadmap: { bg: '#ffe4e6', border: '#f43f5e' },
		faq: { bg: '#e0f2fe', border: '#0ea5e9' },
		risk: { bg: '#fee2e2', border: '#ef4444' },
		competitor: { bg: '#ffedd5', border: '#f97316' },
		parameter: { bg: '#f0fdf4', border: '#84cc16' },
		testcase: { bg: '#faf5ff', border: '#8b5cf6' }
	};

	let availableRelationTypes = $derived(() => {
		const types = new Set<string>();
		for (const edge of allEdges) {
			if (edge.label) types.add(edge.label as string);
		}
		return [...types];
	});

	$effect(() => {
		if (relationFilter === 'all') {
			flowNodes = allNodes;
			flowEdges = allEdges;
		} else {
			const filteredEdgeIds = new Set(allEdges.filter(e => e.label === relationFilter).map(e => e.id));
			const connectedNodeIds = new Set<string>();
			for (const edge of allEdges) {
				if (edge.label === relationFilter) {
					connectedNodeIds.add(edge.source);
					connectedNodeIds.add(edge.target);
				}
			}
			flowNodes = allNodes.filter(n => connectedNodeIds.has(n.id));
			flowEdges = allEdges.filter(e => filteredEdgeIds.has(e.id));
		}
	});

	$effect(() => {
		if (isOpen && entityId && projectId) {
			loadTraceability();
		}
	});

	async function loadTraceability() {
		loading = true;
		error = '';
		try {
			const data = await getTraceability(projectId, entityId, direction);
			if (data && data.chain) {
				buildGraph(data.chain);
			} else {
				flowNodes = [];
				flowEdges = [];
				allNodes = [];
				allEdges = [];
			}
		} catch (e) {
			error = '加载追溯链路时出错';
			console.error(e);
		} finally {
			loading = false;
		}
	}

	function buildGraph(chain: { entityId: string; entityType: string; relationType: string; depth: number }[]) {
		const nodes: Node[] = [];
		const edges: Edge[] = [];

		chain.forEach((item, index) => {
			const yOffset = index * 120;
			const isRoot = index === 0;
			const colors = entityTypeColors[item.entityType] || { bg: '#f3f4f6', border: '#9ca3af' };
			const typeLabel = entityTypeLabels[item.entityType] || item.entityType;
			const entry = entries.find(e => e.id === item.entityId);
			const versionNum = entry?.currentVersionNumber || (entry?.data?.versionNumber as string) || '';
			const label = versionNum ? `${typeLabel} ${versionNum}\n${item.entityId.substring(0, 8)}...` : `${typeLabel}\n${item.entityId.substring(0, 8)}...`;

			nodes.push({
				id: item.entityId,
				position: { x: 250 + (item.depth * 220), y: yOffset },
				data: {
					label,
					entityType: item.entityType
				},
				style: {
					background: isRoot ? '#dbeafe' : colors.bg,
					borderColor: isRoot ? '#3b82f6' : colors.border,
					borderWidth: isRoot ? 3 : 2,
					borderRadius: 10,
					padding: '10px 18px',
					fontSize: 13,
					color: '#1f2937',
					minWidth: 150,
					textAlign: 'center',
					cursor: 'pointer',
					whiteSpace: 'pre-line' as any,
					fontWeight: isRoot ? 600 : 400
				},
				sourcePosition: 'right' as const,
				targetPosition: 'left' as const
			});

			if (index > 0) {
				const relLabel = relationLabels[item.relationType] || item.relationType;
				edges.push({
					id: `e-${chain[index - 1].entityId}-${item.entityId}`,
					source: chain[index - 1].entityId,
					target: item.entityId,
					label: relLabel,
					style: { stroke: item.relationType === 'conflicts' ? '#ef4444' : '#9ca3af', strokeWidth: 2 },
					type: 'smoothstep',
					labelStyle: { fill: item.relationType === 'conflicts' ? '#ef4444' : '#6b7280', fontWeight: 500, fontSize: 11 },
					labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 }
				});
			}
		});

		allNodes = nodes;
		allEdges = edges;
	}

	function handleConnect(connection: Connection) {
		if (!connection.source || !connection.target) return;
		pendingConnection = { source: connection.source, target: connection.target };
		showRelationSelector = true;
	}

	async function handleRelationSelect(relationType: RelationType) {
		if (!pendingConnection || !projectId) return;
		try {
			const srcEntry = entries.find(e => e.id === pendingConnection!.source);
			const tgtEntry = entries.find(e => e.id === pendingConnection!.target);
			const versionSnapshot = {
				entityAVersionNumber: srcEntry?.currentVersionNumber || (srcEntry?.data?.versionNumber as string) || '',
				entityBVersionNumber: tgtEntry?.currentVersionNumber || (tgtEntry?.data?.versionNumber as string) || ''
			};
			await createRelation(projectId, {
				entityAId: pendingConnection.source,
				entityBId: pendingConnection.target,
				relationType,
				confidence: 100,
				confirmed: 1,
				createdBy: 'user',
				versionSnapshot
			});
			const relLabel = relationLabels[relationType] || relationType;
			const newEdge: Edge = {
				id: `e-${pendingConnection.source}-${pendingConnection.target}-${Date.now()}`,
				source: pendingConnection.source,
				target: pendingConnection.target,
				label: relLabel,
				style: { stroke: '#9ca3af', strokeWidth: 2 },
				type: 'smoothstep',
				labelStyle: { fill: '#6b7280', fontWeight: 500, fontSize: 11 },
				labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 }
			};
			allEdges = [...allEdges, newEdge];
			toast.success('关联创建成功');
		} catch (e: any) {
			toast.error(e?.message || '创建关联失败');
		} finally {
			pendingConnection = null;
			showRelationSelector = false;
		}
	}

	function handleNodeDoubleClick(event: { node?: Node }) {
		if (!event.node) return;
		const entityType = event.node.data?.entityType as string | undefined;
		if (entityType && onNavigate) {
			onNavigate(entityType, event.node.id);
		}
		onClose?.();
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={() => onClose?.()}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
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
				<div class="flex flex-wrap items-center gap-2 mt-3">
					{#each ['both', 'upstream', 'downstream'] as dir}
						<button
							class="px-3 py-1.5 text-xs rounded-lg transition-colors {direction === dir ? 'bg-purple-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
							onclick={() => { direction = dir as typeof direction; loadTraceability(); }}
						>
							{dir === 'both' ? '双向' : dir === 'upstream' ? '上游' : '下游'}
						</button>
					{/each}
					<div class="h-4 w-px bg-gray-200 dark:bg-gray-700 mx-1"></div>
					<select class="px-2 py-1 text-xs rounded-lg bg-gray-50 dark:bg-gray-700 border-0 outline-hidden" bind:value={relationFilter}>
						<option value="all">全部关系</option>
						{#each availableRelationTypes() as rtype}
							<option value={rtype}>{rtype}</option>
						{/each}
					</select>
				</div>
				<p class="text-xs text-gray-400 mt-2">拖拽端口创建新关联 · 双击节点跳转编辑 · 下拉筛选关系类型</p>
			</div>

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
					<SvelteFlow
						nodes={$flowNodes}
						edges={$flowEdges}
						fitView
						nodesDraggable={true}
						minZoom={0.3}
						maxZoom={2}
						onconnect={handleConnect}
						onnodedoubleclick={handleNodeDoubleClick}
					>
						<Background patternColor="#e5e7eb" gap={20} />
						<Controls />
					</SvelteFlow>
				{/if}
			</div>
		</div>
	</div>
{/if}

{#if showRelationSelector}
	<PMRelationTypeSelector
		position={{ x: 400, y: 300 }}
		onSelect={handleRelationSelect}
		onCancel={() => { showRelationSelector = false; pendingConnection = null; }}
	/>
{/if}
