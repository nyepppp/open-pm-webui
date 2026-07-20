<script lang="ts">
  import { Handle, Position, type NodeProps } from '@xyflow/svelte';
  import { formatDate } from '$lib/utils/pmTimeUtils';

  // SvelteFlow passes NodeProps; data carries our payload
  let { data }: NodeProps = $props();

  // Derive display values
  const nodeType = $derived((data as any)?.nodeType || 'branch');
  const label = $derived((data as any)?.label || '');
  const meta = $derived((data as any)?.metadata || {});
  const versionBadge = $derived(
    meta.currentVersionNumber
      || (meta.versionId
        ? (typeof meta.versionId === 'string' && meta.versionId.length > 8
          ? meta.versionId.slice(0, 8)
          : meta.versionId)
        : '')
  );
  const createdAt = $derived(meta.createdAt ? formatDate(meta.createdAt) : '');
  const source = $derived(meta.source || 'auto');
  const status = $derived(meta.status || '');
  const paramCount = $derived(meta.paramCount ?? 0);

  // Tier-based saturated palette (stronger contrast: -200 bg, -900/60 dark)
  const tierClass = $derived.by(() => {
    if (nodeType === 'root') {
      return {
        container: 'bg-blue-200 dark:bg-blue-900/60 border-blue-600 text-blue-950 dark:text-blue-100',
        badge: 'bg-blue-600 text-white'
      };
    }
    if (nodeType === 'branch') {
      return {
        container: 'bg-emerald-200 dark:bg-emerald-900/60 border-emerald-600 text-emerald-950 dark:text-emerald-100',
        badge: 'bg-emerald-600 text-white'
      };
    }
    return {
      container: 'bg-amber-200 dark:bg-amber-900/60 border-amber-600 text-amber-950 dark:text-amber-100',
      badge: 'bg-amber-600 text-white'
    };
  });

  // Manual-source nodes get dashed border
  const borderStyle = $derived(source === 'manual' ? 'border-dashed' : 'border-solid');

  // Status dot color
  const statusDot = $derived.by(() => {
    switch (status) {
      case 'draft': return 'bg-gray-400';
      case 'in_review': return 'bg-yellow-500';
      case 'approved': return 'bg-green-500';
      case 'active': return 'bg-blue-500';
      case 'archived': return 'bg-gray-300';
      default: return 'bg-transparent';
    }
  });
</script>

<div
  class="rounded-md px-3 py-2 min-w-[160px] max-w-[240px] border-2 shadow-sm transition {tierClass.container} {borderStyle}"
>
  <Handle type="target" position={Position.Top} class="!bg-gray-500" />

  <!-- Header row: label + status dot -->
  <div class="flex items-center gap-2">
    {#if status}
      <span class="inline-block w-2 h-2 rounded-full {statusDot} shrink-0" title={status}></span>
    {/if}
    <span class="font-semibold text-sm truncate flex-1">{label}</span>
  </div>

  <!-- Version + creation row -->
  <div class="mt-1 flex flex-wrap items-center gap-1 text-[10px]">
    {#if versionBadge}
      <span class="inline-flex items-center px-1.5 py-0.5 rounded {tierClass.badge} font-medium">
        v{versionBadge}
      </span>
    {/if}
    {#if createdAt}
      <span class="text-gray-600 dark:text-gray-300">📅 {createdAt}</span>
    {/if}
  </div>

  <!-- Param count for branches/leaves -->
  {#if nodeType !== 'root' && paramCount > 0}
    <div class="mt-0.5 text-[10px] text-gray-600 dark:text-gray-300">
      {paramCount} 个{nodeType === 'branch' ? '功能' : '参数'}
    </div>
  {/if}

  <Handle type="source" position={Position.Bottom} class="!bg-gray-500" />
</div>
