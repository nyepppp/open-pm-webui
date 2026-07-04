<script lang="ts">
	interface Props {
		title: string;
		children?: import('svelte').Snippet;
	}

	let { title, children }: Props = $props();
</script>

<div class="border-t border-gray-100 dark:border-gray-800 pt-2 mt-1">
	<h4 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-2">{title}</h4>
	{@render children?.()}
</div>
