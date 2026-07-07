<script lang="ts">
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import type { ArchModule, ArchFeature, ArchParameter } from '$lib/stores/pm/architectureStore';

	interface Props {
		show: boolean;
		type: 'module' | 'feature' | 'parameter';
		data?: Partial<ArchModule> | Partial<ArchFeature> | Partial<ArchParameter>;
		onClose: () => void;
		onSubmit: (data: any) => void;
	}

	let { show = false, type = 'module', data, onClose, onSubmit }: Props = $props();

	let formData = $state<Record<string, any>>({});
	let isSubmitting = $state(false);

	// Reset form when opened
	$effect(() => {
		if (show) {
			formData = data ? { ...data } : getDefaultData(type);
		}
	});

	function getDefaultData(itemType: string): Record<string, any> {
		switch (itemType) {
			case 'module':
				return { name: '', description: '' };
			case 'feature':
				return { name: '', description: '' };
			case 'parameter':
				return { name: '', key: '', type: 'config', dataType: 'string', defaultValue: '', required: false, description: '' };
			default:
				return {};
		}
	}

	function handleSubmit() {
		if (!formData.name?.trim()) {
			toast.error('请输入名称');
			return;
		}

		if (type === 'parameter' && !formData.key?.trim()) {
			toast.error('请输入参数 Key');
			return;
		}

		isSubmitting = true;
		try {
			onSubmit({ ...formData, type });
		} catch (e: any) {
			toast.error(e.message || '保存失败');
		} finally {
			isSubmitting = false;
		}
	}

	function handleClose() {
		formData = {};
		onClose();
	}

	const paramTypeOptions = [
		{ value: 'input', label: '输入' },
		{ value: 'output', label: '输出' },
		{ value: 'config', label: '配置' }
	];

	const dataTypeOptions = [
		{ value: 'string', label: 'string' },
		{ value: 'number', label: 'number' },
		{ value: 'boolean', label: 'boolean' },
		{ value: 'object', label: 'object' },
		{ value: 'array', label: 'array' }
	];
</script>

<Modal bind:show size="md">
	<div class="p-6">
		<!-- Header -->
		<div class="flex items-center justify-between mb-6">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
				{#if type === 'module'}
					编辑模块
				{:else if type === 'feature'}
					编辑功能
				{:else}
					编辑参数
				{/if}
			</h3>
			<button
				class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
				onclick={handleClose}
				aria-label="关闭"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Form -->
		<div class="space-y-4">
			<!-- Name -->
			<div>
				<label for="edit-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					名称 <span class="text-red-500">*</span>
				</label>
				<input
					id="edit-name"
					type="text"
					class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
					placeholder="请输入名称"
					bind:value={formData.name}
					onkeydown={(e) => e.key === 'Enter' && handleSubmit()}
				/>
			</div>

				<!-- Key (for parameter) -->
				{#if type === 'parameter'}
					<div>
						<label for="edit-key" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Key <span class="text-red-500">*</span>
						</label>
						<input
							id="edit-key"
							type="text"
							class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="请输入参数 Key"
							bind:value={formData.key}
							onkeydown={(e) => e.key === 'Enter' && handleSubmit()}
						/>
					</div>

				<!-- Parameter Type -->
				<div>
					<label for="edit-param-type" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						参数类型
					</label>
					<select
						id="edit-param-type"
						class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
						bind:value={formData.type}
					>
						{#each paramTypeOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>

				<!-- Data Type -->
				<div>
					<label for="edit-data-type" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						数据类型
					</label>
					<select
						id="edit-data-type"
						class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
						bind:value={formData.dataType}
					>
						{#each dataTypeOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>

				<!-- Default Value -->
				<div>
					<label for="edit-default-value" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						默认值
					</label>
					<input
						id="edit-default-value"
						type="text"
						class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
						placeholder="请输入默认值"
						bind:value={formData.defaultValue}
					/>
				</div>

				<!-- Required -->
				<div class="flex items-center">
					<input
						type="checkbox"
						id="required"
						class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
						bind:checked={formData.required}
					/>
					<label for="required" class="ml-2 text-sm text-gray-700 dark:text-gray-300">
						必填
					</label>
				</div>
			{/if}

			<!-- Description -->
			<div>
				<label for="edit-description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					描述
				</label>
				<textarea
					id="edit-description"
					class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
					placeholder="请输入描述"
					rows="3"
					bind:value={formData.description}
				></textarea>
			</div>
		</div>

		<!-- Actions -->
		<div class="flex justify-end gap-3 mt-6">
			<button
				class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
				onclick={handleClose}
			>
				取消
			</button>
			<button
				class="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
				onclick={handleSubmit}
				disabled={isSubmitting || !formData.name?.trim()}
			>
				{isSubmitting ? '保存中...' : '保存'}
			</button>
		</div>
	</div>
</Modal>