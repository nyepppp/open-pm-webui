<script lang="ts">
	import { goto } from '$app/navigation';

	interface Traceability {
		entityType: string;
		entityId: string;
		entityName: string;
		versionId?: string;
		versionNumber?: string;
		boundAt: number;
		boundBy?: string;
	}

	interface Props {
		nodeId: string;
		nodeData: {
			label: string;
			description?: string;
			inputParams?: string[];
			outputParams?: string[];
			traceability?: Traceability;
		};
		projectId: string;
		onClose: () => void;
		onViewConfig?: () => void;
		onBindTraceability?: (traceability: Traceability) => void;
	}

	let { nodeId, nodeData, projectId, onClose, onViewConfig, onBindTraceability }: Props = $props();

	const entityTypeLabels: Record<string, string> = {
		prd: 'PRD',
		module: '模块',
		feature: '功能',
		parameter: '参数',
		none: '未绑定'
	};

	const entityTypeColors: Record<string, string> = {
		prd: 'bg-purple-100 text-purple-700',
		module: 'bg-blue-100 text-blue-700',
		feature: 'bg-green-100 text-green-700',
		parameter: 'bg-yellow-100 text-yellow-700',
		none: 'bg-gray-100 text-gray-700'
	};

	function handleNavigateToEntity() {
		if (!nodeData.traceability) return;
		const moduleType = nodeData.traceability.entityType === 'module' ? 'architecture' : nodeData.traceability.entityType;
		goto(`/pm/${projectId}/${moduleType}?entryId=${nodeData.traceability.entityId}`);
	}

	function formatDate(timestamp: number): string {
		return new Date(timestamp).toLocaleString('zh-CN');
	}
</script>

<div class="absolute right-0 top-0 h-full w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-y-auto z-20 shadow-lg">
	<div class="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">节点详情</h3>
		<div class="flex items-center gap-2">
			{#if onViewConfig}
				<button 
					class="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
					onclick={onViewConfig}
				>
					查看配置
				</button>
			{/if}
			<button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" onclick={onClose}>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>
		</div>
	</div>

	<div class="p-3 space-y-4">
		<!-- Node Info -->
		<div class="space-y-2">
			<div class="flex items-center gap-2">
				<span class="text-xs font-medium text-gray-500 dark:text-gray-400">名称:</span>
				<span class="text-sm text-gray-900 dark:text-gray-100">{nodeData.label}</span>
			</div>
			{#if nodeData.description}
				<div class="flex items-start gap-2">
					<span class="text-xs font-medium text-gray-500 dark:text-gray-400 shrink-0">描述:</span>
					<span class="text-sm text-gray-900 dark:text-gray-100">{nodeData.description}</span>
				</div>
			{/if}
		</div>

		<!-- Traceability Info -->
		<div class="border-t border-gray-200 dark:border-gray-700 pt-3">
			<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">溯源信息</h4>
			{#if nodeData.traceability}
				<div class="space-y-2">
					<div class="flex items-center gap-2">
						<span class="text-xs font-medium text-gray-500 dark:text-gray-400">类型:</span>
						<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {entityTypeColors[nodeData.traceability.entityType] || entityTypeColors.none}">
							{entityTypeLabels[nodeData.traceability.entityType] || nodeData.traceability.entityType}
						</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="text-xs font-medium text-gray-500 dark:text-gray-400">名称:</span>
						<span class="text-sm text-gray-900 dark:text-gray-100">{nodeData.traceability.entityName}</span>
					</div>
					{#if nodeData.traceability.versionNumber}
						<div class="flex items-center gap-2">
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">版本:</span>
							<span class="text-sm text-gray-900 dark:text-gray-100">v{nodeData.traceability.versionNumber}</span>
						</div>
					{/if}
					<div class="flex items-center gap-2">
						<span class="text-xs font-medium text-gray-500 dark:text-gray-400">绑定时间:</span>
						<span class="text-sm text-gray-900 dark:text-gray-100">{formatDate(nodeData.traceability.boundAt)}</span>
					</div>
					{#if nodeData.traceability.boundBy}
						<div class="flex items-center gap-2">
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">绑定人:</span>
							<span class="text-sm text-gray-900 dark:text-gray-100">{nodeData.traceability.boundBy}</span>
						</div>
					{/if}
					<button
						class="mt-2 w-full px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
						onclick={handleNavigateToEntity}
					>
						查看实体详情
					</button>
				</div>
			{:else}
				<div class="text-center py-6">
					<div class="mb-3">
						<svg class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
						</svg>
					</div>
					<p class="text-sm text-gray-500 dark:text-gray-400 mb-2">该节点未绑定任何实体</p>
					<p class="text-xs text-gray-400 dark:text-gray-500">点击"查看配置"切换到配置面板，在"溯源绑定"标签页中进行绑定</p>
				</div>
			{/if}
		</div>

		<!-- Parameters -->
		{#if nodeData.inputParams && nodeData.inputParams.length > 0}
			<div class="border-t border-gray-200 dark:border-gray-700 pt-3">
				<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">输入参数</h4>
				<div class="space-y-1">
					{#each nodeData.inputParams as param}
						<div class="text-sm text-gray-900 dark:text-gray-100 px-2 py-1 bg-gray-50 dark:bg-gray-700 rounded">{param}</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if nodeData.outputParams && nodeData.outputParams.length > 0}
			<div class="border-t border-gray-200 dark:border-gray-700 pt-3">
				<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">输出参数</h4>
				<div class="space-y-1">
					{#each nodeData.outputParams as param}
						<div class="text-sm text-gray-900 dark:text-gray-100 px-2 py-1 bg-gray-50 dark:bg-gray-700 rounded">{param}</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
