# Workflow + Agent Engine Design Document

**Date:** 2026-07-14
**Status:** Approved
**Author:** Atlas (AI Assistant)

---

## 1. Overview

Design a Dify-style Workflow engine and Agent runtime for the open-pm-webui project, replacing the existing basic workflow system with a more powerful, flexible architecture.

### Goals
- Visual workflow orchestration (drag-and-drop nodes, connections)
- Multiple node types: LLM, Condition, Tool Call, Variable Set, etc.
- Agent capabilities: Tool Use, Memory Management, Task Planning
- Integration with existing Svelte 5 frontend and FastAPI backend
- Support for both predefined workflows and autonomous agent execution

---

## 2. Architecture

### 2.1 High-Level Design (Layered Architecture)

```
┌─────────────────────────────────────────────┐
│              Frontend Layer                  │
│  ┌─────────────┐      ┌─────────────────┐  │
│  │ Workflow    │      │ Agent Chat      │  │
│  │ Designer    │      │ Interface       │  │
│  │ (Svelte 5)  │      │ (Svelte 5)      │  │
│  └──────┬──────┘      └────────┬────────┘  │
└───────┼────────────────────┼───────────────┘
        │                    │
        ▼                    ▼
┌─────────────────────────────────────────────┐
│              API Layer (FastAPI)             │
│  ┌─────────────┐      ┌─────────────────┐  │
│  │ /api/v2/    │      │ /api/v2/agent/  │  │
│  │ workflows   │      │ sessions        │  │
│  │ /executions│      │ /runs           │  │
│  └──────┬──────┘      └────────┬────────┘  │
└───────┼────────────────────┼───────────────┘
        │                    │
        ▼                    ▼
┌─────────────────────────────────────────────┐
│           Service Layer                      │
│  ┌─────────────┐      ┌─────────────────┐  │
│  │ Workflow    │      │ Agent Runtime   │  │
│  │ Engine      │      │ Service         │  │
│  │             │      │                 │  │
│  │ • DAG解析   │      │ • ReAct Loop    │  │
│  │ • 拓扑排序  │      │ • Tool Use      │  │
│  │ • 状态机    │      │ • Memory Mgmt   │  │
│  │ • 节点调度  │      │ • Planning      │  │
│  └──────┬──────┘      └────────┬────────┘  │
└───────┼────────────────────┼───────────────┘
        │                    │
        └──────────┬─────────┘
                   ▼
┌─────────────────────────────────────────────┐
│           Shared Infrastructure              │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ LLM     │ │ Tool    │ │ Memory      │  │
│  │ Adapter │ │ Registry│ │ Store       │  │
│  │         │ │         │ │             │  │
│  │ • OpenAI│ │ • HTTP  │ │ • Short-term│  │
│  │ • Claude│ │ • DB    │ │ • Long-term │  │
│  │ • Local │ │ • PM    │ │ • Vector    │  │
│  └─────────┘ └─────────┘ └─────────────┘  │
└─────────────────────────────────────────────┘
```

### 2.2 Design Rationale

**Why Layered Architecture?**
- Clear separation of concerns between Workflow and Agent
- Shared infrastructure (LLM, Tools, Memory) reduces duplication
- Agent can be embedded as a special node type within Workflow
- Aligns with existing FastAPI/Svelte 5 stack without introducing microservice complexity

---

## 3. Database Schema

### 3.1 Core Tables

