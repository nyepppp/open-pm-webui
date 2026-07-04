import { writable, derived, type Writable, type Readable } from 'svelte/store';
import type { ModuleType, ModuleCategory, ModuleNavItem, ModuleCategoryGroup } from '$lib/apis/pm/types';

// ============================================================================
// Module Navigation Data
// ============================================================================

export const moduleCategories: ModuleCategoryGroup[] = [
	{
		id: 'planning',
		label: '规划',
		icon: 'Map',
		modules: [
			{ id: 'prd', label: 'PRD', icon: 'FileText', category: 'planning', path: '/pm/prd' },
			{ id: 'requirement', label: '需求', icon: 'List', category: 'planning', path: '/pm/requirement' },
			{ id: 'parameter', label: '参数', icon: 'Settings', category: 'planning', path: '/pm/parameter' },
			{ id: 'requirement-boundary', label: '需求边界', icon: 'GitBranch', category: 'planning', path: '/pm/requirement-boundary' },
			{ id: 'flowchart', label: '流程图', icon: 'GitBranch', category: 'planning', path: '/pm/flowchart' },
		]
	},
	{
		id: 'design',
		label: '设计',
		icon: 'Palette',
		modules: [
			{ id: 'testcase', label: '测试用例', icon: 'CheckCircle', category: 'design', path: '/pm/testcase' },
			{ id: 'risk', label: '风险', icon: 'AlertTriangle', category: 'design', path: '/pm/risk' },
			{ id: 'competitor', label: '竞品', icon: 'Users', category: 'design', path: '/pm/competitor' },
			{ id: 'prototype', label: '原型/UI设计', icon: 'Image', category: 'design', path: '/pm/prototype' },
		]
	},
	{
		id: 'execution',
		label: '执行',
		icon: 'Zap',
		modules: [
			{ id: 'roadmap', label: '路线图', icon: 'GitBranch', category: 'execution', path: '/pm/roadmap' },
			{ id: 'meeting', label: '会议', icon: 'MessageSquare', category: 'execution', path: '/pm/meeting' },
			{ id: 'schedule', label: '项目排期', icon: 'Clock', category: 'execution', path: '/pm/schedule' },
		]
	},
	{
		id: 'review',
		label: '复盘',
		icon: 'BarChart',
		modules: [
			{ id: 'acceptance', label: '验收', icon: 'ClipboardCheck', category: 'review', path: '/pm/acceptance' },
			{ id: 'faq', label: 'FAQ', icon: 'HelpCircle', category: 'review', path: '/pm/faq' },
			{ id: 'product-architecture', label: '产品架构', icon: 'Layers', category: 'review', path: '/pm/product-architecture' },
			{ id: 'spec', label: 'SPEC规范', icon: 'FileText', category: 'review', path: '/pm/spec' },
		]
	}
];

// ============================================================================
// State
// ============================================================================

export const currentModule: Writable<ModuleType | null> = writable(null);
export const expandedCategories: Writable<Set<ModuleCategory>> = writable(new Set(['planning']));
export const moduleSearchQuery: Writable<string> = writable('');
export const sidebarCollapsed: Writable<boolean> = writable(false);

// ============================================================================
// Derived Stores
// ============================================================================

export const allModules: Readable<ModuleNavItem[]> = derived(
	[currentModule],
	() => moduleCategories.flatMap((cat: ModuleCategoryGroup) => cat.modules)
);

export const filteredModules: Readable<ModuleNavItem[]> = derived(
	[moduleSearchQuery],
	([$query]) => {
		if (!$query.trim()) {
			return moduleCategories.flatMap((cat: ModuleCategoryGroup) => cat.modules);
		}
		const lowerQuery = $query.toLowerCase();
		return moduleCategories
			.flatMap((cat: ModuleCategoryGroup) => cat.modules)
			.filter((mod: ModuleNavItem) =>
				mod.label.toLowerCase().includes(lowerQuery) ||
				mod.id.toLowerCase().includes(lowerQuery)
			);
	}
);

// ============================================================================
// Actions
// ============================================================================

export function expandCategory(category: ModuleCategory) {
	expandedCategories.update(cats => {
		const newCats = new Set(cats);
		newCats.add(category);
		return newCats;
	});
}

export function collapseCategory(category: ModuleCategory) {
	expandedCategories.update(cats => {
		const newCats = new Set(cats);
		newCats.delete(category);
		return newCats;
	});
}

export function toggleCategory(category: ModuleCategory) {
	expandedCategories.update(cats => {
		const newCats = new Set(cats);
		if (newCats.has(category)) {
			newCats.delete(category);
		} else {
			newCats.add(category);
		}
		return newCats;
	});
}

export function setActiveModule(moduleType: ModuleType) {
	currentModule.set(moduleType);
}

export function isCategoryExpanded(category: ModuleCategory): boolean {
	let expanded = false;
	expandedCategories.subscribe(cats => {
		expanded = cats.has(category);
	})();
	return expanded;
}
