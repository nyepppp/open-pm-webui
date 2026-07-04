<script lang="ts">
	import { SPEC_TEMPLATES, type SpecTemplate } from './specTemplates';

	interface Props {
		open?: boolean;
		onSelect?: (template: SpecTemplate | null) => void;
		onClose?: () => void;
		customTemplates?: any[];
	}

	let { open = false, onSelect, onClose, customTemplates = [] }: Props = $props();

	const allTemplates = $derived([
		...SPEC_TEMPLATES,
		...customTemplates.map((t: any) => ({
			id: t.id,
			name: t.title || t.name || '自定义模板',
			category: (t.metadata?.specCategory || 'functional') as 'functional' | 'prototype',
			content: t.content || '',
			isBuiltIn: false
		}))
	]);

	function stripHtml(html: string): string {
		return html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
	}

	function handleSelect(template: SpecTemplate | null) {
		onSelect?.(template);
		onClose?.();
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={() => onClose?.()}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div>
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">选择 SPEC 模板</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">选择一个模板快速开始，或创建空白文档</p>
				</div>
				<button
					class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					onclick={() => onClose?.()}
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Template Grid -->
			<div class="p-6 overflow-y-auto max-h-[60vh]">
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					{#each allTemplates as template (template.id)}
						<button
							class="flex flex-col items-start p-4 rounded-xl border-2 border-gray-200 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition text-left group"
							onclick={() => handleSelect(template)}
						>
							<div class="flex items-center gap-2 mb-2">
								<span class="px-2 py-0.5 text-xs font-medium rounded-full {template.category === 'functional' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'}">
									{template.category === 'functional' ? '功能 SPEC' : '前端原型 SPEC'}
								</span>
								{#if !template.isBuiltIn}
									<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">自定义</span>
								{/if}
							</div>
							<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition">
								{template.name}
							</h3>
							<p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
								{stripHtml(template.content).slice(0, 100)}
							</p>
						</button>
					{/each}

					<!-- Blank option -->
					<button
						class="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-500 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition"
						onclick={() => handleSelect(null)}
					>
						<svg class="w-8 h-8 text-gray-400 dark:text-gray-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
						</svg>
						<span class="text-sm font-medium text-gray-600 dark:text-gray-400">空白文档</span>
						<span class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">不使用模板</span>
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