```sql
-- Workflow Definitions
CREATE TABLE v2_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_id UUID REFERENCES pm_project(id),
    
    -- DAG Definition (JSONB)
    nodes JSONB NOT NULL DEFAULT '[]',
    edges JSONB NOT NULL DEFAULT '[]',
    
    -- Metadata
    version INTEGER DEFAULT 1,
    is_template BOOLEAN DEFAULT FALSE,
    category VARCHAR(50), -- 'automation', 'agent', 'data_processing'
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, archived
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow Executions
CREATE TABLE v2_workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES v2_workflows(id) ON DELETE CASCADE,
    
    -- Execution Status
    status VARCHAR(20), -- pending, running, paused, completed, failed
    trigger_type VARCHAR(20), -- manual, webhook, schedule, agent
    
    -- Input/Output
    input_data JSONB,
    output_data JSONB,
    
    -- Execution Context
    context JSONB, -- Variable storage
    node_states JSONB, -- {node_id: {status, output, started_at, completed_at}}
    
    -- Error Handling
    error_message TEXT,
    error_node_id UUID,
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Sessions
CREATE TABLE v2_agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    
    -- Agent Configuration
    agent_type VARCHAR(50), -- 'react', 'plan_execute', 'openai_assistant'
    llm_config JSONB, -- {model, temperature, max_tokens}
    
    -- Memory Configuration
    memory_config JSONB, -- {short_term_size, long_term_enabled}
    
    -- Tool Permissions
    allowed_tools JSONB, -- ['tool_id_1', 'tool_id_2']
    
    -- Associated Workflow
    workflow_id UUID REFERENCES v2_workflows(id),
    
    status VARCHAR(20) DEFAULT 'active',
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent Execution Runs
CREATE TABLE v2_agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES v2_agent_sessions(id) ON DELETE CASCADE,
    
    -- User Input
    user_message TEXT NOT NULL,
    
    -- Agent Thought Process
    thought_process JSONB, -- [{step, action, observation, reasoning}]
    
    -- Tool Calls
    tool_calls JSONB, -- [{tool_id, input, output, duration}]
    
    -- Final Response
    assistant_message TEXT,
    
    -- Used Memories
    memories_used JSONB,
    
    -- Associated Workflow Execution
    workflow_execution_id UUID REFERENCES v2_workflow_executions(id),
    
    -- Performance Metrics
    token_usage JSONB, -- {prompt_tokens, completion_tokens}
    duration_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tool Registry
CREATE TABLE v2_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50), -- 'llm', 'data', 'pm', 'web', 'custom'
    
    -- Schemas
    config_schema JSONB,
    input_schema JSONB,
    output_schema JSONB,
    
    -- Execution Configuration
    execution_type VARCHAR(20), -- 'http', 'python', 'javascript', 'sql'
    execution_config JSONB,
    
    -- Authentication
    auth_config JSONB,
    
    is_builtin BOOLEAN DEFAULT FALSE,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Memory Store
CREATE TABLE v2_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES v2_agent_sessions(id) ON DELETE CASCADE,
    
    memory_type VARCHAR(20), -- 'short_term', 'long_term', 'episodic'
    content TEXT NOT NULL,
    
    -- Vectorization (for semantic search)
    embedding VECTOR(1536),
    
    -- Metadata
    metadata JSONB,
    importance_score FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP
);
```

---

## 4. Node Type Definitions

### 4.1 Supported Node Types

```typescript
// Control Flow
type NodeType =
  | 'start'           // Entry point
  | 'end'             // Exit point
  | 'condition'       // Conditional branching
  | 'loop'            // Iteration
  | 'parallel'        // Parallel execution
  | 'merge'           // Join parallel branches
  
  // Data Processing
  | 'variable_set'    // Set variables
  | 'transform'       // Data transformation
  | 'filter'          // Data filtering
  
  // AI/LLM
  | 'llm'             // LLM invocation
  | 'prompt_template' // Prompt template
  | 'agent'           // Agent node (autonomous)
  
  // Tools
  | 'tool_call'       // Generic tool invocation
  | 'http_request'    // HTTP API call
  | 'database_query'  // Database operation
  
  // PM Specific
  | 'pm_create_entry' // Create PRD/requirement/test case
  | 'pm_update_entry' // Update existing entry
  | 'pm_query'        // Query PM data
  
  // Integration
  | 'webhook'         // Webhook trigger
  | 'schedule'        // Scheduled trigger
  | 'event_listen'    // Event listener
```

### 4.2 Node Configuration Interface

```typescript
interface NodeConfig {
  // Common fields
  id: string;
  type: NodeType;
  name: string;
  description?: string;
  
  // Visual positioning
  position: { x: number; y: number };
  
  // Type-specific configuration
  config: Record<string, any>;
  
  // Input/Output ports
  inputs: PortDefinition[];
  outputs: PortDefinition[];
  
  // Error handling strategy
  errorHandling?: {
    strategy: 'retry' | 'fallback' | 'abort';
    maxRetries?: number;
    fallbackNodeId?: string;
  };
}

interface PortDefinition {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'any';
  required: boolean;
  description?: string;
}
```

---

## 5. Workflow Engine Design

### 5.1 Core Engine (Python/FastAPI)

```python
class WorkflowEngine:
    """DAG-based workflow execution engine"""
    
    async def execute(
        self,
        workflow: Workflow,
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute a workflow DAG"""
        
        # 1. Parse DAG
        dag = self._parse_dag(workflow.nodes, workflow.edges)
        
        # 2. Topological sort for execution order
        execution_order = dag.topological_sort()
        
        # 3. Initialize state machine
        state = ExecutionState(workflow_id=workflow.id)
        
        # 4. Execute nodes
        for node_id in execution_order:
            node = dag.get_node(node_id)
            
            # Check preconditions
            if not self._check_preconditions(node, state):
                continue
            
            # Execute node with error handling
            try:
                result = await self._execute_node(node, state)
                state.set_node_result(node_id, result)
            except Exception as e:
                await self._handle_error(node, e, state)
                if state.should_abort:
                    break
        
        # 5. Return execution result
        return ExecutionResult(
            state=state,
            output=state.get_output()
        )
    
    async def _execute_node(self, node: Node, state: ExecutionState) -> NodeResult:
        """Dispatch execution based on node type"""
        executor = self.node_registry.get(node.type)
        return await executor.execute(node, state)
```

