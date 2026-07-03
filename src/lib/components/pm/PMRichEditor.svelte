<script lang="ts">
	import { onMount } from 'svelte';
	import { Editor } from '@tiptap/core';
	import { getPMExtensions } from './pmTiptapConfig';
	import PMDocumentImporter from './PMDocumentImporter.svelte';
	import PMTableOfContents from './PMTableOfContents.svelte';
	import PMAnnotationPanel from './PMAnnotationPanel.svelte';
	import type { EntryAnnotation } from '$lib/apis/pm/types';

	interface Props {
		content?: string;
		onChange?: (content: string) => void;
		placeholder?: string;
		readonly?: boolean;
		showToc?: boolean;
		annotations?: EntryAnnotation[];
		onAnnotationsChange?: (annotations: EntryAnnotation[]) => void;
	}

	let {
		content = '',
		onChange,
		placeholder = '开始输入内容...',
		readonly = false,
		showToc = true,
		annotations = [],
		onAnnotationsChange
	}: Props = $props();

	let editor: Editor | null = $state(null);
	let element: HTMLDivElement | null = $state(null);
	let isFallback = $state(false);
	let fallbackText = $state(content);
	let tocVisible = $state(showToc);
	let activeHeadingLevel = $state(0);
	let annotationPanelVisible = $state(false);
	let hasSelection = $state(false);
	let annotationBtnPos = $state<{ top: number; left: number }>({ top: 0, left: 0 });

	// Track last synced prop content with a non-reactive variable to avoid $effect loops
	let lastPropContent = content;
	let pendingUpdate: number | null = null;
	let editorReady = $state(false);

	onMount(() => {
		if (!element) return;
		// Defer init to next frame so DOM is fully ready
		requestAnimationFrame(() => {
			if (!element) return;
			try {
				editor = new Editor({
					element,
					extensions: getPMExtensions(placeholder),
					content: content || '<p></p>',
					editable: !readonly,
					autofocus: !readonly,
					onUpdate: ({ editor }) => {
						onChange?.(editor.getHTML());
					},
					onTransaction: () => {
						if (!editor || editor.isDestroyed) return;
						// Defer Svelte reactivity trigger to rAF so we don't interleave
						// DOM reads/writes with ProseMirror's updateStateInner.
						if (!pendingUpdate) {
							pendingUpdate = requestAnimationFrame(() => {
								pendingUpdate = null;
								if (editor && !editor.isDestroyed) {
									// Re-assign to trigger Svelte 5 reactivity
									editor = editor;
								}
							});
						}
					},
					onSelectionUpdate: ({ editor }) => {
						if (editor.isDestroyed) return;
						const { from, to } = editor.state.selection;
						const hasSel = from !== to;
						hasSelection = hasSel;
						if (hasSel) {
							const coords = editor.view.coordsAtPos(from);
							const editorRect = element?.getBoundingClientRect();
							if (editorRect) {
								annotationBtnPos = {
									top: coords.top - editorRect.top - 32,
									left: coords.left - editorRect.left
								};
							}
						}
					},
					onCreate: () => {
						editorReady = true;
					}
				});
			} catch (err) {
				console.error('PMRichEditor: TipTap init failed', err);
				isFallback = true;
			}
		});
	});

	// Sync external content prop → editor (one-way, no loop)
	$effect(() => {
		const newContent = content;
		if (newContent !== lastPropContent) {
			lastPropContent = newContent;
			if (editor && !editor.isDestroyed && !isFallback) {
				const currentHTML = editor.getHTML();
				if (newContent !== currentHTML) {
					editor.commands.setContent(newContent || '<p></p>', false);
				}
			}
			if (isFallback) {
				fallbackText = newContent;
			}
		}
	});

	// Sync editable prop → editor options
	$effect(() => {
		if (editor && !editor.isDestroyed) {
			editor.setOptions({ editable: !readonly });
		}
	});

	import { onDestroy } from 'svelte';
	onDestroy(() => {
		if (pendingUpdate) {
			cancelAnimationFrame(pendingUpdate);
		}
		editor?.destroy();
	});

	function handleFallbackInput(e: Event) {
		const target = e.target as HTMLTextAreaElement;
		fallbackText = target.value;
		onChange?.(fallbackText);
	}

	function setHeading(level: number) {
		if (!editor || editor.isDestroyed) return;
		if (activeHeadingLevel === level) {
			editor.chain().focus().setParagraph().run();
			activeHeadingLevel = 0;
		} else {
			editor.chain().focus().toggleHeading({ level: level as 1|2|3|4|5|6 }).run();
			activeHeadingLevel = level;
		}
	}

	function insertLink() {
		if (!editor || editor.isDestroyed) return;
		const url = prompt('输入链接地址:');
		if (url) {
			editor.chain().focus().setLink({ href: url }).run();
		}
	}

	function insertImage() {
		if (!editor || editor.isDestroyed) return;
		const url = prompt('输入图片地址:');
		if (url) {
			editor.chain().focus().setImage({ src: url }).run();
		}
	}

	function insertTable() {
		if (!editor || editor.isDestroyed) return;
		editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
	}

	function addAnnotation() {
		if (!editor || editor.isDestroyed) return;
		const annotationText = prompt('输入批注内容:');
		if (!annotationText) return;
		const id = Date.now().toString();
		editor.chain().focus().setAnnotation({ id, color: 'yellow' }).run();
		const { from, to } = editor.state.selection;
		const selectedText = editor.state.doc.textBetween(from, to, ' ');
		const newAnnotation: EntryAnnotation = {
			id,
			entryId: '',
			entryVersionId: '',
			textRange: { from, to },
			selectedText,
			content: annotationText,
			highlightColor: 'yellow',
			createdBy: '',
			createdAt: Date.now(),
			updatedAt: Date.now()
		};
		onAnnotationsChange?.([...annotations, newAnnotation]);
		hasSelection = false;
	}

	function handleAnnotationClick(annotation: EntryAnnotation) {
		if (!editor || editor.isDestroyed) return;
		try {
			editor.commands.setTextSelection({ from: annotation.textRange.from, to: annotation.textRange.to });
			editor.commands.scrollIntoView();
		} catch { /* position may be stale */ }
	}

	function handleAnnotationRemove(id: string) {
		const updated = annotations.filter(a => a.id !== id);
		onAnnotationsChange?.(updated);
		if (editor && !editor.isDestroyed) {
			editor.chain().focus().unsetAnnotation().run();
		}
	}

	function handleAiModify(annotation: EntryAnnotation) {
		const newContent = prompt('AI 修改批注内容:', annotation.content);
		if (newContent === null) return;
		const updated = annotations.map(a => a.id === annotation.id ? { ...a, content: newContent } : a);
		onAnnotationsChange?.(updated);
	}
