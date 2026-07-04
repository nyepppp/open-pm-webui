<script lang="ts">
	import { BaseEdge, EdgeLabel, getBezierPath, type EdgeProps } from '@xyflow/svelte';

	let {
		label,
		labelStyle,
		sourceX,
		sourceY,
		sourcePosition,
		targetX,
		targetY,
		targetPosition,
		data,
		...rest
	}: EdgeProps = $props();

	let [edgePath, labelX, labelY] = $derived(getBezierPath({
		sourceX,
		sourceY,
		targetX,
		targetY,
		sourcePosition,
		targetPosition,
	}));

	// Extract style from edge data
	let edgeData = $derived((data as Record<string, unknown>) || {});
	let edgeStyle = $derived((edgeData.style as Record<string, unknown>) || {});

	let strokeColor = $derived((edgeStyle.stroke as string) || '#b1b1b7');
	let strokeWidth = $derived((edgeStyle.strokeWidth as number) || 1.5);
	let strokeDasharray = $derived(edgeStyle.strokeDasharray as string | undefined);
	let animated = $derived(edgeStyle.animated as boolean | false);
</script>

<BaseEdge
	path={edgePath}
	markerStart={rest.markerStart}
	markerEnd={rest.markerEnd}
	interactionWidth={rest.interactionWidth}
	style="stroke: {strokeColor}; stroke-width: {strokeWidth}; {strokeDasharray ? `stroke-dasharray: ${strokeDasharray};` : ''}"
/>

{#if animated}
	<path
		d={edgePath}
		fill="none"
		stroke={strokeColor}
		stroke-width={strokeWidth}
		stroke-dasharray="5 5"
		class="animate-dash"
	>
		<animate
			attributeName="stroke-dashoffset"
			values="0;20"
			dur="0.5s"
			repeatCount="indefinite"
		/>
	</path>
{/if}

{#if label}
	<EdgeLabel x={labelX} y={labelY} style={labelStyle}>
		{label}
	</EdgeLabel>
{/if}
