<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as d3 from 'd3';
	import { interpolatePath as d3InterpolatePath } from 'd3-interpolate-path';

	interface TreeNode {
		id: string;
		name: string;
		type: 'root' | 'module' | 'feature';
		children?: TreeNode[];
		data?: { source?: 'auto' | 'manual'; paramCount?: number; description?: string; featureCount?: number };
	}

	interface TooltipContent {
		name: string;
		type: string;
		source?: 'auto' | 'manual';
		paramCount?: number;
		description?: string;
	}

	interface Props {
		data: TreeNode;
		width?: number;
		height?: number;
		onNodeClick?: (node: TreeNode) => void;
		version?: string;
	}

	let { data, width = 1200, height = 800, onNodeClick, version }: Props = $props();

	let container: HTMLDivElement;
	let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
	let g: d3.Selection<SVGGElement, unknown, null, undefined>;
	let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown>;
	let initialized = false;
	let ro: ResizeObserver;

	// Interaction state
	let selectedNodeId: string | null = $state(null);
	let tooltipVisible = $state(false);
	let tooltipX = $state(0);
	let tooltipY = $state(0);
	let tooltipContent: TooltipContent | null = $state(null);

	// Container dimensions (react to resize)
	let containerWidth = $state(width);
	let containerHeight = $state(height);
	let isDark = $state(false);

	const nodeWidth = 140;
	const nodeHeight = 60;

	function createHierarchy(data: TreeNode): d3.HierarchyNode<TreeNode> {
		return d3.hierarchy<TreeNode>(data, d => d.children);
	}

	function layoutBilateralTree(root: d3.HierarchyNode<TreeNode>): d3.HierarchyPointNode<TreeNode> {
		const halfRange = Math.max(containerWidth / 2 - 200, 100);
		const treeLayout = d3.tree<TreeNode>().size([containerHeight - 100, halfRange]);
		const treeData = treeLayout(root);

		const children = treeData.children || [];
		const sorted = [...children].sort((a, b) => a.y - b.y);
		const margin = 60;

		sorted.forEach((node, i) => {
			const isLeft = i % 2 === 0;
			const offset = node.y + margin;
			node.y = isLeft ? -offset : offset;
			if (node.children) {
				node.children.forEach(child => {
					child.y = isLeft ? -(child.y + margin) : child.y + margin;
				});
			}
		});

		treeData.y = 0;
		return treeData;
	}

	function truncateText(text: string, maxWidth: number): string {
		let totalWidth = 0;
		for (const ch of text) {
			totalWidth += ch.charCodeAt(0) > 0x7f ? 7.2 : 6;
		}
		if (totalWidth <= maxWidth) return text;

		let truncated = '';
		let w = 0;
		for (const ch of text) {
			const cw = ch.charCodeAt(0) > 0x7f ? 7.2 : 6;
			if (w + cw > maxWidth - 12) break;
			truncated += ch;
			w += cw;
		}
		return truncated + '...';
	}

	function getNodeColors(type: string, isDarkMode: boolean, isSelected: boolean) {
		const colors = {
			root: { fill: isDarkMode ? '#1e3a5f' : '#dbeafe', stroke: isSelected ? '#1d4ed8' : '#3b82f6' },
			module: { fill: isDarkMode ? '#14532d' : '#dcfce7', stroke: isSelected ? '#15803d' : '#22c55e' },
			feature: { fill: isDarkMode ? '#422006' : '#fef9c3', stroke: isSelected ? '#a16207' : '#eab308' },
		};
		return colors[type as keyof typeof colors] || colors.feature;
	}

	function getSourceDotColor(source: 'auto' | 'manual' | undefined): string {
		if (source === 'auto') return '#3b82f6';
		if (source === 'manual') return '#22c55e';
		return '#94a3b8';
	}

	function updateTooltipPosition(event: MouseEvent) {
		if (!container) return;
		const rect = container.getBoundingClientRect();
		let x = event.clientX - rect.left + 12;
		let y = event.clientY - rect.top - 10;
		const tw = 220, th = 120;
		if (x + tw > containerWidth) x = event.clientX - rect.left - tw - 12;
		if (y + th > containerHeight) y = containerHeight - th - 10;
		if (y < 5) y = 5;
		tooltipX = x;
		tooltipY = y;
	}

	// ---- Render pipeline ----

	function initSVG() {
		if (!container || initialized) return;

		isDark = document.documentElement.classList.contains('dark');
		const mo = new MutationObserver(() => {
			isDark = document.documentElement.classList.contains('dark');
		});
		mo.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

		svg = d3.select(container)
			.append('svg')
			.attr('width', '100%')
			.attr('height', '100%')
			.attr('viewBox', [0, 0, containerWidth, containerHeight]);

		const defs = svg.append('defs');
		defs.append('filter')
			.attr('id', 'selected-glow')
			.append('feDropShadow')
			.attr('dx', 0).attr('dy', 0)
			.attr('stdDeviation', 4)
			.attr('flood-color', '#3b82f6')
			.attr('flood-opacity', 0.5);

		zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 4])
			.on('zoom', (event) => { g?.attr('transform', event.transform); });

		svg.call(zoomBehavior);

		// Background click → deselect
		svg.on('click', (event: MouseEvent) => {
			if ((event.target as Element).tagName === 'svg') {
				selectedNodeId = null;
				updateSelectedStyles();
			}
		});

		g = svg.append('g');

		initialized = true;
	}

	function update() {
		if (!container || !g) return;

		// Recompute layout (reads containerWidth/containerHeight reactively)
		const root = createHierarchy(data);
		const treeData = layoutBilateralTree(root);
		const duration = 400;

		// -- Links (data join) --
		const linkData = treeData.links();
		const links = g.selectAll<SVGPathElement, d3.HierarchyPointLink<TreeNode>>('.link')
			.data(linkData, d => `${d.source.data.id}→${d.target.data.id}`);

		links.exit()
			.transition().duration(duration / 2).attr('opacity', 0).remove();

		const linkEnter = links.enter()
			.append('path')
			.attr('class', 'link')
			.attr('fill', 'none')
			.attr('stroke', isDark ? '#475569' : '#94a3b8')
			.attr('stroke-width', 2)
			.attr('opacity', 0);

		linkEnter.merge(links)
			.transition().duration(duration).attr('opacity', 1)
			.attrTween('d', function(d) {
				const self = this as SVGPathElement;
				const current = self.getAttribute('d') || '';
				const target = linkPath(d);
				return d3InterpolatePath(current, target);
			});

		// -- Nodes (data join) --
		const nodeData = treeData.descendants();
		const nodes = g.selectAll<SVGGElement, d3.HierarchyPointNode<TreeNode>>('.node')
			.data(nodeData, d => d.data.id);

		nodes.exit()
			.transition().duration(duration / 2).attr('opacity', 0)
			.remove();

		const nodeEnter = nodes.enter()
			.append('g')
			.attr('class', 'node')
			.attr('opacity', 0)
			.style('cursor', 'pointer');

		nodeEnter.append('rect')
			.attr('width', nodeWidth)
			.attr('height', nodeHeight)
			.attr('x', -nodeWidth / 2)
			.attr('y', -nodeHeight / 2)
			.attr('rx', 8).attr('ry', 8);

		nodeEnter.append('text')
			.attr('class', 'node-text')
			.attr('text-anchor', 'middle')
			.attr('dy', '0.35em')
			.attr('font-size', '12px')
			.attr('font-family', 'system-ui, sans-serif')
			.attr('fill', isDark ? '#e5e7eb' : '#1f2937');

		nodeEnter.append('circle')
			.attr('class', 'source-dot')
			.attr('r', 5)
			.attr('cx', nodeWidth / 2 - 8)
			.attr('cy', -nodeHeight / 2 + 8);

		// Merge enter + existing
		const nodeMerge = nodeEnter.merge(nodes).sort((a, b) => {
			const depthOrder = (n: typeof a) => n.data.type === 'root' ? 0 : n.data.type === 'module' ? 1 : 2;
			return depthOrder(a) - depthOrder(b);
		});

		// Position with transition
		nodeMerge.transition().duration(duration)
			.attr('opacity', 1)
			.attr('transform', d => `translate(${d.y},${d.x})`);

		// Update rect
		nodeMerge.select('rect')
			.attr('fill', d => getNodeColors(d.data.type, isDark, false).fill)
			.attr('stroke', d => d.data.id === selectedNodeId
				? getNodeColors(d.data.type, isDark, true).stroke
				: getNodeColors(d.data.type, isDark, false).stroke)
			.attr('stroke-width', d => d.data.id === selectedNodeId ? 3 : 2)
			.attr('filter', d => d.data.id === selectedNodeId ? 'url(#selected-glow)' : null);

		// Update text
		nodeMerge.select('text')
			.text(d => truncateText(d.data.name, nodeWidth - 20));

		// Update source dot
		nodeMerge.select('.source-dot')
			.attr('display', d => d.data.type === 'root' || !d.data?.data?.source ? 'none' : null)
			.attr('fill', d => getSourceDotColor(d.data?.data?.source));

		// Bind events (required after data join since enter creates new elements)
		nodeMerge
			.on('click', (event: MouseEvent, d) => {
				event.stopPropagation();
				selectedNodeId = selectedNodeId === d.data.id ? null : d.data.id;
				updateSelectedStyles();
				onNodeClick?.(d.data);
			})
			.on('mouseenter', (event: MouseEvent, d) => {
				if (d.data.type === 'root') return;
				const content = d.data.data;
				tooltipContent = {
					name: d.data.name,
					type: d.data.type === 'module' ? '模块' : '功能',
					source: content?.source,
					paramCount: content?.paramCount,
					description: content?.description,
				};
				tooltipVisible = true;
				updateTooltipPosition(event);
			})
			.on('mousemove', (event: MouseEvent) => {
				if (tooltipVisible) updateTooltipPosition(event);
			})
			.on('mouseleave', () => {
				tooltipVisible = false;
				tooltipContent = null;
			});

		// Version label
		g.selectAll('.version-label').remove();
		if (version) {
			g.append('text')
				.attr('class', 'version-label')
				.attr('x', containerWidth / 2 - 20)
				.attr('y', -(containerHeight / 2) + 30)
				.attr('text-anchor', 'end')
				.text(`版本 ${version}`)
				.attr('font-size', '14px')
				.attr('font-weight', 'bold')
				.attr('fill', '#3b82f6');
		}
	}

	function linkPath(d: d3.HierarchyPointLink<TreeNode>): string {
		return `M${d.source.y},${d.source.x} C${d.source.y},${(d.source.x + d.target.x) / 2} ${d.target.y},${(d.source.x + d.target.x) / 2} ${d.target.y},${d.target.x}`;
	}

	function updateSelectedStyles() {
		if (!g) return;
		g.selectAll<SVGGElement, d3.HierarchyPointNode<TreeNode>>('.node')
			.select('rect')
			.attr('stroke', d => d.data.id === selectedNodeId
				? getNodeColors(d.data.type, isDark, true).stroke
				: getNodeColors(d.data.type, isDark, false).stroke)
			.attr('stroke-width', d => d.data.id === selectedNodeId ? 3 : 2)
			.attr('filter', d => d.data.id === selectedNodeId ? 'url(#selected-glow)' : null);
	}

	function centerTree() {
		if (!g.node() || !svg) return;
		const bounds = (g.node() as SVGGElement).getBBox();
		if (bounds.width > 0 && bounds.height > 0) {
			const scale = 0.8;
			const tx = (containerWidth - bounds.width * scale) / 2 - bounds.x * scale;
			const ty = (containerHeight - bounds.height * scale) / 2 - bounds.y * scale;
			svg.call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
		}
	}

	function render() {
		if (!container) return;
		if (!initialized) {
			initSVG();
			update();
			// Use rAF to ensure SVG is rendered before measuring bounds
			requestAnimationFrame(() => centerTree());
		} else {
			update();
		}
	}

	// Lifecycle
	onMount(() => {
		if (!container) return;
		ro = new ResizeObserver(entries => {
			const entry = entries[0];
			const w = entry.contentRect.width;
			const h = entry.contentRect.height;
			if (w > 0 && h > 0 && (w !== containerWidth || h !== containerHeight)) {
				containerWidth = w;
				containerHeight = h;
			}
		});
		ro.observe(container);
		if (data) render();
	});

	// Reactive re-render on data or size change
	$effect(() => {
		if (data && container && initialized) {
			const _w = containerWidth;
			const _h = containerHeight;
			void (_w + _h);
			svg?.attr('viewBox', [0, 0, containerWidth, containerHeight]);
			update();
		}
	});

	onDestroy(() => {
		if (ro) ro.disconnect();
		if (svg) {
			svg.selectAll('*').remove();
			svg.remove();
		}
		initialized = false;
	});