### 5.2 State Machine

```python
@dataclass
class ExecutionState:
    """Tracks workflow execution state"""
    workflow_id: UUID
    status: ExecutionStatus = ExecutionStatus.PENDING
    variables: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    error: Optional[str] = None
    should_abort: bool = False
    
    def set_node_result(self, node_id: str, result: NodeResult):
        self.node_results[node_id] = result
        
    def get_variable(self, name: str) -> Any:
        return self.variables.get(name)
        
    def set_variable(self, name: str, value: Any):
        self.variables[name] = value
```

---

## 6. Agent Runtime Design

### 6.1 ReAct-based Agent

```python
class AgentRuntime:
    """ReAct-based autonomous agent runtime"""
    
    async def run(
        self,
        session: AgentSession,
        user_message: str
    ) -> AgentRun:
        """Run agent with user input"""
        
        # 1. Retrieve relevant memories
        memories = await self.memory_store.retrieve(
            session_id=session.id,
            query=user_message,
            limit=session.memory_config.short_term_size
        )
        
        # 2. Initialize run record
        run = AgentRun(
            session_id=session.id,
            user_message=user_message,
            thought_process=[]
        )
        
        # 3. ReAct loop
        for step in range(session.max_steps):
            # Think
            thought = await self._think(
                session=session,
                user_message=user_message,
                memories=memories,
                previous_steps=run.thought_process
            )
            run.thought_process.append(thought)
            
            # Decide action
            if thought.should_respond:
                # Direct response
                run.assistant_message = thought.response
                break
            elif thought.should_use_tool:
                # Execute tool
                tool_result = await self._execute_tool(
                    tool_id=thought.tool_id,
                    tool_input=thought.tool_input,
                    session=session
                )
                run.tool_calls.append(tool_result)
                
                # Check if tool triggers workflow
                if tool_result.triggers_workflow:
                    execution = await self.workflow_engine.execute(
                        workflow=tool_result.workflow,
                        context=tool_result.context
                    )
                    run.workflow_execution_id = execution.id
            else:
                # Plan
                plan = await self._plan(
                    session=session,
                    goal=user_message,
                    context=thought.context
                )
                # Execute plan...
        
        # 4. Store memories
        await self.memory_store.store(
            session_id=session.id,
            content=run.assistant_message,
            metadata={'type': 'assistant_response'}
        )
        
        return run
    
    async def _think(
        self,
        session: AgentSession,
        user_message: str,
        memories: List[Memory],
        previous_steps: List[Thought]
    ) -> Thought:
        """LLM thinking process"""
        
        prompt = self._build_react_prompt(
            user_message=user_message,
            memories=memories,
            tools=session.allowed_tools,
            previous_steps=previous_steps
        )
        
        response = await self.llm_adapter.complete(
            model=session.llm_config.model,
            prompt=prompt,
            temperature=session.llm_config.temperature
        )
        
        return self._parse_thought(response)
```

### 6.2 Memory Management

```python
class MemoryStore:
    """Short-term and long-term memory management"""
    
    async def retrieve(
        self,
        session_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Memory]:
        """Retrieve relevant memories"""
        
        # Get short-term memories (recent)
        short_term = await self._get_short_term(session_id, limit)
        
        # Get long-term memories (semantic search)
        query_embedding = await self._embed(query)
        long_term = await self._semantic_search(
            session_id=session_id,
            embedding=query_embedding,
            limit=limit
        )
        
        # Combine and rank
        return self._rank_memories(short_term + long_term, query)
    
    async def store(
        self,
        session_id: UUID,
        content: str,
        metadata: Dict[str, Any]
    ):
        """Store new memory"""
        
        # Generate embedding
        embedding = await self._embed(content)
        
        # Store in database
        await self._insert_memory(
            session_id=session_id,
            content=content,
            embedding=embedding,
            metadata=metadata
        )
```

---

## 7. Frontend Design

### 7.1 Component Architecture

```
src/
├── routes/(app)/workflows/
│   ├── +page.svelte              # Workflow list
│   └── [workflowId]/
│       └── +page.svelte          # Workflow designer
│
├── routes/(app)/agent/
│   ├── +page.svelte              # Agent sessions list
│   └── [sessionId]/
│       └── +page.svelte          # Agent chat interface
│
└── lib/components/workflow-v2/
    ├── WorkflowDesigner.svelte   # Main designer canvas
    ├── NodeSidebar.svelte        # Draggable node palette
    ├── PropertyPanel.svelte      # Node configuration
    ├── Toolbar.svelte            # Designer toolbar
    ├── Canvas.svelte             # SVG canvas for nodes/edges
    ├── NodeComponent.svelte      # Individual node rendering
    ├── EdgeComponent.svelte      # Connection lines
    └── ExecutionPanel.svelte     # Execution monitoring
```

