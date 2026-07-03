<script lang="ts">
	import { onMount } from 'svelte';
	import type { Editor } from '@tiptap/core';
	import mammoth from 'mammoth';
	import { marked } from 'marked';
	import { toast } from 'svelte-sonner';

	interface Props {
		editor: Editor | null;
		onImported?: () => void;
	}

	let { editor, onImported }: Props = $props();

	let showImporter = $state(false);
	let importError = $state('');
	let isImporting = $state(false);

	function openImporter() {
		showImporter = true;
		importError = '';
	}

	function closeImporter() {
		showImporter = false;
		importError = '';
	}

	async function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file || !editor) return;

		isImporting = true;
		importError = '';

		try {
			const ext = file.name.split('.').pop()?.toLowerCase();
			let html = '';

			if (ext === 'docx') {
				const arrayBuffer = await file.arrayBuffer();
				const result = await mammoth.convertToHtml({ arrayBuffer });
				html = result.value;
				if (result.messages.length > 0) {
					console.warn('[PMDocumentImporter] mammoth warnings:', result.messages);
				}
			} else if (ext === 'md' || ext === 'markdown') {
				const text = await file.text();
				html = await marked(text);
			} else if (ext === 'txt') {
				const text = await file.text();
				const paragraphs = text.split(/\n\n+/).map((p) => `<p>${p.replace(/\n/g, '<br>')}</p>`);
				html = paragraphs.join('');
			} else {
				importError = '不支持的文件格式。请使用 .docx, .md 或 .txt 文件。';
				isImporting = false;
				return;
			}

			if (html && editor) {
				editor.commands.setContent(html, true);
				onImported?.();
				toast.success('文档导入成功');
			}
		} catch (err) {
			console.error('[PMDocumentImporter] import failed:', err);
			importError = `导入失败: ${(err as Error).message}`;
			toast.error('文档导入失败');
		} finally {
			isImporting = false;
			showImporter = false;
			input.value = '';
		}
	}
</script>

{#if editor}
	<button
		class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
		onclick={openImporter}
		title="导入文档"
		disabled={!editor}
	>
		<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
		</svg>
	</button>

	{#if showImporter}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onclick={closeImporter}>
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6" onclick={(e) => e.stopPropagation()}>
				<h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">导入文档</h3>
				<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
					支持 .docx、.md、.txt 格式。导入文档的完整文本内容到编辑器中。
				</p>

				<div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
					{#if isImporting}
						<div class="flex items-center justify-center gap-2">
							<svg class="w-5 h-5 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
							</svg>
							<span class="text-sm text-gray-600 dark:text-gray-400">正在导入...</span>
						</div>
					{:else}
						<svg class="w-12 h-12 mx-auto mb-3 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
						</svg>
						<p class="text-sm text-gray-500 dark:text-gray-400 mb-3">点击选择文件或拖拽文件到此处</p>
						<label class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg cursor-pointer transition-colors">
							选择文件
							<input
								type="file"
								class="hidden"
								accept=".docx,.md,.txt,.markdown"
								onchange={handleFileSelect}
							/>
						</label>
					{/if}
				</div>

				{#if importError}
					<p class="mt-3 text-sm text-red-500 dark:text-red-400">{importError}</p>
				{/if}

				<div class="mt-4 flex justify-end">
					<button
						class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
						onclick={closeImporter}
					>
						取消
					</button>
				</div>
			</div>
		</div>
	{/if}
{/if}
