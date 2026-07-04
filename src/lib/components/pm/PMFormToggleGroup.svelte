<script lang="ts">
	interface ToggleOption {
		value: string;
		label: string;
		color?: string;
	}

	interface Props {
		label?: string;
		options: ToggleOption[];
		selected?: string;
		onchange?: (value: string) => void;
	}

	let { label, options, selected = $bindable(''), onchange }: Props = $props();

	const INACTIVE = 'bg-gray-100 dark:bg-gray-700 text-gray-500';

	function handleClick(value: string) {
		selected = value;
		onchange?.(value);
	}
</script>

{#if label}
	<div class="flex items-center gap-2">
		<span class="text-xs text-gray-500">{label}</span>
		<div class="flex items-center gap-1">
			{#each options as opt (opt.value)}
				<button
					class="px-1.5 py-0.5 text-xs rounded transition {selected === opt.value ? (opt.color || 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400') : INACTIVE}"
					onclick={() => handleClick(opt.value)}
				>{opt.label}</button>
			{/each}
		</div>
	</div>
{:else}
	<div class="flex items-center gap-1">
		{#each options as opt (opt.value)}
			<button
				class="px-1.5 py-0.5 text-xs rounded transition {selected === opt.value ? (opt.color || 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400') : INACTIVE}"
				onclick={() => handleClick(opt.value)}
			>{opt.label}</button>
		{/each}
	</div>
{/if}
