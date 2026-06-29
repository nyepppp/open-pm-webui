<script lang="ts">
	import { goto } from '$app/navigation';
	import type { ModuleType } from '$lib/apis/pm/types';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		onConfirm?: (action: 'save' | 'discard' | 'cancel') => void;
		moduleType?: ModuleType;
	}

	let { isOpen = false, onClose, onConfirm, moduleType }: Props = $props();

	function handleSave() {
		onConfirm?.('save');
		onClose?.();
	}

	function handleDiscard() {
		onConfirm?.('discard');
		onClose?.();
	}

	function handleCancel() {
		onConfirm?.('cancel');
		onClose?.();
	}

	const moduleNames: Record<string, string> = {
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
		'product-architecture': '产品架构'
	};
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={handleCancel}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center gap-3">
					<div class="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center flex-shrink-0">
						<svg class="w-5 h-5 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
						</svg>
					</div>
					<div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
							未保存的更改
						</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
							当前{moduleType ? `「${moduleNames[moduleType] || moduleType}」` : ''}有未保存的更改
						</p>
					</div>
				</div>
			</div>

			<!-- Content -->
			<div class="p-6">
				<p class="text-sm text-gray-600 dark:text-gray-400">
					切换版本前，您可以选择保存当前更改或放弃更改。如果不保存，当前编辑的内容将会丢失。
				</p>
			</div>

			<!-- Actions -->
			<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
				<button
					class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
					onclick={handleCancel}
				>
					取消
				</button>
				<button
					class="px-4 py-2 text-sm text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors border border-red-200 dark:border-red-800"
					onclick={handleDiscard}
				>
					放弃更改
				</button>
				<button
					class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white rounded-lg transition-colors"
					onclick={handleSave}
				>
					保存并切换
				</button>
			</div>
		</div>
	</div>
{/if}