### 7.2 Key Components

```typescript
// WorkflowDesigner.svelte
<script lang="ts">
  import { Canvas } from './Canvas.svelte';
  import { NodeSidebar } from './NodeSidebar.svelte';
  import { PropertyPanel } from './PropertyPanel.svelte';
  
  let workflow = $state<Workflow>({
    nodes: [],
    edges: []
  });
  
  let selectedNode = $state<Node | null>(null);
  
  function addNode(type: NodeType, position: Point) {
    const node = createNode(type, position);
    workflow.nodes.push(node);
  }
  
  function connectNodes(source: string, target: string) {
    const edge = createEdge(source, target);
    workflow.edges.push(edge);
  }
  
  async function saveWorkflow() {
    await workflowApi.save(workflow);
  }
</script>

<div class="workflow-designer">
  <Toolbar {workflow} onSave={saveWorkflow} />
  <div class="designer-body">
    <NodeSidebar onDragStart={handleDragStart} />
    <Canvas 
      {workflow}
      bind:selectedNode
      onNodeAdd={addNode}
      onNodeConnect={connectNodes}
    />
    <PropertyPanel node={selectedNode} />
  </div>
</div>
```

---

## 8. API Design

### 8.1 Workflow API

```
POST   /api/v2/workflows              # Create workflow
GET    /api/v2/workflows              # List workflows
GET    /api/v2/workflows/:id          # Get workflow
PUT    /api/v2/workflows/:id          # Update workflow
DELETE /api/v2/workflows/:id          # Delete workflow
POST   /api/v2/workflows/:id/execute  # Execute workflow
GET    /api/v2/workflows/:id/executions # Execution history
```

### 8.2 Execution API

```
GET    /api/v2/executions/:id         # Get execution status
POST   /api/v2/executions/:id/pause  # Pause execution
POST   /api/v2/executions/:id/resume # Resume execution
POST   /api/v2/executions/:id/cancel # Cancel execution
GET    /api/v2/executions/:id/logs   # Execution logs
```

### 8.3 Agent API

```
POST   /api/v2/agent/sessions         # Create session
GET    /api/v2/agent/sessions/:id     # Get session
POST   /api/v2/agent/sessions/:id/chat # Send message
GET    /api/v2/agent/sessions/:id/runs  # Run history
DELETE /api/v2/agent/sessions/:id     # Delete session
```

### 8.4 Tool API

```
GET    /api/v2/tools                  # List tools
POST   /api/v2/tools                  # Register tool
GET    /api/v2/tools/:id              # Get tool
POST   /api/v2/tools/:id/execute      # Execute tool
```

---

## 9. Shared Infrastructure

### 9.1 LLM Adapter

```python
class LLMAdapter:
    """Unified LLM interface supporting multiple providers"""
    
    async def complete(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate completion"""
        provider = self._get_provider(model)
        return await provider.complete(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
```

### 9.2 Tool Registry

```python
class ToolRegistry:
    """Central tool registration and execution"""
    
    def register(self, tool: Tool):
        self._tools[tool.id] = tool
    
    async def execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any]
    ) -> ToolResult:
        tool = self._tools.get(tool_id)
        if not tool:
            raise ToolNotFoundError(tool_id)
        return await tool.execute(input_data)
```

---

## 10. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Database schema migration
- [ ] Core workflow engine (DAG parsing, topological sort)
- [ ] Basic node types (start, end, llm, condition)
- [ ] REST API endpoints

### Phase 2: Frontend (Week 2-3)
- [ ] Workflow designer canvas
- [ ] Node sidebar and property panel
- [ ] Connection handling
- [ ] Save/load workflow

### Phase 3: Agent (Week 3-4)
- [ ] Agent runtime (ReAct loop)
- [ ] Tool registry and execution
- [ ] Memory store (short-term)
- [ ] Agent chat interface

### Phase 4: Advanced Features (Week 4-5)
- [ ] Parallel execution
- [ ] Error handling and retry
- [ ] Long-term memory with vector search
- [ ] PM-specific node types

---

## 11. Migration Strategy

1. **Parallel Deployment**: New v2 tables alongside existing tables
2. **Gradual Migration**: Move existing workflows to new schema
3. **Backward Compatibility**: Keep old API working during transition
4. **Feature Flags**: Enable new features per-project

---

## 12. Success Criteria

- [ ] Visual workflow designer functional
- [ ] Support for 10+ node types
- [ ] Agent can use tools and maintain memory
- [ ] Workflow execution with state tracking
- [ ] Integration with existing PM modules
- [ ] Performance: Workflow execution < 2s for simple flows

---

**Next Step:** Invoke `writing-plans` skill to generate detailed implementation plan.
