<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	/**
	 * PMVirtualList — Virtual scrolling for large lists (1000+ rows)
	 *
	 * Only renders items visible in the viewport + a small overscan buffer,
	 * keeping DOM size constant regardless of total item count.
	 *
	 * Usage:
	 *   <PMVirtualList
	 *     items={myItems}
	 *     itemHeight={48}
	 *     overscan={5}
	 *     let:item
	 *     let:index
	 *   >
	 *     <div>{index}: {item.name}</div>
	 *   </PMVirtualList>
	 */

	interface Props {
		/** Full list of items to render */
		items: unknown[];
		/** Fixed height per item in pixels */
		itemHeight: number;
		/** Number of extra items to render above/below viewport (default: 5) */
		overscan?: number;
		/** Container height in pixels (default: 400) */
		containerHeight?: number;
		/** CSS class for the outer container */
		class?: string;
	}

	let {
		items = [],
		itemHeight = 48,
		overscan = 5,
		containerHeight = 400,
		class: className = ''
	}: Props = $props();

	let viewportEl: HTMLDivElement | null = $state(null);
	let scrollTop = $state(0);

	// Total height of all items (scrollable area)
	let totalHeight = $derived(items.length * itemHeight);

	// Calculate visible range
	let startIndex = $derived(() => {
		const rawStart = Math.floor(scrollTop / itemHeight) - overscan;
		return Math.max(0, rawStart);
	});

	let endIndex = $derived(() => {
		const visibleCount = Math.ceil(containerHeight / itemHeight);
		const rawEnd = Math.floor(scrollTop / itemHeight) + visibleCount + overscan;
		return Math.min(items.length, rawEnd);
	});

	// Visible items slice
	let visibleItems = $derived(
		items.slice(startIndex(), endIndex()).map((item, i) => ({
			item,
			index: startIndex() + i
		}))
	);

	// Offset to position visible items correctly
	let offsetY = $derived(startIndex() * itemHeight);

	function handleScroll() {
		if (viewportEl) {
			scrollTop = viewportEl.scrollTop;
		}
	}

	// Scroll to a specific index
	export function scrollToIndex(index: number, behavior: ScrollBehavior = 'auto') {
		if (viewportEl) {
			const top = Math.max(0, index * itemHeight - containerHeight / 2);
			viewportEl.scrollTo({ top, behavior });
		}
	}
</script>

<div
	bind:this={viewportEl}
	class="pm-virtual-list overflow-y-auto {className}"
	style="height: {containerHeight}px;"
	onscroll={handleScroll}
	role="list"
	aria-label="可滚动列表"
>
	<div style="height: {totalHeight}px; position: relative;">
		<div style="position: absolute; top: {offsetY}px; left: 0; right: 0;">
			{#each visibleItems as { item, index } (index)}
				<div
					style="height: {itemHeight}px;"
					role="listitem"
					aria-rowindex={index + 1}
				>
					{@render children?.({ item, index })}
				</div>
			{/each}
		</div>
	</div>
</div>
