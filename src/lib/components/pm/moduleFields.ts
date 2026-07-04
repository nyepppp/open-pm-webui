import type { FieldConfig } from '$lib/apis/pm/types';

// ============================================================================
// Module-specific field configurations for differentiated editors
// Each module defines its own fields for form/mixed editor mode
// ============================================================================

export const parameterFields: FieldConfig[] = [
	{ name: 'key', label: '参数名', type: 'text', required: true, placeholder: '参数标识符' },
	{ name: 'moduleName', label: '所属模块', type: 'combobox', dataSource: 'modules', placeholder: '选择或输入模块名' },
	{ name: 'featureName', label: '所属功能', type: 'combobox', dataSource: 'features', dependsOn: 'moduleName', placeholder: '选择或输入功能名' },
	{ name: 'paramType', label: '参数类型', type: 'select', required: true, options: ['输入参数', '输出参数', '配置参数'] },
	{ name: 'dataType', label: '数据类型', type: 'select', required: true, options: ['string', 'number', 'boolean', 'object', 'array'] },
	{ name: 'required', label: '是否必填', type: 'select', options: ['是', '否'] },
	{ name: 'defaultValue', label: '默认值', type: 'text', placeholder: '默认值' },
	{ name: 'description', label: '说明', type: 'textarea', placeholder: '参数用途说明' }
];

export const requirementFields: FieldConfig[] = [
	{ name: 'source', label: '来源', type: 'select', options: ['manual', 'excel', 'agent', 'prd'] },
	{ name: 'category', label: '分类', type: 'select', options: ['功能需求', '性能需求', '安全需求', '体验需求'] },
	{ name: 'userRole', label: '用户角色', type: 'text', placeholder: '目标用户角色' },
	{ name: 'expectedBenefit', label: '预期收益', type: 'textarea', placeholder: '预期业务价值' },
	{ name: 'relatedModules', label: '关联模块', type: 'multiselect', options: [] },
	{ name: 'tags', label: '标签', type: 'text', placeholder: '用逗号分隔多个标签' }
];

export const testcaseFields: FieldConfig[] = [
	{ name: 'scenario', label: '测试场景', type: 'textarea', required: true, placeholder: '描述测试场景' },
	{ name: 'precondition', label: '前置条件', type: 'textarea', placeholder: '执行测试前的准备条件' },
	{ name: 'steps', label: '测试步骤', type: 'textarea', required: true, placeholder: '详细测试步骤' },
	{ name: 'inputData', label: '输入数据', type: 'textarea', placeholder: '测试输入数据' },
	{ name: 'expectedResult', label: '预期结果', type: 'textarea', required: true, placeholder: '期望的输出结果' },
	{ name: 'caseType', label: '用例类型', type: 'select', required: true, options: ['functional', 'boundary', 'exception', 'performance'] },
	{ name: 'requirementId', label: '关联需求ID', type: 'text', placeholder: '关联的需求条目ID' },
	{ name: 'parameterId', label: '关联参数ID', type: 'text', placeholder: '关联的参数条目ID' }
];

export const riskFields: FieldConfig[] = [
	{ name: 'probability', label: '发生概率', type: 'select', required: true, options: ['high', 'medium', 'low'] },
	{ name: 'impactScope', label: '影响范围', type: 'textarea', required: true, placeholder: '风险影响的范围描述' },
	{ name: 'owner', label: '负责人', type: 'text', placeholder: '风险负责人' },
	{ name: 'measures', label: '应对措施', type: 'textarea', placeholder: '风险缓解和应对措施' },
	{ name: 'deadline', label: '解决期限', type: 'date', placeholder: 'YYYY-MM-DD' }
];

export const competitorFields: FieldConfig[] = [
	{ name: 'competitorUrl', label: '竞品URL', type: 'text', placeholder: 'https://...' },
	{ name: 'dimension', label: '分析维度', type: 'text', placeholder: '如：功能、性能、价格' },
	{ name: 'ourProduct', label: '我方产品', type: 'textarea', placeholder: '我方产品在该维度的表现' },
	{ name: 'competitorProduct', label: '竞品表现', type: 'textarea', placeholder: '竞品在该维度的表现' },
	{ name: 'analysis', label: '分析结论', type: 'textarea', placeholder: '对比分析结论' }
];

