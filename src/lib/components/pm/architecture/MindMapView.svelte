<script lang="ts">
  import { SvelteFlow, Controls, Background, MiniMap, type Node, type Edge } from '@xyflow/svelte';
  import '@xyflow/svelte/dist/style.css';
  import type { ArchModule, PMRelation } from '$lib/stores/pm/architectureStore';
  import ArchNode from './ArchNode.svelte';

  interface Props {
    modules?: ArchModule[];
    relations?: PMRelation[];
    onNodeClick?: (moduleId: string, featureId?: string) => void;
    readonly?: boolean;
    projectId?: string;
    versionId?: string;
  }

  let { modules = [], relations = [], onNodeClick, readonly = false, projectId = '', versionId }: Props = $props();

  // Custom node types — must be defined outside of $derived/$state to satisfy SvelteFlow
  const nodeTypes = { arch: ArchNode };

  // Build SvelteFlow nodes from ArchModule[]
  function buildNodes(modules: ArchModule[]): Node[] {
    const nodes: Node[] = [{
      id: 'root',
      type: 'arch',
      position: { x: 400, y: 50 },
      data: {
        label: '产品架构',
        nodeType: 'root',
        metadata: {
          versionId,
          source: 'auto',
          paramCount: modules.length
        }
      }
    }];

    modules.forEach((mod, modIdx) => {
      const modId = mod.id || `mod-${modIdx}`;
      const modX = modIdx * 280 + 100;
      nodes.push({
        id: modId,
        type: 'arch',
        position: { x: modX, y: 200 },
        data: {
          label: mod.name,
          nodeType: 'branch',
          moduleId: modId,
          metadata: {
            versionId: mod.versionId,
            currentVersionNumber: mod.currentVersionNumber,
            createdAt: mod.createdAt,
            updatedAt: mod.updatedAt,
            status: mod.status,
            priority: mod.priority,
            source: 'auto',
            paramCount: mod.features?.length || 0,
            description: mod.description
          }
        }
      });

      // Feature nodes (leaf)
      (mod.features || []).forEach((feat, featIdx) => {
        const featId = feat.id || `feat-${modIdx}-${featIdx}`;
        nodes.push({
          id: featId,
          type: 'arch',
          position: { x: modX, y: 300 + featIdx * 70 },
          data: {
            label: feat.name,
            nodeType: 'leaf',
            moduleId: modId,
            featureId: featId,
            metadata: {
              versionId: feat.versionId,
              currentVersionNumber: feat.currentVersionNumber,
              createdAt: feat.createdAt,
              updatedAt: feat.updatedAt,
              status: feat.status,
              priority: feat.priority,
              paramCount: feat.parameters?.length || 0,
              description: feat.description
            }
          }
        });
      });
    });

    return nodes;
  }

  // Build edges from parent-child relationships + cross-module relations
  function buildEdges(modules: ArchModule[], rels: PMRelation[]): Edge[] {
    const edges: Edge[] = [];

    // Map entryId → flow node id so relations (which reference entry ids)
    // can be rendered as cross-module edges.
    const entryIdToNodeId = new Map<string, string>();
    modules.forEach((mod, modIdx) => {
      const modId = mod.id || `mod-${modIdx}`;
      if (mod.entryId) entryIdToNodeId.set(mod.entryId, modId);
      (mod.features || []).forEach((feat, featIdx) => {
        const featId = feat.id || `feat-${modIdx}-${featIdx}`;
        if (feat.entryId) entryIdToNodeId.set(feat.entryId, featId);
      });
    });

    modules.forEach((mod, modIdx) => {
      const modId = mod.id || `mod-${modIdx}`;
      // root -> module
      edges.push({
        id: `e-root-${modId}`,
        source: 'root',
        target: modId,
        type: 'smoothstep',
        style: { stroke: '#9ca3af', strokeWidth: 2 }
      });

      // module -> features
      (mod.features || []).forEach((feat, featIdx) => {
        const featId = feat.id || `feat-${modIdx}-${featIdx}`;
        edges.push({
          id: `e-${modId}-${featId}`,
          source: modId,
          target: featId,
          type: 'smoothstep',
          style: { stroke: '#d1d5db', strokeWidth: 1 }
        });
      });
    });

    // Cross-module relation edges (dashed, colored by relation_type)
    const relationStyles: Record<string, { stroke: string; label?: string }> = {
      references: { stroke: '#8b5cf6', label: '引用' },
      derives: { stroke: '#f59e0b', label: '派生' },
      modifies: { stroke: '#ec4899', label: '修改' },
      conflicts: { stroke: '#ef4444', label: '冲突' },
      contains: { stroke: '#14b8a6', label: '包含' }
    };

    rels.forEach((rel, relIdx) => {
      const sourceNodeId = entryIdToNodeId.get(rel.entity_a_id);
      const targetNodeId = entryIdToNodeId.get(rel.entity_b_id);
      if (!sourceNodeId || !targetNodeId || sourceNodeId === targetNodeId) return;

      const style = relationStyles[rel.relation_type] || { stroke: '#6366f1' };
      edges.push({
        id: `e-rel-${relIdx}-${rel.id}`,
        source: sourceNodeId,
        target: targetNodeId,
        type: 'smoothstep',
        animated: true,
        style: { stroke: style.stroke, strokeWidth: 2, strokeDasharray: '6 4' },
        label: style.label,
        labelStyle: { fill: style.stroke, fontWeight: 600 },
        labelBgStyle: { fill: '#fff' }
      });
    });

    return edges;
  }

  // Reactive nodes and edges
  let nodes = $derived(buildNodes(modules));
  let edges = $derived(buildEdges(modules, relations));

  function handleNodeClick(event: { node: Node }) {
    const node = event.node;
    const data = node.data as any;
    if (!data) return;

    if (data.nodeType === 'root') {
      // Use a sentinel moduleId to signal "root clicked" — caller detects
      // the sentinel and opens the project-level sidebar view.
      onNodeClick?.('__root__');
    } else if (data.nodeType === 'branch') {
      onNodeClick?.(data.moduleId);
    } else if (data.nodeType === 'leaf') {
      onNodeClick?.(data.moduleId, data.featureId);
    }
  }
</script>

<div class="w-full h-full relative">
  {#if modules.length === 0}
    <div class="flex flex-col items-center justify-center h-full text-gray-400">
      <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h7" />
      </svg>
      <p class="text-sm">暂无架构数据</p>
      <p class="text-xs mt-1">请先在参数配置或产品架构模块中添加数据</p>
    </div>
  {:else}
    <SvelteFlow
      {nodes}
      {edges}
      {nodeTypes}
      onnodeclick={handleNodeClick}
      nodesDraggable={!readonly}
      nodesConnectable={false}
      elementsSelectable={!readonly}
      minZoom={0.1}
      maxZoom={2}
      fitView={true}
      proOptions={{ hideAttribution: true }}
    >
      <Background patternColor="#e5e7eb" gap={20} />
      <Controls />
      <MiniMap
        maskColor="rgba(0, 0, 0, 0.1)"
        nodeColor={(node: Node) => {
          const t = (node.data as any)?.nodeType;
          if (t === 'root') return '#3b82f6';
          if (t === 'branch') return '#22c55e';
          return '#eab308';
        }}
      />
    </SvelteFlow>
  {/if}
</div>
