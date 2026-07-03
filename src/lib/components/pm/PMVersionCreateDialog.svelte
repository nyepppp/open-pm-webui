<script lang="ts">
	import { createVersion } from '$lib/apis/pm/version';
	import type { Version } from '$lib/apis/pm/types';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		onCreate?: (version: Partial<Version>) => void;
		projectId?: string;
	}

	let { isOpen = false, onClose, onCreate, projectId = '' }: Props = $props();

	let versionNumber = $state('');
	let label = $state<'milestone' | 'release' | 'review'>('milestone');
	let description = $state('');
	let changedModules = $state<string[]>([]);
	let isSubmitting = $state(false);
	let error = $state('');

	const labelOptions = [
		{ value: 'milestone', label: '里程碑' },
		{ value: 'release', label: '发布' },
		{ value: 'review', label: '评审' }
	] as const;

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

	function handleSubmit() {
		if (!versionNumber.trim()) {
			error = '请输入版本号';
			return;
		}

		isSubmitting = true;
		error = '';

		const versionData: Partial<Version> = {
			versionNumber: versionNumber.trim(),
			label,
			description: description.trim(),
			snapshotPath: `/snapshots/${versionNumber.trim()}`,
			createdAt: Date.now()
		};

		onCreate?.(versionData);
		resetForm();
	}

	function resetForm() {
		versionNumber = '';
		label = 'milestone';
		description = '';
		changedModules = [];
		error = '';
		isSubmitting = false;
	}

	function toggleModule(moduleId: string) {
		changedModules = changedModules.includes(moduleId)
			? changedModules.filter(m => m !== moduleId)
			: [...changedModules, moduleId];
	}

	function handleClose() {
		resetForm();
		onClose?.();
	}
</script>

{#if isOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={handleClose}
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
					创建新版本
				</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					创建项目快照，记录当前状态
				</p>
			</div>

			<!-- Form -->
			<div class="flex-1 overflow-y-auto p-6 space-y-6">
				<!-- Version Number -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
						版本号 <span class="text-red-500">*</span>
					</label>
					<input
						type="text"
						class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
						placeholder="如：v1.0"
						bind:value={versionNumber}
					/>
				</div>

				<!-- Label -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
						标签
					</label>
					<div class="flex gap-2">
						{#each labelOptions as option}
							<button
								class="flex-1 px-4 py-2 text-sm rounded-lg border transition-colors"
								class:bg-blue-600={label === option.value}
								class:text-white={label === option.value}
								class:border-blue-600={label === option.value}
								class:bg-white={label !== option.value}
								class:dark:bg-gray-800={label !== option.value}
								class:text-gray-700={label !== option.value}
								class:dark:text-gray-300={label !== option.value}
								class:border-gray-300={label !== option.value}
								class:dark:border-gray-600={label !== option.value}
								class:hover:bg-gray-50={label !== option.value}
								class:dark:hover:bg-gray-700={label !== option.value}
								onclick={() => label = option.value}
							>
								{option.label}
							</button>
						{/each}
						</div>
					</div>

				<!-- Description -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
						描述
					</label>
					<textarea
						class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-y"
						placeholder="描述此版本的主要变更..."
						rows={3}
						bind:value={description}
					></textarea>
				</div>

				<!-- Changed Modules -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
						变更模块（可选）
					</label>
					<div class="grid grid-cols-2 gap-2">
						{#each moduleOptions as mod}
							<label class="flex items-center gap-2 p-2 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
								<input
									type="checkbox"
									class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
									checked={changedModules.includes(mod.id)}
									onchange={() => toggleModule(mod.id)}
								/>
								<span class="text-sm text-gray-700 dark:text-gray-300">{mod.label}</span>
							</label>
						{/each}
					</div>
				</div>

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
					onclick={handleClose}
				>
					取消
				</button>
				<button
					class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					onclick={handleSubmit}
					disabled={isSubmitting}
				>
					{#if isSubmitting}
						<div class="flex items-center gap-2">
							<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
							创建中...
						</div>
					{:else}
						创建版本
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
