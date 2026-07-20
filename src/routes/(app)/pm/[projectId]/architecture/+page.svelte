<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		isLoading, loadError,
		architectureHierarchy,
		relationEntries,
		loadData, retryLoadData,
		replaceVirtualId,
		findEntryByTitleAndParent,
		createModuleVersionAction
	} from '$lib/stores/pm/architectureStore';
	import type { ArchModule, ArchFeature, ArchParameter, PMRelation } from '$lib/stores/pm/architectureStore';
	import { currentVersion, setCurrentVersion } from '$lib/stores/pm/versionStore';
	import { currentProject } from '$lib/stores/pm/projectStore';
	import MindMapView from '$lib/components/pm/architecture/MindMapView.svelte';
	import ArchitectureTable from '$lib/components/pm/architecture/ArchitectureTable.svelte';
	import ArchNodeDetailSidebar from '$lib/components/pm/architecture/ArchNodeDetailSidebar.svelte';
	import PMVersionSelector from '$lib/components/pm/PMVersionSelector.svelte';
	import PMImportExport from '$lib/components/pm/PMImportExport.svelte';
	import { createEntry, updateEntry, deleteEntry } from '$lib/apis/pm/index';
	import { createEntryVersion } from '$lib/apis/pm/version';

	let projectId = $derived($page.params.projectId!);
	let showVersionSelector = $state(false);
	let activeTab = $state<'mindmap' | 'table'>('mindmap');
	let modules = $state<ArchModule[]>([]);
	let relations = $state<PMRelation[]>([]);
	let tableRef = $state<any>(null);
	let selectedNode = $state<
		| { nodeType: 'root' }
		| { nodeType: 'node'; moduleId: string; featureId?: string; parameterId?: string }
		| null
	>(null);

	// D1: 项目版本号（从 PMVersion 派生）— 传给 ArchitectureTable 显示在三层"版本"列
	let projectVersionNumber = $derived(
		$currentVersion?.versionNumber || $currentVersion?.version_number || ''
	);

	// D10: 导入/导出 state
	let showImportExport = $state(false);
	let importExportMode = $state<'import' | 'export'>('export');

	// Subscribe to architecture hierarchy
	$effect(() => {
		const unsubscribe = architectureHierarchy.subscribe(data => {
			modules = data;
		});
		return unsubscribe;
	});

	// Subscribe to cross-module relations for mindmap edges
	$effect(() => {
		const unsubscribe = relationEntries.subscribe(data => {
			relations = data;
		});
		return unsubscribe;
	});

	onMount(() => { loadData(projectId, $currentVersion?.id); });

	// Reload when global version changes
	$effect(() => {
		const versionId = $currentVersion?.id;
		if (versionId) {
			loadData(projectId, versionId);
		}
	});

	function handleVersionSelect(version: { id: string; versionNumber: string; label?: string }) {
		// Update global version store (propagates to other modules)
		setCurrentVersion(version as any);
		showVersionSelector = false;
		// Reload data with version filter
		loadData(projectId, version.id);
		toast.success(`已切换到版本 ${version.versionNumber}`);
	}

	function handleNodeClick(moduleId: string, featureId?: string, parameterId?: string) {
		// Sentinel moduleId '__root__' signals that the root node was clicked
		if (moduleId === '__root__') {
			selectedNode = { nodeType: 'root' };
		} else {
			selectedNode = { nodeType: 'node', moduleId, featureId, parameterId };
		}
	}

	// 判断 ID 是否为前端虚拟 ID（未持久化或尚未回填真实 ID）
	function isVirtualId(id: string | undefined | null): boolean {
		if (!id) return true;
		return id.startsWith('mod-') || id.startsWith('feat-') || id.startsWith('param-') || id.startsWith('virt-');
	}

	// 显示"无法定位"错误 toast 并提供"刷新"按钮
	function showCannotLocateToast() {
		toast.error('该条目无法定位，请刷新页面后重试', {
			action: {
				label: '刷新',
				onClick: () => retryLoadData(projectId, $currentVersion?.id)
			}
		});
	}

	async function handleTableEdit(type: 'module' | 'feature' | 'parameter', data: any) {
		try {
			const token = localStorage.token || '';
			if (!token) {
				toast.error('未登录');
				return;
			}

			// data.id 可能是前端虚拟 ID（mod-*/feat-*/param-*/virt-*）。
			// 优先使用 entryId（真实 ID）；若仍为虚拟 ID，尝试通过 title + parentId 反查。
			let entryId = data.entryId || data.id;
			if (isVirtualId(entryId)) {
				const title = data.name || data.title || '';
				const parentId = type === 'feature' ? data.moduleId : type === 'parameter' ? data.featureId : undefined;
				const found = findEntryByTitleAndParent(title, parentId);
				if (found) {
					entryId = found.id;
				} else {
					showCannotLocateToast();
					return;
				}
			}

			// Update entry via API
			await updateEntry(token, entryId, {
				title: data.name || data.title,
				data: {
					...data,
					type: type
				}
			});

			// Refresh data (bypass cache so the new entry shows up)
			await retryLoadData(projectId, $currentVersion?.id);
			toast.success('更新成功');
		} catch (e: any) {
			toast.error(e.message || '更新失败');
		}
	}

	async function handleTableDelete(type: 'module' | 'feature' | 'parameter', id: string, data?: any) {
		try {
			const token = localStorage.token || '';
			if (!token) {
				toast.error('未登录');
				return;
			}

			// id 可能是前端虚拟 ID，优先使用 data.entryId（真实 ID）。
			// 若仍为虚拟 ID，尝试通过 title + parentId 反查。
			let entryId = data?.entryId || id;
			if (isVirtualId(entryId)) {
				const title = data?.name || data?.title || '';
				const parentId = type === 'feature' ? data?.moduleId : type === 'parameter' ? data?.featureId : undefined;
				const found = findEntryByTitleAndParent(title, parentId);
				if (found) {
					entryId = found.id;
				} else {
					showCannotLocateToast();
					return;
				}
			}

			await deleteEntry(token, entryId);

			// Refresh data (bypass cache)
			await retryLoadData(projectId, $currentVersion?.id);
			toast.success('删除成功');
		} catch (e: any) {
			toast.error(e.message || '删除失败');
		}
	}

	async function handleTableAdd(
		type: 'module' | 'feature' | 'parameter',
		parentId?: string,
		formData?: Record<string, any>
	) {
		try {
			const token = localStorage.token || '';
			if (!token) {
				toast.error('未登录');
				return;
			}

			// Fall back to empty object if formData is missing (legacy callers).
			const input = formData || {};
			const name = (input.name || '').trim();
			const description = (input.description || '').trim();

			// Build data based on type, preserving user-entered fields.
			const entryData: {
				module_type: string;
				title: string;
				content?: string;
				data: Record<string, unknown>;
			} = {
				module_type: type === 'parameter' ? 'parameter' : 'product-architecture',
				title: name || (type === 'module' ? '新模块' : type === 'feature' ? '新功能' : '新参数'),
				content: description || '',
				data: {
					type: type,
					name: name,
					description: description,
					parentId: parentId || null
				}
			};

			// Add type-specific fields from formData (no more placeholder defaults).
	if (type === 'feature') {
		// 为 feature 写入 moduleName/featureName/moduleId，让 store 聚合时能正确归到父模块下
		// 而不是当成顶级模块。moduleId 持久化后，switch_module_version / 版本跨度计算可正确匹配。
		let moduleName = '';
		let resolvedModuleId = '';
		if (parentId) {
			for (const mod of modules) {
				// 优先按虚拟 id 匹配
				if (mod.id === parentId) {
					moduleName = mod.name;
					resolvedModuleId = mod.entryId || mod.id;
					break;
				}
				// 兜底 1：parentId 可能是真实 entryId（store 重派生后虚拟 id 已变）
				if (mod.entryId && mod.entryId === parentId) {
					moduleName = mod.name;
					resolvedModuleId = mod.entryId;
					break;
				}
				// 兜底 2：parentId 可能是 feature id（误传），仍尝试反查所属模块
				for (const feat of mod.features) {
					if (feat.id === parentId || (feat.entryId && feat.entryId === parentId)) {
						moduleName = mod.name;
						resolvedModuleId = mod.entryId || mod.id;
						break;
					}
				}
				if (moduleName) break;
			}
		}
		// 兜底 3：ID 都匹配不上时，尝试用 formData.moduleName 按名称匹配
		if (!moduleName && input.moduleName) {
			const modByName = modules.find(m => m.name === input.moduleName);
			if (modByName) {
				moduleName = modByName.name;
				resolvedModuleId = modByName.entryId || modByName.id;
			}
		}

		// 防御：无法定位父模块时不写脏数据，避免 store 聚合时把 feature 当成顶级模块
		if (!moduleName) {
			toast.error(`父模块 [${parentId || input.moduleName || '?'}] 不在当前列表，请刷新页面后重试`);
			return;
		}

		entryData.data = {
			...entryData.data,
			moduleName,
			moduleId: resolvedModuleId,
			featureName: name
		};
	}

	if (type === 'parameter') {
		// Resolve parent module/feature names from the virtual parentId so
		// the store can aggregate this parameter under the right node.
		// 同时持久化 featureId/moduleId，避免同名功能跨模块共享参数。
		let moduleName = '';
		let featureName = '';
		let resolvedFeatureId = '';
		let resolvedModuleId = '';
		if (parentId) {
			for (const mod of modules) {
				if (mod.id === parentId || (mod.entryId && mod.entryId === parentId)) {
					moduleName = mod.name;
					resolvedModuleId = mod.entryId || mod.id;
					break;
				}
				for (const feat of mod.features) {
					if (feat.id === parentId || (feat.entryId && feat.entryId === parentId)) {
						featureName = feat.name;
						moduleName = mod.name;
						resolvedFeatureId = feat.entryId || feat.id;
						resolvedModuleId = mod.entryId || mod.id;
						break;
					}
				}
				if (moduleName) break;
			}
		}

		// 防御：无法定位父功能时不写脏数据，避免 store 聚合时新参数被静默丢弃
		if (!featureName) {
			toast.error(`父功能 [${parentId || '?'}] 不在当前列表，请刷新页面后重试`);
			return;
		}

		entryData.data = {
			...entryData.data,
			key: (input.key || '').trim() || `param_${Date.now()}`,
			paramType: input.type || 'config',
			dataType: input.dataType || 'string',
			defaultValue: input.defaultValue || '',
			required: input.required === true || input.required === 1,
			moduleName,
			featureName,
			featureId: resolvedFeatureId,
			moduleId: resolvedModuleId
		};
	}

			const response = await createEntry(token, projectId, entryData);

			// 立即用服务端返回的真实 ID 回填虚拟 ID，确保新增条目可被编辑/删除。
			// replaceVirtualId 在 store 中无匹配虚拟行时为 no-op，retryLoadData 会全量刷新覆盖。
			if (formData?._virtualId && response.id) {
				replaceVirtualId(formData._virtualId, response.id);
			}

			// Refresh data (bypass cache so the new entry shows up immediately)
		await retryLoadData(projectId, $currentVersion?.id);
		toast.success('添加成功');
	} catch (e: any) {
		toast.error(e.message || '添加失败');
	}
}

	// ===== 创建模块版本对话框 =====
	let createVersionTarget = $state<ArchModule | ArchFeature | ArchParameter | null>(null);
	let createVersionLayerType = $state<'module' | 'feature' | 'parameter'>('module');
	let showCreateVersionDialog = $state(false);
	let newVersionNumber = $state('');
	let newVersionSummary = $state('');
	let isCreatingVersion = $state(false);

	// D18: 三层统一处理 — 自动创建 entry（若缺）+ 打开版本对话框
	async function handleOpenCreateVersionDialog(
		target: ArchModule | ArchFeature | ArchParameter,
		layerType: 'module' | 'feature' | 'parameter' = 'module'
	) {
		// D5: 无 entryId 时自动创建 arch entry — 自动聚合的节点没有 PMEntry，
		// 这里先创建一个 architecture 类型的 PMEntry 再打开对话框
		if (!target.entryId) {
			try {
				const token = localStorage.token || '';
				const title = (target as any).name || (target as any).title || target.id;
				const created = await createEntry(token, projectId, {
					module_type: 'architecture',
					title,
					data: {
						node_type: layerType,
						module_id: (target as any).moduleId || target.id,
						feature_id: layerType === 'feature' ? target.id : undefined,
						parameter_id: layerType === 'parameter' ? target.id : undefined,
						node_status: (target as any).status || 'planned'
					},
					status: 'active',
					priority: 'medium'
				});
				// 把新创建的 entryId 回填到 target
				target.entryId = created.id;
				// 同步到 store：根据 layerType 在 architectureHierarchy 中定位并更新 entryId
				try {
					architectureHierarchy.update((mods) =>
						mods.map((m) => {
							if (layerType === 'module' && m.id === target.id) {
								return { ...m, entryId: created.id };
							}
							if (layerType === 'feature') {
								return {
									...m,
									features: (m.features || []).map((f) =>
										f.id === target.id ? { ...f, entryId: created.id } : f
									)
								};
							}
							if (layerType === 'parameter') {
								return {
									...m,
									features: (m.features || []).map((f) => ({
										...f,
										parameters: (f.parameters || []).map((p) =>
											p.id === target.id ? { ...p, entryId: created.id } : p
										)
									}))
								};
							}
							return m;
						})
					);
				} catch (_) { /* store 更新失败不影响当前流程 */ }
				const layerLabel = layerType === 'module' ? '模块' : layerType === 'feature' ? '功能' : '参数';
				toast.info(`已为该${layerLabel}自动创建架构条目`);
			} catch (e: any) {
				toast.error(`自动创建条目失败：${e?.message || e}`);
				return;
			}
		}
		createVersionTarget = target;
		createVersionLayerType = layerType;
		// 默认版本号：若已有版本列表，递增；否则 1.0
		const existing =
			(target as any).moduleVersions ||
			(target as any).featureVersions ||
			(target as any).parameterVersions ||
			[];
		newVersionNumber = existing.length > 0 ? `${existing.length + 1}.0` : '1.0';
		newVersionSummary = '';
		showCreateVersionDialog = true;
	}

	async function handleCreateVersion() {
		if (!createVersionTarget?.entryId) return;
		if (!newVersionNumber.trim()) {
			toast.error('请输入版本号');
			return;
		}
		isCreatingVersion = true;
		try {
			await createModuleVersionAction(projectId, createVersionTarget.entryId, {
				version_number: newVersionNumber.trim(),
				change_summary: newVersionSummary.trim()
			});
			const layerLabel = createVersionLayerType === 'module' ? '模块' : createVersionLayerType === 'feature' ? '功能' : '参数';
			toast.success(`${layerLabel}版本创建成功`);
			showCreateVersionDialog = false;
			createVersionTarget = null;
			newVersionNumber = '';
			newVersionSummary = '';
		} catch (e: any) {
			toast.error(e.message || '创建版本失败');
		} finally {
			isCreatingVersion = false;
		}
	}

	// D10: 扁平层级模式 — 把 modules/features/parameters 摊平为条目数组用于导出
	let architectureEntriesForExport = $derived.by(() => {
		const result: any[] = [];
		for (const m of modules) {
			result.push({
				title: m.name,
				content: m.description || '',
				status: m.status || 'planned',
				priority: 'medium',
				data: { node_type: 'module', module_id: m.id, ...(m as any) },
				current_version_number: (m as any).currentVersionNumber || '',
				created_version_number: (m as any).createdVersionNumber || '',
				versionId: m.entryId || ''
			});
			for (const f of (m.features || [])) {
				result.push({
					title: f.name,
					content: f.description || '',
					status: f.status || 'planned',
					priority: 'medium',
					data: { node_type: 'feature', module_id: m.id, feature_id: f.id, ...(f as any) },
					current_version_number: (f as any).currentVersionNumber || '',
					created_version_number: (f as any).createdVersionNumber || '',
					versionId: f.entryId || ''
				});
				for (const p of (f.parameters || [])) {
					result.push({
						title: p.name,
						content: p.description || '',
						status: p.status || 'planned',
						priority: 'medium',
						data: {
							node_type: 'parameter',
							module_id: m.id,
							feature_id: f.id,
							parameter_id: p.id,
							...(p as any)
						},
						current_version_number: (p as any).currentVersionNumber || '',
						created_version_number: (p as any).createdVersionNumber || '',
						versionId: p.entryId || ''
					});
				}
			}
		}
		return result;
	});

	const archModuleConfig = {
		name: '产品架构',
		tableColumns: [
			{ key: 'title', label: '名称' },
			{ key: 'content', label: '描述' },
			{ key: 'status', label: '状态' }
		]
	};

	// D10: 导入处理 — 支持覆盖/追加/合并
	async function handleArchitectureImport(
		importEntries: any[],
		importMode: 'append' | 'overwrite' | 'merge'
	) {
		const token = localStorage.token || '';
		try {
			if (importMode === 'overwrite') {
				// 覆盖模式：先删除现有所有架构条目
				for (const m of modules) {
					if (m.entryId) {
						try { await deleteEntry(token, projectId, m.entryId); } catch (_) {}
					}
					for (const f of (m.features || [])) {
						if (f.entryId) {
							try { await deleteEntry(token, projectId, f.entryId); } catch (_) {}
						}
					}
				}
			}
			// 创建新条目（append 和 overwrite 都创建；merge 也创建，依赖 loadData 后续合并）
			for (const entry of importEntries) {
				await createEntry(token, projectId, {
					module_type: 'architecture',
					title: entry.title,
					content: entry.content || '',
					data: entry.data || {},
					status: entry.status || 'active',
					priority: entry.priority || 'medium'
				});
			}
			const modeLabel = importMode === 'append' ? '追加' : importMode === 'overwrite' ? '覆盖' : '合并';
			toast.success(`已导入 ${importEntries.length} 条架构条目（${modeLabel}）`);
			await loadData(projectId, $currentVersion?.id);
		} catch (e: any) {
			toast.error(`导入失败：${e?.message || e}`);
		}
	}
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<!-- Header -->
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>产品架构</div>
				{#if $currentVersion}
					<span class="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
						{$currentVersion.versionNumber || $currentVersion.version_number}
					</span>
				{/if}
			</div>
			<div class="flex w-full justify-end gap-1.5 relative z-10">
				<!-- Version Selector -->
				<button
					class="px-2 py-1.5 rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition font-medium text-sm flex items-center"
					onclick={() => { showVersionSelector = true; }}
					title="选择版本"
				>
					<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
					</svg>
					<span>{$currentVersion?.versionNumber || $currentVersion?.version_number || '选择版本'}</span>
				</button>
				<!-- D10: Import Button -->
				<button
					class="px-2 py-1.5 rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition font-medium text-sm flex items-center"
					onclick={() => { importExportMode = 'import'; showImportExport = true; }}
					title="导入"
				>
					<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M12 12v8m0 0l-3-3m3 3l3-3" />
					</svg>
					<span class="text-xs">导入</span>
				</button>
				<!-- D10: Export Button -->
				<button
					class="px-2 py-1.5 rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition font-medium text-sm flex items-center"
					onclick={() => { importExportMode = 'export'; showImportExport = true; }}
					title="导出"
				>
					<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M12 8v8m0 0l-3-3m3 3l3-3" />
					</svg>
					<span class="text-xs">导出</span>
				</button>
				<!-- AI Assistant -->
				<button class="px-2 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition font-medium text-sm flex items-center" title="AI 助手">
					<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
					<div class="ml-1 text-xs">AI</div>
				</button>
			</div>
		</div>
		<!-- Tab Bar -->
		<div class="flex gap-1 mt-2">
			<button
				class="px-4 py-2 rounded-xl text-sm font-medium transition {activeTab === 'mindmap' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}"
				onclick={() => activeTab = 'mindmap'}
			>
				思维导图
			</button>
			<button
				class="px-4 py-2 rounded-xl text-sm font-medium transition {activeTab === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}"
				onclick={() => activeTab = 'table'}
			>
				表格
			</button>
		</div>
	</div>

	<!-- Content -->
	{#if $isLoading}
		<div class="flex items-center justify-center h-[calc(100vh-200px)]">
			<div class="w-8 h-8 border-2 border-gray-300 dark:border-gray-600 border-t-blue-500 rounded-full animate-spin"></div>
		</div>
	{:else if $loadError}
		<div class="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
			<div class="text-red-500 mb-2">{$loadError}</div>
			<button class="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition" onclick={() => retryLoadData(projectId, $currentVersion?.id)}>
				重试
			</button>
		</div>
	{:else}
		{#if activeTab === 'mindmap'}
		<div class="h-[calc(100vh-200px)] flex">
			<div class="flex-1 min-w-0">
				<MindMapView modules={modules} relations={relations} onNodeClick={handleNodeClick} />
			</div>
			{#if selectedNode}
				<ArchNodeDetailSidebar
					{selectedNode}
					{modules}
					projectMeta={{
						projectId,
						projectName: $currentProject?.name,
						projectDescription: $currentProject?.description,
						projectCreatedAt: $currentProject?.createdAt,
						projectUpdatedAt: $currentProject?.updatedAt,
						currentVersion: $currentVersion
					}}
					onClose={() => { selectedNode = null; }}
					onSelectNode={(node) => { selectedNode = node; }}
				/>
			{/if}
		</div>
	{:else}
			<div class="h-[calc(100vh-200px)]">
				<ArchitectureTable
				modules={modules}
				{projectVersionNumber}
				onEdit={handleTableEdit}
				onDelete={handleTableDelete}
				onAdd={handleTableAdd}
				onCreateModuleVersion={handleOpenCreateVersionDialog}
				bind:this={tableRef}
			/>
			</div>
		{/if}
	{/if}
</div>

<!-- Version Selector Modal -->
<PMVersionSelector
	isOpen={showVersionSelector}
	onClose={() => { showVersionSelector = false; }}
	onSelect={handleVersionSelect}
	{projectId}
/>

<!-- D10: Import / Export Dialog -->
<PMImportExport
	show={showImportExport}
	mode={importExportMode}
	entries={architectureEntriesForExport}
	moduleType="architecture"
	moduleConfig={archModuleConfig}
	versionId={$currentVersion?.id || ''}
	onImport={handleArchitectureImport}
	onClose={() => { showImportExport = false; }}
/>

<!-- Create Module Version Dialog -->
{#if showCreateVersionDialog}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={() => { if (!isCreatingVersion) showCreateVersionDialog = false; }}
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
			onclick={(e) => e.stopPropagation()}
		>
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
					创建{createVersionLayerType === 'module' ? '模块' : createVersionLayerType === 'feature' ? '功能' : '参数'}版本
				</h2>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					{#if createVersionTarget}
						{createVersionLayerType === 'module' ? '模块' : createVersionLayerType === 'feature' ? '功能' : '参数'}：{(createVersionTarget as any).name || (createVersionTarget as any).title}
					{/if}
				</p>
			</div>
			<div class="p-6 space-y-4">
				<div>
					<label for="new-version-number" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">版本号</label>
					<input
						id="new-version-number"
						type="text"
						class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
						placeholder="例如 1.0、2.0"
						bind:value={newVersionNumber}
						disabled={isCreatingVersion}
					/>
				</div>
				<div>
					<label for="new-version-summary" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">变更说明</label>
					<textarea
						id="new-version-summary"
						class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 min-h-[80px]"
						placeholder="本次版本的变更说明（可选）"
						bind:value={newVersionSummary}
						disabled={isCreatingVersion}
					></textarea>
				</div>
			</div>
			<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
				<button
					class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
					onclick={() => { if (!isCreatingVersion) showCreateVersionDialog = false; }}
					disabled={isCreatingVersion}
				>取消</button>
				<button
					class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
					onclick={handleCreateVersion}
					disabled={isCreatingVersion || !newVersionNumber.trim()}
				>
					{#if isCreatingVersion}
						<svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						创建中...
					{:else}
						创建版本
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}