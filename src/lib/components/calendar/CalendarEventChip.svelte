<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { CalendarEventModel } from '$lib/apis/calendar';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let event: CalendarEventModel;
	export let calendarColor: string | null = null;

	const dispatch = createEventDispatcher();

	// Module type labels and colors
	const moduleLabels: Record<string, string> = {
		roadmap: '路线图',
		schedule: '排期'
	};

	const moduleColors: Record<string, string> = {
		roadmap: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
		schedule: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
	};

	$: moduleType = event.meta?.module_type as string | undefined;
	$: moduleLabel = moduleType ? moduleLabels[moduleType] : null;
	$: moduleBadgeClass = moduleType ? moduleColors[moduleType] : '';
	$: versionNumber = event.meta?.version_number as string | undefined;
</script>

<Tooltip content="{event.title}{event.location ? ` · ${event.location}` : ''}{versionNumber ? ` · ${versionNumber}` : ''}">
	<button
		class="w-full text-left text-xs flex items-start gap-1.5 py-[1px] px-0.5 rounded-md
			{event.meta?.automation_id ? 'opacity-60' : ''}
			hover:bg-gray-50 dark:hover:bg-gray-800/50 transition truncate"
		on:click|stopPropagation={() => dispatch('click', event)}
	>
		<span
			class="shrink-0 size-[7px] rounded-full mt-[5px]"
			style="background-color: {event.color || calendarColor || '#3b82f6'};"
		></span>
		<span class="truncate flex items-center gap-1">
			{#if !event.all_day}<span class="text-gray-500 dark:text-gray-400"
					>{new Date(event.start_at / 1_000_000)
						.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
						.replace(' ', '')}</span
				>{/if}
			{#if moduleLabel}
				<span class="shrink-0 px-1 py-[1px] rounded text-[10px] font-medium {moduleBadgeClass}">
					{moduleLabel}
				</span>
			{/if}
			<span class="truncate">{event.title}</span>
			{#if versionNumber}
				<span class="shrink-0 text-[10px] text-gray-400 dark:text-gray-500">({versionNumber})</span>
			{/if}
		</span>
	</button>
</Tooltip>
