<script lang="ts">
	import { rollbackVersion } from '$lib/apis/pm/version';
	import type { Version } from '$lib/apis/pm/types';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		onRollback?: (version: Version, scope: 'project' | 'module', moduleType?: string) => void;
		version?: Version;
		projectId?: string;
	}

	let { isOpen = false, onClose, onRollback, version, projectId = '' }: Props = $props();

	let scope = $state<'project' | 'module'>('project');
	let selectedModuleType = $state('');
	let isSubmitting = $state(false);
	let error = $state('');

	const moduleOptions = [
		{ id: 'prd', label: 'PRD' },
		{ id: 'requirement', label: '需求' },
		{ id: 'parameter', label: '参数' },
		{ id: 'testcase', label: '测试用例' },
		{ id: 'risk', label: '风险' },
		{ id: 'competitor', label: '竞品' },
		{ id: 'roadmap', label: '路线图' },
		{ id: 'meeting', label: '会议' },
		{ id: 'acceptance', label: '验收' },
		{ id: 'faq', label: 'FAQ' },
		{ id: 'product-architecture', label: '产品架构' }
	];

	async function handleRollback() {
		if (scope === 'module' && !selectedModuleType) {
			error = '请选择要回滚的模块';
			return;
		}

		isSubmitting = true;
		error = '';

		try {
			const response = await rollbackVersion(projectId, version!.id, scope, scope === 'module' ? selectedModuleType : undefined);
			if (response.success) {
				onRollback?.(version!, scope, selectedModuleType);
				resetAndClose();
			} else {
				error = response.error || '回滚失败';
			}
		} catch (e) {
			error = '回滚时出错';
		} finally {
			isSubmitting = false;
		}
	}

	function resetAndClose() {
		scope = 'project';
		selectedModuleType = '';
		error = '';
		isSubmitting = false;
		onClose?.();
	}

	function formatDate(timestamp: number): string {
		return new Date(timestamp * 1000).toLocaleDateString('zh-CN', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={resetAndClose}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center gap-3">
					<div class="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center flex-shrink-0">
						<svg class="w-5 h-5 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6v-6" />
						</svg>
					</div>
					<div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">回滚到版本</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
							回滚到 {(version?.versionNumber ?? version?.version_number) || '未知版本'} · {version ? formatDate(version.createdAt ?? version.created_at) : ''}
						</p>
					</div>
				</div>
			</div>

			<!-- Content -->
			<div class="p-6 space-y-6">
				<!-- Warning -->
				<div class="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
					<p class="text-sm text-orange-700 dark:text-orange-300">
						⚠️ 回滚操作将恢复到所选版本的状态。当前版本之后的更改将丢失。请谨慎操作。
					</p>
				</div>

				<!-- Scope Selection -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
						回滚范围
					</label>
					<div class="space-y-2">
						<label class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors {scope === 'project' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'}">
							<input type="radio" name="scope" value="project" class="w-4 h-4 text-blue-600 focus:ring-blue-500" checked={scope === 'project'} onchange={() => scope = 'project'} />
							<div>
								<div class="text-sm font-medium text-gray-900 dark:text-gray-100">整项目回滚</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">回滚所有模块到该版本状态</div>
							</div>
						</label>
						<label class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors {scope === 'module' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'}">
							<input type="radio" name="scope" value="module" class="w-4 h-4 text-blue-600 focus:ring-blue-500" checked={scope === 'module'} onchange={() => scope = 'module'} />
							<div>
								<div class="text-sm font-medium text-gray-900 dark:text-gray-100">单模块回滚</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">只回滚指定模块，其他模块保持不变</div>
							</div>
						</label>
					</div>
				</div>

				<!-- Module Selection (if scope is module) -->
				{#if scope === 'module'}
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
							选择模块 <span class="text-red-500">*</span>
						</label>
						<select
							class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
							bind:value={selectedModuleType}
						>
							<option value="" disabled>选择要回滚的模块</option>
							{#each moduleOptions as mod}
								<option value={mod.id}>{mod.label}</option>
							{/each}
						</select>
					</div>
				{/if}

				<!-- Error -->
				{#if error}
					<div class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
						{error}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
				<button
					class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
					onclick={resetAndClose}
				>
					取消
				</button>
				<button
					class="px-4 py-2 text-sm bg-orange-600 hover:bg-orange-700 dark:bg-orange-600 dark:hover:bg-orange-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					onclick={handleRollback}
					disabled={isSubmitting || (scope === 'module' && !selectedModuleType)}
				>
					{#if isSubmitting}
						<div class="flex items-center gap-2">
							<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
							回滚中...
						</div>
					{:else}
						确认回滚
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
