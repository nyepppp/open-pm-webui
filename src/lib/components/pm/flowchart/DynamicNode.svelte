<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import type { NodeProps } from '@xyflow/svelte';
	import TraceabilityBadge from './TraceabilityBadge.svelte';

	let { id, data, selected }: NodeProps = $props();

	// Derive visual properties from node type and data
	let nodeType = $derived((data as Record<string, unknown>)?.type as string || 'process');
	let label = $derived((data as Record<string, unknown>)?.label as string || '节点');
	let description = $derived((data as Record<string, unknown>)?.description as string || '');
	let inputParams = $derived(((data as Record<string, unknown>)?.inputParams as string[]) || []);
	let outputParams = $derived(((data as Record<string, unknown>)?.outputParams as string[]) || []);
	let style = $derived((data as Record<string, unknown>)?.style as Record<string, unknown> | undefined);
	let traceability = $derived(((data as Record<string, unknown>)?.traceability as { entityType: string; entityId: string; entityName: string; versionNumber?: string } | undefined));

	// Shape from style override or default based on type
	let shape = $derived(
		(style?.shape as string) ||
		(nodeType === 'start' ? 'ellipse' :
			nodeType === 'end' ? 'ellipse' :
			nodeType === 'decision' ? 'diamond' : 'rounded')
	);

	// Colors from style override or default based on type
	let bgColor = $derived(
		(style?.backgroundColor as string) ||
		(nodeType === 'start' ? '#dcfce7' :
			nodeType === 'end' ? '#fee2e2' :
			nodeType === 'decision' ? '#fef9c3' :
			nodeType === 'parameter-input' ? '#f3e8ff' :
			nodeType === 'parameter-output' ? '#fce7f3' : '#dbeafe')
	);
	let borderColor = $derived(
		(style?.borderColor as string) ||
		(nodeType === 'start' ? '#86efac' :
			nodeType === 'end' ? '#fca5a5' :
			nodeType === 'decision' ? '#fde047' :
			nodeType === 'parameter-input' ? '#c4b5fd' :
			nodeType === 'parameter-output' ? '#f9a8d4' : '#93c5fd')
	);

	// Container classes based on shape
	let containerClass = $derived(
		shape === 'diamond'
			? 'relative flex items-center justify-center'
			: shape === 'circle'
				? 'rounded-full flex items-center justify-center'
				: shape === 'ellipse'
					? 'rounded-[50%] flex items-center justify-center'
					: 'rounded-lg flex items-center justify-center'
	);
</script>

{#if shape === 'diamond'}
	<div
		class="relative"
		style="width: {(style?.width as number) || 140}px; height: {(style?.height as number) || 80}px;"
	>
		<div
			class="absolute inset-0 rotate-45 {selected ? 'ring-2 ring-blue-400' : ''}"
			style="background-color: {bgColor}; border: {(style?.borderWidth as number) || 2}px solid {borderColor}; border-radius: 4px;"
		></div>
		<div class="relative z-10 flex flex-col items-center justify-center h-full text-center px-4">
			<span class="text-xs font-medium text-gray-800 dark:text-gray-200 truncate max-w-[100px]">{label}</span>
			{#if inputParams.length || outputParams.length}
				<div class="flex gap-1 mt-0.5">
					{#if inputParams.length}
						<span class="text-[10px] px-1 py-0.5 rounded bg-purple-100 text-purple-600">入{inputParams.length}</span>
					{/if}
					{#if outputParams.length}
						<span class="text-[10px] px-1 py-0.5 rounded bg-pink-100 text-pink-600">出{outputParams.length}</span>
					{/if}
				</div>
			{/if}
			<TraceabilityBadge {traceability} />
		</div>
		<Handle type="target" position={Position.Top} id="target" class="!bg-gray-400 !w-2 !h-2 !border-0" />
		<Handle type="source" position={Position.Bottom} id="source" class="!bg-gray-400 !w-2 !h-2 !border-0" />
	</div>
{:else}
	<div
		class="{containerClass} {selected ? 'ring-2 ring-blue-400' : ''} flex-col gap-0.5 shadow-sm"
		style="background-color: {bgColor}; border: {(style?.borderWidth as number) || 2}px solid {borderColor}; min-width: {(style?.width as number) || 120}px; min-height: {(style?.height as number) || 50}px; padding: 8px 12px;"
	>
		{#if nodeType === 'parameter-input'}
			<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-200 text-purple-700 font-medium self-start">输入</span>
		{:else if nodeType === 'parameter-output'}
			<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-pink-200 text-pink-700 font-medium self-start">输出</span>
		{/if}
		<span class="text-xs font-medium text-gray-800 dark:text-gray-200 text-center truncate max-w-[140px]">{label}</span>
		{#if description}
			<span class="text-[10px] text-gray-500 dark:text-gray-400 text-center truncate max-w-[120px]">{description}</span>
		{/if}
		{#if inputParams.length || outputParams.length}
			<div class="flex gap-1">
				{#if inputParams.length}
					<span class="text-[10px] px-1 py-0.5 rounded bg-purple-100 text-purple-600">入{inputParams.length}</span>
				{/if}
				{#if outputParams.length}
					<span class="text-[10px] px-1 py-0.5 rounded bg-pink-100 text-pink-600">出{outputParams.length}</span>
				{/if}
			</div>
		{/if}
		<TraceabilityBadge {traceability} />
		<Handle type="target" position={Position.Top} id="target" class="!bg-gray-400 !w-2 !h-2 !border-0" />
		<Handle type="source" position={Position.Bottom} id="source" class="!bg-gray-400 !w-2 !h-2 !border-0" />
	</div>
{/if}
