<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { moduleCategories, expandedCategories, toggleCategory, setActiveModule, sidebarCollapsed, type ModuleCategory } from '$lib/stores/pm/moduleStore';
	import type { ModuleType } from '$lib/apis/pm/types';

	// Props
	interface Props {
		projectId?: string;
	}

	let { projectId = '' }: Props = $props();

	// Track active module from URL
	let activeModule: ModuleType | null = $derived($page.params.module as ModuleType || null);

	// Track sidebar collapsed state
	let isCollapsed = $derived($sidebarCollapsed);

	// Keyboard navigation state
	let focusedIndex = $state(-1); // -1 means no focus in nav

	// Build a flat list of all focusable items (categories + modules) for keyboard navigation
	interface NavItem {
		type: 'category' | 'module';
		id: string;
		categoryId?: ModuleCategory;
		path?: string;
		moduleType?: ModuleType;
	}

	let flatNavItems = $derived(() => {
		const items: NavItem[] = [];
		for (const category of moduleCategories) {
			items.push({ type: 'category', id: `cat-${category.id}`, categoryId: category.id as ModuleCategory });
			if ($expandedCategories.has(category.id as ModuleCategory)) {
				for (const mod of category.modules) {
					items.push({ type: 'module', id: `mod-${mod.id}`, categoryId: category.id as ModuleCategory, path: mod.path, moduleType: mod.id });
				}
			}
		}
		return items;
	});

	$effect(() => {
		if (activeModule) {
			setActiveModule(activeModule);
		}
	});

	function handleModuleClick(moduleType: ModuleType, path: string) {
		setActiveModule(moduleType);
		goto(path);
	}

	function handleToggleCollapse() {
		sidebarCollapsed.update(c => !c);
	}

	function getCategoryIcon(iconName: string): string {
		const iconMap: Record<string, string> = {
			'Map': '🗺️',
			'Palette': '🎨',
			'Zap': '⚡',
			'BarChart': '📊'
		};
		return iconMap[iconName] || '📁';
	}

	function getModuleIcon(iconName: string): string {
		const iconMap: Record<string, string> = {
			'FileText': '📄',
			'List': '📋',
			'Settings': '⚙️',
			'CheckCircle': '✅',
			'AlertTriangle': '⚠️',
			'Users': '👥',
			'GitBranch': '🌿',
			'MessageSquare': '💬',
			'ClipboardCheck': '📋',
			'HelpCircle': '❓',
			'Layers': '📐'
		};
		return iconMap[iconName] || '📄';
	}

	// Auto-expand category containing active module
	$effect(() => {
		if (activeModule) {
			const category = moduleCategories.find(cat =>
				cat.modules.some(mod => mod.id === activeModule)
			);
			if (category) {
				expandedCategories.update(cats => {
					const newCats = new Set(cats);
					newCats.add(category.id as ModuleCategory);
					return newCats;
				});
			}
		}
	});

	// Keyboard navigation handler
	function handleNavKeydown(event: KeyboardEvent) {
		if (isCollapsed) return;

		const items = flatNavItems();
		const currentItems = items;

		switch (event.key) {
			case 'ArrowDown': {
				event.preventDefault();
				focusedIndex = Math.min(focusedIndex + 1, currentItems.length - 1);
				focusNavItem(currentItems[focusedIndex]);
				break;
			}
			case 'ArrowUp': {
				event.preventDefault();
				focusedIndex = Math.max(focusedIndex - 1, 0);
				focusNavItem(currentItems[focusedIndex]);
				break;
			}
			case 'Enter':
			case ' ': {
				event.preventDefault();
				if (focusedIndex >= 0 && focusedIndex < currentItems.length) {
					const item = currentItems[focusedIndex];
					if (item.type === 'category' && item.categoryId) {
						toggleCategory(item.categoryId);
					} else if (item.type === 'module' && item.moduleType && item.path) {
						handleModuleClick(item.moduleType, item.path);
					}
				}
				break;
			}
			case 'Home': {
				event.preventDefault();
				focusedIndex = 0;
				focusNavItem(currentItems[0]);
				break;
			}
			case 'End': {
				event.preventDefault();
				focusedIndex = currentItems.length - 1;
				focusNavItem(currentItems[currentItems.length - 1]);
				break;
			}
			case 'Escape': {
				focusedIndex = -1;
				(document.activeElement as HTMLElement)?.blur();
				break;
			}
		}
	}

	function focusNavItem(item: NavItem | undefined) {
		if (!item) return;
		const el = document.getElementById(item.id);
		el?.focus();
	}

	function isItemFocused(itemId: string): boolean {
		if (focusedIndex < 0) return false;
		const items = flatNavItems();
		return items[focusedIndex]?.id === itemId;
	}
