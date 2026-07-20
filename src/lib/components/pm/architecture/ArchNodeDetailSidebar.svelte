<script lang="ts">
  import { formatDateTime } from '$lib/utils/pmTimeUtils';
  import type { ArchModule, ArchFeature, ArchParameter } from '$lib/stores/pm/architectureStore';
  import {
    createModuleVersionAction,
    switchModuleVersionAction,
    deleteModuleVersionAction
  } from '$lib/stores/pm/architectureStore';
  import { getModuleVersionSpan, getEntryVersions, switchEntryVersion } from '$lib/apis/pm/index';
  import type { EntryVersion } from '$lib/apis/pm/index';
  import { toast } from 'svelte-sonner';
  import VersionHistoryPopover from './VersionHistoryPopover.svelte';

  type SelectedNode =
    | { nodeType: 'root' }
    | { nodeType: 'node'; moduleId: string; featureId?: string; parameterId?: string }
    | null;

  interface ProjectMeta {
    projectId: string;
    projectName?: string;
    projectDescription?: string;
    projectCreatedAt?: number;
    projectUpdatedAt?: number;
    currentVersion?: any;
  }

  interface Props {
    selectedNode: SelectedNode;
    modules: ArchModule[];
    projectMeta?: ProjectMeta;
    onClose?: () => void;
    // 允许 sidebar 内部触发节点切换（例如在 feature 视图中点击参数项跳转到 parameter 视图）
    onSelectNode?: (node: SelectedNode) => void;
  }

  let { selectedNode, modules, projectMeta, onClose, onSelectNode }: Props = $props();

  // Resolve the selected node into one of: root | module | feature | parameter
  const resolved = $derived.by(() => {
    if (!selectedNode) return null;

    if (selectedNode.nodeType === 'root') {
      return { kind: 'root' as const, meta: projectMeta };
    }

    const mod = modules.find(m => m.id === selectedNode.moduleId);
    if (!mod) return null;

    if (selectedNode.featureId) {
      const feat = mod.features.find(f => f.id === selectedNode.featureId);
      if (!feat) return null;
      // 参数级：在 feature 下进一步定位 parameter
      if (selectedNode.parameterId) {
        const param = feat.parameters.find(p => p.id === selectedNode.parameterId);
        if (param) return { kind: 'parameter' as const, mod, feat, param };
      }
      if (feat) return { kind: 'feature' as const, mod, feat };
    }
    return { kind: 'module' as const, mod };
  });

  // Aggregate related requirements across the feature's parameters
  function aggregateRelatedRequirements(feat: ArchFeature): string[] {
    const set = new Set<string>();
    for (const p of feat.parameters) {
      if (Array.isArray(p.relatedRequirements)) {
        for (const r of p.relatedRequirements) {
          if (r) set.add(String(r));
        }
      }
    }
    return [...set];
  }

  // Version history popover state
  let versionHistoryEntity: { type: 'module' | 'function' | 'parameter'; id: string } | null = $state(null);

  // ===== 模块版本管理状态（与项目版本分离，独立状态） =====
  let showCreateModuleVersion = $state(false);
  let newVersionNumber = $state('');
  let newVersionSummary = $state('');
  let versionSpan = $state<{ featureSpan: number; parameterSpan: number } | null>(null);
  let isVersionActionLoading = $state(false);

  // ===== 参数版本管理状态（条目级修订历史 PMEntryVersion） =====
  let paramVersions = $state<EntryVersion[]>([]);
  let isLoadingParamVersions = $state(false);
  let isSwitchingParamVersion = $state(false);

  // 当选中的模块变化时，拉取版本跨度
  $effect(() => {
    const r = resolved;
    if (r && r.kind === 'module' && r.mod.entryId && projectMeta?.projectId) {
      const token = localStorage.token || '';
      versionSpan = null;
      getModuleVersionSpan(token, projectMeta.projectId, r.mod.entryId)
        .then(span => { versionSpan = span; })
        .catch(() => { versionSpan = null; });
    } else {
      versionSpan = null;
    }
  });

  // 当选中的参数变化时，清空旧版本列表，避免显示上一个参数的残留数据
  $effect(() => {
    const r = resolved;
    if (!r || r.kind !== 'parameter') {
      paramVersions = [];
    }
  });

  async function handleCreateModuleVersion(modEntryId: string) {
    if (!projectMeta?.projectId) return;
    if (!newVersionNumber.trim()) {
      toast.error('请输入版本号');
      return;
    }
    isVersionActionLoading = true;
    try {
      await createModuleVersionAction(projectMeta.projectId, modEntryId, {
        version_number: newVersionNumber.trim(),
        change_summary: newVersionSummary.trim() || 'No description'
      });
      toast.success('模块版本创建成功');
      showCreateModuleVersion = false;
      newVersionNumber = '';
      newVersionSummary = '';
    } catch (e: any) {
      toast.error(e.message || '创建失败');
    } finally {
      isVersionActionLoading = false;
    }
  }

  async function handleSwitchModuleVersion(modEntryId: string, versionId: string) {
    if (!projectMeta?.projectId) return;
    isVersionActionLoading = true;
    try {
      await switchModuleVersionAction(projectMeta.projectId, modEntryId, versionId);
      toast.success('模块版本已切换');
    } catch (e: any) {
      toast.error(e.message || '切换失败');
    } finally {
      isVersionActionLoading = false;
    }
  }

  async function handleDeleteModuleVersion(modEntryId: string, versionId: string) {
    if (!projectMeta?.projectId) return;
    if (!confirm('确定删除此模块版本？删除后不可恢复。')) return;
    isVersionActionLoading = true;
    try {
      await deleteModuleVersionAction(projectMeta.projectId, modEntryId, versionId);
      toast.success('模块版本已删除');
    } catch (e: any) {
      toast.error(e.message || '删除失败');
    } finally {
      isVersionActionLoading = false;
    }
  }

  // ===== 参数版本管理函数（条目级修订历史 PMEntryVersion） =====
  // 拉取参数对应 entry 的修订版本列表，结果按 created_at 降序
  async function loadParamVersions(entryId: string) {
    if (!projectMeta?.projectId) return;
    if (!entryId) {
      toast.error('该参数未绑定条目，无法加载版本');
      return;
    }
    isLoadingParamVersions = true;
    try {
      const token = localStorage.token || '';
      const list = await getEntryVersions(token, projectMeta.projectId, entryId);
      paramVersions = Array.isArray(list) ? list : [];
    } catch (e: any) {
      toast.error(e.message || '加载参数版本失败');
      paramVersions = [];
    } finally {
      isLoadingParamVersions = false;
    }
  }

  // 切换参数到指定条目版本：后端会把 entry 的 content/data 回滚到该版本快照
  async function handleSwitchParamVersion(entryId: string, versionId: string) {
    if (!projectMeta?.projectId) return;
    if (!confirm('确定切换到该条目版本？切换后参数内容会回滚到此版本快照。')) return;
    isSwitchingParamVersion = true;
    try {
      const token = localStorage.token || '';
      await switchEntryVersion(token, projectMeta.projectId, entryId, versionId);
      toast.success('参数条目版本已切换');
      // 切换后重新拉取版本列表以刷新"当前"标记
      await loadParamVersions(entryId);
    } catch (e: any) {
      toast.error(e.message || '切换失败');
    } finally {
      isSwitchingParamVersion = false;
    }
  }

  // Status label mapping
  const statusLabel = (status?: string): string => {
    const map: Record<string, string> = {
      draft: '草稿',
      in_review: '评审中',
      approved: '已通过',
      active: '已启用',
      archived: '已归档'
    };
    return status ? (map[status] || status) : '—';
  };

  const priorityLabel = (priority?: string): string => {
    if (!priority) return '—';
    const map: Record<string, string> = {
      low: '低',
      medium: '中',
      high: '高',
      critical: '紧急'
    };
    return map[priority] || priority;
  };

  // Project-level aggregates for root view
  const totalFeatures = $derived(modules.reduce((sum, m) => sum + m.features.length, 0));
  const totalParams = $derived(
    modules.reduce(
      (sum, m) => sum + m.features.reduce((s, f) => s + f.parameters.length, 0),
      0
    )
  );
