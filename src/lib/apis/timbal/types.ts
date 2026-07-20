/**
 * Timbal API Types
 * 
 * Based on Timbal documentation: https://docs.timbal.ai
 */

// ============================================================================
// Configuration
// ============================================================================

export interface TimbalConfig {
	baseUrl: string;
	apiKey: string;
	organizationId?: string;
	projectId?: string;
}

// ============================================================================
// Workflow Definition (Timbal Format)
// ============================================================================

export interface TimbalWorkflow {
	id: string;
	name: string;
	description?: string;
	steps: TimbalStep[];
	version: string;
	created_at: string;
	updated_at: string;
}

export interface TimbalStep {
	id: string;
	name: string;
	type: TimbalStepType;
	config: Record<string, unknown>;
	depends_on: string[];
	outputs: Record<string, unknown>;
}

export type TimbalStepType =
	| 'agent'
	| 'llm'
	| 'tool'
	| 'condition'
	| 'loop'
	| 'parallel'
	| 'delay'
	| 'custom';

// ============================================================================
// Execution
// ============================================================================

export interface TimbalExecutionRequest {
	workflow_id: string;
	input_data: Record<string, unknown>;
	metadata?: Record<string, unknown>;
}

export interface TimbalExecutionResponse {
	execution_id: string;
	status: TimbalExecutionStatus;
	started_at: string;
	completed_at?: string;
	output?: Record<string, unknown>;
	error?: TimbalExecutionError;
}

export type TimbalExecutionStatus =
	| 'pending'
	| 'running'
	| 'completed'
	| 'failed'
	| 'cancelled';

export interface TimbalExecutionError {
	code: string;
	message: string;
	details?: Record<string, unknown>;
}

// ============================================================================
// Streaming
// ============================================================================

export interface TimbalStreamEvent {
	type: 'step_start' | 'step_complete' | 'output' | 'error' | 'complete';
	execution_id: string;
	step_id?: string;
	data?: Record<string, unknown>;
	timestamp: string;
}

// ============================================================================
// Health
// ============================================================================

export interface TimbalHealthResponse {
	status: 'healthy' | 'unhealthy';
	version: string;
	components: Record<string, {
		status: 'healthy' | 'unhealthy';
		message?: string;
	}>;
}
