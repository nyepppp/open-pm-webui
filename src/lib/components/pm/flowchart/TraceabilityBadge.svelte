<script lang="ts">
	interface Traceability {
		entityType: 'prd' | 'module' | 'feature' | 'parameter' | 'none';
		entityId: string;
		entityName: string;
		versionId?: string;
		versionNumber?: string;
		boundAt: number;
		boundBy?: string;
	}

	interface Props {
		traceability?: {
			entityType: string;
			entityId: string;
			entityName: string;
			versionNumber?: string;
		};
	}

	let { traceability }: Props = $props();

	const entityTypeConfig: Record<string, { label: string; color: string; bgColor: string }> = {
		prd: { label: 'PRD', color: '#8B5CF6', bgColor: '#F3E8FF' },
		module: { label: '模块', color: '#3B82F6', bgColor: '#DBEAFE' },
		feature: { label: '功能', color: '#10B981', bgColor: '#D1FAE5' },
		parameter: { label: '参数', color: '#F59E0B', bgColor: '#FEF3C7' },
		none: { label: '未绑定', color: '#9CA3AF', bgColor: '#F3F4F6' }
	};

	let config = $derived(
		traceability ? entityTypeConfig[traceability.entityType] || entityTypeConfig.none : entityTypeConfig.none
	);
</script>

{#if traceability && traceability.entityType !== 'none'}
	<div
		class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border"
		style="background-color: {config.bgColor}; border-color: {config.color}; color: {config.color};"
	>
		<span class="w-1.5 h-1.5 rounded-full" style="background-color: {config.color};"></span>
		{config.label}
		{#if traceability.versionNumber}
			<span class="opacity-75">v{traceability.versionNumber}</span>
		{/if}
	</div>
{/if}
