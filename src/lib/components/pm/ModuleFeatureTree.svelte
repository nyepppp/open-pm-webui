<script lang="ts">
	import type { ModuleEntry } from '$lib/apis/pm/types';

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

	interface Props {
		modules: TreeModule[];
		selectedModule?: string | null;
		selectedFeature?: string | null;
		onSelect?: (module: string, feature?: string) => void;
		onAddModule?: (name: string) => void;
		onAddFeature?: (moduleName: string, featureName: string) => void;
		onDeleteModule?: (name: string) => void;
		onDeleteFeature?: (moduleName: string, featureName: string) => void;
		collapsed?: boolean;
		versionInfo?: { id: string; versionNumber: string; label?: string } | null;
	}

	let {
		modules = [],
		selectedModule = null,
		selectedFeature = null,
		onSelect,
		onAddModule,
		onAddFeature,
		onDeleteModule,
		onDeleteFeature,
		collapsed = false,
		versionInfo = null
	}: Props = $props();

	let expandedModules = $state<Set<string>>(new Set());
	let showAddModuleInput = $state(false);
	let newModuleName = $state('');
	let showAddFeatureModule = $state<string | null>(null);
	let newFeatureName = $state('');

	let searchQuery = $state('');
	let filteredModules = $derived.by(() => {
		if (!searchQuery.trim()) return modules;
		const q = searchQuery.toLowerCase();
		return modules.filter(mod => 
			mod.name.toLowerCase().includes(q) || 
			mod.features.some(f => f.name.toLowerCase().includes(q))
		);
	});

	// Auto-expand the module containing selectedFeature
	$effect(() => {
		if (selectedModule) {
			expandedModules = new Set([...expandedModules, selectedModule]);
		}
	});

	function toggleModule(name: string) {
		const next = new Set(expandedModules);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		expandedModules = next;
	}

	function handleModuleClick(name: string) {
		toggleModule(name);
		onSelect?.(name);
	}

	function handleFeatureClick(moduleName: string, featureName: string) {
		onSelect?.(moduleName, featureName);
	}

	function handleAddModule() {
		if (newModuleName.trim()) {
			onAddModule?.(newModuleName.trim());
			newModuleName = '';
			showAddModuleInput = false;
		}
	}

	function handleAddFeature(moduleName: string) {
		if (newFeatureName.trim()) {
			onAddFeature?.(moduleName, newFeatureName.trim());
			newFeatureName = '';
			showAddFeatureModule = null;
		}
	}
</script>

