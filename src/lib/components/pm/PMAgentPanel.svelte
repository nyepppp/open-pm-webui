<script lang="ts">
	import { agentSuggestions, pendingSuggestions, agentLoading, agentError, confirmSuggestion, rejectSuggestion } from '$lib/stores/pm/agentStore';
	import type { AgentSuggestion } from '$lib/apis/pm/types';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		moduleId?: string;
		moduleType?: string;
		onTriggerAnalysis?: () => void;
	}

	let { isOpen = false, onClose, moduleId, moduleType, onTriggerAnalysis }: Props = $props();

	let activeTab = $state<'pending' | 'confirmed' | 'rejected'>('pending');
	let selectedSuggestion = $state<AgentSuggestion | null>(null);

	let filteredSuggestions = $derived(
		$agentSuggestions.filter(s => s.status === activeTab)
	);

	function getConfidenceColor(confidence: number): string {
		if (confidence >= 80) return 'text-green-600 dark:text-green-400';
		if (confidence >= 60) return 'text-yellow-600 dark:text-yellow-400';
		return 'text-orange-600 dark:text-orange-400';
	}

	function getTypeLabel(type: string): string {
		const labels: Record<string, string> = {
			completeness: '完整性',
			risk: '风险',
			association: '关联',
			improvement: '改进'
		};
		return labels[type] || type;
	}

	function getTypeColor(type: string): string {
		const colors: Record<string, string> = {
			completeness: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
			risk: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
			association: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
			improvement: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
		};
		return colors[type] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
	}

	function handleConfirm(suggestion: AgentSuggestion) {
		confirmSuggestion(suggestion.id);
	}

	function handleReject(suggestion: AgentSuggestion) {
		rejectSuggestion(suggestion.id);
	}

	function handleTriggerAnalysis() {
		onTriggerAnalysis?.();
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-start justify-end"
		onclick={() => onClose?.()}
		role="dialog"
		aria-modal="true"
		aria-label="AI分析建议面板"
	>
		<div
			class="bg-white dark:bg-gray-800 w-full max-w-md h-full shadow-2xl flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<div class="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center" aria-hidden="true">
							<svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
							</svg>
						</div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
							AI 分析建议
						</h2>
					</div>
					<button
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						onclick={() => onClose?.()}
						aria-label="关闭AI分析面板"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					{moduleType ? `当前模块: ${moduleType}` : ''}
					{#if $pendingSuggestions.length > 0}
						<span class="ml-2 px-2 py-0.5 text-xs bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 rounded-full">
							{$pendingSuggestions.length} 个待处理
						</span>
					{/if}
				</p>
			</div>

			<!-- Trigger Button -->
			<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
				<button
					class="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium bg-purple-600 hover:bg-purple-700 dark:bg-purple-600 dark:hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					onclick={handleTriggerAnalysis}
					disabled={$agentLoading}
					aria-label="运行AI分析"
				>
					{#if $agentLoading}
						<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" aria-hidden="true"></div>
						分析中...
					{:else}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
						</svg>
						运行 AI 分析
					{/if}
				</button>
			</div>

			<!-- Tabs -->
			<div class="flex border-b border-gray-200 dark:border-gray-700" role="tablist" aria-label="建议分类">
				{#each ['pending', 'confirmed', 'rejected'] as tab}
					<button
						class="flex-1 px-4 py-2.5 text-sm font-medium transition-colors {activeTab === tab ? 'text-purple-600 dark:text-purple-400 border-b-2 border-purple-600 dark:border-purple-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}"
						onclick={() => activeTab = tab as typeof activeTab}
						role="tab"
						aria-selected={activeTab === tab}
						aria-label="{tab === 'pending' ? '待处理' : tab === 'confirmed' ? '已采纳' : '已拒绝'}"
					>
						{tab === 'pending' ? '待处理' : tab === 'confirmed' ? '已采纳' : '已拒绝'}
						<span class="ml-1 text-xs text-gray-400 dark:text-gray-500">
							({$agentSuggestions.filter(s => s.status === tab).length})
						</span>
					</button>
				{/each}
			</div>

			<!-- Suggestions List -->
			<div class="flex-1 overflow-y-auto p-4" role="tabpanel" aria-label="建议列表">
				{#if $agentLoading && filteredSuggestions.length === 0}
					<div class="flex items-center justify-center py-12">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" aria-hidden="true"></div>
						<span class="ml-3 text-sm text-gray-500 dark:text-gray-400">分析中...</span>
					</div>
				{:else if $agentError}
					<!-- Graceful degradation: AI unavailable -->
					<div class="text-center py-8">
						<svg class="w-12 h-12 mx-auto mb-3 text-orange-300 dark:text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
						</svg>
						<p class="text-sm font-medium text-orange-600 dark:text-orange-400 mb-1">AI 分析暂时不可用</p>
						<p class="text-sm text-gray-500 dark:text-gray-400 mb-1">{$agentError}</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-2 mb-4">
							所有模块仍可手动编辑，AI 功能恢复后将自动可用。请稍后重试或检查 AI 服务配置。
						</p>
						<button
							class="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
							onclick={handleTriggerAnalysis}
							aria-label="重新尝试AI分析"
						>
							重新尝试
						</button>
					</div>
				{:else if filteredSuggestions.length === 0}
					<div class="text-center py-12">
						<svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
						</svg>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							{activeTab === 'pending' ? '暂无待处理的建议' : activeTab === 'confirmed' ? '暂无已采纳的建议' : '暂无已拒绝的建议'}
						</p>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-2">
							点击上方"运行 AI 分析"按钮获取建议
						</p>
					</div>
				{:else}
					<div class="space-y-3">
						{#each filteredSuggestions as suggestion (suggestion.id)}
							<div class="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-700">
								<div class="flex items-start gap-3">
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-2 mb-2">
											<span class="px-2 py-0.5 text-xs rounded-full {getTypeColor(suggestion.type)}">
												{getTypeLabel(suggestion.type)}
											</span>
											<span class="text-xs {getConfidenceColor(suggestion.confidence)}">
												置信度: {suggestion.confidence}%
											</span>
										</div>
										<h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
											{suggestion.title}
										</h3>
										<p class="text-xs text-gray-500 dark:text-gray-400">
											{suggestion.description}
										</p>
									</div>
								</div>

								<!-- Actions -->
								{#if suggestion.status === 'pending'}
									<div class="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
										<button
											class="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium bg-green-600 hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-500 text-white rounded-lg transition-colors"
											onclick={() => handleConfirm(suggestion)}
											aria-label="采纳建议: {suggestion.title}"
										>
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
											</svg>
											采纳
										</button>
										<button
											class="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-500 text-white rounded-lg transition-colors"
											onclick={() => handleReject(suggestion)}
											aria-label="拒绝建议: {suggestion.title}"
										>
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
											</svg>
											拒绝
										</button>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
