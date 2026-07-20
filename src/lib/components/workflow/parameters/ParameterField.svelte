<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { NodeParameter } from '../nodes';

	interface Props {
		parameter: NodeParameter;
		value: any;
		onChange?: (value: any) => void;
	}

	let { parameter, value, onChange }: Props = $props();

	const dispatch = createEventDispatcher();

	function handleChange(newValue: any) {
		onChange?.(newValue);
		dispatch('change', { id: parameter.id, value: newValue });
	}
</script>

<div class="parameter-field">
	{#if parameter.type === 'text'}
		<div class="space-y-1">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{parameter.name}
				{#if parameter.required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			<input
				type="text"
				class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				placeholder={parameter.placeholder || ''}
				value={value || parameter.defaultValue || ''}
				oninput={(e) => handleChange(e.currentTarget.value)}
			/>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>

	{:else if parameter.type === 'number'}
		<div class="space-y-1">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{parameter.name}
				{#if parameter.required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			<input
				type="number"
				class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				value={value !== undefined ? value : parameter.defaultValue || ''}
				oninput={(e) => handleChange(parseFloat(e.currentTarget.value))}
			/>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>

	{:else if parameter.type === 'boolean'}
		<div class="space-y-1">
			<label class="flex items-center gap-2 cursor-pointer">
				<input
					type="checkbox"
					class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
					checked={value !== undefined ? value : parameter.defaultValue || false}
					onchange={(e) => handleChange(e.currentTarget.checked)}
				/>
				<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
					{parameter.name}
					{#if parameter.required}
						<span class="text-red-500">*</span>
					{/if}
				</span>
			</label>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>

	{:else if parameter.type === 'select'}
		<div class="space-y-1">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{parameter.name}
				{#if parameter.required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			<select
				class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				value={value || parameter.defaultValue || ''}
				onchange={(e) => handleChange(e.currentTarget.value)}
			>
				{#if parameter.options}
					{#each parameter.options as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				{/if}
			</select>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>

	{:else if parameter.type === 'textarea'}
		<div class="space-y-1">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{parameter.name}
				{#if parameter.required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			<textarea
				class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono"
				rows="4"
				placeholder={parameter.placeholder || ''}
				value={value || parameter.defaultValue || ''}
				oninput={(e) => handleChange(e.currentTarget.value)}
			></textarea>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>

	{:else if parameter.type === 'json'}
		<div class="space-y-1">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{parameter.name}
				{#if parameter.required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			<textarea
				class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono"
				rows="6"
				placeholder="输入 JSON 数据"
				value={value !== undefined ? JSON.stringify(value, null, 2) : JSON.stringify(parameter.defaultValue, null, 2)}
				oninput={(e) => {
					try {
						const parsed = JSON.parse(e.currentTarget.value);
						handleChange(parsed);
					} catch {
						// 不合法的JSON，但允许用户继续输入
						handleChange(e.currentTarget.value);
					}
				}}
			></textarea>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>

	{:else if parameter.type === 'file'}
		<div class="space-y-1">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{parameter.name}
				{#if parameter.required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			<div class="flex items-center gap-2">
				<input
					type="file"
					class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
					onchange={(e) => {
						const file = e.currentTarget.files?.[0];
						if (file) {
							handleChange({ name: file.name, size: file.size, type: file.type });
						}
					}}
				/>
			</div>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>

	{:else if parameter.type === 'reference'}
		<div class="space-y-1">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
				{parameter.name}
				{#if parameter.required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			<input
				type="text"
				class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				placeholder="输入引用ID"
				value={value || parameter.defaultValue || ''}
				oninput={(e) => handleChange(e.currentTarget.value)}
			/>
			{#if parameter.description}
				<p class="text-xs text-gray-500 dark:text-gray-400">{parameter.description}</p>
			{/if}
		</div>
	{/if}
</script>
