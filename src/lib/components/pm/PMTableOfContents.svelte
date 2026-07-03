<script lang="ts">
	import type { Editor } from '@tiptap/core';
	import type { HeadingItem } from './pmTiptapConfig';
	import { extractHeadings } from './pmTiptapConfig';

	interface Props {
		editor: Editor | null;
		onHeadingClick?: (heading: HeadingItem) => void;
	}

	let { editor, onHeadingClick }: Props = $props();

	let headings = $state<HeadingItem[]>([]);
	let collapsedLevels = $state<Set<number>>(new Set());

	$effect(() => {
		if (!editor) {
			headings = [];
			return;
		}

		const updateHeadings = () => {
			headings = extractHeadings(editor!);
		};

		updateHeadings();

		const handler = () => {
			updateHeadings();
		};

		editor.on('update', handler);
		return () => {
			editor.off('update', handler);
		};
	});

	function toggleCollapse(level: number) {
		const next = new Set(collapsedLevels);
		if (next.has(level)) {
			next.delete(level);
		} else {
			next.add(level);
		}
		collapsedLevels = next;
	}

	function handleHeadingClick(heading: HeadingItem) {
		onHeadingClick?.(heading);
		if (!editor) return;

		// Find heading position in document and scroll to it
		let foundPos = -1;
		editor.state.doc.descendants((node, pos) => {
			if (foundPos >= 0) return false;
			if (node.type.name === 'heading' && node.textContent === heading.text) {
				foundPos = pos;
				return false;
			}
		});

		if (foundPos >= 0) {
			editor.chain().focus().setTextSelection(foundPos).run();
			// Scroll the editor container to the heading
			const editorEl = (editor.view.dom as HTMLElement).closest('.pm-editor-content');
			if (editorEl) {
				const headingDom = editor.view.dom.querySelector(`[data-heading="${heading.id}"]`);
				if (headingDom) {
					headingDom.scrollIntoView({ behavior: 'smooth', block: 'center' });
				}
			}
		}
	}

	function isHeadingVisible(heading: HeadingItem): boolean {
		for (const level of collapsedLevels) {
			if (heading.level > level) return false;
		}
		return true;
	}

	function hasChildHeadings(heading: HeadingItem): boolean {
		const idx = headings.indexOf(heading);
		if (idx < 0 || idx === headings.length - 1) return false;
		return headings[idx + 1].level > heading.level;
	}
</script>

{#if headings.length > 0}
	<div class="pm-toc flex flex-col h-full">
		<div class="px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-t-lg">
			<h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">目录</h4>
		</div>
		<div class="flex-1 overflow-auto px-2 py-2">
			{#each headings as heading (heading.id)}
				{#if isHeadingVisible(heading)}
					<div
						class="flex items-center gap-1 py-1 px-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer transition-colors {heading.level <= 2 ? 'font-medium' : ''}"
						style="padding-left: {(heading.level - 1) * 12}px;"
						onclick={() => handleHeadingClick(heading)}
					>
						{#if hasChildHeadings(heading)}
							<button
								class="w-4 h-4 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 shrink-0"
								onclick={(e) => { e.stopPropagation(); toggleCollapse(heading.level); }}
								title={collapsedLevels.has(heading.level) ? '展开' : '折叠'}
							>
								{#if collapsedLevels.has(heading.level)}
									<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" /></svg>
								{:else}
									<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 010-1.414l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
								{/if}
							</button>
						{:else}
							<span class="w-4 shrink-0"></span>
						{/if}
						<span class="truncate text-gray-700 dark:text-gray-300 {heading.level === 1 ? 'text-sm font-semibold' : heading.level === 2 ? 'text-sm font-medium' : 'text-xs'}">
							{heading.text || '(空标题)'}
						</span>
					</div>
				{/if}
			{/each}
		</div>
		<div class="px-3 py-1.5 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-b-lg">
			<span class="text-xs text-gray-400 dark:text-gray-500">{headings.length} 个标题</span>
		</div>
	</div>
{/if}

<style>
	.pm-toc :global(*) {
		scrollbar-width: thin;
	}
</style>