{#if collapsed}
	<!-- Collapsed mode: dropdown selectors -->
	<div class="flex gap-2 items-center flex-wrap">
		<select
			class="px-2 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
			value={selectedModule ?? ''}
			onchange={(e) => { const v = (e.target as HTMLSelectElement).value; onSelect?.(v || '', undefined); }}
		>
			<option value="">全部模块</option>
			{#each modules as mod}
				<option value={mod.name}>{mod.name} {mod.source === 'manual' ? '(规划中)' : ''}</option>
			{/each}
		</select>
		{#if selectedModule}
			{@const mod = modules.find(m => m.name === selectedModule)}
			{#if mod && mod.features.length > 0}
				<select
					class="px-2 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
					value={selectedFeature ?? ''}
					onchange={(e) => { const v = (e.target as HTMLSelectElement).value; onSelect?.(selectedModule, v || undefined); }}
				>
					<option value="">全部功能</option>
					{#each mod.features as feat}
						<option value={feat.name}>{feat.name} ({feat.paramCount})</option>
					{/each}
				</select>
			{/if}
		{/if}
	</div>
{:else}
	<!-- Expanded mode: tree navigation -->
	<div class="flex flex-col gap-0.5 overflow-y-auto text-sm">
		<!-- Search -->
		<div class="px-2 py-1.5">
			<div class="relative">
				<svg class="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="text"
					class="w-full pl-8 pr-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 placeholder-gray-400"
					placeholder="搜索模块或功能..."
					bind:value={searchQuery}
				/>
			</div>
		</div>
		
		<!-- Version info -->
		{#if versionInfo}
			<div class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
				版本: <span class="font-medium text-gray-700 dark:text-gray-300">{versionInfo.versionNumber}</span>
			</div>
		{/if}
		
		{#each filteredModules as mod}
			<!-- Module node -->
			<button
				class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-left transition-colors {selectedModule === mod.name ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'}"
				onclick={() => handleModuleClick(mod.name)}
			>
				<svg class="w-3.5 h-3.5 shrink-0 transition-transform {expandedModules.has(mod.name) ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
				<span class="truncate">{mod.name}</span>
				{#if mod.source === 'manual'}
					<span class="text-xs text-orange-500 dark:text-orange-400 shrink-0">规划中</span>
				{/if}
				<span class="text-xs text-gray-400 ml-auto shrink-0">{mod.features.length}</span>
				{#if mod.source === 'manual' && onDeleteModule}
					<button
						class="ml-0.5 text-gray-300 hover:text-red-500 dark:text-gray-600 dark:hover:text-red-400 transition-colors"
						onclick={(e) => { e.stopPropagation(); onDeleteModule?.(mod.name); }}
						title="删除模块"
					>
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
					</button>
				{/if}
			</button>

			<!-- Features under module -->
			{#if expandedModules.has(mod.name)}
				<div class="ml-5 flex flex-col gap-0.5">
					{#each mod.features as feat}
						<button
							class="flex items-center gap-1.5 px-2 py-1 rounded-lg text-left transition-colors {selectedModule === mod.name && selectedFeature === feat.name ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50 text-gray-600 dark:text-gray-400'}"
							onclick={() => handleFeatureClick(mod.name, feat.name)}
						>
							<span class="truncate">{feat.name}</span>
							{#if feat.source === 'manual'}
								<span class="text-xs text-orange-500 dark:text-orange-400 shrink-0">规划中</span>
							{/if}
							<span class="text-xs text-gray-400 ml-auto shrink-0">{feat.paramCount}</span>
							{#if feat.source === 'manual' && onDeleteFeature}
								<button
									class="ml-0.5 text-gray-300 hover:text-red-500 dark:text-gray-600 dark:hover:text-red-400 transition-colors"
									onclick={(e) => { e.stopPropagation(); onDeleteFeature?.(mod.name, feat.name); }}
									title="删除功能"
								>
									<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
								</button>
							{/if}
						</button>
					{/each}

					<!-- Add feature button -->
					{#if showAddFeatureModule === mod.name}
						<div class="flex items-center gap-1 px-2 py-1">
							<input
								type="text"
								class="flex-1 px-1.5 py-0.5 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800"
								placeholder="功能名称"
								bind:value={newFeatureName}
								onkeydown={(e) => { if (e.key === 'Enter') handleAddFeature(mod.name); if (e.key === 'Escape') showAddFeatureModule = null; }}
							/>
							<button class="text-xs text-blue-600" onclick={() => handleAddFeature(mod.name)}>✓</button>
							<button class="text-xs text-gray-400" onclick={() => { showAddFeatureModule = null; newFeatureName = ''; }}>✕</button>
						</div>
					{:else}
						<button
							class="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-blue-600 transition-colors"
							onclick={() => { showAddFeatureModule = mod.name; newFeatureName = ''; }}
						>
							+ 添加功能
						</button>
					{/if}
				</div>
			{/if}
		{/each}

		<!-- Add module -->
		{#if showAddModuleInput}
			<div class="flex items-center gap-1 px-2 py-1.5">
				<input
					type="text"
					class="flex-1 px-1.5 py-0.5 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800"
					placeholder="模块名称"
					bind:value={newModuleName}
					onkeydown={(e) => { if (e.key === 'Enter') handleAddModule(); if (e.key === 'Escape') showAddModuleInput = false; }}
				/>
				<button class="text-xs text-blue-600" onclick={handleAddModule}>✓</button>
				<button class="text-xs text-gray-400" onclick={() => { showAddModuleInput = false; newModuleName = ''; }}>✕</button>
			</div>
		{:else}
			<button
				class="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-400 hover:text-blue-600 transition-colors"
				onclick={() => { showAddModuleInput = true; newModuleName = ''; }}
			>
				+ 添加模块
			</button>
		{/if}
	</div>
{/if}
