<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getEntries } from '$lib/apis/pm/index';

	let projectId = $derived($page.params.projectId);

	// Entity types from PRD §3.5
	interface Entity {
		id: string;
		type: string;
		name: string;
		moduleId?: string;
		x: number;
		y: number;
	}

	interface Relation {
		id: string;
		entityAId: string;
		entityBId: string;
		relationType: string;
		confidence: number;
		confirmed: number;
		createdBy: string;
	}

	const typeColors: Record<string, string> = {
		requirement: '#3B82F6',
		document: '#8B5CF6',
		parameter: '#10B981',
		module: '#F59E0B',
		feature: '#EF4444',
		version: '#6366F1'
	};

	const typeLabels: Record<string, string> = {
		requirement: '需求',
		document: '文档',
		parameter: '参数',
		module: '模块',
		feature: '功能',
		version: '版本'
	};

	const relationLabels: Record<string, string> = {
		contains: '包含',
		references: '引用',
		derives: '派生',
		modifies: '修改',
		conflicts: '冲突'
	};

	let entities = $state<Entity[]>([]);
	let relations = $state<Relation[]>([]);
	let isLoading = $state(true);
	let selectedEntity = $state<Entity | null>(null);
	let showAddRelation = $state(false);
	let filterType = $state<string>('all');
	let filterRelation = $state<string>('all');

	// Load entities from all modules as graph nodes
	async function loadGraph() {
		isLoading = true;
		try {
			const token = localStorage.token || '';
			const modules = ['prd', 'requirement', 'parameter', 'testcase', 'risk', 'competitor'];
			const allEntries: any[] = [];
			for (const mod of modules) {
				try {
					const entries = await getEntries(token, projectId, mod);
					if (Array.isArray(entries)) {
						entries.forEach((e: any) => allEntries.push({ ...e, _moduleType: mod }));
					}
				} catch { /* skip module if empty */ }
			}
			// Map entries to entities with positions in a grid
			const cols = Math.ceil(Math.sqrt(allEntries.length));
			entities = allEntries.map((e: any, i: number) => ({
				id: e.id,
				type: e._moduleType === 'prd' ? 'document' : e._moduleType === 'parameter' ? 'parameter' : 'requirement',
				name: e.title || e.name || '未命名',
				moduleId: e._moduleType,
				x: 80 + (i % cols) * 180,
				y: 80 + Math.floor(i / cols) * 120
			}));
			relations = [];
		} catch {
			entities = [];
			relations = [];
		} finally {
			isLoading = false;
		}
	}

	onMount(() => { loadGraph(); });

	let filteredEntities = $derived(
		filterType === 'all' ? entities : entities.filter(e => e.type === filterType)
	);

	let filteredRelations = $derived(
		filterRelation === 'all' ? relations : relations.filter(r => r.relationType === filterRelation)
	);

	// Drag state
	let dragging = $state<Entity | null>(null);
	let dragOffset = $state({ x: 0, y: 0 });

	function startDrag(e: MouseEvent, entity: Entity) {
		dragging = entity;
		dragOffset = { x: e.clientX - entity.x, y: e.clientY - entity.y };
	}

	function onDrag(e: MouseEvent) {
		if (!dragging) return;
		const idx = entities.findIndex(en => en.id === dragging.id);
		if (idx >= 0) {
			entities[idx] = { ...entities[idx], x: e.clientX - dragOffset.x, y: e.clientY - dragOffset.y };
			entities = [...entities];
		}
	}

	function stopDrag() { dragging = null; }
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>溯源关系</div>
				<div class="text-lg font-medium text-gray-500">{entities.length} 实体</div>
			</div>
			<div class="flex items-center gap-2">
				<!-- Type filter -->
				<div class="flex items-center gap-1">
					{#each ['all', 'requirement', 'document', 'parameter', 'module', 'feature', 'version'] as t}
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
	</div>

	<div class="bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 overflow-hidden" style="height: calc(100vh - 200px);">
		{#if isLoading}
			<div class="flex items-center justify-center h-full"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div></div>
		{:else if entities.length === 0}
			<div class="flex flex-col items-center justify-center h-full py-12">
				<svg class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 003.75.614m-16.5 0a3.004 3.004 0 01-.621-4.72L4.318 3.44A1.5 1.5 0 015.378 3h13.243a1.5 1.5 0 011.06.44l1.19 1.189a3 3 0 01-.621 4.72m-13.5 8.65h3.75a.75.75 0 00.75-.75V13.5a.75.75 0 00-.75-.75H6.75a.75.75 0 00-.75.75v3.15c0 .415.336.75.75.75z" /></svg>
				<p class="text-sm text-gray-500 dark:text-gray-400 mb-2">暂无实体数据</p>
				<p class="text-xs text-gray-400">在各模块中创建条目后，关系图将自动生成</p>
			</div>
		{:else}
			<!-- SVG-based relation graph -->
			<svg
				class="w-full h-full"
				onmousemove={onDrag}
				onmouseup={stopDrag}
				onmouseleave={stopDrag}
				viewBox="0 0 {Math.max(800, Math.max(...entities.map(e => e.x)) + 100)} {Math.max(400, Math.max(...entities.map(e => e.y)) + 100)}"
			>
				<!-- Relation lines -->
				{#each filteredRelations as rel (rel.id)}
					{@const a = entities.find(e => e.id === rel.entityAId)}
					{@const b = entities.find(e => e.id === rel.entityBId)}
					{#if a && b}
						<line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
							stroke={rel.relationType === 'conflicts' ? '#EF4444' : rel.relationType === 'derives' ? '#8B5CF6' : '#94A3B8'}
							stroke-width="2"
							stroke-dasharray={rel.confirmed === 0 ? '6 3' : 'none'}
							opacity="0.6"
						/>
					{/if}
				{/each}

				<!-- Entity nodes -->
				{#each filteredEntities as entity (entity.id)}
					<g
						transform="translate({entity.x}, {entity.y})"
						class="cursor-grab active:cursor-grabbing"
						onmousedown={(e) => startDrag(e, entity)}
						onclick={() => { selectedEntity = selectedEntity?.id === entity.id ? null : entity; }}
					>
						<circle r="28" fill={typeColors[entity.type] || '#6B7280'} opacity="0.15" stroke={typeColors[entity.type] || '#6B7280'} stroke-width={selectedEntity?.id === entity.id ? 3 : 1.5} />
						<text text-anchor="middle" y="4" class="text-[10px] fill-gray-700 dark:fill-gray-300" style="pointer-events: none;">{entity.name.slice(0, 6)}</text>
						<text text-anchor="middle" y="-20" class="text-[8px] fill-gray-400" style="pointer-events: none;">{typeLabels[entity.type] || entity.type}</text>
					</g>
				{/each}
			</svg>
		{/if}
	</div>

	<!-- Selected entity detail -->
	{#if selectedEntity}
		<div class="fixed bottom-4 right-4 w-80 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-4 z-50">
			<div class="flex items-center justify-between mb-2">
				<h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100">{selectedEntity.name}</h4>
				<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" onclick={() => { selectedEntity = null; }}>
					<svg class="size-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
				</button>
			</div>
			<div class="flex items-center gap-2 mb-2">
				<span class="px-2 py-0.5 text-xs rounded-full" style="background: {typeColors[selectedEntity.type]}20; color: {typeColors[selectedEntity.type]}">{typeLabels[selectedEntity.type]}</span>
				{#if selectedEntity.moduleId}
					<span class="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500">{selectedEntity.moduleId}</span>
				{/if}
			</div>
			<div class="space-y-1 text-xs text-gray-500">
				<p>关联数: {relations.filter(r => r.entityAId === selectedEntity.id || r.entityBId === selectedEntity.id).length}</p>
			</div>
		</div>
	{/if}
</div>
