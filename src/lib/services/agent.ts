import { WEBUI_API_BASE_URL } from '$lib/constants';
import type { AgentSuggestion } from '$lib/apis/pm/types';

// ============================================================================
// Types
// ============================================================================

export interface PMContext {
	projectId: string;
	projectName?: string;
	moduleType?: string;
	entryId?: string;
	entryTitle?: string;
	userId?: string;
}

export interface AgentResponse {
	message: string;
	intent: { skillId: string; confidence: number };
	actions?: AgentAction[];
	skillId?: string;
}

export interface AgentAction {
	id: string;
	type: string;
	label: string;
	description: string;
	payload: Record<string, unknown>;
	status: 'pending' | 'executed' | 'failed';
}

export interface SkillDefinition {
	id: string;
	name: string;
	description: string;
	icon: string;
	parameters: SkillParameter[];
	execute?: (params: unknown, context: PMContext) => Promise<SkillResult>;
}

export interface SkillParameter {
	name: string;
	type: 'string' | 'number' | 'boolean' | 'array' | 'object';
	required: boolean;
	description: string;
}

export interface SkillResult {
	success: boolean;
	data?: unknown;
	error?: string;
}

export interface Workflow {
	id: string;
	name: string;
	steps: WorkflowStep[];
}

export interface WorkflowStep {
	id: string;
	skillId: string;
	inputs: Record<string, unknown>;
	outputs: Record<string, unknown>;
	condition?: string;
}

export interface WorkflowResult {
	success: boolean;
	steps: { stepId: string; status: 'completed' | 'failed' | 'skipped'; result?: unknown }[];
	error?: string;
}

// ============================================================================
// PMAgentService
// ============================================================================

const PM_API_BASE = `${WEBUI_API_BASE_URL}/pm`;

function getHeaders(token: string = '') {
	return {
		Accept: 'application/json',
		'Content-Type': 'application/json',
		...(token && { authorization: `Bearer ${token}` })
	};
}

class PMAgentServiceClass {
	private skills: Map<string, SkillDefinition> = new Map();
	private token: string = '';

	constructor() {
		if (typeof localStorage !== 'undefined') {
			this.token = localStorage.token || '';
		}
	}

	// Send message to Agent with PM context
	async chat(message: string, context: PMContext): Promise<AgentResponse> {
		const response = await fetch(`${PM_API_BASE}/agent/chat`, {
			method: 'POST',
			headers: getHeaders(this.token),
			body: JSON.stringify({
				message,
				project_id: context.projectId,
				module_type: context.moduleType,
				entry_id: context.entryId,
				context: {
					projectName: context.projectName,
					entryTitle: context.entryTitle,
				}
			})
		});
		if (!response.ok) throw new Error(`Agent chat failed (${response.status})`);
		return response.json();
	}

	// Call specific skill
	async callSkill(skillId: string, data: unknown, context: PMContext): Promise<SkillResult> {
		const skill = this.skills.get(skillId);
		if (skill && skill.execute) {
			return skill.execute(data, context);
		}
		
		// Fallback: use backend skill API
		const response = await fetch(`${PM_API_BASE}/agent/skill/${skillId}`, {
			method: 'POST',
			headers: getHeaders(this.token),
			body: JSON.stringify({
				project_id: context.projectId,
				module_type: context.moduleType,
				entry_id: context.entryId,
				data
			})
		});
		if (!response.ok) throw new Error(`Skill call failed (${response.status})`);
		const result = await response.json();
		return { success: true, data: result };
	}

	// Register custom skill
	registerSkill(skill: SkillDefinition): void {
		this.skills.set(skill.id, skill);
	}

	// Get available skills
	async getSkills(): Promise<SkillDefinition[]> {
		const response = await fetch(`${PM_API_BASE}/agent/skills`, {
			method: 'GET',
			headers: getHeaders(this.token)
		});
		if (!response.ok) throw new Error('Failed to fetch skills');
		return response.json();
	}

	// Get local registered skills
	getLocalSkills(): SkillDefinition[] {
		return Array.from(this.skills.values());
	}
}

export const PMAgentService = new PMAgentServiceClass();

// ============================================================================
// PM Tool Functions
// ============================================================================

