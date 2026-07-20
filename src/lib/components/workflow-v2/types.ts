/**
 * Workflow Designer v2 - Type Definitions
 * 
 * Core types for the workflow designer system.
 * Used by Canvas, NodeSidebar, PropertyPanel, and WorkflowDesigner components.
 */

// ===== Basic Geometry =====

export interface Point {
	x: number;
	y: number;
}

export interface Size {
	width: number;
	height: number;
}

// ===== Port System =====

export type PortDirection = 'input' | 'output';

export interface Port {
	id: string;
	name: string;
	direction: PortDirection;
	dataType?: string;
	required?: boolean;
}

// ===== Node System =====

export type NodeType =
	// Control
	| 'start'
	| 'end'
	| 'condition'
	| 'variable_set'
	| 'loop'
	// AI
	| 'llm'
	| 'agent'
	| 'knowledge_retrieval'
	| 'template'
	| 'parameter_extractor'
	// Tools
	| 'http_request'
	| 'code'
	| 'tool_call'
	| 'answer'
	// 扩展资源调用（openwebui Functions / Skills / MCP）
	| 'function_call'
	| 'skill_call'
	| 'mcp_call'
	// PM工作台
	| 'pm_module'
	// 人工确认（human-in-the-loop，运行时通过 awaiting_input 事件挂起/恢复）
	| 'human_input';

export interface WorkflowNode {
	id: string;
	type: NodeType;
	name: string;
	description?: string;
	x: number;
	y: number;
	width?: number;
	height?: number;
	config?: Record<string, unknown>;
	ports?: Port[];
	selected?: boolean;
}

// ===== Edge System =====

export interface WorkflowEdge {
	id: string;
	sourceNodeId: string;
	sourcePortId?: string;
	targetNodeId: string;
	targetPortId?: string;
	label?: string;
	condition?: string;
	dataMappingRules?: Record<string, string>;
}

// ===== Workflow =====

export interface Workflow {
	id: string;
	name: string;
	description?: string;
	version?: string;
	status?: 'draft' | 'published' | 'archived' | 'active';
	nodes: WorkflowNode[];
	edges: WorkflowEdge[];
	createdAt?: number;
	updatedAt?: number;
	created_at?: number;
	updated_at?: number;
	owner_id?: string;
	project_ids?: string[];
	project_id?: string;
	tags?: string[];
}

// ===== Node Template (for sidebar) =====

export interface NodeOutputSchema {
	name: string;
	type: 'string' | 'number' | 'object' | 'array' | 'boolean';
	description?: string;
}

export interface NodeTemplate {
	id: string;
	type: NodeType;
	label: string;
	description: string;
	icon: string;
	color: string;
	category: string;
	config?: Record<string, unknown>;
	ports?: Port[];
	outputs?: NodeOutputSchema[];
}

export interface NodeCategory {
	id: string;
	label: string;
	icon: string;
	nodes: NodeTemplate[];
}

// ===== Constants =====

export const NODE_TYPES: NodeType[] = [
	'start',
	'end',
	'condition',
	'variable_set',
	'loop',
	'llm',
	'agent',
	'knowledge_retrieval',
	'template',
	'parameter_extractor',
	'http_request',
	'code',
	'tool_call',
	'answer',
	'function_call',
	'skill_call',
	'mcp_call',
	'pm_module',
	'human_input'
];

export const NODE_TYPE_COLORS: Record<NodeType, string> = {
	start: '#22c55e',
	end: '#ef4444',
	llm: '#3b82f6',
	condition: '#f59e0b',
	variable_set: '#8b5cf6',
	tool_call: '#06b6d4',
	agent: '#ec4899',
	loop: '#0ea5e9',
	knowledge_retrieval: '#14b8a6',
	template: '#a855f7',
	parameter_extractor: '#f97316',
	http_request: '#64748b',
	code: '#84cc16',
	answer: '#10b981',
	function_call: '#d97706',
	skill_call: '#059669',
	mcp_call: '#7c3aed',
	pm_module: '#6366f1',
	human_input: '#f59e0b'
};

export const NODE_TYPE_LABELS: Record<NodeType, string> = {
	start: 'Start',
	end: 'End',
	llm: 'LLM',
	condition: 'Condition',
	variable_set: 'Set Variable',
	tool_call: 'Tool Call',
	agent: 'Agent',
	loop: 'Loop',
	knowledge_retrieval: 'Knowledge Retrieval',
	template: 'Template',
	parameter_extractor: 'Parameter Extractor',
	http_request: 'HTTP Request',
	code: 'Code',
	answer: 'Answer',
	function_call: 'Function Call',
	skill_call: 'Skill Call',
	mcp_call: 'MCP Call',
	pm_module: 'PM Module',
	human_input: 'Human Input'
};

