<script lang="ts">
	interface Props {
		nodes: any[];
		edges: any[];
		texts?: any[];
		onNodesChange?: (nodes: any[]) => void;
		onEdgesChange?: (edges: any[]) => void;
		onTextsChange?: (texts: any[]) => void;
		onConnect?: (connection: any) => void;
		onNodeClick?: (node: any) => void;
		onPaneClick?: () => void;
		readonly?: boolean;
		mode?: 'select' | 'pan' | 'connect' | 'add';
	}

	let { 
		nodes = [], 
		edges = [], 
		texts = [],
		onNodesChange, 
		onEdgesChange, 
		onTextsChange,
		onConnect, 
		onNodeClick, 
		onPaneClick,
		readonly = false,
		mode = 'select'
	}: Props = $props();

	let localNodes = $state<any[]>([]);
	let localEdges = $state<any[]>([]);
	let localTexts = $state<any[]>([]);
	let selectedNodeId = $state<string | null>(null);
	let selectedEdgeId = $state<string | null>(null);
	let selectedTextId = $state<string | null>(null);
	let isDragging = $state(false);
	let dragOffset = $state({ x: 0, y: 0 });
	let svgElement = $state<SVGSVGElement | null>(null);
	
	// 连线模式
	let isConnecting = $state(false);
	let connectSourceId = $state<string | null>(null);
	let connectSourcePoint = $state<string>('center');
	let tempEdge = $state<{x1: number, y1: number, x2: number, y2: number} | null>(null);
	
	// 编辑模式
	let editingNodeId = $state<string | null>(null);
	let editingText = $state('');
	let editingInputRef = $state<HTMLInputElement | null>(null);
	
	// 悬停状态
	let hoveredNodeId = $state<string | null>(null);
	let hoveredPoint = $state<string | null>(null);
	let snapTargetNode = $state<any | null>(null);
	let snapTargetPoint = $state<string | null>(null);
	const SNAP_DISTANCE = 50;

	$effect(() => {
		localNodes = nodes ? [...nodes] : [];
	});

	$effect(() => {
		localEdges = edges ? [...edges] : [];
	});
	
	$effect(() => {
		localTexts = texts ? [...texts] : [];
	});

	function getNodeDimensions(node: any) {
		const shape = node.data?.shape || 'rectangle';
		const defaultWidth = shape === 'diamond' ? 100 : shape === 'circle' ? 80 : 140;
		const defaultHeight = shape === 'diamond' ? 100 : shape === 'circle' ? 80 : 60;
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

	// 获取节点的四个连接锚点
	function getNodeConnectionPoints(node: any) {
		const { width, height } = getNodeDimensions(node);
		return {
			top: { x: node.position.x + width / 2, y: node.position.y },
			right: { x: node.position.x + width, y: node.position.y + height / 2 },
			bottom: { x: node.position.x + width / 2, y: node.position.y + height },
			left: { x: node.position.x, y: node.position.y + height / 2 }
		};
	}

	function getEdgePath(edge: any) {
		const sourceNode = localNodes.find(n => n.id === edge.source);
		const targetNode = localNodes.find(n => n.id === edge.target);
		if (!sourceNode || !targetNode) return '';

		const sourcePoints = getNodeConnectionPoints(sourceNode);
		const targetPoints = getNodeConnectionPoints(targetNode);

		// 使用指定的锚点或默认使用中心
		const sourcePoint = edge.sourcePoint || 'bottom';
		const targetPoint = edge.targetPoint || 'top';
		
		const sp = (sourcePoints as any)[sourcePoint] || sourcePoints.bottom;
		const tp = (targetPoints as any)[targetPoint] || targetPoints.top;

		// 根据连线类型生成路径
		const lineType = edge.lineType || 'straight';
		
		switch (lineType) {
			case 'orthogonal':
				return getOrthogonalPath(sp, tp, sourcePoint, targetPoint);
			case 'curved':
				return getCurvedPath(sp, tp);
			default:
				return `M ${sp.x} ${sp.y} L ${tp.x} ${tp.y}`;
		}
	}

	function getOrthogonalPath(sp: any, tp: any, sourcePoint: string, targetPoint: string) {
		// 简化的正交路径：先水平再垂直，或先垂直再水平
		const midX = (sp.x + tp.x) / 2;
		return `M ${sp.x} ${sp.y} L ${midX} ${sp.y} L ${midX} ${tp.y} L ${tp.x} ${tp.y}`;
	}

	function getCurvedPath(sp: any, tp: any) {
		const midX = (sp.x + tp.x) / 2;
		const midY = (sp.y + tp.y) / 2;
		return `M ${sp.x} ${sp.y} Q ${midX} ${sp.y} ${midX} ${midY} T ${tp.x} ${tp.y}`;
	}

	function getNodeCenter(node: any) {
		const { width, height } = getNodeDimensions(node);
		return {
			x: node.position.x + width / 2,
			y: node.position.y + height / 2
		};
	}

	function handleNodeClick(event: MouseEvent, node: any) {
		event.stopPropagation();
		
		if (mode === 'connect' || isConnecting) {
			// 连线模式：点击目标节点完成连线
			if (connectSourceId && connectSourceId !== node.id) {
				// 如果有吸附目标，使用吸附的锚点
				let targetPoint = hoveredPoint || 'top';
				if (snapTargetNode && snapTargetPoint) {
					targetPoint = snapTargetPoint;
				}
				
				const newEdge = {
					id: `edge-${connectSourceId}-${node.id}-${Date.now()}`,
					source: connectSourceId,
					target: node.id,
					sourcePoint: connectSourcePoint,
					targetPoint: targetPoint,
					label: '',
					lineType: 'straight',
					arrowEnd: true
				};
				localEdges = [...localEdges, newEdge];
				onEdgesChange?.(localEdges);
			}
			isConnecting = false;
			connectSourceId = null;
			connectSourcePoint = 'center';
			tempEdge = null;
			snapTargetNode = null;
			snapTargetPoint = null;
			return;
		}
		
		if (!readonly) {
			selectedNodeId = node.id;
			selectedEdgeId = null;
			selectedTextId = null;
		}
		onNodeClick?.(node);
	}

	function handleEdgeClick(event: MouseEvent, edge: any) {
		event.stopPropagation();
		if (!readonly) {
			selectedEdgeId = edge.id;
			selectedNodeId = null;
			selectedTextId = null;
		}
	}

	function handlePaneClick() {
		if (isConnecting) {
			isConnecting = false;
			connectSourceId = null;
			connectSourcePoint = 'center';
			tempEdge = null;
			snapTargetNode = null;
			snapTargetPoint = null;
			return;
		}
		selectedNodeId = null;
		selectedEdgeId = null;
		selectedTextId = null;
		onPaneClick?.();
	}

	function handleNodeMouseDown(event: MouseEvent, node: any) {
		if (readonly || mode === 'connect') return;
		event.stopPropagation();
		isDragging = true;
		selectedNodeId = node.id;
		selectedEdgeId = null;
		selectedTextId = null;
		
		const rect = svgElement?.getBoundingClientRect();
		if (rect) {
			dragOffset.x = event.clientX - rect.left - node.position.x;
			dragOffset.y = event.clientY - rect.top - node.position.y;
		}
	}

	function handleMouseMove(event: MouseEvent) {
		if (isConnecting && connectSourceId) {
			const rect = svgElement?.getBoundingClientRect();
			if (!rect) return;
			
			const mouseX = event.clientX - rect.left;
			const mouseY = event.clientY - rect.top;
			
			// 查找最近的节点和锚点
			let closestNode: any = null;
			let closestPoint: string | null = null;
			let closestDistance = Infinity;
			
			for (const node of localNodes) {
				if (node.id === connectSourceId) continue; // 跳过源节点
				
				const points = getNodeConnectionPoints(node);
				for (const [pointName, pos] of Object.entries(points)) {
					const dx = pos.x - mouseX;
					const dy = pos.y - mouseY;
					const distance = Math.sqrt(dx * dx + dy * dy);
					
					if (distance < closestDistance && distance <= SNAP_DISTANCE) {
						closestDistance = distance;
						closestNode = node;
						closestPoint = pointName;
					}
				}
			}
			
			// 更新吸附目标
			if (closestNode && closestPoint) {
				snapTargetNode = closestNode;
				snapTargetPoint = closestPoint;
			} else {
				snapTargetNode = null;
				snapTargetPoint = null;
			}
			
			const sourceNode = localNodes.find(n => n.id === connectSourceId);
			if (sourceNode) {
				const points = getNodeConnectionPoints(sourceNode);
				const sp = (points as any)[connectSourcePoint] || points.bottom;
				
				// 如果有吸附目标，使用吸附点的坐标
				let targetX = mouseX;
				let targetY = mouseY;
				
				if (snapTargetNode && snapTargetPoint) {
					const targetPoints = getNodeConnectionPoints(snapTargetNode);
					const tp = (targetPoints as any)[snapTargetPoint];
					if (tp) {
						targetX = tp.x;
						targetY = tp.y;
					}
				}
				
				tempEdge = {
					x1: sp.x,
					y1: sp.y,
					x2: targetX,
					y2: targetY
				};
			}
			return;
		}
		
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

	// 双击编辑节点文本
	function handleNodeDoubleClick(event: MouseEvent, node: any) {
		event.stopPropagation();
		if (readonly) return;
		editingNodeId = node.id;
		editingText = node.data?.label || '';
		selectedNodeId = node.id;
		
		setTimeout(() => {
			editingInputRef?.focus();
			editingInputRef?.select();
		}, 0);
	}

	// 保存编辑
	function saveNodeEdit() {
		if (!editingNodeId) return;
		
		localNodes = localNodes.map(n => {
			if (n.id === editingNodeId) {
				return {
					...n,
					data: {
						...n.data,
						label: editingText
					}
				};
			}
			return n;
		});
		
		onNodesChange?.(localNodes);
		editingNodeId = null;
		editingText = '';
	}

	// 取消编辑
	function cancelNodeEdit() {
		editingNodeId = null;
		editingText = '';
	}

	// 键盘事件
	function handleKeyDown(event: KeyboardEvent) {
		if (editingNodeId) {
			if (event.key === 'Enter') {
				event.preventDefault();
				saveNodeEdit();
			} else if (event.key === 'Escape') {
				event.preventDefault();
				cancelNodeEdit();
			}
			return;
		}
		
		if ((event.key === 'Delete' || event.key === 'Backspace') && !readonly) {
			if (selectedNodeId) {
				event.preventDefault();
				localNodes = localNodes.filter(n => n.id !== selectedNodeId);
				localEdges = localEdges.filter(e => e.source !== selectedNodeId && e.target !== selectedNodeId);
				selectedNodeId = null;
				onNodesChange?.(localNodes);
				onEdgesChange?.(localEdges);
			} else if (selectedEdgeId) {
				event.preventDefault();
				localEdges = localEdges.filter(e => e.id !== selectedEdgeId);
				selectedEdgeId = null;
				onEdgesChange?.(localEdges);
			}
		}
	}

	// 开始连线
	export function startConnection(nodeId: string, point: string = 'center') {
		isConnecting = true;
		connectSourceId = nodeId;
		connectSourcePoint = point;
		selectedNodeId = nodeId;
	}

	// 获取选中节点
	export function getSelectedNode() {
		return localNodes.find(n => n.id === selectedNodeId);
	}

	// 更新节点样式
	export function updateNodeStyle(nodeId: string, style: any) {
		localNodes = localNodes.map(n => {
			if (n.id === nodeId) {
				return {
					...n,
					data: {
						...n.data,
						...style
					}
				};
			}
			return n;
		});
		onNodesChange?.(localNodes);
	}
	
	// 获取连线样式
	function getEdgeStrokeDash(edge: any) {
		const style = edge.style || {};
		if (style.strokeDasharray) return style.strokeDasharray;
		if (edge.lineType === 'dashed') return '5,5';
		if (edge.lineType === 'dotted') return '2,2';
		return 'none';
	}
	
	// 获取箭头标记
	function getArrowMarker(edge: any, isSelected: boolean) {
		// 默认显示箭头，除非明确设置 arrowEnd: false
		if (edge.arrowEnd === false || (edge.style && edge.style.arrowEnd === false)) {
			return '';
		}
		return isSelected ? 'url(#arrowhead-selected)' : 'url(#arrowhead)';
	}
</script>

<svelte:window onkeydown={handleKeyDown} />

<div class="w-full h-full relative" style="min-height: 400px;" onclick={handlePaneClick} role="presentation">
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<svg 
		class="w-full h-full" 
		style="min-height: 400px; cursor: {isConnecting ? 'crosshair' : mode === 'pan' ? 'grab' : 'default'};"
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
			<marker id="arrowhead-selected" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
				<polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6"/>
			</marker>
		</defs>
		<rect width="100%" height="100%" fill="url(#grid)"/>
		
		<!-- 连线 -->
		{#each localEdges as edge}
			{@const pathD = getEdgePath(edge)}
			{@const isSelected = selectedEdgeId === edge.id}
			{#if pathD}
				<path 
					d={pathD} 
					fill="none" 
					stroke={isSelected ? '#3b82f6' : '#9ca3af'} 
					stroke-width={isSelected ? 3 : 2}
					stroke-dasharray={getEdgeStrokeDash(edge)}
					marker-end={getArrowMarker(edge, isSelected)}
					class="cursor-pointer"
					onclick={(e) => handleEdgeClick(e, edge)}
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleEdgeClick(e as any, edge); }}
					tabindex="0"
					role="button"
					aria-label="连线"
				/>
				<!-- 连线文本 -->
				{#if edge.label}
					{@const midX = (edge.sourceX + edge.targetX) / 2}
					{@const midY = (edge.sourceY + edge.targetY) / 2}
					<text 
						x={midX} 
						y={midY - 5} 
						text-anchor="middle" 
						fill="#666"
						font-size="12"
						style="pointer-events: none;"
					>
						{edge.label}
					</text>
				{/if}
			{/if}
		{/each}
		
		<!-- 临时连线（连线模式） -->
		{#if tempEdge}
			<line 
				x1={tempEdge.x1} 
				y1={tempEdge.y1} 
				x2={tempEdge.x2} 
				y2={tempEdge.y2}
				stroke="#3b82f6" 
				stroke-width="2" 
				stroke-dasharray="5,5"
				marker-end="url(#arrowhead-selected)"
			/>
		{/if}
		
		<!-- 节点 -->
		{#each localNodes as node}
			{@const isSelected = selectedNodeId === node.id}
			{@const shapePath = getNodeShape(node)}
			{@const { width, height } = getNodeDimensions(node)}
			{@const isEditing = editingNodeId === node.id}
			{@const connectionPoints = getNodeConnectionPoints(node)}
			{@const isSnapTarget = snapTargetNode?.id === node.id}
			<g 
				class="cursor-pointer"
				onclick={(e) => handleNodeClick(e, node)}
				onmousedown={(e) => handleNodeMouseDown(e, node)}
				ondblclick={(e) => handleNodeDoubleClick(e, node)}
				onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleNodeClick(e as any, node); }}
				role="button"
				tabindex="0"
				aria-label={node.data?.label || 'Flowchart node'}
				onmouseenter={() => hoveredNodeId = node.id}
				onmouseleave={() => hoveredNodeId = null}
			>
				<path 
					d={shapePath}
					fill={node.style?.backgroundColor || '#dbeafe'}
					stroke={isSelected ? '#3b82f6' : isSnapTarget ? '#10b981' : (node.style?.borderColor || '#93c5fd')}
					stroke-width={isSelected ? 3 : isSnapTarget ? 4 : 2}
					style="filter: {isSelected ? 'drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3))' : isSnapTarget ? 'drop-shadow(0 2px 4px rgba(16, 185, 129, 0.4))' : 'none'};"
				/>
				
				{#if !isEditing}
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
					{node.data?.label || '节点'}
				</text>
				<!-- Traceability binding badge -->
				{#if node.data?.traceability?.entityId}
					{@const tr = node.data.traceability}
					{@const badgeText = tr.entityName || tr.entityType || '已绑定'}
					{@const badgeWidth = Math.max(40, badgeText.length * 7 + 16)}
					<g style="pointer-events: none;">
						<rect
							x={node.position.x + width - badgeWidth - 4}
							y={node.position.y - 10}
							width={badgeWidth}
							height="14"
							rx="7"
							fill="#10b981"
							stroke="#fff"
							stroke-width="1.5"
						/>
						<circle
							cx={node.position.x + width - badgeWidth - 4 + 7}
							cy={node.position.y - 3}
							r="2.5"
							fill="#fff"
						/>
						<text
							x={node.position.x + width - badgeWidth - 4 + 13}
							y={node.position.y - 3}
							text-anchor="start"
							dominant-baseline="middle"
							fill="#fff"
							font-size="9"
							font-weight="600"
						>
							{badgeText}
						</text>
					</g>
				{/if}
			{:else}
					<foreignObject 
						x={node.position.x} 
						y={node.position.y + height/2 - 12} 
						width={width} 
						height="24"
					>
						<input
							bind:this={editingInputRef}
							type="text"
							value={editingText}
							oninput={(e) => editingText = e.currentTarget.value}
							onblur={saveNodeEdit}
							onkeydown={(e) => {
								if (e.key === 'Enter') {
									e.preventDefault();
									saveNodeEdit();
								} else if (e.key === 'Escape') {
									e.preventDefault();
									cancelNodeEdit();
								}
							}}
							class="w-full text-center text-sm bg-white border border-blue-400 rounded px-1 outline-none"
							style="color: {node.style?.color || '#1f2937'};"
						/>
					</foreignObject>
				{/if}
				
				<!-- 连接锚点（仅在选中、悬停且非只读时显示） -->
				{#if (isSelected || hoveredNodeId === node.id) && !readonly && !isConnecting}
					{#each Object.entries(connectionPoints) as [pointKey, pos]}
						{@const pointName = pointKey}
						{@const isHovered = hoveredPoint === pointName}
						<circle 
							cx={pos.x} 
							cy={pos.y} 
							r="5" 
							fill={isHovered ? '#3b82f6' : '#fff'}
							stroke="#3b82f6" 
							stroke-width="2"
							class="cursor-crosshair transition-all"
							onclick={(e) => {
								e.stopPropagation();
								startConnection(node.id, pointName);
							}}
							onmouseenter={() => hoveredPoint = pointName}
							onmouseleave={() => hoveredPoint = null}
						/>
					{/each}
				{/if}
			</g>
		{/each}
		
		<!-- 独立文本框 -->
		{#each localTexts as textItem}
			{@const isTextSelected = selectedTextId === textItem.id}
			<g 
				class="cursor-pointer"
				onclick={(e) => {
					e.stopPropagation();
					selectedTextId = textItem.id;
					selectedNodeId = null;
					selectedEdgeId = null;
				}}
			>
				<text 
					x={textItem.position.x} 
					y={textItem.position.y} 
					text-anchor={textItem.style?.textAlign || 'left'}
					fill={textItem.style?.color || '#1f2937'}
					font-size={textItem.style?.fontSize || '14'}
					font-family={textItem.style?.fontFamily || 'inherit'}
					font-weight={isTextSelected ? 'bold' : 'normal'}
					style="pointer-events: none;"
				>
					{textItem.text}
				</text>
			</g>
		{/each}
	</svg>
	
	<!-- 状态提示 -->
	{#if isConnecting}
		<div class="absolute top-2 left-1/2 -translate-x-1/2 bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
			连线模式：点击目标节点锚点完成连线，点击空白处取消
		</div>
	{/if}
</div>

<style>
	text {
		user-select: none;
	}
	
	input {
		font-family: inherit;
	}
	
	circle {
		transition: all 0.2s ease;
	}
	
	circle:hover {
		r: 7;
	}
</style>
