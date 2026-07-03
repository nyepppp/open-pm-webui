<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import dayjs from '$lib/dayjs';
	import { getEntries, createEntry, deleteEntry, updateEntry, getEntry } from '$lib/apis/pm/index';
	import { syncEntryToCalendar } from '$lib/apis/pm/calendarSync';
	import PMSyncToCalendarModal from '$lib/components/pm/PMSyncToCalendarModal.svelte';
	import { currentVersion } from '$lib/stores/pm/versionStore';
	import { createNewNote } from '$lib/apis/notes/index';
	import RichTextInput from '$lib/components/common/RichTextInput.svelte';
	import { marked } from 'marked';
	import type { ModuleType, ModuleStatus, Priority, PRDSection, MindMapNode } from '$lib/apis/pm/types';
	import PMMindMap from '$lib/components/pm/PMMindMap.svelte';

	let projectId = $derived($page.params.projectId);
	let moduleType = $derived($page.params.module as ModuleType);

	type EditorType = 'rich' | 'table' | 'form' | 'mindmap';
	interface ModuleConf { name: string; editorType: EditorType; tableColumns?: { key: string; label: string; width?: string }[]; formFields?: { key: string; label: string; type: 'text' | 'textarea' | 'select' }[] }

	const moduleConfig: Record<string, ModuleConf> = {
		requirement: { name: '需求管理', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '标题' },
			{ key: 'description', label: '描述', width: 'w-32' },
			{ key: 'source', label: '来源', width: 'w-16' }, { key: 'category', label: '分类', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }, { key: 'updatedAt', label: '更新', width: 'w-24' }
		]},
		parameter: { name: '参数配置', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '参数名' },
			{ key: 'paramKey', label: 'Key', width: 'w-24' }, { key: 'paramType', label: '类型', width: 'w-16' },
			{ key: 'dataType', label: '数据类型', width: 'w-16' }, { key: 'defaultValue', label: '默认值', width: 'w-20' },
			{ key: 'sourceDocument', label: '来源', width: 'w-20' }, { key: 'moduleName', label: '所属模块', width: 'w-20' },
			{ key: 'featureName', label: '所属功能', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }
		]},
		testcase: { name: '测试用例', editorType: 'table', tableColumns: [
			{ key: 'priority', label: '优先级', width: 'w-16' }, { key: 'title', label: '用例标题' },
			{ key: 'caseType', label: '类型', width: 'w-16' }, { key: 'scenario', label: '场景', width: 'w-24' },
			{ key: 'requirementId', label: '关联需求', width: 'w-20' }, { key: 'parameterId', label: '关联参数', width: 'w-20' },
			{ key: 'status', label: '状态', width: 'w-16' }, { key: 'updatedAt', label: '更新', width: 'w-24' }
		]},
		prd: { name: 'PRD 文档', editorType: 'rich' },
		risk: { name: '风险分析', editorType: 'form', formFields: [
			{ key: 'probability', label: '概率', type: 'select' }, { key: 'impactScope', label: '影响范围', type: 'text' },
			{ key: 'owner', label: '负责人', type: 'text' }, { key: 'measures', label: '应对措施', type: 'textarea' }
		]},
		competitor: { name: '竞品分析', editorType: 'competitor', formFields: [
			{ key: 'competitorUrl', label: '竞品URL', type: 'text' }, { key: 'dimension', label: '分析维度', type: 'text' },
			{ key: 'ourProduct', label: '我方产品', type: 'textarea' }, { key: 'competitorProduct', label: '竞品', type: 'textarea' },
			{ key: 'analysis', label: '分析结论', type: 'textarea' }
		]},
		roadmap: { name: '产品路线图', editorType: 'table', tableColumns: [
			{ key: 'title', label: '节点名称' }, { key: 'nodeType', label: '类型', width: 'w-20' },
			{ key: 'nodeStatus', label: '状态', width: 'w-20' }, { key: 'startDate', label: '开始', width: 'w-24' },
			{ key: 'endDate', label: '结束', width: 'w-24' }, { key: 'dependencies', label: '依赖', width: 'w-24' },
			{ key: 'updatedAt', label: '更新', width: 'w-24' }
		]},
		meeting: { name: '会议纪要', editorType: 'rich' },
		acceptance: { name: '验收报告', editorType: 'form', formFields: [
			{ key: 'scope', label: '验收范围', type: 'textarea' }, { key: 'result', label: '结果', type: 'select' },
			{ key: 'remainingIssues', label: '遗留问题', type: 'textarea' }
		]},
		faq: { name: 'FAQ', editorType: 'form', formFields: [
			{ key: 'question', label: '问题', type: 'textarea' }, { key: 'answer', label: '答案', type: 'textarea' },
			{ key: 'audience', label: '受众', type: 'text' }, { key: 'relatedFeatures', label: '关联功能', type: 'text' }
		]},
		'product-architecture': { name: '产品架构', editorType: 'mindmap' }
	};

	let config = $derived(moduleConfig[moduleType] || { name: '未知模块', editorType: 'rich' as EditorType });
	let entries = $state<any[]>([]);
	let isLoading = $state(true);
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
	let newSourceDocument = $state('');
	let newModuleName = $state('');
	let newFeatureName = $state('');
	// Testcase-specific
	let newCaseType = $state<'functional' | 'boundary' | 'exception' | 'performance'>('functional');
	let newScenario = $state('');
	let newRequirementId = $state('');
	let newParameterId = $state('');
	// Requirement-specific
	let newSource = $state<'manual' | 'excel' | 'agent' | 'prd'>('manual');
	let newCategory = $state('');
	let newDescription = $state('');
	// Roadmap-specific
	let newNodeType = $state<'milestone' | 'feature' | 'release'>('feature');
	let newNodeStatus = $state<'planned' | 'in_progress' | 'completed' | 'delayed'>('planned');
	let newStartDate = $state('');
	let newEndDate = $state('');
	let newDependencies = $state('');
	// Schedule-specific
	let newTaskStatus = $state<'planned' | 'in_progress' | 'completed' | 'delayed'>('planned');
	let newOwner = $state('');
	let newTaskDescription = $state('');
	// Form-specific (FAQ, competitor, risk, acceptance)
	let newFormData = $state<Record<string, string>>({});

	// Testcase related entries for dropdowns
	let requirementEntries = $state<any[]>([]);
	let parameterEntries = $state<any[]>([]);

	async function loadRelatedEntries() {
		if (moduleType !== 'testcase') return;
		try {
			const token = localStorage.token || '';
			requirementEntries = await getEntries(token, projectId, 'requirement');
			parameterEntries = await getEntries(token, projectId, 'parameter');
		} catch {
			requirementEntries = [];
			parameterEntries = [];
		}
	}

	async function loadEntries() { isLoading = true; try { const token = localStorage.token || ''; entries = await getEntries(token, projectId, moduleType); } catch { entries = []; } finally { isLoading = false; } }
	onMount(() => { loadEntries(); });
	$effect(() => { moduleType; showNewForm = false; newFormData = {}; loadEntries(); loadRelatedEntries(); });

	async function handleCreate() {
		if (!newTitle.trim()) return;
		try {
			const token = localStorage.token || '';
			const data: Record<string, unknown> = { module_type: moduleType, title: newTitle, content: newContent || undefined, status: newStatus, priority: newPriority };
			if (moduleType === 'parameter') {
				data.data = { key: newParamKey, paramType: newParamType, dataType: newDataType, defaultValue: newDefaultValue, sourceDocument: newSourceDocument, moduleName: newModuleName, featureName: newFeatureName };
			} else if (moduleType === 'testcase') {
				data.data = { caseType: newCaseType, scenario: newScenario, requirementId: newRequirementId, parameterId: newParameterId };
			} else if (moduleType === 'requirement') {
				data.data = { source: newSource, category: newCategory };
				data.content = newDescription || undefined;
			} else if (moduleType === 'roadmap') {
				data.data = { nodeType: newNodeType, nodeStatus: newNodeStatus, startDate: newStartDate, endDate: newEndDate, dependencies: newDependencies };
			} else if (moduleType === 'schedule') {
				data.data = { taskStatus: newTaskStatus, startDate: newStartDate, endDate: newEndDate, owner: newOwner };
				data.content = newTaskDescription || undefined;
			} else if (moduleType === 'competitor') {
				const dims: { name: string; ourScore: number; competitorScore: number; notes: string }[] = [];
				if (newFormData.dim1Name) dims.push({ name: newFormData.dim1Name, ourScore: Number(newFormData.dim1Our) || 50, competitorScore: Number(newFormData.dim1Comp) || 50, notes: '' });
				data.data = { competitorUrl: newFormData.competitorUrl, description: newFormData.description, dimensions: dims };
			} else if (config.editorType === 'form') {
				data.data = { ...newFormData };
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
		newParamKey = ''; newParamType = 'config'; newDataType = 'string'; newDefaultValue = ''; newSourceDocument = ''; newModuleName = ''; newFeatureName = '';
		newCaseType = 'functional'; newScenario = ''; newRequirementId = ''; newParameterId = '';
		newSource = 'manual'; newCategory = ''; newDescription = '';
		newNodeType = 'feature'; newNodeStatus = 'planned'; newStartDate = ''; newEndDate = ''; newDependencies = '';
		newTaskStatus = 'planned'; newOwner = ''; newTaskDescription = '';
		newFormData = {}; showNewForm = false;
	}
	async function handleDelete(entryId: string) { try { const token = localStorage.token || ''; await deleteEntry(token, entryId); await loadEntries(); toast.success('删除成功'); } catch (e: any) { toast.error(e.message || '删除失败'); } }
	async function handleExportToNote(entry: any) { try { const token = localStorage.token || ''; await createNewNote(token, { title: `[PM] ${entry.title}`, data: { content: { md: entry.content || '', html: '', json: null } }, meta: null, access_grants: [] }); toast.success('已导出为笔记'); } catch (e: any) { toast.error(e.message || '导出失败'); } }
	function handleExportToWorkspace() { toast.info('导出到工作空间功能开发中'); }

	// Calendar sync
	let showSyncModal = $state(false);
	let syncEntryId = $state('');
	let syncEntryTitle = $state('');

	function openSyncModal(entry: any) {
		syncEntryId = entry.id;
		syncEntryTitle = entry.title;
		showSyncModal = true;
	}

	async function handleSyncToCalendar(calendarId: string) {
		if (!syncEntryId) return;
		try {
			const token = localStorage.token || '';
			const result = await syncEntryToCalendar(token, syncEntryId, calendarId);
			if (result.status) {
				const actionText = result.action === 'created' ? '创建' : '更新';
				toast.success(`已${actionText}日历事件`);
				entries = entries.map(e => e.id === syncEntryId ? { ...e, data: { ...e.data, calendarEventId: result.event_id } } : e);
			}
		} catch (e: any) {
			toast.error(e.message || '同步失败');
		} finally {
			showSyncModal = false;
		}
	}

	let filteredEntries = $derived(query ? entries.filter(e => e.title.toLowerCase().includes(query.toLowerCase())) : entries);
	function formatTime(ts: number): string { try { return dayjs(ts / 1_000_000).fromNow(); } catch { return ''; } }
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
		agent: { l: 'AI', c: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' },
		prd: { l: 'PRD', c: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' }
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
	const taskStatusMap: Record<string, { l: string; c: string }> = {
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

	function openEditDrawer(entry: any) {
		editDrawerEntry = entry;
		editTitle = entry.title || '';
		editContent = entry.content || '';
		editPriority = entry.priority || 'p2';
		editStatus = entry.status || 'draft';
		editSource = getEntryData(entry, 'source') || 'manual';
		editCategory = getEntryData(entry, 'category') || '';
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
		try {
			const text = await file.text();
			// Split by ## headings to create sections
			const headingRegex = /^##\s+(.+)$/gm;
			const splits: { title: string; content: string }[] = [];
			let lastIndex = 0;
			let match: RegExpExecArray | null;
			const matches: { index: number; title: string }[] = [];
			while ((match = headingRegex.exec(text)) !== null) {
				matches.push({ index: match.index, title: match[1].trim() });
			}
			if (matches.length === 0) {
				// No ## headings — put entire content in one section
				const html = marked.parse(text) as string;
				splits.push({ title: file.name.replace(/\.(md|markdown|txt)$/, ''), content: html });
			} else {
				// Content before first heading
				if (matches[0].index > 0) {
					const before = text.slice(0, matches[0].index).trim();
					if (before) {
						splits.push({ title: '概述', content: marked.parse(before) as string });
					}
				}
				for (let i = 0; i < matches.length; i++) {
					const start = matches[i].index;
					const end = i < matches.length - 1 ? matches[i + 1].index : text.length;
					const sectionText = text.slice(start, end).trim();
					const html = marked.parse(sectionText) as string;
					splits.push({ title: matches[i].title, content: html });
				}
			}
			// Convert splits to PRDSections
			const newSections: PRDSection[] = splits.map((s, i) => ({
				id: Date.now().toString() + '-' + i,
				type: i === 0 ? 'overview' : i === 1 ? 'background' : 'requirement',
				title: s.title,
				content: s.content,
				parameters: [],
				order: editingSections.length + i
			}));
			editingSections = [...editingSections, ...newSections];
			editingActiveSection = newSections[0]?.id || editingActiveSection;
			editingContentHtml = newSections[0]?.content || '';
			toast.success(`已导入 ${newSections.length} 个章节`);
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
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: { sections: editingSections }
				});
			} else if (isFormView && editingEntry) {
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: editingEntry.data
				});
			} else if (isCompetitorView && editingEntry) {
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml,
					data: editingEntry.data
				});
			} else {
				await updateEntry(token, editingEntryId, {
					title: editingDocTitle,
					status: editingDocStatus,
					content: editingContentMd || editingContentHtml
				});
			}
			toast.success('保存成功');
			await loadEntries();
		} catch (e: any) {
			toast.error(e.message || '保存失败');
		}
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
				{#if moduleType === 'roadmap'}
					<div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
						<button class="px-2 py-1 text-xs rounded-md transition {roadmapView === 'table' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}" onclick={() => { roadmapView = 'table'; }}>表格</button>
						<button class="px-2 py-1 text-xs rounded-md transition {roadmapView === 'gantt' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}" onclick={() => { roadmapView = 'gantt'; }}>甘特图</button>
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
				<input class="w-full text-sm py-1 rounded-r-xl outline-hidden bg-transparent" bind:value={query} placeholder="搜索..." />
				{#if query}<button class="p-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-900 transition" onclick={() => { query = ''; }} aria-label="清除"><svg class="size-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>{/if}
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
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="负责人" bind:value={newFormData.owner} />
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="应对措施" rows="2" bind:value={newFormData.measures}></textarea>
					{:else if moduleType === 'acceptance'}
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500" placeholder="验收项" bind:value={newTitle} />
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="验收范围" rows="2" bind:value={newFormData.scope}></textarea>
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
						<div class="flex gap-2">
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="来源文档" bind:value={newSourceDocument} />
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="所属模块" bind:value={newModuleName} />
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="所属功能" bind:value={newFeatureName} />
						</div>
					{:else if moduleType === 'testcase'}
						<div class="flex items-center gap-1">
							<span class="text-xs text-gray-500">用例类型：</span>
							{#each ['functional', 'boundary', 'exception', 'performance'] as ct}
								<button class="px-1.5 py-0.5 text-xs rounded transition {ctBtnCls(ct)}" onclick={() => { newCaseType = ct as any; }}>{caseTypeMap[ct].l}</button>
							{/each}
						</div>
						<input type="text" class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="测试场景" bind:value={newScenario} />
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
					{:else if moduleType === 'requirement'}
						<textarea class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden resize-none" placeholder="需求描述" rows="2" bind:value={newDescription}></textarea>
						<div class="flex items-center gap-2">
							<div class="flex items-center gap-1">
								<span class="text-xs text-gray-500">来源：</span>
								{#each ['manual', 'excel', 'agent', 'prd'] as s}
									<button class="px-1.5 py-0.5 text-xs rounded transition {srcBtnCls(s)}" onclick={() => { newSource = s as any; }}>{sourceMap[s].l}</button>
								{/each}
							</div>
							<input type="text" class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border-0 rounded-xl outline-hidden" placeholder="分类" bind:value={newCategory} />
						</div>
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
					{/if}
					<div class="flex justify-end gap-2">
						<button class="px-3 py-1.5 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" onclick={resetForm}>取消</button>
						<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-50" onclick={handleCreate} disabled={!newTitle.trim()}>{moduleType === 'faq' ? '添加' : '创建'}</button>
					</div>
		</div>
	</div>
{/if}

<PMSyncToCalendarModal
	bind:show={showSyncModal}
	entryTitle={syncEntryTitle}
	on:sync={(e) => handleSyncToCalendar(e.detail.calendarId)}
/>

		{#if isLoading}
			<div class="flex items-center justify-center py-12"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div></div>
		{:else if filteredEntries.length === 0}
			<div class="py-12 text-center">
				<p class="text-sm text-gray-500 dark:text-gray-400">{query ? '没有找到匹配的条目' : `还没有${config.name}条目`}</p>
				{#if !query && !showNewForm}<button class="mt-3 px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-xl transition" onclick={() => { showNewForm = true; }}>创建第一个条目</button>{/if}
			</div>
		{:else if isTableView && moduleType === 'roadmap' && roadmapView === 'gantt'}
			{#key filteredEntries}
			{@const ganttEntries = filteredEntries.filter((e: any) => getEntryData(e, 'startDate') && getEntryData(e, 'endDate'))}
			{#if ganttEntries.length === 0}
				<div class="py-8 text-center text-sm text-gray-400">暂无带日期的节点，无法展示甘特图</div>
			{:else}
				{@const allDates = ganttEntries.flatMap((e: any) => [new Date(getEntryData(e, 'startDate')).getTime(), new Date(getEntryData(e, 'endDate')).getTime()])}
				{@const minTs = Math.min(...allDates)}
				{@const maxTs = Math.max(...allDates)}
				{@const totalDays = Math.max(1, Math.ceil((maxTs - minTs) / 86400000))}
				{@const dayW = Math.max(20, Math.min(40, 800 / totalDays))}
				{@const barH = 28}
				{@const rowGap = 8}
				{@const headerH = 30}
				{@const svgW = totalDays * dayW + 200}
				{@const svgH = ganttEntries.length * (barH + rowGap) + headerH + 20}
				<div class="overflow-x-auto px-3 pb-3">
					<svg viewBox="0 0 {svgW} {svgH}" class="w-full" style="min-width: {svgW}px;">
						<!-- month headers -->
						{#each (() => {
							const ms: { label: string; x: number; w: number }[] = [];
							const d = new Date(minTs);
							d.setDate(1);
							while (d.getTime() <= maxTs) {
								const mStart = new Date(d.getFullYear(), d.getMonth(), 1);
								const mEnd = new Date(d.getFullYear(), d.getMonth() + 1, 0);
								const sx = Math.max(0, (mStart.getTime() - minTs) / 86400000 * dayW);
								const ex = (Math.min(mEnd.getTime(), maxTs) - minTs) / 86400000 * dayW;
								ms.push({ label: `${d.getFullYear()}/${d.getMonth() + 1}`, x: sx, w: ex - sx });
								d.setMonth(d.getMonth() + 1);
							}
							return ms;
						})() as m}
							<rect x="{m.x}" y="0" width="{m.w}" height="{headerH}" fill="#f3f4f6" rx="2" />
							<text x="{m.x + m.w / 2}" y="{headerH - 8}" text-anchor="middle" font-size="11" fill="#9ca3af">{m.label}</text>
						{/each}
						<!-- week grid lines -->
						{#each Array(Math.ceil(totalDays / 7)) as _, wi}
							{@const x = wi * 7 * dayW}
							<line x1="{x}" y1="{headerH}" x2="{x}" y2="{svgH}" stroke="#e5e7eb" stroke-width="0.5" />
						{/each}
						<!-- task bars -->
						{#each ganttEntries as entry, i}
							{@const sd = new Date(getEntryData(entry, 'startDate')).getTime()}
							{@const ed = new Date(getEntryData(entry, 'endDate')).getTime()}
							{@const startDay = Math.max(0, (sd - minTs) / 86400000)}
							{@const durDays = Math.max(1, (ed - sd) / 86400000)}
							{@const bx = startDay * dayW}
							{@const by = headerH + i * (barH + rowGap)}
							{@const bw = durDays * dayW}
							{@const ns = getEntryData(entry, 'nodeStatus')}
							{@const nt = getEntryData(entry, 'nodeType')}
							{@const color = ns === 'completed' ? '#22c55e' : ns === 'in_progress' ? '#3b82f6' : ns === 'delayed' ? '#ef4444' : '#9ca3af'}
							<text x="{bx - 5}" y="{by + barH / 2 + 4}" text-anchor="end" font-size="11" fill="#374151">{entry.title}</text>
							<rect x="{bx}" y="{by}" width="{bw}" height="{barH}" rx="4" fill="{color}" opacity="0.75" />
							<text x="{bx + 6}" y="{by + barH / 2 + 4}" font-size="10" fill="white" font-weight="500">{nodeTypeMap[nt]?.l || ''}</text>
						{/each}
					</svg>
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
					<tbody>{#each filteredEntries as entry (entry.id)}
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
									{:else if col.key === 'taskStatus'}
										{@const ts = getEntryData(entry, 'taskStatus')}
										<span class="px-1.5 py-0.5 rounded text-xs {taskStatusMap[ts]?.c || INACTIVE}">{taskStatusMap[ts]?.l || ts || '-'}</span>
									{:else if col.key === 'startDate' || col.key === 'endDate'}
										<span class="text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap">{getEntryData(entry, col.key) || '-'}</span>
									{:else if col.key === 'dependencies'}
										<span class="text-xs text-gray-600 dark:text-gray-400 truncate block max-w-24">{getEntryData(entry, 'dependencies') || '-'}</span>
									{:else}
										<span class="text-xs text-gray-600 dark:text-gray-400">{getEntryData(entry, col.key) || '-'}</span>
									{/if}
								</td>
							{/each}{/if}
							<td class="px-4 py-2.5 text-right"><div class="flex items-center justify-end gap-1">
										<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title="编辑" onclick={() => openEditDrawer(entry)}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg></button>
										{#if (moduleType === 'roadmap' || moduleType === 'schedule') && getEntryData(entry, 'startDate')}
											<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title={getEntryData(entry, 'calendarEventId') ? '已同步（点击更新）' : '同步到日历'} onclick={() => openSyncModal(entry)}><svg class="size-3.5 {getEntryData(entry, 'calendarEventId') ? 'text-green-500' : 'text-gray-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" /></svg></button>
										{/if}
								{#if moduleType === 'parameter'}
									<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title="导出到工作空间" onclick={() => handleExportToWorkspace()}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg></button>
								{/if}
								<button class="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition" title="导出为笔记" onclick={() => handleExportToNote(entry)}><svg class="size-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm0 5.25h.007v.008H3.75V12zm0 5.25h.007v.008H3.75V17.25z" /></svg></button>
								<button class="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition" title="删除" onclick={() => handleDelete(entry.id)}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg></button>
							</div></td>
						</tr>
					{/each}</tbody>
				</table>
			</div>
		{:else if isFormView || isMindmapView}
			<div class="px-2.5 py-1 gap-1.5 flex flex-col">{#each filteredEntries as entry (entry.id)}
				<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
				<div class="flex cursor-pointer w-full px-3.5 py-2 border border-gray-50 dark:border-gray-850/30 bg-transparent dark:hover:bg-gray-850 hover:bg-white rounded-2xl transition group" role="button" tabindex="0" onclick={() => openEntryEditor(entry.id)} onkeydown={(e) => { if (e.key === 'Enter') openEntryEditor(entry.id); }}>
					<div class="w-full flex flex-col justify-between"><div class="flex-1">
						<div class="flex items-center gap-2 self-center justify-between">
							<div class="text-sm font-medium capitalize flex-1 w-full line-clamp-1">{entry.title}</div>
							<div class="flex shrink-0 items-center text-xs gap-2">
								{#if entry.priority}<span class="px-1.5 py-0.5 rounded text-xs {prioMap[entry.priority]?.c || ''}">{prioMap[entry.priority]?.l || ''}</span>{/if}
								<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || statusMap.draft.c}">{statusMap[entry.status]?.l || '草稿'}</span>
								<span class="text-gray-500">{formatTime(entry.updated_at || entry.updatedAt)}</span>
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
								{#if (getEntryData(entry, 'dimensions') || []).length > 3}<span class="text-[10px] text-gray-400">+{(getEntryData(entry, 'dimensions') || []).length - 3}</span>{/if}
							</div>
						{:else if moduleType === 'product-architecture'}
							{@const nodeCount = (getEntryData(entry, 'nodes') || []).length}
							<div class="text-xs text-gray-400 mt-1">🗺️ {nodeCount || 0} 个节点</div>
						{:else if entry.content}
							<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">{entry.content}</div>
						{/if}
					</div></div>
				</div>
			{/each}</div>
		{:else}
			<div class="px-2.5 py-1 gap-1.5 flex flex-col">{#each filteredEntries as entry (entry.id)}
				<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
				<div class="flex cursor-pointer w-full px-3.5 py-1.5 border border-gray-50 dark:border-gray-850/30 bg-transparent dark:hover:bg-gray-850 hover:bg-white rounded-2xl transition group" role="button" tabindex="0" onclick={() => openEntryEditor(entry.id)} onkeydown={(e) => { if (e.key === 'Enter') openEntryEditor(entry.id); }}>
					<div class="w-full flex flex-col justify-between"><div class="flex-1">
						<div class="flex items-center gap-2 self-center justify-between">
							<div class="text-sm font-medium capitalize flex-1 w-full line-clamp-1">{entry.title}</div>
							<div class="flex shrink-0 items-center text-xs gap-2">
								{#if entry.priority}<span class="px-1.5 py-0.5 rounded text-xs {prioMap[entry.priority]?.c || ''}">{prioMap[entry.priority]?.l || ''}</span>{/if}
								<span class="px-1.5 py-0.5 rounded text-xs {statusMap[entry.status]?.c || statusMap.draft.c}">{statusMap[entry.status]?.l || '草稿'}</span>
								<span class="text-gray-500">{formatTime(entry.updated_at || entry.updatedAt)}</span>
								<button class="p-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition opacity-0 group-hover:opacity-100" title="删除" onclick={(e) => { e.stopPropagation(); handleDelete(entry.id); }}><svg class="size-3.5 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
							</div>
						</div>
						{#if entry.content}<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">{entry.content}</div>{/if}
					</div></div>
				</div>
			{/each}</div>
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
				<span class="px-2 py-0.5 text-xs rounded {statusMap[editingDocStatus]?.c || statusMap.draft.c}">{statusMap[editingDocStatus]?.l || '草稿'}</span>
			</div>
			<div class="flex items-center gap-2">
				<select class="text-xs px-2 py-1 bg-gray-50 dark:bg-gray-800 border-0 rounded-lg outline-hidden" bind:value={editingDocStatus}>
					{#each ['draft', 'review', 'approved', 'archived'] as s}<option value={s}>{statusMap[s]?.l || s}</option>{/each}
				</select>
				<button class="px-3 py-1.5 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg font-medium" onclick={saveEntryDoc}>保存</button>
			</div>
		</div>
		<div class="flex flex-1 overflow-hidden">
			{#if moduleType === 'prd'}
				<div class="w-56 flex-shrink-0 border-r border-gray-100 dark:border-gray-800 overflow-y-auto p-3">
					<div class="text-xs font-semibold text-gray-500 uppercase mb-2">章节大纲</div>
					<div class="space-y-0.5">
						{#each editingSections as sec (sec.id)}
							<button class="w-full flex items-center gap-2 px-2.5 py-2 text-sm rounded-lg transition text-left {editingActiveSection === sec.id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-medium' : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'}" onclick={() => switchPrdSection(sec.id)}>
								<span class="w-5 h-5 rounded text-[10px] flex items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-500 flex-shrink-0">{sec.order + 1}</span>
								<span class="truncate">{sec.title || sectionTypeLabels[sec.type] || sec.type}</span>
							</button>
						{/each}
					</div>
					<button class="w-full mt-3 px-2.5 py-2 text-xs rounded-lg border border-dashed border-gray-300 dark:border-gray-700 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition" onclick={() => { const ns: PRDSection = { id: Date.now().toString(), type: 'appendix', title: '新章节', content: '', parameters: [], order: editingSections.length }; editingSections = [...editingSections, ns]; editingActiveSection = ns.id; }}>+ 添加章节</button>
					<button class="w-full mt-2 px-2.5 py-2 text-xs rounded-lg border border-dashed border-blue-300 dark:border-blue-700 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition" onclick={handleMdImport}>📥 导入 Markdown</button>
					<input bind:this={mdFileInput} type="file" accept=".md,.markdown,.txt" class="hidden" onchange={onMdFileSelected} />
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
										{:else}
											<option value="">请选择</option>
										{/if}
									</select>
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
					<div class="h-full">
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
				{:else}
					<div class="max-w-3xl mx-auto h-full">
						<RichTextInput
							id="pm-entry-{editingEntryId}"
							className="input-prose-sm h-full"
							bind:value={editingContentJson}
							html={editingContentHtml}
							placeholder="在此编写内容..."
							editable={true}
							richText={true}
							link={true}
							onChange={(content) => {
								editingContentHtml = content.html;
								editingContentMd = content.md;
							}}
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
	<div class="fixed top-0 right-0 z-50 h-full w-full max-w-md bg-white dark:bg-gray-900 shadow-xl flex flex-col transition-transform">
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
						{#each ['manual', 'excel', 'agent', 'prd'] as s}
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
{/if}
