<script lang="ts">
	import type { ModuleEntry, ModuleType, EntryAnnotation } from '$lib/apis/pm/types';
	import { getEntries } from '$lib/apis/pm/index';

	interface Props {
		projectId: string;
		token: string;
		annotation?: EntryAnnotation;
		onConfirm: (data: {
			linkedEntries: string[];
			boundary?: string;
			elementRef?: { componentName?: string; selector?: string };
		}) => void;
		onCancel: () => void;
	}

	let { projectId, token, annotation, onConfirm, onCancel }: Props = $props();

	let searchQuery = $state('');
	let selectedEntries = $state<string[]>(annotation?.linkedEntries || []);
	let boundaryInput = $state(annotation?.boundary || '');
	let componentNameInput = $state(annotation?.elementRef?.componentName || '');
	let loading = $state(false);
	let entryMap = $state<Map<string, ModuleEntry>>(new Map());
	let entriesByModule = $state<Map<ModuleType, ModuleEntry[]>>(new Map());
	let boundarySuggestions = $state<string[]>([]);

	const linkableModules: ModuleType[] = ['requirement', 'spec', 'parameter', 'prd'];

	async function loadEntries() {
		loading = true;
		try {
			const newMap = new Map<string, ModuleEntry>();
			const newByModule = new Map<ModuleType, ModuleEntry[]>();
			const boundaries = new Set<string>();

			for (const mod of linkableModules) {
				const entries = await getEntries(token, projectId, mod);
				const filtered = Array.isArray(entries) ? entries : [];
				newByModule.set(mod, filtered);
				for (const e of filtered) {
					newMap.set(e.id, e);
					// Extract boundaries from existing annotations
					const entryAnnotations = (e.data || e.metadata || {})?.annotations;
					if (Array.isArray(entryAnnotations)) {
						for (const a of entryAnnotations) {
							if (a.boundary) boundaries.add(a.boundary);
						}
					}
				}
			}
			entryMap = newMap;
			entriesByModule = newByModule;
			boundarySuggestions = [...boundaries].sort();
		} catch (e) {
			console.warn('[PMAnnotationLinkDialog] Failed to load entries:', e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		loadEntries();
	});

	function toggleEntry(id: string) {
		if (selectedEntries.includes(id)) {
			selectedEntries = selectedEntries.filter((e) => e !== id);
		} else {
			selectedEntries = [...selectedEntries, id];
		}
	}

	function handleConfirm() {
		onConfirm({
			linkedEntries: selectedEntries,
			boundary: boundaryInput.trim() || undefined,
			elementRef: componentNameInput.trim()
				? { componentName: componentNameInput.trim() }
				: undefined
		});
	}

	let filteredEntriesByModule = $derived.by(() => {
		const result = new Map<ModuleType, ModuleEntry[]>();
		for (const [mod, entries] of entriesByModule) {
			const filtered = entries.filter(
				(e) =>
					!searchQuery ||
					e.title.toLowerCase().includes(searchQuery.toLowerCase())
			);
			if (filtered.length > 0) {
				result.set(mod, filtered);
			}
		}
		return result;
	});

	function getModuleLabel(mod: ModuleType): string {
		const labels: Record<string, string> = {
			requirement: '需求',
			spec: '规格',
			parameter: '参数',
			prd: 'PRD'
		};
		return labels[mod] || mod;
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
	role="dialog"
	aria-modal="true"
	onclick={onCancel}
>
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col"
		onclick={(e) => e.stopPropagation()}
	>
		<!-- Header -->
		<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
				{annotation ? '编辑批注关联' : '关联批注'}
			</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
				选择要关联的需求、规格或参数条目
			</p>
		</div>

		<!-- Body -->
		<div class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
			<!-- Search -->
			<input
				type="text"
				placeholder="搜索条目..."
				class="w-full rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				bind:value={searchQuery}
			/>

			<!-- Entry List -->
			{#if loading}
				<div class="text-center py-8 text-sm text-gray-400">加载中...</div>
			{:else if filteredEntriesByModule.size === 0}
				<div class="text-center py-8 text-sm text-gray-400">未找到匹配条目</div>
			{:else}
				{#each filteredEntriesByModule as [mod, entries]}
					<div>
						<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
							{getModuleLabel(mod)} ({entries.length})
						</h4>
						<div class="space-y-1 max-h-40 overflow-y-auto">
							{#each entries as entry}
								<button
									class="w-full text-left px-3 py-2 rounded-xl text-sm transition-colors {selectedEntries.includes(entry.id)
										? 'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-300 dark:ring-blue-700'
										: 'hover:bg-gray-50 dark:hover:bg-gray-800'}"
									onclick={() => toggleEntry(entry.id)}
								>
									<div class="flex items-center gap-2">
										<div class="w-4 h-4 rounded border {selectedEntries.includes(entry.id) ? 'bg-blue-500 border-blue-500' : 'border-gray-300 dark:border-gray-600'} flex items-center justify-center">
											{#if selectedEntries.includes(entry.id)}
												<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="3">
													<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
												</svg>
											{/if}
										</div>
										<span class="text-gray-800 dark:text-gray-200 truncate">{entry.title}</span>
									</div>
								</button>
							{/each}
						</div>
					</div>
				{/each}
			{/if}

			<!-- Boundary Input -->
			<div>
				<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1" for="boundary-input">功能边界</label>
				<input
					id="boundary-input"
					type="text"
					placeholder="例如：用户管理、支付流程"
					list="boundary-suggestions"
					class="w-full rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
					bind:value={boundaryInput}
				/>
				<datalist id="boundary-suggestions">
					{#each boundarySuggestions as s}
						<option value={s} />
					{/each}
				</datalist>
			</div>

			<!-- Component Name -->
			<div>
				<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1" for="component-input">组件名称</label>
				<input
					id="component-input"
					type="text"
					placeholder="例如：LoginForm、CartButton"
					class="w-full rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
					bind:value={componentNameInput}
				/>
			</div>
		</div>

		<!-- Footer -->
		<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
			<button
				class="px-4 py-2 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
				onclick={onCancel}
			>
				取消
			</button>
			<button
				class="px-4 py-2 rounded-xl bg-black text-white dark:bg-white dark:text-black text-sm font-medium hover:opacity-90 transition-opacity"
				onclick={handleConfirm}
			>
				确认关联
			</button>
		</div>
	</div>
</div>
