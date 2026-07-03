import {
	agentToolCreateEntry,
	agentToolUpdateEntry,
	agentToolCreateRelation,
	agentToolListEntries,
	agentToolGetEntry
} from '$lib/apis/pm/index';
import type { AgentAction, ModuleType } from '$lib/apis/pm/types';

// ============================================================================
// PM Agent Tool Registry
// Generic tool functions that the Agent can call to interact with PM data
// ============================================================================

export interface ToolResult {
	success: boolean;
	data?: unknown;
	error?: string;
}

export interface ToolContext {
	token: string;
	projectId: string;
	moduleType?: string;
	entryId?: string;
}

// Tool function type
export type ToolFunction = (ctx: ToolContext, payload: Record<string, unknown>) => Promise<ToolResult>;

// Tool registry
const toolRegistry: Record<string, ToolFunction> = {
	'pm.entry.create': async (ctx, payload) => {
		try {
			const result = await agentToolCreateEntry(ctx.token, {
				project_id: ctx.projectId,
				module_type: payload.module_type || ctx.moduleType,
				title: payload.title,
				content: payload.content,
				data: payload.data,
				status: payload.status || 'draft',
				priority: payload.priority,
			});
			return { success: true, data: result };
		} catch (err) {
			return { success: false, error: err instanceof Error ? err.message : String(err) };
		}
	},

	'pm.entry.update': async (ctx, payload) => {
		try {
			const result = await agentToolUpdateEntry(ctx.token, {
				entry_id: payload.entry_id || ctx.entryId,
				title: payload.title,
				content: payload.content,
				data: payload.data,
				status: payload.status,
				priority: payload.priority,
			});
			return { success: true, data: result };
		} catch (err) {
			return { success: false, error: err instanceof Error ? err.message : String(err) };
		}
	},

	'pm.relation.create': async (ctx, payload) => {
		try {
			const result = await agentToolCreateRelation(ctx.token, {
				project_id: ctx.projectId,
				entity_a_id: payload.entity_a_id,
				entity_b_id: payload.entity_b_id,
				relation_type: payload.relation_type || 'references',
				confidence: payload.confidence || 100,
			});
			return { success: true, data: result };
		} catch (err) {
			return { success: false, error: err instanceof Error ? err.message : String(err) };
		}
	},

	'pm.entry.list': async (ctx, payload) => {
		try {
			const result = await agentToolListEntries(
				ctx.token,
				ctx.projectId,
				payload.module_type as string || ctx.moduleType
			);
			return { success: true, data: result };
		} catch (err) {
			return { success: false, error: err instanceof Error ? err.message : String(err) };
		}
	},

	'pm.entry.get': async (ctx, payload) => {
		try {
			const result = await agentToolGetEntry(
				ctx.token,
				payload.entry_id as string || ctx.entryId || ''
			);
			return { success: true, data: result };
		} catch (err) {
			return { success: false, error: err instanceof Error ? err.message : String(err) };
		}
	},
};

// ============================================================================
// Skill Registry
// Maps skill IDs to their tool capabilities
// ============================================================================

export interface SkillConfig {
	id: string;
	name: string;
	description: string;
	icon: string;
	tools: string[];
	systemPrompt: string;
}