</script>

<div class="pm-rich-editor flex flex-col bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
	{#if isFallback}
		<textarea
			class="w-full p-4 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 resize-none focus:outline-none min-h-[200px]"
			value={fallbackText}
			oninput={handleFallbackInput}
			placeholder={placeholder}
		></textarea>
	{:else}
		{#if !readonly}
			<!-- Toolbar -->
			<div class="flex items-center gap-0.5 px-2 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-t-lg flex-wrap">
				<!-- Text formatting -->
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('bold') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleBold().run()}
					title="粗体 (Ctrl+B)"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6V4zm0 8h9a4 4 0 014 4 4 4 0 01-4 4H6v-8z" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('italic') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleItalic().run()}
					title="斜体 (Ctrl+I)"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 4h4m-2 0v16m-4 0h8" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('strike') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleStrike().run()}
					title="删除线"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5a4 4 0 00-4 4c0 2 1.5 3 4 3s4-1 4-3a4 4 0 00-4-4zM8 19a4 4 0 004-3" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('underline') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleUnderline().run()}
					title="下划线"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v8a5 5 0 0010 0V4M5 20h14" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('highlight') ? 'bg-yellow-200 dark:bg-yellow-800 text-yellow-700 dark:text-yellow-300' : ''}"
					onclick={() => editor?.chain().focus().toggleHighlight().run()}
					title="高亮"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 17.5H3v-3.5L15.232 5.232z" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('code') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleCode().run()}
					title="行内代码"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
				</button>

				<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-0.5"></div>

				<!-- Headings -->
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-xs font-bold {editor?.isActive('heading', { level: 1 }) ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => setHeading(1)}
					title="标题 1"
				>
					H1
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-xs font-bold {editor?.isActive('heading', { level: 2 }) ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => setHeading(2)}
					title="标题 2"
				>
					H2
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-xs font-bold {editor?.isActive('heading', { level: 3 }) ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => setHeading(3)}
					title="标题 3"
				>
					H3
				</button>

				<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-0.5"></div>

				<!-- Lists -->
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('bulletList') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleBulletList().run()}
					title="无序列表"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('orderedList') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleOrderedList().run()}
					title="有序列表"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h12M7 12h12M7 17h12M3 7h.01M3 12h.01M3 17h.01" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('blockquote') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleBlockquote().run()}
					title="引用块"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 4H6a2 2 0 00-2 2v4a2 2 0 002 2h4m0-8v8m4-4h4a2 2 0 002-2V6a2 2 0 00-2-2h-4m0 8V4" /></svg>
				</button>

				<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-0.5"></div>

				<!-- Insert -->
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
					onclick={insertLink}
					title="插入链接"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
					onclick={insertImage}
					title="插入图片"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
					onclick={insertTable}
					title="插入表格"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18M10 3v18M14 3v18M4 4h16a1 1 0 011 1v14a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('codeBlock') ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => editor?.chain().focus().toggleCodeBlock().run()}
					title="代码块"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
					onclick={() => editor?.chain().focus().setHorizontalRule().run()}
					title="分割线"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12h18" /></svg>
				</button>

				<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-0.5"></div>

				<!-- Undo/Redo -->
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
					onclick={() => editor?.chain().focus().undo().run()}
					title="撤销 (Ctrl+Z)"
					disabled={!editor?.can().undo()}
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v2M3 10l4-4M3 10l4 4" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
					onclick={() => editor?.chain().focus().redo().run()}
					title="重做 (Ctrl+Y)"
					disabled={!editor?.can().redo()}
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a5 5 0 00-5 5v2M21 10l-4-4M21 10l-4 4" /></svg>
				</button>

				<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-0.5"></div>

				<!-- Document Import -->
				<PMDocumentImporter editor={editor} />

				<!-- TOC Toggle -->
				{#if showToc}
					<button
						class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {tocVisible ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
						onclick={() => tocVisible = !tocVisible}
						title="目录"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h10M4 18h10" /></svg>
					</button>
				{/if}

				<!-- Annotation Toggle -->
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {annotationPanelVisible ? 'bg-gray-200 dark:bg-gray-700 text-blue-600' : ''}"
					onclick={() => annotationPanelVisible = !annotationPanelVisible}
					title="批注面板"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" /></svg>
				</button>
			</div>
		{/if}

		<!-- Editor content area with optional TOC sidebar and annotation panel -->
		<div class="flex-1 flex min-h-[200px] overflow-hidden">
			{#if tocVisible && !readonly}
				<div class="w-56 shrink-0 border-r border-gray-200 dark:border-gray-700 overflow-auto hidden lg:block">
					<PMTableOfContents editor={editor} />
				</div>
			{/if}
			<div class="flex-1 relative overflow-auto">
				<!-- Floating annotation button -->
				{#if hasSelection && !readonly}
					<button
						class="absolute z-10 px-2 py-1 text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-lg shadow-md hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-colors flex items-center gap-1"
						style="top: {annotationBtnPos.top}px; left: {annotationBtnPos.left}px;"
						onclick={addAnnotation}
					>
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" /></svg>
						批注
					</button>
				{/if}
				<div
					bind:this={element}
					class="pm-editor-content p-4 max-w-none"
				></div>
			</div>
			{#if annotationPanelVisible && !readonly}
				<PMAnnotationPanel
					annotations={annotations}
					onAnnotationClick={handleAnnotationClick}
					onAnnotationRemove={handleAnnotationRemove}
					onAiModify={handleAiModify}
				/>
			{/if}
		</div>
	{/if}
</div>

<style>
	.pm-rich-editor :global(.ProseMirror) {
		outline: none;
		min-height: 200px;
		cursor: text;
		color: inherit;
	}

	.pm-rich-editor :global(.ProseMirror p.is-editor-empty:first-child::before) {
		content: attr(data-placeholder);
		float: left;
		color: #9ca3af;
		pointer-events: none;
		height: 0;
	}

	.pm-rich-editor :global(.ProseMirror h1) {
		font-size: 2em;
		font-weight: 700;
		margin: 0.67em 0 0.33em;
	}

	.pm-rich-editor :global(.ProseMirror h2) {
		font-size: 1.5em;
		font-weight: 600;
		margin: 0.75em 0 0.5em;
	}

	.pm-rich-editor :global(.ProseMirror h3) {
		font-size: 1.25em;
		font-weight: 600;
		margin: 0.75em 0 0.5em;
	}

	.pm-rich-editor :global(.ProseMirror h4) {
		font-size: 1.1em;
		font-weight: 600;
		margin: 0.75em 0 0.5em;
	}

	.pm-rich-editor :global(.ProseMirror p) {
		margin: 0.5em 0;
	}

	.pm-rich-editor :global(.ProseMirror ul) {
		padding-left: 1.5em;
		margin: 0.5em 0;
	}

	.pm-rich-editor :global(.ProseMirror ol) {
		padding-left: 1.5em;
		margin: 0.5em 0;
	}

	.pm-rich-editor :global(.ProseMirror blockquote) {
		border-left: 3px solid #d1d5db;
		padding-left: 1em;
		margin: 0.5em 0;
		color: #6b7280;
	}

	.pm-rich-editor :global(.ProseMirror code) {
		background-color: rgba(156, 163, 175, 0.2);
		padding: 0.2em 0.4em;
		border-radius: 0.25em;
		font-size: 0.875em;
	}

	.pm-rich-editor :global(.ProseMirror pre) {
		background-color: #1f2937;
		color: #f3f4f6;
		padding: 1em;
		border-radius: 0.5em;
		overflow-x: auto;
		margin: 0.5em 0;
	}

	.pm-rich-editor :global(.ProseMirror pre code) {
		background: none;
		padding: 0;
		color: inherit;
	}

	.pm-rich-editor :global(.ProseMirror mark) {
		background-color: #fef08a;
		padding: 0.1em 0.2em;
		border-radius: 0.15em;
	}

	.pm-rich-editor :global(.ProseMirror table) {
		border-collapse: collapse;
		width: 100%;
		margin: 0.75em 0;
	}

	.pm-rich-editor :global(.ProseMirror table td),
	.pm-rich-editor :global(.ProseMirror table th) {
		border: 1px solid #d1d5db;
		padding: 0.5em 0.75em;
		text-align: left;
		min-width: 80px;
	}

	.pm-rich-editor :global(.ProseMirror table th) {
		background-color: #f3f4f6;
		font-weight: 600;
	}

	.pm-rich-editor :global(.ProseMirror img) {
		max-width: 100%;
		height: auto;
		border-radius: 0.5em;
		margin: 0.5em 0;
	}

	.pm-rich-editor :global(.ProseMirror a) {
		color: #3b82f6;
		text-decoration: underline;
		cursor: pointer;
	}

	.pm-rich-editor :global(.ProseMirror hr) {
		border: none;
		border-top: 1px solid #d1d5db;
		margin: 1em 0;
	}

	.pm-rich-editor :global(.ProseMirror span[data-annotation-id]) {
		background-color: #FFF9C4;
		border-bottom: 2px solid #FFD600;
		cursor: pointer;
	}
</style>