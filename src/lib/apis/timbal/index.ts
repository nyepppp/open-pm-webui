/**
 * Timbal API Client
 * 
 * Provides integration with Timbal's workflow execution platform.
 * Based on: https://docs.timbal.ai
 */

import type {
	TimbalConfig,
	TimbalWorkflow,
	TimbalExecutionRequest,
	TimbalExecutionResponse,
	TimbalStreamEvent,
	TimbalHealthResponse
} from './types';

// ============================================================================
// Configuration
// ============================================================================

let config: TimbalConfig = {
	baseUrl: '',
	apiKey: ''
};

export function configureTimbal(newConfig: Partial<TimbalConfig>) {
	config = { ...config, ...newConfig };
}

export function getTimbalConfig(): TimbalConfig {
	return { ...config };
}

// ============================================================================
// HTTP Client
// ============================================================================

async function timbalFetch<T>(
	endpoint: string,
	options: RequestInit = {}
): Promise<T> {
	if (!config.baseUrl) {
		throw new Error('Timbal base URL not configured. Call configureTimbal() first.');
	}

	const url = `${config.baseUrl}${endpoint}`;
	const headers = {
		'Content-Type': 'application/json',
		...(config.apiKey && { Authorization: `Bearer ${config.apiKey}` }),
		...options.headers
	};

	const response = await fetch(url, {
		...options,
		headers
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({}));
		throw new Error(
			`Timbal API error: ${response.status} ${response.statusText}\n${JSON.stringify(error, null, 2)}`
		);
	}

	return response.json();
}

// ============================================================================
// Workflow Management
// ============================================================================

export async function createWorkflow(workflow: TimbalWorkflow): Promise<TimbalWorkflow> {
	return timbalFetch('/workflows', {
		method: 'POST',
		body: JSON.stringify(workflow)
	});
}

export async function getWorkflow(workflowId: string): Promise<TimbalWorkflow> {
	return timbalFetch(`/workflows/${workflowId}`);
}

export async function updateWorkflow(
	workflowId: string,
	updates: Partial<TimbalWorkflow>
): Promise<TimbalWorkflow> {
	return timbalFetch(`/workflows/${workflowId}`, {
		method: 'PUT',
		body: JSON.stringify(updates)
	});
}

export async function deleteWorkflow(workflowId: string): Promise<void> {
	await timbalFetch(`/workflows/${workflowId}`, {
		method: 'DELETE'
	});
}

export async function listWorkflows(): Promise<TimbalWorkflow[]> {
	return timbalFetch('/workflows');
}

// ============================================================================
// Execution
// ============================================================================

export async function executeWorkflow(
	workflowId: string,
	inputData: Record<string, unknown> = {}
): Promise<TimbalExecutionResponse> {
	const request: TimbalExecutionRequest = {
		workflow_id: workflowId,
		input_data: inputData
	};

	return timbalFetch('/run', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}

export async function getExecutionStatus(
	executionId: string
): Promise<TimbalExecutionResponse> {
	return timbalFetch(`/executions/${executionId}`);
}

export async function cancelExecution(executionId: string): Promise<void> {
	await timbalFetch(`/executions/${executionId}/cancel`, {
		method: 'POST'
	});
}

// ============================================================================
// Streaming
// ============================================================================

export function streamWorkflow(
	workflowId: string,
	inputData: Record<string, unknown> = {},
	onEvent: (event: TimbalStreamEvent) => void,
	onError?: (error: Error) => void
): () => void {
	if (!config.baseUrl) {
		throw new Error('Timbal base URL not configured. Call configureTimbal() first.');
	}

	const url = new URL(`${config.baseUrl}/stream`);
	url.searchParams.append('workflow_id', workflowId);

	const eventSource = new EventSource(url.toString());

	eventSource.onmessage = (event) => {
		try {
			const data = JSON.parse(event.data) as TimbalStreamEvent;
			onEvent(data);
		} catch (error) {
			console.error('Failed to parse stream event:', error);
		}
	};

	eventSource.onerror = (error) => {
		if (onError) {
			onError(new Error('Stream error: ' + JSON.stringify(error)));
		}
		eventSource.close();
	};

	// Return cleanup function
	return () => {
		eventSource.close();
	};
}

// ============================================================================
// Health
// ============================================================================

export async function checkHealth(): Promise<TimbalHealthResponse> {
	return timbalFetch('/healthcheck');
}

// ============================================================================
// Utility
// ============================================================================

export function isConfigured(): boolean {
	return !!config.baseUrl && !!config.apiKey;
}

export function getConfigSummary(): { baseUrl: string; isConfigured: boolean } {
	return {
		baseUrl: config.baseUrl,
		isConfigured: isConfigured()
	};
}
