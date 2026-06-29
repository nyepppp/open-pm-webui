<script lang="ts">
	import PMFormEditor from './PMFormEditor.svelte';
	import PMRichEditor from './PMRichEditor.svelte';
	import type { FieldConfig } from '$lib/apis/pm/types';

	// Props
	interface Props {
		formFields: FieldConfig[];
		formData?: Record<string, unknown>;
		richTextContent?: string;
		richTextPlaceholder?: string;
		onChange?: (data: { formData: Record<string, unknown>; richText: string }) => void;
		onSubmit?: (data: { formData: Record<string, unknown>; richText: string }) => void;
	}

	let {
		formFields,
		formData = {},
		richTextContent = '',
		richTextPlaceholder = '输入详细描述...',
		onChange,
		onSubmit
	}: Props = $props();

	let currentFormData = $state<Record<string, unknown>>({ ...formData });
	let currentRichText = $state(richTextContent);

	function handleFormChange(data: Record<string, unknown>) {
		currentFormData = data;
		onChange?.({ formData: currentFormData, richText: currentRichText });
	}

	function handleRichTextChange(content: string) {
		currentRichText = content;
		onChange?.({ formData: currentFormData, richText: currentRichText });
	}

	function handleSubmit() {
		onSubmit?.({ formData: currentFormData, richText: currentRichText });
	}
</script>

<div class="pm-mixed-editor flex flex-col h-full gap-6">
	<!-- Form Section -->
	<div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider mb-4">
			基本信息
		</h3>
		<PMFormEditor
			fields={formFields}
			data={currentFormData}
			onChange={handleFormChange}
		/>
	</div>

	<!-- Rich Text Section -->
	<div class="flex-1 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col min-h-[300px]">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider px-6 pt-6 pb-2">
			详细描述
		</h3>
		<div class="flex-1 px-6 pb-6">
			<PMRichEditor
				content={currentRichText}
				onChange={handleRichTextChange}
				placeholder={richTextPlaceholder}
			/>
		</div>
	</div>

	<!-- Submit Button -->
	{#if onSubmit}
		<div class="flex justify-end">
			<button
				class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors shadow-sm hover:shadow-md"
				onclick={handleSubmit}
				aria-label="保存条目"
			>
				保存
			</button>
		</div>
	{/if}
</div>
