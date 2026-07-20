<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	interface CustomParameter {
		id: string;
		name: string;
		type: 'text' | 'number' | 'boolean' | 'select' | 'textarea' | 'json';
		value: any;
		required: boolean;
		description?: string;
	}

	interface Props {
		parameters: CustomParameter[];
		readonly?: boolean;
		onChange?: (parameters: CustomParameter[]) => void;
	}

	let { parameters = [], readonly = false, onChange }: Props = $props();

	const dispatch = createEventDispatcher();

	let localParams = $state<CustomParameter[]>([...parameters]);
	let newParamName = $state('');
	let newParamType: CustomParameter['type'] = $state('text');
	let newParamRequired = $state(false);
	let newParamDescription = $state('');
	let showAddForm = $state(false);

	function handleParamChange(index: number, field: keyof CustomParameter, value: any) {
		localParams = localParams.map((param, i) =>
			i === index ? { ...param, [field]: value } : param
		);
		onChange?.(localParams);
		dispatch('change', { parameters: localParams });
	}

	function addParameter() {
		if (!newParamName.trim()) return;

		const newParam: CustomParameter = {
			id: `custom_${Date.now()}`,
			name: newParamName.trim(),
			type: newParamType,
			value: getDefaultValue(newParamType),
			required: newParamRequired,
			description: newParamDescription.trim() || undefined
		};

		localParams = [...localParams, newParam];
		onChange?.(localParams);
		dispatch('change', { parameters: localParams });

		// Reset form
		newParamName = '';
		newParamType = 'text';
		newParamRequired = false;
		newParamDescription = '';
		showAddForm = false;
	}

	function removeParameter(index: number) {
		localParams = localParams.filter((_, i) => i !== index);
		onChange?.(localParams);
		dispatch('change', { parameters: localParams });
	}

	function getDefaultValue(type: CustomParameter['type']) {
		switch (type) {
			case 'number':
				return 0;
			case 'boolean':
				return false;
			case 'json':
				return {};
			default:
				return '';
		}
	}

	function getTypeLabel(type: CustomParameter['type']): string {
		const labels: Record<string, string> = {
			text: '文本',
			number: '数字',
			boolean: '布尔',
			select: '选择',
			textarea: '多行文本',
			json: 'JSON'
		};
		return labels[type] || type;
	}
</script>

<div class="space-y-4">
	<!-- Parameter List -->
	{#if localParams.length > 0}
		<div class="space-y-3">
			{#each localParams as param, index (param.id)}
				<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-3 space-y-2">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{param.name}
							</span>
							<span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
								{getTypeLabel(param.type)}
							</span>
							{#if param.required}
								<span class="text-xs px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">
									必填
								</span>
							{/if}
						</div>
						{#if !readonly}
							<button
								class="text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors"
								onclick={() => removeParameter(index)}
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						{/if}
					</div>

					{#if param.description}
						<p class="text-xs text-gray-500 dark:text-gray-400">{param.description}</p>
					{/if}

					<!-- Value Input -->
					{#if !readonly}
						<div>
							{#if param.type === 'text'}
								<input
									type="text"
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									value={param.value || ''}
									oninput={(e) => handleParamChange(index, 'value', e.currentTarget.value)}
								/>
							{:else if param.type === 'number'}
								<input
									type="number"
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									value={param.value || 0}
									oninput={(e) => handleParamChange(index, 'value', parseFloat(e.currentTarget.value))}
								/>
							{:else if param.type === 'boolean'}
								<label class="flex items-center gap-2 cursor-pointer">
									<input
										type="checkbox"
										class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
										checked={param.value || false}
										onchange={(e) => handleParamChange(index, 'value', e.currentTarget.checked)}
									/>
									<span class="text-sm text-gray-700 dark:text-gray-300">启用</span>
								</label>
							{:else if param.type === 'textarea'}
								<textarea
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
									rows="3"
									value={param.value || ''}
									oninput={(e) => handleParamChange(index, 'value', e.currentTarget.value)}
								></textarea>
							{:else if param.type === 'json'}
								<textarea
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono"
									rows="4"
									value={JSON.stringify(param.value, null, 2)}
									oninput={(e) => {
										try {
											const parsed = JSON.parse(e.currentTarget.value);
											handleParamChange(index, 'value', parsed);
										} catch {
											handleParamChange(index, 'value', e.currentTarget.value);
										}
									}}
								></textarea>
							{/if}
						</div>
					{:else}
						<div class="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded p-2">
							{JSON.stringify(param.value)}
						</div>
						{/if}
						</div>
					{/each}
				</div>
			{/if}

	<!-- Add Parameter Button -->
	{#if !readonly}
		{#if !showAddForm}
			<button
				class="w-full py-2 px-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-500 dark:text-gray-400 hover:border-gray-400 dark:hover:border-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
				onclick={() => showAddForm = true}
			>
				+ 添加自定义参数
			</button>
		{:else}
			<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3">
				<h4 class="text-sm font-medium text-gray-900 dark:text-white">添加自定义参数</h4>

				<div class="space-y-2">
					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							参数名称
						</label>
						<input
							type="text"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							placeholder="输入参数名称"
							bind:value={newParamName}
						/>
					</div>

					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							参数类型
						</label>
						<select
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							bind:value={newParamType}
						>
							<option value="text">文本</option>
							<option value="number">数字</option>
							<option value="boolean">布尔</option>
							<option value="textarea">多行文本</option>
							<option value="json">JSON</option>
						</select>
					</div>

					<div>
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="checkbox"
								class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
								bind:checked={newParamRequired}
							/>
							<span class="text-sm text-gray-700 dark:text-gray-300">必填</span>
						</label>
					</div>

					<div>
						<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
							描述（可选）
						</label>
						<input
							type="text"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							placeholder="参数描述"
							bind:value={newParamDescription}
						/>
					</div>
				</div>

				<div class="flex gap-2">
					<button
						class="flex-1 px-3 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
						onclick={addParameter}
						disabled={!newParamName.trim()}
					>
						添加
					</button>
					<button
						class="flex-1 px-3 py-2 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
						onclick={() => showAddForm = false}
					>
						取消
					</button>
				</div>
			</div>
		{/if}
	{/if}
</div>
