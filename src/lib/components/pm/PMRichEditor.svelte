<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Placeholder from '@tiptap/extension-placeholder';

	interface Props {
		content?: string;
		onChange?: (content: string) => void;
		placeholder?: string;
		readonly?: boolean;
	}

	let { content = '', onChange, placeholder = '开始输入内容...', readonly = false }: Props = $props();

	let editor: Editor | null = $state(null);
	let element: HTMLDivElement | null = $state(null);
	let isFallback = $state(false);
	let fallbackText = $state(content);

	onMount(() => {
		if (!element) return;

		try {
			editor = new Editor({
				element,
				extensions: [
					StarterKit,
					Placeholder.configure({ placeholder })
				],
				content: content || '<p></p>',
				editable: !readonly,
				onUpdate: ({ editor }) => {
					onChange?.(editor.getHTML());
				}
			});
		} catch (err) {
			console.error('PMRichEditor: TipTap init failed', err);
			isFallback = true;
		}
	});

	onDestroy(() => {
		editor?.destroy();
	});

	let lastPropContent = $state(content);
	$effect(() => {
		if (content !== lastPropContent) {
			lastPropContent = content;
			if (editor && !isFallback) {
				const currentHTML = editor.getHTML();
				if (content !== currentHTML) {
					editor.commands.setContent(content || '<p></p>', false);
				}
			}
			if (isFallback) {
				fallbackText = content;
			}
		}
	});

	function handleFallbackInput(e: Event) {
		const target = e.target as HTMLTextAreaElement;
		fallbackText = target.value;
		onChange?.(fallbackText);
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
			<div class="flex items-center gap-1 px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-t-lg">
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('bold') ? 'bg-gray-200 dark:bg-gray-700' : ''}"
					onclick={() => editor?.chain().focus().toggleBold().run()}
					title="粗体"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6V4zm0 8h9a4 4 0 014 4 4 4 0 01-4 4H6v-8z" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('italic') ? 'bg-gray-200 dark:bg-gray-700' : ''}"
					onclick={() => editor?.chain().focus().toggleItalic().run()}
					title="斜体"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 4h4m-2 0v16m-4 0h8" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('heading', { level: 2 }) ? 'bg-gray-200 dark:bg-gray-700' : ''}"
					onclick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
					title="标题"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16" /></svg>
				</button>
				<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1"></div>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('bulletList') ? 'bg-gray-200 dark:bg-gray-700' : ''}"
					onclick={() => editor?.chain().focus().toggleBulletList().run()}
					title="无序列表"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
				</button>
				<button
					class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors {editor?.isActive('orderedList') ? 'bg-gray-200 dark:bg-gray-700' : ''}"
					onclick={() => editor?.chain().focus().toggleOrderedList().run()}
					title="有序列表"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h12M7 12h12M7 17h12M3 7h.01M3 12h.01M3 17h.01" /></svg>
				</button>
			</div>
		{/if}

		<div
			bind:this={element}
			class="p-4 overflow-auto prose dark:prose-invert max-w-none min-h-[200px]"
		></div>
	{/if}
</div>

<style>
	.pm-rich-editor :global(.ProseMirror) {
		outline: none;
		min-height: 200px;
	}

	.pm-rich-editor :global(.ProseMirror p.is-editor-empty:first-child::before) {
		content: attr(data-placeholder);
		float: left;
		color: #9ca3af;
		pointer-events: none;
		height: 0;
	}

	.pm-rich-editor :global(.ProseMirror p) {
		margin: 0.5em 0;
	}

	.pm-rich-editor :global(.ProseMirror h2) {
		font-size: 1.5em;
		font-weight: 600;
		margin: 0.75em 0 0.5em;
	}

	.pm-rich-editor :global(.ProseMirror ul) {
		padding-left: 1.5em;
		margin: 0.5em 0;
	}

	.pm-rich-editor :global(.ProseMirror ol) {
		padding-left: 1.5em;
		margin: 0.5em 0;
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
</style>