export const NODE_TYPE_ICONS: Record<NodeType, string> = {
	start: 'play',
	end: 'stop',
	llm: 'brain',
	condition: 'git-branch',
	variable_set: 'variable',
	tool_call: 'wrench',
	agent: 'bot',
	loop: 'repeat',
	knowledge_retrieval: 'database',
	template: 'file-text',
	parameter_extractor: 'extract',
	http_request: 'globe',
	code: 'code',
	answer: 'message-square',
	function_call: 'code',
	skill_call: 'award',
	mcp_call: 'plug',
	pm_module: 'briefcase',
	human_input: 'hand'
};

export const NODE_CATEGORIES: NodeCategory[] = [
	{
		id: 'control',
		label: 'Control',
		icon: 'control',
		nodes: [
			{
				id: 'node-start',
				type: 'start',
				label: 'Start',
				description: 'Workflow entry point',
				icon: 'play',
				color: '#22c55e',
				category: 'control',
				ports: [{ id: 'out', name: 'output', direction: 'output' }],
				outputs: [{ name: 'input', type: 'string', description: '工作流输入参数' }]
			},
			{
				id: 'node-end',
				type: 'end',
				label: 'End',
				description: 'Workflow exit point',
				icon: 'stop',
				color: '#ef4444',
				category: 'control',
				ports: [{ id: 'in', name: 'input', direction: 'input' }]
			},
			{
				id: 'node-condition',
				type: 'condition',
				label: 'Condition',
				description: 'Branch based on condition',
				icon: 'git-branch',
				color: '#f59e0b',
				category: 'control',
				config: { condition: '', conditions: [], combinator: 'and' },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'true', name: 'true', direction: 'output' },
					{ id: 'false', name: 'false', direction: 'output' }
				],
				outputs: [{ name: 'result', type: 'boolean', description: '条件求值结果' }]
			},
			{
				id: 'node-variable',
				type: 'variable_set',
				label: 'Set Variable',
				description: 'Set or update a variable',
				icon: 'variable',
				color: '#8b5cf6',
				category: 'control',
				config: { variable_name: '', variable_value: '' },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [{ name: 'variable_value', type: 'string', description: '设置的变量值' }]
			},
			{
				id: 'node-loop',
				type: 'loop',
				label: 'Loop',
				description: 'Iterate over array or while condition',
				icon: 'repeat',
				color: '#0ea5e9',
				category: 'control',
				config: { loop_type: 'for_each', iterator: '', condition: '', max_iterations: 1000, body_node_ids: [] },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'body', name: 'body', direction: 'output' },
					{ id: 'done', name: 'done', direction: 'output' }
				],
				outputs: [
					{ name: 'current_item', type: 'object', description: '当前迭代项' },
					{ name: 'current_index', type: 'number', description: '当前迭代索引' },
					{ name: 'results', type: 'array', description: '所有迭代结果' }
				]
			}
		]
	},
	{
		id: 'ai',
		label: 'AI',
		icon: 'sparkles',
		nodes: [
			{
				id: 'node-llm',
				type: 'llm',
				label: 'LLM',
				description: 'Call a language model',
				icon: 'brain',
				color: '#3b82f6',
				category: 'ai',
				config: { model: '', system_prompt: '', prompt: '', temperature: 0.7, max_tokens: 2048 },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'response', type: 'string', description: 'LLM 响应文本' },
					{ name: 'metadata', type: 'object', description: 'token 用量、模型名等元数据' }
				]
			},
			{
				id: 'node-agent',
				type: 'agent',
				label: 'Agent',
				description: 'Call an AI agent',
				icon: 'bot',
				color: '#ec4899',
				category: 'ai',
				config: { agent_id: '', instructions: '' },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'response', type: 'string', description: 'Agent 响应文本' },
					{ name: 'metadata', type: 'object', description: '执行元数据' }
				]
			},
			{
				id: 'node-knowledge',
				type: 'knowledge_retrieval',
				label: 'Knowledge Retrieval',
				description: 'Retrieve from knowledge base',
				icon: 'database',
				color: '#14b8a6',
				category: 'ai',
				config: { query: '', knowledge_base_id: '', top_k: 5 },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'documents', type: 'array', description: '检索到的文档列表' },
					{ name: 'count', type: 'number', description: '文档数量' }
				]
			},
			{
				id: 'node-template',
				type: 'template',
				label: 'Template',
				description: 'Render a template with variables',
				icon: 'file-text',
				color: '#a855f7',
				category: 'ai',
				config: { template: '', output_variable: 'result' },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [{ name: 'result', type: 'string', description: '渲染后的文本（变量名取自 config.output_variable）' }]
			},
			{
				id: 'node-parameter-extractor',
				type: 'parameter_extractor',
				label: 'Parameter Extractor',
				description: 'Extract structured parameters from text via LLM',
				icon: 'extract',
				color: '#f97316',
				category: 'ai',
				config: { model: '', input_text: '', parameters: [], output_variable: 'extracted' },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [{ name: 'extracted', type: 'object', description: '提取的结构化参数（变量名取自 config.output_variable）' }]
			}
		]
	},
	{
		id: 'tools',
		label: 'Tools',
		icon: 'wrench',
		nodes: [
			{
				id: 'node-http',
				type: 'http_request',
				label: 'HTTP Request',
				description: 'Send an HTTP request',
				icon: 'globe',
				color: '#64748b',
				category: 'tools',
				config: { method: 'GET', url: '', headers: {}, body: '' },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'status_code', type: 'number', description: 'HTTP 状态码' },
					{ name: 'body', type: 'object', description: '响应体（解析后）' },
					{ name: 'headers', type: 'object', description: '响应头' }
				]
			},
			{
				id: 'node-code',
				type: 'code',
				label: 'Code',
				description: 'Execute Python code in a sandbox',
				icon: 'code',
				color: '#84cc16',
				category: 'tools',
				config: { code: '', input_variables: {}, output_variable: 'result' },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [{ name: 'result', type: 'object', description: '代码返回值（变量名取自 config.output_variable）' }]
			},
			{
			id: 'node-tool',
			type: 'tool_call',
			label: 'Tool Call',
			description: 'Call an external tool',
			icon: 'wrench',
			color: '#06b6d4',
			category: 'tools',
			config: { tool_name: '', parameters: {} },
			ports: [
				{ id: 'in', name: 'input', direction: 'input' },
				{ id: 'out', name: 'output', direction: 'output' }
			],
			outputs: [{ name: 'result', type: 'object', description: '工具调用返回值' }]
		},
		{
			id: 'node-answer',
			type: 'answer',
			label: 'Answer',
			description: 'Output a direct answer',
			icon: 'message-square',
			color: '#10b981',
			category: 'tools',
			config: { answer: '', output_variable: 'answer' },
			ports: [
				{ id: 'in', name: 'input', direction: 'input' },
				{ id: 'out', name: 'output', direction: 'output' }
			],
			outputs: [{ name: 'answer', type: 'string', description: '最终答案文本' }]
		},
		{
			id: 'node-function-call',
			type: 'function_call',
			label: 'Function Call',
			description: '调用 openwebui Function (filter / action / pipe)',
			icon: 'code',
			color: '#d97706',
			category: 'tools',
			config: { extension_id: '', input_mapping: {}, output_schema: [] },
			ports: [
				{ id: 'in', name: 'input', direction: 'input' },
				{ id: 'out', name: 'output', direction: 'output' }
			],
			outputs: [{ name: 'result', type: 'object', description: 'Function 执行返回值' }]
		},
		{
			id: 'node-skill-call',
			type: 'skill_call',
			label: 'Skill Call',
			description: '调用 openwebui Skill',
			icon: 'award',
			color: '#059669',
			category: 'tools',
			config: { extension_id: '', input_mapping: {}, output_schema: [] },
			ports: [
				{ id: 'in', name: 'input', direction: 'input' },
				{ id: 'out', name: 'output', direction: 'output' }
			],
			outputs: [{ name: 'result', type: 'object', description: 'Skill 执行返回值' }]
		},
		{
			id: 'node-mcp-call',
			type: 'mcp_call',
			label: 'MCP Call',
			description: '调用 MCP server 提供的 tool',
			icon: 'plug',
			color: '#7c3aed',
			category: 'tools',
			config: {
				server_id: '',
				extension_id: '',
				input_mapping: {},
				output_schema: []
			},
			ports: [
				{ id: 'in', name: 'input', direction: 'input' },
				{ id: 'out', name: 'output', direction: 'output' }
			],
			outputs: [{ name: 'result', type: 'object', description: 'MCP tool 调用返回值' }]
		},
		{
			id: 'node-human-input',
			type: 'human_input',
			label: 'Human Input',
			description: '暂停工作流并向用户请求输入/确认（human-in-the-loop）',
			icon: 'hand',
			color: '#f59e0b',
			category: 'tools',
			config: {
				prompt: '',
				fields: [],
				output_variable: 'human_input_result'
			},
			ports: [
				{ id: 'in', name: 'input', direction: 'input' },
				{ id: 'out', name: 'output', direction: 'output' }
			],
			outputs: [
				{ name: 'response', type: 'object', description: '用户提交的表单响应（变量名取自 config.output_variable）' }
			]
		}
		]
	},
	{
		id: 'pm',
		label: 'PM工作台',
		icon: 'briefcase',
		nodes: [
			{
				id: 'node-pm-prd', type: 'pm_module', label: 'PRD文档', description: 'Read/write PRD entries',
				icon: 'file-text', color: '#6366f1', category: 'pm',
				config: { module_type: 'prd', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-requirement', type: 'pm_module', label: '需求管理', description: 'Read/write requirement entries',
				icon: 'list-checks', color: '#6366f1', category: 'pm',
				config: { module_type: 'requirement', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-roadmap', type: 'pm_module', label: '产品路线图', description: 'Read/write roadmap entries',
				icon: 'map', color: '#6366f1', category: 'pm',
				config: { module_type: 'roadmap', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-parameter', type: 'pm_module', label: '参数配置', description: 'Read/write parameter entries',
				icon: 'settings', color: '#6366f1', category: 'pm',
				config: { module_type: 'parameter', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-architecture', type: 'pm_module', label: '产品架构', description: 'Read/write architecture entries',
				icon: 'layout', color: '#6366f1', category: 'pm',
				config: { module_type: 'architecture', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-prototype', type: 'pm_module', label: '原型/UI设计', description: 'Read/write prototype entries',
				icon: 'figma', color: '#6366f1', category: 'pm',
				config: { module_type: 'prototype', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-competitor', type: 'pm_module', label: '竞品分析', description: 'Read/write competitor entries',
				icon: 'telescope', color: '#6366f1', category: 'pm',
				config: { module_type: 'competitor', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-spec', type: 'pm_module', label: 'SPEC规范', description: 'Read/write spec entries',
				icon: 'book', color: '#6366f1', category: 'pm',
				config: { module_type: 'spec', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-flowchart', type: 'pm_module', label: '流程图', description: 'Read/write flowchart entries',
				icon: 'git-branch', color: '#6366f1', category: 'pm',
				config: { module_type: 'flowchart', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-schedule', type: 'pm_module', label: '项目排期', description: 'Read/write schedule entries',
				icon: 'calendar', color: '#6366f1', category: 'pm',
				config: { module_type: 'schedule', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-testcase', type: 'pm_module', label: '测试用例', description: 'Read/write testcase entries',
				icon: 'check-square', color: '#6366f1', category: 'pm',
				config: { module_type: 'testcase', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-risk', type: 'pm_module', label: '风险分析', description: 'Read/write risk entries',
				icon: 'alert-triangle', color: '#6366f1', category: 'pm',
				config: { module_type: 'risk', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-meeting', type: 'pm_module', label: '会议纪要', description: 'Read/write meeting entries',
				icon: 'users', color: '#6366f1', category: 'pm',
				config: { module_type: 'meeting', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-acceptance', type: 'pm_module', label: '验收报告', description: 'Read/write acceptance entries',
				icon: 'clipboard-check', color: '#6366f1', category: 'pm',
				config: { module_type: 'acceptance', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-faq', type: 'pm_module', label: 'FAQ', description: 'Read/write FAQ entries',
				icon: 'help-circle', color: '#6366f1', category: 'pm',
				config: { module_type: 'faq', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			},
			{
				id: 'node-pm-requirement-boundary', type: 'pm_module', label: '需求边界', description: 'Read/write requirement-boundary entries',
				icon: 'box', color: '#6366f1', category: 'pm',
				config: { module_type: 'requirement-boundary', action: 'read', project_id: '', entry_id: '', filter: {}, data: {} },
				ports: [
					{ id: 'in', name: 'input', direction: 'input' },
					{ id: 'out', name: 'output', direction: 'output' }
				],
				outputs: [
					{ name: 'entries', type: 'array', description: '查询到的条目列表' },
					{ name: 'count', type: 'number', description: '条目数量' }
				]
			}
		]
	}
];

// ===== Canvas Events =====

export interface CanvasDragEvent {
	nodeType: NodeType;
	position: Point;
}

export interface NodeSelectEvent {
	nodeId: string | null;
}

export interface NodeMoveEvent {
	nodeId: string;
	position: Point;
}

// ===== Utility Types =====

export type WorkflowStatus = 'draft' | 'published' | 'archived';

export interface WorkflowMetadata {
	id: string;
	name: string;
	description?: string;
	version: string;
	status: WorkflowStatus;
	createdAt: number;
	updatedAt: number;
}
