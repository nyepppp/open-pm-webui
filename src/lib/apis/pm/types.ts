/**
 * Base types for PM (Project Management) Workspace
 * Shared across all PM modules, stores, and APIs
 */

// ============================================================================
// Module Types
// ============================================================================

export type ModuleType =
	| 'prd'
	| 'requirement'
	| 'parameter'
	| 'testcase'
	| 'risk'
	| 'competitor'
	| 'roadmap'
	| 'meeting'
	| 'acceptance'
	| 'faq'
	| 'product-architecture';

export type ModuleCategory = 'planning' | 'design' | 'execution' | 'review';

export type ModuleStatus = 'draft' | 'review' | 'approved' | 'archived';

export type Priority = 'p0' | 'p1' | 'p2' | 'p3';

// ============================================================================
// Core Entities
// ============================================================================

export interface Project {
	id: string;
	name: string;
	description?: string;
	type: 'prd' | 'competitor' | 'general';
	status: 'active' | 'archived' | 'deleted';
	config?: Record<string, unknown>;
	createdAt: number;
	updatedAt: number;
}

export interface Version {
	id: string;
	projectId: string;
	versionNumber: string;
	label?: 'milestone' | 'release' | 'review';
	description: string;
	snapshotPath: string;
	createdBy?: string;
	createdAt: number;
}

export interface ModuleEntry {
	id: string;
	projectId: string;
	moduleType: ModuleType;
	title: string;
	content?: string;
	metadata?: Record<string, unknown>;
	versionId?: string;
	status: ModuleStatus;
	priority?: Priority;
	createdAt: number;
	updatedAt: number;
	version: number; // optimistic lock
}

// ============================================================================
// Module-Specific Schemas
// ============================================================================

// PRD Document
export interface PRDSection {
	id: string;
	type: 'overview' | 'background' | 'goal' | 'requirement' | 'non_functional' | 'appendix';
	title: string;
	content: string;
	parameters: string[];
	order: number;
}

export interface PRDDocument {
	sections: PRDSection[];
	template?: 'standard' | 'minimal' | 'detailed';
	attachments?: Attachment[];
}

export interface Attachment {
	id: string;
	name: string;
	url: string;
	size: number;
	mimeType: string;
}

// Requirement
export interface Requirement {
	source?: 'manual' | 'excel' | 'agent';
	category?: string;
	tags?: string[];
	userRole?: string;
	expectedBenefit?: string;
	relatedModules?: string[];
}

// Parameter
export interface Parameter {
	key: string;
	moduleId?: string;
	featureId?: string;
	paramType: 'input' | 'output' | 'config';
	dataType: 'string' | 'number' | 'boolean' | 'object' | 'array';
	required: 0 | 1;
	defaultValue?: string;
	description?: string;
	sourceDocument?: string;
}

// Testcase
export interface Testcase {
	scenario: string;
	precondition?: string;
	steps: string;
	inputData?: string;
	expectedResult: string;
	caseType: 'functional' | 'boundary' | 'exception' | 'performance';
	requirementId?: string;
	parameterId?: string;
}

// Risk
export interface Risk {
	probability: 'high' | 'medium' | 'low';
	impactScope: string;
	owner?: string;
	measures?: string;
	deadline?: number;
}

// Competitor
export interface Competitor {
	name: string;
	url?: string;
	description?: string;
	dimensions?: CompetitorDimension[];
}

export interface CompetitorDimension {
	name: string;
	score: number; // 0-100
	notes?: string;
}

// Roadmap
export interface Roadmap {
	nodes: MindMapNode[];
	layout?: 'hierarchical' | 'radial' | 'free';
}

// Meeting
export interface Meeting {
	participants?: string[];
	meetingDate?: number;
	conclusions?: string;
	actionItems?: ActionItem[];
}

export interface ActionItem {
	id: string;
	description: string;
	assignee?: string;
	deadline?: number;
	status: 'pending' | 'in_progress' | 'completed';
}

// Acceptance
export interface Acceptance {
	scope?: string;
	result?: 'pass' | 'fail' | 'partial';
	passedItems?: string[];
	remainingIssues?: string[];
}

// FAQ
export interface FAQ {
	question: string;
	answer: string;
	audience?: string;
	relatedFeatures?: string[];
}

// Product Architecture
export interface ProductArchitecture {
	nodes: MindMapNode[];
	autoExtracted?: boolean;
}

// ============================================================================
// MindMap
// ============================================================================

export interface MindMapNode {
	id: string;
	projectId: string;
	parentId: string | null;
	label: string;
	type: 'root' | 'branch' | 'leaf' | 'dependency';
	position: { x: number; y: number };
	metadata?: {
		color?: string;
		icon?: string;
		progress?: number;
		status?: 'planned' | 'in_progress' | 'completed' | 'delayed';
	};
	moduleRef?: string | null;
	createdAt: number;
	updatedAt: number;
}

// ============================================================================
// Relation
// ============================================================================

export type RelationType = 'contains' | 'references' | 'derives' | 'modifies' | 'conflicts';

export interface Relation {
	id: string;
	projectId: string;
	entityAId: string;
	entityBId: string;
	relationType: RelationType;
	confidence?: number; // 0-100
	confirmed: 0 | 1;
	createdBy?: 'ai' | 'user';
	createdAt: number;
}

// ============================================================================
// Agent
// ============================================================================

export interface AgentSuggestion {
	id: string;
	moduleId: string;
	moduleType: ModuleType;
	type: 'completeness' | 'risk' | 'association' | 'improvement';
	title: string;
	description: string;
	confidence: number;
	status: 'pending' | 'confirmed' | 'rejected';
	createdAt: number;
}

// ============================================================================
// Navigation
// ============================================================================

export interface ModuleNavItem {
	id: ModuleType;
	label: string;
	icon: string;
	category: ModuleCategory;
	path: string;
}

export interface ModuleCategoryGroup {
	id: ModuleCategory;
	label: string;
	icon: string;
	modules: ModuleNavItem[];
}

// ============================================================================
// Editor Types
// ============================================================================

export type EditorType = 'rich' | 'form' | 'mixed' | 'mindmap';

export interface EditorConfig {
	type: EditorType;
	moduleType: ModuleType;
	fields: FieldConfig[];
}

export interface FieldConfig {
	name: string;
	label: string;
	type: 'text' | 'textarea' | 'select' | 'multiselect' | 'number' | 'date' | 'json' | 'richtext';
	required?: boolean;
	options?: string[];
	placeholder?: string;
	validation?: {
		min?: number;
		max?: number;
		pattern?: string;
	};
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
	success: boolean;
	data?: T;
	error?: string;
	message?: string;
}

export interface PaginatedResponse<T> {
	items: T[];
	total: number;
	page: number;
	pageSize: number;
	hasMore: boolean;
}
