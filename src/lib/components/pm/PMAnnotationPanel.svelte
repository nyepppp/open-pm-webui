<script lang="ts">
	import type { EntryAnnotation } from '$lib/apis/pm/types';

	interface Props {
		annotations: EntryAnnotation[];
		onAnnotationClick: (annotation: EntryAnnotation) => void;
		onAnnotationRemove: (id: string) => void;
		onAiModify: (annotation: EntryAnnotation) => void;
	}

	let { annotations, onAnnotationClick, onAnnotationRemove, onAiModify }: Props = $props();

	let annotationCount = $derived(annotations.length);

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
</script>

<div class="w-64 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
	<!-- Header -->
	<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
		<span class="inline-block w-2.5 h-2.5 rounded-full bg-yellow-400"></span>
		<h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
			批注 ({annotationCount})
		</h3>
	</div>

	<!-- Annotation List -->
	<div class="flex-1 overflow-y-auto">
		{#if annotationCount === 0}
			<div class="flex items-center justify-center h-full">
				<p class="text-sm text-gray-400 dark:text-gray-500">暂无批注</p>
			</div>
		{:else}
			<div class="p-2 space-y-2">
				{#each annotations as annotation (annotation.id)}
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

						<!-- Footer: timestamp + actions -->
						<div class="flex items-center justify-between">
							<span class="text-xs text-gray-400 dark:text-gray-500">
								{formatTimestamp(annotation.createdAt)}
							</span>

							<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
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
