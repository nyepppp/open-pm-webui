<script lang="ts">
	export let entry: {
		id: string;
		title: string;
		module_type: string;
		status: string;
		priority?: string;
		content?: string;
		data?: Record<string, any>;
	};

	export let onCopy: (content: string) => void = () => {};
	export let onSelect: (entry: any) => void = () => {};

	let expanded = false;

	function toggleExpand() {
		expanded = !expanded;
	}

	function handleCopy() {
		const content = formatEntryContent(entry);
		onCopy(content);
	}

	function formatEntryContent(entry: any): string {
		const data = entry.data || {};
		const parameters = data.parameters || [];
		const paramText = parameters
			.map((p: any) => `- **${p.name}**: ${p.description} (默认值: ${p.default || 'N/A'})`)
			.join('\n');

		return `# ${entry.title}

## 基本信息
- **模块类型**: ${entry.module_type}
- **状态**: ${entry.status}
- **优先级**: ${entry.priority || '未设置'}

## 需求描述
${entry.content || '无内容'}

## 功能参数
${paramText || '无参数'}
`;
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'active':
			case 'completed':
				return 'bg-green-100 text-green-800';
			case 'draft':
				return 'bg-gray-100 text-gray-800';
			case 'in_progress':
				return 'bg-blue-100 text-blue-800';
			case 'archived':
				return 'bg-yellow-100 text-yellow-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}

	function getModuleTypeLabel(moduleType: string): string {
		const labels: Record<string, string> = {
			requirement: '需求',
			feature: '功能',
			spec: 'SPEC',
			prototype: '原型',
			document: '文档'
		};
		return labels[moduleType] || moduleType;
	}
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
	<div class="p-4">
		<div class="flex items-start justify-between">
			<div class="flex-1 min-w-0">
				<h3 class="text-sm font-medium text-gray-900 truncate">
					{entry.title}
				</h3>
				<div class="mt-1 flex items-center gap-2">
					<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
						{getModuleTypeLabel(entry.module_type)}
					</span>
					<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {getStatusColor(entry.status)}">
						{entry.status}
					</span>
					{#if entry.priority}
						<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
							{entry.priority}
						</span>
					{/if}
				</div>
			</div>
			<div class="flex items-center gap-1 ml-2">
				<button
					on:click={handleCopy}
					class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
					title="复制内容"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
					</svg>
				</button>
				<button
					on:click={() => onSelect(entry)}
					class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
					title="引用到对话"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
				</button>
				<button
					on:click={toggleExpand}
					class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
					title="展开/收起"
				>
					<svg class="w-4 h-4 transform transition-transform {expanded ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
					</svg>
				</button>
			</div>
		</div>

		{#if expanded}
			<div class="mt-3 pt-3 border-t border-gray-100">
				{#if entry.content}
					<div class="text-sm text-gray-600 mb-2">
						{entry.content}
					</div>
				{/if}
				{#if entry.data?.parameters}
					<div class="mt-2">
						<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">参数</h4>
						<div class="space-y-1">
							{#each entry.data.parameters as param}
								<div class="flex items-center justify-between text-sm">
									<span class="text-gray-700 font-medium">{param.name}</span>
									<span class="text-gray-500">{param.description}</span>
									{#if param.default}
										<span class="text-xs text-gray-400">默认: {param.default}</span>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