export async function pmCreateEntry(projectId: string, moduleType: string, data: unknown) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/entries`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify({ ...data, module_type: moduleType })
	});
	if (!response.ok) throw new Error('Failed to create entry');
	return response.json();
}

export async function pmUpdateEntry(entryId: string, data: unknown) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to update entry');
	return response.json();
}

export async function pmDeleteEntry(entryId: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete entry');
	return response.json();
}

export async function pmGetEntry(entryId: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to get entry');
	return response.json();
}

export async function pmListEntries(projectId: string, moduleType?: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const query = moduleType ? `?module_type=${moduleType}` : '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/entries${query}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to list entries');
	return response.json();
}

export async function pmCreateRelation(projectId: string, entityA: string, entityB: string, type: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/relations`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify({ entity_a_id: entityA, entity_b_id: entityB, relation_type: type })
	});
	if (!response.ok) throw new Error('Failed to create relation');
	return response.json();
}

export async function pmGetRelations(projectId: string, entityId?: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const query = entityId ? `?entity_id=${entityId}` : '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/relations${query}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to get relations');
	return response.json();
}

export async function pmDeleteRelation(relationId: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/relations/${relationId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete relation');
	return response.json();
}

export async function pmCreateVersion(projectId: string, data: unknown) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/versions`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create version');
	return response.json();
}

export async function pmGetVersions(projectId: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/versions`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to get versions');
	return response.json();
}

export async function pmCompareVersions(projectId: string, versionA: string, versionB: string) {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/versions/compare?versionA=${versionA}&versionB=${versionB}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to compare versions');
	return response.json();
}

// ============================================================================
// Workflow Execution
// ============================================================================

export async function executeWorkflow(workflow: Workflow, context: PMContext): Promise<WorkflowResult> {
	const results: WorkflowResult['steps'] = [];
	
	for (const step of workflow.steps) {
		// Check condition
		if (step.condition) {
			try {
				const conditionResult = eval(step.condition);
				if (!conditionResult) {
					results.push({ stepId: step.id, status: 'skipped' });
					continue;
				}
			} catch {
				results.push({ stepId: step.id, status: 'skipped' });
				continue;
			}
		}
		
		try {
			const result = await PMAgentService.callSkill(step.skillId, step.inputs, context);
			results.push({ stepId: step.id, status: result.success ? 'completed' : 'failed', result });
		} catch (error) {
			results.push({ stepId: step.id, status: 'failed', result: { error: String(error) } });
		}
	}
	
	const allCompleted = results.every(r => r.status === 'completed');
	return {
		success: allCompleted,
		steps: results
	};
}

// ============================================================================
// Skill Registry
// ============================================================================

export const SkillRegistry = {
	skills: new Map<string, SkillDefinition>(),
	
	register(skill: SkillDefinition): void {
		this.skills.set(skill.id, skill);
		PMAgentService.registerSkill(skill);
	},
	
	get(id: string): SkillDefinition | undefined {
		return this.skills.get(id);
	},
	
	getAll(): SkillDefinition[] {
		return Array.from(this.skills.values());
	},
	
	remove(id: string): void {
		this.skills.delete(id);
	}
};

// Register built-in skills
SkillRegistry.register({
	id: 'prd-generation',
	name: 'PRD 生成',
	description: '根据需求生成 PRD 文档大纲和内容',
	icon: 'document',
	parameters: [
		{ name: 'productName', type: 'string', required: true, description: '产品名称' },
		{ name: 'targetUsers', type: 'string', required: true, description: '目标用户群体' },
		{ name: 'features', type: 'array', required: true, description: '核心功能需求列表' }
	]
});

SkillRegistry.register({
	id: 'requirement-analysis',
	name: '需求分析',
	description: '分析需求分类、优先级和潜在冲突',
	icon: 'search',
	parameters: [
		{ name: 'requirements', type: 'array', required: true, description: '需求描述列表' }
	]
});

SkillRegistry.register({
	id: 'competitor-research',
	name: '竞品调研',
	description: '竞品对比分析和维度评分',
	icon: 'chart',
	parameters: [
		{ name: 'competitorName', type: 'string', required: true, description: '竞品名称' },
		{ name: 'dimensions', type: 'array', required: false, description: '对比维度' }
	]
});

SkillRegistry.register({
	id: 'parameter-extract',
	name: '参数提取',
	description: '从文档中提取关键参数和配置项',
	icon: 'code',
	parameters: [
		{ name: 'document', type: 'string', required: true, description: '文档内容或条目ID' }
	]
});

SkillRegistry.register({
	id: 'testcase-generate',
	name: '测试用例生成',
	description: '根据需求生成测试用例',
	icon: 'check',
	parameters: [
		{ name: 'feature', type: 'string', required: true, description: '功能描述' }
	]
});
