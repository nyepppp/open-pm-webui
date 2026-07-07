<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as echarts from 'echarts';
	import type { ArchModule } from '$lib/stores/pm/architectureStore';

	interface Props {
		modules: ArchModule[];
		onNodeClick?: (moduleId: string, featureId?: string) => void;
	}

	let { modules, onNodeClick }: Props = $props();

	let chartContainer: HTMLDivElement;
	let chart: echarts.ECharts | null = null;

	function convertToTreeData(modules: ArchModule[]): any[] {
		return modules.map(mod => ({
			name: mod.name,
			value: mod.id,
			itemStyle: {
				color: '#3b82f6',
				borderColor: '#2563eb',
				borderWidth: 2
			},
			label: {
				fontSize: 14,
				fontWeight: 'bold',
				color: '#1f2937'
			},
			children: mod.features.map(feat => ({
				name: feat.name,
				value: feat.id,
				moduleId: mod.id,
				itemStyle: {
					color: '#10b981',
					borderColor: '#059669',
					borderWidth: 1
				},
				label: {
					fontSize: 12,
					color: '#374151'
				},
				children: feat.parameters.length > 0 ? feat.parameters.map(param => ({
					name: param.name,
					value: param.id,
					featureId: feat.id,
					itemStyle: {
						color: '#f59e0b',
						borderColor: '#d97706',
						borderWidth: 1
					},
					label: {
						fontSize: 11,
						color: '#6b7280'
					}
				})) : undefined
			}))
		}));
	}

	function initChart() {
		if (!chartContainer) return;

		chart = echarts.init(chartContainer);
		updateChart();

		chart.on('click', (params: any) => {
			if (params?.data?.value && onNodeClick) {
				const moduleId = params.data.moduleId || params.data.value;
				const featureId = params.data.featureId;
				onNodeClick(moduleId, featureId);
			}
		});

		const handleResize = () => {
			chart?.resize();
		};
		window.addEventListener('resize', handleResize);

		return () => {
			window.removeEventListener('resize', handleResize);
		};
	}

	function updateChart() {
		if (!chart) return;

		const treeData = convertToTreeData(modules);

		const option = {
			tooltip: {
				trigger: 'item',
				triggerOn: 'mousemove',
				formatter: (params: any) => {
					const data = params.data;
					if (data.children) {
						return `<div style="font-weight: bold;">${data.name}</div><div style="color: #6b7280;">包含 ${data.children.length} 个子项</div>`;
					}
					return data.name;
				}
			},
			series: [
				{
					type: 'tree',
					data: treeData,
					top: '5%',
					left: '5%',
					bottom: '5%',
					right: '5%',
					symbolSize: 14,
					orient: 'LR',
					expandAndCollapse: true,
					initialTreeDepth: 2,
					label: {
						position: 'right',
						verticalAlign: 'middle',
						align: 'left',
						fontSize: 12
					},
					leaves: {
						label: {
							position: 'right',
							verticalAlign: 'middle',
							align: 'left'
						}
					},
					emphasis: {
						focus: 'descendant'
					},
					lineStyle: {
						color: '#d1d5db',
						width: 1.5,
						curveness: 0.5
					}
				}
			]
		};

		chart.setOption(option);
	}

	$effect(() => {
		if (modules && chart) {
			updateChart();
		}
	});

	onMount(() => {
		const cleanup = initChart();
		return () => {
			cleanup?.();
			chart?.dispose();
			chart = null;
		};
	});

	onDestroy(() => {
		chart?.dispose();
		chart = null;
	});
</script>

<div class="w-full h-full" bind:this={chartContainer}></div>
