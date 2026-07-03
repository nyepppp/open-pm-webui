import { getOne, create } from './index';
import type { AgentSuggestion, ModuleType, ApiResponse } from './types';

// ============================================================================
// AI Service Error Types
// ============================================================================

export type AIServiceErrorType =
	| 'no_api_key'      // 401: AI API Key not configured
	| 'rate_limited'    // 429: Rate limit exceeded
	| 'unavailable'     // 503: AI service unavailable
	| 'timeout'         // Request timeout
	| 'network'         // Network error
	| 'unknown';        // Unknown error

export interface AIServiceError {
	type: AIServiceErrorType;
	message: string;
	retryable: boolean;
	suggestion: string; // User-facing suggestion for resolution
}

// ============================================================================
// Error Classification
// ============================================================================

export function classifyAIError(error: string | number | null): AIServiceError {
	if (!error) {
		return {
			type: 'unknown',
			message: '未知错误',
			retryable: false,
			suggestion: '请稍后重试'
		};
	}

	// HTTP status code classification
	if (typeof error === 'number') {
		switch (error) {
			case 401:
				return {
					type: 'no_api_key',
					message: 'AI 服务未配置',
					retryable: false,
					suggestion: '请在设置中配置 AI API Key 后再使用分析功能'
				};
			case 429:
				return {
					type: 'rate_limited',
					message: 'AI 服务请求频率超限',
					retryable: true,
					suggestion: '请稍后再试，或减少自动分析频率'
				};
			case 503:
				return {
					type: 'unavailable',
					message: 'AI 服务暂时不可用',
					retryable: true,
					suggestion: 'AI 服务正在维护中，请稍后重试。您仍可手动编辑所有内容'
				};
			default:
				return {
					type: 'unknown',
					message: `请求失败 (${error})`,
					retryable: error >= 500,
					suggestion: '请稍后重试'
				};
		}
	}

	// String error classification
	const errorStr = String(error).toLowerCase();
	if (errorStr.includes('api key') || errorStr.includes('unauthorized') || errorStr.includes('401')) {
		return {
			type: 'no_api_key',
			message: 'AI 服务未配置',
			retryable: false,
			suggestion: '请在设置中配置 AI API Key 后再使用分析功能'
		};
	}
	if (errorStr.includes('rate limit') || errorStr.includes('429') || errorStr.includes('too many')) {
		return {
			type: 'rate_limited',
			message: 'AI 服务请求频率超限',
			retryable: true,
			suggestion: '请稍后再试，或减少自动分析频率'
		};
	}
	if (errorStr.includes('unavailable') || errorStr.includes('503') || errorStr.includes('service')) {
		return {
			type: 'unavailable',
			message: 'AI 服务暂时不可用',
			retryable: true,
			suggestion: 'AI 服务正在维护中，请稍后重试。您仍可手动编辑所有内容'
		};
	}
	if (errorStr.includes('timeout') || errorStr.includes('timed out')) {
		return {
			type: 'timeout',
			message: 'AI 分析超时',
			retryable: true,
			suggestion: '文档内容可能过长，请尝试缩短内容后重试'
		};
	}
	if (errorStr.includes('network') || errorStr.includes('fetch') || errorStr.includes('connection')) {
		return {
			type: 'network',
			message: '网络连接失败',
			retryable: true,
			suggestion: '请检查网络连接后重试'
		};
	}

	return {
		type: 'unknown',
		message: String(error),
		retryable: false,
		suggestion: '请稍后重试'
	};
}

// ============================================================================
// API Functions (with graceful error handling)
// ============================================================================

export function getSuggestions(moduleId: string, moduleType: ModuleType) {
	return getOne<AgentSuggestion[]>(`/agent/suggestions?moduleId=${moduleId}&moduleType=${moduleType}`);
}

export async function triggerAnalysis(
	moduleId: string,
	moduleType: ModuleType,
	type: 'completeness' | 'risk' | 'association' | 'improvement'
): Promise<ApiResponse<AgentSuggestion[]>> {
	try {
		const result = await create<AgentSuggestion[]>(`/agent/analyze`, { moduleId, moduleType, type });

		if (!result.success && result.error) {
			// Classify the error for better user messaging
			const classified = classifyAIError(result.error);
			return {
				success: false,
				error: classified.message,
				message: classified.suggestion
			};
		}

		return result;
	} catch (err) {
		// Network/fetch errors
		const classified = classifyAIError(err instanceof Error ? err.message : String(err));
		return {
			success: false,
			error: classified.message,
			message: classified.suggestion
		};
	}
}

export function confirmSuggestion(suggestionId: string) {
	return create<AgentSuggestion>(`/agent/suggestions/${suggestionId}/confirm`, {});
}

export function rejectSuggestion(suggestionId: string) {
	return create<AgentSuggestion>(`/agent/suggestions/${suggestionId}/reject`, {});
}
