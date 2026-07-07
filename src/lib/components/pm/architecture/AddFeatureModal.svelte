<script lang="ts">
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import type { Parameter } from '$lib/apis/pm/types';

	interface Props {
		show: boolean;
		moduleName: string;
		onClose: () => void;
		onSubmit: (featureName: string, parameters: Parameter[]) => void;
	}

	let { show = false, moduleName = '', onClose, onSubmit }: Props = $props();

	let featureName = $state('');
	let parameters = $state<Parameter[]>([]);
	let isSubmitting = $state(false);

	function addParameter() {
		parameters = [...parameters, {
			key: '',
			paramType: 'input',
			dataType: 'string',
			required: 0,
			defaultValue: '',
			description: ''
		}];
	}

	function removeParameter(index: number) {
		parameters = parameters.filter((_, i) => i !== index);
	}

	function handleSubmit() {
		if (!featureName.trim()) {
			toast.error('请输入功能名称');
			return;
		}

		// Validate parameter keys
		const validParams = parameters.filter(p => p.key.trim());
		if (validParams.length !== parameters.length) {
			toast.error('请填写所有参数名称或删除空参数');
			return;
		}

		isSubmitting = true;
		try {
			onSubmit(featureName.trim(), validParams);
			featureName = '';
			parameters = [];
		} catch (e: any) {
			toast.error(e.message || '添加功能失败');
		} finally {
			isSubmitting = false;
		}
	}

	function handleClose() {
		featureName = '';
		parameters = [];
		onClose();
	}

	// Initialize with one empty parameter row
	$effect(() => {
		if (show && parameters.length === 0) {
			addParameter();
		}
	});
</script>

<Modal bind:show size="md">
	<div class="p-6">
		<!-- Header -->
		<div class="flex items-center justify-between mb-6">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
				添加功能 - {moduleName}
			</h3>
			<button
				class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
				onclick={handleClose}
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Feature Name -->
		<div class="mb-4">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
				功能名称 <span class="text-red-500">*</span>
			</label>
			<input
				type="text"
				class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
				placeholder="请输入功能名称"
				bind:value={featureName}
				onkeydown={(e) => e.key === 'Enter' && handleSubmit()}
			/>
		</div>

		<!-- Parameters Section -->
		<div class="mb-4">
			<div class="flex items-center justify-between mb-3">
				<label class="text-sm font-medium text-gray-700 dark:text-gray-300">
					参数列表
				</label>
				<button
					class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
					onclick={addParameter}
				>
					+ 添加参数
				</button>
			</div>

			{#if parameters.length > 0}
				<div class="space-y-2">
					{#each parameters as param, index}
						<div class="flex items-start gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
							<div class="flex-1 grid grid-cols-2 gap-2">
								<div>
									<label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">参数名 *</label>
									<input
										type="text"
										class="w-full px-2 py-1.5 text-xs border rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
										placeholder="参数名"
										bind:value={param.key}
									/>
								</div>
								<div>
									<label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">类型</label>
									<select
										class="w-full px-2 py-1.5 text-xs border rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
										bind:value={param.dataType}
									>
										<option value="string">string</option>
										<option value="number">number</option>
										<option value="boolean">boolean</option>
										<option value="object">object</option>
										<option value="array">array</option>
									</select>
								</div>
								<div>
									<label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">描述</label>
									<input
										type="text"
										class="w-full px-2 py-1.5 text-xs border rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
										placeholder="参数描述"
										bind:value={param.description}
									/>
								</div>
								<div>
									<label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">默认值</label>
									<input
										type="text"
										class="w-full px-2 py-1.5 text-xs border rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
										placeholder="默认值"
										bind:value={param.defaultValue}
									/>
								</div>
							</div>
							<button
								class="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors mt-4"
								onclick={() => removeParameter(index)}
								title="删除参数"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
							</button>
						</div>
					{/each}
				</div>
			{:else}
				<div class="text-center py-4 text-sm text-gray-400 dark:text-gray-500">
					暂无参数，点击"添加参数"开始
				</div>
			{/if}
		</div>

		<!-- Actions -->
		<div class="flex justify-end gap-3">
			<button
				class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
				onclick={handleClose}
			>
				取消
			</button>
			<button
				class="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
				onclick={handleSubmit}
				disabled={isSubmitting || !featureName.trim()}
			>
				{isSubmitting ? '添加中...' : '确认添加'}
			</button>
		</div>
	</div>
</Modal>