export const skillRegistry: SkillConfig[] = [
	{
		id: 'prd-generation',
		name: 'PRD 生成',
		description: '根据需求生成 PRD 文档大纲和内容',
		icon: 'document',
		tools: ['pm.entry.create', 'pm.entry.update'],
		systemPrompt: `你是 PRD 生成专家。根据用户提供的需求信息，生成结构化的 PRD 文档。
请按照以下结构生成：
1. 概述 - 产品定位和核心价值
2. 背景 - 市场背景和用户需求
3. 目标 - 产品目标和成功指标
4. 功能需求 - 详细功能描述（按优先级排序）
5. 非功能需求 - 性能、安全、体验要求
6. 附录 - 术语表和参考资料

生成后，用 action 块标记可创建的条目。`
	},
	{
		id: 'requirement-analysis',
		name: '需求分析',
		description: '分析需求分类、优先级和潜在冲突',
		icon: 'search',
		tools: ['pm.entry.list', 'pm.entry.get', 'pm.entry.update'],
		systemPrompt: `你是需求分析专家。分析项目中的需求条目，给出：
- 分类建议（功能/性能/安全/体验）
- 优先级建议（P0-P3）
- 潜在冲突和遗漏
- 关联关系建议`
	},
	{
		id: 'competitor-research',
		name: '竞品调研',
		description: '竞品对比分析和维度评分',
		icon: 'chart',
		tools: ['pm.entry.create', 'pm.entry.list'],
		systemPrompt: `你是竞品分析专家。根据用户提供的竞品信息，生成对比矩阵。
分析维度包括：功能、性能、价格、用户体验、技术架构等。
给出评分（0-100）和分析结论。`
	},
	{
		id: 'prototype-check',
		name: '原型走查',
		description: 'UI/原型走查检查和问题发现',
		icon: 'eye',
		tools: ['pm.entry.get', 'pm.entry.update'],
		systemPrompt: `你是 UI/UX 走查专家。检查原型设计，发现潜在问题：
- 交互流程是否完整
- 信息架构是否合理
- 视觉一致性
- 可访问性
- 边界情况处理`
	},
	{
		id: 'parameter-extract',
		name: '参数提取',
		description: '从文档中提取关键参数和配置项',
		icon: 'code',
		tools: ['pm.entry.get', 'pm.entry.create'],
		systemPrompt: `你是参数提取专家。从 PRD 或需求文档中提取关键参数：
- 参数名/Key
- 参数类型（输入/输出/配置）
- 数据类型
- 默认值
- 所属模块/功能
- 说明`
	},
	{
		id: 'testcase-generate',
		name: '测试用例生成',
		description: '根据需求生成测试用例',
		icon: 'check',
		tools: ['pm.entry.list', 'pm.entry.get', 'pm.entry.create'],
		systemPrompt: `你是测试用例生成专家。根据需求生成全面的测试用例：
- 功能测试用例（正常路径）
- 边界测试用例（极限值）
- 异常测试用例（错误处理）
- 性能测试用例（负载/压力）
每个用例包含：场景、前置条件、步骤、输入数据、预期结果。`
	},
	{
		id: 'version-compare',
		name: '版本对比',
		description: '对比不同版本的差异',
		icon: 'diff',
		tools: ['pm.entry.get', 'pm.entry.list'],
		systemPrompt: `你是版本对比专家。分析不同版本之间的差异，给出：
- 新增内容
- 修改内容
- 删除内容
- 影响范围评估
- 建议操作`
	},
	{
		id: 'relation-suggest',
		name: '关联建议',
		description: 'AI 建议条目间的关联关系',
		icon: 'link',
		tools: ['pm.entry.list', 'pm.relation.create'],
		systemPrompt: `你是关系分析专家。基于项目中的条目，分析可能的关联关系：
- 依赖关系（A 依赖 B）
- 引用关系（A 引用 B）
- 派生关系（A 派生自 B）
- 冲突关系（A 与 B 冲突）
给出关联建议和置信度评分。`
	},
	{
		id: 'workflow-suggest',
		name: '流程建议',
		description: '工作流步骤和下一步建议',
		icon: 'flow',
		tools: ['pm.entry.list'],
		systemPrompt: `你是项目管理专家。基于当前项目状态，建议下一步操作：
- 识别缺失的模块/条目
- 建议优先级排序
- 识别阻塞项
- 建议资源分配`
	},
];

// ============================================================================
// Tool Execution
// ============================================================================

export async function executeAgentAction(
	action: AgentAction,
	ctx: ToolContext
): Promise<ToolResult> {
	const toolFn = toolRegistry[action.type];
	if (!toolFn) {
		return { success: false, error: `Unknown tool type: ${action.type}` };
	}
	return toolFn(ctx, action.payload as Record<string, unknown>);
}

export function getSkillConfig(skillId: string): SkillConfig | undefined {
	return skillRegistry.find(s => s.id === skillId);
}

export function getAvailableSkills(): SkillConfig[] {
	return skillRegistry;
}

export function getToolRegistry(): Record<string, ToolFunction> {
	return { ...toolRegistry };
}