export const scheduleFields: FieldConfig[] = [
	{ name: 'assignee', label: '负责人', type: 'text', placeholder: '任务负责人' },
	{ name: 'startDate', label: '开始日期', type: 'date' },
	{ name: 'endDate', label: '结束日期', type: 'date' },
	{ name: 'progress', label: '进度(%)', type: 'number', validation: { min: 0, max: 100 } },
	{ name: 'isMilestone', label: '是否里程碑', type: 'select', options: ['是', '否'] }
];

export const acceptanceFields: FieldConfig[] = [
	{ name: 'requirementId', label: '关联需求', type: 'text', placeholder: '关联需求ID' },
	{ name: 'scope', label: '验收范围', type: 'textarea', placeholder: '本次验收的范围描述' },
	{ name: 'result', label: '验收结果', type: 'select', options: ['pass', 'fail', 'partial'] },
	{ name: 'remainingIssues', label: '遗留问题', type: 'textarea', placeholder: '未解决的遗留问题' }
];

export const faqFields: FieldConfig[] = [
	{ name: 'question', label: '问题', type: 'textarea', required: true, placeholder: '常见问题描述' },
	{ name: 'answer', label: '答案', type: 'textarea', required: true, placeholder: '问题的详细解答' },
	{ name: 'audience', label: '受众', type: 'text', placeholder: '目标受众，如：开发、测试、用户' },
	{ name: 'relatedFeatures', label: '关联功能', type: 'text', placeholder: '关联的功能模块' }
];

export const meetingFields: FieldConfig[] = [
	{ name: 'participants', label: '参会人员', type: 'text', placeholder: '用逗号分隔参会人员' },
	{ name: 'meetingDate', label: '会议日期', type: 'date' },
	{ name: 'conclusions', label: '会议结论', type: 'textarea', placeholder: '会议达成的结论' },
	{ name: 'actionItems', label: '待办事项', type: 'textarea', placeholder: 'JSON格式的待办事项数组' }
];

export const prototypeFields: FieldConfig[] = [
	{ name: 'protoType', label: '原型类型', type: 'select', options: ['web', 'mobile', 'desktop', 'other'] },
	{ name: 'annotations', label: '标注说明', type: 'textarea', placeholder: '原型标注和说明' },
	{ name: 'reviewStatus', label: '评审状态', type: 'select', options: ['pending', 'pass', 'fail'] }
];

export const roadmapFields: FieldConfig[] = [
	{ name: 'nodeType', label: '节点类型', type: 'select', options: ['feature', 'milestone', 'epic', 'task'] },
	{ name: 'nodeStatus', label: '节点状态', type: 'select', options: ['planned', 'in_progress', 'completed', 'delayed'] },
	{ name: 'startDate', label: '开始日期', type: 'date' },
	{ name: 'endDate', label: '结束日期', type: 'date' },
	{ name: 'dependencies', label: '依赖项', type: 'text', placeholder: '逗号分隔的依赖节点ID' }
];

export const productArchitectureFields: FieldConfig[] = [
	{ name: 'architectureType', label: '架构类型', type: 'select', options: ['frontend', 'backend', 'database', 'infrastructure', 'integration'] },
	{ name: 'techStack', label: '技术栈', type: 'text', placeholder: '使用的技术栈' },
	{ name: 'autoExtracted', label: '自动提取', type: 'select', options: ['是', '否'] }
];

export const requirementBoundaryFields: FieldConfig[] = [
	{ name: 'scenario', label: '场景', type: 'textarea', required: true, placeholder: '描述需求边界场景' },
	{ name: 'function', label: '功能', type: 'textarea', placeholder: '功能描述' },
	{ name: 'usage', label: '使用方式', type: 'textarea', placeholder: '使用方式说明' },
	{ name: 'expectedEffect', label: '预期效果', type: 'textarea', placeholder: '预期效果描述' },
	{ name: 'relatedRequirements', label: '关联需求', type: 'text', placeholder: '关联需求ID' },
	{ name: 'relatedParameters', label: '关联参数', type: 'text', placeholder: '关联参数ID' }
];

