<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as d3 from 'd3';

	interface TreeNode {
		id: string;
		name: string;
		type: 'root' | 'module' | 'feature';
		children?: TreeNode[];
		data?: any;
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

	const nodeWidth = 140;
	const nodeHeight = 60;
	const levelWidth = 180;
	const siblingGap = 20;

	function createHierarchy(data: TreeNode): d3.HierarchyNode<TreeNode> {
		return d3.hierarchy<TreeNode>(data, d => d.children);
	}

	function layoutBilateralTree(root: d3.HierarchyNode<TreeNode>): d3.HierarchyPointNode<TreeNode> {
		const treeLayout = d3.tree<TreeNode>().size([height - 100, width - 400]);
		const treeData = treeLayout(root);
		
		// Separate nodes into left and right groups
		const rootNode = treeData;
		const children = rootNode.children || [];
		const midIndex = Math.ceil(children.length / 2);
		
		// Left group (first half)
		const leftNodes = children.slice(0, midIndex);
		// Right group (second half)
		const rightNodes = children.slice(midIndex);
		
		// Position left nodes on the left side
		leftNodes.forEach((node, i) => {
			node.y = -node.y - 100; // Mirror to left side
			node.x = node.x;
			// Position feature nodes
			if (node.children) {
				node.children.forEach((child, j) => {
					child.y = -child.y - 100;
					child.x = child.x;
				});
			}
		});
		
		// Position right nodes on the right side
		rightNodes.forEach((node, i) => {
			node.y = node.y + 100; // Keep on right side
			node.x = node.x;
			// Position feature nodes
			if (node.children) {
				node.children.forEach((child, j) => {
					child.y = child.y + 100;
					child.x = child.x;
				});
			}
		});
		
		return treeData;
	}

	function render() {
		if (!container) return;

		// Clear previous content
		d3.select(container).selectAll('*').remove();

		// Create SVG
		svg = d3.select(container)
			.append('svg')
			.attr('width', '100%')
			.attr('height', '100%')
			.attr('viewBox', [0, 0, width, height]);

		// Add zoom behavior
		zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 4])
			.on('zoom', (event) => {
				g.attr('transform', event.transform);
			});

		svg.call(zoomBehavior);

		// Create main group - center the root node
		g = svg.append('g')
			.attr('transform', `translate(${width / 2}, ${height / 2})`);

		// Create hierarchy and layout
		const root = createHierarchy(data);
		const treeData = layoutBilateralTree(root);

		// Draw links
		const links = g.selectAll('.link')
			.data(treeData.links())
			.enter()
			.append('path')
			.attr('class', 'link')
			.attr('d', d => {
				const sourceX = d.source.x;
				const sourceY = d.source.y;
				const targetX = d.target.x;
				const targetY = d.target.y;
				
				// Create curved path
				return `M${sourceY},${sourceX} C${sourceY},${(sourceX + targetX) / 2} ${targetY},${(sourceX + targetX) / 2} ${targetY},${targetX}`;
			})
			.attr('fill', 'none')
			.attr('stroke', '#94a3b8')
			.attr('stroke-width', 2);

		// Draw nodes
		const nodes = g.selectAll('.node')
			.data(treeData.descendants())
			.enter()
			.append('g')
			.attr('class', 'node')
			.attr('transform', d => `translate(${d.y},${d.x})`)
			.style('cursor', 'pointer')
			.on('click', (event, d) => {
				onNodeClick?.(d.data);
			});

		// Node rectangles
		nodes.append('rect')
			.attr('width', nodeWidth)
			.attr('height', nodeHeight)
			.attr('x', -nodeWidth / 2)
			.attr('y', -nodeHeight / 2)
			.attr('rx', 8)
			.attr('ry', 8)
			.attr('fill', d => {
				if (d.data.type === 'root') return '#dbeafe';
				if (d.data.type === 'module') return '#dcfce7';
				return '#fef9c3';
			})
			.attr('stroke', d => {
				if (d.data.type === 'root') return '#3b82f6';
				if (d.data.type === 'module') return '#22c55e';
				return '#eab308';
			})
			.attr('stroke-width', 2);

		// Node text
		nodes.append('text')
			.attr('text-anchor', 'middle')
			.attr('dy', '0.35em')
			.text(d => d.data.name)
			.attr('font-size', '12px')
			.attr('font-family', 'system-ui, sans-serif')
			.attr('fill', '#1f2937')
			.each(function(d) {
				const text = d3.select(this);
				const words = d.data.name.split('');
				if (words.length > 10) {
					text.text(d.data.name.substring(0, 10) + '...');
				}
			});

		// Version label
		if (version) {
			svg.append('text')
				.attr('x', width - 20)
				.attr('y', 30)
				.attr('text-anchor', 'end')
				.text(`版本 ${version}`)
				.attr('font-size', '14px')
				.attr('font-weight', 'bold')
				.attr('fill', '#3b82f6');
		}

		// Center the tree
		const bounds = g.node()?.getBBox();
		if (bounds) {
			const scale = 0.8;
			const translateX = (width - bounds.width * scale) / 2 - bounds.x * scale;
			const translateY = (height - bounds.height * scale) / 2 - bounds.y * scale;
			
			svg.call(zoomBehavior.transform, d3.zoomIdentity
				.translate(translateX, translateY)
				.scale(scale)
			);
		}
	}

	$effect(() => {
		if (data && container) {
			render();
		}
	});

	onMount(() => {
		if (data && container) {
			render();
		}
	});

	onDestroy(() => {
		if (svg) {
			svg.selectAll('*').remove();
		}
	});
</script>

<div bind:this={container} style="width: 100%; height: 100%; overflow: hidden;"></div>
