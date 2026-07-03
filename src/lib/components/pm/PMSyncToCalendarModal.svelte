<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { getCalendars } from '$lib/apis/calendar';
	import type { CalendarModel } from '$lib/apis/calendar';

	export let show = false;
	export let entryTitle = '';

	const dispatch = createEventDispatcher();

	let calendars: CalendarModel[] = [];
	let selectedCalendarId = '';
	let loading = false;
	let loaded = false;

	async function loadCalendars() {
		try {
			calendars = (await getCalendars(localStorage.token)) ?? [];
			const defaultCal = calendars.find((c) => c.is_default);
			selectedCalendarId = defaultCal?.id || calendars[0]?.id || '';
			loaded = true;
		} catch (err) {
			toast.error('加载日历失败');
			calendars = [];
		}
	}

	function handleSelect(calendarId: string) {
		selectedCalendarId = calendarId;
	}

	function handleSync() {
		if (!selectedCalendarId) {
			toast.error('请选择日历');
			return;
		}
		dispatch('sync', { calendarId: selectedCalendarId });
	}

	$: if (show && !loaded) {
		loadCalendars();
	}
</script>

<Modal size="sm" bind:show>
	<div class="flex flex-col">
		<div class="px-5 pt-4 pb-2">
			<h3 class="text-base font-medium">同步到日历</h3>
			<p class="text-sm text-gray-500 mt-1 truncate">{entryTitle}</p>
		</div>

		<div class="px-5 py-2">
			{#if !loaded}
				<div class="flex justify-center py-4">
					<Spinner className="size-5" />
				</div>
			{:else if calendars.length === 0}
				<div class="text-center py-4 text-sm text-gray-500">
					<p>您还没有日历</p>
					<p class="text-xs mt-1">请先创建日历后再同步</p>
				</div>
			{:else}
				<div class="space-y-1">
					{#each calendars as calendar (calendar.id)}
						<button
							class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition {selectedCalendarId === calendar.id ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' : 'hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent'}"
							on:click={() => handleSelect(calendar.id)}
						>
							<div
								class="w-3 h-3 rounded-full shrink-0"
								style="background-color: {calendar.color || '#3b82f6'}"
							/>
							<span class="text-sm flex-1 truncate">{calendar.name}</span>
							{#if calendar.is_default}
								<span class="text-xs text-gray-400">默认</span>
							{/if}
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<div class="flex items-center justify-end gap-2 px-5 pb-4 pt-2">
			<button
				class="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 transition"
				on:click={() => (show = false)}
			>
				取消
			</button>
			<button
				class="px-4 py-1.5 text-sm bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex items-center gap-2 {loading || !selectedCalendarId ? 'opacity-50 cursor-not-allowed' : ''}"
				on:click={handleSync}
				disabled={loading || !selectedCalendarId}
			>
				{#if loading}
					<Spinner className="size-4" />
				{/if}
				同步
			</button>
		</div>
	</div>
</Modal>
