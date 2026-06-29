/**
 * Agent Analysis Service
 * Implements AI-assisted analysis for PM modules
 * T075: PRD completeness analysis
 * T076: Risk identification analysis
 * T077: Requirement-testcase association suggestions
 */

import { triggerAnalysis } from '$lib/apis/pm/agent';
import { addSuggestion, setAgentLoading, setAgentError, clearSuggestions } from '$lib/stores/pm/agentStore';
import type { ModuleType, AgentSuggestion } from '$lib/apis/pm/types';

// ============================================================================
// PRD Completeness Analysis (T075)
// ============================================================================

export const PRD_REQUIRED_SECTIONS = [
	{ type: 'overview', label: '概述' },
	{ type: 'background', label: '背景' },
	{ type: 'goal', label: '目标' },
	{ type: 'requirement', label: '功能需求' },
	{ type: 'non_functional', label: '非功能性需求' },
	{ type: 'appendix', label: '附录' }
];

export async function analyzePRDCompleteness(moduleId: string): Promise<void> {
	setAgentLoading(true);
	setAgentError(null);

	try {
		const response = await triggerAnalysis(moduleId, 'prd', 'completeness');
		if (response.success && response.data) {
			const suggestions: AgentSuggestion[] = response.data.map((s: any) => ({
				id: s.id || `sug-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
				moduleId,
				moduleType: 'prd' as ModuleType,
				type: 'completeness',
				title: s.title,
				description: s.description,
				confidence: s.confidence || 0,
				status: 'pending' as const,
				createdAt: Date.now()
			}));
			suggestions.forEach(s => addSuggestion(s));
		} else {
			setAgentError(response.error || 'PRD分析失败');
		}
	} catch (e) {
		setAgentError('PRD分析时出错');
	} finally {
		setAgentLoading(false);
	}
}

// ============================================================================
// Risk Identification Analysis (T076)
// ============================================================================

export const RISK_CATEGORIES = [
	{ key: 'technical', label: '技术风险' },
	{ key: 'schedule', label: '进度风险' },
	{ key: 'resource', label: '资源风险' },
	{ key: 'scope', label: '范围风险' },
	{ key: 'quality', label: '质量风险' },
	{ key: 'dependency', label: '依赖风险' }
];

export async function analyzeRiskIdentification(moduleId: string): Promise<void> {
	setAgentLoading(true);
	setAgentError(null);

	try {
		const response = await triggerAnalysis(moduleId, 'risk', 'risk');
		if (response.success && response.data) {
			const suggestions: AgentSuggestion[] = response.data.map((s: any) => ({
				id: s.id || `sug-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
				moduleId,
				moduleType: 'risk' as ModuleType,
				type: 'risk',
				title: s.title,
				description: s.description,
				confidence: s.confidence || 0,
				status: 'pending' as const,
				createdAt: Date.now()
			}));
			suggestions.forEach(s => addSuggestion(s));
		} else {
			setAgentError(response.error || '风险分析失败');
		}
	} catch (e) {
		setAgentError('风险分析时出错');
	} finally {
		setAgentLoading(false);
	}
}

// ============================================================================
// Requirement-Testcase Association Suggestions (T077)
// ============================================================================

export async function analyzeRequirementTestcaseAssociation(moduleId: string): Promise<void> {
	setAgentLoading(true);
	setAgentError(null);

	try {
		const response = await triggerAnalysis(moduleId, 'requirement', 'association');
		if (response.success && response.data) {
			const suggestions: AgentSuggestion[] = response.data.map((s: any) => ({
				id: s.id || `sug-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
				moduleId,
				moduleType: 'requirement' as ModuleType,
				type: 'association',
				title: s.title,
				description: s.description,
				confidence: s.confidence || 0,
				status: 'pending' as const,
				createdAt: Date.now()
			}));
			suggestions.forEach(s => addSuggestion(s));
		} else {
			setAgentError(response.error || '关联分析失败');
		}
	} catch (e) {
		setAgentError('关联分析时出错');
	} finally {
		setAgentLoading(false);
	}
}

// ============================================================================
// Unified Analysis Trigger
// ============================================================================

export async function runAnalysisForModule(moduleId: string, moduleType: ModuleType): Promise<void> {
	setAgentLoading(true);
	setAgentError(null);
	clearSuggestions();

	try {
		const response = await triggerAnalysis(moduleId, moduleType, 'improvement');
		if (response.success && response.data) {
			const suggestions: AgentSuggestion[] = response.data.map((s: any) => ({
				id: s.id || `sug-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
				moduleId,
				moduleType,
				type: s.type || 'improvement',
				title: s.title,
				description: s.description,
				confidence: s.confidence || 0,
				status: 'pending' as const,
				createdAt: Date.now()
			}));
			suggestions.forEach(s => addSuggestion(s));
		} else {
			setAgentError(response.error || '分析失败');
		}
	} catch (e) {
		setAgentError('分析时出错');
	} finally {
		setAgentLoading(false);
	}
}
