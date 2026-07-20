<script lang="ts">
  import type { WorkflowNode, WorkflowEdge, NodeType } from './types';
  import { NODE_TYPE_LABELS, NODE_TYPE_COLORS, NODE_CATEGORIES } from './types';
  import NodeOutputPicker from './NodeOutputPicker.svelte';
  import { goto } from '$app/navigation';
  import {
    getExtensions,
    type Extension,
    type ExtensionType,
    type ExtensionSpecField
  } from '$lib/apis/workflow/index';
  import { models } from '$lib/stores';

  // 模型选项（用于 LLM / parameter_extractor 节点的下拉框）
  let modelOptions = $derived($models || []);

  // ===== Props =====
  interface Props {
    node: WorkflowNode | null;
    nodes?: WorkflowNode[];
    edges?: WorkflowEdge[];
    onNodeUpdate?: (nodeId: string, updates: Partial<WorkflowNode>) => void;
    onNodeFocus?: (nodeId: string) => void;
    // FAIL-2: 输出项跳转回调，由父组件传入则使用父组件实现；
    // 不传则 PropertyPanel 内部用 goto 跳转到对应路由。
    onJumpToTarget?: (target: { kind: string; value: string }) => void;
  }

  let { node, nodes = [], edges = [], onNodeUpdate, onNodeFocus, onJumpToTarget }: Props = $props();

  // ===== Variable Picker State =====
  // Tracks which textarea's picker is currently open (null = closed).
  // Format: `<configKey>` for simple textareas; `input_mapping:<fieldName>` for extension input fields.
  let activePickerField = $state<string | null>(null);

  // ===== Extension Lists (Part A) =====
  // 懒加载的 openwebui 扩展资源列表。按需在节点切换时加载。
  let toolsList = $state<Extension[]>([]);
  let functionsList = $state<Extension[]>([]);
  let skillsList = $state<Extension[]>([]);
  let mcpList = $state<Extension[]>([]);
  let extensionsLoading = $state<Record<ExtensionType, boolean>>({
    tools: false,
    functions: false,
    skills: false,
    mcp: false
  });
  let extensionsError = $state<Record<ExtensionType, string | null>>({
    tools: null,
    functions: null,
    skills: null,
    mcp: null
  });

  // 当切换到扩展节点时，加载对应的扩展列表。
  $effect(() => {
    if (!node) return;
    const t = node.type;
    if (t === 'tool_call') loadExtensionList('tools');
    else if (t === 'function_call') loadExtensionList('functions');
    else if (t === 'skill_call') loadExtensionList('skills');
    else if (t === 'mcp_call') {
      loadExtensionList('mcp');
    }
  });

  async function loadExtensionList(type: ExtensionType) {
    if (extensionsLoading[type]) return;
    // 已加载则跳过
    if (
      (type === 'tools' && toolsList.length > 0) ||
      (type === 'functions' && functionsList.length > 0) ||
      (type === 'skills' && skillsList.length > 0) ||
      (type === 'mcp' && mcpList.length > 0)
    ) return;

    extensionsLoading = { ...extensionsLoading, [type]: true };
    extensionsError = { ...extensionsError, [type]: null };
    try {
      const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
      const list = await getExtensions(token, type);
      if (type === 'tools') toolsList = list;
      else if (type === 'functions') functionsList = list;
      else if (type === 'skills') skillsList = list;
      else if (type === 'mcp') mcpList = list;
    } catch (e: any) {
      extensionsError = { ...extensionsError, [type]: e?.message || '加载失败' };
    } finally {
      extensionsLoading = { ...extensionsLoading, [type]: false };
    }
  }

  // ===== Derived =====
  const nodeTypeLabel = $derived(() => {
    if (!node) return '';
    return NODE_TYPE_LABELS[node.type] || node.type;
  });

  const nodeColor = $derived(() => {
    if (!node) return '#6b7280';
    return NODE_TYPE_COLORS[node.type] || '#6b7280';
  });

  // MCP server 分组（二级联动）：按 server_id 分组
  const mcpServers = $derived(() => {
    const map = new Map<string, { id: string; name: string; tools: Extension[] }>();
    for (const ext of mcpList) {
      const sid = ext.server_id || '';
      if (!sid) continue;
      if (!map.has(sid)) {
        map.set(sid, { id: sid, name: ext.server_name || sid, tools: [] });
      }
      map.get(sid)!.tools.push(ext);
    }
    return Array.from(map.values());
  });

  // 当前 MCP server 选中后，可选的 tools 列表
  const currentMcpTools = $derived(() => {
    if (!node || node.type !== 'mcp_call') return [];
    const sid = (node.config?.server_id as string) || '';
    if (!sid) return [];
    return mcpList.filter(e => (e.server_id || '') === sid);
  });

  // 当前选中扩展节点对应的 spec 字段（用于渲染入参表单）
  const currentExtensionSpec = $derived((): ExtensionSpecField[] => {
    if (!node) return [];
    const t = node.type;
    const extId = (node.config?.extension_id as string) || '';
    if (!extId) return [];
    let list: Extension[] = [];
    if (t === 'tool_call') list = toolsList;
    else if (t === 'function_call') list = functionsList;
    else if (t === 'skill_call') list = skillsList;
    else if (t === 'mcp_call') list = mcpList;
    const found = list.find(e => e.id === extId);
    return found?.spec || [];
  });

  // PM module types available in the workspace
  const PM_MODULE_TYPES = [
    'prd', 'requirement', 'requirement-boundary', 'roadmap', 'parameter',
    'architecture', 'prototype', 'competitor', 'spec', 'flowchart',
    'schedule', 'testcase', 'risk', 'meeting', 'acceptance', 'faq'
  ];

  // ===== Event Handlers =====
  function handleNameChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (node && onNodeUpdate) {
      onNodeUpdate(node.id, { name: target.value });
    }
  }

  function handleDescriptionChange(event: Event) {
    const target = event.target as HTMLTextAreaElement;
    if (node && onNodeUpdate) {
      onNodeUpdate(node.id, { description: target.value });
    }
  }

  // Update a single config key (shallow merge into config).
  function updateConfig(key: string, value: unknown) {
    if (!node || !onNodeUpdate) return;
    const newConfig = { ...(node.config || {}), [key]: value };
    onNodeUpdate(node.id, { config: newConfig });
  }

  // Replace the entire config object — used for JSON-based fields.
  function replaceConfig(newConfig: Record<string, unknown>) {
    if (!node || !onNodeUpdate) return;
    onNodeUpdate(node.id, { config: newConfig });
  }

  // Parse a JSON textarea; on failure, keep the prior value and surface the error.
  function parseJsonSafe(raw: string, fallback: unknown): unknown {
    try {
      return JSON.parse(raw || 'null');
    } catch {
      return fallback;
    }
  }

  function jsonString(value: unknown): string {
    if (value === null || value === undefined) return '';
    if (typeof value === 'string') return value;
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  // ===== Variable Picker Helpers =====
  // Append a {{node_id.field}} reference to the end of a textarea's bound config field.
  // Simple and reliable under Svelte 5 runes; cursor-position insertion can be added later.
  function insertVariable(fieldKey: string, variableRef: string) {
    if (!node) return;
    const currentConfig = node.config || {};
    const currentValue = (currentConfig[fieldKey] as string) || '';
    const newValue = currentValue + `{{${variableRef}}}`;
    updateConfig(fieldKey, newValue);
    activePickerField = null;
  }

  // 为扩展节点的 input_mapping.<fieldName> 插入变量引用。
  // input_mapping 结构: { fieldName: string | {{ref}} }
  function insertInputMappingVariable(fieldName: string, variableRef: string) {
    if (!node) return;
    const config = node.config || {};
    const inputMapping = ((config.input_mapping as Record<string, string>) || {});
    const currentValue = inputMapping[fieldName] || '';
    const newMapping = { ...inputMapping, [fieldName]: currentValue + `{{${variableRef}}}` };
    updateConfig('input_mapping', newMapping);
    activePickerField = null;
  }

  function togglePicker(fieldKey: string) {
    activePickerField = activePickerField === fieldKey ? null : fieldKey;
  }

  // ===== Extension Dropdown Handlers =====
  function handleExtensionSelect(extType: ExtensionType, extensionId: string) {
    if (!node || !onNodeUpdate) return;
    const config = { ...(node.config || {}) };
    config.extension_id = extensionId;
    // 切换扩展时重置 input_mapping（旧字段可能不再适用）
    config.input_mapping = {};
    onNodeUpdate(node.id, { config });
  }

  function handleMcpServerSelect(serverId: string) {
    if (!node || !onNodeUpdate) return;
    const config = { ...(node.config || {}) };
    config.server_id = serverId;
    // 切换 server 时重置 extension_id 和 input_mapping
    config.extension_id = '';
    config.input_mapping = {};
    onNodeUpdate(node.id, { config });
  }

  // 更新某个 input_mapping 字段的值
  function updateInputMappingField(fieldName: string, value: string) {
    if (!node || !onNodeUpdate) return;
    const config = node.config || {};
    const inputMapping = ((config.input_mapping as Record<string, string>) || {});
    const newMapping = { ...inputMapping, [fieldName]: value };
    updateConfig('input_mapping', newMapping);
  }

  // ===== 上下游面板 (Part B) =====
  // 反向 BFS 找出当前节点的所有上游节点（复用 NodeOutputPicker 的算法）
  function findUpstreamNodes(currentNodeId: string): WorkflowNode[] {
    const visited = new Set<string>();
    const queue = [currentNodeId];
    const upstream: WorkflowNode[] = [];
    const MAX_DEPTH = 10;
    let depth = 0;
    while (queue.length > 0 && depth < MAX_DEPTH) {
      const cur = queue.shift()!;
      if (visited.has(cur)) continue;
      visited.add(cur);
      const incomingEdges = edges.filter(e => e.targetNodeId === cur);
      for (const edge of incomingEdges) {
        const sourceNode = nodes.find(n => n.id === edge.sourceNodeId);
        if (sourceNode && !visited.has(sourceNode.id)) {
          upstream.push(sourceNode);
          queue.push(sourceNode.id);
        }
      }
      depth++;
    }
    return upstream;
  }

  // 获取节点的输出字段（参考 NodeOutputPicker 实现）
  function getNodeOutputs(n: WorkflowNode) {
    if (n.type === 'template' || n.type === 'parameter_extractor' || n.type === 'code') {
      const varName = (n.config?.output_variable as string) || 'result';
      const type = n.type === 'code' ? 'object' : 'string';
      return [{ name: varName, type, description: '动态输出变量' }];
    }
    if (n.type === 'start') {
      return [{ name: 'input', type: 'string', description: '工作流输入参数' }];
    }
    for (const category of NODE_CATEGORIES) {
      for (const template of category.nodes) {
        if (template.type === n.type) {
          return template.outputs || [];
        }
      }
    }
    return [];
  }

  // 获取节点的输出目标列表（用于输出侧推断）
  function getOutputTargets(n: WorkflowNode): Array<{ label: string; kind: 'pm_module' | 'openwebui_resource' | 'variable' | 'answer'; value: string }> {
    if (!n) return [];
    const targets: Array<{ label: string; kind: 'pm_module' | 'openwebui_resource' | 'variable' | 'answer'; value: string }> = [];
    const cfg = n.config || {};
    if (n.type === 'pm_module') {
      const moduleType = (cfg.module_type as string) || '';
      const action = (cfg.action as string) || 'read';
      targets.push({
        label: `PM 模块 / ${moduleType || '?'} (${action})`,
        kind: 'pm_module',
        value: moduleType
      });
    } else if (n.type === 'answer') {
      const wt = (cfg.write_target as string) || '';
      if (wt) {
        targets.push({
          label: `写入 PM 条目 / ${wt}`,
          kind: 'answer',
          value: wt
        });
      } else {
        targets.push({
          label: '最终答案输出（聊天界面）',
          kind: 'answer',
          value: 'chat'
        });
      }
    } else if (n.type === 'tool_call' || n.type === 'function_call' || n.type === 'skill_call' || n.type === 'mcp_call') {
      const extId = (cfg.extension_id as string) || '';
      const labelMap: Record<string, string> = {
        tool_call: 'openwebui Tool',
        function_call: 'openwebui Function',
        skill_call: 'openwebui Skill',
        mcp_call: 'MCP Tool'
      };
      targets.push({
        label: `${labelMap[n.type] || n.type} / ${extId || '?'}`,
        kind: 'openwebui_resource',
        value: extId
      });
    }
    // 默认输出变量
    const outputs = getNodeOutputs(n);
    for (const o of outputs) {
      targets.push({
        label: `变量: ${o.name} (${o.type})`,
        kind: 'variable',
        value: o.name
      });
    }
    return targets;
  }

  const upstreamNodes = $derived(() => {
    if (!node) return [];
    return findUpstreamNodes(node.id);
  });

  const outputTargets = $derived(() => {
    if (!node) return [];
    return getOutputTargets(node);
  });

  function handleFocusUpstream(nodeId: string) {
    onNodeFocus?.(nodeId);
  }

  // FAIL-2: 输出项跳转。若父组件传入 onJumpToTarget 则交给父组件；
  // 否则 PropertyPanel 内部用 goto 直接跳转到对应路由。
  function handleFocusOutput(target: { kind: string; value: string }) {
    // 优先交给父组件实现
    if (onJumpToTarget) {
      onJumpToTarget(target);
      return;
    }
    // 降级：内部用 goto 跳转
    const cfg = (node?.config as Record<string, any>) || {};
    const projectId = (cfg.project_id as string) || '';
    const moduleType = (cfg.module_type as string) || target.value || '';
    switch (target.kind) {
      case 'pm_module':
        // 跳转到 PM 模块列表页
        if (projectId && moduleType) {
          goto(`/pm/${projectId}/${moduleType}`);
        } else if (projectId) {
          goto(`/pm/${projectId}`);
        } else {
          console.log('[PropertyPanel] 跳转 PM 模块失败：缺少 projectId', target);
        }
        break;
      case 'pm_entry':
        // 跳转到 PM 模块详情页（带 entry query 参数）
        if (projectId && moduleType && target.value) {
          goto(`/pm/${projectId}/${moduleType}?entry=${encodeURIComponent(target.value)}`);
        } else {
          console.log('[PropertyPanel] 跳转 PM 条目失败：缺少 projectId/module/entryId', target);
        }
        break;
      case 'answer':
        // answer 节点的 write_target 是 PM 模块名，跳到对应模块列表页
        if (projectId && target.value) {
          goto(`/pm/${projectId}/${target.value}`);
        } else if (projectId) {
          goto(`/pm/${projectId}`);
        } else {
          console.log('[PropertyPanel] 跳转 answer 写入目标失败：缺少 projectId', target);
        }
        break;
      case 'openwebui_resource':
        // 根据当前节点类型推断扩展资源管理页
        if (node?.type === 'tool_call') {
          goto('/admin/tools');
        } else if (node?.type === 'function_call') {
          goto('/admin/functions');
        } else if (node?.type === 'skill_call') {
          goto('/admin/settings/functions');
        } else if (node?.type === 'mcp_call') {
          goto('/admin/settings/connections');
        } else {
          console.log('[PropertyPanel] 跳转 openwebui 资源失败：未知节点类型', node?.type, target);
        }
        break;
      case 'variable':
      default:
        // 变量类输出不跳转，仅日志
        console.log('[PropertyPanel] variable 输出，无跳转目标', target);
        break;
    }
  }
</script>

<div class="property-panel">
  {#if node}
    <!-- Header -->
    <div class="panel-header">
      <div class="node-type-badge" style="background-color: {nodeColor()}">
        {nodeTypeLabel()}
      </div>
      <h3 class="panel-title">Properties</h3>
    </div>

    <!-- Basic Properties -->
    <div class="property-section">
      <h4 class="section-title">Basic</h4>

      <div class="property-field">
        <label class="field-label" for="node-name">Name</label>
        <input
          id="node-name"
          type="text"
          class="field-input"
          value={node.name}
          onchange={handleNameChange}
        />
      </div>

      <div class="property-field">
        <label class="field-label" for="node-type">Type</label>
        <input
          id="node-type"
          type="text"
          class="field-input"
          value={nodeTypeLabel()}
          readonly
          disabled
        />
      </div>

      <div class="property-field">
        <label class="field-label" for="node-id">ID</label>
        <input
          id="node-id"
          type="text"
          class="field-input field-input--mono"
          value={node.id}
          readonly
          disabled
        />
      </div>

      <div class="property-field">
        <label class="field-label" for="node-description">Description</label>
        <textarea
          id="node-description"
          class="field-textarea"
          value={node.description || ''}
          onchange={handleDescriptionChange}
          rows="3"
          placeholder="Add a description..."
        ></textarea>
      </div>
    </div>

    <!-- Position -->
    <div class="property-section">
      <h4 class="section-title">Position</h4>
      <div class="position-grid">
        <div class="property-field">
          <label class="field-label" for="node-x">X</label>
          <input id="node-x" type="number" class="field-input" value={node.x} readonly disabled />
        </div>
        <div class="property-field">
          <label class="field-label" for="node-y">Y</label>
          <input id="node-y" type="number" class="field-input" value={node.y} readonly disabled />
        </div>
      </div>
    </div>

    <!-- Type-specific Configuration -->
    <div class="property-section">
      <h4 class="section-title">Configuration</h4>

      {#if node.type === 'llm'}
        <!-- LLM config -->
        <div class="property-field">
          <label class="field-label" for="cfg-model">Model</label>
          <select id="cfg-model" class="field-input"
            value={node.config?.model as string || ''}
            onchange={(e) => updateConfig('model', e.currentTarget.value || '')}>
            <option value="">继承聊天当前模型</option>
            {#each modelOptions as m}
              <option value={m.id}>{m.name}</option>
            {/each}
          </select>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-system-prompt">System Prompt</label>
          <div class="field-with-picker">
            <textarea id="cfg-system-prompt" class="field-textarea" rows="3"
              value={node.config?.system_prompt as string || ''}
              onchange={(e) => updateConfig('system_prompt', e.currentTarget.value)}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('system_prompt')}>
              {activePickerField === 'system_prompt' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'system_prompt'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('system_prompt', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-prompt">Prompt</label>
          <div class="field-with-picker">
            <textarea id="cfg-prompt" class="field-textarea" rows="4"
              value={node.config?.prompt as string || ''}
              onchange={(e) => updateConfig('prompt', e.currentTarget.value)}
              placeholder={'Use {{var}} or {{node_id.field}} to reference variables'}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('prompt')}>
              {activePickerField === 'prompt' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'prompt'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('prompt', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
        </div>
        <div class="property-field-row">
          <div class="property-field">
            <label class="field-label" for="cfg-temp">Temperature</label>
            <input id="cfg-temp" type="number" step="0.1" min="0" max="2" class="field-input"
              value={node.config?.temperature as number ?? 0.7}
              onchange={(e) => updateConfig('temperature', parseFloat(e.currentTarget.value))} />
          </div>
          <div class="property-field">
            <label class="field-label" for="cfg-max-tokens">Max Tokens</label>
            <input id="cfg-max-tokens" type="number" min="1" class="field-input"
              value={node.config?.max_tokens as number ?? 2048}
              onchange={(e) => updateConfig('max_tokens', parseInt(e.currentTarget.value, 10))} />
          </div>
        </div>

      {:else if node.type === 'condition'}
        <!-- Condition config -->
        <div class="property-field">
          <label class="field-label" for="cfg-condition">Condition Expression</label>
          <div class="field-with-picker">
            <textarea id="cfg-condition" class="field-textarea" rows="3"
              value={node.config?.condition as string || ''}
              onchange={(e) => updateConfig('condition', e.currentTarget.value)}
              placeholder={"e.g. {{count}} > 5 and {{status}} == 'active'"}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('condition')}>
              {activePickerField === 'condition' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'condition'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('condition', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
          <span class="field-hint">Output edges with label "true" / "false" are followed based on this expression.</span>
        </div>

      {:else if node.type === 'variable_set'}
        <!-- Variable set config -->
        <div class="property-field">
          <label class="field-label" for="cfg-var-name">Variable Name</label>
          <input id="cfg-var-name" type="text" class="field-input"
            value={node.config?.variable_name as string || ''}
            onchange={(e) => updateConfig('variable_name', e.currentTarget.value)} />
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-var-value">Variable Value</label>
          <input id="cfg-var-value" type="text" class="field-input"
            value={node.config?.variable_value as string || ''}
            onchange={(e) => updateConfig('variable_value', e.currentTarget.value)}
            placeholder={'Use {{var}} for substitution'} />
        </div>

      {:else if node.type === 'loop'}
        <!-- Loop config -->
        <div class="property-field">
          <label class="field-label" for="cfg-loop-type">Loop Type</label>
          <select id="cfg-loop-type" class="field-input"
            value={node.config?.loop_type as string || 'for_each'}
            onchange={(e) => updateConfig('loop_type', e.currentTarget.value)}>
            <option value="for_each">For Each</option>
            <option value="while">While</option>
            <option value="times">Times</option>
          </select>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-iterator">Iterator Variable</label>
          <input id="cfg-iterator" type="text" class="field-input"
            value={node.config?.iterator as string || ''}
            onchange={(e) => updateConfig('iterator', e.currentTarget.value)}
            placeholder="Variable holding the iterable (for_each)" />
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-loop-condition">Condition (while)</label>
          <input id="cfg-loop-condition" type="text" class="field-input"
            value={node.config?.condition as string || ''}
            onchange={(e) => updateConfig('condition', e.currentTarget.value)}
            placeholder={'e.g. {{counter}} < 10'} />
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-max-iter">Max Iterations</label>
          <input id="cfg-max-iter" type="number" min="1" class="field-input"
            value={node.config?.max_iterations as number ?? 1000}
            onchange={(e) => updateConfig('max_iterations', parseInt(e.currentTarget.value, 10))} />
        </div>

      {:else if node.type === 'http_request'}
        <!-- HTTP request config -->
        <div class="property-field-row">
          <div class="property-field" style="flex: 0 0 100px">
            <label class="field-label" for="cfg-method">Method</label>
            <select id="cfg-method" class="field-input"
              value={node.config?.method as string || 'GET'}
              onchange={(e) => updateConfig('method', e.currentTarget.value)}>
              <option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option>
            </select>
          </div>
          <div class="property-field" style="flex: 1">
            <label class="field-label" for="cfg-url">URL</label>
            <input id="cfg-url" type="text" class="field-input"
              value={node.config?.url as string || ''}
              onchange={(e) => updateConfig('url', e.currentTarget.value)}
              placeholder="https://api.example.com/v1/resource" />
          </div>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-headers">Headers (JSON)</label>
          <textarea id="cfg-headers" class="field-textarea" rows="3"
            value={jsonString(node.config?.headers)}
            onchange={(e) => updateConfig('headers', parseJsonSafe(e.currentTarget.value, node.config?.headers || {}))}></textarea>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-body">Body (JSON or text)</label>
          <div class="field-with-picker">
            <textarea id="cfg-body" class="field-textarea" rows="4"
              value={node.config?.body as string || ''}
              onchange={(e) => updateConfig('body', e.currentTarget.value)}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('body')}>
              {activePickerField === 'body' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'body'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('body', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
        </div>

      {:else if node.type === 'code'}
        <!-- Code node config -->
        <div class="property-field">
          <label class="field-label" for="cfg-code">Python Code</label>
          <div class="field-with-picker">
            <textarea id="cfg-code" class="field-textarea code-area" rows="8"
              value={node.config?.code as string || ''}
              onchange={(e) => updateConfig('code', e.currentTarget.value)}
              placeholder={"def main(inputs):\\n    return {'result': inputs['x'] * 2}"}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('code')}>
              {activePickerField === 'code' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'code'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('code', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-input-vars">Input Variables (JSON)</label>
          <textarea id="cfg-input-vars" class="field-textarea" rows="3"
            value={jsonString(node.config?.input_variables)}
            onchange={(e) => updateConfig('input_variables', parseJsonSafe(e.currentTarget.value, node.config?.input_variables || {}))}></textarea>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-output-var">Output Variable Name</label>
          <input id="cfg-output-var" type="text" class="field-input"
            value={node.config?.output_variable as string || 'result'}
            onchange={(e) => updateConfig('output_variable', e.currentTarget.value)} />
        </div>

      {:else if node.type === 'pm_module'}
        <!-- PM Module config: full module_type + action + project/entry selectors -->
        <div class="property-field">
          <label class="field-label" for="cfg-module-type">Module Type</label>
          <select id="cfg-module-type" class="field-input"
            value={node.config?.module_type as string || 'prd'}
            onchange={(e) => updateConfig('module_type', e.currentTarget.value)}>
            {#each PM_MODULE_TYPES as mt}
              <option value={mt}>{mt}</option>
            {/each}
          </select>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-action">Action</label>
          <select id="cfg-action" class="field-input"
            value={node.config?.action as string || 'read'}
            onchange={(e) => updateConfig('action', e.currentTarget.value)}>
            <option value="read">read</option>
            <option value="create">create</option>
            <option value="update">update</option>
            <option value="delete">delete</option>
          </select>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-project-id">Project ID</label>
          <input id="cfg-project-id" type="text" class="field-input"
            value={node.config?.project_id as string || ''}
            onchange={(e) => updateConfig('project_id', e.currentTarget.value)}
            placeholder={'PM workspace project UUID (or use {{project_id}})'} />
        </div>
        {#if (node.config?.action || 'read') === 'read'}
          <div class="property-field">
            <label class="field-label" for="cfg-filter">Filter (JSON)</label>
            <textarea id="cfg-filter" class="field-textarea" rows="3"
              value={jsonString(node.config?.filter)}
              onchange={(e) => updateConfig('filter', parseJsonSafe(e.currentTarget.value, node.config?.filter || {}))}></textarea>
          </div>
        {/if}
        {#if ['create', 'update'].includes(node.config?.action as string)}
          <div class="property-field">
            <label class="field-label" for="cfg-entry-id">Entry ID (for update)</label>
            <input id="cfg-entry-id" type="text" class="field-input"
              value={node.config?.entry_id as string || ''}
              onchange={(e) => updateConfig('entry_id', e.currentTarget.value)}
              placeholder="Required for update; leave empty for create" />
          </div>
          <div class="property-field">
            <label class="field-label" for="cfg-data">Data (JSON)</label>
            <textarea id="cfg-data" class="field-textarea" rows="6"
              value={jsonString(node.config?.data)}
              onchange={(e) => updateConfig('data', parseJsonSafe(e.currentTarget.value, node.config?.data || {}))}></textarea>
          </div>
        {/if}
        {#if ['update', 'delete'].includes(node.config?.action as string)}
          <div class="property-field">
            <label class="field-label" for="cfg-entry-id-2">Entry ID</label>
            <input id="cfg-entry-id-2" type="text" class="field-input"
              value={node.config?.entry_id as string || ''}
              onchange={(e) => updateConfig('entry_id', e.currentTarget.value)}
              placeholder="PM entry UUID" />
          </div>
        {/if}

      {:else if node.type === 'human_input'}
        <!-- Human Input config: prompt + fields + output_variable -->
        <div class="property-field">
          <label class="field-label" for="cfg-prompt">Prompt（向用户展示的提示文案）</label>
          <div class="field-with-picker">
            <textarea id="cfg-prompt" class="field-textarea" rows="3"
              value={node.config?.prompt as string || ''}
              onchange={(e) => updateConfig('prompt', e.currentTarget.value)}
              placeholder={'例如：请确认以下模块列表是否正确，或选择需要保留的模块'}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('prompt')}>
              {activePickerField === 'prompt' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'prompt'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('prompt', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
          <span class="field-hint">工作流执行到此节点会暂停，前端弹出表单展示此提示文案。</span>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-fields">Fields（表单字段定义 JSON 数组）</label>
          <textarea id="cfg-fields" class="field-textarea" rows="8"
            value={jsonString(node.config?.fields)}
            onchange={(e) => updateConfig('fields', parseJsonSafe(e.currentTarget.value, node.config?.fields || []))}></textarea>
          <span class="field-hint">
            每项格式：<code>{'{"name":"module_list","label":"模块列表","type":"textarea","required":true}'}</code><br/>
            type 可选：text / textarea / select / confirm；type=select 时需提供 options 数组。
          </span>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-output-var-human">Output Variable Name</label>
          <input id="cfg-output-var-human" type="text" class="field-input"
            value={node.config?.output_variable as string || 'human_input_result'}
            onchange={(e) => updateConfig('output_variable', e.currentTarget.value)} />
          <span class="field-hint">用户提交的表单响应会写入此变量，可在下游节点用 <code>{'{{var_name}}'}</code> 引用。</span>
        </div>

      {:else if node.type === 'knowledge_retrieval'}
        <div class="property-field">
          <label class="field-label" for="cfg-query">Query</label>
          <textarea id="cfg-query" class="field-textarea" rows="2"
            value={node.config?.query as string || ''}
            onchange={(e) => updateConfig('query', e.currentTarget.value)}
            placeholder={'Use {{var}} for substitution'}></textarea>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-kb-id">Knowledge Base ID</label>
          <input id="cfg-kb-id" type="text" class="field-input"
            value={node.config?.knowledge_base_id as string || ''}
            onchange={(e) => updateConfig('knowledge_base_id', e.currentTarget.value)} />
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-top-k">Top K</label>
          <input id="cfg-top-k" type="number" min="1" class="field-input"
            value={node.config?.top_k as number ?? 5}
            onchange={(e) => updateConfig('top_k', parseInt(e.currentTarget.value, 10))} />
        </div>

      {:else if node.type === 'template'}
        <div class="property-field">
          <label class="field-label" for="cfg-template">Template</label>
          <div class="field-with-picker">
            <textarea id="cfg-template" class="field-textarea" rows="6"
              value={node.config?.template as string || ''}
              onchange={(e) => updateConfig('template', e.currentTarget.value)}
              placeholder={'Hello {{name}}, your order {{order_id}} is {{status}}.'}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('template')}>
              {activePickerField === 'template' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'template'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('template', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-out-var">Output Variable</label>
          <input id="cfg-out-var" type="text" class="field-input"
            value={node.config?.output_variable as string || 'result'}
            onchange={(e) => updateConfig('output_variable', e.currentTarget.value)} />
        </div>

      {:else if node.type === 'parameter_extractor'}
        <div class="property-field">
          <label class="field-label" for="cfg-pe-model">Model</label>
          <select id="cfg-pe-model" class="field-input"
            value={node.config?.model as string || ''}
            onchange={(e) => updateConfig('model', e.currentTarget.value || '')}>
            <option value="">继承聊天当前模型</option>
            {#each modelOptions as m}
              <option value={m.id}>{m.name}</option>
            {/each}
          </select>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-pe-input">Input Text</label>
          <div class="field-with-picker">
            <textarea id="cfg-pe-input" class="field-textarea" rows="3"
              value={node.config?.input_text as string || ''}
              onchange={(e) => updateConfig('input_text', e.currentTarget.value)}
              placeholder={'Use {{var}} or {{node_id.field}} to reference text'}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('input_text')}>
              {activePickerField === 'input_text' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'input_text'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('input_text', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-pe-params">Parameters (JSON schema list)</label>
          <textarea id="cfg-pe-params" class="field-textarea" rows="4"
            value={jsonString(node.config?.parameters)}
            onchange={(e) => updateConfig('parameters', parseJsonSafe(e.currentTarget.value, node.config?.parameters || []))}></textarea>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-pe-out">Output Variable</label>
          <input id="cfg-pe-out" type="text" class="field-input"
            value={node.config?.output_variable as string || 'extracted'}
            onchange={(e) => updateConfig('output_variable', e.currentTarget.value)} />
        </div>

      {:else if node.type === 'answer'}
        <div class="property-field">
          <label class="field-label" for="cfg-answer">Answer</label>
          <div class="field-with-picker">
            <textarea id="cfg-answer" class="field-textarea" rows="4"
              value={node.config?.answer as string || ''}
              onchange={(e) => updateConfig('answer', e.currentTarget.value)}
              placeholder={'Use {{var}} or {{node_id.field}} for substitution'}></textarea>
            <button class="insert-var-btn" onclick={() => togglePicker('answer')}>
              {activePickerField === 'answer' ? '取消' : '＋ 插入变量'}
            </button>
            {#if activePickerField === 'answer'}
              <NodeOutputPicker
                currentNode={node}
                {nodes}
                {edges}
                onInsert={(ref) => insertVariable('answer', ref)}
                onClose={() => activePickerField = null}
              />
            {/if}
          </div>
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-answer-out">Output Variable</label>
          <input id="cfg-answer-out" type="text" class="field-input"
            value={node.config?.output_variable as string || 'answer'}
            onchange={(e) => updateConfig('output_variable', e.currentTarget.value)} />
        </div>

      {:else if node.type === 'tool_call' || node.type === 'function_call' || node.type === 'skill_call'}
        <!-- 扩展资源调用节点（tool_call / function_call / skill_call）配置面板 -->
        {#if node.type === 'tool_call'}
          <div class="property-field">
            <label class="field-label" for="cfg-tool-ext">Tool</label>
            {#if extensionsLoading.tools}
              <div class="ext-loading">加载 Tools…</div>
            {:else if extensionsError.tools}
              <div class="ext-error">加载失败：{extensionsError.tools}</div>
              <button class="ext-retry-btn" onclick={() => loadExtensionList('tools')}>重试</button>
            {:else}
              <select id="cfg-tool-ext" class="field-input"
                value={(node.config?.extension_id as string) || ''}
                onchange={(e) => handleExtensionSelect('tools', e.currentTarget.value)}>
                <option value="">— 选择 Tool —</option>
                {#each toolsList as ext (ext.id)}
                  <option value={ext.id}>{ext.name}</option>
                {/each}
              </select>
              {#if toolsList.length === 0}
                <span class="field-hint">未发现已注册的 Tool，请先在 openwebui 中安装。</span>
              {/if}
            {/if}
          </div>
        {:else if node.type === 'function_call'}
          <div class="property-field">
            <label class="field-label" for="cfg-fn-ext">Function</label>
            {#if extensionsLoading.functions}
              <div class="ext-loading">加载 Functions…</div>
            {:else if extensionsError.functions}
              <div class="ext-error">加载失败：{extensionsError.functions}</div>
              <button class="ext-retry-btn" onclick={() => loadExtensionList('functions')}>重试</button>
            {:else}
              <select id="cfg-fn-ext" class="field-input"
                value={(node.config?.extension_id as string) || ''}
                onchange={(e) => handleExtensionSelect('functions', e.currentTarget.value)}>
                <option value="">— 选择 Function —</option>
                {#each functionsList as ext (ext.id)}
                  <option value={ext.id}>{ext.name}</option>
                {/each}
              </select>
              {#if functionsList.length === 0}
                <span class="field-hint">未发现已注册的 Function。</span>
              {/if}
            {/if}
          </div>
        {:else if node.type === 'skill_call'}
          <div class="property-field">
            <label class="field-label" for="cfg-skill-ext">Skill</label>
            {#if extensionsLoading.skills}
              <div class="ext-loading">加载 Skills…</div>
            {:else if extensionsError.skills}
              <div class="ext-error">加载失败：{extensionsError.skills}</div>
              <button class="ext-retry-btn" onclick={() => loadExtensionList('skills')}>重试</button>
            {:else}
              <select id="cfg-skill-ext" class="field-input"
                value={(node.config?.extension_id as string) || ''}
                onchange={(e) => handleExtensionSelect('skills', e.currentTarget.value)}>
                <option value="">— 选择 Skill —</option>
                {#each skillsList as ext (ext.id)}
                  <option value={ext.id}>{ext.name}</option>
                {/each}
              </select>
              {#if skillsList.length === 0}
                <span class="field-hint">未发现已注册的 Skill。</span>
              {/if}
            {/if}
          </div>
        {/if}

        <!-- 入参字段：从扩展 spec 动态渲染 -->
        {#if currentExtensionSpec().length > 0}
          <div class="property-field">
            <label class="field-label">Input Mapping</label>
            <span class="field-hint">为每个入参填值，或点击"插入变量"引用上游节点输出。</span>
          </div>
          {#each currentExtensionSpec() as field (field.name)}
            {@const inputMapping = (node.config?.input_mapping as Record<string, string>) || {}}
            {@const pickerKey = `input_mapping:${field.name}`}
            <div class="property-field">
              <label class="field-label" for="cfg-ext-input-{field.name}">
                {field.name}
                {#if field.required}<span class="required-mark">*</span>{/if}
                <span class="field-type-hint">{field.type}</span>
              </label>
              <div class="field-with-picker">
                <input
                  id="cfg-ext-input-{field.name}"
                  type="text"
                  class="field-input"
                  value={inputMapping[field.name] || ''}
                  onchange={(e) => updateInputMappingField(field.name, e.currentTarget.value)}
                  placeholder={field.description || `e.g. {{upstream_node.field}}`}
                />
                <button class="insert-var-btn" onclick={() => togglePicker(pickerKey)}>
                  {activePickerField === pickerKey ? '取消' : '＋ 变量'}
                </button>
                {#if activePickerField === pickerKey}
                  <NodeOutputPicker
                    currentNode={node}
                    {nodes}
                    {edges}
                    onInsert={(ref) => insertInputMappingVariable(field.name, ref)}
                    onClose={() => activePickerField = null}
                  />
                {/if}
              </div>
              {#if field.description}
                <span class="field-hint">{field.description}</span>
              {/if}
            </div>
          {/each}
        {/if}

        <!-- output_schema 编辑器 -->
        <div class="property-field">
          <label class="field-label" for="cfg-ext-output-schema">Output Schema (JSON)</label>
          <textarea id="cfg-ext-output-schema" class="field-textarea" rows="3"
            value={jsonString(node.config?.output_schema)}
            onchange={(e) => updateConfig('output_schema', parseJsonSafe(e.currentTarget.value, node.config?.output_schema || []))}
            placeholder={'[{"name": "result", "type": "object"}]'}></textarea>
          <span class="field-hint">用于将原始返回值结构化为节点输出。</span>
        </div>

      {:else if node.type === 'mcp_call'}
        <!-- MCP Call 配置面板：Server → Tool 二级联动 -->
        <div class="property-field">
          <label class="field-label" for="cfg-mcp-server">MCP Server</label>
          {#if extensionsLoading.mcp}
            <div class="ext-loading">加载 MCP Servers…</div>
          {:else if extensionsError.mcp}
            <div class="ext-error">加载失败：{extensionsError.mcp}</div>
            <button class="ext-retry-btn" onclick={() => loadExtensionList('mcp')}>重试</button>
          {:else}
            <select id="cfg-mcp-server" class="field-input"
              value={(node.config?.server_id as string) || ''}
              onchange={(e) => handleMcpServerSelect(e.currentTarget.value)}>
              <option value="">— 选择 MCP Server —</option>
              {#each mcpServers as srv (srv.id)}
                <option value={srv.id}>{srv.name}</option>
              {/each}
            </select>
            {#if mcpServers.length === 0}
              <span class="field-hint">未发现已配置的 MCP server，请先在 openwebui 中配置 type=mcp 的 server。</span>
            {/if}
          {/if}
        </div>

        {#if (node.config?.server_id as string)}
          <div class="property-field">
            <label class="field-label" for="cfg-mcp-tool">MCP Tool</label>
            <select id="cfg-mcp-tool" class="field-input"
              value={(node.config?.extension_id as string) || ''}
              onchange={(e) => handleExtensionSelect('mcp', e.currentTarget.value)}>
              <option value="">— 选择 Tool —</option>
              {#each currentMcpTools() as ext (ext.id)}
                <option value={ext.id}>{ext.name}</option>
              {/each}
            </select>
          </div>
        {/if}

        <!-- 入参字段：从 MCP tool spec 动态渲染 -->
        {#if currentExtensionSpec().length > 0}
          <div class="property-field">
            <label class="field-label">Input Mapping</label>
            <span class="field-hint">为每个入参填值，或点击"插入变量"引用上游节点输出。</span>
          </div>
          {#each currentExtensionSpec() as field (field.name)}
            {@const inputMapping = (node.config?.input_mapping as Record<string, string>) || {}}
            {@const pickerKey = `input_mapping:${field.name}`}
            <div class="property-field">
              <label class="field-label" for="cfg-mcp-input-{field.name}">
                {field.name}
                {#if field.required}<span class="required-mark">*</span>{/if}
                <span class="field-type-hint">{field.type}</span>
              </label>
              <div class="field-with-picker">
                <input
                  id="cfg-mcp-input-{field.name}"
                  type="text"
                  class="field-input"
                  value={inputMapping[field.name] || ''}
                  onchange={(e) => updateInputMappingField(field.name, e.currentTarget.value)}
                  placeholder={field.description || `e.g. {{upstream_node.field}}`}
                />
                <button class="insert-var-btn" onclick={() => togglePicker(pickerKey)}>
                  {activePickerField === pickerKey ? '取消' : '＋ 变量'}
                </button>
                {#if activePickerField === pickerKey}
                  <NodeOutputPicker
                    currentNode={node}
                    {nodes}
                    {edges}
                    onInsert={(ref) => insertInputMappingVariable(field.name, ref)}
                    onClose={() => activePickerField = null}
                  />
                {/if}
              </div>
              {#if field.description}
                <span class="field-hint">{field.description}</span>
              {/if}
            </div>
          {/each}
        {/if}

        <!-- output_schema 编辑器 -->
        <div class="property-field">
          <label class="field-label" for="cfg-mcp-output-schema">Output Schema (JSON)</label>
          <textarea id="cfg-mcp-output-schema" class="field-textarea" rows="3"
            value={jsonString(node.config?.output_schema)}
            onchange={(e) => updateConfig('output_schema', parseJsonSafe(e.currentTarget.value, node.config?.output_schema || []))}
            placeholder={'[{"name": "result", "type": "object"}]'}></textarea>
        </div>

      {:else if node.type === 'agent'}
        <div class="property-field">
          <label class="field-label" for="cfg-agent-id">Agent ID</label>
          <input id="cfg-agent-id" type="text" class="field-input"
            value={node.config?.agent_id as string || ''}
            onchange={(e) => updateConfig('agent_id', e.currentTarget.value)} />
        </div>
        <div class="property-field">
          <label class="field-label" for="cfg-agent-instructions">Instructions</label>
          <textarea id="cfg-agent-instructions" class="field-textarea" rows="4"
            value={node.config?.instructions as string || ''}
            onchange={(e) => updateConfig('instructions', e.currentTarget.value)}></textarea>
        </div>

      {:else if node.type === 'start' || node.type === 'end'}
        <p class="empty-hint">No configuration for this node type.</p>

      {:else if node.config && Object.keys(node.config).length > 0}
        <!-- Fallback: reflective editor for unknown types that have config -->
        {#each Object.entries(node.config) as [key, value]}
          <div class="property-field">
            <label class="field-label" for="config-{key}">{key}</label>
            {#if typeof value === 'boolean'}
              <input id="config-{key}" type="checkbox" class="field-checkbox" checked={value}
                onchange={(e) => updateConfig(key, e.currentTarget.checked)} />
            {:else if typeof value === 'number'}
              <input id="config-{key}" type="number" class="field-input" value={value}
                onchange={(e) => updateConfig(key, parseFloat(e.currentTarget.value))} />
            {:else}
              <input id="config-{key}" type="text" class="field-input" value={String(value)}
                onchange={(e) => updateConfig(key, e.currentTarget.value)} />
            {/if}
          </div>
        {/each}
      {:else}
        <p class="empty-hint">No configuration for this node type.</p>
      {/if}
    </div>

    <!-- Ports -->
    {#if node.ports && node.ports.length > 0}
      <div class="property-section">
        <h4 class="section-title">Ports</h4>
        {#each node.ports as port}
          <div class="port-item">
            <span class="port-direction" class:input={port.direction === 'input'} class:output={port.direction === 'output'}>
              {port.direction}
            </span>
            <span class="port-name">{port.name}</span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- 上下游面板 (Part B) -->
    <div class="property-section">
      <h4 class="section-title">上下游</h4>

      <!-- 输入侧：反向 BFS 列出上游节点 + 字段 -->
      <div class="io-panel-group">
        <div class="io-panel-label">输入侧（上游节点）</div>
        {#if upstreamNodes().length === 0}
          <p class="empty-hint">当前节点没有上游节点</p>
        {:else}
          <div class="upstream-list">
            {#each upstreamNodes() as upNode (upNode.id)}
              {@const upOutputs = getNodeOutputs(upNode)}
              <div class="upstream-item">
                <button class="upstream-jump-btn" title="跳转到上游节点"
                  onclick={() => handleFocusUpstream(upNode.id)}>
                  <span class="upstream-name">{upNode.name}</span>
                  <span class="upstream-type-badge">{upNode.type}</span>
                </button>
                <div class="upstream-fields">
                  {#if upOutputs.length === 0}
                    <span class="empty-hint">无输出字段</span>
                  {:else}
                    {#each upOutputs as field (field.name)}
                      <div class="upstream-field" title={field.description || ''}>
                        <code class="field-ref">{`${upNode.id}.${field.name}`}</code>
                        <span class="field-type-hint">{field.type}</span>
                      </div>
                    {/each}
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- 输出侧：根据节点类型推断输出目标 -->
      <div class="io-panel-group">
        <div class="io-panel-label">输出侧</div>
        {#if outputTargets().length === 0}
          <p class="empty-hint">无输出目标</p>
        {:else}
          <div class="output-list">
            {#each outputTargets() as target (target.label)}
              <button
                class="output-target-btn"
                title={target.value}
                onclick={() => handleFocusOutput(target)}>
                <span class="output-kind-badge kind-{target.kind}">{target.kind}</span>
                <span class="output-label">{target.label}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {:else}
    <div class="empty-state">
      <div class="empty-icon">📋</div>
      <p class="empty-title">No node selected</p>
      <p class="empty-description">Click on a node in the canvas to view and edit its properties.</p>
    </div>
  {/if}
</div>

<style>
  .property-panel {
    width: 300px;
    height: 100%;
    background: #ffffff;
    border-left: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }

  .panel-header {
    padding: 16px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .node-type-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    color: white;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .panel-title {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
    margin: 0;
  }

  .property-section {
    padding: 16px;
    border-bottom: 1px solid #e5e7eb;
  }

  .section-title {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 12px 0;
  }

  .property-field {
    margin-bottom: 12px;
  }

  .property-field-row {
    display: flex;
    gap: 8px;
  }

  .field-label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: #374151;
    margin-bottom: 4px;
  }

  .field-hint {
    display: block;
    margin-top: 4px;
    font-size: 11px;
    color: #6b7280;
    line-height: 1.4;
  }

  .field-input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    background: #ffffff;
    transition: border-color 0.2s ease;
    box-sizing: border-box;
  }

  .field-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .field-input:disabled {
    background: #f3f4f6;
    color: #6b7280;
    cursor: not-allowed;
  }

  .field-input--mono {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 11px;
  }

  .field-textarea {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 13px;
    background: #ffffff;
    resize: vertical;
    min-height: 60px;
    box-sizing: border-box;
    font-family: inherit;
  }

  .field-textarea.code-area {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 12px;
    min-height: 140px;
  }

  .field-textarea:focus {
    outline: none;
    border-color: #3b82f6;
  }

  /* Variable picker wrapper — positioned relative so the picker dropdown
     can be absolutely positioned within the field. */
  .field-with-picker {
    position: relative;
  }

  .insert-var-btn {
    margin-top: 4px;
    padding: 4px 10px;
    font-size: 11px;
    color: #3b82f6;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }

  .insert-var-btn:hover {
    background: #dbeafe;
    border-color: #93c5fd;
  }

  .field-checkbox {
    width: 16px;
    height: 16px;
    margin-top: 4px;
    accent-color: #3b82f6;
  }

  .position-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .port-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    border-bottom: 1px solid #f3f4f6;
  }

  .port-item:last-child {
    border-bottom: none;
  }

  .port-direction {
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
  }

  .port-direction.input {
    background: #dbeafe;
    color: #1e40af;
  }

  .port-direction.output {
    background: #dcfce7;
    color: #166534;
  }

  .port-name {
    font-size: 13px;
    color: #374151;
  }

  .empty-hint {
    font-size: 12px;
    color: #9ca3af;
    margin: 0;
    font-style: italic;
  }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
  }

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  .empty-title {
    font-size: 16px;
    font-weight: 600;
    color: #374151;
    margin: 0 0 8px 0;
  }

  .empty-description {
    font-size: 13px;
    color: #6b7280;
    margin: 0;
    line-height: 1.5;
  }

  /* ===== 扩展面板新增样式 ===== */
  .ext-loading {
    font-size: 12px;
    color: #6b7280;
    padding: 8px 10px;
    background: #f9fafb;
    border: 1px dashed #d1d5db;
    border-radius: 6px;
  }

  .ext-error {
    font-size: 12px;
    color: #991b1b;
    padding: 8px 10px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    margin-bottom: 6px;
  }

  .ext-retry-btn {
    padding: 4px 10px;
    font-size: 11px;
    color: #3b82f6;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    cursor: pointer;
  }

  .ext-retry-btn:hover {
    background: #dbeafe;
  }

  .required-mark {
    color: #ef4444;
    margin-left: 2px;
    font-weight: 700;
  }

  .field-type-hint {
    font-size: 10px;
    color: #9ca3af;
    margin-left: 6px;
    font-family: 'Monaco', 'Menlo', monospace;
    font-weight: 400;
    text-transform: lowercase;
  }

  /* ===== 上下游面板新增样式 ===== */
  .io-panel-group {
    margin-bottom: 12px;
  }

  .io-panel-group:last-child {
    margin-bottom: 0;
  }

  .io-panel-label {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 6px;
  }

  .upstream-list,
  .output-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .upstream-item {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    overflow: hidden;
  }

  .upstream-jump-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 6px 8px;
    background: #f9fafb;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s;
  }

  .upstream-jump-btn:hover {
    background: #eff6ff;
  }

  .upstream-name {
    font-size: 12px;
    font-weight: 600;
    color: #1f2937;
  }

  .upstream-type-badge {
    font-size: 9px;
    padding: 1px 5px;
    background: #e5e7eb;
    color: #6b7280;
    border-radius: 3px;
    text-transform: uppercase;
  }

  .upstream-fields {
    padding: 4px 8px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .upstream-field {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 2px 0;
    font-size: 11px;
  }

  .field-ref {
    font-family: 'Monaco', 'Menlo', monospace;
    color: #1e40af;
    background: #dbeafe;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 10px;
  }

  .output-target-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 6px 8px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s, border-color 0.15s;
  }

  .output-target-btn:hover {
    background: #f0fdf4;
    border-color: #86efac;
  }

  .output-kind-badge {
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 3px;
    text-transform: uppercase;
    font-weight: 600;
  }

  .output-kind-badge.kind-pm_module {
    background: #dbeafe;
    color: #1e40af;
  }

  .output-kind-badge.kind-answer {
    background: #dcfce7;
    color: #166534;
  }

  .output-kind-badge.kind-openwebui_resource {
    background: #fef3c7;
    color: #92400e;
  }

  .output-kind-badge.kind-variable {
    background: #f3e8ff;
    color: #6b21a8;
  }

  .output-label {
    font-size: 11px;
    color: #374151;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .property-panel {
      background: #1f2937;
      border-left-color: #374151;
    }

    .panel-title {
      color: #f9fafb;
    }

    .section-title {
      color: #9ca3af;
    }

    .field-label {
      color: #d1d5db;
    }

    .field-input {
      background: #374151;
      border-color: #4b5563;
      color: #f9fafb;
    }

    .field-input:disabled {
      background: #1f2937;
      color: #9ca3af;
    }

    .field-textarea {
      background: #374151;
      border-color: #4b5563;
      color: #f9fafb;
    }

    .insert-var-btn {
      color: #93c5fd;
      background: #1e3a5f;
      border-color: #1d4ed8;
    }

    .insert-var-btn:hover {
      background: #1e40af;
      border-color: #3b82f6;
    }

    .port-name {
      color: #d1d5db;
    }

    .empty-title {
      color: #f9fafb;
    }

    .empty-description {
      color: #9ca3af;
    }
  }
</style>
