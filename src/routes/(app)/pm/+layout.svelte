<script lang="ts">
	import { showSidebar } from '$lib/stores';

	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<svelte:head>
	<title>PM 工作台</title>
</svelte:head>

<div
	class="flex flex-col h-full w-full transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''} max-w-full"
>
	{@render children?.()}
</div>