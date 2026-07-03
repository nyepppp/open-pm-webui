<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';
	import { getEntries, createEntry, deleteEntry, updateEntry, getEntry } from '$lib/apis/pm/index';
	import { createCalendarEvent, getCalendars } from '$lib/apis/calendar';
	import { currentVersion, versions as versionList } from '$lib/stores/pm/versionStore';
	import { createNewNote } from '$lib/apis/notes/index';
	import { getModuleFields, getModuleEditorConfig, type ModuleEditorConfig } from '$lib/components/pm/moduleFields';
	import PMRichEditor from '$lib/components/pm/PMRichEditor.svelte';
	import PMVersionHistoryDropdown from '$lib/components/pm/PMVersionHistoryDropdown.svelte';
	import PMVersionComparePanel from '$lib/components/pm/PMVersionComparePanel.svelte';
	import PMVersionBranchDialog from '$lib/components/pm/PMVersionBranchDialog.svelte';
	import PMVersionMergePanel from '$lib/components/pm/PMVersionMergePanel.svelte';
	import PMSaveVersionDialog from '$lib/components/pm/PMSaveVersionDialog.svelte';
	import { createEntryVersion } from '$lib/apis/pm/version';
	import { marked } from 'marked';
	import type { ModuleType, ModuleStatus, Priority, PRDSection, MindMapNode, ModuleEntry } from '$lib/apis/pm/types';
	import PMMindMap from '$lib/components/pm/PMMindMap.svelte';
	import PMTraceabilityGraph from '$lib/components/pm/PMTraceabilityGraph.svelte';
	import PMAgentChatPanel from '$lib/components/pm/PMAgentChatPanel.svelte';
	import { chatContext } from '$lib/stores/pm/agentChatStore';
	import { currentProjectName } from '$lib/stores/pm/projectStore';
	import type { AgentAction } from '$lib/apis/pm/types';
	import mammoth from 'mammoth';

	let projectId = $derived($page.params.projectId);
	let moduleType = $derived($page.params.module as ModuleType);

	type EditorType = 'rich' | 'table' | 'form' | 'mindmap';
	interface ModuleConf { name: string; editorType: EditorType; tableColumns?: { key: string; label: string; width?: string }[]; formFields?: { key: string; label: string; type: 'text' | 'textarea' | 'select' }[] }

	const moduleConfig: Record<string, ModuleConf> = {
		requirement: { name: '需求管理', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '标题' },
			{ key: 'description', label: '描述', width: 'w-32' },
			{ key: 'source', label: '来源', width: 'w-16' }, { key: 'category', label: '分类', width: 'w-20' },
			{ key: 'userRole', label: '用户角色', width: 'w-20' }, { key: 'tags', label: '标签', width: 'w-24' },
			{ key: 'currentVersionNumber', label: '版本', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }, { key: 'updatedAt', label: '更新', width: 'w-24' }
		]},
		parameter: { name: '参数配置', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '参数名' },
			{ key: 'paramKey', label: 'Key', width: 'w-24' }, { key: 'paramType', label: '类型', width: 'w-16' },
			{ key: 'dataType', label: '数据类型', width: 'w-16' }, { key: 'defaultValue', label: '默认值', width: 'w-20' },
			{ key: 'required', label: '必填', width: 'w-12' }, { key: 'description', label: '描述', width: 'w-24' },
			{ key: 'sourceDocument', label: '来源', width: 'w-20' }, { key: 'moduleName', label: '所属模块', width: 'w-20' },
			{ key: 'featureName', label: '所属功能', width: 'w-20' },
			{ key: 'currentVersionNumber', label: '版本', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }
		]},
		testcase: { name: '测试用例', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '用例标题' },
			{ key: 'caseType', label: '类型', width: 'w-16' }, { key: 'scenario', label: '场景', width: 'w-24' },
			{ key: 'precondition', label: '前置条件', width: 'w-24' }, { key: 'steps', label: '步骤', width: 'w-24' },
			{ key: 'expectedResult', label: '预期结果', width: 'w-24' },
			{ key: 'requirementId', label: '关联需求', width: 'w-20' }, { key: 'featureName', label: '关联功能', width: 'w-20' },
			{ key: 'currentVersionNumber', label: '版本', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }, { key: 'updatedAt', label: '更新', width: 'w-24' }
		]},
		prd: { name: 'PRD 文档', editorType: 'rich' },
		risk: { name: '风险分析', editorType: 'form', formFields: [
			{ key: 'probability', label: '概率', type: 'select' }, { key: 'impactScope', label: '影响范围', type: 'text' },
			{ key: 'featureName', label: '关联功能块', type: 'select' },
			{ key: 'owner', label: '负责人', type: 'text' }, { key: 'measures', label: '应对措施', type: 'textarea' }
		]},
		competitor: { name: '竞品分析', editorType: 'competitor', formFields: [
			{ key: 'competitorUrl', label: '竞品URL', type: 'text' }, { key: 'dimension', label: '分析维度', type: 'text' },
			{ key: 'ourProduct', label: '我方产品', type: 'textarea' }, { key: 'competitorProduct', label: '竞品', type: 'textarea' },
			{ key: 'analysis', label: '分析结论', type: 'textarea' }
		]},
		roadmap: { name: '产品路线图', editorType: 'table', tableColumns: [
			{ key: 'title', label: '节点名称' }, { key: 'description', label: '描述', width: 'w-32' },
			{ key: 'nodeType', label: '类型', width: 'w-20' },
			{ key: 'currentVersionNumber', label: '版本', width: 'w-20' },
			{ key: 'nodeStatus', label: '状态', width: 'w-20' },
			{ key: 'startDate', label: '开始', width: 'w-24' },
			{ key: 'endDate', label: '结束', width: 'w-24' }, { key: 'dependencies', label: '依赖', width: 'w-24' },
			{ key: 'updatedAt', label: '更新', width: 'w-24' }
		]},
		meeting: { name: '会议纪要', editorType: 'rich' },
		acceptance: { name: '验收报告', editorType: 'form', formFields: [
			{ key: 'requirementId', label: '关联需求', type: 'select' },
			{ key: 'scope', label: '验收范围', type: 'textarea' }, { key: 'result', label: '结果', type: 'select' },
			{ key: 'remainingIssues', label: '遗留问题', type: 'textarea' }
		]},
		faq: { name: 'FAQ', editorType: 'form', formFields: [
			{ key: 'question', label: '问题', type: 'textarea' }, { key: 'answer', label: '答案', type: 'textarea' },
			{ key: 'audience', label: '受众', type: 'text' }, { key: 'relatedFeatures', label: '关联功能', type: 'select' }
		]},
		'product-architecture': { name: '产品架构', editorType: 'mindmap' },
		prototype: { name: '原型/UI设计', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '名称' },
			{ key: 'protoType', label: '类型', width: 'w-20' }, { key: 'description', label: '描述', width: 'w-32' },
			{ key: 'currentVersionNumber', label: '版本', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }, { key: 'updatedAt', label: '更新', width: 'w-24' }
		]},
		schedule: { name: '项目排期', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '任务名称' },
			{ key: 'assignee', label: '负责人', width: 'w-20' },
			{ key: 'startDate', label: '开始', width: 'w-24' }, { key: 'endDate', label: '结束', width: 'w-24' },
			{ key: 'progress', label: '进度', width: 'w-16' }, { key: 'isMilestone', label: '里程碑', width: 'w-16' },
			{ key: 'currentVersionNumber', label: '版本', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }, { key: 'updatedAt', label: '更新', width: 'w-24' }
		]}
	};

	let config = $derived(moduleConfig[moduleType] || { name: '未知模块', editorType: 'rich' as EditorType });
	let entries = $state<ModuleEntry[]>([]);
	let isLoading = $state(true);
	let loadError = $state('');
	let query = $state('');
	let showNewForm = $state(false);
	let newTitle = $state('');
	let newContent = $state('');
	let newPriority = $state<Priority>('p2');
	let newStatus = $state<ModuleStatus>('draft');
	// Parameter-specific
	let newParamKey = $state('');
	let newParamType = $state<'input' | 'output' | 'config'>('config');
	let newDataType = $state<'string' | 'number' | 'boolean' | 'object' | 'array'>('string');
	let newDefaultValue = $state('');
	let newParamRequired = $state(true);
	let newParamDescription = $state('');
	let newSourceDocument = $state('');
	let newModuleName = $state('');
	let newFeatureName = $state('');
	// Testcase-specific
	let newCaseType = $state<'functional' | 'boundary' | 'exception' | 'performance'>('functional');
	let newScenario = $state('');
	let newPrecondition = $state('');
	let newSteps = $state('');
	let newInputData = $state('');
	let newExpectedResult = $state('');
	let newRequirementId = $state('');
	let newParameterId = $state('');
	// Requirement-specific
	let newSource = $state<'manual' | 'excel' | 'agent'>('manual');
	let newCategory = $state('');
	let newDescription = $state('');
	let newTags = $state('');
	let newUserRole = $state('');
	let newExpectedBenefit = $state('');
	let newRelatedModules = $state('');
	// Roadmap-specific
	let newNodeType = $state<'milestone' | 'feature' | 'release'>('feature');
	let newNodeStatus = $state<'planned' | 'in_progress' | 'completed' | 'delayed'>('planned');
	let newStartDate = $state('');
	let newEndDate = $state('');
	let newDependencies = $state('');
	// Prototype-specific
	let newProtoType = $state<'image' | 'package' | 'review'>('image');
	// Schedule-specific
	let newAssignee = $state('');
	let newProgress = $state('');
	let newIsMilestone = $state(false);
	let newScheduleStatus = $state<ModuleStatus>('draft');
	// Form-specific (FAQ, competitor, risk, acceptance, meeting)
	let newFormData = $state<Record<string, string>>({});
	// Version field for roadmap/testcase/risk
	let newVersionId = $state('');
	// PRD editor version
	let editingVersionId = $state('');

	// Testcase related entries for dropdowns
	let requirementEntries = $state<any[]>([]);
	let parameterEntries = $state<any[]>([]);
	let prdEntries = $state<any[]>([]);
	let featureOptions = $derived([...new Set(parameterEntries.map((p: any) => (p.data || p.metadata || {}).featureName).filter(Boolean))]);
	let moduleOptions = $derived([...new Set(filteredEntries.map((e: any) => (e.data || e.metadata || {}).moduleName).filter(Boolean))].sort());
	let featureOptionsForModule = $derived(newModuleName ? [...new Set(filteredEntries.filter((e: any) => (e.data || e.metadata || {}).moduleName === newModuleName).map((e: any) => (e.data || e.metadata || {}).featureName).filter(Boolean))].sort() : []);

	// Reset feature when module changes
	$effect(() => {
		newModuleName;
		newFeatureName = '';
	});

	async function loadRelatedEntries() {
		const token = localStorage.token || '';
		try {
			if (moduleType === 'testcase' || moduleType === 'acceptance') {
				requirementEntries = await getEntries(token, projectId, 'requirement');
			}
			if (moduleType === 'testcase' || moduleType === 'faq' || moduleType === 'risk') {
				parameterEntries = await getEntries(token, projectId, 'parameter');
			}
			if (moduleType === 'parameter') {
				prdEntries = await getEntries(token, projectId, 'prd');
			}
		} catch (e: any) {
			console.warn('[PM] loadRelatedEntries failed:', e?.message);
		}
	}

	async function loadEntries() {
		isLoading = true;
		loadError = '';
		try {
			const token = localStorage.token || '';
			if (!token) { loadError = '未登录，请先登录'; entries = []; isLoading = false; return; }
			entries = await getEntries(token, projectId, moduleType);
		} catch (e: any) {
			entries = [];
			const msg = e?.message || e?.detail || '加载失败，请检查网络或项目权限';
			loadError = msg;
			console.error('[PM] loadEntries failed:', msg, { projectId, moduleType });
		} finally {
			isLoading = false;
			// Auto-open mindmap for product-architecture
			if (moduleType === 'product-architecture' && entries.length === 1) {
				openEntryEditor(entries[0].id);
			}
		}
	}
	let _loadAbort: AbortController | null = null;
	onMount(() => { loadEntries(); loadRelatedEntries(); });
	$effect(() => { moduleType; showNewForm = false; newFormData = {}; _loadAbort?.abort(); loadEntries(); loadRelatedEntries(); });

	async function handleCreate() {
		if (!newTitle.trim()) return;
		try {
			const token = localStorage.token || '';
			const data: Record<string, unknown> = { module_type: moduleType, title: newTitle, content: newContent || undefined, status: newStatus, priority: newPriority };
			if (moduleType === 'parameter') {
				data.data = { key: newParamKey, paramType: newParamType, dataType: newDataType, defaultValue: newDefaultValue, required: newParamRequired ? 1 : 0, description: newParamDescription, sourceDocument: newSourceDocument, moduleName: newModuleName, featureName: newFeatureName };
			} else if (moduleType === 'testcase') {
				data.data = { caseType: newCaseType, scenario: newScenario, precondition: newPrecondition, steps: newSteps, inputData: newInputData, expectedResult: newExpectedResult, requirementId: newRequirementId, parameterId: newParameterId, featureName: newFeatureName };
			} else if (moduleType === 'requirement') {
				data.data = { source: newSource, category: newCategory, description: newDescription, tags: newTags.split(',').map(t => t.trim()).filter(Boolean), userRole: newUserRole, expectedBenefit: newExpectedBenefit, relatedModules: newRelatedModules.split(',').map(t => t.trim()).filter(Boolean) };
				data.content = newDescription || undefined;
			} else if (moduleType === 'roadmap') {
				data.data = { nodeType: newNodeType, nodeStatus: newNodeStatus, startDate: newStartDate, endDate: newEndDate, dependencies: newDependencies, versionId: newVersionId };
			} else if (moduleType === 'prototype') {
				data.data = { protoType: newProtoType };
			} else if (moduleType === 'schedule') {
				data.data = { assignee: newAssignee, progress: Number(newProgress) || 0, isMilestone: newIsMilestone, startDate: newStartDate, endDate: newEndDate };
				data.status = newScheduleStatus;
			} else if (moduleType === 'competitor') {
				const dims: { name: string; ourScore: number; competitorScore: number; notes: string }[] = [];
				if (newFormData.dim1Name) dims.push({ name: newFormData.dim1Name, ourScore: Number(newFormData.dim1Our) || 50, competitorScore: Number(newFormData.dim1Comp) || 50, notes: '' });
				data.data = { competitorUrl: newFormData.competitorUrl, description: newFormData.description, dimensions: dims };
			} else if (config.editorType === 'form') {
				data.data = { ...newFormData };
			}
			// Auto-associate with current version for all module types
			const currentVer = $currentVersion;
			if (currentVer?.id) {
				data.versionId = currentVer.id;
				if (data.data && typeof data.data === 'object') {
					(data.data as Record<string, unknown>).versionId = currentVer.id;
				} else {
					// For rich editor types (meeting, prd) without explicit data, create data with versionId
					data.data = { versionId: currentVer.id };
				}
			}
			const created = await createEntry(token, projectId, data);
			resetForm(); await loadEntries(); toast.success('创建成功');
			// Auto-open editor for competitor after create
			if (moduleType === 'competitor' && created?.id) {
				openEntryEditor(created.id);
			}
		} catch (e: any) { toast.error(e.message || '创建失败'); }
	}
	function resetForm() {
		newTitle = ''; newContent = ''; newPriority = 'p2'; newStatus = 'draft';
		newParamKey = ''; newParamType = 'config'; newDataType = 'string'; newDefaultValue = ''; newParamRequired = true; newParamDescription = ''; newSourceDocument = ''; newModuleName = ''; newFeatureName = '';
		newCaseType = 'functional'; newScenario = ''; newPrecondition = ''; newSteps = ''; newInputData = ''; newExpectedResult = ''; newRequirementId = ''; newParameterId = '';
		newSource = 'manual'; newCategory = ''; newDescription = ''; newTags = ''; newUserRole = ''; newExpectedBenefit = ''; newRelatedModules = '';
		newNodeType = 'feature'; newNodeStatus = 'planned'; newStartDate = ''; newEndDate = ''; newDependencies = '';
		newVersionId = '';
		newProtoType = 'image'; newAssignee = ''; newProgress = ''; newIsMilestone = false; newScheduleStatus = 'draft';
		newFormData = {}; showNewForm = false;
	}
	async function handleDelete(entryId: string) { try { const token = localStorage.token || ''; await deleteEntry(token, entryId); await loadEntries(); toast.success('删除成功'); } catch (e: any) { toast.error(e.message || '删除失败'); } }
	async function handleExportToNote(entry: any) { try { const token = localStorage.token || ''; await createNewNote(token, { title: `[PM] ${entry.title}`, data: { content: { md: entry.content || '', html: '', json: null } }, meta: null, access_grants: [] }); toast.success('已导出为笔记'); } catch (e: any) { toast.error(e.message || '导出失败'); } }

	// Filter / Sort / Pagination
	let filterStatus = $state<string>('all');
	let filterPriority = $state<string>('all');
	let filterVersion = $state<string>('all');
	let sortField = $state<string>('updatedAt');
	let sortDir = $state<'asc' | 'desc'>('desc');
	let currentPage = $state(1);
	const PAGE_SIZE = 20;

	let filteredAndSorted = $derived(() => {
		let result = entries;
		if (query) result = result.filter(e => e.title.toLowerCase().includes(query.toLowerCase()));
		if (filterStatus !== 'all') result = result.filter(e => e.status === filterStatus);
		if (filterPriority !== 'all') result = result.filter(e => e.priority === filterPriority);
		if (filterVersion !== 'all') {
			result = result.filter(e => {
				const vn = e.currentVersionNumber || getEntryData(e, 'versionNumber') || '';
				return vn === filterVersion;
			});
		}
		result = [...result].sort((a, b) => {
			let va: number | string, vb: number | string;
			if (sortField === 'updatedAt') { va = a.updated_at || a.updatedAt || 0; vb = b.updated_at || b.updatedAt || 0; }
			else if (sortField === 'createdAt') { va = a.created_at || a.createdAt || 0; vb = b.created_at || b.createdAt || 0; }
			else if (sortField === 'priority') { const po: Record<string, number> = { p0: 0, p1: 1, p2: 2, p3: 3 }; va = po[a.priority] ?? 9; vb = po[b.priority] ?? 9; }
			else if (sortField === 'versionNumber') { va = a.currentVersionNumber || ''; vb = b.currentVersionNumber || ''; }
			else { va = a.updated_at || a.updatedAt || 0; vb = b.updated_at || b.updatedAt || 0; }
			if (va < vb) return sortDir === 'asc' ? -1 : 1;
			if (va > vb) return sortDir === 'asc' ? 1 : -1;
			return 0;
		});
		return result;
	});
	let filteredEntries = $derived(filteredAndSorted());
	let totalPages = $derived(Math.max(1, Math.ceil(filteredEntries.length / PAGE_SIZE)));
	let pagedEntries = $derived(filteredEntries.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));
	$effect(() => { filteredEntries; if (currentPage > totalPages) currentPage = totalPages; });

	let versionOptions = $derived(() => {
		const vns = new Set<string>();
		entries.forEach(e => { const vn = e.currentVersionNumber || getEntryData(e, 'versionNumber'); if (vn) vns.add(vn); });
		return [...vns].sort();
	});

	function toggleSort(field: string) {
		if (sortField === field) { sortDir = sortDir === 'asc' ? 'desc' : 'asc'; }
		else { sortField = field; sortDir = 'desc'; }
	}
	function sortIndicator(field: string): string {
		if (sortField !== field) return '';
		return sortDir === 'asc' ? ' ↑' : ' ↓';
	}

	import { normalizeTs, formatDate, formatDateTime } from '$lib/utils/pmTimeUtils';
	function formatTime(ts: unknown): string {
		const ms = normalizeTs(ts);
		if (ms == null) return '';
		try { return dayjs(ms).fromNow(); } catch { return ''; }
	}
	function getEntryData(entry: any, key: string): string { return (entry.data || entry.metadata || {})[key] ?? ''; }

	const statusMap: Record<string, { l: string; c: string }> = {
		draft: { l: '草稿', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' },
		review: { l: '评审中', c: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
		approved: { l: '已批准', c: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		archived: { l: '已归档', c: 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500' }
	};
	const prioMap: Record<string, { l: string; c: string }> = {
		p0: { l: 'P0', c: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' },
		p1: { l: 'P1', c: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400' },
		p2: { l: 'P2', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		p3: { l: 'P3', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' }
	};
	const sourceMap: Record<string, { l: string; c: string }> = {
		manual: { l: '手动', c: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
		excel: { l: 'Excel', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		agent: { l: 'AI', c: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' }
	};
	const paramTypeMap: Record<string, { l: string; c: string }> = {
		input: { l: '输入', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		output: { l: '输出', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		config: { l: '配置', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' }
	};
	const caseTypeMap: Record<string, { l: string; c: string }> = {
		functional: { l: '功能', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		boundary: { l: '边界', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
		exception: { l: '异常', c: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' },
		performance: { l: '性能', c: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' }
	};
	const INACTIVE = 'bg-gray-100 dark:bg-gray-700 text-gray-500';
	let isTableView = $derived(config.editorType === 'table');
	let isFormView = $derived(config.editorType === 'form');
	let isRichView = $derived(config.editorType === 'rich');
	let isMindmapView = $derived(config.editorType === 'mindmap');
	let isCompetitorView = $derived(config.editorType === 'competitor');

	// Roadmap view toggle
	let roadmapView = $state<'table' | 'gantt'>('table');
	let ganttTimeScale = $state<'day' | 'week' | 'month'>('week');
	let ganttViewOffset = $state(0);

	const nodeTypeMap: Record<string, { l: string; c: string }> = {
		milestone: { l: '里程碑', c: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' },
		feature: { l: '功能', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		release: { l: '发布', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' }
	};
	const nodeStatusMap: Record<string, { l: string; c: string }> = {
		planned: { l: '计划中', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' },
		in_progress: { l: '进行中', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
		completed: { l: '已完成', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		delayed: { l: '延期', c: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' }
	};
	const probMap: Record<string, { l: string; c: string }> = {
		high: { l: '高', c: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' },
		medium: { l: '中', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
		low: { l: '低', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' }
	};
	const resultMap: Record<string, { l: string; c: string }> = {
		pass: { l: '通过', c: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
		fail: { l: '不通过', c: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' },
		partial: { l: '部分通过', c: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' }
	};
	function prioBtnCls(p: string) { return newPriority === p ? (prioMap[p]?.c || '') : INACTIVE; }
	function srcBtnCls(s: string) { return newSource === s ? (sourceMap[s]?.c || '') : INACTIVE; }
	function ptBtnCls(pt: string) { return newParamType === pt ? (paramTypeMap[pt]?.c || '') : INACTIVE; }
	function ctBtnCls(ct: string) { return newCaseType === ct ? (caseTypeMap[ct]?.c || '') : INACTIVE; }

	// Table inline edit drawer
	let showEditDrawer = $state(false);
	let editDrawerEntry = $state<any>(null);
	let editTitle = $state('');
	let editContent = $state('');
	let editPriority = $state<Priority>('p2');
	let editStatus = $state<ModuleStatus>('draft');
	let editSource = $state<string>('manual');
	let editCategory = $state('');
	let editVersionId = $state<string>('');

	function openEditDrawer(entry: any) {
		editDrawerEntry = entry;
		editTitle = entry.title || '';
		editContent = entry.content || '';
		editPriority = entry.priority || 'p2';
		editStatus = entry.status || 'draft';
		editSource = getEntryData(entry, 'source') || 'manual';
		editCategory = getEntryData(entry, 'category') || '';
		editVersionId = getEntryData(entry, 'versionId') || entry.versionId || '';
		showEditDrawer = true;
	}

	async function saveEditDrawer() {
		if (!editDrawerEntry) return;
		try {
			const token = localStorage.token || '';
			const data: Record<string, unknown> = {
				title: editTitle,
				content: editContent || undefined,
				status: editStatus,
				priority: editPriority
			};
			if (moduleType === 'requirement') {
				data.data = { source: editSource, category: editCategory };
			} else if (moduleType === 'roadmap') {
				data.data = { ...(editDrawerEntry.data || {} ) };
			} else if (moduleType === 'testcase') {
				data.data = { ...(editDrawerEntry.data || {} ) };
			} else if (moduleType === 'parameter') {
				data.data = { ...(editDrawerEntry.data || {} ) };
			} else if (moduleType === 'prototype' || moduleType === 'schedule') {
				data.data = { ...(editDrawerEntry.data || {} ) };
			}
			// Preserve versionId from data if present
			const drawerVersionId = editDrawerEntry.data?.versionId || editDrawerEntry.versionId;
			if (drawerVersionId) {
				data.versionId = drawerVersionId;
				if (data.data && typeof data.data === 'object') {
					(data.data as Record<string, unknown>).versionId = drawerVersionId;
				}
			}
			await updateEntry(token, editDrawerEntry.id, data);
			showEditDrawer = false;
			editDrawerEntry = null;
			await loadEntries();
			toast.success('更新成功');
		} catch (e: any) {
			toast.error(e.message || '更新失败');
		}
	}

	// Rich-text entry editor
	let editingEntryId = $state<string | null>(null);
	let editingEntry = $state<any>(null);
	let editingSections = $state<PRDSection[]>([]);
	let editingActiveSection = $state<string>('');
	let editingDocTitle = $state('');
	let editingDocStatus = $state<ModuleStatus>('draft');
	let editingContentHtml = $state('');
	let editingContentMd = $state('');
	let editingContentJson = $state('');
	let showVersionCompare = $state(false);
	let showBranchDialog = $state(false);
	let showMergePanel = $state(false);
	let autoSaveTimer: ReturnType<typeof setTimeout> | null = $state(null);
	let saveStatus = $state<'saved' | 'unsaved' | 'auto-saving'>('saved');
	let lastAutoSaveTime = $state<number>(0);
	let showSaveVersionDialog = $state(false);
	const defaultSections: PRDSection[] = [
		{ id: '1', type: 'overview', title: '概述', content: '', parameters: [], order: 0 },
		{ id: '2', type: 'background', title: '背景', content: '', parameters: [], order: 1 },
		{ id: '3', type: 'goal', title: '目标', content: '', parameters: [], order: 2 },
		{ id: '4', type: 'requirement', title: '需求', content: '', parameters: [], order: 3 },
		{ id: '5', type: 'non_functional', title: '非功能需求', content: '', parameters: [], order: 4 },
		{ id: '6', type: 'appendix', title: '附录', content: '', parameters: [], order: 5 }
	];
	const sectionTypeLabels: Record<string, string> = { overview: '概述', background: '背景', goal: '目标', requirement: '需求', non_functional: '非功能', appendix: '附录' };

	async function openEntryEditor(entryId: string) {
		try {
			const token = localStorage.token || '';
			editingEntry = await getEntry(token, entryId);
			editingDocTitle = editingEntry.title;
			editingDocStatus = editingEntry.status || 'draft';
			editingVersionId = getEntryData(editingEntry, 'versionId') || editingEntry.versionId || '';

			if (moduleType === 'prd') {
				const data = editingEntry.data || editingEntry.metadata || {};
				editingSections = data.sections?.length ? data.sections : [...defaultSections];
				editingActiveSection = editingSections[0]?.id || '';
				// Load the active section content into the rich editor
				const sec = editingSections.find(s => s.id === editingActiveSection);
				editingContentHtml = sec?.content || '';
				editingContentMd = '';
				editingContentJson = '';
			} else if (isFormView || isMindmapView) {
				editingContentHtml = editingEntry.content || '';
				editingContentMd = '';
				editingContentJson = '';
				editingSections = [];
				editingActiveSection = '';
			} else {
				editingContentHtml = editingEntry.content || '';
				editingContentMd = '';
				editingContentJson = '';
				editingSections = [];
				editingActiveSection = '';
			}
			editingEntryId = entryId;
		} catch (e: any) {
			toast.error(e.message || '加载文档失败');
		}
	}

	function closeEntryEditor() {
		editingEntryId = null;
		editingEntry = null;
		editingSections = [];
		editingActiveSection = '';
		editingContentHtml = '';
		editingContentMd = '';
		editingContentJson = '';
		editingVersionId = '';
		if (autoSaveTimer) { clearTimeout(autoSaveTimer); autoSaveTimer = null; }
		saveStatus = 'saved';
	}

	let AUTO_SAVE_DELAY = 30000; // 30 seconds

	function triggerAutoSave() {
		if (!editingEntryId) return;
		if (autoSaveTimer) clearTimeout(autoSaveTimer);
		autoSaveTimer = setTimeout(async () => {
			if (!editingEntryId) return;
			saveStatus = 'auto-saving';
			await saveEntryContentOnly();
			lastAutoSaveTime = Date.now();
			saveStatus = 'saved';
		}, AUTO_SAVE_DELAY);
	}

	async function saveEntryContentOnly() {
		if (!editingEntryId) return;
		try {
			const token = localStorage.token || '';
			if (moduleType === 'prd') {
				const idx = editingSections.findIndex(s => s.id === editingActiveSection);
				if (idx >= 0) {
					editingSections[idx] = { ...editingSections[idx], content: editingContentMd || editingContentHtml };
					editingSections = [...editingSections];
				}
				const autoPrdVid = editingVersionId || editingEntry?.data?.versionId || '';
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle, status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: { sections: editingSections, versionId: autoPrdVid },
					versionId: autoPrdVid
				});
			} else {
				const autoVid = editingVersionId || editingEntry?.data?.versionId || '';
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle, status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: { ...(editingEntry?.data || {}), versionId: autoVid },
					versionId: autoVid
				});
			}
		} catch (e: any) {
			console.warn('[PM] auto-save failed:', e?.message);
		}
	}

	function switchPrdSection(sectionId: string) {
		// Save current section
		const idx = editingSections.findIndex(s => s.id === editingActiveSection);
		if (idx >= 0) {
			editingSections[idx] = { ...editingSections[idx], content: editingContentMd || editingContentHtml };
			editingSections = [...editingSections];
		}
		// Load new section
		editingActiveSection = sectionId;
		const sec = editingSections.find(s => s.id === sectionId);
		editingContentHtml = sec?.content || '';
		editingContentMd = '';
		editingContentJson = '';
	}

	// PRD MD import
	let mdFileInput: HTMLInputElement | null = $state(null);

	function handleMdImport() {
		mdFileInput?.click();
	}

	async function onMdFileSelected(e: Event) {
		const file = (e.target as HTMLInputElement).files?.[0];
		if (!file) return;
		const ext = file.name.split('.').pop()?.toLowerCase();
		try {
			let html = '';
			if (ext === 'docx' || ext === 'doc') {
				const arrayBuffer = await file.arrayBuffer();
				const result = await mammoth.convertToHtml({ arrayBuffer });
				html = result.value;
			} else if (ext === 'md' || ext === 'markdown' || ext === 'txt') {
				const text = await file.text();
				html = await marked.parse(text) as string;
			} else {
				toast.info('不支持的文件格式，请使用 .md / .txt / .docx / .doc');
				if (mdFileInput) mdFileInput.value = '';
				return;
			}
			// Import full text directly into the rich text editor
			if (editingContentHtml) {
				editingContentHtml = editingContentHtml + '<br/><br/>' + html;
			} else {
				editingContentHtml = html;
			}
			editingContentMd = '';
			editingContentJson = '';
			toast.success(`已导入文档：${file.name}`);
		} catch (e: any) {
			toast.error(e.message || '导入失败');
		}
		// Reset file input
		if (mdFileInput) mdFileInput.value = '';
	}

	async function saveEntryDoc() {
		if (!editingEntryId) return;
		try {
			const token = localStorage.token || '';
			if (moduleType === 'prd') {
				// Save the current section content back
				const idx = editingSections.findIndex(s => s.id === editingActiveSection);
				if (idx >= 0) {
					editingSections[idx] = { ...editingSections[idx], content: editingContentMd || editingContentHtml };
					editingSections = [...editingSections];
				}
				const prdVersionId = editingVersionId || $currentVersion?.id || '';
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: { sections: editingSections, versionId: prdVersionId },
					versionId: prdVersionId
				});
			} else if (isFormView && editingEntry) {
				const formVersionId = editingVersionId || $currentVersion?.id || '';
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: { ...editingEntry.data, versionId: formVersionId },
					versionId: formVersionId
				});
			} else if (isCompetitorView && editingEntry) {
				const compVersionId = editingVersionId || $currentVersion?.id || '';
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: { ...editingEntry.data, versionId: compVersionId },
					versionId: compVersionId
				});
			} else {
				const richVersionId = editingVersionId || $currentVersion?.id || '';
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: { ...(editingEntry?.data || {}), versionId: richVersionId },
					versionId: richVersionId
				});
			}
			toast.success('保存成功');
			await loadEntries();
			showSaveVersionDialog = true;
		} catch (e: any) {
			toast.error(e.message || '保存失败');
		}
	}

	async function saveAsNewVersion() {
		if (!editingEntryId) return;
		try {
			const currentVer = $currentVersion;
			await createEntryVersion(projectId, editingEntryId, {
				changeSummary: `保存: ${editingDocTitle}`,
				branchName: editingEntry?.branchName || 'main',
				projectVersionId: currentVer?.id
			});
			toast.success('新版本已创建');
		} catch (e: any) {
			console.warn('[PM] version creation failed:', e?.message);
		}
	}

	// Sync single entry to calendar
	async function syncSingleToCalendar(entry: any) {
		try {
			const d = entry.data || entry.metadata || {};
			if (d.calendarEventId) { toast.info('该条目已同步到日程'); return; }
			const token = localStorage.token || '';
			const calendars = await getCalendars(token);
			if (!calendars || calendars.length === 0) { toast.error('没有可用的日历，请先创建日历'); return; }
			const defaultCal = calendars.find((c: any) => c.is_default) || calendars[0];
			if (!defaultCal) { toast.error('没有可用的日历，请先创建日历'); return; }
			const startDate = d.startDate ? new Date(d.startDate) : null;
			const endDate = d.endDate ? new Date(d.endDate) : (startDate ? new Date(startDate.getTime() + 86400000) : null);
			if (!startDate) { toast.info('该条目没有日期，无法同步到日程'); return; }
			const nodeType = d.nodeType || 'feature';
			const nodeStatus = d.nodeStatus || 'planned';
			const typeLabel = nodeTypeMap[nodeType]?.l || nodeType;
			const statusLabel = nodeStatusMap[nodeStatus]?.l || nodeStatus;
			const assignee = d.assignee || '';
			const result = await createCalendarEvent(token, {
				calendar_id: defaultCal.id,
				title: `${entry.title} - ${typeLabel} - ${statusLabel}`,
				description: `${moduleType === 'roadmap' ? '路线图' : '排期'}同步: ${entry.title} (${typeLabel}, ${statusLabel})${assignee ? ' · 负责人: ' + assignee : ''}`,
				start_at: Math.floor(startDate.getTime() / 1000),
				end_at: Math.floor((endDate || new Date(startDate.getTime() + 86400000)).getTime() / 1000),
				all_day: true,
				data: { pm_entry_id: entry.id, project_id: projectId, module_type: moduleType }
			});
			// Mark as synced to prevent duplicates
			const updatedData = { ...(entry.data || {}) };
			updatedData.calendarEventId = result.id;
			await updateEntry(token, entry.id, { data: updatedData });
			toast.success('已同步到日程');
			await loadEntries();
		} catch (e: any) {
			console.error('[PM] syncSingleToCalendar error:', e);
			toast.error(e.message || '同步到日程失败');
		}
	}

	// Traceability side panel
	let showTracePanel = $state(false);
	let traceEntry = $state<any>(null);
	let showTraceGraph = $state(false);

	// Agent chat panel
	let showAgentPanel = $state(false);

	function openTracePanel(entry: any) {
		traceEntry = entry;
		showTracePanel = true;
	}

	function closeTracePanel() {
		showTracePanel = false;
		traceEntry = null;
	}

	// Inline editing for schedule table
	let inlineEditCell = $state<{ entryId: string; field: string } | null>(null);
	let inlineEditValue = $state('');

	function startInlineEdit(entry: any, field: string) {
		if (moduleType !== 'schedule' && moduleType !== 'roadmap') return;
		inlineEditCell = { entryId: entry.id, field };
		const d = entry.data || entry.metadata || {};
		if (field === 'title') inlineEditValue = entry.title;
		else if (field === 'assignee') inlineEditValue = d.assignee || '';
		else if (field === 'startDate') inlineEditValue = d.startDate || '';
		else if (field === 'endDate') inlineEditValue = d.endDate || '';
		else if (field === 'progress') inlineEditValue = String(d.progress || 0);
		else if (field === 'isMilestone') inlineEditValue = String(d.isMilestone || false);
		else if (field === 'status') inlineEditValue = entry.status || 'draft';
		else inlineEditValue = d[field] || '';
	}

	async function saveInlineEdit(entry: any) {
		if (!inlineEditCell) return;
		try {
			const token = localStorage.token || '';
			const data: Record<string, unknown> = {};
			const d = { ...(entry.data || entry.metadata || {}) };
			if (inlineEditCell.field === 'title') {
				data.title = inlineEditValue;
			} else if (inlineEditCell.field === 'status') {
				data.status = inlineEditValue;
			} else if (inlineEditCell.field === 'progress') {
				d.progress = Number(inlineEditValue) || 0;
				data.data = d;
			} else if (inlineEditCell.field === 'isMilestone') {
				d.isMilestone = inlineEditValue === 'true';
				data.data = d;
			} else {
				d[inlineEditCell.field] = inlineEditValue;
				data.data = d;
			}
			await updateEntry(token, entry.id, data);
			inlineEditCell = null;
			await loadEntries();
		} catch (e: any) {
			toast.error(e.message || '更新失败');
			inlineEditCell = null;
		}
	}

	// Product architecture view toggle
	let archView = $state<'cards' | 'mindmap'>('mindmap');

	// Prototype editor tabs
	let protoTab = $state<'design' | 'annotations' | 'review'>('design');
	let newAnnotationText = $state('');

	function addAnnotation() {
		if (!editingEntry || !newAnnotationText.trim()) return;
		const d = { ...(editingEntry.data || {}) };
		const annotations: { id: string; x: number; y: number; text: string }[] = Array.isArray(d.annotations) ? [...d.annotations] : [];
		annotations.push({ id: Date.now().toString(), x: 50, y: 50, text: newAnnotationText.trim() });
		d.annotations = annotations;
		editingEntry = { ...editingEntry, data: d };
		newAnnotationText = '';
	}

	function removeAnnotation(idx: number) {
		if (!editingEntry) return;
		const d = { ...(editingEntry.data || {}) };
		const annotations: { id: string; x: number; y: number; text: string }[] = Array.isArray(d.annotations) ? [...d.annotations] : [];
		annotations.splice(idx, 1);
		d.annotations = annotations;
		editingEntry = { ...editingEntry, data: d };
	}

	// Prototype check item
	let newCheckName = $state('');
	function addCheckItem() {
		if (!editingEntry || !newCheckName.trim()) return;
		const d = { ...(editingEntry.data || {}) };
		const checks: { id: string; name: string; status: string; issue: string }[] = Array.isArray(d.checks) ? [...d.checks] : [];
		checks.push({ id: Date.now().toString(), name: newCheckName.trim(), status: 'pending', issue: '' });
		d.checks = checks;
		editingEntry = { ...editingEntry, data: d };
		newCheckName = '';
	}
	function removeCheckItem(idx: number) {
		if (!editingEntry) return;
		const d = { ...(editingEntry.data || {}) };
		const checks: { id: string; name: string; status: string; issue: string }[] = Array.isArray(d.checks) ? [...d.checks] : [];
		checks.splice(idx, 1);
		d.checks = checks;
		editingEntry = { ...editingEntry, data: d };
	}
	function updateCheckItem(idx: number, field: 'name' | 'status' | 'issue', value: string) {
		if (!editingEntry) return;
		const d = { ...(editingEntry.data || {}) };
		const checks: { id: string; name: string; status: string; issue: string }[] = Array.isArray(d.checks) ? [...d.checks] : [];
		if (checks[idx]) { checks[idx] = { ...checks[idx], [field]: value }; d.checks = checks; editingEntry = { ...editingEntry, data: d }; }
	}

</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>{config.name}</div>
				<div class="text-lg font-medium text-gray-500">{filteredEntries.length}</div>
			</div>
			<div class="flex w-full justify-end gap-1.5">
				<button
					class="px-2 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition font-medium text-sm flex items-center"
					onclick={() => { showAgentPanel = !showAgentPanel; }}
					title="AI 助手"
				>
					<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
					<div class="ml-1 text-xs">AI</div>
				</button>
				{#if moduleType === 'roadmap' || moduleType === 'schedule'}
					<div class="flex items-center gap-2">
						<div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
							<button class="px-2 py-1 text-xs rounded-md transition {roadmapView === 'table' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}" onclick={() => { roadmapView = 'table'; }}>表格</button>
							<button class="px-2 py-1 text-xs rounded-md transition {roadmapView === 'gantt' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}" onclick={() => { roadmapView = 'gantt'; }}>甘特图</button>
						</div>
						{#if roadmapView === 'gantt'}
							<div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
								<button class="px-2 py-1 text-xs rounded-md transition {ganttTimeScale === 'day' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500'}" onclick={() => { ganttTimeScale = 'day'; ganttViewOffset = 0; }}>天</button>
								<button class="px-2 py-1 text-xs rounded-md transition {ganttTimeScale === 'week' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500'}" onclick={() => { ganttTimeScale = 'week'; ganttViewOffset = 0; }}>周</button>
								<button class="px-2 py-1 text-xs rounded-md transition {ganttTimeScale === 'month' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500'}" onclick={() => { ganttTimeScale = 'month'; ganttViewOffset = 0; }}>月</button>
							</div>
							<button class="px-1.5 py-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition" onclick={() => { ganttViewOffset -= 1; }}>◀</button>
							<button class="px-1.5 py-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition" onclick={() => { ganttViewOffset = 0; }}>今天</button>
							<button class="px-1.5 py-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition" onclick={() => { ganttViewOffset += 1; }}>▶</button>
						{/if}
					</div>
				{/if}
				{#if !showNewForm}
					<button class="px-2 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black transition font-medium text-sm flex items-center" onclick={() => { showNewForm = true; }}>
						<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
						<div class="ml-1 text-xs">新建</div>
					</button>
				{/if}
			</div>
		</div>
	</div>

	<div class="py-2 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30">
		<div class="px-3.5 flex flex-1 items-center w-full space-x-2 py-0.5 pb-2">
			<div class="flex flex-1 items-center">
				<div class="self-center ml-1 mr-3"><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></div>
				<input class="w-full text-sm py-1 rounded-r-xl outline-hidden bg-transparent focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-gray-800 pointer-events-auto" bind:value={query} placeholder="搜索..." />
				{#if query}<button class="p-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-900 transition" onclick={() => { query = ''; }} aria-label="清除"><svg class="size-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>{/if}
			</div>
		</div>
		<!-- Filter bar -->
		<div class="px-3.5 flex flex-wrap items-center gap-2 pb-2 text-xs">
			<select class="px-1.5 py-0.5 rounded text-xs bg-gray-50 dark:bg-gray-850 border-0 outline-hidden" bind:value={filterStatus} onchange={() => { currentPage = 1; }}>
				<option value="all">全部状态</option>
				<option value="draft">草稿</option>
				<option value="review">评审中</option>
				<option value="approved">已批准</option>
				<option value="archived">已归档</option>
			</select>
			<select class="px-1.5 py-0.5 rounded text-xs bg-gray-50 dark:bg-gray-850 border-0 outline-hidden" bind:value={filterPriority} onchange={() => { currentPage = 1; }}>
				<option value="all">全部优先级</option>
				<option value="p0">P0</option>
				<option value="p1">P1</option>
				<option value="p2">P2</option>
				<option value="p3">P3</option>
			</select>
			<select class="px-1.5 py-0.5 rounded text-xs bg-gray-50 dark:bg-gray-850 border-0 outline-hidden" bind:value={filterVersion} onchange={() => { currentPage = 1; }}>
				<option value="all">全部版本</option>
				{#each versionOptions() as vn}
					<option value={vn}>{vn}</option>
				{/each}
			</select>
			<div class="flex items-center gap-1 ml-auto text-gray-400">
				<span>排序:</span>
				<button class="px-1.5 py-0.5 rounded transition {sortField === 'updatedAt' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}" onclick={() => toggleSort('updatedAt')}>更新{sortIndicator('updatedAt')}</button>
				<button class="px-1.5 py-0.5 rounded transition {sortField === 'createdAt' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}" onclick={() => toggleSort('createdAt')}>创建{sortIndicator('createdAt')}</button>
				<button class="px-1.5 py-0.5 rounded transition {sortField === 'priority' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}" onclick={() => toggleSort('priority')}>优先{sortIndicator('priority')}</button>
				<button class="px-1.5 py-0.5 rounded transition {sortField === 'versionNumber' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}" onclick={() => toggleSort('versionNumber')}>版本{sortIndicator('versionNumber')}</button>
			</div>
		</div>

		{#if showNewForm}
			<div class="px-3.5 pb-3">
				<div class="border border-gray-200 dark:border-gray-700 rounded-2xl p-3 space-y-2">
					{#if moduleType === 'faq'}
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" placeholder="问题" rows="2" bind:value={newTitle}></textarea>
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" placeholder="答案" rows="3" bind:value={newFormData.answer}></textarea>
						<div class="flex gap-2">
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="受众" bind:value={newFormData.audience} />
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="关联功能（溯源）" bind:value={newFormData.relatedFeatures} />
						</div>
					{:else if moduleType === 'competitor'}
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="竞品名称" bind:value={newTitle} />
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="竞品URL" bind:value={newFormData.competitorUrl} />
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="描述" bind:value={newFormData.description} />
						<div class="flex gap-2">
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="维度1名称" bind:value={newFormData.dim1Name} />
							<input type="number" min="0" max="100" class="w-16 text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden text-center" placeholder="我方" bind:value={newFormData.dim1Our} />
							<input type="number" min="0" max="100" class="w-16 text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden text-center" placeholder="竞品" bind:value={newFormData.dim1Comp} />
						</div>
					{:else if moduleType === 'risk'}
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="风险描述" bind:value={newTitle} />
						<div class="flex gap-2">
							<span class="text-xs text-gray-500 self-center">概率：</span>
							{#each ['high', 'medium', 'low'] as pr}
								<button class="px-1.5 py-0.5 text-xs rounded transition {newFormData.probability === pr ? (probMap[pr]?.c || '') : INACTIVE}" onclick={() => { newFormData.probability = pr; }}>{probMap[pr].l}</button>
							{/each}
						</div>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="影响范围" bind:value={newFormData.impactScope} />
						<select class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newFormData.featureName}>
							<option value="">关联功能块（可选）</option>
							{#each featureOptions as fo}
								<option value={fo}>{fo}</option>
							{/each}
						</select>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="负责人" bind:value={newFormData.owner} />
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="应对措施" rows="2" bind:value={newFormData.measures}></textarea>
						<input type="date" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="截止日期" bind:value={newFormData.deadline} />
					{:else if moduleType === 'acceptance'}
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="验收项" bind:value={newTitle} />
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="验收范围" rows="2" bind:value={newFormData.scope}></textarea>
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="通过项（每行一个）" rows="2" bind:value={newFormData.passedItems}></textarea>
						<div class="flex gap-2">
							<span class="text-xs text-gray-500 self-center">结果：</span>
							{#each ['pass', 'fail', 'partial'] as r}
								<button class="px-1.5 py-0.5 text-xs rounded transition {newFormData.result === r ? (resultMap[r]?.c || '') : INACTIVE}" onclick={() => { newFormData.result = r; }}>{resultMap[r].l}</button>
							{/each}
						</div>
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="遗留问题" rows="2" bind:value={newFormData.remainingIssues}></textarea>
					{:else}
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder={moduleType === 'roadmap' ? '节点名称' : '标题'} bind:value={newTitle} onkeydown={(e) => { if (e.key === 'Enter' && newTitle.trim()) handleCreate(); }} />
						{#if isRichView || moduleType === 'meeting'}
							<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" placeholder="内容（可选）" rows="2" bind:value={newContent}></textarea>
						{/if}
						{#if moduleType === 'meeting'}
							<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="参会人员（逗号分隔）" bind:value={newFormData.participants} />
							<input type="datetime-local" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newFormData.meetingDate} />
							<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="会议结论" rows="2" bind:value={newFormData.conclusions}></textarea>
							<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="待办事项（每行一个）" rows="2" bind:value={newFormData.actionItems}></textarea>
						{/if}
						{#if moduleType !== 'roadmap'}
							<div class="flex items-center gap-2">
								<span class="text-xs text-gray-500">优先级：</span>
								{#each ['p0','p1','p2','p3'] as p}
									<button class="px-1.5 py-0.5 text-xs rounded transition {prioBtnCls(p)}" onclick={() => { newPriority = p as Priority; }}>{prioMap[p].l}</button>
								{/each}
							</div>
						{/if}
					{/if}
					{#if moduleType === 'parameter'}
						<div class="flex items-center gap-2">
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="参数 Key" bind:value={newParamKey} />
							<div class="flex items-center gap-1">
								{#each ['input', 'output', 'config'] as pt}
									<button class="px-1.5 py-0.5 text-xs rounded transition {ptBtnCls(pt)}" onclick={() => { newParamType = pt as any; }}>{paramTypeMap[pt].l}</button>
								{/each}
							</div>
						</div>
						<div class="flex items-center gap-2">
							<select class="text-sm px-2 py-1 bg-gray-50 dark:bg-gray-850 border-0 rounded-lg outline-hidden" bind:value={newDataType}>
								{#each ['string', 'number', 'boolean', 'object', 'array'] as dt}<option value={dt}>{dt}</option>{/each}
							</select>
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="默认值" bind:value={newDefaultValue} />
						</div>
						<div class="flex items-center gap-2">
							<label class="flex items-center gap-1 text-xs text-gray-500"><input type="checkbox" bind:checked={newParamRequired} /> 必填</label>
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="描述" bind:value={newParamDescription} />
						</div>
						<div class="flex gap-2">
							<select class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newSourceDocument}>
								<option value="">来源文档（可选）</option>
								{#each prdEntries as prd (prd.id)}
									<option value={prd.title}>{prd.title}</option>
								{/each}
								<option value="__manual">手动输入...</option>
							</select>
							<select class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newModuleName}>
								<option value="">选择模块</option>
								{#each moduleOptions as mo}
									<option value={mo}>{mo}</option>
								{/each}
							</select>
							<select class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newFeatureName} disabled={!newModuleName}>
								<option value="">选择功能</option>
								{#each featureOptionsForModule as fo}
									<option value={fo}>{fo}</option>
								{/each}
							</select>
						</div>
					{:else if moduleType === 'testcase'}
						<div class="flex items-center gap-1">
							<span class="text-xs text-gray-500">用例类型：</span>
							{#each ['functional', 'boundary', 'exception', 'performance'] as ct}
								<button class="px-1.5 py-0.5 text-xs rounded transition {ctBtnCls(ct)}" onclick={() => { newCaseType = ct as any; }}>{caseTypeMap[ct].l}</button>
							{/each}
						</div>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="测试场景" bind:value={newScenario} />
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="前置条件" rows="2" bind:value={newPrecondition}></textarea>
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="测试步骤" rows="3" bind:value={newSteps}></textarea>
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="输入数据" rows="2" bind:value={newInputData}></textarea>
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="预期结果" rows="2" bind:value={newExpectedResult}></textarea>
						<div class="flex gap-2">
							<select class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newRequirementId}>
								<option value="">关联需求（可选）</option>
								{#each requirementEntries as req (req.id)}
									<option value={req.id}>[{prioMap[req.priority]?.l || 'P2'}] {req.title} ({req.id.slice(0, 6)})</option>
								{/each}
							</select>
							<select class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newParameterId}>
								<option value="">关联参数（可选）</option>
								{#each parameterEntries as param (param.id)}
									<option value={param.id}>{param.title} ({param.id.slice(0, 6)})</option>
								{/each}
							</select>
						</div>
						<div class="flex gap-2">
							<select class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newFeatureName}>
								<option value="">关联功能（可选）</option>
								{#each featureOptions as fo}
									<option value={fo}>{fo}</option>
								{/each}
							</select>
						</div>
					{:else if moduleType === 'requirement'}
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="需求描述" rows="2" bind:value={newDescription}></textarea>
						<div class="flex items-center gap-2">
							<div class="flex items-center gap-1">
								<span class="text-xs text-gray-500">来源：</span>
								{#each ['manual', 'excel', 'agent'] as s}
									<button class="px-1.5 py-0.5 text-xs rounded transition {srcBtnCls(s)}" onclick={() => { newSource = s as any; }}>{sourceMap[s].l}</button>
								{/each}
							</div>
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="分类" bind:value={newCategory} />
						</div>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="标签（逗号分隔）" bind:value={newTags} />
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="用户角色" bind:value={newUserRole} />
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="预期收益" rows="2" bind:value={newExpectedBenefit}></textarea>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="关联模块（逗号分隔）" bind:value={newRelatedModules} />
					{:else if moduleType === 'roadmap'}
						<div class="flex gap-2">
							<select class="text-sm px-2 py-1 bg-gray-50 dark:bg-gray-850 border-0 rounded-lg outline-hidden" bind:value={newNodeType}>
								{#each ['milestone', 'feature', 'release'] as nt}<option value={nt}>{nodeTypeMap[nt].l}</option>{/each}
							</select>
							<select class="text-sm px-2 py-1 bg-gray-50 dark:bg-gray-850 border-0 rounded-lg outline-hidden" bind:value={newNodeStatus}>
								{#each ['planned', 'in_progress', 'completed', 'delayed'] as ns}<option value={ns}>{nodeStatusMap[ns].l}</option>{/each}
							</select>
						</div>
						<div class="flex gap-2">
							<input type="date" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newStartDate} />
							<input type="date" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newEndDate} />
						</div>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="依赖节点ID（逗号分隔）" bind:value={newDependencies} />
						<select class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newVersionId}>
							<option value="">版本（可选）</option>
							{#each $versionList as v (v.id)}
								<option value={v.id}>{v.versionNumber || v.version_number || 'v?'}</option>
							{/each}
						</select>
					{/if}
					<div class="flex justify-end gap-2">
						<button class="px-3 py-1.5 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={resetForm}>取消</button>
						<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-50" onclick={handleCreate} disabled={!newTitle.trim()}>{moduleType === 'faq' ? '添加' : '创建'}</button>
					</div>
				</div>
			</div>
			<input bind:this={mdFileInput} type="file" accept=".md,.markdown,.txt,.docx,.doc" class="hidden" onchange={onMdFileSelected} />
			{/if}

		{#if loadError}
			<div class="py-12 text-center">
				<svg class="w-10 h-10 mx-auto text-red-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
				<p class="text-sm text-red-500 dark:text-red-400">{loadError}</p>
				<button class="mt-3 px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-xl transition" onclick={loadEntries}>重试</button>
			</div>
		{:else if isLoading}
			<div class="flex items-center justify-center py-12"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div></div>
		{:else if filteredEntries.length === 0}
			<div class="py-12 text-center">
				<p class="text-sm text-gray-500 dark:text-gray-400">{query ? '没有找到匹配的条目' : `还没有${config.name}条目`}</p>
				{#if !query && !showNewForm}<button class="mt-3 px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-xl transition" onclick={() => { showNewForm = true; }}>创建第一个条目</button>{/if}
			</div>
		{:else if isTableView && (moduleType === 'roadmap' || moduleType === 'schedule') && roadmapView === 'gantt'}
			{#key filteredEntries}
			{@const ganttEntries = filteredEntries.filter((e: any) => getEntryData(e, 'startDate') && getEntryData(e, 'endDate'))}
			{#if ganttEntries.length === 0}
				<div class="py-8 text-center text-sm text-gray-400">暂无带日期的节点，无法展示甘特图</div>
			{:else}
				{@const allDates = ganttEntries.flatMap((e: any) => [new Date(getEntryData(e, 'startDate')).getTime(), new Date(getEntryData(e, 'endDate')).getTime()])}
				{@const dataMinTs = Math.min(...allDates)}
				{@const dataMaxTs = Math.max(...allDates)}
				{@const scaleMs = ganttTimeScale === 'day' ? 86400000 : ganttTimeScale === 'week' ? 7 * 86400000 : 30 * 86400000}
				{@const viewRangeMs = scaleMs * (ganttTimeScale === 'day' ? 31 : ganttTimeScale === 'week' ? 12 : 12)}
				{@const nowTs = Date.now()}
				{@const viewCenterTs = nowTs + ganttViewOffset * viewRangeMs}
				{@const minTs = Math.min(dataMinTs, viewCenterTs - viewRangeMs / 2)}
				{@const maxTs = Math.max(dataMaxTs, viewCenterTs + viewRangeMs / 2)}
				{@const totalMs = maxTs - minTs || 86400000}
				{@const todayLeft = ((nowTs - minTs) / totalMs) * 100}
				<div class="px-3 pb-3 overflow-x-auto relative" style="min-width: 700px;">
					<!-- Column headers based on time scale -->
					<div class="flex border-b border-gray-200 dark:border-gray-700 mb-1 ml-48 relative h-7">
						{#each (() => {
							const cols: { label: string; left: number; width: number }[] = [];
							const d = new Date(minTs);
							if (ganttTimeScale === 'month') {
								d.setDate(1);
								while (d.getTime() <= maxTs) {
									const mStart = new Date(d.getFullYear(), d.getMonth(), 1);
									const mEnd = new Date(d.getFullYear(), d.getMonth() + 1, 0);
									const left = ((mStart.getTime() - minTs) / totalMs) * 100;
									const right = ((Math.min(mEnd.getTime(), maxTs) - minTs) / totalMs) * 100;
									cols.push({ label: `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}`, left, width: Math.max(right - left, 5) });
									d.setMonth(d.getMonth() + 1);
								}
							} else if (ganttTimeScale === 'week') {
								d.setDate(d.getDate() - d.getDay() + 1);
								while (d.getTime() <= maxTs) {
									const wStart = d.getTime();
									const wEnd = wStart + 7 * 86400000;
									const left = ((wStart - minTs) / totalMs) * 100;
									const right = ((Math.min(wEnd, maxTs) - minTs) / totalMs) * 100;
									cols.push({ label: `${d.getMonth() + 1}/${d.getDate()}`, left, width: Math.max(right - left, 3) });
									d.setDate(d.getDate() + 7);
								}
							} else {
								while (d.getTime() <= maxTs) {
									const dStart = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
									const dEnd = dStart + 86400000;
									const left = ((dStart - minTs) / totalMs) * 100;
									const right = ((Math.min(dEnd, maxTs) - minTs) / totalMs) * 100;
									cols.push({ label: d.getDate() === 1 || cols.length === 0 ? `${d.getMonth() + 1}/${d.getDate()}` : `${d.getDate()}`, left, width: Math.max(right - left, 1) });
									d.setDate(d.getDate() + 1);
								}
							}
							return cols;
						})() as col}
							<div class="text-[10px] text-gray-500 text-center border-r border-gray-100 dark:border-gray-800 py-1 absolute" style="left: {col.left}%; width: {col.width}%;">{col.label}</div>
						{/each}
					</div>
					<!-- Task rows -->
					{#each ganttEntries as entry, i}
						{@const sd = new Date(getEntryData(entry, 'startDate')).getTime()}
						{@const ed = new Date(getEntryData(entry, 'endDate')).getTime()}
						{@const left = ((sd - minTs) / totalMs) * 100}
						{@const width = Math.max(((ed - sd) / totalMs) * 100, 2)}
						{@const ns = getEntryData(entry, 'nodeStatus')}
						{@const nt = getEntryData(entry, 'nodeType')}
						{@const vid = getEntryData(entry, 'versionId')}
						{@const vLabel = vid ? ($versionList.find((v: any) => v.id === vid)?.versionNumber || vid) : ''}
						{@const pg = getEntryData(entry, 'progress') || 0}
						{@const barColor = ns === 'completed' ? 'bg-green-500' : ns === 'in_progress' ? 'bg-blue-500' : ns === 'delayed' ? 'bg-red-500' : 'bg-gray-400'}
						{@const durationDays = Math.ceil((ed - sd) / 86400000)}
						{@const entryDesc = getEntryData(entry, 'description') || ''}
						<div class="flex items-center gap-2 py-1.5 relative" style="min-height: 36px;">
							<!-- Label with duration -->
							<div class="w-48 flex-shrink-0 pr-2 text-right">
								<div class="text-xs text-gray-700 dark:text-gray-300 truncate">{entry.title}</div>
								<div class="text-[10px] text-gray-400">{durationDays}天{entryDesc ? ' · ' + entryDesc.slice(0, 20) : ''}</div>
							</div>
							<!-- Bar area -->
							<div class="flex-1 relative h-7">
								<!-- Grid lines -->
								{#each Array(Math.ceil((maxTs - minTs) / scaleMs) + 1) as _, wi}
									{@const gleft = ((wi * scaleMs) / totalMs) * 100}
									<div class="absolute top-0 bottom-0 border-l border-gray-100 dark:border-gray-800" style="left: {gleft}%;"></div>
								{/each}
								<div class="absolute top-0 h-full {barColor} rounded-md opacity-80 flex items-center px-2 cursor-pointer hover:opacity-100 transition" style="left: {left}%; width: {width}%;" onclick={() => openEditDrawer(entry)} title="{entry.title} ({durationDays}天) {entryDesc}">
									<span class="text-[10px] text-white font-medium truncate">{nodeTypeMap[nt]?.l || ''}{vLabel ? ' · ' + vLabel : ''}{pg ? ` ${pg}%` : ''}</span>
									{#if pg > 0 && pg < 100}
										<div class="absolute bottom-0 left-0 h-1 bg-white/30 rounded-b-md" style="width: {pg}%;"></div>
									{/if}
								</div>
							</div>
						</div>
					{/each}
					<!-- Global today marker spanning all rows -->
					{#if todayLeft >= 0 && todayLeft <= 100}
						<div class="absolute top-0 bottom-0 w-px bg-red-400 dark:bg-red-500 z-20 pointer-events-none" style="left: calc(0.75rem + 12rem + (100% - 12rem - 1.5rem) * {todayLeft} / 100);">
							<div class="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-full text-[9px] text-red-500 font-medium whitespace-nowrap bg-white dark:bg-gray-900 px-1 rounded">今天</div>
						</div>
					{/if}
				</div>
			{/if}
 			{/key}
		{:else if isTableView}
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead><tr class="border-b border-gray-100 dark:border-gray-800">
						{#if config.tableColumns}{#each config.tableColumns as col (col.key)}<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase {col.width || ''}">{col.label}</th>{/each}{/if}
						<th class="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase w-24">操作</th>
					</tr></thead>
					<tbody>{#each pagedEntries as entry (entry.id)}
						<tr class="border-b border-gray-50 dark:border-gray-850/30 hover:bg-gray-50 dark:hover:bg-gray-850 transition">
							{#if config.tableColumns}{#each config.tableColumns as col (col.key)}
								<td class="px-4 py-2.5 {col.width || ''}">
									{#if col.key === 'priority'}
										<span class="px-1.5 py-0.5 rounded text-xs {prioMap[entry.priority]?.c || prioMap.p2.c}">{prioMap[entry.priority]?.l || 'P2'}</span>
									{:else if col.key === 'title'}
										<span class="font-medium text-gray-900 dark:text-gray-100 max-w-xs truncate block">{entry.title}</span>
									{:else if col.key === 'status'}
										<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || statusMap.draft.c}">{statusMap[entry.status]?.l || '草稿'}</span>
									{:else if col.key === 'updatedAt'}
										<span class="text-gray-500 whitespace-nowrap">{formatTime(entry.updated_at || entry.updatedAt)}</span>
									{:else if col.key === 'description'}
										<span class="text-gray-600 dark:text-gray-400 truncate block max-w-32">{entry.content || '-'}</span>
									{:else if col.key === 'source'}
										{@const src = getEntryData(entry, 'source')}
										<span class="px-1.5 py-0.5 rounded text-xs {sourceMap[src]?.c || INACTIVE}">{sourceMap[src]?.l || src || '-'}</span>
									{:else if col.key === 'category'}
										<span class="text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'category') || '-'}</span>
									{:else if col.key === 'userRole'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-20">{getEntryData(entry, 'userRole') || '-'}</span>
									{:else if col.key === 'tags'}
										<div class="flex flex-wrap gap-1">{#each (getEntryData(entry, 'tags') || []) as tag}<span class="px-1 py-0.5 rounded text-[10px] bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">{tag}</span>{/each}</div>
									{:else if col.key === 'precondition'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'precondition') || '-'}</span>
									{:else if col.key === 'steps'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'steps') || '-'}</span>
									{:else if col.key === 'expectedResult'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'expectedResult') || '-'}</span>
									{:else if col.key === 'required'}
										<span class="text-xs text-gray-600 dark:text-gray-400">{getEntryData(entry, 'required') ? '是' : '否'}</span>
									{:else if col.key === 'description'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'description') || '-'}</span>
									{:else if col.key === 'paramKey'}
										<code class="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded font-mono">{getEntryData(entry, 'key') || '-'}</code>
									{:else if col.key === 'paramType'}
										{@const pt = getEntryData(entry, 'paramType')}
										<span class="px-1.5 py-0.5 rounded text-xs {paramTypeMap[pt]?.c || INACTIVE}">{paramTypeMap[pt]?.l || pt || '-'}</span>
									{:else if col.key === 'dataType'}
										<span class="text-xs text-gray-600 dark:text-gray-400 font-mono">{getEntryData(entry, 'dataType') || '-'}</span>
									{:else if col.key === 'defaultValue'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'defaultValue') || '-'}</span>
									{:else if col.key === 'sourceDocument'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-20">{getEntryData(entry, 'sourceDocument') || '-'}</span>
									{:else if col.key === 'moduleName'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-20">{getEntryData(entry, 'moduleName') || '-'}</span>
									{:else if col.key === 'featureName'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-20">{getEntryData(entry, 'featureName') || '-'}</span>
									{:else if col.key === 'caseType'}
										{@const ct = getEntryData(entry, 'caseType')}
										<span class="px-1.5 py-0.5 rounded text-xs {caseTypeMap[ct]?.c || INACTIVE}">{caseTypeMap[ct]?.l || ct || '-'}</span>
									{:else if col.key === 'scenario'}
										<span class="text-gray-600 dark:text-gray-400 truncate block max-w-28">{getEntryData(entry, 'scenario') || '-'}</span>
									{:else if col.key === 'requirementId'}
										{@const rid = getEntryData(entry, 'requirementId')}
										{#if rid}<code class="text-xs px-1 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded font-mono">{rid}</code>{:else}<span class="text-xs text-gray-400">-</span>{/if}
									{:else if col.key === 'parameterId'}
										{@const pid = getEntryData(entry, 'parameterId')}
										{#if pid}<code class="text-xs px-1 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded font-mono">{pid}</code>{:else}<span class="text-xs text-gray-400">-</span>{/if}
									{:else if col.key === 'nodeType'}
										{@const nt = getEntryData(entry, 'nodeType')}
										<span class="px-1.5 py-0.5 rounded text-xs {nodeTypeMap[nt]?.c || INACTIVE}">{nodeTypeMap[nt]?.l || nt || '-'}</span>
									{:else if col.key === 'nodeStatus'}
										{@const ns = getEntryData(entry, 'nodeStatus')}
										<span class="px-1.5 py-0.5 rounded text-xs {nodeStatusMap[ns]?.c || INACTIVE}">{nodeStatusMap[ns]?.l || ns || '-'}</span>
									{:else if col.key === 'currentVersionNumber'}
										{@const cvn = entry.currentVersionNumber}
										{@const entryVid = entry.versionId || getEntryData(entry, 'versionId')}
										{@const isUuid = cvn && /^[0-9a-f]{8}-/i.test(String(cvn))}
										{@const resolvedVid = isUuid ? cvn : entryVid}
										{@const matchedVersion = resolvedVid ? $versionList.find((v: any) => v.id === resolvedVid) : null}
										{@const displayVn = matchedVersion ? (matchedVersion.versionNumber || matchedVersion.version_number) : (!isUuid && cvn ? cvn : '')}
										{#if displayVn}
											<span class="px-1.5 py-0.5 rounded text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">{displayVn}</span>
											{#if entry.branchName && entry.branchName !== 'main'}
												<span class="ml-1 px-1 py-0.5 rounded text-[10px] bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400">{entry.branchName}</span>
											{/if}
										{:else}
											<span class="text-xs text-gray-400">-</span>
										{/if}
									{:else if col.key === 'versionId'}
										{@const vid = getEntryData(entry, 'versionId') || entry.versionId}
										{#if vid}<span class="px-1.5 py-0.5 rounded text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">{$versionList.find((v: any) => v.id === vid)?.versionNumber || vid}</span>{:else}<span class="text-xs text-gray-400">-</span>{/if}
									{:else if col.key === 'startDate' || col.key === 'endDate'}
										{#if (moduleType === 'schedule' || moduleType === 'roadmap') && inlineEditCell?.entryId === entry.id && inlineEditCell?.field === col.key}
											<input type="date" class="text-xs px-1 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 rounded outline-hidden" bind:value={inlineEditValue} onblur={() => saveInlineEdit(entry)} onchange={() => saveInlineEdit(entry)} />
										{:else}
											<span class="text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap cursor-pointer" ondblclick={() => startInlineEdit(entry, col.key)}>{getEntryData(entry, col.key) || '-'}</span>
										{/if}
									{:else if col.key === 'dependencies'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'dependencies') || '-'}</span>
									{:else if col.key === 'protoType'}
										{@const pt = getEntryData(entry, 'protoType')}
										<span class="px-1.5 py-0.5 rounded text-xs {pt === 'image' ? 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400' : pt === 'package' ? 'bg-yellow-50 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400' : 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400'}">{pt === 'image' ? '图片' : pt === 'package' ? '文件包' : pt === 'review' ? '评审记录' : '-'}</span>
									{:else if col.key === 'assignee'}
										{#if (moduleType === 'schedule' || moduleType === 'roadmap') && inlineEditCell?.entryId === entry.id && inlineEditCell?.field === 'assignee'}
											<input type="text" class="w-full text-xs px-1 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 rounded outline-hidden" bind:value={inlineEditValue} onblur={() => saveInlineEdit(entry)} onkeydown={(e) => { if (e.key === 'Enter') saveInlineEdit(entry); if (e.key === 'Escape') { inlineEditCell = null; } }} />
										{:else}
											<span class="text-xs text-gray-600 dark:text-gray-400 cursor-pointer" ondblclick={() => startInlineEdit(entry, 'assignee')}>{getEntryData(entry, 'assignee') || '-'}</span>
										{/if}
									{:else if col.key === 'progress'}
										{#if (moduleType === 'schedule') && inlineEditCell?.entryId === entry.id && inlineEditCell?.field === 'progress'}
											<input type="number" min="0" max="100" class="w-16 text-xs px-1 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 rounded outline-hidden text-center" bind:value={inlineEditValue} onblur={() => saveInlineEdit(entry)} onkeydown={(e) => { if (e.key === 'Enter') saveInlineEdit(entry); if (e.key === 'Escape') { inlineEditCell = null; } }} />
										{:else}
											{@const pg = getEntryData(entry, 'progress') || 0}
											<div class="flex items-center gap-1 cursor-pointer" ondblclick={() => startInlineEdit(entry, 'progress')}><div class="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"><div class="h-full bg-blue-500 rounded-full" style="width: {pg}%"></div></div><span class="text-xs text-gray-500">{pg}%</span></div>
										{/if}
									{:else if col.key === 'isMilestone'}
										{#if getEntryData(entry, 'isMilestone')}<span class="px-1.5 py-0.5 rounded text-xs bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400">★</span>{:else}<span class="text-xs text-gray-400">-</span>{/if}
									{:else}
										<span class="text-xs text-gray-600 dark:text-gray-400">{getEntryData(entry, col.key) || '-'}</span>
									{/if}
								</td>
							{/each}{/if}
							<td class="px-4 py-2.5 text-right"><div class="flex items-center justify-end gap-1">
								{#if moduleType === 'roadmap' || moduleType === 'schedule'}
									<button class="p-1 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition" title="同步到日程" onclick={() => syncSingleToCalendar(entry)}>
										<svg class="size-3.5 text-gray-400 hover:text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75v7.5a2.25 2.25 0 002.25 2.25h13.5A2.25 2.25 0 0021 26.25v-7.5M3 9h18M3 9l9-6 9 6" /></svg>
									</button>
								{/if}
								<button class="p-1 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition" title="溯源信息" onclick={() => openTracePanel(entry)}>
									<svg class="size-3.5 text-gray-400 hover:text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.813a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364l1.757 1.757" /></svg>
								</button>
								<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title="编辑" onclick={() => openEditDrawer(entry)}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg></button>
								<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title="导出为笔记" onclick={() => handleExportToNote(entry)}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm0 5.25h.007v.008H3.75V12zm0 5.25h.007v.008H3.75V17.25z" /></svg></button>
								<button class="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition" title="删除" onclick={() => handleDelete(entry.id)}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg></button>
							</div></td>
						</tr>
					{/each}</tbody>
				</table>
			</div>
	{:else if isFormView || isMindmapView}
		{#if moduleType === 'product-architecture'}
			<!-- View toggle for product architecture -->
			<div class="px-3.5 py-1 flex items-center gap-2 border-b border-gray-100 dark:border-gray-800">
				<span class="text-xs text-gray-500">视图：</span>
				<div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
					<button class="px-2 py-1 text-xs rounded-md transition {archView === 'cards' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500'}" onclick={() => { archView = 'cards'; }}>卡片</button>
					<button class="px-2 py-1 text-xs rounded-md transition {archView === 'mindmap' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500'}" onclick={() => { archView = 'mindmap'; }}>思维导图</button>
				</div>
			</div>
			{#if archView === 'mindmap' && filteredEntries.length > 0}
				<div class="h-[600px]">
					<PMMindMap
						nodes={(() => {
							const allNodes: MindMapNode[] = [];
							for (const entry of filteredEntries) {
								const nodes = (entry.data || entry.metadata || {}).nodes || [];
								allNodes.push(...nodes);
							}
							return allNodes;
						})() as MindMapNode[]}
						onChange={async (updatedNodes: MindMapNode[]) => {
							// Map nodes back to their source entries by matching node IDs
							const nodeToEntry = new Map<string, string>();
							for (const entry of filteredEntries) {
								const entryNodes: MindMapNode[] = (entry.data || entry.metadata || {}).nodes || [];
								for (const n of entryNodes) {
									nodeToEntry.set(n.id, entry.id);
								}
							}
							// Group updated nodes by entry
							const entryNodesMap = new Map<string, MindMapNode[]>();
							for (const node of updatedNodes) {
								const eid = nodeToEntry.get(node.id);
								if (eid) {
									if (!entryNodesMap.has(eid)) entryNodesMap.set(eid, []);
									entryNodesMap.get(eid)!.push(node);
								}
							}
							// Update each entry's nodes
							const token = localStorage.token || '';
							for (const [entryId, nodes] of entryNodesMap) {
								const entry = filteredEntries.find(e => e.id === entryId);
								if (!entry) continue;
								const d = { ...(entry.data || entry.metadata || {}) };
								d.nodes = nodes;
								try {
									await updateEntry(token, entryId, { data: d });
								} catch (e: any) {
									console.warn('[MindMap] save failed for entry', entryId, e?.message);
								}
							}
							await loadEntries();
						}}
						readonly={false}
					/>
				</div>
			{:else}
				<div class="px-2.5 py-1 gap-1.5 flex flex-col">{#each filteredEntries as entry (entry.id)}
					<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
					<div class="flex cursor-pointer w-full px-3.5 py-2 border border-gray-50 dark:border-gray-850/30 bg-transparent dark:hover:bg-gray-850 hover:bg-white rounded-2xl transition group" role="button" tabindex="0" onclick={() => openEntryEditor(entry.id)} onkeydown={(e) => { if (e.key === 'Enter') openEntryEditor(entry.id); }}>
					<div class="w-full flex flex-col justify-between"><div class="flex-1">
							<div class="flex items-center gap-2 self-center justify-between">
								<div class="text-sm font-medium capitalize flex-1 w-full line-clamp-1">{entry.title}</div>
								<div class="flex shrink-0 items-center text-xs gap-2">
														{#if true}
															{@const cardVersionId = getEntryData(entry, 'versionId') || entry.versionId || (entry.currentVersionNumber && /^[0-9a-f]{8}-/i.test(String(entry.currentVersionNumber)) ? entry.currentVersionNumber : '')}
															{@const cardVersion = cardVersionId ? $versionList.find((v: any) => v.id === cardVersionId) : null}
															{@const cardVersionDisplay = cardVersion ? (cardVersion.versionNumber || cardVersion.version_number) : (cardVersionId && !/^[0-9a-f]{8}-/i.test(cardVersionId) ? cardVersionId : '')}
															<span class="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded-full {cardVersionDisplay ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-400'}">
																{cardVersionDisplay || '-'}
															</span>
														{/if}
									{#if entry.priority}<span class="px-1.5 py-0.5 rounded text-xs {prioMap[entry.priority]?.c || ''}">{prioMap[entry.priority]?.l || ''}</span>{/if}
									<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || statusMap.draft.c}">{statusMap[entry.status]?.l || '草稿'}</span>
									<span class="text-gray-500">{formatTime(entry.updated_at || entry.updatedAt)}</span>
									<button class="p-1 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition opacity-0 group-hover:opacity-100" title="溯源" onclick={(e) => { e.stopPropagation(); openTracePanel(entry); }}><svg class="size-3.5 text-gray-400 hover:text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.813a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364l1.757 1.757" /></svg></button>
									<button class="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition opacity-0 group-hover:opacity-100" title="删除" onclick={(e) => { e.stopPropagation(); handleDelete(entry.id); }}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
								</div>
							</div>
							<div class="text-xs text-gray-400 mt-1">🗺️ {(getEntryData(entry, 'nodes') || []).length || 0} 个节点</div>
						</div></div>
					</div>
				{/each}</div>
			{/if}
	{/if}
	{:else}
		<div class="px-2.5 py-1 gap-1.5 flex flex-col">{#each filteredEntries as entry (entry.id)}
				<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
				<div class="flex cursor-pointer w-full px-3.5 py-2 border border-gray-50 dark:border-gray-850/30 bg-transparent dark:hover:bg-gray-850 hover:bg-white rounded-2xl transition group" role="button" tabindex="0" onclick={() => openEntryEditor(entry.id)} onkeydown={(e) => { if (e.key === 'Enter') openEntryEditor(entry.id); }}>
					<div class="w-full flex flex-col justify-between"><div class="flex-1">
						<div class="flex items-center gap-2 self-center justify-between">
							<div class="text-sm font-medium capitalize flex-1 w-full line-clamp-1">{entry.title}</div>
							<div class="flex shrink-0 items-center text-xs gap-2">
														{#if true}
															{@const cardVersionId2 = getEntryData(entry, 'versionId') || entry.versionId || (entry.currentVersionNumber && /^[0-9a-f]{8}-/i.test(String(entry.currentVersionNumber)) ? entry.currentVersionNumber : '')}
															{@const cardVersion2 = cardVersionId2 ? $versionList.find((v: any) => v.id === cardVersionId2) : null}
															{@const cardVersionDisplay2 = cardVersion2 ? (cardVersion2.versionNumber || cardVersion2.version_number) : (cardVersionId2 && !/^[0-9a-f]{8}-/i.test(cardVersionId2) ? cardVersionId2 : '')}
															<span class="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded-full {cardVersionDisplay2 ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-400'}">
																{cardVersionDisplay2 || '-'}
															</span>
														{/if}
								{#if entry.priority}<span class="px-1.5 py-0.5 rounded text-xs {prioMap[entry.priority]?.c || ''}">{prioMap[entry.priority]?.l || ''}</span>{/if}
								<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || statusMap.draft.c}">{statusMap[entry.status]?.l || '草稿'}</span>
								<span class="text-gray-500">{formatTime(entry.updated_at || entry.updatedAt)}</span>
								<button class="p-1 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition opacity-0 group-hover:opacity-100" title="溯源" onclick={(e) => { e.stopPropagation(); openTracePanel(entry); }}><svg class="size-3.5 text-gray-400 hover:text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.813a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364l1.757 1.757" /></svg></button>
								<button class="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition opacity-0 group-hover:opacity-100" title="删除" onclick={(e) => { e.stopPropagation(); handleDelete(entry.id); }}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
							</div>
						</div>
						{#if moduleType === 'faq'}
							<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-1">{getEntryData(entry, 'answer') || ''}</div>
						{:else if moduleType === 'risk'}
							<div class="flex gap-2 mt-1">
								{#if getEntryData(entry, 'probability')}<span class="px-1 py-0.5 rounded text-[10px] {probMap[getEntryData(entry, 'probability')]?.c || ''}">概率:{probMap[getEntryData(entry, 'probability')]?.l || getEntryData(entry, 'probability')}</span>{/if}
								{#if getEntryData(entry, 'impactScope')}<span class="text-[10px] text-gray-500">影响:{getEntryData(entry, 'impactScope')}</span>{/if}
							</div>
						{:else if moduleType === 'competitor'}
							<div class="flex gap-2 mt-1 items-center">
								{#if getEntryData(entry, 'competitorUrl')}<span class="text-[10px] text-blue-500 truncate">{getEntryData(entry, 'competitorUrl')}</span>{/if}
								{#each (getEntryData(entry, 'dimensions') || []).slice(0, 3) as dim}
									<span class="px-1 py-0.5 rounded text-[10px] {dim.ourScore >= dim.competitorScore ? 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400' : 'bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400'}">{dim.name || '维度'} {dim.ourScore}:{dim.competitorScore}</span>
								{/each}
							</div>
						{:else if entry.content}
							<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">{entry.content}</div>
						{/if}
					</div></div>
				</div>
			{/each}</div>
		{/if}
		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="px-3.5 py-3 flex items-center justify-between border-t border-gray-100 dark:border-gray-800">
				<span class="text-xs text-gray-500">共 {filteredEntries.length} 条，第 {currentPage}/{totalPages} 页</span>
				<div class="flex items-center gap-1">
					<button class="px-2 py-1 text-xs rounded-lg transition {currentPage <= 1 ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed' : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'}" onclick={() => { if (currentPage > 1) currentPage--; }} disabled={currentPage <= 1}>上一页</button>
					{#each Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
						if (totalPages <= 7) return i + 1;
						if (currentPage <= 4) return i + 1;
						if (currentPage >= totalPages - 3) return totalPages - 6 + i;
						return currentPage - 3 + i;
					}) as pageNum}
						<button class="px-2 py-1 text-xs rounded-lg transition {currentPage === pageNum ? 'bg-black text-white dark:bg-white dark:text-black font-medium' : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'}" onclick={() => { currentPage = pageNum; }}>{pageNum}</button>
					{/each}
					<button class="px-2 py-1 text-xs rounded-lg transition {currentPage >= totalPages ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed' : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400'}" onclick={() => { if (currentPage < totalPages) currentPage++; }} disabled={currentPage >= totalPages}>下一页</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Entry Editor (rich text, form, mindmap) -->
{#if editingEntryId && (isRichView || isFormView || isMindmapView || isCompetitorView)}
	<div class="fixed inset-0 z-50 bg-white dark:bg-gray-900 flex flex-col">
		<div class="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700">
			<div class="flex items-center gap-3">
				<button class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition" onclick={closeEntryEditor} title="返回">
					<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
				</button>
				<input type="text" class="text-sm font-medium bg-transparent border-0 outline-none flex-1 max-w-md text-gray-900 dark:text-gray-100" bind:value={editingDocTitle} placeholder="标题" />
			</div>
			<div class="flex items-center gap-2">
				{#if moduleType === 'prd'}
					<span class="px-2.5 py-1 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg flex items-center gap-1">
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" /></svg>
						{$currentVersion?.versionNumber || $currentVersion?.version_number || 'v1.0'}
					</span>
					{#if saveStatus === 'unsaved'}
						<span class="px-2 py-1 text-xs text-orange-600 dark:text-orange-400">未保存更改</span>
					{:else if saveStatus === 'auto-saving'}
						<span class="px-2 py-1 text-xs text-blue-500">自动保存中...</span>
					{:else if lastAutoSaveTime > 0}
						<span class="px-2 py-1 text-xs text-gray-400">自动保存于 {new Date(lastAutoSaveTime).toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'})}</span>
					{/if}
					<button class="px-2.5 py-1.5 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition flex items-center gap-1" onclick={handleMdImport}>
						<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>
						导入
					</button>
				{:else}
					<PMVersionHistoryDropdown {projectId} entryId={editingEntryId || ''} currentVersionNumber={editingEntry?.currentVersionNumber} readonly />
				{/if}
				<div class="flex items-center gap-1">
					<button class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition flex items-center gap-1" onclick={() => { showVersionCompare = true; }} title="版本比较">
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
						比较
					</button>
					<button class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition flex items-center gap-1" onclick={() => { showBranchDialog = true; }} title="创建分支">
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
						分支
					</button>
					<button class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition flex items-center gap-1" onclick={() => { showMergePanel = true; }} title="合并分支">
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
						合并
					</button>
				</div>
				<select class="text-xs px-2 py-1 bg-gray-50 dark:bg-gray-800 border-0 rounded-lg outline-hidden" bind:value={editingDocStatus}>
					{#each ['draft', 'review', 'approved', 'archived'] as s}<option value={s}>{statusMap[s]?.l || s}</option>{/each}
				</select>
				<select class="text-xs px-2 py-1 bg-gray-50 dark:bg-gray-800 border-0 rounded-lg outline-hidden" value={editingVersionId} onchange={(e) => { editingVersionId = (e.target as HTMLSelectElement).value; saveStatus = 'unsaved'; }}>
					<option value="">无版本</option>
					{#each $versionList as v (v.id)}
						<option value={v.id}>{v.versionNumber || v.version_number || 'v?'}</option>
					{/each}
				</select>
				<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg font-medium" onclick={saveEntryDoc}>保存</button>
			</div>
		</div>
		<div class="flex flex-1 overflow-hidden">
			{#if moduleType === 'prd'}
				<input bind:this={mdFileInput} type="file" accept=".md,.markdown,.txt,.docx,.doc" class="hidden" onchange={onMdFileSelected} />
				<!-- PRD Section Sidebar -->
				<div class="w-56 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-850 flex flex-col">
					<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
						<h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">文档章节</h3>
					</div>
					<div class="flex-1 overflow-y-auto p-2 space-y-1">
						{#each editingSections as section (section.id)}
							<button
								class="w-full text-left px-3 py-2 text-sm rounded-lg transition {editingActiveSection === section.id ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 font-medium' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
								onclick={() => switchPrdSection(section.id)}
							>
								<div class="flex items-center gap-2">
									<span class="truncate">{section.title}</span>
									{#if section.content?.trim()}
										<span class="w-2 h-2 rounded-full bg-green-400 flex-shrink-0" title="有内容"></span>
									{/if}
								</div>
							</button>
						{/each}
					</div>
				</div>
			{/if}
			<div class="flex-1 overflow-y-auto p-6">
				{#if isFormView && editingEntry}
					<div class="max-w-2xl mx-auto space-y-4">
						{#each (config.formFields || []) as field (field.key)}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{field.label}</label>
								{#if field.type === 'textarea'}
									<textarea
										class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none"
										rows="3"
										value={getEntryData(editingEntry, field.key)}
										oninput={(e) => {
											const d = { ...(editingEntry.data || {}) };
											d[field.key] = (e.target as HTMLTextAreaElement).value;
											editingEntry = { ...editingEntry, data: d };
										}}
									></textarea>
								{:else if field.type === 'select'}
									<select
										class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden"
										value={getEntryData(editingEntry, field.key)}
										onchange={(e) => {
											const d = { ...(editingEntry.data || {}) };
											d[field.key] = (e.target as HTMLSelectElement).value;
											editingEntry = { ...editingEntry, data: d };
										}}
									>
										{#if field.key === 'probability'}
											{#each ['high', 'medium', 'low'] as opt}<option value={opt}>{probMap[opt]?.l || opt}</option>{/each}
										{:else if field.key === 'result'}
											{#each ['pass', 'fail', 'partial'] as opt}<option value={opt}>{resultMap[opt]?.l || opt}</option>{/each}
										{:else if field.key === 'requirementId'}
											<option value="">无</option>
											{#each requirementEntries as req (req.id)}
												<option value={req.id}>[{prioMap[req.priority]?.l || 'P2'}] {req.title}</option>
											{/each}
										{:else if field.key === 'relatedFeatures'}
											<option value="">无</option>
											{#each featureOptions as fo}
												<option value={fo}>{fo}</option>
											{/each}
										{:else if field.key === 'featureName'}
											<option value="">无</option>
											{#each featureOptions as fo}
												<option value={fo}>{fo}</option>
											{/each}
										{:else}
											<option value="">请选择</option>
										{/if}
								</select>
								{:else if field.type === 'combobox'}
									<input
										list={`cb-${field.key}`}
										class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden focus:ring-2 focus:ring-blue-500"
										placeholder={field.placeholder || '选择或输入...'}
										value={getEntryData(editingEntry, field.key)}
										oninput={(e) => {
											const d = { ...(editingEntry.data || {}) };
											d[field.key] = (e.target as HTMLInputElement).value;
											editingEntry = { ...editingEntry, data: d };
										}}
									/>
									<datalist id={`cb-${field.key}`}>
										{#if field.dataSource === 'modules'}
											{#each [...new Set(entries.filter((e: any) => e.moduleType).map((e: any) => {
												const cfg = moduleConfig[e.moduleType as keyof typeof moduleConfig];
												return cfg?.name || e.moduleType;
											}))] as modName}
												<option value={modName} />
											{/each}
										{:else if field.dataSource === 'features'}
											{#each [...new Set(entries
												.filter((e: any) => {
													if (!field.dependsOn) return true;
													const parentVal = getEntryData(editingEntry, field.dependsOn);
													if (!parentVal) return true;
													const modType = Object.entries(moduleConfig).find(([_, v]) => v.name === parentVal)?.[0];
													return !modType || e.moduleType === modType;
												})
												.map((e: any) => e.title)
											)] as featName}
												<option value={featName} />
											{/each}
										{/if}
									</datalist>
					{:else if moduleType === 'prototype'}
						<div class="flex items-center gap-2">
							<span class="text-xs text-gray-500">类型：</span>
							{#each [['image', '图片'], ['package', '文件包'], ['review', '评审记录']] as [val, lbl]}
								<button class="px-1.5 py-0.5 text-xs rounded transition {newProtoType === val ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}" onclick={() => { newProtoType = val as any; }}>{lbl}</button>
							{/each}
						</div>
						{#if newProtoType === 'image' || newProtoType === 'package'}
							<input type="file" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" accept={newProtoType === 'image' ? '.png,.jpg,.jpeg,.gif,.svg,.webp' : '.zip,.rar,.7z,.tar.gz'} onchange={async (e) => { const f = (e.target as HTMLInputElement).files?.[0]; if (f) { try { const reader = new FileReader(); reader.onload = () => { newContent = reader.result as string; }; reader.readAsDataURL(f); } catch { newContent = f.name; } } }} />
						{/if}
						{#if newProtoType === 'review'}
							<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="评审结果" rows="3" bind:value={newContent}></textarea>
						{/if}
					{:else if moduleType === 'schedule'}
						<div class="flex gap-2">
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="负责人" bind:value={newAssignee} />
							<input type="number" class="w-20 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="进度%" min="0" max="100" bind:value={newProgress} />
							<label class="flex items-center gap-1 text-xs text-gray-500"><input type="checkbox" bind:checked={newIsMilestone} /> 里程碑</label>
						</div>
						<div class="flex gap-2">
							<input type="date" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newStartDate} />
							<input type="date" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newEndDate} />
							<select class="text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" bind:value={newScheduleStatus}>
								<option value="draft">草稿</option>
								<option value="in_progress">进行中</option>
								<option value="completed">已完成</option>
								<option value="delayed">延期</option>
							</select>
						</div>
					{:else}
						<input
										type="text"
										class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500"
										value={getEntryData(editingEntry, field.key)}
										oninput={(e) => {
											const d = { ...(editingEntry.data || {}) };
											d[field.key] = (e.target as HTMLInputElement).value;
											editingEntry = { ...editingEntry, data: d };
										}}
									/>
								{/if}
							</div>
						{/each}
						{#if editingEntry.content}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">补充说明</label>
								<p class="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{editingEntry.content}</p>
							</div>
						{/if}
						{#if moduleType === 'prototype'}
							<!-- Prototype tabs: annotations & review -->
							<div class="border-t border-gray-200 dark:border-gray-700 pt-4 mt-2">
								<div class="flex items-center gap-1 mb-3">
									<button class="px-2.5 py-1 text-xs rounded-lg transition {protoTab === 'design' ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}" onclick={() => { protoTab = 'design'; }}>设计</button>
									<button class="px-2.5 py-1 text-xs rounded-lg transition {protoTab === 'annotations' ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}" onclick={() => { protoTab = 'annotations'; }}>标注</button>
									<button class="px-2.5 py-1 text-xs rounded-lg transition {protoTab === 'review' ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}" onclick={() => { protoTab = 'review'; }}>评审</button>
								</div>
								{#if protoTab === 'design'}
									<div class="space-y-3">
										<div>
											<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">原型类型</label>
											<div class="flex items-center gap-2">
												{#each [['image', '图片'], ['package', '文件包'], ['review', '评审记录']] as [val, lbl]}
													<button class="px-1.5 py-0.5 text-xs rounded transition {getEntryData(editingEntry, 'protoType') === val ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}" onclick={() => { const d = { ...(editingEntry.data || {}) }; d.protoType = val; editingEntry = { ...editingEntry, data: d }; }}>{lbl}</button>
												{/each}
											</div>
										</div>
										<div>
											<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">描述</label>
											<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" rows="3" value={editingEntry.content || ''} oninput={(e) => { editingEntry = { ...editingEntry, content: (e.target as HTMLTextAreaElement).value }; }} placeholder="原型描述..."></textarea>
										</div>
									</div>
								{:else if protoTab === 'annotations'}
									<div class="space-y-3">
										<div class="flex items-center gap-2">
											<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="输入标注内容..." bind:value={newAnnotationText} onkeydown={(e) => { if (e.key === 'Enter' && newAnnotationText.trim()) addAnnotation(); }} />
											<button class="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-40" onclick={addAnnotation} disabled={!newAnnotationText.trim()}>添加</button>
										</div>
										{#each (editingEntry.data?.annotations || []) as ann, i (ann.id)}
											<div class="flex items-start gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
												<span class="flex-shrink-0 w-5 h-5 flex items-center justify-center text-[10px] font-bold bg-yellow-200 dark:bg-yellow-800 text-yellow-700 dark:text-yellow-300 rounded-full">{i + 1}</span>
												<span class="flex-1 text-sm text-gray-700 dark:text-gray-300">{ann.text}</span>
												<button class="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 transition" onclick={() => removeAnnotation(i)}>
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
												</button>
											</div>
										{/each}
										{#if !(editingEntry.data?.annotations?.length)}
											<p class="text-xs text-gray-400 text-center py-3">暂无标注，在上方输入框添加</p>
										{/if}
									</div>
								{:else if protoTab === 'review'}
									<div class="space-y-3">
										<div class="flex items-center gap-2">
											<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="输入评审检查项..." bind:value={newCheckName} onkeydown={(e) => { if (e.key === 'Enter' && newCheckName.trim()) addCheckItem(); }} />
											<button class="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-40" onclick={addCheckItem} disabled={!newCheckName.trim()}>添加</button>
										</div>
										{#each (editingEntry.data?.checks || []) as chk, i (chk.id)}
											<div class="p-3 border border-gray-200 dark:border-gray-700 rounded-xl space-y-2">
												<div class="flex items-center gap-2">
													<span class="flex-1 text-sm font-medium text-gray-700 dark:text-gray-300">{chk.name}</span>
													<select class="text-xs px-2 py-1 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg outline-hidden" value={chk.status} onchange={(e) => { updateCheckItem(i, 'status', (e.target as HTMLSelectElement).value); }}>
														<option value="pending">待检查</option>
														<option value="pass">通过</option>
														<option value="fail">不通过</option>
													</select>
													<button class="p-1 text-gray-400 hover:text-red-500 transition" onclick={() => removeCheckItem(i)}>
														<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
													</button>
												</div>
												{#if chk.status === 'fail'}
													<input type="text" class="w-full text-xs px-2 py-1 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg outline-hidden" placeholder="问题描述..." value={chk.issue || ''} oninput={(e) => { updateCheckItem(i, 'issue', (e.target as HTMLInputElement).value); }} />
												{/if}
											</div>
										{/each}
										{#if !(editingEntry.data?.checks?.length)}
											<p class="text-xs text-gray-400 text-center py-3">暂无评审项，在上方输入框添加</p>
										{/if}
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{:else if isCompetitorView && editingEntry}
					<div class="max-w-4xl mx-auto space-y-5">
						<!-- Basic info -->
						<div class="space-y-3">
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">竞品名称</label>
								<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" value={editingEntry.title} oninput={(e) => { editingEntry = { ...editingEntry, title: (e.target as HTMLInputElement).value }; editingDocTitle = (e.target as HTMLInputElement).value; }} />
							</div>
							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">竞品URL</label>
									<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editingEntry, 'competitorUrl')} oninput={(e) => { const d = { ...(editingEntry.data || {}) }; d.competitorUrl = (e.target as HTMLInputElement).value; editingEntry = { ...editingEntry, data: d }; }} placeholder="https://..." />
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
									<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editingEntry, 'description')} oninput={(e) => { const d = { ...(editingEntry.data || {}) }; d.description = (e.target as HTMLInputElement).value; editingEntry = { ...editingEntry, data: d }; }} placeholder="竞品简要描述" />
								</div>
							</div>
						</div>

						<!-- Dimension scoring matrix -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<label class="text-sm font-medium text-gray-700 dark:text-gray-300">维度评分矩阵</label>
								<button class="px-2 py-1 text-xs rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition" onclick={() => {
									const dims = getEntryData(editingEntry, 'dimensions');
									const arr: { name: string; ourScore: number; competitorScore: number; notes: string }[] = Array.isArray(dims) ? [...dims] : [];
									arr.push({ name: '', ourScore: 50, competitorScore: 50, notes: '' });
									const d = { ...(editingEntry.data || {}) }; d.dimensions = arr; editingEntry = { ...editingEntry, data: d };
								}}>+ 添加维度</button>
							</div>
							<div class="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
								<table class="w-full text-sm">
									<thead>
										<tr class="bg-gray-50 dark:bg-gray-800">
											<th class="px-3 py-2 text-left text-xs font-medium text-gray-500 w-36">维度名称</th>
											<th class="px-3 py-2 text-center text-xs font-medium text-gray-500 w-24">我方评分</th>
											<th class="px-3 py-2 text-center text-xs font-medium text-gray-500 w-24">竞品评分</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-gray-500">备注</th>
											<th class="px-3 py-2 w-10"></th>
										</tr>
									</thead>
									<tbody>
										{#each (getEntryData(editingEntry, 'dimensions') || []) as dim, i}
											<tr class="border-t border-gray-100 dark:border-gray-800">
												<td class="px-3 py-2"><input type="text" class="w-full text-sm bg-transparent outline-hidden" value={dim.name || ''} oninput={(e) => { const d = { ...(editingEntry.data || {}) }; const dims = [...(d.dimensions || [])]; dims[i] = { ...dims[i], name: (e.target as HTMLInputElement).value }; d.dimensions = dims; editingEntry = { ...editingEntry, data: d }; }} placeholder="如：用户体验" /></td>
												<td class="px-3 py-2 text-center">
													<input type="number" min="0" max="100" class="w-16 text-sm text-center bg-transparent outline-hidden" value={dim.ourScore ?? 50} oninput={(e) => { const d = { ...(editingEntry.data || {}) }; const dims = [...(d.dimensions || [])]; dims[i] = { ...dims[i], ourScore: Math.min(100, Math.max(0, Number((e.target as HTMLInputElement).value) || 0)) }; d.dimensions = dims; editingEntry = { ...editingEntry, data: d }; }} />
													<div class="mt-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"><div class="h-full bg-blue-500 rounded-full" style="width: {dim.ourScore ?? 50}%"></div></div>
												</td>
												<td class="px-3 py-2 text-center">
													<input type="number" min="0" max="100" class="w-16 text-sm text-center bg-transparent outline-hidden" value={dim.competitorScore ?? 50} oninput={(e) => { const d = { ...(editingEntry.data || {}) }; const dims = [...(d.dimensions || [])]; dims[i] = { ...dims[i], competitorScore: Math.min(100, Math.max(0, Number((e.target as HTMLInputElement).value) || 0)) }; d.dimensions = dims; editingEntry = { ...editingEntry, data: d }; }} />
													<div class="mt-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"><div class="h-full bg-orange-500 rounded-full" style="width: {dim.competitorScore ?? 50}%"></div></div>
												</td>
												<td class="px-3 py-2"><input type="text" class="w-full text-sm bg-transparent outline-hidden" value={dim.notes || ''} oninput={(e) => { const d = { ...(editingEntry.data || {}) }; const dims = [...(d.dimensions || [])]; dims[i] = { ...dims[i], notes: (e.target as HTMLInputElement).value }; d.dimensions = dims; editingEntry = { ...editingEntry, data: d }; }} placeholder="备注" /></td>
												<td class="px-3 py-2">
													<button class="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition" onclick={() => { const d = { ...(editingEntry.data || {}) }; const dims = [...(d.dimensions || [])]; dims.splice(i, 1); d.dimensions = dims; editingEntry = { ...editingEntry, data: d }; }}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
												</td>
											</tr>
										{/each}
										{#if !(getEntryData(editingEntry, 'dimensions') || []).length}
											<tr><td colspan="5" class="px-3 py-4 text-center text-xs text-gray-400">暂无维度，点击上方按钮添加</td></tr>
										{/if}
									</tbody>
								</table>
							</div>
						</div>

						<!-- Analysis conclusion -->
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">分析结论</label>
							<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" rows="4" value={getEntryData(editingEntry, 'analysis')} oninput={(e) => { const d = { ...(editingEntry.data || {}) }; d.analysis = (e.target as HTMLTextAreaElement).value; editingEntry = { ...editingEntry, data: d }; }} placeholder="总结竞品对比分析结论..."></textarea>
						</div>
					</div>
				{:else if isMindmapView}
					<div class="h-full flex flex-col">
						{#if moduleType === 'product-architecture'}
							<div class="flex items-center gap-2 px-3 py-1.5 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
								<span class="text-xs text-gray-500">版本：</span>
								<span class="text-xs font-medium text-gray-700 dark:text-gray-300">{$currentVersion?.versionNumber || $currentVersion?.version_number || '默认版本'}</span>
							</div>
						{/if}
						<div class="flex-1">
							<PMMindMap
								nodes={(editingEntry?.data?.nodes || editingEntry?.metadata?.nodes || []) as MindMapNode[]}
								onChange={(updatedNodes: MindMapNode[]) => {
									if (!editingEntry) return;
									const d = { ...(editingEntry.data || {}) };
									d.nodes = updatedNodes;
									editingEntry = { ...editingEntry, data: d };
								}}
								readonly={false}
							/>
						</div>
					</div>
				{:else}
					<div class="h-full">
						<PMRichEditor
							content={editingContentHtml}
							onChange={(html) => {
								editingContentHtml = html;
								editingContentMd = html;
								// Update current section content in editingSections
								if (moduleType === 'prd' && editingActiveSection) {
									const idx = editingSections.findIndex(s => s.id === editingActiveSection);
									if (idx >= 0) {
										editingSections[idx] = { ...editingSections[idx], content: html };
										editingSections = [...editingSections];
									}
								}
								saveStatus = 'unsaved';
								triggerAutoSave();
							}}
							placeholder="在此编写内容..."
							showToc={true}
						/>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<!-- Table Edit Drawer -->
{#if showEditDrawer && editDrawerEntry}
	<div class="fixed inset-0 z-40 bg-black/30" onclick={() => { showEditDrawer = false; }}></div>
	<div class="fixed z-50 h-full {moduleType === 'roadmap' || moduleType === 'schedule' ? 'inset-0 flex items-center justify-center' : 'top-0 right-0 w-full max-w-md shadow-xl flex flex-col'} bg-white dark:bg-gray-900 transition-transform">
		<div class="{moduleType === 'roadmap' || moduleType === 'schedule' ? 'w-full max-w-lg rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col max-h-[80vh]' : 'flex flex-col h-full'}">
		<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">编辑</h3>
			<button class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition" onclick={() => { showEditDrawer = false; }}>
				<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
			</button>
		</div>
		<div class="flex-1 overflow-y-auto p-4 space-y-3">
			<div>
				<label class="block text-xs font-medium text-gray-500 mb-1">标题</label>
				<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" bind:value={editTitle} />
			</div>
			{#if moduleType === 'requirement'}
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">描述</label>
					<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden resize-none focus:ring-2 focus:ring-blue-500" rows="3" bind:value={editContent}></textarea>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">来源</label>
					<div class="flex gap-1">
						{#each ['manual', 'excel', 'agent'] as s}
							<button class="px-1.5 py-0.5 text-xs rounded transition {editSource === s ? (sourceMap[s]?.c || '') : INACTIVE}" onclick={() => { editSource = s; }}>{sourceMap[s]?.l || s}</button>
						{/each}
					</div>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">分类</label>
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" bind:value={editCategory} />
				</div>
			{:else if moduleType === 'roadmap'}
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">节点类型</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'nodeType')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.nodeType = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						{#each ['milestone', 'feature', 'release'] as nt}<option value={nt}>{nodeTypeMap[nt]?.l || nt}</option>{/each}
					</select>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">状态</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'nodeStatus')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.nodeStatus = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						{#each ['planned', 'in_progress', 'completed', 'delayed'] as ns}<option value={ns}>{nodeStatusMap[ns]?.l || ns}</option>{/each}
					</select>
				</div>
				<div class="flex gap-2">
					<div class="flex-1">
						<label class="block text-xs font-medium text-gray-500 mb-1">开始日期</label>
						<input type="date" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'startDate')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.startDate = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
					</div>
					<div class="flex-1">
						<label class="block text-xs font-medium text-gray-500 mb-1">结束日期</label>
						<input type="date" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'endDate')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.endDate = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
					</div>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">描述</label>
					<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500 resize-none" rows="2" value={editDrawerEntry.content || ''} oninput={(e) => { editDrawerEntry = { ...editDrawerEntry, content: (e.target as HTMLTextAreaElement).value }; }}></textarea>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">版本</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'versionId')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.versionId = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						<option value="">无</option>
						{#each $versionList as v (v.id)}
							<option value={v.id}>{v.versionNumber || v.version_number || 'v?'}</option>
						{/each}
					</select>
				</div>
			{:else if moduleType === 'testcase'}
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">测试场景</label>
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'scenario')} oninput={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.scenario = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">用例类型</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'caseType')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.caseType = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						{#each ['functional', 'boundary', 'exception', 'performance'] as ct}<option value={ct}>{caseTypeMap[ct]?.l || ct}</option>{/each}
					</select>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">关联需求</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'requirementId')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.requirementId = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						<option value="">无</option>
						{#each requirementEntries as req (req.id)}
							<option value={req.id}>[{prioMap[req.priority]?.l || 'P2'}] {req.title}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">关联参数</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'parameterId')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.parameterId = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						<option value="">无</option>
						{#each parameterEntries as param (param.id)}
							<option value={param.id}>{param.title}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">关联功能</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'featureName')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.featureName = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						<option value="">无</option>
						{#each featureOptions as fo}
							<option value={fo}>{fo}</option>
						{/each}
					</select>
				</div>
			{:else if moduleType === 'parameter'}
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">参数 Key</label>
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'key')} oninput={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.key = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">参数类型</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'paramType')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.paramType = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						{#each ['input', 'output', 'config'] as pt}<option value={pt}>{paramTypeMap[pt]?.l || pt}</option>{/each}
					</select>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">数据类型</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'dataType')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.dataType = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						{#each ['string', 'number', 'boolean', 'object', 'array'] as dt}<option value={dt}>{dt}</option>{/each}
					</select>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">默认值</label>
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'defaultValue')} oninput={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.defaultValue = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
				</div>
			{:else if moduleType === 'prototype'}
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">类型</label>
					<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" value={getEntryData(editDrawerEntry, 'protoType')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.protoType = (e.target as HTMLSelectElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }}>
						<option value="image">图片</option>
						<option value="package">文件包</option>
						<option value="review">评审记录</option>
					</select>
				</div>
				{#if getEntryData(editDrawerEntry, 'protoType') === 'review'}
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">评审结果</label>
					<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden resize-none focus:ring-2 focus:ring-blue-500" rows="3" value={editContent} oninput={(e) => { editContent = (e.target as HTMLTextAreaElement).value; }}></textarea>
				</div>
				{/if}
			{:else if moduleType === 'schedule'}
				<div>
					<label class="block text-xs font-medium text-gray-500 mb-1">负责人</label>
					<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'assignee')} oninput={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.assignee = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
				</div>
				<div class="flex gap-2">
					<div class="flex-1">
						<label class="block text-xs font-medium text-gray-500 mb-1">开始日期</label>
						<input type="date" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'startDate')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.startDate = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
					</div>
					<div class="flex-1">
						<label class="block text-xs font-medium text-gray-500 mb-1">结束日期</label>
						<input type="date" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" value={getEntryData(editDrawerEntry, 'endDate')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.endDate = (e.target as HTMLInputElement).value; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
					</div>
				</div>
				<div class="flex gap-2">
					<div class="flex-1">
						<label class="block text-xs font-medium text-gray-500 mb-1">进度</label>
						<input type="number" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden" min="0" max="100" value={getEntryData(editDrawerEntry, 'progress') || 0} oninput={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.progress = Number((e.target as HTMLInputElement).value) || 0; editDrawerEntry = { ...editDrawerEntry, data: d }; }} />
					</div>
					<div class="flex items-end pb-2">
						<label class="flex items-center gap-1 text-xs text-gray-500"><input type="checkbox" checked={getEntryData(editDrawerEntry, 'isMilestone')} onchange={(e) => { const d = { ...(editDrawerEntry.data || {} ) }; d.isMilestone = (e.target as HTMLInputElement).checked; editDrawerEntry = { ...editDrawerEntry, data: d }; }} /> 里程碑</label>
					</div>
				</div>
			{/if}
			<div>
				<label class="block text-xs font-medium text-gray-500 mb-1">优先级</label>
				<div class="flex gap-1">
					{#each ['p0','p1','p2','p3'] as p}
						<button class="px-1.5 py-0.5 text-xs rounded transition {editPriority === p ? (prioMap[p]?.c || '') : INACTIVE}" onclick={() => { editPriority = p as Priority; }}>{prioMap[p]?.l || p}</button>
					{/each}
				</div>
			</div>
			<div>
				<label class="block text-xs font-medium text-gray-500 mb-1">状态</label>
				<select class="w-full text-sm px-2 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg outline-hidden" bind:value={editStatus}>
					{#each ['draft', 'review', 'approved', 'archived'] as s}<option value={s}>{statusMap[s]?.l || s}</option>{/each}
				</select>
			</div>
		</div>
		<div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-2">
			<button class="px-3 py-1.5 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={() => { showEditDrawer = false; }}>取消</button>
			<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg font-medium transition" onclick={saveEditDrawer}>保存</button>
		</div>
		</div>
	</div>
{/if}

<!-- Traceability Side Panel -->
{#if showTracePanel && traceEntry}
	<div class="fixed inset-0 z-40 bg-black/30" onclick={closeTracePanel}></div>
	<div class="fixed top-0 right-0 z-50 w-96 h-full bg-white dark:bg-gray-900 shadow-xl flex flex-col border-l border-gray-200 dark:border-gray-700">
		<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
				<svg class="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.813a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364l1.757 1.757" /></svg>
				溯源信息
			</h3>
			<button class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition" onclick={closeTracePanel}>
				<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
			</button>
		</div>
		<div class="flex-1 overflow-y-auto p-4 space-y-4">
			<div>
				<div class="text-xs font-medium text-gray-500 uppercase mb-2">基本信息</div>
				<div class="space-y-1.5">
					<div class="flex items-center justify-between text-sm"><span class="text-gray-500">标题</span><span class="text-gray-900 dark:text-gray-100 font-medium truncate max-w-52">{traceEntry.title}</span></div>
					<div class="flex items-center justify-between text-sm"><span class="text-gray-500">模块</span><span class="text-gray-900 dark:text-gray-100">{config.name}</span></div>
					<div class="flex items-center justify-between text-sm"><span class="text-gray-500">状态</span><span class="px-1.5 py-0.5 rounded text-xs {statusMap[traceEntry.status]?.c || statusMap.draft.c}">{statusMap[traceEntry.status]?.l || '草稿'}</span></div>
					<div class="flex items-center justify-between text-sm"><span class="text-gray-500">优先级</span><span class="px-1.5 py-0.5 rounded text-xs {prioMap[traceEntry.priority]?.c || prioMap.p2.c}">{prioMap[traceEntry.priority]?.l || 'P2'}</span></div>
					<div class="flex items-center justify-between text-sm"><span class="text-gray-500">创建时间</span><span class="text-gray-900 dark:text-gray-100 text-xs">{dayjs(normalizeTs(traceEntry.created_at || traceEntry.createdAt)).format('YYYY-MM-DD HH:mm')}</span></div>
				</div>
			</div>
			<div>
				<div class="text-xs font-medium text-gray-500 uppercase mb-2">版本信息</div>
				{#if traceEntry.versionId || getEntryData(traceEntry, 'versionId')}
				{@const entryVid = traceEntry.versionId || getEntryData(traceEntry, 'versionId')}
				<span class="px-2 py-1 rounded text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">{$versionList.find((v: any) => v.id === entryVid)?.versionNumber || entryVid}</span>
			{:else}<span class="text-xs text-gray-400">未绑定版本</span>{/if}
			</div>
			<div>
				<div class="text-xs font-medium text-gray-500 uppercase mb-2">来源信息</div>
				<div class="space-y-1.5">
					{#if getEntryData(traceEntry, 'source')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">来源</span><span class="px-1.5 py-0.5 rounded text-xs {sourceMap[getEntryData(traceEntry, 'source')]?.c || INACTIVE}">{sourceMap[getEntryData(traceEntry, 'source')]?.l || getEntryData(traceEntry, 'source')}</span></div>{/if}
					{#if getEntryData(traceEntry, 'sourceDocument')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">来源文档</span><span class="text-gray-900 dark:text-gray-100 text-xs truncate max-w-48">{getEntryData(traceEntry, 'sourceDocument')}</span></div>{/if}
					{#if getEntryData(traceEntry, 'category')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">分类</span><span class="text-gray-900 dark:text-gray-100 text-xs">{getEntryData(traceEntry, 'category')}</span></div>{/if}
				</div>
			</div>
			<div>
				<div class="text-xs font-medium text-gray-500 uppercase mb-2">关联关系</div>
				<div class="space-y-1.5">
					{#if getEntryData(traceEntry, 'requirementId')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">关联需求</span><a href="/pm/{projectId}/requirement" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">{getEntryData(traceEntry, 'requirementId').slice(0, 8)}...</a></div>{/if}
					{#if getEntryData(traceEntry, 'parameterId')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">关联参数</span><a href="/pm/{projectId}/parameter" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">{getEntryData(traceEntry, 'parameterId').slice(0, 8)}...</a></div>{/if}
					{#if getEntryData(traceEntry, 'featureName')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">所属功能</span><span class="text-gray-900 dark:text-gray-100 text-xs">{getEntryData(traceEntry, 'featureName')}</span></div>{/if}
					{#if getEntryData(traceEntry, 'moduleName')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">所属模块</span><span class="text-gray-900 dark:text-gray-100 text-xs">{getEntryData(traceEntry, 'moduleName')}</span></div>{/if}
					{#if !getEntryData(traceEntry, 'requirementId') && !getEntryData(traceEntry, 'parameterId') && !getEntryData(traceEntry, 'featureName') && !getEntryData(traceEntry, 'moduleName')}<span class="text-xs text-gray-400">暂无关联关系</span>{/if}
				</div>
			</div>
			{#if moduleType === 'risk'}
				<div>
					<div class="text-xs font-medium text-gray-500 uppercase mb-2">风险详情</div>
					<div class="space-y-1.5">
						{#if getEntryData(traceEntry, 'probability')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">概率</span><span class="px-1.5 py-0.5 rounded text-xs {probMap[getEntryData(traceEntry, 'probability')]?.c || ''}">{probMap[getEntryData(traceEntry, 'probability')]?.l || '-'}</span></div>{/if}
						{#if getEntryData(traceEntry, 'impactScope')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">影响范围</span><span class="text-gray-900 dark:text-gray-100 text-xs">{getEntryData(traceEntry, 'impactScope')}</span></div>{/if}
						{#if getEntryData(traceEntry, 'owner')}<div class="flex items-center justify-between text-sm"><span class="text-gray-500">负责人</span><span class="text-gray-900 dark:text-gray-100 text-xs">{getEntryData(traceEntry, 'owner')}</span></div>{/if}
					</div>
				</div>
			{/if}
			{#if moduleType === 'competitor' && (getEntryData(traceEntry, 'dimensions') || []).length > 0}
				<div>
					<div class="text-xs font-medium text-gray-500 uppercase mb-2">维度评分</div>
					<div class="space-y-1">
						{#each (getEntryData(traceEntry, 'dimensions') || []) as dim}
							<div class="flex items-center justify-between text-xs"><span class="text-gray-700 dark:text-gray-300">{dim.name || '维度'}</span><span class="{dim.ourScore >= dim.competitorScore ? 'text-green-600' : 'text-orange-600'}">我方 {dim.ourScore} vs 竞品 {dim.competitorScore}</span></div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
		<div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
			<button class="w-full px-3 py-2 text-xs bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition flex items-center justify-center gap-1" onclick={() => { showTraceGraph = true; }}>
				<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
				查看溯源图
			</button>
		</div>
	</div>
{/if}

<!-- Traceability Graph -->
<PMTraceabilityGraph
	isOpen={showTraceGraph}
	entityId={traceEntry?.id || ''}
	{projectId}
	entries={entries}
	onClose={() => { showTraceGraph = false; }}
	onNavigate={(moduleType, entryId) => { showTraceGraph = false; closeTracePanel(); }}
/>

<!-- Agent Chat Panel -->
<PMAgentChatPanel
	isOpen={showAgentPanel}
	onClose={() => { showAgentPanel = false; }}
	{projectId}
	{moduleType}
	entryId={editingEntryId || undefined}
	projectName={$currentProjectName || undefined}
	entryTitle={editingDocTitle || undefined}
	entryContentSummary={(editingContentMd || editingContentHtml || '').slice(0, 200) || undefined}
	onApplyAction={(action) => {
		if (action.type === 'pm.entry.create') {
			const payload = action.payload as Record<string, unknown>;
			showNewForm = true;
			newTitle = (payload.title as string) || '';
			newContent = (payload.content as string) || '';
			toast.success(`AI 建议：${action.label}`);
		} else if (action.type === 'pm.entry.update' && editingEntryId) {
			toast.success(`AI 建议：${action.label}，请手动确认更新`);
		} else {
			toast.success(`AI 建议已记录：${action.label}`);
		}
	}}
/>

<!-- Version Compare Panel -->
{#if showVersionCompare && editingEntryId}
	<PMVersionComparePanel
		{projectId}
		entryId={editingEntryId}
		onClose={() => { showVersionCompare = false; }}
		onRestore={(version) => {
			editingContentHtml = version.content || '';
			editingDocTitle = version.metadata?.title as string || editingDocTitle;
			editingDocStatus = (version.metadata?.status as ModuleStatus) || editingDocStatus;
			showVersionCompare = false;
			toast.success(`已恢复到 ${version.versionNumber}`);
		}}
	/>
{/if}

<!-- Version Branch Dialog -->
{#if showBranchDialog && editingEntryId}
	<PMVersionBranchDialog
		{projectId}
		entryId={editingEntryId}
		onClose={() => { showBranchDialog = false; }}
		onBranchCreated={() => { loadEntries(); }}
	/>
{/if}

<!-- Version Merge Panel -->
{#if showMergePanel && editingEntryId}
	<PMVersionMergePanel
		{projectId}
		entryId={editingEntryId}
		onClose={() => { showMergePanel = false; }}
		onMerged={() => { loadEntries(); }}
	/>
{/if}

<!-- Save Version Dialog -->
<PMSaveVersionDialog
	open={showSaveVersionDialog}
	currentVersionNumber={editingEntry?.currentVersionNumber || 'v1.0'}
	onClose={() => { showSaveVersionDialog = false; }}
	onSaveNewVersion={async () => { showSaveVersionDialog = false; await saveAsNewVersion(); }}
	onSaveContentOnly={() => { showSaveVersionDialog = false; toast.success('内容已保存'); }}
/>
