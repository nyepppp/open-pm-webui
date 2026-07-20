<script lang="ts">
  import type { Workflow, WorkflowNode, WorkflowEdge, Point, NodeType, NodeTemplate } from './types';
  import { NODE_TYPE_LABELS } from './types';
  import Canvas from './Canvas.svelte';
  import NodeSidebar from './NodeSidebar.svelte';
  import PropertyPanel from './PropertyPanel.svelte';
  import { goto } from '$app/navigation';
  import { getExecutionStatus, getExecutionNodeDetail, resumeWorkflowRun, type WorkflowValidationDetail, type ExecutionNodeDetail } from '$lib/apis/workflow/index';
  import { socket } from '$lib/stores';
  import { onDestroy } from 'svelte';
  import { toast } from 'svelte-sonner';

  // ===== Props =====
  interface Props {
    workflow?: Workflow;
    onSave?: (workflow: Workflow) => void | Promise<void>;
    onExecute?: (workflowId: string, inputData?: Record<string, unknown>) => void | Promise<any>;
    validationErrors?: WorkflowValidationDetail[] | null;
    onClearValidationErrors?: () => void;
  }

  let {
    workflow: initialWorkflow,
    onSave,
    onExecute,
    validationErrors = null,
    onClearValidationErrors
  }: Props = $props();

  // ===== State =====
  let workflow = $state<Workflow>(initialWorkflow || {
    id: crypto.randomUUID(),
    name: 'New Workflow',
    description: '',
    nodes: [],
    edges: [],
    status: 'draft'
  });

  // L1/D79: 监听 initialWorkflow prop 变化，同步到内部 $state
  // 修复 Bug 3 真正根因 —— Svelte 5 $state 只在首次挂载从 prop 初始化，
  // 后续 prop 变化不自动同步。{#key designerKey} remount 在批量更新机制下
  // 可能拿 stale 值，导致 onSave 传出 stale 的 1 节点 workflow。
  // $effect 主动同步可消除时序竞态。
  $effect(() => {
    if (initialWorkflow) {
      // 深比较 nodes/edges，避免无意义更新触发循环
      const currentNodes = JSON.stringify(workflow.nodes || []);
      const propNodes = JSON.stringify(initialWorkflow.nodes || []);
      const currentEdges = JSON.stringify(workflow.edges || []);
      const propEdges = JSON.stringify(initialWorkflow.edges || []);
      if (currentNodes !== propNodes || currentEdges !== propEdges) {
        console.log('[Bug3-Diag] L1 $effect sync: nodes', (workflow.nodes || []).length, '→', (initialWorkflow.nodes || []).length, 'edges', (workflow.edges || []).length, '→', (initialWorkflow.edges || []).length);
        workflow = { ...initialWorkflow };
      }
    }
  });

  let selectedNodeId = $state<string | null>(null);
  let selectedEdgeId = $state<string | null>(null);
  let sidebarCollapsed = $state(false);
  let isSaving = $state(false);
  let showExecutionPanel = $state(false);
  let executionStatus = $state<'idle' | 'running' | 'success' | 'error' | 'awaiting_input'>('idle');

  // Execution progress state
  let executionProgress = $state<{ completed_nodes: number; total_nodes: number; current_node_id: string } | null>(null);
  let nodeResults = $state<Record<string, any>>({});
  let executionOutput = $state<any>(null);
  let executionError = $state<string | null>(null);

  // 当前执行 ID（用于查询节点运行时详情）
  let currentExecutionId = $state<string | null>(null);
  // 当前选中查看详情的节点
  let selectedNodeDetail = $state<ExecutionNodeDetail | null>(null);
  let nodeDetailLoading = $state(false);
  let nodeDetailError = $state<string | null>(null);

  // human_input 节点挂起时的表单状态（轮询到 status === 'awaiting_input' 时填充）
  let awaitingInput = $state<{
    nodeId: string;
    prompt: string;
    fields: Array<{ name: string; label: string; type: string; options?: string[]; required?: boolean }>;
    outputVariable: string;
  } | null>(null);
  let humanInputResponse = $state<Record<string, any>>({});
  let isResuming = $state(false);

  // 执行过程实时日志（按时间倒序，最多保留 200 条）
  type LogEntry = {
    ts: number;
    event: string;       // node.started / node.completed / node.error / execution.progress / execution.completed
    message: string;
    nodeId?: string;
    level: 'info' | 'success' | 'error' | 'warn';
  };
  let executionLogs = $state<LogEntry[]>([]);

  // FAIL-1: Canvas 组件实例引用，用于调用 centerOnNode 实现画布居中
  let canvasRef = $state<{ centerOnNode: (nodeId: string) => void } | null>(null);

  // ===== Derived =====
  const selectedNode = $derived(() => {
    return workflow.nodes.find(n => n.id === selectedNodeId) || null;
  });

  const nodeCount = $derived(() => workflow.nodes.length);
  const edgeCount = $derived(() => workflow.edges.length);

  // ===== Node Management =====
  function generateNodeId(): string {
    return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  function addNode(template: NodeTemplate, position: Point) {
    // Deep-copy the template config so each node instance has its own editable
    // config (critical for PM modules — every PM node shares type 'pm_module'
    // but distinguishes itself via config.module_type).
    const configCopy = template.config
      ? JSON.parse(JSON.stringify(template.config))
      : {};

    // Copy ports from the template if present, otherwise default to a single
    // input + output port. The condition node, for instance, ships with
    // true / false output ports that must be preserved for routing.
    const portsCopy = template.ports
      ? template.ports.map(p => ({ ...p }))
      : [
          { id: 'in', name: 'input', direction: 'input' as const },
          { id: 'out', name: 'output', direction: 'output' as const }
        ];

    const newNode: WorkflowNode = {
      id: generateNodeId(),
      type: template.type,
      name: template.label || NODE_TYPE_LABELS[template.type] || template.type,
      x: position.x,
      y: position.y,
      width: 160,
      height: 60,
      config: configCopy,
      ports: portsCopy
    };

    workflow = {
      ...workflow,
      nodes: [...workflow.nodes, newNode]
    };

    selectedNodeId = newNode.id;
  }

  function updateNode(nodeId: string, updates: Partial<WorkflowNode>) {
    workflow = {
      ...workflow,
      nodes: workflow.nodes.map(n =>
        n.id === nodeId ? { ...n, ...updates } : n
      )
    };
  }

  function deleteNode(nodeId: string) {
    workflow = {
      ...workflow,
      nodes: workflow.nodes.filter(n => n.id !== nodeId),
      edges: workflow.edges.filter(e =>
        e.sourceNodeId !== nodeId && e.targetNodeId !== nodeId
      )
    };

    if (selectedNodeId === nodeId) {
      selectedNodeId = null;
    }
  }

  // ===== Edge Management =====
  function addEdge(sourceNodeId: string, targetNodeId: string, sourcePortId?: string, targetPortId?: string) {
    // Prevent duplicate edges
    const exists = workflow.edges.some(e =>
      e.sourceNodeId === sourceNodeId &&
      e.targetNodeId === targetNodeId &&
      e.sourcePortId === sourcePortId &&
      e.targetPortId === targetPortId
    );
    if (exists) return;

    const newEdge: WorkflowEdge = {
      id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      sourceNodeId,
      targetNodeId,
      sourcePortId,
      targetPortId
    };

    workflow = {
      ...workflow,
      edges: [...workflow.edges, newEdge]
    };
  }

  function deleteEdge(edgeId: string) {
    workflow = {
      ...workflow,
      edges: workflow.edges.filter(e => e.id !== edgeId)
    };
    if (selectedEdgeId === edgeId) {
      selectedEdgeId = null;
    }
  }

  // ===== Event Handlers =====
  function handleNodeSelect(nodeId: string | null) {
    selectedNodeId = nodeId;
  }

  function handleEdgeSelect(edgeId: string | null) {
    selectedEdgeId = edgeId;
  }

  function handleNodeMove(nodeId: string, position: Point) {
    updateNode(nodeId, { x: position.x, y: position.y });
  }

  function handleNodeDrop(template: NodeTemplate, position: Point) {
    addNode(template, position);
  }

  function handleNodeUpdate(nodeId: string, updates: Partial<WorkflowNode>) {
    updateNode(nodeId, updates);
  }

  function handleEdgeCreate(sourceNodeId: string, targetNodeId: string, sourcePortId?: string, targetPortId?: string) {
    addEdge(sourceNodeId, targetNodeId, sourcePortId, targetPortId);
  }

  function handleEdgeDelete(edgeId: string) {
    deleteEdge(edgeId);
  }

  async function handleSave() {
    isSaving = true;
    try {
      await onSave?.(workflow);
    } finally {
      isSaving = false;
    }
  }

  async function handleExecute() {
    showExecutionPanel = true;
    executionStatus = 'running';
    executionProgress = null;
    nodeResults = {};
    executionOutput = null;
    executionError = null;
    selectedNodeDetail = null;
    nodeDetailError = null;
    currentExecutionId = null;
    executionLogs = [];   // 清空上次的日志

    // D6: 执行前自动保存 — 保存失败则中止执行，把错误暴露给用户
    if (onSave) {
      executionLogs = [{
        ts: Date.now(),
        event: 'save.started',
        level: 'info',
        message: '⏺ 正在保存工作流…'
      }, ...executionLogs];
      try {
        await handleSave();
        executionLogs = [{
          ts: Date.now(),
          event: 'save.completed',
          level: 'success',
          message: '✓ 保存完成，开始执行…'
        }, ...executionLogs];
      } catch (saveErr: any) {
        executionStatus = 'error';
        executionError = `保存失败：${saveErr?.message || saveErr}`;
        executionLogs = [{
          ts: Date.now(),
          event: 'save.error',
          level: 'error',
          message: `✗ 保存失败：${saveErr?.message || saveErr}（已中止执行）`
        }, ...executionLogs];
        toast.error('保存失败，已中止执行');
        return;
      }
    }

    try {
      const result = await onExecute?.(workflow.id);
      if (result?.execution_id) {
        currentExecutionId = result.execution_id;
        await pollExecutionStatus(result.execution_id);
      } else {
        // No execution_id returned; mark as success if no error
        executionStatus = 'success';
      }
    } catch (error) {
      executionStatus = 'error';
      executionError = error instanceof Error ? error.message : String(error);
      // D6: 错误兜底 — 把异常写入 executionLogs 让用户在执行面板看到错误
      executionLogs = [{
        ts: Date.now(),
        event: 'execution.error',
        level: 'error',
        message: `✗ 执行失败：${executionError}`
      }, ...executionLogs];
      console.error('Execution failed:', error);
    }
  }

  /** Socket.IO 推送的 workflow:event 事件处理 */
  function handleWorkflowEvent(payload: any) {
    if (!payload || !currentExecutionId || payload.execution_id !== currentExecutionId) return;
    const event = payload.event;
    const ts = payload.timestamp ? new Date(payload.timestamp).getTime() : Date.now();
    let entry: LogEntry | null = null;
    switch (event) {
      case 'node.started':
        entry = {
          ts, event, level: 'info',
          nodeId: payload.node_id,
          message: `▶ 节点开始：${payload.node_name || payload.node_id}（${payload.node_type}）`
        };
        break;
      case 'node.completed':
        entry = {
          ts, event, level: 'success',
          nodeId: payload.node_id,
          message: `✓ 节点完成：${payload.node_id}（耗时 ${Math.round(payload.execution_time_ms || 0)}ms）`
        };
        break;
      case 'node.error':
        entry = {
          ts, event, level: 'error',
          nodeId: payload.node_id,
          message: `✗ 节点失败：${payload.node_id} — ${payload.error}`
        };
        break;
      case 'execution.progress':
        entry = {
          ts, event, level: 'info',
          message: `进度：${payload.completed_nodes}/${payload.total_nodes}（${(payload.progress || 0).toFixed(1)}%）`
        };
        executionProgress = {
          completed_nodes: payload.completed_nodes,
          total_nodes: payload.total_nodes,
          current_node_id: ''
        };
        break;
      case 'execution.completed':
        entry = {
          ts, event, level: payload.status === 'completed' ? 'success' : 'error',
          message: payload.status === 'completed'
            ? `✓ 执行完成`
            : `✗ 执行失败：${payload.error_message || ''}`
        };
        break;
      default:
        return;
    }
    if (entry) {
      executionLogs = [entry, ...executionLogs].slice(0, 200);  // 最多保留 200 条
    }
  }

  // 订阅 Socket.IO workflow:event 事件（仅在 socket 可用时绑定）
  let socketBound = $state(false);
  $effect(() => {
    if ($socket && !socketBound) {
      $socket.on('workflow:event', handleWorkflowEvent);
      socketBound = true;
    }
  });
  onDestroy(() => {
    if ($socket) {
      $socket.off('workflow:event', handleWorkflowEvent);
    }
  });

  async function pollExecutionStatus(executionId: string) {
    const pollInterval = 1000;
    const maxDuration = 300000;
    const startTime = Date.now();
    const token = localStorage.token || '';

    while (executionStatus === 'running' && Date.now() - startTime < maxDuration) {
      try {
        const status = await getExecutionStatus(token, workflow.id, executionId);
        nodeResults = status.node_results || {};
        if (status.node_results) {
          executionProgress = {
            completed_nodes: Object.keys(status.node_results).length,
            total_nodes: workflow.nodes?.length || 0,
            current_node_id: ''
          };
        }

        // 保留服务端 logs 作为兜底（断网/Socket.IO 未触发时仍可见）
        if (Array.isArray((status as any).logs)) {
          const merged = [...executionLogs];
          for (const log of (status as any).logs) {
            const ts = log.timestamp ? log.timestamp * 1000 : Date.now();
            const exists = merged.some(m => m.ts === ts && m.event === log.event_type);
            if (!exists) {
              merged.unshift({
                ts,
                event: log.event_type,
                message: JSON.stringify(log.data || {}),
                level: 'info'
              });
            }
          }
          executionLogs = merged.slice(0, 200);
        }

        if (status.status === 'completed') {
          executionStatus = 'success';
          executionOutput = status.output_data;
          break;
        } else if (status.status === 'failed') {
          executionStatus = 'error';
          executionError = status.error_message || 'Execution failed';
          break;
        } else if (status.status === 'awaiting_input' && status.awaiting_input) {
          // human_input 节点挂起：填充表单状态，退出轮询，等用户提交后恢复
          const ai = status.awaiting_input;
          awaitingInput = {
            nodeId: ai.node_id,
            prompt: ai.prompt,
            fields: ai.fields || [],
            outputVariable: ai.output_variable || 'human_input_result'
          };
          humanInputResponse = {};
          executionStatus = 'awaiting_input';
          break;
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
      await new Promise(r => setTimeout(r, pollInterval));
    }

    if (executionStatus === 'running') {
      executionStatus = 'error';
      executionError = 'Execution timed out (5 minutes)';
    }
  }

  /** 用户提交 human_input 表单后唤醒后端，继续轮询 */
  async function submitHumanInput() {
    if (!awaitingInput || !currentExecutionId) return;
    // 必填校验
    const missing = awaitingInput.fields
      .filter(f => f.required)
      .filter(f => {
        const v = humanInputResponse[f.name];
        return v === undefined || v === null || v === '' || v === false;
      });
    if (missing.length > 0) {
      toast.error(`请填写必填字段：${missing.map(f => f.label).join(', ')}`);
      return;
    }
    isResuming = true;
    try {
      const token = localStorage.token || '';
      await resumeWorkflowRun(token, currentExecutionId, awaitingInput.nodeId, humanInputResponse);
      awaitingInput = null;
      humanInputResponse = {};
      executionStatus = 'running';
      await pollExecutionStatus(currentExecutionId);
    } catch (e: any) {
      toast.error(e.message || '提交失败');
    } finally {
      isResuming = false;
    }
  }

  /** 用户取消 human_input 表单 -> 终止执行 */
  function cancelHumanInput() {
    awaitingInput = null;
    humanInputResponse = {};
    executionStatus = 'error';
    executionError = '用户取消了人工确认';
  }

  // 点击执行历史中的节点，加载并展示该节点的运行时详情（Part B - Task 8）
  async function handleNodeResultClick(nodeId: string) {
    if (!currentExecutionId) {
      // 没有当前执行上下文，直接选中该节点
      selectedNodeId = nodeId;
      return;
    }
    nodeDetailLoading = true;
    nodeDetailError = null;
    selectedNodeDetail = null;
    try {
      const token = localStorage.token || '';
      const detail = await getExecutionNodeDetail(token, workflow.id, currentExecutionId, nodeId);
      selectedNodeDetail = detail;
      // 同时在画布上选中该节点
      selectedNodeId = nodeId;
    } catch (e: any) {
      nodeDetailError = e?.message || '加载节点详情失败';
      // 即使详情加载失败，也选中该节点
      selectedNodeId = nodeId;
    } finally {
      nodeDetailLoading = false;
    }
  }

  function handleCloseNodeDetail() {
    selectedNodeDetail = null;
    nodeDetailError = null;
  }

  // 当用户在画布上手动选中节点时，也清空旧的详情（避免显示陈旧数据）
  function handleNodeSelectWithDetailReset(nodeId: string | null) {
    selectedNodeId = nodeId;
    if (selectedNodeDetail && selectedNodeDetail.node_id !== nodeId) {
      selectedNodeDetail = null;
    }
  }

  // 当用户修改了节点（消除校验错误的前提）
  function handleNodeUpdateWithValidation(nodeId: string, updates: Partial<WorkflowNode>) {
    updateNode(nodeId, updates);
    // 节点变更后清空校验错误（用户已经在修复）
    if (validationErrors && validationErrors.length > 0) {
      onClearValidationErrors?.();
    }
  }

  // 上下游面板"跳转上游节点"回调
  // FAIL-1: 先调用 Canvas 的 centerOnNode 让目标节点视觉居中，再设置选中。
  function handleFocusNode(nodeId: string) {
    canvasRef?.centerOnNode(nodeId);
    selectedNodeId = nodeId;
  }

  // FAIL-2: 输出项跳转回调。从当前选中节点的 config 取 projectId/module_type，
  // 然后用 goto 跳转到对应路由。若无 projectId 则降级为日志。
  function handleJumpToTarget(target: { kind: string; value: string }) {
    const cur = selectedNode();
    const cfg = (cur?.config as Record<string, any>) || {};
    const projectId = (cfg.project_id as string) || '';
    const moduleType = (cfg.module_type as string) || target.value || '';
    switch (target.kind) {
      case 'pm_module':
        if (projectId && moduleType) {
          goto(`/pm/${projectId}/${moduleType}`);
        } else if (projectId) {
          goto(`/pm/${projectId}`);
        } else {
          console.log('[WorkflowDesigner] 跳转 PM 模块失败：缺少 projectId', target);
        }
        break;
      case 'pm_entry':
        if (projectId && moduleType && target.value) {
          goto(`/pm/${projectId}/${moduleType}?entry=${encodeURIComponent(target.value)}`);
        } else {
          console.log('[WorkflowDesigner] 跳转 PM 条目失败：缺少信息', target);
        }
        break;
      case 'answer':
        // answer 节点 write_target 是 PM 模块名，跳到模块列表页
        if (projectId && target.value) {
          goto(`/pm/${projectId}/${target.value}`);
        } else if (projectId) {
          goto(`/pm/${projectId}`);
        } else {
          console.log('[WorkflowDesigner] 跳转 answer 写入目标失败：缺少 projectId', target);
        }
        break;
      case 'openwebui_resource':
        if (cur?.type === 'tool_call') {
          goto('/admin/tools');
        } else if (cur?.type === 'function_call') {
          goto('/admin/functions');
        } else if (cur?.type === 'skill_call') {
          goto('/admin/settings/functions');
        } else if (cur?.type === 'mcp_call') {
          goto('/admin/settings/connections');
        } else {
          console.log('[WorkflowDesigner] 跳转 openwebui 资源失败：未知节点类型', cur?.type, target);
        }
        break;
      case 'variable':
      default:
        console.log('[WorkflowDesigner] variable 输出，无跳转目标', target);
        break;
    }
  }

  function handleNameChange(event: Event) {
    const target = event.target as HTMLInputElement;
    workflow = { ...workflow, name: target.value };
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Delete') {
      if (selectedNodeId) {
        deleteNode(selectedNodeId);
      } else if (selectedEdgeId) {
        deleteEdge(selectedEdgeId);
      }
    }
  }
</script>

<div class="workflow-designer" onkeydown={handleKeyDown} tabindex="0" role="application" aria-label="Workflow designer">
  <!-- Header -->
  <header class="designer-header">
    <div class="header-left">
      <input
        type="text"
        class="workflow-name-input"
        value={workflow.name}
        onchange={handleNameChange}
        aria-label="Workflow name"
      />
      <div class="workflow-stats">
        <span class="stat">{nodeCount()} nodes</span>
        <span class="stat">{edgeCount()} edges</span>
      </div>
    </div>

    <div class="header-right">
      <button
        class="btn btn--secondary"
        onclick={handleExecute}
        disabled={executionStatus === 'running'}
      >
        {#if executionStatus === 'running'}
          <span class="spinner"></span>
          Running...
        {:else}
          ▶ Execute
        {/if}
      </button>

      <button
        class="btn btn--primary"
        onclick={handleSave}
        disabled={isSaving}
      >
        {#if isSaving}
          <span class="spinner"></span>
          Saving...
        {:else}
          💾 Save
        {/if}
      </button>
    </div>
  </header>

  <!-- Main Content -->
  <div class="designer-body">
    <!-- Sidebar -->
    <NodeSidebar
      collapsed={sidebarCollapsed}
      onToggleCollapse={() => sidebarCollapsed = !sidebarCollapsed}
      onNodeDragStart={(node, clientX, clientY) => {
        // Handle drag start if needed
      }}
    />

    <!-- Canvas -->
    <div class="canvas-wrapper">
      <Canvas
        bind:this={canvasRef}
        nodes={workflow.nodes}
        edges={workflow.edges}
        selectedNodeId={selectedNodeId}
        selectedEdgeId={selectedEdgeId}
        nodeResults={nodeResults}
        validationErrors={validationErrors}
        onNodeSelect={handleNodeSelectWithDetailReset}
        onNodeMove={handleNodeMove}
        onNodeDrop={handleNodeDrop}
        onEdgeCreate={handleEdgeCreate}
        onEdgeSelect={handleEdgeSelect}
        onEdgeDelete={handleEdgeDelete}
      />
    </div>

    <!-- Property Panel -->
    <PropertyPanel
      node={selectedNode()}
      nodes={workflow.nodes}
      edges={workflow.edges}
      onNodeUpdate={handleNodeUpdateWithValidation}
      onNodeFocus={handleFocusNode}
      onJumpToTarget={handleJumpToTarget}
    />
  </div>

  <!-- Execution Panel -->
  {#if showExecutionPanel}
    <div class="execution-panel" class:success={executionStatus === 'success'} class:error={executionStatus === 'error'} class:running={executionStatus === 'running'} class:awaiting={executionStatus === 'awaiting_input'}>
      <div class="execution-header">
        <div class="execution-content">
          {#if executionStatus === 'running'}
            <span class="spinner"></span>
            <span>Executing workflow...</span>
          {:else if executionStatus === 'awaiting_input'}
            <span class="status-icon">⏸</span>
            <span>等待人工确认...</span>
          {:else if executionStatus === 'success'}
            <span class="status-icon">✅</span>
            <span>Workflow executed successfully!</span>
          {:else if executionStatus === 'error'}
            <span class="status-icon">❌</span>
            <span>Workflow execution failed</span>
          {/if}
        </div>
        <button class="close-btn" onclick={() => showExecutionPanel = false}>✕</button>
      </div>

      <!-- human_input 表单模态（执行面板内联展示） -->
      {#if awaitingInput}
        <div class="human-input-form">
          <h4 class="form-prompt">{awaitingInput.prompt}</h4>
          {#if awaitingInput.fields.length === 0}
            <p class="form-empty">此节点未定义表单字段，直接点击"确认并继续"以恢复执行。</p>
          {:else}
            {#each awaitingInput.fields as field}
              <div class="form-field">
                <label for={`hf-${field.name}`}>
                  {field.label}{field.required ? ' *' : ''}
                </label>
                {#if field.type === 'textarea'}
                  <textarea id={`hf-${field.name}`} rows="3"
                    bind:value={humanInputResponse[field.name]}></textarea>
                {:else if field.type === 'select'}
                  <select id={`hf-${field.name}`}
                    bind:value={humanInputResponse[field.name]}>
                    <option value="">请选择</option>
                    {#each field.options || [] as opt}
                      <option value={opt}>{opt}</option>
                    {/each}
                  </select>
                {:else if field.type === 'confirm'}
                  <label class="checkbox-label">
                    <input type="checkbox"
                      bind:checked={humanInputResponse[field.name]} />
                    <span>{field.label}</span>
                  </label>
                {:else}
                  <input id={`hf-${field.name}`} type="text"
                    bind:value={humanInputResponse[field.name]} />
                {/if}
              </div>
            {/each}
          {/if}
          <div class="form-actions">
            <button class="submit-btn" onclick={submitHumanInput} disabled={isResuming}>
              {isResuming ? '提交中...' : '提交并继续'}
            </button>
            <button class="cancel-btn" onclick={cancelHumanInput} disabled={isResuming}>取消</button>
          </div>
        </div>
      {/if}

      <!-- Progress bar -->
      {#if executionProgress}
        <div class="progress-bar">
          <div class="progress-fill" style="width: {executionProgress.total_nodes > 0 ? (executionProgress.completed_nodes / executionProgress.total_nodes * 100) : 0}%"></div>
          <span class="progress-text">{executionProgress.completed_nodes} / {executionProgress.total_nodes} nodes</span>
        </div>
      {/if}

      <!-- 实时日志 -->
      {#if executionLogs.length > 0}
        <div class="execution-logs">
          <div class="logs-header">
            <span>实时日志（{executionLogs.length}）</span>
            <button class="clear-logs-btn" onclick={() => executionLogs = []}>清空</button>
          </div>
          <div class="logs-list">
            {#each executionLogs as log (log.ts + log.event + log.message)}
              <div class="log-entry log-{log.level}">
                <span class="log-time">{new Date(log.ts).toLocaleTimeString()}</span>
                <span class="log-message">{log.message}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Node results list -->
      {#if Object.keys(nodeResults).length > 0}
        <div class="node-results-list">
          {#each Object.entries(nodeResults) as [nodeId, result]}
            <button
              class="node-result"
              class:selected={selectedNodeDetail?.node_id === nodeId}
              onclick={() => handleNodeResultClick(nodeId)}
              title="点击查看节点运行时详情"
            >
              <span class="node-name">{workflow.nodes.find(n => n.id === nodeId)?.name || nodeId}</span>
              <span class="status-badge {result.status}">{result.status}</span>
              {#if result.execution_time_ms}
                <span class="time">{Math.round(result.execution_time_ms)}ms</span>
              {/if}
            </button>
          {/each}
        </div>
      {/if}

      <!-- 节点运行时详情 (Part B - Task 8) -->
      {#if nodeDetailLoading}
        <div class="node-detail-panel">
          <div class="node-detail-header">
            <span>加载节点详情…</span>
          </div>
        </div>
      {:else if nodeDetailError}
        <div class="node-detail-panel">
          <div class="node-detail-header">
            <span>节点详情加载失败</span>
            <button class="close-btn" onclick={handleCloseNodeDetail}>✕</button>
          </div>
          <div class="execution-error">{nodeDetailError}</div>
        </div>
      {:else if selectedNodeDetail}
        <div class="node-detail-panel">
          <div class="node-detail-header">
            <span class="node-detail-title">{selectedNodeDetail.node_name}</span>
            <span class="node-detail-type">{selectedNodeDetail.node_type}</span>
            <button class="close-btn" onclick={handleCloseNodeDetail}>✕</button>
          </div>
          <div class="node-detail-row">
            <span class="detail-label">状态</span>
            <span class="status-badge {selectedNodeDetail.status}">{selectedNodeDetail.status}</span>
          </div>
          {#if selectedNodeDetail.execution_time_ms != null}
            <div class="node-detail-row">
              <span class="detail-label">耗时</span>
              <span class="detail-value">{Math.round(selectedNodeDetail.execution_time_ms)}ms</span>
            </div>
          {/if}
          {#if selectedNodeDetail.error}
            <div class="node-detail-row">
              <span class="detail-label">错误</span>
              <span class="detail-value error-text">{selectedNodeDetail.error}</span>
            </div>
          {/if}
          {#if selectedNodeDetail.tool_call}
            <div class="node-detail-section">
              <div class="detail-section-title">Tool Call</div>
              <div class="node-detail-row">
                <span class="detail-label">Extension</span>
                <span class="detail-value mono">{selectedNodeDetail.tool_call.extension_id || '-'}</span>
              </div>
              {#if selectedNodeDetail.tool_call.input != null}
                <div class="node-detail-row">
                  <span class="detail-label">Input</span>
                  <pre class="detail-pre">{JSON.stringify(selectedNodeDetail.tool_call.input, null, 2)}</pre>
                </div>
              {/if}
              {#if selectedNodeDetail.tool_call.output != null}
                <div class="node-detail-row">
                  <span class="detail-label">Output</span>
                  <pre class="detail-pre">{JSON.stringify(selectedNodeDetail.tool_call.output, null, 2)}</pre>
                </div>
              {/if}
            </div>
          {/if}
          {#if selectedNodeDetail.write_target}
            {@const wtEntryId = selectedNodeDetail.write_target_entry_id || null}
            {@const wtProjectId = selectedNodeDetail.write_target_project_id || null}
            {@const wtModule = selectedNodeDetail.write_target_module || selectedNodeDetail.write_target}
            {@const wtHref = (wtEntryId && wtProjectId && wtModule)
              ? `/pm/${wtProjectId}/${wtModule}?entry=${encodeURIComponent(wtEntryId)}`
              : null}
            <div class="node-detail-row">
              <span class="detail-label">写入目标</span>
              {#if wtHref}
                <!-- FAIL-3: 有 entry_id 时渲染为可点击链接，新标签页打开 -->
                <a
                  class="detail-value pm-write-target pm-write-target-link"
                  href={wtHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="在新标签页中查看 PM 条目"
                >
                  已写入 PM 条目 {wtEntryId}
                </a>
              {:else}
                <!-- FAIL-3: 无 entry_id 时降级为纯文本 -->
                <span class="detail-value pm-write-target">PM 模块: {selectedNodeDetail.write_target}</span>
              {/if}
            </div>
          {/if}
          {#if selectedNodeDetail.output && Object.keys(selectedNodeDetail.output).length > 0}
            <div class="node-detail-section">
              <div class="detail-section-title">Output</div>
              <pre class="detail-pre">{JSON.stringify(selectedNodeDetail.output, null, 2)}</pre>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Final output -->
      {#if executionOutput}
        <div class="execution-output">
          <h4>Output</h4>
          <pre>{JSON.stringify(executionOutput, null, 2)}</pre>
        </div>
      {/if}

      <!-- Error message -->
      {#if executionError}
        <div class="execution-error">{executionError}</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .workflow-designer {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    position: relative;
    overflow: hidden;
    background-color: #f9fafb;
    outline: none;
  }

  /* Header */
  .designer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background-color: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    flex-shrink: 0;
    height: 56px;
    box-sizing: border-box;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .workflow-name-input {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    background: transparent;
    transition: border-color 0.2s ease, background-color 0.2s ease;
    min-width: 200px;
  }

  .workflow-name-input:hover {
    border-color: #e5e7eb;
    background-color: #f9fafb;
  }

  .workflow-name-input:focus {
    outline: none;
    border-color: #3b82f6;
    background-color: #ffffff;
  }

  .workflow-stats {
    display: flex;
    gap: 12px;
  }

  .stat {
    font-size: 12px;
    color: #6b7280;
    padding: 4px 8px;
    background-color: #f3f4f6;
    border-radius: 4px;
  }

  .header-right {
    display: flex;
    gap: 8px;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn--primary {
    background-color: #3b82f6;
    color: white;
  }

  .btn--primary:hover:not(:disabled) {
    background-color: #2563eb;
  }

  .btn--secondary {
    background-color: #f3f4f6;
    color: #374151;
    border-color: #e5e7eb;
  }

  .btn--secondary:hover:not(:disabled) {
    background-color: #e5e7eb;
  }

  /* Body */
  .designer-body {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .canvas-wrapper {
    flex: 1;
    overflow: hidden;
    position: relative;
  }

  /* Execution Panel */
  .execution-panel {
    position: absolute;
    bottom: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px 16px;
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 10;
    max-width: 400px;
    max-height: 60vh;
    overflow-y: auto;
  }

  .execution-panel.success {
    border-color: #22c55e;
    background-color: #f0fdf4;
  }

  .execution-panel.error {
    border-color: #ef4444;
    background-color: #fef2f2;
  }

  .execution-panel.running {
    border-color: #3b82f6;
    background-color: #eff6ff;
  }

  .execution-panel.awaiting {
    border-color: #f59e0b;
    background-color: #fffbeb;
    max-width: 480px;
  }

  /* human_input 表单 */
  .human-input-form {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 10px 0;
    border-top: 1px dashed #fbbf24;
    margin-top: 6px;
  }
  .human-input-form .form-prompt {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #92400e;
  }
  .human-input-form .form-empty {
    font-size: 12px;
    color: #6b7280;
    margin: 0;
  }
  .human-input-form .form-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 12px;
  }
  .human-input-form .form-field label {
    font-weight: 500;
    color: #374151;
  }
  .human-input-form .form-field input[type="text"],
  .human-input-form .form-field textarea,
  .human-input-form .form-field select {
    width: 100%;
    padding: 6px 8px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 12px;
    font-family: inherit;
    box-sizing: border-box;
  }
  .human-input-form .form-field textarea {
    resize: vertical;
  }
  .human-input-form .checkbox-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: normal;
  }
  .human-input-form .form-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    margin-top: 4px;
  }
  .human-input-form .submit-btn,
  .human-input-form .cancel-btn {
    padding: 6px 14px;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
  }
  .human-input-form .submit-btn {
    background-color: #f59e0b;
    color: #ffffff;
  }
  .human-input-form .submit-btn:disabled {
    background-color: #d1d5db;
    cursor: not-allowed;
  }
  .human-input-form .cancel-btn {
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .execution-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .execution-content {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #374151;
  }

  .status-icon {
    font-size: 16px;
  }

  .close-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    color: #6b7280;
    transition: background-color 0.2s ease;
  }

  .close-btn:hover {
    background-color: #f3f4f6;
  }

  /* Progress bar */
  .progress-bar {
    position: relative;
    width: 100%;
    height: 20px;
    background-color: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background-color: #3b82f6;
    transition: width 0.3s ease;
  }

  .progress-text {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 11px;
    line-height: 20px;
    color: #111827;
    font-weight: 500;
  }

  /* Node results */
  .node-results-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 12px;
  }

  .node-result {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
    width: 100%;
    transition: background 0.15s, border-color 0.15s;
  }

  .node-result:hover {
    background: #f0f9ff;
    border-color: #bae6fd;
  }

  .node-result.selected {
    background: #dbeafe;
    border-color: #3b82f6;
  }

  /* 节点运行时详情面板 */
  .node-detail-panel {
    margin-top: 8px;
    padding: 8px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-size: 12px;
  }

  .node-detail-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 6px;
  }

  .node-detail-title {
    font-weight: 600;
    color: #1f2937;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .node-detail-type {
    font-size: 10px;
    padding: 1px 5px;
    background: #e5e7eb;
    color: #6b7280;
    border-radius: 3px;
    text-transform: uppercase;
  }

  .node-detail-row {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 3px 0;
  }

  .detail-label {
    font-size: 11px;
    color: #6b7280;
    min-width: 60px;
    font-weight: 500;
  }

  .detail-value {
    font-size: 12px;
    color: #1f2937;
    flex: 1;
    word-break: break-word;
  }

  .detail-value.mono {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 11px;
  }

  .detail-value.error-text {
    color: #991b1b;
  }

  .detail-value.pm-write-target {
    color: #1e40af;
    font-weight: 500;
  }

  /* FAIL-3: answer 节点写入目标链接样式 */
  .detail-value.pm-write-target-link {
    color: #1d4ed8;
    text-decoration: underline;
    cursor: pointer;
    display: inline-block;
    word-break: break-all;
  }

  .detail-value.pm-write-target-link:hover {
    color: #1e3a8a;
    text-decoration: underline;
  }

  .detail-pre {
    flex: 1;
    background: #1f2937;
    color: #f9fafb;
    padding: 6px;
    border-radius: 4px;
    font-size: 10px;
    overflow-x: auto;
    max-height: 100px;
    overflow-y: auto;
    margin: 0;
    font-family: 'Monaco', 'Menlo', monospace;
  }

  .node-detail-section {
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px dashed #e5e7eb;
  }

  .detail-section-title {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  .node-result .node-name {
    flex: 1;
    font-weight: 500;
    color: #374151;
  }

  .status-badge {
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    text-transform: uppercase;
  }

  .status-badge.completed {
    background-color: #dcfce7;
    color: #166534;
  }

  .status-badge.running, .status-badge.in_progress {
    background-color: #fef3c7;
    color: #92400e;
  }

  .status-badge.failed {
    background-color: #fee2e2;
    color: #991b1b;
  }

  .time {
    color: #6b7280;
    font-size: 11px;
  }

  /* Output */
  .execution-output {
    margin-top: 8px;
  }

  .execution-output h4 {
    font-size: 12px;
    font-weight: 600;
    margin: 0 0 4px 0;
    color: #374151;
  }

  .execution-output pre {
    background-color: #1f2937;
    color: #f9fafb;
    padding: 8px;
    border-radius: 4px;
    font-size: 11px;
    overflow-x: auto;
    max-height: 150px;
    overflow-y: auto;
    margin: 0;
  }

  .execution-error {
    margin-top: 8px;
    padding: 8px;
    background-color: #fee2e2;
    color: #991b1b;
    border-radius: 4px;
    font-size: 12px;
  }

  /* Spinner */
  .spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid #e5e7eb;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .workflow-designer {
      background-color: #111827;
    }

    .designer-header {
      background-color: #1f2937;
      border-bottom-color: #374151;
    }

    .workflow-name-input {
      color: #f9fafb;
    }

    .workflow-name-input:hover {
      background-color: #374151;
      border-color: #4b5563;
    }

    .stat {
      background-color: #374151;
      color: #9ca3af;
    }

    .btn--secondary {
      background-color: #374151;
      color: #d1d5db;
      border-color: #4b5563;
    }

    .btn--secondary:hover:not(:disabled) {
      background-color: #4b5563;
    }

    .execution-panel {
      background-color: #1f2937;
      border-color: #374151;
    }

    .execution-content {
      color: #d1d5db;
    }
  }

  /* 实时日志区块 */
  .execution-logs {
    border-top: 1px solid #e5e7eb;
    padding: 8px 12px;
    max-height: 240px;
    display: flex;
    flex-direction: column;
  }
  .logs-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 4px;
  }
  .clear-logs-btn {
    background: transparent;
    border: 1px solid #e5e7eb;
    color: #6b7280;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
  }
  .clear-logs-btn:hover {
    background: #f3f4f6;
  }
  .logs-list {
    flex: 1;
    overflow-y: auto;
    font-family: ui-monospace, monospace;
    font-size: 11px;
  }
  .log-entry {
    display: flex;
    gap: 8px;
    padding: 2px 0;
  }
  .log-time { color: #9ca3af; flex-shrink: 0; }
  .log-message { white-space: pre-wrap; word-break: break-all; }
  .log-info .log-message { color: #6b7280; }
  .log-success .log-message { color: #10b981; }
  .log-error .log-message { color: #ef4444; }
  .log-warn .log-message { color: #f59e0b; }
</style>
