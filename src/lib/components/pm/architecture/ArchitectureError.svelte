<script lang="ts">
	interface Props {
		error: string;
		onRetry?: () => void;
	}

	let { error = '', onRetry }: Props = $props();
</script>

<div class="flex h-64 flex-col items-center justify-center gap-4">
	<svg
		class="h-12 w-12 text-red-500"
		fill="none"
		viewBox="0 0 24 24"
		stroke="currentColor"
		stroke-width="2"
	>
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
		/>
	</svg>
	<p class="text-sm text-red-500 dark:text-red-400">{error}</p>
	{#if onRetry}
		<button
			onclick={onRetry}
			class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
		>
			重试
		</button>
	{/if}
</div>
