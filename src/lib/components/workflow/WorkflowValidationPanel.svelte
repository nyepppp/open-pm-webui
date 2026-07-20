<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	interface ValidationError {
		field: string;
		message: string;
		severity: 'error' | 'warning' | 'info';
	}

	interface Props {
		errors: ValidationError[];
		showSummary?: boolean;
		onErrorClick?: (error: ValidationError) => void;
	}

	let { errors = [], showSummary = true, onErrorClick }: Props = $props();

	const dispatch = createEventDispatcher();

	function getSeverityIcon(severity: string): string {
		switch (severity) {
			case 'error':
				return '✗';
			case 'warning':
				return '⚠';
			case 'info':
				return 'ℹ';
			default:
				return '•';
		}
	}

	function getSeverityColor(severity: string): string {
		switch (severity) {
			case 'error':
				return 'text-red-600 bg-red-50 dark:bg-red-900/20';
			case 'warning':
				return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20';
			case 'info':
				return 'text-blue-600 bg-blue-50 dark:bg-blue-900/20';
			default:
				return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
		}
	}

	function getSeverityBorderColor(severity: string): string {
		switch (severity) {
			case 'error':
				return 'border-red-200 dark:border-red-800';
			case 'warning':
				return 'border-yellow-200 dark:border-yellow-800';
			case 'info':
				return 'border-blue-200 dark:border-blue-800';
			default:
				return 'border-gray-200 dark:border-gray-700';
		}
	}

	function handleErrorClick(error: ValidationError) {
		onErrorClick?.(error);
		dispatch('errorClick', { error });
	}

	function getErrorCount(severity: string): number {
		return errors.filter((e) => e.severity === severity).length;
	}
</script>

{#if errors.length > 0}
	<div class="space-y-2">
		<!-- Summary -->
		{#if showSummary}
			<div class="flex items-center gap-4 text-xs">
				{#if getErrorCount('error') > 0}
					<span class="inline-flex items-center gap-1 text-red-600">
						<span>{getErrorCount('error')} 个错误</span>
					</span>
				{/if}
				{#if getErrorCount('warning') > 0}
					<span class="inline-flex items-center gap-1 text-yellow-600">
						<span>{getErrorCount('warning')} 个警告</span>
					</span>
				{/if}
				{#if getErrorCount('info') > 0}
					<span class="inline-flex items-center gap-1 text-blue-600">
						<span>{getErrorCount('info')} 个提示</span>
					</span>
				{/if}
			</div>
		{/if}

		<!-- Error List -->
		<div class="space-y-1 max-h-48 overflow-y-auto">
			{#each errors as error (error.field + error.message)}
				<div
					class="flex items-start gap-2 p-2 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors {getSeverityBorderColor(error.severity)}"
					onclick={() => handleErrorClick(error)}
					role="button"
					tabindex="0"
					onkeydown={(e) => {
						if (e.key === 'Enter' || e.key === ' ') {
							e.preventDefault();
							handleErrorClick(error);
						}
					}}
				>
					<span class="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs {getSeverityColor(error.severity)}">
						{getSeverityIcon(error.severity)}
					</span>
					<div class="flex-1 min-w-0">
						<p class="text-xs font-medium text-gray-900 dark:text-white">
							{error.field}
						</p>
						<p class="text-xs text-gray-600 dark:text-gray-400">
							{error.message}
						</p>
					</div>
				</div>
			{/each}
		</div>
	</div>
{/if}
