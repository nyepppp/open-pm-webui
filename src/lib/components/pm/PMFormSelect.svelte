<script lang="ts">
	interface SelectOption {
		value: string;
		label: string;
	}

	interface Props {
		label?: string;
		value?: string;
		options?: SelectOption[];
		placeholder?: string;
		disabled?: boolean;
		editable?: boolean;
		class?: string;
		onchange?: (e: Event) => void;
	}

	let { label, value = $bindable(''), options = [], placeholder, disabled = false, editable = false, class: className = '', onchange }: Props = $props();
	let selectId = $derived(label ? `pm-select-${Math.random().toString(36).slice(2, 9)}` : undefined);
</script>

{#if label}
	<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1" for={selectId}>{label}</label>
{/if}
{#if editable}
	<input
		id={selectId}
		type="text"
		list="{selectId}-datalist"
		class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 {disabled ? 'opacity-50 cursor-not-allowed' : ''} {className}"
		{placeholder}
		{disabled}
		bind:value
		{onchange}
	/>
	<datalist id="{selectId}-datalist">
		{#each options as opt (opt.value)}
			<option value={opt.value}>{opt.label}</option>
		{/each}
	</datalist>
{:else}
	<select
		id={selectId}
		class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 {disabled ? 'opacity-50 cursor-not-allowed' : ''} {className}"
		{disabled}
		bind:value
		{onchange}
	>
		{#if placeholder}
			<option value="">{placeholder}</option>
		{/if}
		{#each options as opt (opt.value)}
			<option value={opt.value}>{opt.label}</option>
		{/each}
	</select>
{/if}
