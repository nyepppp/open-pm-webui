<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import { WEBUI_BASE_URL } from '$lib/constants';

	let selected = '';
	
	// Check if we're on the workflows page
	$: isWorkflowsPage = $page.url.pathname.startsWith('/workflows');
	$: isPmPage = $page.url.pathname.startsWith('/pm');
</script>

<nav
	aria-label="App navigation"
	class="min-w-[4.5rem] bg-gray-50 dark:bg-gray-950 flex gap-2.5 flex-col pt-8"
>
	<div class="flex justify-center relative">
		{#if selected === 'home'}
			<div class="absolute top-0 left-0 flex h-full">
				<div class="my-auto rounded-r-lg w-1 h-8 bg-black dark:bg-white"></div>
			</div>
		{/if}

		<Tooltip content="Home" placement="right">
			<button
				aria-label="Home"
				class=" cursor-pointer {selected === 'home' ? 'rounded-2xl' : 'rounded-full'}"
				on:click={() => {
					selected = 'home';

					if (window.electronAPI) {
						window.electronAPI.load('home');
					}
				}}
			>
				<img
					src="{WEBUI_BASE_URL}/static/splash.png"
					class="size-11 dark:invert p-0.5"
					alt="logo"
					draggable="false"
				/>
			</button>
		</Tooltip>
	</div>

	<div class=" -mt-1 border-[1.5px] border-gray-100 dark:border-gray-900 mx-4"></div>

	<div class="flex justify-center relative group">
		{#if selected === ''}
			<div class="absolute top-0 left-0 flex h-full">
				<div class="my-auto rounded-r-lg w-1 h-8 bg-black dark:bg-white"></div>
			</div>
		{/if}
		<button
			aria-label="Chat"
			class=" cursor-pointer bg-transparent"
			on:click={() => {
				selected = '';
			}}
		>
			<img
				src="{WEBUI_BASE_URL}/static/favicon.png"
				class="size-10 {selected === '' ? 'rounded-2xl' : 'rounded-full'}"
				alt="logo"
				draggable="false"
			/>
		</button>
	</div>

	<!-- PM Workflows -->
	<div class="flex justify-center relative group">
		{#if isWorkflowsPage}
			<div class="absolute top-0 left-0 flex h-full">
				<div class="my-auto rounded-r-lg w-1 h-8 bg-black dark:bg-white"></div>
			</div>
		{/if}
		<Tooltip content="工作流" placement="right">
			<button
				aria-label="工作流"
				class="cursor-pointer p-2.5 rounded-xl transition-all duration-200 hover:bg-gray-100 dark:hover:bg-gray-800 {isWorkflowsPage ? 'bg-gray-100 dark:bg-gray-800' : ''}"
				on:click={() => goto('/workflows')}
			>
				<svg class="size-6 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12a7.5 7.5 0 0015 0m-15 0a7.5 7.5 0 1115 0m-15 0H3m18 0h-1.5M5.25 17.25l1.5-1.5m12 0l1.5 1.5M5.25 6.75l1.5 1.5m12 0l1.5-1.5" />
				</svg>
			</button>
		</Tooltip>
	</div>

	<!-- PM Workspace -->
	<div class="flex justify-center relative group">
		{#if isPmPage}
			<div class="absolute top-0 left-0 flex h-full">
				<div class="my-auto rounded-r-lg w-1 h-8 bg-black dark:bg-white"></div>
			</div>
		{/if}
		<Tooltip content="PM 工作台" placement="right">
			<button
				aria-label="PM 工作台"
				class="cursor-pointer p-2.5 rounded-xl transition-all duration-200 hover:bg-gray-100 dark:hover:bg-gray-800 {isPmPage ? 'bg-gray-100 dark:bg-gray-800' : ''}"
				on:click={() => goto('/pm')}
			>
				<svg class="size-6 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
				</svg>
			</button>
		</Tooltip>
	</div>

	<!-- <div class="flex justify-center relative group text-gray-400">
		<button class=" cursor-pointer p-2" on:click={() => {}}>
			<Plus className="size-4" strokeWidth="2" />
		</button>
	</div> -->
</nav>
