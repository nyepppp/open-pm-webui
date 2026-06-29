import type { FieldConfig } from '$lib/apis/pm/types';

// ============================================================================
// Module Field Configurations
// Each module defines its own form fields for the structured form editor
// ============================================================================

export const prdFields: FieldConfig[] = [
	{ name: 'title', label: '标题', type: 'text', required: true, placeholder: '输入PRD标题' },
	{ name: 'version', label: '版本', type: 'text', required: true, placeholder: '如：v1.0' },
	{ name: 'status', label: '状态', type: 'select', required: true, options: ['草稿', '评审中', '已批准', '已归档'] },
	{ name: 'priority', label: '优先级', type: 'select', options: ['P0-紧急', 'P1-高', 'P2-中', 'P3-低'] }
];

export const requirementFields: FieldConfig[] = [
	{ name: 'title', label: '需求标题', type: 'text', required: true, placeholder: '输入需求标题' },
	{ name: 'source', label: '来源', type: 'select', options: ['手动录入', 'Excel导入', 'Agent提取'] },
	{ name: 'category', label: '分类', type: 'text', placeholder: '如：功能需求、性能需求' },
	{ name: 'tags', label: '标签', type: 'text', placeholder: '用逗号分隔多个标签' },
	{ name: 'userRole', label: '用户角色', type: 'text', placeholder: '目标用户角色' },
	{ name: 'expectedBenefit', label: '预期收益', type: 'textarea', placeholder: '描述该需求带来的价值' }
];

export const parameterFields: FieldConfig[] = [
	{ name: 'key', label: '参数名', type: 'text', required: true, placeholder: '参数标识符' },
	{ name: 'moduleId', label: '所属模块', type: 'text', placeholder: '关联的模块ID' },
	{ name: 'featureId', label: '功能ID', type: 'text', placeholder: '关联的功能ID' },
	{ name: 'paramType', label: '参数类型', type: 'select', required: true, options: ['输入参数', '输出参数', '配置参数'] },
	{ name: 'dataType', label: '数据类型', type: 'select', required: true, options: ['string', 'number', 'boolean', 'object', 'array'] },
	{ name: 'required', label: '是否必填', type: 'select', options: ['是', '否'] },
	{ name: 'defaultValue', label: '默认值', type: 'text', placeholder: '默认值' },
	{ name: 'description', label: '说明', type: 'textarea', placeholder: '参数用途说明' }
];

export const testcaseFields: FieldConfig[] = [
	{ name: 'title', label: '用例标题', type: 'text', required: true, placeholder: '输入测试用例标题' },
	{ name: 'scenario', label: '测试场景', type: 'textarea', required: true, placeholder: '描述测试场景' },
	{ name: 'precondition', label: '前置条件', type: 'textarea', placeholder: '执行测试前需要满足的条件' },
	{ name: 'steps', label: '测试步骤', type: 'textarea', required: true, placeholder: '详细描述测试步骤' },
	{ name: 'expectedResult', label: '预期结果', type: 'textarea', required: true, placeholder: '预期的测试结果' },
	{ name: 'caseType', label: '用例类型', type: 'select', required: true, options: ['功能测试', '边界测试', '异常测试', '性能测试'] },
	{ name: 'requirementId', label: '关联需求', type: 'text', placeholder: '关联的需求ID' },
	{ name: 'parameterId', label: '关联参数', type: 'text', placeholder: '关联的参数ID' }
];

export const riskFields: FieldConfig[] = [
	{ name: 'title', label: '风险标题', type: 'text', required: true, placeholder: '输入风险标题' },
	{ name: 'probability', label: '风险等级', type: 'select', required: true, options: ['高', '中', '低'] },
	{ name: 'impactScope', label: '影响范围', type: 'textarea', placeholder: '描述风险的影响范围' },
	{ name: 'owner', label: '负责人', type: 'text', placeholder: '风险负责人' },
	{ name: 'measures', label: '应对措施', type: 'textarea', placeholder: '描述风险应对措施' },
	{ name: 'deadline', label: '截止日期', type: 'date' }
];

export const competitorFields: FieldConfig[] = [
	{ name: 'name', label: '竞品名称', type: 'text', required: true, placeholder: '输入竞品名称' },
	{ name: 'url', label: '官网链接', type: 'text', placeholder: 'https://...' },
	{ name: 'description', label: '描述', type: 'textarea', placeholder: '竞品描述' }
];

export const roadmapFields: FieldConfig[] = [
	{ name: 'title', label: '里程碑名称', type: 'text', required: true, placeholder: '输入里程碑名称' },
	{ name: 'layout', label: '布局模式', type: 'select', options: ['层级树状', '径向', '自由布局'] }
];

export const meetingFields: FieldConfig[] = [
	{ name: 'title', label: '会议主题', type: 'text', required: true, placeholder: '输入会议主题' },
	{ name: 'participants', label: '参会人员', type: 'text', placeholder: '用逗号分隔多个参会人' },
	{ name: 'meetingDate', label: '会议日期', type: 'date' },
	{ name: 'conclusions', label: '会议结论', type: 'textarea', placeholder: '会议达成的结论' }
];

export const acceptanceFields: FieldConfig[] = [
	{ name: 'title', label: '验收项', type: 'text', required: true, placeholder: '输入验收项名称' },
	{ name: 'scope', label: '验收范围', type: 'textarea', placeholder: '描述验收范围' },
	{ name: 'result', label: '验收结果', type: 'select', options: ['通过', '不通过', '部分通过'] }
];

export const faqFields: FieldConfig[] = [
	{ name: 'question', label: '问题', type: 'textarea', required: true, placeholder: '输入常见问题' },
	{ name: 'answer', label: '答案', type: 'textarea', required: true, placeholder: '输入问题答案' },
	{ name: 'audience', label: '受众', type: 'text', placeholder: '目标受众' },
	{ name: 'relatedFeatures', label: '相关功能', type: 'text', placeholder: '用逗号分隔多个功能' }
];

export const productArchitectureFields: FieldConfig[] = [
	{ name: 'title', label: '架构节点', type: 'text', required: true, placeholder: '输入节点名称' },
	{ name: 'autoExtracted', label: '自动提取', type: 'select', options: ['是', '否'] }
];

// ============================================================================
// Editor Type Mapping
// Maps each module to its editor type
// ============================================================================

export type EditorType = 'rich' | 'form' | 'mixed' | 'mindmap';

export const moduleEditorTypes: Record<string, EditorType> = {
	prd: 'rich',
	requirement: 'form',
	parameter: 'form',
	testcase: 'form',
	risk: 'mixed',
	competitor: 'rich',
	roadmap: 'mindmap',
	meeting: 'rich',
	acceptance: 'form',
	faq: 'rich',
	'product-architecture': 'mindmap'
};

export function getModuleFields(moduleType: string): FieldConfig[] {
	switch (moduleType) {
		case 'prd': return prdFields;
		case 'requirement': return requirementFields;
		case 'parameter': return parameterFields;
		case 'testcase': return testcaseFields;
		case 'risk': return riskFields;
		case 'competitor': return competitorFields;
		case 'roadmap': return roadmapFields;
		case 'meeting': return meetingFields;
		case 'acceptance': return acceptanceFields;
		case 'faq': return faqFields;
		case 'product-architecture': return productArchitectureFields;
		default: return [];
	}
}
