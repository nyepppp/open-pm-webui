<script lang="ts">
	interface Props {
		nodes: any[];
		edges: any[];
		onNodesChange?: (nodes: any[]) => void;
		onEdgesChange?: (edges: any[]) => void;
		onConnect?: (connection: any) => void;
		onNodeClick?: (node: any) => void;
		onPaneClick?: () => void;
		readonly?: boolean;
	}

	let { 
		nodes = [], 
		edges = [], 
		onNodesChange, 
		onEdgesChange, 
		onConnect, 
		onNodeClick, 
		onPaneClick,
		readonly = false 
	}: Props = $props();

	let localNodes = $state<any[]>([]);
	let localEdges = $state<any[]>([]);
	let selectedNodeId = $state<string | null>(null);
	let isDragging = $state(false);
	let dragOffset = $state({ x: 0, y: 0 });
	let svgElement = $state<SVGSVGElement | null>(null);

	$effect(() => {
		localNodes = nodes ? [...nodes] : [];
	});

	$effect(() => {
		localEdges = edges ? [...edges] : [];
	});

	function getNodeDimensions(node: any) {
		const shape = node.data?.shape || 'rectangle';
		const defaultWidth = shape === 'diamond' ? 100 : 140;
		const defaultHeight = shape === 'diamond' ? 100 : 60;
		return {
			width: node.style?.width ? parseInt(node.style.width) : defaultWidth,
			height: node.style?.height ? parseInt(node.style.height) : defaultHeight
		};
	}

	function getNodeShape(node: any) {
		const { width, height } = getNodeDimensions(node);
		const shape = node.data?.shape || 'rectangle';
		
		switch (shape) {
			case 'circle':
				return `M ${node.position.x + width/2} ${node.position.y} A ${width/2} ${height/2} 0 1 1 ${node.position.x + width/2} ${node.position.y + height} A ${width/2} ${height/2} 0 1 1 ${node.position.x + width/2} ${node.position.y}`;
			case 'diamond':
				return `M ${node.position.x + width/2} ${node.position.y} L ${node.position.x + width} ${node.position.y + height/2} L ${node.position.x + width/2} ${node.position.y + height} L ${node.position.x} ${node.position.y + height/2} Z`;
			case 'ellipse':
				return `M ${node.position.x + width/2} ${node.position.y} A ${width/2} ${height/2} 0 1 1 ${node.position.x + width/2} ${node.position.y + height} A ${width/2} ${height/2} 0 1 1 ${node.position.x + width/2} ${node.position.y}`;
			default:
				// rectangle or rounded
				const rx = shape === 'rounded' ? 12 : 0;
				return `M ${node.position.x + rx} ${node.position.y} H ${node.position.x + width - rx} Q ${node.position.x + width} ${node.position.y} ${node.position.x + width} ${node.position.y + rx} V ${node.position.y + height - rx} Q ${node.position.x + width} ${node.position.y + height} ${node.position.x + width - rx} ${node.position.y + height} H ${node.position.x + rx} Q ${node.position.x} ${node.position.y + height} ${node.position.x} ${node.position.y + height - rx} V ${node.position.y + rx} Q ${node.position.x} ${node.position.y} ${node.position.x + rx} ${node.position.y}`;
		}
	}

	function getEdgePath(edge: any) {
		const sourceNode = localNodes.find(n => n.id === edge.source);
		const targetNode = localNodes.find(n => n.id === edge.target);
		if (!sourceNode || !targetNode) return '';

		const sourceDim = getNodeDimensions(sourceNode);
		const targetDim = getNodeDimensions(targetNode);

		const sx = sourceNode.position.x + sourceDim.width / 2;
		const sy = sourceNode.position.y + sourceDim.height / 2;
		const tx = targetNode.position.x + targetDim.width / 2;
		const ty = targetNode.position.y + targetDim.height / 2;

		// Simple straight line for now, can be enhanced with bezier curves
		return `M ${sx} ${sy} L ${tx} ${ty}`;
	}

	function handleNodeClick(event: MouseEvent, node: any) {
		event.stopPropagation();
		if (!readonly) {
			selectedNodeId = node.id;
		}
		onNodeClick?.(node);
	}

	function handlePaneClick() {
		selectedNodeId = null;
		onPaneClick?.();
	}

	function handleNodeMouseDown(event: MouseEvent, node: any) {
		if (readonly) return;
		event.stopPropagation();
		isDragging = true;
		selectedNodeId = node.id;
		
		const rect = svgElement?.getBoundingClientRect();
		if (rect) {
			dragOffset.x = event.clientX - rect.left - node.position.x;
			dragOffset.y = event.clientY - rect.top - node.position.y;
		}
	}

	function handleMouseMove(event: MouseEvent) {
		if (!isDragging || readonly || !selectedNodeId) return;
		
		const rect = svgElement?.getBoundingClientRect();
		if (!rect) return;
		
		const x = event.clientX - rect.left - dragOffset.x;
		const y = event.clientY - rect.top - dragOffset.y;
		
		localNodes = localNodes.map(n => {
			if (n.id === selectedNodeId) {
				return { ...n, position: { x, y } };
			}
			return n;
		});
		onNodesChange?.(localNodes);
	}

	function handleMouseUp() {
		isDragging = false;
	}

	function handleMouseLeave() {
		isDragging = false;
	}
</script>

<div class="w-full h-full" style="min-height: 400px;" onclick={handlePaneClick} role="presentation">
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<svg 
		class="w-full h-full" 
		style="min-height: 400px; cursor: default;"
		bind:this={svgElement}
		onmousemove={handleMouseMove}
		onmouseup={handleMouseUp}
		onmouseleave={handleMouseLeave}
	>
		<defs>
			<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
				<path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" stroke-width="0.5"/>
			</pattern>
			<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
				<polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af"/>
			</marker>
		</defs>
		<rect width="100%" height="100%" fill="url(#grid)"/>
		
		{#each localEdges as edge}
			{@const pathD = getEdgePath(edge)}
			{#if pathD}
				<path 
					d={pathD} 
					fill="none" 
					stroke="#9ca3af" 
					stroke-width="2"
					marker-end="url(#arrowhead)"
				/>
			{/if}
		{/each}
		
		{#each localNodes as node}
			{@const isSelected = selectedNodeId === node.id}
			{@const shapePath = getNodeShape(node)}
			{@const { width, height } = getNodeDimensions(node)}
			<g 
				class="cursor-pointer"
				onclick={(e) => handleNodeClick(e, node)}
				onmousedown={(e) => handleNodeMouseDown(e, node)}
				onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleNodeClick(e as any, node); }}
				role="button"
				tabindex="0"
				aria-label={node.data?.label || 'Flowchart node'}
			>
				<path 
					d={shapePath}
					fill={node.style?.backgroundColor || '#dbeafe'}
					stroke={isSelected ? '#3b82f6' : (node.style?.borderColor || '#93c5fd')}
					stroke-width={isSelected ? 3 : 2}
				/>
				<text 
					x={node.position.x + width/2} 
					y={node.position.y + height/2} 
					text-anchor="middle" 
					dominant-baseline="middle"
					fill={node.style?.color || '#1f2937'}
					font-size="14"
					font-weight="500"
					style="pointer-events: none;"
				>
					{node.data?.label || ''}
				</text>
			</g>
		{/each}
	</svg>
</div>
