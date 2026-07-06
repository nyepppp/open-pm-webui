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
	| 'product-architecture'
	| 'prototype'
	| 'schedule'
	| 'requirement-boundary'
	| 'spec'
	| 'flowchart'
	| 'architecture';

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
	data?: Record<string, unknown>;
	metadata?: Record<string, unknown>;
	versionId?: string;
	status: ModuleStatus;
	priority?: Priority;
	currentVersionNumber?: string;
	branchName?: string;
	createdAt: number;
	updatedAt: number;
	version: number; // optimistic lock
}

// Entry-level version snapshot
export interface EntryVersion {
	id: string;
	entryId: string;
	projectId: string;
	moduleType: ModuleType;
	versionNumber: string;
	content: string;
	entry_metadata: Record<string, unknown>;
	parentId: string | null;
	branchName: string;
	changeSummary: string;
	projectVersionId?: string;
	createdBy: string;
	createdAt: number;
}

// Version branch
export interface VersionBranch {
	id: string;
	projectId: string;
	entryId: string;
	name: string;
	sourceVersionId: string;
	status: 'active' | 'merged' | 'archived';
	mergedToVersionId: string | null;
	createdAt: number;
	updatedAt: number;
}

// Conflict item for version merge
export interface ConflictItem {
	path: string;
	type: 'content' | 'metadata';
	sourceValue: unknown;
	targetValue: unknown;
	resolution: 'source' | 'target' | 'manual' | null;
	resolvedValue: unknown | null;
}

// Version merge record
export interface VersionMerge {
	id: string;
	branchId: string;
	sourceVersionId: string;
	targetVersionId: string;
	conflicts: ConflictItem[];
	status: 'pending' | 'resolved' | 'auto_merged';
	resolvedBy: string | null;
	mergedAt: number | null;
	createdAt: number;
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
	source?: 'manual' | 'excel' | 'agent' | 'prd';
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
		moduleType?: string;
		entryId?: string;
		versionId?: string;
		priority?: string;
		entryCount?: number;
		source?: 'auto' | 'manual';
		paramCount?: number;
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
	versionSnapshot?: {
		entityAVersionNumber?: string;
		entityBVersionNumber?: string;
	};
	createdAt: number;
}

// ============================================================================
// Annotation
// ============================================================================

export interface EntryAnnotation {
	id: string;
	entryId: string;
	entryVersionId: string;
	textRange: { from: number; to: number };
	selectedText: string;
	content: string;
	highlightColor: string;
	createdBy: string;
	createdAt: number;
	updatedAt: number;
	elementRef?: {
		componentName?: string;
		selector?: string;
	};
	linkedEntries?: string[];
	boundary?: string;
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

// Agent Chat
export interface AgentChatMessage {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	timestamp: number;
	actions?: AgentAction[];
	skillId?: string;
}

export type AgentSkillId =
	| 'prd-generation'
	| 'requirement-analysis'
	| 'competitor-research'
	| 'prototype-check'
	| 'parameter-extract'
	| 'testcase-generate'
	| 'version-compare'
	| 'relation-suggest'
	| 'workflow-suggest'
	| 'general';

export interface AgentSkill {
	id: AgentSkillId;
	name: string;
	description: string;
	icon: string;
}

export interface AgentIntent {
	skillId: AgentSkillId;
	confidence: number;
}

export interface AgentAction {
	id: string;
	type: 'pm.entry.create' | 'pm.entry.update' | 'pm.relation.create' | 'pm.version.create' | 'pm.parameter.extract';
	label: string;
	description: string;
	payload: Record<string, unknown>;
	status: 'pending' | 'applied' | 'dismissed';
}

export interface AgentChatRequest {
	message: string;
	projectId: string;
	moduleType?: ModuleType;
	entryId?: string;
	context?: {
		projectName?: string;
		entryTitle?: string;
		entryContentSummary?: string;
	};
}

export interface AgentChatResponse {
	message: string;
	intent?: AgentIntent;
	actions?: AgentAction[];
	skillId?: AgentSkillId;
}

export interface AgentStatus {
	available: boolean;
	provider: string;
	model: string;
	lastAnalysisAt?: number;
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
	type: 'text' | 'textarea' | 'select' | 'multiselect' | 'number' | 'date' | 'json' | 'richtext' | 'combobox';
	required?: boolean;
	options?: string[];
	dataSource?: 'modules' | 'features' | 'parameters';
	dependsOn?: string;
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

export interface FlowchartData {
	nodes: FlowchartNode[];
	edges: FlowchartEdge[];
	viewport?: { x: number; y: number; zoom: number };
	nodeTypes?: Record<string, CustomNodeType>;
}

export interface CustomNodeType {
	label: string;
	defaultStyle: NodeStyle;
	icon?: string;
	description?: string;
}

export interface NodeStyle {
	backgroundColor?: string;
	borderColor?: string;
	borderWidth?: number;
	borderRadius?: number;
	width?: number;
	height?: number;
	icon?: string;
	shape?: 'rectangle' | 'rounded' | 'circle' | 'diamond' | 'ellipse';
}

export interface FlowchartNode {
	id: string;
	type: string;
	position: { x: number; y: number };
	data: {
		label: string;
		description?: string;
		style?: Partial<NodeStyle>;
		inputParams?: string[];
		outputParams?: string[];
		traceability?: NodeTraceability;
	};
}

export interface NodeTraceability {
	entityType: 'prd' | 'module' | 'feature' | 'parameter' | 'none';
	entityId: string;
	entityName: string;
	versionId?: string;
	versionNumber?: string;
	boundAt: number;
	boundBy?: string;
}

export interface FlowchartEdge {
	id: string;
	source: string;
	target: string;
	label?: string;
	type?: 'default' | 'conditional';
	style?: EdgeStyle;
}

export interface EdgeStyle {
	stroke?: string;
	strokeWidth?: number;
	strokeDasharray?: string;
	animated?: boolean;
}
