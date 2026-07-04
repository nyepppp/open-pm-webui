<script lang="ts">
	interface Props {
		label?: string;
		value?: string;
		placeholder?: string;
		type?: 'text' | 'number' | 'date' | 'datetime-local';
		disabled?: boolean;
		class?: string;
		oninput?: (e: Event) => void;
		onkeydown?: (e: KeyboardEvent) => void;
	}

	let { label, value = $bindable(''), placeholder, type = 'text', disabled = false, class: className = '', oninput, onkeydown }: Props = $props();
	let inputId = $derived(label ? `pm-input-${Math.random().toString(36).slice(2, 9)}` : undefined);
</script>

{#if label}
	<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1" for={inputId}>{label}</label>
{/if}
<input
	id={inputId}
	{type}
	class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 {disabled ? 'opacity-50 cursor-not-allowed' : ''} {className}"
	{placeholder}
	{disabled}
	bind:value
	{oninput}
	{onkeydown}
/>
