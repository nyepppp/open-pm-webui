<script lang="ts">
	import type { FieldConfig } from '$lib/apis/pm/types';

	// Props
	interface Props {
		fields: FieldConfig[];
		data?: Record<string, unknown>;
		onChange?: (data: Record<string, unknown>) => void;
		onSubmit?: (data: Record<string, unknown>) => void;
	}

	let { fields, data = {}, onChange, onSubmit }: Props = $props();

	// Local form state
	let formData = $state<Record<string, unknown>>({ ...data });
	let errors = $state<Record<string, string>>({});
	let touched = $state<Set<string>>(new Set());

	function handleFieldChange(fieldName: string, value: unknown) {
		formData = { ...formData, [fieldName]: value };
		touched = new Set([...touched, fieldName]);
		onChange?.(formData);
	}

	function handleSubmit(event: Event) {
		event.preventDefault();
		if (validateForm()) {
			onSubmit?.(formData);
		}
	}

	function validateForm(): boolean {
		const newErrors: Record<string, string> = {};
		for (const field of fields) {
			if (field.required && !formData[field.name]) {
				newErrors[field.name] = `${field.label} 不能为空`;
			}
			if (field.validation?.min !== undefined) {
				const val = Number(formData[field.name]);
				if (!isNaN(val) && val < field.validation.min) {
					newErrors[field.name] = `${field.label} 不能小于 ${field.validation.min}`;
				}
			}
			if (field.validation?.max !== undefined) {
				const val = Number(formData[field.name]);
				if (!isNaN(val) && val > field.validation.max) {
					newErrors[field.name] = `${field.label} 不能大于 ${field.validation.max}`;
				}
			}
			if (field.validation?.pattern) {
				const val = String(formData[field.name] || '');
				const regex = new RegExp(field.validation.pattern);
				if (val && !regex.test(val)) {
					newErrors[field.name] = `${field.label} 格式不正确`;
				}
			}
		}
		errors = newErrors;
		return Object.keys(newErrors).length === 0;
	}

	function getFieldValue(field: FieldConfig): unknown {
		return formData[field.name] ?? '';
	}

	function isFieldError(field: FieldConfig): boolean {
		return touched.has(field.name) && !!errors[field.name];
	}
</script>

<form class="pm-form-editor space-y-6" onsubmit={handleSubmit}>
	{#each fields as field (field.name)}
		<div class="form-field">
			<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
				{field.label}
				{#if field.required}
					<span class="text-red-500 dark:text-red-400">*</span>
				{/if}
			</label>

			{#if field.type === 'text'}
				<input
					type="text"
					class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors {isFieldError(field) ? 'border-red-500 dark:border-red-400 focus:ring-red-500' : ''}"
					placeholder={field.placeholder}
					value={String(getFieldValue(field) || '')}
					oninput={(e) => handleFieldChange(field.name, e.currentTarget.value)}
				/>

			{:else if field.type === 'textarea'}
				<textarea
					class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-y {isFieldError(field) ? 'border-red-500 dark:border-red-400 focus:ring-red-500' : ''}"
					placeholder={field.placeholder}
					rows={4}
					oninput={(e) => handleFieldChange(field.name, e.currentTarget.value)}
				>{String(getFieldValue(field) || '')}</textarea>

			{:else if field.type === 'select'}
				<select
					class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors {isFieldError(field) ? 'border-red-500 dark:border-red-400 focus:ring-red-500' : ''}"
					onchange={(e) => handleFieldChange(field.name, e.currentTarget.value)}
				>
					{#if field.placeholder}
						<option value="" disabled selected={!getFieldValue(field)}>{field.placeholder}</option>
					{/if}
					{#each field.options || [] as option}
						<option value={option} selected={getFieldValue(field) === option}>{option}</option>
					{/each}
				</select>

			{:else if field.type === 'multiselect'}
				<div class="space-y-2">
					{#each field.options || [] as option}
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="checkbox"
								class="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
								value={option}
								checked={Array.isArray(getFieldValue(field)) && (getFieldValue(field) as string[]).includes(option)}
								onchange={(e) => {
									const current = Array.isArray(getFieldValue(field)) ? [...(getFieldValue(field) as string[])] : [];
									if (e.currentTarget.checked) {
										handleFieldChange(field.name, [...current, option]);
									} else {
										handleFieldChange(field.name, current.filter(v => v !== option));
									}
								}}
							/>
							<span class="text-sm text-gray-700 dark:text-gray-300">{option}</span>
						</label>
					{/each}
				</div>

			{:else if field.type === 'number'}
				<input
					type="number"
					class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors {isFieldError(field) ? 'border-red-500 dark:border-red-400 focus:ring-red-500' : ''}"
					placeholder={field.placeholder}
					value={Number(getFieldValue(field)) || ''}
					oninput={(e) => handleFieldChange(field.name, e.currentTarget.valueAsNumber)}
				/>

			{:else if field.type === 'date'}
				<input
					type="date"
					class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors {isFieldError(field) ? 'border-red-500 dark:border-red-400 focus:ring-red-500' : ''}"
					value={String(getFieldValue(field) || '')}
					onchange={(e) => handleFieldChange(field.name, e.currentTarget.value)}
				/>

			{:else if field.type === 'json'}
				<textarea
					class="w-full px-3 py-2 text-sm font-mono bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-y {isFieldError(field) ? 'border-red-500 dark:border-red-400 focus:ring-red-500' : ''}"
					placeholder={field.placeholder || '{"key": "value"}'}
					rows={6}
					oninput={(e) => {
						const value = e.currentTarget.value;
						try {
							const parsed = value ? JSON.parse(value) : {};
							handleFieldChange(field.name, parsed);
						} catch {
							handleFieldChange(field.name, value);
						}
					}}
				>{String(getFieldValue(field) || '')}</textarea>
			{/if}

			{#if isFieldError(field)}
				<p class="mt-1 text-xs text-red-500 dark:text-red-400">{errors[field.name]}</p>
			{/if}
		</div>
	{/each}

	<!-- Submit Button -->
	{#if onSubmit}
		<div class="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
			<button
				type="submit"
				class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors shadow-sm hover:shadow-md"
			>
				保存
			</button>
		</div>
	{/if}
</form>
