<script lang="ts">
  /**
   * WorkflowNodeSidebar - 工作流节点侧边栏
   *
   * 提供可拖拽的工作流节点面板，整合：
   * - PM 工作台模块节点（需求、PRD、测试用例等）
   * - OpenWebUI 节点（Agent、模型、知识库等）
   * - 通用控制节点（开始、结束、条件、循环等）
   *
   * 特性：
   * - 分类折叠/展开
   * - 拖拽到画布创建节点
   * - 搜索过滤
   * - 节点描述提示
   */

  import { createEventDispatcher } from 'svelte';

  // ===== 节点类型定义 =====
  interface NodeTemplate {
    id: string;
    type: string;
    label: string;
    description: string;
    icon: string;
    color: string;
    category: string;
    config?: Record<string, unknown>;
  }

  interface NodeCategory {
    id: string;
    label: string;
    icon: string;
    nodes: NodeTemplate[];
  }

  // ===== Props =====
  interface Props {
    collapsed?: boolean;
    onToggleCollapse?: () => void;
  }

  let { collapsed = false, onToggleCollapse }: Props = $props();

  // ===== 搜索 =====
  let searchQuery = $state('');

  // ===== PM 模块节点 =====
  const pmModuleNodes: NodeTemplate[] = [
    {
      id: 'pm-requirement',
      type: 'pm_module',
      label: '需求管理',
      description: '读取或写入需求模块数据',
      icon: '📋',
      color: '#3b82f6',
      category: 'pm',
      config: { module_type: 'requirement', operation: 'read' },
    },
    {
      id: 'pm-prd',
      type: 'pm_module',
      label: 'PRD 文档',
      description: '读取或写入 PRD 模块数据',
      icon: '📄',
      color: '#8b5cf6',
      category: 'pm',
      config: { module_type: 'prd', operation: 'read' },
    },
    {
      id: 'pm-testcase',
      type: 'pm_module',
      label: '测试用例',
      description: '读取或写入测试用例模块数据',
      icon: '✅',
      color: '#10b981',
      category: 'pm',
      config: { module_type: 'testcase', operation: 'read' },
    },
    {
      id: 'pm-parameter',
      type: 'pm_module',
      label: '参数配置',
      description: '读取或写入参数模块数据',
      icon: '⚙️',
      color: '#f59e0b',
      category: 'pm',
      config: { module_type: 'parameter', operation: 'read' },
    },
    {
      id: 'pm-roadmap',
      type: 'pm_module',
      label: '路线图',
      description: '读取或写入路线图模块数据',
      icon: '🗺️',
      color: '#ef4444',
      category: 'pm',
      config: { module_type: 'roadmap', operation: 'read' },
    },
    {
      id: 'pm-risk',
      type: 'pm_module',
      label: '风险管理',
      description: '读取或写入风险模块数据',
      icon: '⚠️',
      color: '#f97316',
      category: 'pm',
      config: { module_type: 'risk', operation: 'read' },
    },
  ];

  // ===== OpenWebUI 节点 =====
  const openWebUINodes: NodeTemplate[] = [
    {
      id: 'owui-agent',
      type: 'agent_call',
      label: 'Agent 调用',
      description: '调用 OpenWebUI Agent 进行推理',
      icon: '🤖',
      color: '#2196f3',
      category: 'openwebui',
      config: { agent_type: 'chat', model: '' },
    },
    {
      id: 'owui-model',
      type: 'model_call',
      label: '模型调用',
      description: '直接调用 LLM 模型',
      icon: '🧠',
      color: '#9c27b0',
      category: 'openwebui',
      config: { model: '', temperature: 0.7 },
    },
    {
      id: 'owui-knowledge',
      type: 'knowledge_query',
      label: '知识库查询',
      description: '从知识库检索相关信息',
      icon: '📚',
      color: '#4caf50',
      category: 'openwebui',
      config: { knowledge_id: '', top_k: 5 },
    },
    {
      id: 'owui-prompt',
      type: 'prompt_template',
      label: '提示词模板',
      description: '使用预定义提示词模板',
      icon: '💬',
      color: '#ff9800',
      category: 'openwebui',
      config: { template_id: '', variables: {} },
    },
    {
      id: 'owui-tool',
      type: 'tool_call',
      label: '工具调用',
      description: '调用 OpenWebUI 工具',
      icon: '🔧',
      color: '#607d8b',
      category: 'openwebui',
      config: { tool_id: '', parameters: {} },
    },
    {
      id: 'owui-skill',
      type: 'skill_call',
      label: '技能调用',
      description: '调用 PM 技能（如生成测试用例）',
      icon: '⚡',
      color: '#00bcd4',
      category: 'openwebui',
      config: { skill_id: '', parameters: {} },
    },
  ];

  // ===== 控制节点 =====
  const controlNodes: NodeTemplate[] = [
    {
      id: 'ctrl-start',
      type: 'start',
      label: '开始',
      description: '工作流入口节点',
      icon: '🟢',
      color: '#4caf50',
      category: 'control',
    },
    {
      id: 'ctrl-end',
      type: 'end',
      label: '结束',
      description: '工作流出口节点',
      icon: '🔴',
      color: '#f44336',
      category: 'control',
    },
    {
      id: 'ctrl-condition',
      type: 'condition',
      label: '条件分支',
      description: '根据条件选择分支',
      icon: '🔀',
      color: '#ff5722',
      category: 'control',
      config: { condition: '' },
    },
    {
      id: 'ctrl-loop',
      type: 'loop',
      label: '循环',
      description: '循环执行子工作流',
      icon: '🔄',
      color: '#795548',
      category: 'control',
      config: { max_iterations: 10, condition: '' },
    },
    {
      id: 'ctrl-parallel',
      type: 'parallel_merge',
      label: '并行聚合',
      description: '并行执行多个分支并聚合结果',
      icon: '⏩',
      color: '#607d8b',
      category: 'control',
    },
    {
      id: 'ctrl-delay',
      type: 'delay',
      label: '延迟',
      description: '延迟指定时间后继续',
      icon: '⏱️',
      color: '#9e9e9e',
      category: 'control',
      config: { delay_ms: 1000 },
    },
  ];

  // ===== 数据转换节点 =====
  const transformNodes: NodeTemplate[] = [
    {
      id: 'trans-map',
      type: 'data_transform',
      label: '字段映射',
      description: '映射字段到目标格式',
      icon: '🗺️',
      color: '#ff9800',
      category: 'transform',
      config: { mappings: {} },
    },
    {
      id: 'trans-filter',
      type: 'data_filter',
      label: '数据过滤',
      description: '根据条件过滤数据',
      icon: '🔍',
      color: '#ff5722',
      category: 'transform',
      config: { condition: '' },
    },
    {
      id: 'trans-merge',
      type: 'data_merge',
      label: '数据合并',
      description: '合并多个数据源',
      icon: '🔀',
      color: '#795548',
      category: 'transform',
      config: { merge_strategy: 'append' },
    },
    {
      id: 'trans-split',
      type: 'data_split',
      label: '数据拆分',
      description: '将数据拆分为多个部分',
      icon: '✂️',
      color: '#607d8b',
      category: 'transform',
      config: { split_by: '' },
    },
  ];

  // ===== 分类配置 =====
  const categories: NodeCategory[] = [
    { id: 'control', label: '控制节点', icon: '🎮', nodes: controlNodes },
    { id: 'pm', label: 'PM 模块', icon: '📊', nodes: pmModuleNodes },
    { id: 'openwebui', label: 'OpenWebUI', icon: '⚡', nodes: openWebUINodes },
    { id: 'transform', label: '数据转换', icon: '🔄', nodes: transformNodes },
  ];

  // ===== 状态 =====
  let expandedCategories = $state<Set<string>>(new Set(['control', 'pm']));
  let hoveredNode: NodeTemplate | null = $state(null);
  let tooltipPosition = $state({ x: 0, y: 0 });

  // ===== 过滤后的分类 =====
  const filteredCategories = $derived(() => {
    if (!searchQuery.trim()) return categories;
    const query = searchQuery.toLowerCase();
    return categories.map(cat => ({
      ...cat,
      nodes: cat.nodes.filter(
        n =>
          n.label.toLowerCase().includes(query) ||
          n.description.toLowerCase().includes(query) ||
          n.type.toLowerCase().includes(query)
      ),
    })).filter(cat => cat.nodes.length > 0);
  });

  // ===== 事件 =====
  const dispatch = createEventDispatcher<{
    dragstart: { node: NodeTemplate; clientX: number; clientY: number };
    nodeSelect: NodeTemplate;
  }>();

  function toggleCategory(categoryId: string) {
    expandedCategories = new Set(expandedCategories);
    if (expandedCategories.has(categoryId)) {
      expandedCategories.delete(categoryId);
    } else {
      expandedCategories.add(categoryId);
    }
  }

  function handleDragStart(event: DragEvent, node: NodeTemplate) {
    if (!event.dataTransfer) return;
    event.dataTransfer.setData('application/json', JSON.stringify(node));
    event.dataTransfer.effectAllowed = 'copy';
    dispatch('dragstart', { node, clientX: event.clientX, clientY: event.clientY });
  }

  function handleNodeClick(node: NodeTemplate) {
    dispatch('nodeSelect', node);
  }

  function handleMouseEnter(event: MouseEvent, node: NodeTemplate) {
    hoveredNode = node;
    tooltipPosition = { x: event.clientX, y: event.clientY };
  }

  function handleMouseLeave() {
    hoveredNode = null;
  }

  function handleMouseMove(event: MouseEvent) {
    if (hoveredNode) {
      tooltipPosition = { x: event.clientX, y: event.clientY };
    }
  }
