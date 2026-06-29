<script lang="ts">
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<svelte:head>
	<title>PM 工作台</title>
</svelte:head>

<div class="flex flex-col h-full w-full">
	{@render children?.()}
</div>