</script>

<div bind:this={container} class="relative w-full h-full overflow-hidden">
	{#if tooltipVisible && tooltipContent}
		<div
			class="absolute z-50 pointer-events-none px-3 py-2 rounded-lg shadow-lg bg-gray-900/90 text-white text-xs max-w-[220px]"
			style="left: {tooltipX}px; top: {tooltipY}px;"
		>
			<div class="font-semibold text-sm mb-1">{tooltipContent.name}</div>
			<div class="flex items-center gap-2 mb-0.5">
				<span
					class="px-1.5 py-0.5 rounded text-[10px] font-medium {tooltipContent.type === '模块' ? 'bg-blue-500/30' : 'bg-yellow-500/30'}"
				>
					{tooltipContent.type}
				</span>
				{#if tooltipContent.source}
					<span class="flex items-center gap-1">
						<span
							class="inline-block w-2 h-2 rounded-full {tooltipContent.source === 'auto' ? 'bg-blue-400' : 'bg-green-400'}"
						></span>
						<span>{tooltipContent.source === 'auto' ? '自动' : '手动'}</span>
					</span>
				{/if}
			</div>
			{#if tooltipContent.paramCount !== undefined}
				<div class="text-gray-300">参数: {tooltipContent.paramCount} 个</div>
			{/if}
			{#if tooltipContent.description}
				<div class="text-gray-300 mt-0.5 line-clamp-3">{tooltipContent.description}</div>
			{/if}
		</div>
	{/if}
</div>