</script>

<nav
	class="pm-module-nav h-full flex flex-col bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out {isCollapsed ? 'w-16' : 'w-64'}"
	onkeydown={handleNavKeydown}
	role="navigation"
	aria-label="PM模块导航"
>
	<!-- Header with collapse toggle -->
	<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
		{#if !isCollapsed}
			<h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
				模块导航
			</h2>
		{/if}
		<button
			class="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex-shrink-0"
			onclick={handleToggleCollapse}
			title={isCollapsed ? '展开侧边栏' : '折叠侧边栏'}
			aria-label={isCollapsed ? '展开侧边栏' : '折叠侧边栏'}
			aria-expanded={!isCollapsed}
		>
			<svg
				class="w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform duration-300 {isCollapsed ? 'rotate-180' : ''}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				{#if isCollapsed}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
				{:else}
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 7l-7 7-7-7" />
				{/if}
			</svg>
		</button>
	</div>

	<!-- Categories -->
	<div class="flex-1 overflow-y-auto py-2" role="tree" aria-label="模块分类">
		{#each moduleCategories as category (category.id)}
			<div class="mb-1" role="treeitem" aria-expanded={$expandedCategories.has(category.id as ModuleCategory)}>
				<!-- Category Header -->
				<button
					id="cat-{category.id}"
					class="w-full flex items-center {isCollapsed ? 'justify-center px-2' : 'justify-between px-4'} py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors rounded-lg mx-2 {isItemFocused(`cat-${category.id}`) ? 'ring-2 ring-blue-500 ring-offset-1' : ''}"
					onclick={() => !isCollapsed && toggleCategory(category.id as ModuleCategory)}
					aria-expanded={$expandedCategories.has(category.id as ModuleCategory)}
					title={isCollapsed ? category.label : ''}
					tabindex="-1"
				>
					<div class="flex items-center gap-2 {isCollapsed ? 'justify-center' : ''}">
						<span class="text-lg flex-shrink-0">{getCategoryIcon(category.icon)}</span>
						{#if !isCollapsed}
							<span>{category.label}</span>
						{/if}
					</div>
					{#if !isCollapsed}
						<svg
							class="w-4 h-4 transition-transform duration-200 {$expandedCategories.has(category.id as ModuleCategory) ? 'rotate-180' : ''}"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
						</svg>
					{/if}
				</button>

				<!-- Module List -->
				{#if !isCollapsed && $expandedCategories.has(category.id as ModuleCategory)}
					<div class="mt-1 space-y-0.5 animate-expand" role="group" aria-label="{category.label}模块">
						{#each category.modules as module (module.id)}
							<button
								id="mod-{module.id}"
								class="w-full flex items-center gap-2 px-6 py-2 text-sm transition-all duration-200 rounded-md mx-2 relative group
									{activeModule === module.id
										? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 font-medium shadow-sm'
										: 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200'}
									{isItemFocused(`mod-${module.id}`) ? 'ring-2 ring-blue-500 ring-offset-1' : ''}
								"
								onclick={() => handleModuleClick(module.id, module.path)}
								aria-current={activeModule === module.id ? 'page' : undefined}
								tabindex="-1"
							>
								<!-- Active indicator bar -->
								{#if activeModule === module.id}
									<span class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-blue-500 dark:bg-blue-400 rounded-r-full"></span>
								{/if}
								<span class="text-base flex-shrink-0 {activeModule === module.id ? 'scale-110' : 'group-hover:scale-105'} transition-transform">{getModuleIcon(module.icon)}</span>
								<span>{module.label}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>

	<!-- Mobile overlay when sidebar is open -->
	{#if !isCollapsed}
		<div class="lg:hidden fixed inset-0 bg-black/20 z-40" onclick={() => sidebarCollapsed.set(true)}></div>
	{/if}
</nav>

<style>
	.pm-module-nav {
		scrollbar-width: thin;
		scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
	}

	.pm-module-nav::-webkit-scrollbar {
		width: 4px;
	}

	.pm-module-nav::-webkit-scrollbar-track {
		background: transparent;
	}

	.pm-module-nav::-webkit-scrollbar-thumb {
		background-color: rgba(156, 163, 175, 0.5);
		border-radius: 2px;
	}

	@keyframes expand {
		from {
			opacity: 0;
			max-height: 0;
		}
		to {
			opacity: 1;
			max-height: 500px;
		}
	}

	.animate-expand {
		animation: expand 0.2s ease-out forwards;
	}
</style>
