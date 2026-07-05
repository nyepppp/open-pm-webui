<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getEntries, createEntry, updateEntry, deleteEntry, getEntry } from '$lib/apis/pm/index';
	import { currentVersion, versions as versionList } from '$lib/stores/pm/versionStore';
	import type { ModuleEntry, ModuleStatus, Priority, MindMapNode } from '$lib/apis/pm/types';
	import PMMindMap from '$lib/components/pm/PMMindMap.svelte';
	import ModuleFeatureTree from '$lib/components/pm/ModuleFeatureTree.svelte';
	import ParameterTable from '$lib/components/pm/ParameterTable.svelte';

	// ============================================================================
	// Types
	// ============================================================================

	interface TreeModule {
		name: string;
		source: 'auto' | 'manual';
		features: TreeFeature[];
	}

	interface TreeFeature {
		name: string;
		source: 'auto' | 'manual';
		paramCount: number;
	}

	// ============================================================================
	// Route params
	// ============================================================================

	let projectId = $derived($page.params.projectId);

	// ============================================================================
	// Tab state
	// ============================================================================

	let activeTab = $state<'mindmap' | 'params'>('mindmap');
	let navigateToModule = $state<string | null>(null);
	let navigateToFeature = $state<string | null>(null);

	// Tree selection state (params tab)
	let selectedModule = $state<string | null>(null);
	let selectedFeature = $state<string | null>(null);
	let treeCollapsed = $state(false);

	$effect(() => {
		function onResize() {
			if (window.innerWidth < 768 && !treeCollapsed) treeCollapsed = true;
		}
		onResize();
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});

	// Sync cross-tab navigation into tree selection
	$effect(() => {
		if (navigateToModule) {
			selectedModule = navigateToModule;
			selectedFeature = navigateToFeature;
			navigateToModule = null;
			navigateToFeature = null;
		}
	});

	// ============================================================================
	// Data loading
	// ============================================================================

	let parameterEntries = $state<ModuleEntry[]>([]);
	let archEntries = $state<ModuleEntry[]>([]);
	let isLoading = $state(true);
	let loadError = $state('');

	async function loadData() {
		isLoading = true;
		loadError = '';
		try {
			const token = localStorage.token || '';
			if (!token) { loadError = '未登录，请先登录'; isLoading = false; return; }
			const [params, archs] = await Promise.all([
				getEntries(token, projectId!, 'parameter'),
				getEntries(token, projectId!, 'product-architecture')
			]);
			parameterEntries = params;
			archEntries = archs;
		} catch (e: any) {
			loadError = e?.message || '加载数据失败';
			console.error('[Architecture] loadData failed:', loadError);
		} finally {
			isLoading = false;
		}
	}

	onMount(() => { loadData(); });

	// ============================================================================
	// Aggregation: parameter moduleName/featureName → tree
	// ============================================================================

	function aggregateModuleFeatureTree(
		paramEntries: ModuleEntry[],
		architectureEntries: ModuleEntry[]
	): TreeModule[] {
		// 1. Auto modules from parameter entries
		const autoModules = new Map<string, Set<string>>();
		for (const entry of paramEntries) {
			const d = entry.data || {};
			const mod = (d.moduleName as string) || '';
			const feat = (d.featureName as string) || '';
			if (mod) {
				if (!autoModules.has(mod)) autoModules.set(mod, new Set());
				if (feat) autoModules.get(mod)!.add(feat);
			}
		}

		// 2. Manual modules/features from product-architecture entries
		const manualModules = new Map<string, Set<string>>();
		for (const entry of architectureEntries) {
			const d = entry.data || {};
			const nodes = d.nodes as MindMapNode[] | undefined;
			if (!nodes) continue;
			for (const node of nodes) {
				if (node.metadata?.source === 'manual') {
					if (node.type === 'branch') {
						if (!manualModules.has(node.label)) manualModules.set(node.label, new Set());
					} else if (node.type === 'leaf' && node.parentId) {
						const parent = nodes.find(n => n.id === node.parentId);
						if (parent) {
							if (!manualModules.has(parent.label)) manualModules.set(parent.label, new Set());
							manualModules.get(parent.label)!.add(node.label);
						}
					}
				}
			}
		}

		// 3. Merge: auto primary, manual supplements
		const allModules = new Map(autoModules);
		for (const [mod, feats] of manualModules) {
			if (!allModules.has(mod)) allModules.set(mod, new Set());
			for (const f of feats) allModules.get(mod)!.add(f);
		}

		// 4. Build TreeModule[]
		return [...allModules.entries()]
			.sort(([a], [b]) => a.localeCompare(b))
			.map(([name, features]) => ({
				name,
				source: autoModules.has(name) ? 'auto' as const : 'manual' as const,
				features: [...features].sort().map(f => ({
					name: f,
					source: (autoModules.get(name)?.has(f) ? 'auto' : 'manual') as 'auto' | 'manual',
					paramCount: paramEntries.filter(e =>
						(e.data?.moduleName === name) && (e.data?.featureName === f)
					).length
				}))
			}));
	}

	let aggregatedTree = $derived(aggregateModuleFeatureTree(parameterEntries, archEntries));

	// ============================================================================
	// Architecture entry for mindmap (use first arch entry, or create)
	// ============================================================================

	let mindmapNodes = $derived.by(() => {
		// Extract nodes from the first architecture entry
		if (archEntries.length > 0) {
			const data = archEntries[0].data || {};
			return (data.nodes as MindMapNode[]) || [];
		}
		return [];
	});

	let editingEntryId = $derived(archEntries[0]?.id || null);

	async function handleMindmapChange(nodes: MindMapNode[]) {
		if (!editingEntryId) {
			// Create a new architecture entry
			try {
				const token = localStorage.token || '';
				const currentVer = $currentVersion;
				const entryData: Record<string, unknown> = { nodes };
				if (currentVer?.id) {
					entryData.versionId = currentVer.id;
				}
				await createEntry(token, projectId!, {
					module_type: 'product-architecture',
					title: '产品架构图',
					status: 'draft',
					priority: 'p2',
					data: entryData
				});
				await loadData();
			} catch (e: any) {
				toast.error(e.message || '保存架构图失败');
			}
			return;
		}
		// Update existing entry
		try {
			const token = localStorage.token || '';
			await updateEntry(token, editingEntryId, {
				data: { ...(archEntries[0]?.data || {}), nodes }
			});
		} catch (e: any) {
			toast.error(e.message || '保存架构图失败');
		}
	}

	async function handleSync(diff: any) {
		await loadData();
	}

	// ============================================================================
	// Cross-tab navigation
	// ============================================================================

	function handleNavigate(target: { moduleName: string; featureName?: string }) {
		navigateToModule = target.moduleName;
		navigateToFeature = target.featureName || null;
		activeTab = 'params';
	}

	// ============================================================================
	// Manual module/feature management (saves to product-architecture API)
	// ============================================================================

	async function handleAddModule(name: string) {
		// Add a manual branch node to the architecture entry
		try {
			const currentNodes = mindmapNodes;
			const newId = `manual-${Date.now()}`;
			const newNode: MindMapNode = {
				id: newId,
				type: 'branch',
				label: name,
				parentId: null,
				position: { x: 0, y: 0 },
				createdAt: Date.now(),
				updatedAt: Date.now(),
				metadata: { source: 'manual' }
			};
			const updatedNodes = [...currentNodes, newNode];
			await handleMindmapChange(updatedNodes);
			await loadData();
			toast.success(`模块 "${name}" 已添加`);
		} catch (e: any) {
			toast.error(e.message || '添加模块失败');
		}
	}

	async function handleAddFeature(moduleName: string, featureName: string) {
		try {
			const currentNodes = mindmapNodes;
			const existingParent = currentNodes.find(n => n.label === moduleName && n.type === 'branch');

			let nodesToAdd: MindMapNode[] = [];

			let parentId: string;
			if (existingParent) {
				parentId = existingParent.id;
			} else {
				// Create parent module first
				parentId = `manual-${Date.now()}-parent`;
				nodesToAdd.push({
					id: parentId,
					type: 'branch',
					label: moduleName,
					parentId: null,
					position: { x: 0, y: 0 },
					createdAt: Date.now(),
					updatedAt: Date.now(),
					metadata: { source: 'manual' }
				});
			}

			const newId = `manual-${Date.now()}`;
			nodesToAdd.push({
				id: newId,
				type: 'leaf',
				label: featureName,
				parentId: parentId,
				position: { x: 0, y: 0 },
				createdAt: Date.now(),
				updatedAt: Date.now(),
				metadata: { source: 'manual' }
			});

			const updatedNodes = [...currentNodes, ...nodesToAdd];
			await handleMindmapChange(updatedNodes);
			await loadData();
			toast.success(`功能 "${featureName}" 已添加到 "${moduleName}"`);
		} catch (e: any) {
			toast.error(e.message || '添加功能失败');
		}
	}

	async function handleDeleteModule(name: string) {
		try {
			const currentNodes = mindmapNodes;
			// Remove the module node and all its children
			const moduleNode = currentNodes.find(n => n.label === name && n.type === 'branch');
			if (!moduleNode) return;
			const updatedNodes = currentNodes.filter(n =>
				n.id !== moduleNode.id && n.parentId !== moduleNode.id
			);
			await handleMindmapChange(updatedNodes);
			await loadData();
			if (selectedModule === name) {
				selectedModule = null;
				selectedFeature = null;
			}
			toast.success(`模块 "${name}" 已删除`);
		} catch (e: any) {
			toast.error(e.message || '删除模块失败');
		}
	}

	async function handleDeleteFeature(moduleName: string, featureName: string) {
		try {
			const currentNodes = mindmapNodes;
			const featureNode = currentNodes.find(
				n => n.label === featureName && n.type === 'leaf' &&
					currentNodes.find(p => p.id === n.parentId)?.label === moduleName
			);
			if (!featureNode) return;
			const updatedNodes = currentNodes.filter(n => n.id !== featureNode.id);
			await handleMindmapChange(updatedNodes);
			await loadData();
			if (selectedFeature === featureName) {
				selectedFeature = null;
			}
			toast.success(`功能 "${featureName}" 已删除`);
		} catch (e: any) {
			toast.error(e.message || '删除功能失败');
		}
	}

	function handleTreeSelect(module: string, feature?: string) {
		selectedModule = module;
		selectedFeature = feature || null;
	}

	async function handleParamDataChange() {
		await loadData();
	}

	// ============================================================================
	// Version data for mindmap
	// ============================================================================

	interface VersionOption {
		id: string;
		versionNumber: string;
		label?: string;
	}

	let versionOptions: VersionOption[] = $derived(
		$versionList.map((v: any) => ({
			id: v.id,
			versionNumber: v.versionNumber,
			label: v.label
		}))
	);

	// ============================================================================
	// Helper
	// ============================================================================

	function getEntryData(entry: any, key: string): string {
		return (entry.data || entry.metadata || {})[key] ?? '';
	}

	const statusMap: Record<string, { l: string; c: string }> = {
		draft: { l: '草稿', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' },
		review: { l: '评审中', c: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
		approved: { l: '已批准', c: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		archived: { l: '已归档', c: 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500' }
	};
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<!-- Header -->
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>产品架构</div>
			</div>
			<div class="flex w-full justify-end gap-1.5">
				<button
					class="px-2 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition font-medium text-sm flex items-center"
					title="AI 助手"
				>
					<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
					<div class="ml-1 text-xs">AI</div>
				</button>
			</div>
		</div>

		<!-- Tab Bar -->
		<div class="flex items-center gap-1 mt-1">
			<button
				class="px-4 py-1.5 text-sm font-medium rounded-lg transition-colors {activeTab === 'mindmap' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				onclick={() => { activeTab = 'mindmap'; }}
			>
				架构图
			</button>
			<button
				class="px-4 py-1.5 text-sm font-medium rounded-lg transition-colors {activeTab === 'params' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				onclick={() => { activeTab = 'params'; }}
			>
				参数详情
			</button>
		</div>
	</div>

	<!-- Content -->
	{#if isLoading}
		<div class="flex items-center justify-center h-64">
			<div class="text-gray-500 dark:text-gray-400">加载中...</div>
		</div>
	{:else if loadError}
		<div class="flex items-center justify-center h-64">
			<div class="text-red-500 dark:text-red-400">{loadError}</div>
		</div>
	{:else if activeTab === 'mindmap'}
		<div class="h-[calc(100vh-200px)]">
			<PMMindMap
				nodes={mindmapNodes}
				onChange={handleMindmapChange}
				projectId={projectId}
				versions={versionOptions}
				onSync={handleSync}
				aggregatedModules={aggregatedTree}
				onNavigate={handleNavigate}
			/>
		</div>
	{:else if activeTab === 'params'}
		<div class="flex gap-3 h-[calc(100vh-200px)]">
			<!-- Left: Module/Feature tree -->
			<div class="{treeCollapsed ? 'w-full' : 'w-64 shrink-0'} flex flex-col">
				<div class="flex items-center justify-between mb-2">
					{#if !treeCollapsed}
						<span class="text-sm font-medium text-gray-700 dark:text-gray-300">模块结构</span>
					{/if}
					<button
						class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"
						onclick={() => { treeCollapsed = !treeCollapsed; }}
						title={treeCollapsed ? '展开导航' : '收起导航'}
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							{#if treeCollapsed}
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
							{:else}
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
							{/if}
						</svg>
					</button>
				</div>
				<ModuleFeatureTree
					modules={aggregatedTree}
					{selectedModule}
					{selectedFeature}
					onSelect={handleTreeSelect}
					onAddModule={handleAddModule}
					onAddFeature={handleAddFeature}
					onDeleteModule={handleDeleteModule}
					onDeleteFeature={handleDeleteFeature}
					collapsed={treeCollapsed}
				/>
			</div>

			<!-- Right: Parameter table -->
			<div class="flex-1 min-w-0 overflow-hidden">
				<ParameterTable
					entries={parameterEntries}
					projectId={projectId!}
					filterModule={selectedModule}
					filterFeature={selectedFeature}
					onDataChange={handleParamDataChange}
				/>
			</div>
		</div>
	{/if}
</div>