</script>

{#if resolved}
  <aside class="w-80 h-full border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 shrink-0">
      <div class="flex items-center gap-2 min-w-0">
        <span class="inline-flex items-center justify-center w-7 h-7 rounded-md text-xs font-bold shrink-0
          {resolved.kind === 'root' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' : resolved.kind === 'module' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200' : resolved.kind === 'parameter' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200' : 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200'}">
          {resolved.kind === 'root' ? 'P' : resolved.kind === 'module' ? 'M' : resolved.kind === 'parameter' ? 'P' : 'F'}
        </span>
        <span class="font-semibold text-sm truncate text-gray-900 dark:text-gray-100">
          {#if resolved.kind === 'root'}
            {resolved.meta?.projectName || '项目'}
          {:else if resolved.kind === 'module'}
            {resolved.mod.name}
          {:else if resolved.kind === 'feature'}
            {resolved.feat!.name}
          {:else if resolved.kind === 'parameter'}
            {resolved.param!.name || resolved.param!.key || '参数'}
          {/if}
        </span>
      </div>
      <button
        class="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 shrink-0"
        onclick={() => onClose?.()}
        title="关闭"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3 text-sm">
      {#if resolved.kind === 'root'}
        <!-- ROOT VIEW: project-level meta -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">类型</span>
          <span class="px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200">项目</span>
        </div>

        {#if resolved.meta?.currentVersion}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">当前版本</span>
            <span class="px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 font-medium">
              {resolved.meta.currentVersion.versionNumber || resolved.meta.currentVersion.version_number || '—'}
            </span>
          </div>
        {/if}

        {#if resolved.meta?.projectDescription}
          <div>
            <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">描述</div>
            <p class="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{resolved.meta.projectDescription}</p>
          </div>
        {/if}

        {#if resolved.meta?.projectCreatedAt}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">创建时间</span>
            <span class="text-xs text-gray-700 dark:text-gray-300">{formatDateTime(resolved.meta.projectCreatedAt)}</span>
          </div>
        {/if}

        {#if resolved.meta?.projectUpdatedAt}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">更新时间</span>
            <span class="text-xs text-gray-700 dark:text-gray-300">{formatDateTime(resolved.meta.projectUpdatedAt)}</span>
          </div>
        {/if}

        <!-- Aggregates -->
        <div class="pt-2 border-t border-gray-100 dark:border-gray-800 space-y-1.5">
          <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">架构概览</div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-600 dark:text-gray-400">模块数</span>
            <span class="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium">{modules.length}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-600 dark:text-gray-400">功能数</span>
            <span class="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium">{totalFeatures}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-600 dark:text-gray-400">参数数</span>
            <span class="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium">{totalParams}</span>
          </div>
        </div>

        {#if resolved.meta?.projectId}
          <div class="pt-2 border-t border-gray-100 dark:border-gray-800">
            <div class="text-[10px] text-gray-400">项目ID: {resolved.meta.projectId}</div>
          </div>
        {/if}
      {:else if resolved.kind === 'module'}
        <!-- MODULE VIEW -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">类型</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">模块</span>
        </div>

        <!-- Current version -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">当前版本</span>
          <span class="px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 font-medium">
            {resolved.mod.currentVersionNumber || (resolved.mod.versionId ? resolved.mod.versionId.slice(0, 8) : '—')}
          </span>
        </div>

        <!-- Created version -->
        {#if resolved.mod.createdVersionNumber}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">创建版本</span>
            <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
              {resolved.mod.createdVersionNumber}
            </span>
          </div>
        {/if}

        <!-- Branch -->
        {#if resolved.mod.branchName}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">分支</span>
            <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono">
              {resolved.mod.branchName}
            </span>
          </div>
        {/if}

        <!-- Status -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">状态</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            {statusLabel(resolved.mod.status)}
          </span>
        </div>

        <!-- Priority -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">优先级</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            {priorityLabel(resolved.mod.priority)}
          </span>
        </div>

        <!-- Created/updated times -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">创建时间</span>
          <span class="text-xs text-gray-700 dark:text-gray-300">{formatDateTime(resolved.mod.createdAt)}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">更新时间</span>
          <span class="text-xs text-gray-700 dark:text-gray-300">{formatDateTime(resolved.mod.updatedAt)}</span>
        </div>

        <!-- Description -->
        {#if resolved.mod.description}
          <div>
            <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">描述</div>
            <p class="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{resolved.mod.description}</p>
          </div>
        {/if}

        <!-- Features list -->
        <div>
          <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">
            包含功能 ({resolved.mod.features.length})
          </div>
          {#if resolved.mod.features.length === 0}
            <p class="text-xs text-gray-400">暂无功能</p>
          {:else}
            <ul class="space-y-1">
              {#each resolved.mod.features as feat}
                <li class="text-xs text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                  <span class="w-1 h-1 rounded-full bg-amber-500"></span>
                  <span class="truncate">{feat.name}</span>
                  <span class="text-gray-400 ml-auto shrink-0">{feat.parameters?.length || 0}参数</span>
                </li>
              {/each}
            </ul>
          {/if}
        </div>

        <!-- ===== 模块版本管理（与项目版本 PMVersion 分离，独立卡片） ===== -->
        {#if resolved.mod.entryId && projectMeta?.projectId}
          <div class="pt-3 border-t border-gray-200 dark:border-gray-700">
            <div class="rounded-md border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10 p-3 space-y-2">
              <!-- 标题：明确标注"模块版本"，避免与项目版本混淆 -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <span class="inline-flex items-center justify-center w-4 h-4 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">M</span>
                  <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">模块版本管理</span>
                </div>
                <button
                  class="text-[11px] px-2 py-0.5 rounded border border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 disabled:opacity-50"
                  onclick={() => showCreateModuleVersion = !showCreateModuleVersion}
                  disabled={isVersionActionLoading}
                >
                  {showCreateModuleVersion ? '取消' : '+ 新建版本'}
                </button>
              </div>

              <!-- 当前模块版本 -->
              <div class="text-[11px] text-gray-600 dark:text-gray-400">
                当前模块版本:
                <span class="ml-1 px-1.5 py-0.5 rounded font-mono font-medium {resolved.mod.moduleVersionId ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}">
                  {resolved.mod.moduleVersionId ? resolved.mod.moduleVersionId.slice(0, 8) : '未绑定'}
                </span>
              </div>

              <!-- 版本跨度 -->
              {#if versionSpan}
                <div class="text-[11px] text-gray-500 dark:text-gray-400">
                  版本跨度: <span class="font-medium text-gray-700 dark:text-gray-300">{versionSpan.featureSpan}</span> 功能 / <span class="font-medium text-gray-700 dark:text-gray-300">{versionSpan.parameterSpan}</span> 参数
                </div>
              {/if}

              <!-- 新建版本表单 -->
              {#if showCreateModuleVersion}
                <div class="space-y-2 pt-2 border-t border-emerald-200 dark:border-emerald-800">
                  <div>
                    <!-- svelte-ignore a11y_label_has_associated_control -->
                    <label class="block text-[10px] text-gray-500 dark:text-gray-400 mb-0.5">版本号 *</label>
                    <input
                      type="text"
                      class="w-full text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      placeholder="例如: v2"
                      bind:value={newVersionNumber}
                      disabled={isVersionActionLoading}
                    />
                  </div>
                  <div>
                    <!-- svelte-ignore a11y_label_has_associated_control -->
                    <label class="block text-[10px] text-gray-500 dark:text-gray-400 mb-0.5">变更说明</label>
                    <textarea
                      class="w-full text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-y"
                      rows="2"
                      placeholder="简述本次版本变更"
                      bind:value={newVersionSummary}
                      disabled={isVersionActionLoading}
                    ></textarea>
                  </div>
                  <button
                    class="w-full text-xs px-2 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
                    onclick={() => handleCreateModuleVersion(resolved.mod.entryId!)}
                    disabled={isVersionActionLoading || !newVersionNumber.trim()}
                  >
                    {isVersionActionLoading ? '创建中...' : '确认创建'}
                  </button>
                </div>
              {/if}

              <!-- 版本列表 -->
              {#if resolved.mod.moduleVersions && resolved.mod.moduleVersions.length > 0}
                <div class="pt-2 border-t border-emerald-200 dark:border-emerald-800 space-y-1">
                  <div class="text-[10px] text-gray-500 dark:text-gray-400">版本历史 ({resolved.mod.moduleVersions.length})</div>
                  {#each resolved.mod.moduleVersions as ver}
                    <div class="flex items-center justify-between text-[11px] py-1 px-1.5 rounded hover:bg-emerald-100/50 dark:hover:bg-emerald-900/20">
                      <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-1.5">
                          <span class="font-mono font-medium text-gray-800 dark:text-gray-200">{ver.version_number}</span>
                          {#if ver.id === resolved.mod.moduleVersionId}
                            <span class="text-[9px] px-1 rounded bg-emerald-200 text-emerald-800 dark:bg-emerald-800 dark:text-emerald-100">当前</span>
                          {/if}
                        </div>
                        {#if ver.change_summary}
                          <div class="text-[10px] text-gray-500 dark:text-gray-400 truncate">{ver.change_summary}</div>
                        {/if}
                        <div class="text-[9px] text-gray-400">{formatDateTime(ver.created_at)}</div>
                      </div>
                      <div class="flex items-center gap-1 shrink-0 ml-1">
                        {#if ver.id !== resolved.mod.moduleVersionId}
                          <button
                            class="text-[10px] px-1.5 py-0.5 rounded border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
                            onclick={() => handleSwitchModuleVersion(resolved.mod.entryId!, ver.id)}
                            disabled={isVersionActionLoading}
                            title="切换到该版本"
                          >切换</button>
                        {/if}
                        <button
                          class="text-[10px] px-1.5 py-0.5 rounded border border-red-300 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
                          onclick={() => handleDeleteModuleVersion(resolved.mod.entryId!, ver.id)}
                          disabled={isVersionActionLoading}
                          title="删除该版本"
                        >删除</button>
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="text-[10px] text-gray-400 italic">暂无模块版本记录</div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Version history entry -->
        {#if resolved.mod.entryId}
          <div class="pt-2 border-t border-gray-100 dark:border-gray-800">
            <button
              class="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              onclick={() => versionHistoryEntity = { type: 'module', id: resolved.mod.entryId! }}
            >
              📜 查看版本历史
            </button>
          </div>
        {/if}

        <div class="pt-2 border-t border-gray-100 dark:border-gray-800">
          <div class="text-[10px] text-gray-400">
            ID: {resolved.mod.id}
          </div>
          {#if resolved.mod.entryId}
            <div class="text-[10px] text-gray-400">
              Entry ID: {resolved.mod.entryId}
            </div>
          {/if}
        </div>
      {:else if resolved.kind === 'feature'}
        <!-- FEATURE VIEW -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">类型</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">功能</span>
        </div>

        <!-- Current version -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">当前版本</span>
          <span class="px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 font-medium">
            {resolved.feat!.currentVersionNumber || (resolved.feat!.versionId ? resolved.feat!.versionId.slice(0, 8) : '—')}
          </span>
        </div>

        <!-- ===== 功能版本管理（翡翠绿卡片，与模块版本管理样式一致） ===== -->
        {#if resolved.feat!.entryId && projectMeta?.projectId}
          <div class="pt-3 border-t border-gray-200 dark:border-gray-700">
            <div class="rounded-md border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10 p-3 space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <span class="inline-flex items-center justify-center w-4 h-4 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">F</span>
                  <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">功能版本管理</span>
                </div>
              </div>

              <!-- ① 当前模块版本（功能继承自父模块） -->
              <div class="text-[11px] text-gray-600 dark:text-gray-400">
                当前模块版本:
                <span class="ml-1 px-1.5 py-0.5 rounded font-mono font-medium {resolved.mod.moduleVersionId ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}">
                  {resolved.mod.moduleVersionId ? resolved.mod.moduleVersionId.slice(0, 8) : '未绑定'}
                </span>
              </div>

              <!-- ② 子参数版本数（功能下绑定到模块版本的参数数量） -->
              <div class="text-[11px] text-gray-500 dark:text-gray-400">
                子参数版本数: <span class="font-medium text-gray-700 dark:text-gray-300">{resolved.feat!.parameters.filter(p => p.moduleVersionId).length}</span> / {resolved.feat!.parameters.length} 参数
              </div>

              <!-- 自身条目版本（PMEntryVersion，自动创建的修订历史） -->
              <div class="text-[11px] text-gray-500 dark:text-gray-400">
                自身条目版本:
                <span class="ml-1 px-1.5 py-0.5 rounded font-mono font-medium bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200">
                  {resolved.feat!.versionId ? resolved.feat!.versionId.slice(0, 8) : '—'}
                </span>
                <span class="ml-1 text-gray-400">({resolved.feat!.currentVersionNumber || '无版本号'})</span>
              </div>
            </div>
          </div>
        {/if}

        <!-- Created version -->
        {#if resolved.feat!.createdVersionNumber}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">创建版本</span>
            <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
              {resolved.feat!.createdVersionNumber}
            </span>
          </div>
        {/if}

        <!-- Branch -->
        {#if resolved.feat!.branchName}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">分支</span>
            <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono">
              {resolved.feat!.branchName}
            </span>
          </div>
        {/if}

        <!-- Status -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">状态</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            {statusLabel(resolved.feat!.status)}
          </span>
        </div>

        <!-- Priority -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">优先级</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            {priorityLabel(resolved.feat!.priority)}
          </span>
        </div>

        <!-- Times -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">创建时间</span>
          <span class="text-xs text-gray-700 dark:text-gray-300">{formatDateTime(resolved.feat!.createdAt)}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">更新时间</span>
          <span class="text-xs text-gray-700 dark:text-gray-300">{formatDateTime(resolved.feat!.updatedAt)}</span>
        </div>

        <!-- Description -->
        {#if resolved.feat!.description}
          <div>
            <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">描述</div>
            <p class="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{resolved.feat!.description}</p>
          </div>
        {/if}

        <!-- Related requirements (aggregated from parameters) -->
        {@const relatedReqs = aggregateRelatedRequirements(resolved.feat!)}
        {#if relatedReqs.length > 0}
          <div>
            <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">
              关联需求 ({relatedReqs.length})
            </div>
            <ul class="space-y-1">
              {#each relatedReqs as req}
                <li class="text-xs text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                  <span class="w-1 h-1 rounded-full bg-purple-500"></span>
                  <span class="truncate">{req}</span>
                </li>
              {/each}
            </ul>
          </div>
        {/if}

        <!-- Parameters list -->
        {#if resolved.feat!.parameters.length > 0}
          <div>
            <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">
              参数列表 ({resolved.feat!.parameters.length}) <span class="text-[10px] text-gray-400">· 点击查看版本</span>
            </div>
            <ul class="space-y-1.5">
              {#each resolved.feat!.parameters as param}
                <li class="text-xs bg-gray-50 dark:bg-gray-800 rounded p-2 cursor-pointer hover:bg-emerald-50 dark:hover:bg-emerald-900/20 hover:border-emerald-300 dark:hover:border-emerald-700 border border-transparent transition-colors"
                    onclick={() => onSelectNode?.({ nodeType: 'node', moduleId: resolved.mod.id, featureId: resolved.feat!.id, parameterId: param.id })}
                    title="点击查看参数版本详情">
                  <div class="flex items-center gap-1.5 mb-0.5">
                    <span class="font-medium text-gray-800 dark:text-gray-200 truncate">{param.name || param.key}</span>
                    {#if param.required}
                      <span class="text-red-500 text-[10px]">*</span>
                    {/if}
                    {#if param.entryId}
                      <span class="ml-auto text-[9px] px-1 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200 shrink-0">已绑定</span>
                    {/if}
                  </div>
                  <div class="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-gray-500 dark:text-gray-400">
                    <span>键: {param.key || '—'}</span>
                    <span>类型: {param.dataType}</span>
                    {#if param.defaultValue}
                      <span>默认: {param.defaultValue}</span>
                    {/if}
                  </div>
                  {#if param.sourceDocument}
                    <div class="mt-0.5 text-[10px] text-gray-500 dark:text-gray-400">
                      📄 来源: <span class="truncate">{param.sourceDocument}</span>
                    </div>
                  {/if}
                  {#if param.description}
                    <p class="mt-1 text-[11px] text-gray-600 dark:text-gray-300 leading-snug">{param.description}</p>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        {/if}

        <!-- Version history entry -->
        {#if resolved.feat!.entryId}
          <div class="pt-2 border-t border-gray-100 dark:border-gray-800">
            <button
              class="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              onclick={() => versionHistoryEntity = { type: 'function', id: resolved.feat!.entryId! }}
            >
              📜 查看版本历史
            </button>
          </div>
        {/if}

        <div class="pt-2 border-t border-gray-100 dark:border-gray-800">
          <div class="text-[10px] text-gray-400">
            ID: {resolved.feat!.id}
          </div>
          <div class="text-[10px] text-gray-400">
            所属模块ID: {resolved.feat!.moduleId}
          </div>
          {#if resolved.feat!.entryId}
            <div class="text-[10px] text-gray-400">
              Entry ID: {resolved.feat!.entryId}
            </div>
          {/if}
        </div>
      {:else if resolved.kind === 'parameter'}
        <!-- PARAMETER VIEW -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">类型</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">参数</span>
        </div>

        <!-- Basic info -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">名称</span>
          <span class="text-xs text-gray-800 dark:text-gray-200 font-medium">{resolved.param!.name || resolved.param!.key || '—'}</span>
          {#if resolved.param!.required}
            <span class="text-red-500 text-[10px]">*</span>
          {/if}
        </div>

        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">键</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono">
            {resolved.param!.key || '—'}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">参数类型</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            {resolved.param!.type}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-gray-400 text-xs">数据类型</span>
          <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            {resolved.param!.dataType}
          </span>
        </div>

        {#if resolved.param!.defaultValue}
          <div class="flex items-center gap-2">
            <span class="text-gray-500 dark:text-gray-400 text-xs">默认值</span>
            <span class="px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-mono">
              {resolved.param!.defaultValue}
            </span>
          </div>
        {/if}

        {#if resolved.param!.description}
          <div>
            <div class="text-gray-500 dark:text-gray-400 text-xs mb-1">描述</div>
            <p class="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">{resolved.param!.description}</p>
          </div>
        {/if}

        <!-- ===== 参数版本管理（翡翠绿卡片） ===== -->
        {#if resolved.param!.entryId && projectMeta?.projectId}
          <div class="pt-3 border-t border-gray-200 dark:border-gray-700">
            <div class="rounded-md border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10 p-3 space-y-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <span class="inline-flex items-center justify-center w-4 h-4 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">P</span>
                  <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">参数版本管理</span>
                </div>
                <button
                  class="text-[11px] px-2 py-0.5 rounded border border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 disabled:opacity-50"
                  onclick={() => loadParamVersions(resolved.param!.entryId!)}
                  disabled={isLoadingParamVersions}
                >
                  {isLoadingParamVersions ? '加载中...' : '🔄 刷新版本'}
                </button>
              </div>

              <!-- ① 自身模块版本（参数继承自父模块） -->
              <div class="text-[11px] text-gray-600 dark:text-gray-400">
                当前模块版本:
                <span class="ml-1 px-1.5 py-0.5 rounded font-mono font-medium {resolved.param!.moduleVersionId ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}">
                  {resolved.param!.moduleVersionId ? resolved.param!.moduleVersionId.slice(0, 8) : '未绑定'}
                </span>
              </div>

              <!-- ② 自身条目版本（PMEntryVersion，自动创建的修订历史） -->
              <div class="text-[11px] text-gray-500 dark:text-gray-400">
                自身条目版本:
                <span class="ml-1 px-1.5 py-0.5 rounded font-mono font-medium bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200">
                  {resolved.param!.versionId ? resolved.param!.versionId.slice(0, 8) : '—'}
                </span>
                <span class="ml-1 text-gray-400">({resolved.param!.currentVersionNumber || '无版本号'})</span>
              </div>

              <!-- 版本历史列表（从后端拉取，可切换） -->
              {#if paramVersions.length > 0}
                <div class="pt-2 border-t border-emerald-200 dark:border-emerald-800 space-y-1">
                  <div class="text-[10px] text-gray-500 dark:text-gray-400">条目修订历史 ({paramVersions.length})</div>
                  {#each paramVersions as ver}
                    <div class="flex items-center justify-between text-[11px] py-1 px-1.5 rounded hover:bg-emerald-100/50 dark:hover:bg-emerald-900/20">
                      <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-1.5">
                          <span class="font-mono font-medium text-gray-800 dark:text-gray-200">{ver.version_number}</span>
                          {#if ver.id === resolved.param!.versionId}
                            <span class="text-[9px] px-1 rounded bg-emerald-200 text-emerald-800 dark:bg-emerald-800 dark:text-emerald-100">当前</span>
                          {/if}
                        </div>
                        <div class="text-[9px] text-gray-400">{formatDateTime(ver.created_at)}</div>
                      </div>
                      <div class="flex items-center gap-1 shrink-0 ml-1">
                        {#if ver.id !== resolved.param!.versionId}
                          <button
                            class="text-[10px] px-1.5 py-0.5 rounded border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
                            onclick={() => handleSwitchParamVersion(resolved.param!.entryId!, ver.id)}
                            disabled={isSwitchingParamVersion}
                            title="切换到该版本"
                          >切换</button>
                        {/if}
                      </div>
                    </div>
                  {/each}
                </div>
              {:else if !isLoadingParamVersions}
                <div class="text-[10px] text-gray-400 italic pt-1">点击"刷新版本"加载条目修订历史</div>
              {/if}
            </div>
          </div>
        {/if}

        <div class="pt-2 border-t border-gray-100 dark:border-gray-800">
          <div class="text-[10px] text-gray-400">
            ID: {resolved.param!.id}
          </div>
          <div class="text-[10px] text-gray-400">
            所属功能ID: {resolved.param!.featureId}
          </div>
          {#if resolved.param!.entryId}
            <div class="text-[10px] text-gray-400">
              Entry ID: {resolved.param!.entryId}
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </aside>
{/if}

{#if versionHistoryEntity}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="presentation">
    <div class="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
      <VersionHistoryPopover
        entityType={versionHistoryEntity.type}
        entityId={versionHistoryEntity.id}
        onClose={() => versionHistoryEntity = null}
      />
    </div>
  </div>
{/if}
