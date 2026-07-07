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

	$effect(() => {
		localNodes = nodes ? [...nodes] : [];
	});

	$effect(() => {
		localEdges = edges ? [...edges] : [];
	});

	function getNodeShape(node: any) {
		const shape = node.data?.shape || 'rectangle';
		const width = node.style?.width ? parseInt(node.style.width) : 140;
		const height = node.style?.height ? parseInt(node.style.height) : 60;
		
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

		const sourceWidth = sourceNode.style?.width ? parseInt(sourceNode.style.width) : 140;
		const sourceHeight = sourceNode.style?.height ? parseInt(sourceNode.style.height) : 60;
		const targetWidth = targetNode.style?.width ? parseInt(targetNode.style.width) : 140;
		const targetHeight = targetNode.style?.height ? parseInt(targetNode.style.height) : 60;

		const sx = sourceNode.position.x + sourceWidth / 2;
		const sy = sourceNode.position.y + sourceHeight / 2;
		const tx = targetNode.position.x + targetWidth / 2;
		const ty = targetNode.position.y + targetHeight / 2;

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
		const rect = (event.target as Element).closest('svg')?.getBoundingClientRect();
		if (rect) {
			dragOffset.x = event.clientX - rect.left - node.position.x;
			dragOffset.y = event.clientY - rect.top - node.position.y;
		}
	}

	function handleMouseMove(event: MouseEvent) {
		if (!isDragging || readonly || !selectedNodeId) return;
		
		const svg = (event.target as Element).closest('svg');
		if (!svg) return;
		const rect = svg.getBoundingClientRect();
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
</script>

<div class="w-full h-full" style="min-height: 400px;" onclick={handlePaneClick} role="presentation">
	<svg 
		class="w-full h-full" 
		style="min-height: 400px; cursor: default;"
		onmousemove={handleMouseMove}
		onmouseup={handleMouseUp}
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
			{@const width = node.style?.width ? parseInt(node.style.width) : 140}
			{@const height = node.style?.height ? parseInt(node.style.height) : 60}
			<g 
				class="cursor-pointer"
				onclick={(e) => handleNodeClick(e, node)}
				onmousedown={(e) => handleNodeMouseDown(e, node)}
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
