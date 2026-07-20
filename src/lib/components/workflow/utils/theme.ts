/**
 * Workflow UI Theme Utilities
 *
 * Provides consistent styling following OpenWebUI design system.
 */

export const WORKFLOW_COLORS = {
	// Node colors
	nodeStart: '#4CAF50',
	nodeEnd: '#F44336',
	nodeLLM: '#2196F3',
	nodeAgent: '#9C27B0',
	nodeData: '#FF9800',
	nodeCondition: '#795548',
	nodeLoop: '#607D8B',
	nodeParallel: '#00BCD4',
	nodeMerge: '#009688',
	nodeWebhook: '#FF5722',
	nodePM: '#3F51B5',
	nodeCustom: '#757575',

	// Status colors
	statusCompleted: '#4CAF50',
	statusRunning: '#2196F3',
	statusFailed: '#F44336',
	statusPending: '#9E9E9E',
	statusStopped: '#FF9800',

	// UI colors
	primary: '#3B82F6',
	primaryHover: '#2563EB',
	secondary: '#6B7280',
	success: '#10B981',
	warning: '#F59E0B',
	danger: '#EF4444',
	info: '#3B82F6',

	// Background colors
	bgLight: '#FFFFFF',
	bgDark: '#111827',
	bgLightSecondary: '#F9FAFB',
	bgDarkSecondary: '#1F2937',

	// Text colors
	textLight: '#111827',
	textDark: '#F9FAFB',
	textLightSecondary: '#6B7280',
	textDarkSecondary: '#9CA3AF',

	// Border colors
	borderLight: '#E5E7EB',
	borderDark: '#374151'
} as const;

export const WORKFLOW_TYPOGRAPHY = {
	// Font sizes
	title: 'text-lg font-semibold',
	subtitle: 'text-base font-medium',
	body: 'text-sm',
	caption: 'text-xs',
	small: 'text-xs',

	// Font weights
	bold: 'font-bold',
	semibold: 'font-semibold',
	medium: 'font-medium',
	normal: 'font-normal',

	// Line heights
	tight: 'leading-tight',
	snug: 'leading-snug',
	normal: 'leading-normal',
	relaxed: 'leading-relaxed'
} as const;

export const WORKFLOW_SPACING = {
	xs: 'gap-1',
	sm: 'gap-2',
	md: 'gap-3',
	lg: 'gap-4',
	xl: 'gap-6',
	'2xl': 'gap-8'
} as const;

export const WORKFLOW_SHADOWS = {
	sm: 'shadow-sm',
	md: 'shadow-md',
	lg: 'shadow-lg',
	xl: 'shadow-xl',
	inner: 'shadow-inner',
	none: 'shadow-none'
} as const;

export const WORKFLOW_TRANSITIONS = {
	fast: 'transition-all duration-150',
	normal: 'transition-all duration-200',
	slow: 'transition-all duration-300'
} as const;

/**
 * Get node color based on type
 */
export function getNodeColor(type: string): string {
	const colorMap: Record<string, string> = {
		start: WORKFLOW_COLORS.nodeStart,
		end: WORKFLOW_COLORS.nodeEnd,
		llm_call: WORKFLOW_COLORS.nodeLLM,
		agent_call: WORKFLOW_COLORS.nodeAgent,
		data_transform: WORKFLOW_COLORS.nodeData,
		condition: WORKFLOW_COLORS.nodeCondition,
		loop: WORKFLOW_COLORS.nodeLoop,
		parallel: WORKFLOW_COLORS.nodeParallel,
		merge: WORKFLOW_COLORS.nodeMerge,
		webhook: WORKFLOW_COLORS.nodeWebhook,
		pm_module: WORKFLOW_COLORS.nodePM,
		custom: WORKFLOW_COLORS.nodeCustom
	};
	return colorMap[type] || WORKFLOW_COLORS.nodeCustom;
}

/**
 * Get status color based on status
 */
export function getStatusColor(status: string): string {
	const colorMap: Record<string, string> = {
		completed: WORKFLOW_COLORS.statusCompleted,
		running: WORKFLOW_COLORS.statusRunning,
		failed: WORKFLOW_COLORS.statusFailed,
		pending: WORKFLOW_COLORS.statusPending,
		stopped: WORKFLOW_COLORS.statusStopped
	};
	return colorMap[status] || WORKFLOW_COLORS.statusPending;
}

/**
 * Get status background class
 */
export function getStatusBgClass(status: string): string {
	switch (status) {
		case 'completed':
			return 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400';
		case 'running':
			return 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400';
		case 'failed':
			return 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400';
		case 'stopped':
			return 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400';
		default:
			return 'bg-gray-50 dark:bg-gray-900/20 text-gray-600 dark:text-gray-400';
	}
}

/**
 * Get common button classes
 */
export function getButtonClasses(variant: 'primary' | 'secondary' | 'danger' | 'ghost' = 'primary', size: 'sm' | 'md' | 'lg' = 'md'): string {
	const baseClasses = 'inline-flex items-center justify-center rounded-xl font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';

	const variantClasses = {
		primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 dark:bg-blue-600 dark:hover:bg-blue-700',
		secondary: 'bg-gray-200 text-gray-700 hover:bg-gray-300 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600',
		danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 dark:bg-red-600 dark:hover:bg-red-700',
		ghost: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:ring-gray-500 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800'
	};

	const sizeClasses = {
		sm: 'px-3 py-1.5 text-sm',
		md: 'px-4 py-2 text-sm',
		lg: 'px-6 py-3 text-base'
	};

	return `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`;
}

/**
 * Get common input classes
 */
export function getInputClasses(): string {
	return 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors';
}

/**
 * Get common card classes
 */
export function getCardClasses(): string {
	return 'bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm';
}

/**
 * Get common modal classes
 */
export function getModalClasses(): string {
	return 'bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 shadow-xl';
}

/**
 * Check if dark mode is active
 */
export function isDarkMode(): boolean {
	if (typeof window === 'undefined') return false;
	return document.documentElement.classList.contains('dark');
}

/**
 * Toggle dark mode
 */
export function toggleDarkMode(): void {
	if (typeof window === 'undefined') return;
	const isDark = document.documentElement.classList.contains('dark');
	if (isDark) {
		document.documentElement.classList.remove('dark');
		localStorage.theme = 'light';
	} else {
		document.documentElement.classList.add('dark');
		localStorage.theme = 'dark';
	}
}

/**
 * Initialize dark mode from localStorage
 */
export function initDarkMode(): void {
	if (typeof window === 'undefined') return;
	if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
		document.documentElement.classList.add('dark');
	} else {
		document.documentElement.classList.remove('dark');
	}
}
