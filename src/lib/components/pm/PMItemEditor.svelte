<script lang="ts">
	import type { ModuleEntry } from '$lib/apis/pm/types';

	// Props
	interface Props {
		items: ModuleEntry[];
		selectedId?: string | null;
		loading?: boolean;
		onSelect?: (item: ModuleEntry) => void;
		onCreate?: () => void;
		onDelete?: (item: ModuleEntry) => void;
	}

	let { items, selectedId = null, loading = false, onSelect, onCreate, onDelete }: Props = $props();

	// Virtual scrolling state
	const ITEM_HEIGHT = 64; // approximate height of each item row
	const OVERSCAN = 5;
	let viewportEl: HTMLDivElement | null = $state(null);
	let scrollTop = $state(0);
	let containerHeight = $state(600);

	// Threshold to switch from full render to virtual scrolling
	const VIRTUAL_THRESHOLD = 100;

	// Whether to use virtual scrolling
	let useVirtualScroll = $derived(items.length > VIRTUAL_THRESHOLD);

	// Total height of all items (scrollable area)
	let totalHeight = $derived(items.length * ITEM_HEIGHT);

	// Calculate visible range for virtual scroll
	let startIndex = $derived(() => {
		const rawStart = Math.floor(scrollTop / ITEM_HEIGHT) - OVERSCAN;
		return Math.max(0, rawStart);
	});

	let endIndex = $derived(() => {
		const visibleCount = Math.ceil(containerHeight / ITEM_HEIGHT);
		const rawEnd = Math.floor(scrollTop / ITEM_HEIGHT) + visibleCount + OVERSCAN;
		return Math.min(items.length, rawEnd);
	});

	// Visible items slice for virtual scroll
	let visibleItems = $derived(
		items.slice(startIndex(), endIndex()).map((item, i) => ({
			item,
			index: startIndex() + i
		}))
	);

	// Offset to position visible items correctly
	let offsetY = $derived(startIndex() * ITEM_HEIGHT);

	function handleVirtualScroll() {
		if (viewportEl) {
			scrollTop = viewportEl.scrollTop;
		}
	}

	// ResizeObserver to track container height
	let resizeObserver: ResizeObserver | null = null;

	$effect(() => {
		if (viewportEl) {
			resizeObserver = new ResizeObserver((entries) => {
				for (const entry of entries) {
					containerHeight = entry.contentRect.height;
				}
			});
			resizeObserver.observe(viewportEl);
		}
		return () => {
			resizeObserver?.disconnect();
		};
	});

	// Scroll to a specific item
	export function scrollToItem(index: number, behavior: ScrollBehavior = 'auto') {
		if (viewportEl) {
			const top = Math.max(0, index * ITEM_HEIGHT - containerHeight / 2);
			viewportEl.scrollTo({ top, behavior });
		}
	}

	function formatDate(timestamp: number): string {
		return new Date(timestamp * 1000).toLocaleDateString('zh-CN', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'draft': return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
			case 'review': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
			case 'approved': return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
			case 'archived': return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
			default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
		}
	}

	function getStatusLabel(status: string): string {
		switch (status) {
			case 'draft': return '草稿';
			case 'review': return '评审中';
			case 'approved': return '已批准';
			case 'archived': return '已归档';
			default: return status;
		}
	}

	function getPriorityColor(priority: string): string {
		switch (priority) {
			case 'p0': return 'text-red-600 dark:text-red-400';
			case 'p1': return 'text-orange-600 dark:text-orange-400';
			case 'p2': return 'text-yellow-600 dark:text-yellow-400';
			case 'p3': return 'text-green-600 dark:text-green-400';
			default: return 'text-gray-600 dark:text-gray-400';
		}
	}
</script>

<div class="pm-item-editor flex flex-col h-full bg-white dark:bg-gray-900">
	<!-- Header -->
	<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
			条目列表
			<span class="text-xs font-normal text-gray-500 dark:text-gray-400 ml-2">
				({items.length} 个条目)
			</span>
		</h3>
		<button
			class="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white rounded-lg transition-colors"
			onclick={() => onCreate?.()}
			aria-label="新建条目"
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			新建
		</button>
	</div>

	<!-- Item List -->
	<div class="flex-1 overflow-y-auto" bind:this={viewportEl} onscroll={handleVirtualScroll} role="list" aria-label="条目列表">
		{#if loading}
			<div class="flex items-center justify-center py-8">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
			</div>
		{:else if items.length === 0}
			<div class="text-center py-8 px-4">
				<svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
				</svg>
				<p class="text-sm text-gray-500 dark:text-gray-400">暂无条目</p>
			</div>
		{:else if useVirtualScroll}
			<!-- Virtual scrolling for 100+ items -->
			<div style="height: {totalHeight}px; position: relative;">
				<div style="position: absolute; top: {offsetY}px; left: 0; right: 0;">
					{#each visibleItems as { item, index } (item.id)}
						{@render itemRow(item, index)}
					{/each}
				</div>
			</div>
		{:else}
			<!-- Standard rendering for small lists -->
			<div class="divide-y divide-gray-100 dark:divide-gray-800">
				{#each items as item (item.id)}
					{@render itemRow(item, items.indexOf(item))}
				{/each}
			</div>
		{/if}
	</div>
</div>

{#snippet itemRow(item: ModuleEntry, index: number)}
	<div
		class="group flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 {selectedId === item.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
		style="height: {ITEM_HEIGHT}px;"
		onclick={() => onSelect?.(item)}
		role="listitem"
		aria-rowindex={index + 1}
		aria-selected={selectedId === item.id}
		tabindex="0"
		onkeydown={(e) => {
			if (e.key === 'Enter' || e.key === ' ') {
				e.preventDefault();
				onSelect?.(item);
			}
		}}
	>
		<!-- Status indicator -->
		<div class="flex-shrink-0 mt-0.5">
			<div class="w-2 h-2 rounded-full bg-blue-500"></div>
		</div>

		<!-- Content -->
		<div class="flex-1 min-w-0">
			<div class="flex items-center gap-2 mb-1">
				<h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
					{item.title || '未命名条目'}
				</h4>
				{#if item.priority}
					<span class="text-xs {getPriorityColor(item.priority)}">
						{item.priority.toUpperCase()}
					</span>
				{/if}
			</div>
			<div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
				<span class="px-1.5 py-0.5 rounded {getStatusColor(item.status)}">
					{getStatusLabel(item.status)}
				</span>
				<span>{formatDate(item.updatedAt)}</span>
			</div>
		</div>

		<!-- Delete button -->
		<button
			class="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-all"
			onclick={(e) => {
				e.stopPropagation();
				onDelete?.(item);
			}}
			title="删除"
			aria-label="删除条目 {item.title}"
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
			</svg>
		</button>
	</div>
{/snippet}
