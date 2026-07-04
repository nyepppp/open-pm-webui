<script lang="ts">
	import { GLOSSARY_DATA } from './specTemplates';

	interface Props {
		visible?: boolean;
		editor?: any;
		onToggle?: () => void;
	}

	let { visible = false, editor, onToggle }: Props = $props();

	type GlossaryTab = 'layout' | 'typography' | 'color';
	let activeTab = $state<GlossaryTab>('layout');

	const tabs: { id: GlossaryTab; label: string }[] = [
		{ id: 'layout', label: '布局排版' },
		{ id: 'typography', label: '文字排版' },
		{ id: 'color', label: '色彩系统' }
	];

	let currentTerms = $derived(GLOSSARY_DATA[activeTab] || []);

	function insertTerm(term: string, termEn: string, definition: string) {
		if (!editor) return;
		const html = `<p><strong>${term} (${termEn})</strong>：${definition}</p>`;
		editor.chain().focus().insertContent(html).run();
	}
</script>

{#if visible}
	<div class="flex flex-col h-full w-[280px] border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex-shrink-0 transition-all duration-200">
		<!-- Header with toggle -->
		<div class="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700">
			<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">术语参考</h3>
			<button
				class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
				onclick={() => onToggle?.()}
				title="收起面板"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
				</svg>
			</button>
		</div>

		<!-- Tabs -->
		<div class="flex border-b border-gray-200 dark:border-gray-700">
			{#each tabs as tab (tab.id)}
				<button
					class="flex-1 px-2 py-2 text-xs font-medium transition {activeTab === tab.id
						? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
						: 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}"
					onclick={() => { activeTab = tab.id; }}
				>
					{tab.label}
				</button>
			{/each}
		</div>

		<!-- Terms list -->
		<div class="flex-1 overflow-y-auto">
			{#each currentTerms as item (item.termEn)}
				<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
				<div class="group px-3 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800 last:border-b-0">
					<div class="flex items-start justify-between gap-1">
						<div class="flex-1 min-w-0">
							<div class="text-sm font-medium text-gray-800 dark:text-gray-200">
								{item.term} <span class="text-xs text-gray-400 dark:text-gray-500 font-normal">({item.termEn})</span>
							</div>
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{item.definition}</p>
						</div>
						<button
							class="flex-shrink-0 mt-0.5 px-1.5 py-0.5 text-[10px] font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded opacity-0 group-hover:opacity-100 transition-opacity hover:bg-blue-100 dark:hover:bg-blue-900/40"
							onclick={() => insertTerm(item.term, item.termEn, item.definition)}
						>
							插入
						</button>
					</div>
				</div>
			{/each}
		</div>

		<!-- Footer hint -->
		<div class="px-3 py-2 text-[10px] text-gray-400 dark:text-gray-500 border-t border-gray-200 dark:border-gray-700">
			点击"插入"将术语添加到编辑器光标位置
		</div>
	</div>
{:else}
	<!-- Collapsed toggle button -->
	<button
		class="flex-shrink-0 w-8 h-full flex items-center justify-center border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
		onclick={() => onToggle?.()}
		title="展开术语参考"
	>
		<span class="writing-mode-vertical text-xs text-gray-400 dark:text-gray-500 font-medium" style="writing-mode: vertical-rl; letter-spacing: 2px;">术语</span>
	</button>
{/if}
