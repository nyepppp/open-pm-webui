<script lang="ts">
  import type { NodeTemplate, NodeCategory } from './types';
  import { NODE_CATEGORIES } from './types';

  // ===== Props =====
  interface Props {
    collapsed?: boolean;
    onToggleCollapse?: () => void;
    onNodeDragStart?: (node: NodeTemplate, clientX: number, clientY: number) => void;
    onNodeSelect?: (node: NodeTemplate) => void;
  }

  let { collapsed = false, onToggleCollapse, onNodeDragStart, onNodeSelect }: Props = $props();

  // ===== State =====
  let searchQuery = $state('');
  let expandedCategories = $state<Set<string>>(new Set(['control']));
  let hoveredNode = $state<NodeTemplate | null>(null);
  let tooltipPosition = $state({ x: 0, y: 0 });

  // ===== Derived =====
  const filteredCategories = $derived(() => {
    if (!searchQuery.trim()) return NODE_CATEGORIES;
    const query = searchQuery.toLowerCase();
    return NODE_CATEGORIES
      .map(cat => ({
        ...cat,
        nodes: cat.nodes.filter(
          n =>
            n.label.toLowerCase().includes(query) ||
            n.description.toLowerCase().includes(query) ||
            n.type.toLowerCase().includes(query)
        )
      }))
      .filter(cat => cat.nodes.length > 0);
  });

  // ===== Event Handlers =====
  function toggleCategory(categoryId: string) {
    const newSet = new Set(expandedCategories);
    if (newSet.has(categoryId)) {
      newSet.delete(categoryId);
    } else {
      newSet.add(categoryId);
    }
    expandedCategories = newSet;
  }

  function handleDragStart(event: DragEvent, node: NodeTemplate) {
    if (!event.dataTransfer) return;
    event.dataTransfer.setData('application/json', JSON.stringify(node));
    event.dataTransfer.effectAllowed = 'copy';
    onNodeDragStart?.(node, event.clientX, event.clientY);
  }

  function handleNodeClick(node: NodeTemplate) {
    onNodeSelect?.(node);
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

  // ===== Icon helpers =====
  function getCategoryIcon(icon: string): string {
    const iconMap: Record<string, string> = {
      control: '🎮',
      sparkles: '✨',
      wrench: '🔧',
      ai: '🤖',
      tools: '🔨'
    };
    return iconMap[icon] || '📦';
  }

  function getNodeIcon(icon: string): string {
    const iconMap: Record<string, string> = {
      play: '▶️',
      stop: '⏹️',
      brain: '🧠',
      'git-branch': '🔀',
      variable: '📝',
      bot: '🤖',
      wrench: '🔧'
    };
    return iconMap[icon] || '📦';
  }
</script>

<div
  class="node-sidebar"
  class:collapsed
  onmousemove={handleMouseMove}
>
  <!-- Header -->
  <div class="sidebar-header">
    {#if !collapsed}
      <h2 class="sidebar-title">Node Library</h2>
    {/if}
    <button
      class="collapse-btn"
      onclick={onToggleCollapse}
      title={collapsed ? 'Expand' : 'Collapse'}
      aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
    >
      <svg
        class="collapse-icon"
        class:rotated={collapsed}
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
    <div class="search-container">
      <div class="search-input-wrapper">
        <input
          type="text"
          placeholder="Search nodes..."
          class="search-input"
          bind:value={searchQuery}
          aria-label="Search nodes"
        />
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- Categories -->
    <div class="categories-container">
      {#each filteredCategories() as category (category.id)}
        <div class="category-section">
          <!-- Category Header -->
          <button
            class="category-header"
            onclick={() => toggleCategory(category.id)}
            aria-expanded={expandedCategories.has(category.id)}
          >
            <div class="category-title">
              <span class="category-icon">{getCategoryIcon(category.icon)}</span>
              <span class="category-label">{category.label}</span>
              <span class="category-count">({category.nodes.length})</span>
            </div>
            <svg
              class="category-arrow"
              class:expanded={expandedCategories.has(category.id)}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Node List -->
          {#if expandedCategories.has(category.id)}
            <div class="node-list">
              {#each category.nodes as node (node.id)}
                <div
                  class="node-item"
                  draggable="true"
                  ondragstart={(e) => handleDragStart(e, node)}
                  onclick={() => handleNodeClick(node)}
                  onmouseenter={(e) => handleMouseEnter(e, node)}
                  onmouseleave={handleMouseLeave}
                  role="button"
                  tabindex="0"
                  aria-label={`${node.label} - ${node.description}`}
                >
                  <!-- Color indicator -->
                  <div
                    class="node-color-indicator"
                    style="background-color: {node.color}"
                  ></div>

                  <!-- Icon -->
                  <span class="node-icon">{getNodeIcon(node.icon)}</span>

                  <!-- Label -->
                  <div class="node-info">
                    <div class="node-label">{node.label}</div>
                    <div class="node-type-text">{node.type}</div>
                  </div>

                  <!-- Drag hint -->
                  <svg
                    class="drag-hint"
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
    <div class="sidebar-footer">
      <p class="footer-text">Drag nodes to canvas</p>
    </div>
  {:else}
    <!-- Collapsed state - icon only -->
    <div class="collapsed-icons">
      {#each NODE_CATEGORIES as category (category.id)}
        <div class="collapsed-item" title={category.label}>
          <span class="collapsed-icon">{getCategoryIcon(category.icon)}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Tooltip -->
{#if hoveredNode && !collapsed}
  <div
    class="node-tooltip"
    style="left: {tooltipPosition.x + 16}px; top: {tooltipPosition.y - 8}px;"
  >
    <div class="tooltip-title">{hoveredNode.label}</div>
    <div class="tooltip-desc">{hoveredNode.description}</div>
    <div class="tooltip-type">Type: {hoveredNode.type}</div>
  </div>
{/if}

<style>
  .node-sidebar {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
    transition: width 0.3s ease;
    width: 280px;
    overflow: hidden;
  }

  .node-sidebar.collapsed {
    width: 56px;
  }

  /* Header */
  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid #e5e7eb;
    flex-shrink: 0;
  }

  .sidebar-title {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
    margin: 0;
  }

  .collapse-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px;
    border: none;
    background: transparent;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.15s ease;
    color: #6b7280;
  }

  .collapse-btn:hover {
    background-color: #f3f4f6;
  }

  .collapse-icon {
    width: 20px;
    height: 20px;
    transition: transform 0.3s ease;
  }

  .collapse-icon.rotated {
    transform: rotate(180deg);
  }

  /* Search */
  .search-container {
    padding: 8px 16px;
    flex-shrink: 0;
  }

  .search-input-wrapper {
    position: relative;
  }

  .search-input {
    width: 100%;
    padding: 6px 12px 6px 32px;
    font-size: 13px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background-color: #f9fafb;
    color: #111827;
    outline: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
    box-sizing: border-box;
  }

  .search-input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }

  .search-input::placeholder {
    color: #9ca3af;
  }

  .search-icon {
    position: absolute;
    left: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    color: #9ca3af;
    pointer-events: none;
  }

  /* Categories */
  .categories-container {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }

  .category-section {
    margin-bottom: 4px;
  }

  .category-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 8px 16px;
    border: none;
    background: transparent;
    cursor: pointer;
    transition: background-color 0.15s ease;
    text-align: left;
  }

  .category-header:hover {
    background-color: #f9fafb;
  }

  .category-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 500;
    color: #374151;
  }

  .category-icon {
    font-size: 16px;
    line-height: 1;
  }

  .category-label {
    font-weight: 500;
  }

  .category-count {
    font-size: 11px;
    color: #9ca3af;
    font-weight: 400;
  }

  .category-arrow {
    width: 16px;
    height: 16px;
    color: #9ca3af;
    transition: transform 0.2s ease;
    flex-shrink: 0;
  }

  .category-arrow.expanded {
    transform: rotate(180deg);
  }

  /* Node List */
  .node-list {
    padding: 4px 12px;
  }

  .node-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: grab;
    transition: background-color 0.15s ease;
    margin-bottom: 4px;
  }

  .node-item:hover {
    background-color: #f3f4f6;
  }

  .node-item:active {
    cursor: grabbing;
  }

  .node-color-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .node-icon {
    font-size: 16px;
    line-height: 1;
    flex-shrink: 0;
  }

  .node-info {
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  .node-label {
    font-size: 13px;
    font-weight: 500;
    color: #111827;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .node-type-text {
    font-size: 11px;
    color: #6b7280;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .drag-hint {
    width: 16px;
    height: 16px;
    color: #d1d5db;
    opacity: 0;
    transition: opacity 0.15s ease;
    flex-shrink: 0;
  }

  .node-item:hover .drag-hint {
    opacity: 1;
  }

  /* Footer */
  .sidebar-footer {
    padding: 8px 16px;
    border-top: 1px solid #e5e7eb;
    flex-shrink: 0;
  }

  .footer-text {
    font-size: 11px;
    color: #9ca3af;
    text-align: center;
    margin: 0;
  }

  /* Collapsed state */
  .collapsed-icons {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 0;
    gap: 8px;
    flex: 1;
  }

  .collapsed-item {
    padding: 8px;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .collapsed-item:hover {
    background-color: #f3f4f6;
  }

  .collapsed-icon {
    font-size: 20px;
    line-height: 1;
  }

  /* Tooltip */
  .node-tooltip {
    position: fixed;
    z-index: 50;
    background-color: #1f2937;
    color: white;
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    pointer-events: none;
    max-width: 240px;
    font-size: 12px;
  }

  .tooltip-title {
    font-weight: 600;
    margin-bottom: 4px;
    color: #f9fafb;
  }

  .tooltip-desc {
    color: #d1d5db;
    margin-bottom: 4px;
    line-height: 1.4;
  }

  .tooltip-type {
    color: #9ca3af;
    font-size: 11px;
  }

  /* Scrollbar */
  .categories-container::-webkit-scrollbar {
    width: 4px;
  }

  .categories-container::-webkit-scrollbar-track {
    background: transparent;
  }

  .categories-container::-webkit-scrollbar-thumb {
    background-color: rgba(156, 163, 175, 0.5);
    border-radius: 2px;
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .node-sidebar {
      background-color: #111827;
      border-right-color: #374151;
    }

    .sidebar-title {
      color: #f9fafb;
    }

    .collapse-btn {
      color: #9ca3af;
    }

    .collapse-btn:hover {
      background-color: #1f2937;
    }

    .search-input {
      background-color: #1f2937;
      border-color: #374151;
      color: #f9fafb;
    }

    .search-input::placeholder {
      color: #6b7280;
    }

    .category-header:hover {
      background-color: #1f2937;
    }

    .category-title {
      color: #d1d5db;
    }

    .node-item:hover {
      background-color: #1f2937;
    }

    .node-label {
      color: #f9fafb;
    }

    .node-type-text {
      color: #9ca3af;
    }

    .sidebar-footer {
      border-top-color: #374151;
    }

    .collapsed-item:hover {
      background-color: #1f2937;
    }
  }
</style>
