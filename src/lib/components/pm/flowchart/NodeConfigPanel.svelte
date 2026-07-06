<script lang="ts">
	import type { FlowchartNode } from '$lib/apis/pm/types';
	import type { ModuleEntry } from '$lib/apis/pm/types';
	import EntityBindingPanel from './EntityBindingPanel.svelte';

	interface Props {
		node: FlowchartNode;
		parameterEntries?: ModuleEntry[];
		projectId?: string;
		onUpdate: (nodeId: string, data: Partial<FlowchartNode['data']>) => void;
		onClose: () => void;
	}

	let { node, parameterEntries = [], projectId = '', onUpdate, onClose }: Props = $props();

	let nodeLabel = $state(node.data.label);
	let nodeDescription = $state(node.data.description || '');
	let selectedShape = $state(node.data.style?.shape || 'rounded');
	let bgColor = $state(node.data.style?.backgroundColor || '');
	let borderColor = $state(node.data.style?.borderColor || '');
	let selectedInputParams = $state<string[]>(node.data.inputParams || []);
	let selectedOutputParams = $state<string[]>(node.data.outputParams || []);
	let activeTab = $state<'basic' | 'binding'>('basic');

	const shapes = [
		{ value: 'rectangle', label: '矩形' },
		{ value: 'rounded', label: '圆角' },
		{ value: 'circle', label: '圆形' },
		{ value: 'diamond', label: '菱形' },
		{ value: 'ellipse', label: '椭圆' }
	];

	function saveChanges() {
		onUpdate(node.id, {
			label: nodeLabel,
			description: nodeDescription,
			style: {
				...node.data.style,
				shape: selectedShape,
				backgroundColor: bgColor || undefined,
				borderColor: borderColor || undefined
			},
			inputParams: selectedInputParams,
			outputParams: selectedOutputParams
		});
	}

	function toggleInputParam(paramId: string) {
		selectedInputParams = selectedInputParams.includes(paramId)
			? selectedInputParams.filter(id => id !== paramId)
			: [...selectedInputParams, paramId];
		saveChanges();
	}

	function toggleOutputParam(paramId: string) {
		selectedOutputParams = selectedOutputParams.includes(paramId)
			? selectedOutputParams.filter(id => id !== paramId)
			: [...selectedOutputParams, paramId];
		saveChanges();
	}

	function handleBind(binding: { entityType: string; entityId: string; entityName: string }) {
		const traceabilityData: Record<string, unknown> = {
			...binding,
			boundAt: Date.now()
		};
		onUpdate(node.id, {
			traceability: traceabilityData
		});
	}

	function handleUnbind() {
		const data: Record<string, unknown> = {};
		onUpdate(node.id, data);
	}
</script>

<div class="absolute right-0 top-0 h-full w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-y-auto z-20 shadow-lg">
	<div class="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">节点配置</h3>
		<button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" onclick={onClose}>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
		</button>
	</div>

	<!-- Tabs -->
	<div class="flex border-b border-gray-200 dark:border-gray-700">
		<button
			class="flex-1 px-3 py-2 text-xs font-medium transition {activeTab === 'basic' ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
			onclick={() => activeTab = 'basic'}
		>
			基础配置
		</button>
		<button
			class="flex-1 px-3 py-2 text-xs font-medium transition {activeTab === 'binding' ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
			onclick={() => activeTab = 'binding'}
		>
			溯源绑定
		</button>
	</div>

	<div class="p-3 space-y-4">
		{#if activeTab === 'basic'}
			<!-- Basic Properties -->
			<div>
				<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">名称</label>
				<input
					type="text"
					class="w-full px-2 py-1.5 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 outline-hidden focus:ring-1 focus:ring-blue-400"
					bind:value={nodeLabel}
					onchange={saveChanges}
				/>
			</div>

			<div>
				<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">描述</label>
				<textarea
					class="w-full px-2 py-1.5 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 outline-hidden focus:ring-1 focus:ring-blue-400 resize-none"
					rows="2"
					bind:value={nodeDescription}
					onchange={saveChanges}
				></textarea>
			</div>

			<!-- Shape Selector -->
			<div>
				<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">形状</label>
				<select
					class="w-full px-2 py-1.5 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 outline-hidden"
					bind:value={selectedShape}
					onchange={saveChanges}
				>
					{#each shapes as shape}
						<option value={shape.value}>{shape.label}</option>
					{/each}
				</select>
			</div>

			<!-- Colors -->
			<div class="grid grid-cols-2 gap-2">
				<div>
					<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">背景色</label>
					<input
						type="color"
						class="w-full h-8 rounded border border-gray-200 dark:border-gray-600 cursor-pointer"
						bind:value={bgColor}
						onchange={saveChanges}
					/>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">边框色</label>
					<input
						type="color"
						class="w-full h-8 rounded border border-gray-200 dark:border-gray-600 cursor-pointer"
						bind:value={borderColor}
						onchange={saveChanges}
					/>
				</div>
			</div>

			<!-- Input Parameters -->
			<div>
				<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">输入参数</label>
				<div class="max-h-32 overflow-y-auto space-y-1">
					{#if parameterEntries.length === 0}
						<span class="text-xs text-gray-400">暂无参数</span>
					{:else}
						{#each parameterEntries as param}
							<label class="flex items-center gap-1.5 text-xs text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 px-1 py-0.5 rounded">
								<input
									type="checkbox"
									class="rounded border-gray-300 text-blue-500 focus:ring-blue-400"
									checked={selectedInputParams.includes(param.id)}
									onchange={() => toggleInputParam(param.id)}
								/>
								<span class="truncate">{param.title || param.id}</span>
							</label>
						{/each}
					{/if}
				</div>
			</div>

			<!-- Output Parameters -->
			<div>
				<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">输出参数</label>
				<div class="max-h-32 overflow-y-auto space-y-1">
					{#if parameterEntries.length === 0}
						<span class="text-xs text-gray-400">暂无参数</span>
					{:else}
						{#each parameterEntries as param}
							<label class="flex items-center gap-1.5 text-xs text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 px-1 py-0.5 rounded">
								<input
									type="checkbox"
									class="rounded border-gray-300 text-pink-500 focus:ring-pink-400"
									checked={selectedOutputParams.includes(param.id)}
									onchange={() => toggleOutputParam(param.id)}
								/>
								<span class="truncate">{param.title || param.id}</span>
							</label>
						{/each}
					{/if}
				</div>
			</div>
		{:else}
			<!-- Traceability Binding -->
			<EntityBindingPanel
				{projectId}
				currentBinding={node.data.traceability}
				onBind={handleBind}
				onUnbind={handleUnbind}
			/>
		{/if}
	</div>
</div>
