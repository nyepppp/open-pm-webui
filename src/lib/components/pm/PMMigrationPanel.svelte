<script lang="ts">
	import type { ModuleEntry } from '$lib/apis/pm/types';

	// Props
	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		onConfirm?: () => void;
		migratedItems?: ModuleEntry[];
		failedItems?: { item: ModuleEntry; reason: string }[];
	}

	let {
		isOpen = false,
		onClose,
		onConfirm,
		migratedItems = [],
		failedItems = []
	}: Props = $props();

	let currentStep = $state<'summary' | 'review' | 'confirm'>('summary');

	function handleConfirm() {
		onConfirm?.();
		onClose?.();
	}

	function handleSkip() {
		onClose?.();
	}

	function getStatusIcon(status: string) {
		switch (status) {
			case 'success':
				return `<svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`;
			case 'warning':
				return `<svg class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>`;
			case 'error':
				return `<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>`;
			default:
				return '';
		}
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={() => onClose?.()}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
						数据迁移
					</h2>
					<button
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						onclick={() => onClose?.()}
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					系统检测到旧格式数据，需要迁移到新格式
				</p>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto p-6">
				{#if currentStep === 'summary'}
					<!-- Summary Step -->
					<div class="space-y-6">
						<!-- Migration Stats -->
						<div class="grid grid-cols-3 gap-4">
							<div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
								<div class="text-2xl font-bold text-green-600 dark:text-green-400">
									{migratedItems.length}
								</div>
								<div class="text-sm text-green-700 dark:text-green-300 mt-1">
									迁移成功
								</div>
							</div>
							<div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
								<div class="text-2xl font-bold text-red-600 dark:text-red-400">
									{failedItems.length}
								</div>
								<div class="text-sm text-red-700 dark:text-red-300 mt-1">
									迁移失败
								</div>
							</div>
							<div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
								<div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
									{migratedItems.length + failedItems.length}
								</div>
								<div class="text-sm text-blue-700 dark:text-blue-300 mt-1">
									总计
								</div>
							</div>
						</div>

						<!-- Migration Details -->
						<div class="space-y-4">
							<h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">
								迁移详情
							</h3>

							<!-- Success Items -->
							{#if migratedItems.length > 0}
								<div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
									<h4 class="text-sm font-medium text-green-700 dark:text-green-300 mb-2 flex items-center gap-2">
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
										</svg>
										成功迁移的条目
									</h4>
									<ul class="space-y-1 text-sm text-gray-600 dark:text-gray-400">
										{#each migratedItems.slice(0, 5) as item}
											<li class="flex items-center gap-2">
												<span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
												{item.title || '未命名条目'}
											</li>
										{/each}
										{#if migratedItems.length > 5}
											<li class="text-gray-400 dark:text-gray-500">...还有 {migratedItems.length - 5} 个条目</li>
										{/if}
									</ul>
								</div>
							{/if}

							<!-- Failed Items -->
							{#if failedItems.length > 0}
								<div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
									<h4 class="text-sm font-medium text-red-700 dark:text-red-300 mb-2 flex items-center gap-2">
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
										</svg>
										迁移失败的条目
									</h4>
									<ul class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
										{#each failedItems as { item, reason }}
											<li class="flex items-start gap-2">
												<span class="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 flex-shrink-0"></span>
												<div>
													<div class="font-medium">{item.title || '未命名条目'}</div>
													<div class="text-xs text-red-500 dark:text-red-400">{reason}</div>
												</div>
											</li>
										{/each}
									</ul>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
				<button
					class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
					onclick={handleSkip}
				>
					跳过，稍后处理
				</button>
				<div class="flex items-center gap-3">
					<button
						class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
						onclick={handleSkip}
					>
						取消
					</button>
					<button
						class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white rounded-lg transition-colors"
						onclick={handleConfirm}
					>
						确认迁移
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
