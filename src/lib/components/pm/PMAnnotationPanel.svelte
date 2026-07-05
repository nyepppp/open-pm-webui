<script lang="ts">
	import type { EntryAnnotation, ModuleEntry } from '$lib/apis/pm/types';

	interface Props {
		annotations: EntryAnnotation[];
		linkedEntriesData?: Map<string, ModuleEntry>;
		onAnnotationClick: (annotation: EntryAnnotation) => void;
		onAnnotationRemove: (id: string) => void;
		onAiModify: (annotation: EntryAnnotation) => void;
		onLinkEntries?: (annotation: EntryAnnotation) => void;
	}

	let {
		annotations,
		linkedEntriesData = new Map(),
		onAnnotationClick,
		onAnnotationRemove,
		onAiModify,
		onLinkEntries
	}: Props = $props();

	let boundaryFilter = $state<string>('all');
	let annotationCount = $derived(annotations.length);

	let boundaries = $derived.by(() => {
		const set = new Set<string>();
		for (const a of annotations) {
			if (a.boundary) set.add(a.boundary);
		}
		return [...set].sort();
	});

	let filteredAnnotations = $derived(
		boundaryFilter === 'all'
			? annotations
			: annotations.filter((a) => a.boundary === boundaryFilter)
	);

	function truncate(text: string, maxLen: number = 40): string {
		if (text.length <= maxLen) return text;
		return text.slice(0, maxLen) + '…';
	}

	function formatTimestamp(ts: number): string {
		const date = new Date(ts);
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		const hours = String(date.getHours()).padStart(2, '0');
		const minutes = String(date.getMinutes()).padStart(2, '0');
		return `${month}-${day} ${hours}:${minutes}`;
	}

	function getLinkedEntry(id: string): ModuleEntry | undefined {
		return linkedEntriesData.get(id);
	}

	function getModuleLabel(moduleType: string): string {
		const labels: Record<string, string> = {
			requirement: '需求',
			spec: '规格',
			parameter: '参数',
			prd: 'PRD',
			testcase: '用例'
		};
		return labels[moduleType] || moduleType;
	}

	function getModuleTypeColor(moduleType: string): string {
		const colors: Record<string, string> = {
			requirement: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
			spec: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
			parameter: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
			prd: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
			testcase: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300'
		};
		return colors[moduleType] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
	}
</script>

<div class="w-64 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
	<!-- Header -->
	<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
		<span class="inline-block w-2.5 h-2.5 rounded-full bg-yellow-400"></span>
		<h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
			批注 ({annotationCount})
		</h3>
	</div>

	<!-- Boundary Filter -->
	{#if boundaries.length > 0}
		<div class="px-3 py-2 border-b border-gray-100 dark:border-gray-800">
			<select
				class="w-full text-xs rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-2 py-1.5 text-gray-700 dark:text-gray-300 focus:ring-1 focus:ring-blue-500"
				bind:value={boundaryFilter}
			>
				<option value="all">全部边界</option>
				{#each boundaries as b}
					<option value={b}>{b}</option>
				{/each}
			</select>
		</div>
	{/if}

	<!-- Annotation List -->
	<div class="flex-1 overflow-y-auto">
		{#if filteredAnnotations.length === 0}
			<div class="flex items-center justify-center h-full">
				<p class="text-sm text-gray-400 dark:text-gray-500">
					{annotationCount === 0 ? '暂无批注' : '无匹配批注'}
				</p>
			</div>
		{:else}
			<div class="p-2 space-y-2">
				{#each filteredAnnotations as annotation (annotation.id)}
					<div
						class="rounded-xl border border-gray-200 dark:border-gray-700 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer group"
						onclick={() => onAnnotationClick(annotation)}
					>
						<!-- Selected text excerpt with highlight -->
						<div class="mb-2">
							<span
								class="text-xs px-1.5 py-0.5 rounded bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 font-medium"
							>
								{truncate(annotation.selectedText)}
							</span>
						</div>

						<!-- Annotation content -->
						<p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-2">
							{annotation.content}
						</p>

						<!-- Boundary tag -->
						{#if annotation.boundary}
							<span class="inline-block text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 mb-1.5">
								{annotation.boundary}
							</span>
						{/if}

						<!-- Element ref -->
						{#if annotation.elementRef?.componentName}
							<span class="inline-block text-[10px] px-1.5 py-0.5 rounded-full bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 mb-1.5">
								组件: {annotation.elementRef.componentName}
							</span>
						{/if}

						<!-- Linked entries badges -->
						{#if annotation.linkedEntries && annotation.linkedEntries.length > 0}
							<div class="flex flex-wrap gap-1 mb-2">
								{#each annotation.linkedEntries as linkedId}
									{@const linkedEntry = getLinkedEntry(linkedId)}
									{#if linkedEntry}
										<a
											href="/pm/{linkedEntry.projectId}/{linkedEntry.moduleType}"
											class="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full {getModuleTypeColor(linkedEntry.moduleType)} hover:opacity-80 transition-opacity"
											onclick={(e) => { e.stopPropagation(); }}
										>
											{getModuleLabel(linkedEntry.moduleType)}
											{truncate(linkedEntry.title, 16)}
										</a>
										<!-- Parameter indicators -->
										{#if linkedEntry.moduleType === 'parameter' && linkedEntry.data}
											{@const paramData = linkedEntry.data as Record<string, unknown>}
											{#if paramData.paramType}
												<span class="text-[9px] px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
													{paramData.paramType}
												</span>
											{/if}
											{#if paramData.required === 1}
												<span class="text-[9px] px-1 py-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">必填</span>
											{/if}
											{#if paramData.defaultValue}
												<span class="text-[9px] px-1 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
													默认: {String(paramData.defaultValue).slice(0, 12)}
												</span>
											{/if}
										{/if}
									{:else}
										<span class="inline-flex items-center text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500">
											{linkedId.slice(0, 8)}…
										</span>
									{/if}
								{/each}
							</div>
						{/if}

						<!-- Footer: timestamp + actions -->
						<div class="flex items-center justify-between">
							<span class="text-xs text-gray-400 dark:text-gray-500">
								{formatTimestamp(annotation.createdAt)}
							</span>

							<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
								<!-- Link entries button -->
								{#if onLinkEntries}
									<button
										class="text-xs px-2 py-0.5 rounded-md bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
										onclick={(e) => { e.stopPropagation(); onLinkEntries(annotation); }}
									>
										关联
									</button>
								{/if}
								<!-- AI Modify button -->
								<button
									class="text-xs px-2 py-0.5 rounded-md bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors"
									onclick={(e) => { e.stopPropagation(); onAiModify(annotation); }}
								>
									AI 修改
								</button>

								<!-- Remove button -->
								<button
									class="text-xs w-5 h-5 flex items-center justify-center rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
									onclick={(e) => { e.stopPropagation(); onAnnotationRemove(annotation.id); }}
									title="删除批注"
								>
									✕
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
