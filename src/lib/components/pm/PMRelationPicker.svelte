<script lang="ts">
	import { writable } from 'svelte/store';
	import type { ModuleEntry, ModuleType } from '$lib/apis/pm/types';

	// Props
	interface Props {
		targetModuleType: ModuleType;
		projectId: string;
		selectedId?: string | null;
		placeholder?: string;
		onSelect?: (item: ModuleEntry) => void;
		onClear?: () => void;
	}

	let {
		targetModuleType,
		projectId,
		selectedId = null,
		placeholder = '选择关联条目...',
		onSelect,
		onClear
	}: Props = $props();

	// Mock data - replace with actual API call
	let items = writable<ModuleEntry[]>([]);
	let isOpen = $state(false);
	let searchQuery = $state('');
	let loading = $state(false);

	// Module type labels
	const moduleLabels: Record<ModuleType, string> = {
		prd: 'PRD文档',
		requirement: '需求',
		parameter: '参数',
		testcase: '测试用例',
		risk: '风险',
		competitor: '竞品',
		roadmap: '路线图',
		meeting: '会议',
		acceptance: '验收',
		faq: 'FAQ',
		'product-architecture': '产品架构',
		prototype: '原型',
		schedule: '排期',
		'requirement-boundary': '需求边界',
		spec: 'SPEC规范',
		flowchart: '流程图',
		architecture: '产品架构'
	};

	// Filtered items based on search
	let filteredItems = $derived(
		$items.filter(item =>
			item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
			item.id.toLowerCase().includes(searchQuery.toLowerCase())
		)
	);

	// Selected item
	let selectedItem = $derived($items.find(item => item.id === selectedId));

	// Load items from API
	async function loadItems() {
		loading = true;
		try {
			// TODO: Replace with actual API call
			// const response = await getModuleList(projectId, targetModuleType);
			// items.set(response.data?.items || []);

			// Mock data for now
			items.set([
				{
					id: '1',
					projectId,
					moduleType: targetModuleType,
					title: '示例条目 1',
					status: 'draft',
					createdAt: Date.now(),
					updatedAt: Date.now(),
					version: 1
				},
				{
					id: '2',
					projectId,
					moduleType: targetModuleType,
					title: '示例条目 2',
					status: 'approved',
					createdAt: Date.now(),
					updatedAt: Date.now(),
					version: 1
				}
			]);
		} finally {
			loading = false;
		}
	}

	function handleOpen() {
		isOpen = true;
		loadItems();
	}

	function handleClose() {
		isOpen = false;
		searchQuery = '';
	}

	function handleSelect(item: ModuleEntry) {
		onSelect?.(item);
		handleClose();
	}

	function handleClear() {
		onClear?.();
	}
</script>

<div class="pm-relation-picker relative">
	<!-- Trigger Button -->
	{#if selectedItem}
		<div class="flex items-center gap-2">
			<div class="flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg">
				<span class="text-xs text-blue-600 dark:text-blue-400 font-medium">{moduleLabels[targetModuleType]}</span>
				<span class="text-sm text-gray-900 dark:text-gray-100">{selectedItem.title}</span>
				<button
					class="ml-1 p-0.5 text-gray-400 hover:text-red-500 dark:hover:text-red-400 rounded transition-colors"
					onclick={handleClear}
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
		</div>
	{:else}
		<button
			class="w-full flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-500 dark:text-gray-400 hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
			onclick={handleOpen}
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
			</svg>
			{placeholder}
		</button>
	{/if}

	<!-- Dropdown -->
	{#if isOpen}
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="fixed inset-0 z-50"
			onclick={handleClose}
		>
			<div
				class="absolute z-50 w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
				style="top: 100%; left: 0; margin-top: 4px;"
				onclick={(e) => e.stopPropagation()}
			>
				<!-- Header -->
				<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
					<div class="flex items-center justify-between mb-2">
						<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
							选择{moduleLabels[targetModuleType]}
						</h3>
						<button
							class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
							onclick={handleClose}
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					<!-- Search -->
					<div class="relative">
						<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<input
							type="text"
							class="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="搜索..."
							bind:value={searchQuery}
						/>
					</div>
				</div>

				<!-- Item List -->
				<div class="max-h-80 overflow-y-auto">
					{#if loading}
						<div class="flex items-center justify-center py-8">
							<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
						</div>
					{:else if filteredItems.length === 0}
						<div class="text-center py-8">
							<svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
							</svg>
							<p class="text-sm text-gray-500 dark:text-gray-400">没有找到匹配的条目</p>
						</div>
					{:else}
						<div class="divide-y divide-gray-100 dark:divide-gray-700">
							{#each filteredItems as item (item.id)}
								<button
									class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors {selectedId === item.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
									onclick={() => handleSelect(item)}
								>
									<div class="flex-shrink-0">
										<div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
											<svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
											</svg>
										</div>
									</div>
									<div class="flex-1 min-w-0">
										<p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
											{item.title}
										</p>
										<p class="text-xs text-gray-500 dark:text-gray-400">
											{item.id} · {new Date(item.updatedAt * 1000).toLocaleDateString('zh-CN')}
										</p>
									</div>
									{#if selectedId === item.id}
										<svg class="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
										</svg>
									{/if}
								</button>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
