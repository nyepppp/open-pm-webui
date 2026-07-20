/**
 * Node Type Definitions and Registry
 *
 * Defines all available workflow node types and their configurations.
 */

export interface NodeParameter {
	id: string;
	name: string;
	type: 'text' | 'number' | 'boolean' | 'select' | 'file' | 'reference' | 'json' | 'textarea';
	required: boolean;
	defaultValue?: any;
	options?: { label: string; value: string }[];
	description?: string;
	validationRules?: string[];
	placeholder?: string;
}

export interface NodeTypeDefinition {
	type: string;
	label: string;
	category: string;
	icon: string;
	color: string;
	borderColor: string;
	backgroundColor: string;
	description: string;
	parameters: NodeParameter[];
	inputCount: number;
	outputCount: number;
	maxInputs: number;
	maxOutputs: number;
	allowMultipleInputs: boolean;
	allowMultipleOutputs: boolean;
	isConfigurable: boolean;
}

export const NODE_CATEGORIES = {
	BASIC: '基础节点',
	AGENT: 'Agent 节点',
	DATA: '数据处理',
	LOGIC: '逻辑控制',
	INTEGRATION: '集成',
	CUSTOM: '自定义'
} as const;

export const NODE_TYPES: Record<string, NodeTypeDefinition> = {
	start: {
		type: 'start',
		label: '开始',
		category: NODE_CATEGORIES.BASIC,
		icon: 'Play',
		color: '#4CAF50',
		borderColor: '#4CAF50',
		backgroundColor: '#E8F5E9',
		description: '工作流的起始节点',
		parameters: [
			{
				id: 'input_schema',
				name: '输入模式',
				type: 'json',
				required: false,
				defaultValue: {},
				description: '定义期望的输入数据结构'
			}
		],
		inputCount: 0,
		outputCount: 1,
		maxInputs: 0,
		maxOutputs: 1,
		allowMultipleInputs: false,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	end: {
		type: 'end',
		label: '结束',
		category: NODE_CATEGORIES.BASIC,
		icon: 'Square',
		color: '#F44336',
		borderColor: '#F44336',
		backgroundColor: '#FFEBEE',
		description: '工作流的结束节点',
		parameters: [
			{
				id: 'output_schema',
				name: '输出模式',
				type: 'json',
				required: false,
				defaultValue: {},
				description: '定义输出数据结构'
			}
		],
		inputCount: 1,
		outputCount: 0,
		maxInputs: 1,
		maxOutputs: 0,
		allowMultipleInputs: true,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	llm_call: {
		type: 'llm_call',
		label: 'LLM 调用',
		category: NODE_CATEGORIES.AGENT,
		icon: 'Brain',
		color: '#2196F3',
		borderColor: '#2196F3',
		backgroundColor: '#E3F2FD',
		description: '调用大语言模型进行推理',
		parameters: [
			{
				id: 'model',
				name: '模型',
				type: 'select',
				required: true,
				defaultValue: 'gpt-4',
				options: [
					{ label: 'GPT-4', value: 'gpt-4' },
					{ label: 'GPT-3.5', value: 'gpt-3.5-turbo' },
					{ label: 'Claude', value: 'claude' },
					{ label: 'Gemini', value: 'gemini' }
				],
				description: '选择要使用的LLM模型'
			},
			{
				id: 'temperature',
				name: '温度',
				type: 'number',
				required: false,
				defaultValue: 0.7,
				validationRules: ['min:0', 'max:2'],
				description: '控制输出的随机性 (0-2)'
			},
			{
				id: 'max_tokens',
				name: '最大令牌数',
				type: 'number',
				required: false,
				defaultValue: 2048,
				validationRules: ['min:1', 'max:8192'],
				description: '生成文本的最大长度'
			},
			{
				id: 'system_prompt',
				name: '系统提示词',
				type: 'textarea',
				required: false,
				defaultValue: '',
				placeholder: '你是一个有帮助的助手...',
				description: '系统级别的提示词'
			},
			{
				id: 'user_prompt',
				name: '用户提示词',
				type: 'textarea',
				required: true,
				defaultValue: '',
				placeholder: '请输入您的问题...',
				description: '用户输入的提示词模板'
			}
		],
		inputCount: 1,
		outputCount: 1,
		maxInputs: 1,
		maxOutputs: 1,
		allowMultipleInputs: false,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	agent_call: {
		type: 'agent_call',
		label: 'Agent 调用',
		category: NODE_CATEGORIES.AGENT,
		icon: 'Bot',
		color: '#9C27B0',
		borderColor: '#9C27B0',
		backgroundColor: '#F3E5F5',
		description: '调用自定义Agent执行任务',
		parameters: [
			{
				id: 'agent_id',
				name: 'Agent ID',
				type: 'text',
				required: true,
				defaultValue: '',
				placeholder: '输入Agent ID',
				description: '要调用的Agent标识符'
			},
			{
				id: 'task',
				name: '任务描述',
				type: 'textarea',
				required: true,
				defaultValue: '',
				placeholder: '描述Agent需要执行的任务...',
				description: 'Agent需要完成的任务'
			},
			{
				id: 'tools',
				name: '可用工具',
				type: 'json',
				required: false,
				defaultValue: [],
				description: 'Agent可用的工具列表'
			}
		],
		inputCount: 1,
		outputCount: 1,
		maxInputs: 1,
		maxOutputs: 1,
		allowMultipleInputs: false,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	data_transform: {
		type: 'data_transform',
		label: '数据转换',
		category: NODE_CATEGORIES.DATA,
		icon: 'ArrowLeftRight',
		color: '#FF9800',
		borderColor: '#FF9800',
		backgroundColor: '#FFF3E0',
		description: '转换和映射数据格式',
		parameters: [
			{
				id: 'transformation_type',
				name: '转换类型',
				type: 'select',
				required: true,
				defaultValue: 'map',
				options: [
					{ label: '映射 (Map)', value: 'map' },
					{ label: '过滤 (Filter)', value: 'filter' },
					{ label: '聚合 (Aggregate)', value: 'aggregate' },
					{ label: '排序 (Sort)', value: 'sort' },
					{ label: '自定义 (Custom)', value: 'custom' }
				],
				description: '选择数据转换的类型'
			},
			{
				id: 'config',
				name: '转换配置',
				type: 'json',
				required: false,
				defaultValue: {},
				description: '转换的具体配置参数'
			}
		],
		inputCount: 1,
		outputCount: 1,
		maxInputs: 1,
		maxOutputs: 1,
		allowMultipleInputs: false,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	condition: {
		type: 'condition',
		label: '条件分支',
		category: NODE_CATEGORIES.LOGIC,
		icon: 'GitBranch',
		color: '#795548',
		borderColor: '#795548',
		backgroundColor: '#EFEBE9',
		description: '根据条件决定执行路径',
		parameters: [
			{
				id: 'condition_expression',
				name: '条件表达式',
				type: 'textarea',
				required: true,
				defaultValue: '',
				placeholder: '例如: input.score > 0.5',
				description: 'JavaScript条件表达式，返回true或false'
			},
			{
				id: 'true_label',
				name: 'True分支标签',
				type: 'text',
				required: false,
				defaultValue: '是',
				description: '条件为真时的分支标签'
			},
			{
				id: 'false_label',
				name: 'False分支标签',
				type: 'text',
				required: false,
				defaultValue: '否',
				description: '条件为假时的分支标签'
			}
		],
		inputCount: 1,
		outputCount: 2,
		maxInputs: 1,
		maxOutputs: 2,
		allowMultipleInputs: false,
		allowMultipleOutputs: true,
		isConfigurable: true
	},
	loop: {
		type: 'loop',
		label: '循环',
		category: NODE_CATEGORIES.LOGIC,
		icon: 'RotateCcw',
		color: '#607D8B',
		borderColor: '#607D8B',
		backgroundColor: '#ECEFF1',
		description: '循环执行直到条件满足',
		parameters: [
			{
				id: 'loop_type',
				name: '循环类型',
				type: 'select',
				required: true,
				defaultValue: 'while',
				options: [
					{ label: 'While 循环', value: 'while' },
					{ label: 'For 循环', value: 'for' },
					{ label: 'Do-While 循环', value: 'do_while' }
				],
				description: '选择循环类型'
			},
			{
				id: 'condition',
				name: '循环条件',
				type: 'textarea',
				required: true,
				defaultValue: '',
				placeholder: '例如: i < 10',
				description: '循环继续的条件表达式'
			},
			{
				id: 'max_iterations',
				name: '最大迭代次数',
				type: 'number',
				required: false,
				defaultValue: 100,
				validationRules: ['min:1', 'max:10000'],
				description: '防止无限循环的最大次数'
			}
		],
		inputCount: 1,
		outputCount: 2,
		maxInputs: 1,
		maxOutputs: 2,
		allowMultipleInputs: false,
		allowMultipleOutputs: true,
		isConfigurable: true
	},
	parallel: {
		type: 'parallel',
		label: '并行执行',
		category: NODE_CATEGORIES.LOGIC,
		icon: 'Split',
		color: '#00BCD4',
		borderColor: '#00BCD4',
		backgroundColor: '#E0F7FA',
		description: '并行执行多个分支',
		parameters: [
			{
				id: 'branches',
				name: '分支数量',
				type: 'number',
				required: true,
				defaultValue: 2,
				validationRules: ['min:2', 'max:10'],
				description: '并行执行的分支数量'
			}
		],
		inputCount: 1,
		outputCount: 2,
		maxInputs: 1,
		maxOutputs: 10,
		allowMultipleInputs: false,
		allowMultipleOutputs: true,
		isConfigurable: true
	},
	merge: {
		type: 'merge',
		label: '合并',
		category: NODE_CATEGORIES.LOGIC,
		icon: 'Merge',
		color: '#009688',
		borderColor: '#009688',
		backgroundColor: '#E0F2F1',
		description: '合并多个分支的结果',
		parameters: [
			{
				id: 'merge_strategy',
				name: '合并策略',
				type: 'select',
				required: true,
				defaultValue: 'all',
				options: [
					{ label: '等待全部', value: 'all' },
					{ label: '等待任意', value: 'any' },
					{ label: '优先第一个', value: 'first' }
				],
				description: '选择合并策略'
			}
		],
		inputCount: 2,
		outputCount: 1,
		maxInputs: 10,
		maxOutputs: 1,
		allowMultipleInputs: true,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	webhook: {
		type: 'webhook',
		label: 'Webhook',
		category: NODE_CATEGORIES.INTEGRATION,
		icon: 'Webhook',
		color: '#FF5722',
		borderColor: '#FF5722',
		backgroundColor: '#FBE9E7',
		description: '发送HTTP请求到外部服务',
		parameters: [
			{
				id: 'url',
				name: 'URL',
				type: 'text',
				required: true,
				defaultValue: '',
				placeholder: 'https://api.example.com/webhook',
				description: '目标URL地址'
			},
			{
				id: 'method',
				name: '请求方法',
				type: 'select',
				required: true,
				defaultValue: 'POST',
				options: [
					{ label: 'GET', value: 'GET' },
					{ label: 'POST', value: 'POST' },
					{ label: 'PUT', value: 'PUT' },
					{ label: 'DELETE', value: 'DELETE' },
					{ label: 'PATCH', value: 'PATCH' }
				],
				description: 'HTTP请求方法'
			},
			{
				id: 'headers',
				name: '请求头',
				type: 'json',
				required: false,
				defaultValue: {},
				description: '自定义HTTP请求头'
			},
			{
				id: 'timeout',
				name: '超时时间(秒)',
				type: 'number',
				required: false,
				defaultValue: 30,
				validationRules: ['min:1', 'max:300'],
				description: '请求超时时间'
			}
		],
		inputCount: 1,
		outputCount: 1,
		maxInputs: 1,
		maxOutputs: 1,
		allowMultipleInputs: false,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	pm_module: {
		type: 'pm_module',
		label: 'PM 模块',
		category: NODE_CATEGORIES.INTEGRATION,
		icon: 'Briefcase',
		color: '#3F51B5',
		borderColor: '#3F51B5',
		backgroundColor: '#E8EAF6',
		description: '调用PM工作台的模块功能',
		parameters: [
			{
				id: 'module_type',
				name: '模块类型',
				type: 'select',
				required: true,
				defaultValue: 'requirement',
				options: [
					{ label: '需求', value: 'requirement' },
					{ label: '模块', value: 'module' },
					{ label: '功能', value: 'feature' },
					{ label: '参数', value: 'parameter' }
				],
				description: 'PM模块类型'
			},
			{
				id: 'action',
				name: '操作',
				type: 'select',
				required: true,
				defaultValue: 'create',
				options: [
					{ label: '创建', value: 'create' },
					{ label: '读取', value: 'read' },
					{ label: '更新', value: 'update' },
					{ label: '删除', value: 'delete' }
				],
				description: '要执行的操作'
			}
		],
		inputCount: 1,
		outputCount: 1,
		maxInputs: 1,
		maxOutputs: 1,
		allowMultipleInputs: false,
		allowMultipleOutputs: false,
		isConfigurable: true
	},
	custom: {
		type: 'custom',
		label: '自定义',
		category: NODE_CATEGORIES.CUSTOM,
		icon: 'Code',
		color: '#757575',
		borderColor: '#757575',
		backgroundColor: '#F5F5F5',
		description: '自定义代码节点',
		parameters: [
			{
				id: 'code',
				name: '代码',
				type: 'textarea',
				required: true,
				defaultValue: '',
				placeholder: '// 输入自定义代码',
				description: '自定义执行代码 (JavaScript)'
			}
		],
		inputCount: 1,
		outputCount: 1,
		maxInputs: 1,
		maxOutputs: 1,
		allowMultipleInputs: false,
		allowMultipleOutputs: false,
		isConfigurable: true
	}
};

export function getNodeType(type: string): NodeTypeDefinition | undefined {
	return NODE_TYPES[type];
}

export function getAllNodeTypes(): NodeTypeDefinition[] {
	return Object.values(NODE_TYPES);
}

export function getNodeTypesByCategory(category: string): NodeTypeDefinition[] {
	return Object.values(NODE_TYPES).filter(node => node.category === category);
}

export function getNodeCategories(): string[] {
	return [...new Set(Object.values(NODE_TYPES).map(node => node.category))];
}

export function validateNodeConfig(type: string, config: Record<string, any>): { valid: boolean; errors: string[] } {
	const nodeType = getNodeType(type);
	if (!nodeType) {
		return { valid: false, errors: [`未知的节点类型: ${type}`] };
	}

	const errors: string[] = [];

	for (const param of nodeType.parameters) {
		if (param.required && (config[param.id] === undefined || config[param.id] === null || config[param.id] === '')) {
			errors.push(`参数 "${param.name}" 是必填项`);
		}

		if (config[param.id] !== undefined && config[param.id] !== null) {
			// Type validation
			switch (param.type) {
				case 'number':
					if (typeof config[param.id] !== 'number') {
						errors.push(`参数 "${param.name}" 必须是数字`);
					}
					break;
				case 'boolean':
					if (typeof config[param.id] !== 'boolean') {
						errors.push(`参数 "${param.name}" 必须是布尔值`);
					}
					break;
			}

			// Validation rules
			if (param.validationRules) {
				for (const rule of param.validationRules) {
					const [ruleType, ruleValue] = rule.split(':');
					switch (ruleType) {
						case 'min':
							if (config[param.id] < parseFloat(ruleValue)) {
								errors.push(`参数 "${param.name}" 不能小于 ${ruleValue}`);
							}
							break;
						case 'max':
							if (config[param.id] > parseFloat(ruleValue)) {
								errors.push(`参数 "${param.name}" 不能大于 ${ruleValue}`);
							}
							break;
					}
				}
			}
		}
	}

	return { valid: errors.length === 0, errors };
}
