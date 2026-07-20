<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { NodeTypeDefinition } from './nodes';
	import ParameterField from './parameters/ParameterField.svelte';

	interface Props {
		nodeType: NodeTypeDefinition | null;
		nodeConfig: Record<string, any>;
		onConfigChange?: (config: Record<string, any>) => void;
		onClose?: () => void;
	}

	let { nodeType, nodeConfig, onConfigChange, onClose }: Props = $props();

	const dispatch = createEventDispatcher();

	let localConfig = $state({ ...nodeConfig });

	function handleParameterChange(paramId: string, value: any) {
		localConfig = { ...localConfig, [paramId]: value };
		onConfigChange?.(localConfig);
		dispatch('configChange', { config: localConfig });
	}

	function handleSave() {
		onConfigChange?.(localConfig);
		dispatch('save', { config: localConfig });
	}

	function handleReset() {
		localConfig = { ...nodeConfig };
		dispatch('reset');
	}
</script>

{#if nodeType}
	<div class="w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
		<!-- Header -->
		<div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
			<div class="flex items-center gap-2">
				<div
					class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
					style="background-color: {nodeType.color}"
				>
					{nodeType.label.charAt(0)}
				</div>
				<div>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-white">{nodeType.label}</h3>
					<p class="text-xs text-gray-500 dark:text-gray-400">{nodeType.type}</p>
				</div>
			</div>
			<button
				class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
				onclick={() => onClose?.()}
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Description -->
		<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
			<p class="text-xs text-gray-600 dark:text-gray-400">{nodeType.description}</p>
		</div>

		<!-- Parameters -->
		<div class="flex-1 overflow-y-auto p-4 space-y-4">
			{#if nodeType.parameters.length > 0}
				<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
					参数配置
				</h4>
				{#each nodeType.parameters as parameter (parameter.id)}
					<ParameterField
						{parameter}
						value={localConfig[parameter.id]}
						onChange={(value) => handleParameterChange(parameter.id, value)}
					/>
				{/each}
			{:else}
				<div class="text-center py-8">
					<p class="text-sm text-gray-500 dark:text-gray-400">此节点无需配置</p>
				</div>
			{/if}
		</div>

		<!-- Footer -->
		<div class="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
			<button
				class="w-full px-3 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
				onclick={handleSave}
			>
				保存配置
			</button>
			<button
				class="w-full px-3 py-2 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
				onclick={handleReset}
			>
				重置
			</button>
		</div>
	</div>
{:else}
	<div class="w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex items-center justify-center h-full">
		<div class="text-center p-4">
			<p class="text-sm text-gray-500 dark:text-gray-400">选择一个节点以配置</p>
		</div>
	</div>
{/if}