export const specFields: FieldConfig[] = [
	{ name: 'specCategory', label: 'SPEC分类', type: 'select', options: ['functional', 'prototype'] },
	{ name: 'relatedRequirements', label: '关联需求', type: 'text', placeholder: '关联需求ID列表' },
	{ name: 'relatedParameters', label: '关联参数', type: 'text', placeholder: '关联参数ID列表' }
];

// ============================================================================
// Module field registry - maps module type to its field configuration
// ============================================================================

export const moduleFieldRegistry: Record<string, FieldConfig[]> = {
	parameter: parameterFields,
	requirement: requirementFields,
	testcase: testcaseFields,
	risk: riskFields,
	competitor: competitorFields,
	schedule: scheduleFields,
	acceptance: acceptanceFields,
	faq: faqFields,
	meeting: meetingFields,
	prototype: prototypeFields,
	roadmap: roadmapFields,
	'product-architecture': productArchitectureFields,
	'requirement-boundary': requirementBoundaryFields,
	spec: specFields,
};

// ============================================================================
// Editor type mapping - determines which editor UI to render per module
// ============================================================================

export type ModuleEditorType = 'rich' | 'form' | 'mixed' | 'mindmap' | 'table';

export interface ModuleEditorConfig {
	editorType: ModuleEditorType;
	fields: FieldConfig[];
	label: string;
	icon: string;
	category: 'planning' | 'design' | 'execution' | 'review';
}

export const moduleEditorConfig: Record<string, ModuleEditorConfig> = {
	prd: {
		editorType: 'rich',
		fields: [],
		label: 'PRD 文档',
		icon: 'document',
		category: 'planning'
	},
	requirement: {
		editorType: 'table',
		fields: requirementFields,
		label: '需求管理',
		icon: 'list',
		category: 'planning'
	},
	parameter: {
		editorType: 'table',
		fields: parameterFields,
		label: '参数配置',
		icon: 'settings',
		category: 'design'
	},
	testcase: {
		editorType: 'table',
		fields: testcaseFields,
		label: '测试用例',
		icon: 'check',
		category: 'execution'
	},
	risk: {
		editorType: 'form',
		fields: riskFields,
		label: '风险分析',
		icon: 'alert',
		category: 'execution'
	},
	competitor: {
		editorType: 'form',
		fields: competitorFields,
		label: '竞品分析',
		icon: 'chart',
		category: 'design'
	},
	roadmap: {
		editorType: 'table',
		fields: roadmapFields,
		label: '产品路线图',
		icon: 'map',
		category: 'planning'
	},
	meeting: {
		editorType: 'mixed',
		fields: meetingFields,
		label: '会议纪要',
		icon: 'calendar',
		category: 'execution'
	},
	acceptance: {
		editorType: 'form',
		fields: acceptanceFields,
		label: '验收报告',
		icon: 'shield',
		category: 'review'
	},
	faq: {
		editorType: 'form',
		fields: faqFields,
		label: 'FAQ',
		icon: 'help',
		category: 'review'
	},
	'product-architecture': {
		editorType: 'mindmap',
		fields: productArchitectureFields,
		label: '产品架构',
		icon: 'diagram',
		category: 'design'
	},
	prototype: {
		editorType: 'mixed',
		fields: prototypeFields,
		label: '原型/UI设计',
		icon: 'image',
		category: 'design'
	},
	schedule: {
		editorType: 'table',
		fields: scheduleFields,
		label: '项目排期',
		icon: 'clock',
		category: 'execution'
	},
	'requirement-boundary': {
		editorType: 'form',
		fields: requirementBoundaryFields,
		label: '需求边界',
		icon: 'git-branch',
		category: 'planning'
	},
	spec: {
		editorType: 'rich',
		fields: specFields,
		label: 'SPEC规范',
		icon: 'document',
		category: 'review'
	}
};

export function getModuleFields(moduleType: string): FieldConfig[] {
	return moduleFieldRegistry[moduleType] || [];
}

export function getModuleEditorConfig(moduleType: string): ModuleEditorConfig {
	return moduleEditorConfig[moduleType] || {
		editorType: 'rich',
		fields: [],
		label: moduleType,
		icon: 'file',
		category: 'planning'
	};
}