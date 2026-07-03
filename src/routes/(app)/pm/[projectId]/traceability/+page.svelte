<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getEntries } from '$lib/apis/pm/index';
	import { getRelationList, createRelation, deleteRelation } from '$lib/apis/pm/relation';
	import { SvelteFlow, Controls, Background, type Node, type Edge, type Connection } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import PMRelationTypeSelector from '$lib/components/pm/PMRelationTypeSelector.svelte';
	import PMTraceDetailPanel from '$lib/components/pm/PMTraceDetailPanel.svelte';
	import type { RelationType } from '$lib/apis/pm/types';

	let projectId = $derived($page.params.projectId);

	const typeColors: Record<string, string> = {
		prd: '#8B5CF6', requirement: '#3B82F6', parameter: '#10B981',
		testcase: '#F59E0B', risk: '#EF4444', competitor: '#6366F1',
		roadmap: '#EC4899', meeting: '#14B8A6', acceptance: '#F97316',
		faq: '#8B5CF6', 'product-architecture': '#06B6D4', prototype: '#A855F7', schedule: '#22C55E'
	};

	const typeLabels: Record<string, string> = {
		prd: 'PRD', requirement: '需求', parameter: '参数',
		testcase: '测试用例', risk: '风险', competitor: '竞品',
		roadmap: '路线图', meeting: '会议', acceptance: '验收',
		faq: 'FAQ', 'product-architecture': '产品架构', prototype: '原型', schedule: '排期'
	};

	const relationLabels: Record<string, string> = {
		contains: '包含', references: '引用', derives: '派生', modifies: '修改', conflicts: '冲突'
	};

	const relationColors: Record<string, string> = {
		contains: '#3B82F6', references: '#22C55E', derives: '#8B5CF6', modifies: '#F59E0B', conflicts: '#EF4444'
	};

	let isLoading = $state(true);
	let flowNodes = $state<Node[]>([]);
	let flowEdges = $state<Edge[]>([]);
	let allEntries = $state<any[]>([]);
	let allRelations = $state<any[]>([]);
	let filterType = $state<string>('all');
	let selectedNodeId = $state<string | null>(null);
	let showDetailPanel = $state(false);
	let selectedEntity = $state<{ id: string; name: string; type: string } | null>(null);
	let relationTypeSelectorPos = $state<{ x: number; y: number } | null>(null);
	let pendingConnection = $state<{ source: string; target: string } | null>(null);
	let edgeContextMenu = $state<{ x: number; y: number; edgeId: string; relationId: string } | null>(null);

	async function loadGraph() {
		isLoading = true;
		try {
			const token = localStorage.token || '';
			const modules = ['prd', 'requirement', 'parameter', 'testcase', 'risk', 'competitor', 'roadmap', 'meeting', 'acceptance', 'faq'];
			const entries: any[] = [];
			for (const mod of modules) {
				try {
					const result = await getEntries(token, projectId, mod);
					if (Array.isArray(result)) {
						result.forEach((e: any) => entries.push({ ...e, _moduleType: mod }));
					}
				} catch { /* skip */ }
			}
			allEntries = entries;

			// Load all relations for the project
			let relations: any[] = [];
			try {
				relations = await getRelationList(projectId) || [];
			} catch { /* no relations yet */ }
			allRelations = relations;

			buildFlowGraph(entries, relations);
		} catch {
			allEntries = [];
			allRelations = [];
		} finally {
			isLoading = false;
		}
	}

	function buildFlowGraph(entries: any[], relations: any[]) {
		// Layout nodes in a grid
		const cols = Math.ceil(Math.sqrt(entries.length));
		const nodes: Node[] = entries.map((e: any, i: number) => {
			const modType = e._moduleType || e.moduleType || 'requirement';
			const color = typeColors[modType] || '#6B7280';
			return {
				id: e.id,
				position: { x: 80 + (i % cols) * 220, y: 80 + Math.floor(i / cols) * 130 },
				data: {
					label: e.title || '未命名',
					entityType: modType,
					entityId: e.id,
					moduleType: modType,
					status: e.status
				},
				style: {
					background: `${color}18`,
					borderColor: color,
					borderWidth: 2,
					borderRadius: 12,
					padding: '8px 16px',
					fontSize: 12,
					color: '#1f2937',
					minWidth: 140,
					textAlign: 'center',
					cursor: 'pointer'
				},
				sourcePosition: 'right' as const,
				targetPosition: 'left' as const
			};
		});

		const edges: Edge[] = relations.map((r: any) => ({
			id: r.id || `e-${r.entityAId}-${r.entityBId}`,
			source: r.entityAId,
			target: r.entityBId,
			label: relationLabels[r.relationType] || r.relationType,
			style: { stroke: relationColors[r.relationType] || '#94A3B8', strokeWidth: 2 },
			labelStyle: { fontSize: 10, fill: '#6B7280' },
			type: 'smoothstep',
			animated: r.relationType === 'conflicts'
		}));

		flowNodes = nodes;
		flowEdges = edges;
	}

	let filteredNodes = $derived(
		filterType === 'all' ? flowNodes : flowNodes.filter(n => n.data?.entityType === filterType)
	);

	function handleNodeClick(event: { node?: Node }) {
		const node = event.node;
		if (!node) return;
		selectedNodeId = node.id;
		selectedEntity = {
			id: node.id,
			name: node.data?.label || '未命名',
			type: node.data?.entityType || ''
		};
		showDetailPanel = true;
	}

	function handleNodeDoubleClick(event: { node?: Node }) {
		const node = event.node;
		if (!node) return;
		const moduleType = node.data?.moduleType;
		const entryId = node.id;
		if (moduleType) {
			goto(`/pm/${projectId}/${moduleType}?entryId=${entryId}`);
		}
	}

	function handleConnect(connection: Connection) {
		if (!connection.source || !connection.target) return;
		pendingConnection = { source: connection.source, target: connection.target };
		// Show relation type selector at center of viewport
		relationTypeSelectorPos = { x: 400, y: 300 };
	}

	async function handleRelationTypeSelect(relationType: RelationType) {
		if (!pendingConnection) return;
		try {
			const token = localStorage.token || '';
			const created = await createRelation(projectId, {
				entityAId: pendingConnection.source,
				entityBId: pendingConnection.target,
				relationType,
				confidence: 100,
				confirmed: 1,
				createdBy: 'user'
			});
			// Add edge to graph
			const newEdge: Edge = {
				id: created?.id || `e-${pendingConnection.source}-${pendingConnection.target}-${Date.now()}`,
				source: pendingConnection.source,
				target: pendingConnection.target,
				label: relationLabels[relationType] || relationType,
				style: { stroke: relationColors[relationType] || '#94A3B8', strokeWidth: 2 },
				labelStyle: { fontSize: 10, fill: '#6B7280' },
				type: 'smoothstep',
				animated: relationType === 'conflicts'
			};
			flowEdges = [...flowEdges, newEdge];
			toast.success('关联创建成功');
		} catch (e: any) {
			toast.error(e?.message || '创建关联失败');
		} finally {
			pendingConnection = null;
			relationTypeSelectorPos = null;
		}
	}

	function handleEdgeContextMenu(event: MouseEvent, edge: Edge) {
		event.preventDefault();
		edgeContextMenu = { x: event.clientX, y: event.clientY, edgeId: edge.id, relationId: edge.id };
	}

	async function handleDeleteEdge() {
		if (!edgeContextMenu) return;
		try {
			await deleteRelation(projectId, edgeContextMenu.relationId);
			flowEdges = flowEdges.filter(e => e.id !== edgeContextMenu!.edgeId);
			toast.success('关联已删除');
		} catch (e: any) {
			toast.error(e?.message || '删除失败');
		} finally {
			edgeContextMenu = null;
		}
	}

	function handleNavigateToEntry(moduleType: string, entryId: string) {
		goto(`/pm/${projectId}/${moduleType}?entryId=${entryId}`);
	}

	function handleRelationDeleted(relationId: string) {
		flowEdges = flowEdges.filter(e => e.id !== relationId);
	}

	onMount(() => { loadGraph(); });
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>溯源关系</div>
				<div class="text-lg font-medium text-gray-500">{allEntries.length} 实体 · {flowEdges.length} 关联</div>
			</div>
			<div class="flex items-center gap-2">
				<div class="flex items-center gap-1">
					{#each ['all', 'prd', 'requirement', 'parameter', 'testcase', 'risk', 'competitor'] as t}
						<button
							class="px-2 py-1 text-xs rounded-lg transition {filterType === t ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}"
							onclick={() => { filterType = t; }}
						>{t === 'all' ? '全部' : typeLabels[t] || t}</button>
					{/each}
				</div>
				<button class="px-2 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black transition font-medium text-sm flex items-center" onclick={loadGraph}>
					<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" /></svg>
					<div class="ml-1 text-xs">刷新</div>
				</button>
			</div>
		</div>
		<p class="text-xs text-gray-400 px-0.5">拖拽节点端口创建关联 · 单击查看详情 · 双击跳转编辑 · 右键连线删除</p>
	</div>

	<div class="bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 overflow-hidden flex" style="height: calc(100vh - 220px);">
		{#if isLoading}
			<div class="flex items-center justify-center w-full h-full"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div></div>
		{:else if allEntries.length === 0}
			<div class="flex flex-col items-center justify-center w-full h-full py-12">
				<svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 003.75.614m-16.5 0a3.004 3.004 0 01-.621-4.72L4.318 3.44A1.5 1.5 0 015.378 3h13.243a1.5 1.5 0 011.06.44l1.19 1.189a3 3 0 01-.621 4.72m-13.5 8.65h3.75a.75.75 0 00.75-.75V13.5a.75.75 0 00-.75-.75H6.75a.75.75 0 00-.75.75v3.15c0 .415.336.75.75.75z" /></svg>
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-2">暂无实体数据</p>
				<p class="text-xs text-gray-400">在各模块中创建条目后，关系图将自动生成</p>
			</div>
		{:else}
			<!-- Flow graph area -->
			<div class="flex-1 relative">
				<SvelteFlow
					nodes={filteredNodes}
					edges={flowEdges}
					fitView
					nodesDraggable={true}
					minZoom={0.3}
					maxZoom={2}
					onnodeclick={handleNodeClick}
					onnodedoubleclick={handleNodeDoubleClick}
					onconnect={handleConnect}
					onedgecontextmenu={(e: any) => {
						if (e.edge) handleEdgeContextMenu(e.event, e.edge);
					}}
				>
					<Background patternColor="#e5e7eb" gap={20} />
					<Controls />
				</SvelteFlow>
			</div>

			<!-- Detail panel -->
			{#if showDetailPanel && selectedEntity}
				<PMTraceDetailPanel
					{projectId}
					entityId={selectedEntity.id}
					entityName={selectedEntity.name}
					entityType={selectedEntity.type}
					onClose={() => { showDetailPanel = false; selectedEntity = null; }}
					onNavigate={handleNavigateToEntry}
					onRelationDeleted={handleRelationDeleted}
				/>
			{/if}
		{/if}
	</div>
</div>

<!-- Relation Type Selector popup -->
{#if relationTypeSelectorPos}
	<PMRelationTypeSelector
		position={relationTypeSelectorPos}
		onSelect={handleRelationTypeSelect}
		onCancel={() => { relationTypeSelectorPos = null; pendingConnection = null; }}
	/>
{/if}

<!-- Edge context menu -->
{#if edgeContextMenu}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="fixed inset-0 z-50" onclick={() => { edgeContextMenu = null; }}></div>
	<div
		class="fixed z-50 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden w-40"
		style="left: {edgeContextMenu.x}px; top: {edgeContextMenu.y}px;"
	>
		<button
			class="w-full text-left px-3 py-2 text-xs hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-colors"
			onclick={handleDeleteEdge}
		>
			删除关联
		</button>
		<button
			class="w-full text-left px-3 py-2 text-xs hover:bg-gray-50 dark:hover:bg-gray-750 text-gray-700 dark:text-gray-300 transition-colors"
			onclick={() => { edgeContextMenu = null; }}
		>
			取消
		</button>
	</div>
{/if}