</script>

<div
  class="workflow-node-sidebar flex flex-col h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 {collapsed ? 'w-14' : 'w-72'}"
  onmousemove={handleMouseMove}
>
  <!-- Header -->
  <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
    {#if !collapsed}
      <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">节点库</h2>
    {/if}
    <button
      class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      onclick={onToggleCollapse}
      title={collapsed ? '展开' : '折叠'}
    >
      <svg
        class="w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform duration-300 {collapsed ? 'rotate-180' : ''}"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        {#if collapsed}
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        {:else}
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 7l-7 7-7-7" />
        {/if}
      </svg>
    </button>
  </div>

  {#if !collapsed}
    <!-- Search -->
    <div class="px-4 py-2">
      <div class="relative">
        <input
          type="text"
          placeholder="搜索节点..."
          class="w-full px-3 py-1.5 pl-9 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          bind:value={searchQuery}
        />
        <svg class="absolute left-2.5 top-2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- Categories -->
    <div class="flex-1 overflow-y-auto py-2">
      {#each filteredCategories() as category}
        <div class="mb-1">
          <!-- Category Header -->
          <button
            class="w-full flex items-center justify-between px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            onclick={() => toggleCategory(category.id)}
          >
            <div class="flex items-center gap-2">
              <span class="text-lg">{category.icon}</span>
              <span>{category.label}</span>
              <span class="text-xs text-gray-400 dark:text-gray-500">({category.nodes.length})</span>
            </div>
            <svg
              class="w-4 h-4 text-gray-400 transition-transform duration-200 {expandedCategories.has(category.id) ? 'rotate-180' : ''}"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Node List -->
          {#if expandedCategories.has(category.id)}
            <div class="px-2 py-1 space-y-1">
              {#each category.nodes as node}
                <div
                  class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-grab hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group"
                  draggable="true"
                  ondragstart={(e) => handleDragStart(e, node)}
                  onclick={() => handleNodeClick(node)}
                  onmouseenter={(e) => handleMouseEnter(e as unknown as MouseEvent, node)}
                  onmouseleave={handleMouseLeave}
                  role="button"
                  tabindex="0"
                >
                  <!-- Color indicator -->
                  <div
                    class="w-3 h-3 rounded-full flex-shrink-0"
                    style="background-color: {node.color}"
                  ></div>

                  <!-- Icon -->
                  <span class="text-base">{node.icon}</span>

                  <!-- Label -->
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {node.label}
                    </div>
                    <div class="text-xs text-gray-400 dark:text-gray-500 truncate">
                      {node.type}
                    </div>
                  </div>

                  <!-- Drag hint -->
                  <svg
                    class="w-4 h-4 text-gray-300 dark:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16" />
                  </svg>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <!-- Footer -->
    <div class="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
      <p class="text-xs text-gray-400 dark:text-gray-500 text-center">
        拖拽节点到画布
      </p>
    </div>
  {:else}
    <!-- Collapsed state - icon only -->
    <div class="flex-1 flex flex-col items-center py-4 gap-3">
      {#each categories as category}
        <div class="relative group">
          <button
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title={category.label}
          >
            <span class="text-xl">{category.icon}</span>
          </button>
          <!-- Tooltip -->
          <div class="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
            {category.label}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Tooltip -->
{#if hoveredNode && !collapsed}
  <div
    class="fixed z-50 bg-gray-900 dark:bg-gray-800 text-white text-xs rounded-lg px-3 py-2 shadow-lg pointer-events-none max-w-xs"
    style="left: {tooltipPosition.x + 16}px; top: {tooltipPosition.y - 8}px;"
  >
    <div class="font-medium mb-1">{hoveredNode.label}</div>
    <div class="text-gray-300 dark:text-gray-400">{hoveredNode.description}</div>
    <div class="mt-1 text-gray-400 dark:text-gray-500 text-[10px]">
      类型: {hoveredNode.type}
    </div>
  </div>
{/if}

<style>
  .workflow-node-sidebar {
    scrollbar-width: thin;
    scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
  }

  .workflow-node-sidebar::-webkit-scrollbar {
    width: 4px;
  }

  .workflow-node-sidebar::-webkit-scrollbar-track {
    background: transparent;
  }

  .workflow-node-sidebar::-webkit-scrollbar-thumb {
    background-color: rgba(156, 163, 175, 0.5);
    border-radius: 2px;
  }
</style>
