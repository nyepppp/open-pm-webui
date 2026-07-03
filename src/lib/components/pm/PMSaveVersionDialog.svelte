<script lang="ts">
	interface Props {
		open: boolean;
		currentVersionNumber: string;
		onClose: () => void;
		onSaveNewVersion: () => void;
		onSaveContentOnly: () => void;
	}

	let { open, currentVersionNumber, onClose, onSaveNewVersion, onSaveContentOnly }: Props = $props();

	function getNextVersion(current: string): string {
		const match = current.match(/^v?(\d+)\.(\d+)$/);
		if (match) {
			const major = parseInt(match[1], 10);
			const minor = parseInt(match[2], 10);
			return `v${major}.${minor + 1}`;
		}
		return current;
	}

	let nextVersion = $derived(getNextVersion(currentVersionNumber));
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={onClose}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
							<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
							</svg>
						</div>
						<div>
							<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
								是否创建新版本？
							</h2>
							<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
								保存时可以选择版本管理方式
							</p>
						</div>
					</div>
					<button
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
						onclick={onClose}
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			</div>

			<!-- Content -->
			<div class="p-6 space-y-4">
				<!-- Version display -->
				<div class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
					<div class="flex-1">
						<div class="text-xs text-gray-500 dark:text-gray-400">当前版本</div>
						<div class="text-sm font-medium text-gray-700 dark:text-gray-300">{currentVersionNumber}</div>
					</div>
					<svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
					<div class="flex-1">
						<div class="text-xs text-blue-500 dark:text-blue-400">新版本</div>
						<div class="text-sm font-medium text-blue-700 dark:text-blue-300">{nextVersion}</div>
					</div>
				</div>

				<!-- Description -->
				<p class="text-sm text-gray-600 dark:text-gray-400">
					创建新版本会在版本历史中记录本次修改，仅保存内容则只更新当前版本的内容不递增版本号
				</p>
			</div>

			<!-- Actions -->
			<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
				<button
					class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
					onclick={onSaveContentOnly}
				>
					仅保存内容
				</button>
				<button
					class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white rounded-lg transition-colors"
					onclick={onSaveNewVersion}
				>
					创建新版本
				</button>
			</div>
		</div>
	</div>
{/if}
