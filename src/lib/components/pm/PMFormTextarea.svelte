<script lang="ts">
	interface Props {
		label?: string;
		value?: string;
		placeholder?: string;
		rows?: number;
		disabled?: boolean;
		class?: string;
		oninput?: (e: Event) => void;
	}

	let { label, value = $bindable(''), placeholder, rows = 3, disabled = false, class: className = '', oninput }: Props = $props();
	let textareaId = $derived(label ? `pm-textarea-${Math.random().toString(36).slice(2, 9)}` : undefined);
</script>

{#if label}
	<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1" for={textareaId}>{label}</label>
{/if}
<textarea
	id={textareaId}
	class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none {disabled ? 'opacity-50 cursor-not-allowed' : ''} {className}"
	{placeholder}
	{rows}
	{disabled}
	bind:value
	{oninput}
></textarea>
