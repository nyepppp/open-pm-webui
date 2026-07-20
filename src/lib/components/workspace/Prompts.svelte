<script lang="ts">
	import { toast } from 'svelte-sonner';
	import fileSaver from 'file-saver';
	const { saveAs } = fileSaver;

	import { goto } from '$app/navigation';
	import { onMount, getContext, tick, onDestroy } from 'svelte';
	import { WEBUI_NAME, config, user } from '$lib/stores';

	import {
		createNewPrompt,
		deletePromptById,
		togglePromptById,
		getPromptItems,
		getPromptTags,
		getRoles,
		upgradeToRole,
		removeRole,
		type RolePrompt,
		type RoleForm
	} from '$lib/apis/prompts';
	import { capitalizeFirstLetter, slugify, copyToClipboard } from '$lib/utils';
	import { tools as toolsStore, skills as skillsStore } from '$lib/stores';

	import PromptMenu from './Prompts/PromptMenu.svelte';
	import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
	import Clipboard from '../icons/Clipboard.svelte';
	import Check from '../icons/Check.svelte';
	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Search from '../icons/Search.svelte';
	import Plus from '../icons/Plus.svelte';
	import ChevronRight from '../icons/ChevronRight.svelte';
	import Spinner from '../common/Spinner.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import XMark from '../icons/XMark.svelte';
	import GarbageBin from '../icons/GarbageBin.svelte';
	import ViewSelector from './common/ViewSelector.svelte';
	import TagSelector from './common/TagSelector.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Switch from '../common/Switch.svelte';
	import Pagination from '../common/Pagination.svelte';

	let shiftKey = false;

	const i18n = getContext('i18n');
	let promptsImportInputElement: HTMLInputElement;
	let loaded = false;

	let importFiles = null;
	let query = '';
	let searchDebounceTimer: ReturnType<typeof setTimeout>;

	let prompts = null;
	let tags = [];
	let total = null;
	let loading = false;

	let showDeleteConfirm = false;
	let deletePrompt = null;

	let tagsContainerElement: HTMLDivElement;
	let viewOption = '';
	let selectedTag = '';
	let copiedId: string | null = null;

	let page = 1;

	// ===== Part B: 角色提示词 =====
	// 顶部标签页切换：'prompts' | 'roles'
	let activeTab: 'prompts' | 'roles' = 'prompts';
	// 角色列表
	let roles: RolePrompt[] = [];
	let rolesLoading = false;
	// 角色 编辑/升级 弹窗
	let showRoleModal = false;
	// 当前正在编辑的角色（null 表示新建/从普通 prompt 升级）
	let editingRole: RolePrompt | null = null;
	// 关联的 prompt（升级为角色时使用）
	let rolePromptId: string | null = null;
	// 角色表单
	let roleForm: RoleForm = {
		system_prompt: '',
		tools: [],
		suggested_models: [],
		description: ''
	};

	// 可选工具列表（从 store 派生）
	const availableTools = $derived(
		[...($toolsStore ?? []), ...($skillsStore ?? []).map((s: any) => ({ id: s.id, name: s.name, type: 'skill' }))]
	);

	// 加载角色列表
	const loadRoles = async () => {
		rolesLoading = true;
		try {
			roles = await getRoles(localStorage.token);
		} catch (err) {
			toast.error(`${err}`);
			roles = [];
		} finally {
			rolesLoading = false;
		}
	};

	// 打开"升级为角色"弹窗（关联一个已存在的 prompt）
	const openUpgradeRoleModal = (prompt: any) => {
		rolePromptId = prompt.id;
		editingRole = null;
		roleForm = {
			system_prompt: prompt.content || '',
			tools: [],
			suggested_models: [],
			description: prompt.name || ''
		};
		showRoleModal = true;
	};

	// 打开"编辑角色"弹窗
	const openEditRoleModal = (role: RolePrompt) => {
		editingRole = role;
		rolePromptId = role.id;
		roleForm = {
			system_prompt: role.system_prompt || '',
			tools: role.tools || [],
			suggested_models: role.suggested_models || [],
			description: role.description || ''
		};
		showRoleModal = true;
	};

	// 关闭弹窗
	const closeRoleModal = () => {
		showRoleModal = false;
		editingRole = null;
		rolePromptId = null;
	};

	// 提交角色表单（升级或更新）
	const handleRoleSubmit = async () => {
		if (!rolePromptId) {
			toast.error('缺少关联的 prompt ID');
			return;
		}
		try {
			await upgradeToRole(localStorage.token, rolePromptId, roleForm);
			toast.success(editingRole ? '角色已更新' : '已升级为角色');
			closeRoleModal();
			await loadRoles();
		} catch (err) {
			toast.error(`${err}`);
		}
	};

	// 取消角色标记
	const handleRemoveRole = async (role: RolePrompt) => {
		try {
			await removeRole(localStorage.token, role.id);
			toast.success(`已取消角色：${role.name}`);
			await loadRoles();
		} catch (err) {
			toast.error(`${err}`);
		}
	};

	// 切换工具选中状态
	const toggleTool = (toolId: string) => {
		if (roleForm.tools.includes(toolId)) {
			roleForm = { ...roleForm, tools: roleForm.tools.filter((id) => id !== toolId) };
		} else {
			roleForm = { ...roleForm, tools: [...roleForm.tools, toolId] };
		}
	};

	// Debounce only query changes
	$effect(() => {
		if (query !== undefined) {
			loading = true;
			clearTimeout(searchDebounceTimer);
			searchDebounceTimer = setTimeout(() => {
				page = 1;
				getPromptList();
			}, 300);
		}
	});

	// Immediate response to page/filter changes
	$effect(() => {
		if (page && selectedTag !== undefined && viewOption !== undefined) {
			getPromptList();
		}
	});

	const getPromptList = async () => {
		if (!loaded) return;

		loading = true;
		try {
			const res = await getPromptItems(
				localStorage.token,
				query,
				viewOption,
				selectedTag,
				null,
				null,
				page
			).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				prompts = res.items;
				total = res.total;

				// get tags
				tags = await getPromptTags(localStorage.token).catch((error) => {
					toast.error(`${error}`);
					return [];
				});
			}
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	};

	const shareHandler = async (prompt) => {
		toast.success($i18n.t('Redirecting you to Open WebUI Community'));

		const url = 'https://openwebui.com';

		const tab = await window.open(`${url}/prompts/create`, '_blank');
		window.addEventListener(
			'message',
			(event) => {
				if (event.origin !== url) return;
				if (event.data === 'loaded') {
					tab.postMessage(JSON.stringify(prompt), '*');
				}
			},
			false
		);
	};

	const cloneHandler = async (prompt) => {
		const clonedPrompt = { ...prompt };

		clonedPrompt.title = `${clonedPrompt.title} (Clone)`;
		const baseCommand = clonedPrompt.command.startsWith('/')
			? clonedPrompt.command.substring(1)
			: clonedPrompt.command;
		clonedPrompt.command = slugify(`${baseCommand} clone`);

		sessionStorage.prompt = JSON.stringify(clonedPrompt);
		goto('/workspace/prompts/create');
	};

	const exportHandler = async (prompt) => {
		let blob = new Blob([JSON.stringify([prompt])], {
			type: 'application/json'
		});
		saveAs(blob, `prompt-export-${Date.now()}.json`);
	};

	const copyHandler = async (prompt) => {
		const res = await copyToClipboard(prompt.content);
		if (res) {
			copiedId = prompt.command;
			setTimeout(() => {
				copiedId = null;
			}, 2000);
		}
	};

	const deleteHandler = async (prompt) => {
		const command = prompt.command;

		const res = await deletePromptById(localStorage.token, prompt.id).catch((err) => {
			toast.error(err);
			return null;
		});

		if (res) {
			toast.success($i18n.t(`Deleted {{name}}`, { name: command }));
		}

		page = 1;
		getPromptList();
	};

	onMount(async () => {
		viewOption = localStorage?.workspaceViewOption || '';
		loaded = true;
		// 后台加载角色列表（不阻塞 prompts 列表加载）
		loadRoles();

		const onKeyDown = (event) => {
			if (event.key === 'Shift') {
				shiftKey = true;
			}
		};

		const onKeyUp = (event) => {
			if (event.key === 'Shift') {
				shiftKey = false;
			}
		};

		const onBlur = () => {
			shiftKey = false;
		};

		window.addEventListener('keydown', onKeyDown);
		window.addEventListener('keyup', onKeyUp);
		window.addEventListener('blur', onBlur);

		return () => {
			clearTimeout(searchDebounceTimer);
			window.removeEventListener('keydown', onKeyDown);
			window.removeEventListener('keyup', onKeyUp);
			window.removeEventListener('blur', onBlur);
		};
	});

	onDestroy(() => {
		clearTimeout(searchDebounceTimer);
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Prompts')} • {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<DeleteConfirmDialog
		bind:show={showDeleteConfirm}
		title={$i18n.t('Delete prompt?')}
		on:confirm={() => {
			deleteHandler(deletePrompt);
		}}
	>
		<div class=" text-sm text-gray-500 truncate">
			{$i18n.t('This will delete')} <span class="  font-medium">{deletePrompt.command}</span>.
		</div>
	</DeleteConfirmDialog>

	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<input
			id="prompts-import-input"
			bind:this={promptsImportInputElement}
			bind:files={importFiles}
			type="file"
			accept=".json"
			hidden
			on:change={() => {
				console.log(importFiles);
				if (!importFiles || importFiles.length === 0) return;

				const reader = new FileReader();
				reader.onload = async (event) => {
					const savedPrompts = JSON.parse(event.target.result);
					console.log(savedPrompts);

					try {
						for (const prompt of savedPrompts) {
							await createNewPrompt(localStorage.token, {
								command: prompt.command,
								name: prompt.name,
								content: prompt.content
							}).catch((error) => {
								toast.error(typeof error === 'string' ? error : JSON.stringify(error));
								return null;
							});
						}

						page = 1;
						await getPromptList();
					} finally {
						importFiles = null;
						promptsImportInputElement.value = '';
					}
				};

				reader.readAsText(importFiles[0]);
			}}
		/>
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>
					{$i18n.t('Prompts')}
				</div>

				<div class="text-lg font-medium text-gray-500 dark:text-gray-500">
					{total ?? ''}
				</div>
			</div>

			<div class="flex w-full justify-end gap-1.5">
				{#if $user?.role === 'admin' || $user?.permissions?.workspace?.prompts_import}
					<button
						class="flex text-xs items-center space-x-1 px-3 py-1.5 rounded-xl bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-200 transition"
						on:click={() => {
							promptsImportInputElement.click();
						}}
					>
						<div class=" self-center font-medium line-clamp-1">
							{$i18n.t('Import')}
						</div>
					</button>
				{/if}

				{#if total && ($user?.role === 'admin' || $user?.permissions?.workspace?.prompts_export)}
					<button
						class="flex text-xs items-center space-x-1 px-3 py-1.5 rounded-xl bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-200 transition"
						on:click={async () => {
							let blob = new Blob([JSON.stringify(prompts)], {
								type: 'application/json'
							});
							saveAs(blob, `prompts-export-${Date.now()}.json`);
						}}
					>
						<div class=" self-center font-medium line-clamp-1">
							{$i18n.t('Export')}
						</div>
					</button>
				{/if}
				<a
					class=" px-2 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black transition font-medium text-sm flex items-center"
					href="/workspace/prompts/create"
				>
					<Plus className="size-3" strokeWidth="2.5" />

					<div class=" hidden md:block md:ml-1 text-xs">{$i18n.t('New Prompt')}</div>
				</a>
			</div>
		</div>
	</div>

	<!-- Part B: 顶部标签页切换 Prompts | Roles -->
	<div class="flex gap-1 mb-2 px-1">
		<button
			class="px-3 py-1.5 text-sm rounded-lg transition-colors {activeTab === 'prompts'
				? 'bg-black text-white dark:bg-white dark:text-black font-medium'
				: 'bg-gray-50 dark:bg-gray-850 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
			on:click={() => (activeTab = 'prompts')}
		>
			{$i18n.t('Prompts')}
		</button>
		<button
			class="px-3 py-1.5 text-sm rounded-lg transition-colors {activeTab === 'roles'
				? 'bg-black text-white dark:bg-white dark:text-black font-medium'
				: 'bg-gray-50 dark:bg-gray-850 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
			on:click={() => { activeTab = 'roles'; loadRoles(); }}
		>
			{$i18n.t('Roles')}
			{#if roles.length > 0}
				<span class="ml-1 text-xs opacity-60">{roles.length}</span>
			{/if}
		</button>
	</div>

	{#if activeTab === 'prompts'}
	<div
		class="py-2 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30"
	>
		<div class=" flex w-full space-x-2 py-0.5 px-3.5 pb-2">
			<div class="flex flex-1">
				<div class=" self-center ml-1 mr-3">
					<Search className="size-3.5" />
				</div>
				<input
					class=" w-full text-sm pr-4 py-1 rounded-r-xl outline-hidden bg-transparent"
					bind:value={query}
					aria-label={$i18n.t('Search Prompts')}
					placeholder={$i18n.t('Search Prompts')}
				/>

				{#if query}
					<div class="self-center pl-1.5 translate-y-[0.5px] rounded-l-xl bg-transparent">
						<button
							class="p-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-900 transition"
							aria-label={$i18n.t('Clear search')}
							on:click={() => {
								query = '';
							}}
						>
							<XMark className="size-3" strokeWidth="2" />
						</button>
					</div>
				{/if}
			</div>
		</div>

		<div
			class="px-3 flex w-full bg-transparent overflow-x-auto scrollbar-none -mx-1"
			on:wheel={(e) => {
				if (e.deltaY !== 0) {
					e.preventDefault();
					e.currentTarget.scrollLeft += e.deltaY;
				}
			}}
		>
			<div
				class="flex gap-0.5 w-fit text-center text-sm rounded-full bg-transparent px-1.5 whitespace-nowrap"
				bind:this={tagsContainerElement}
			>
				<ViewSelector
					bind:value={viewOption}
					onChange={async (value) => {
						localStorage.workspaceViewOption = value;
						page = 1;
						await tick();
					}}
				/>

				{#if (tags ?? []).length > 0}
					<TagSelector
						bind:value={selectedTag}
						items={tags.map((tag) => ({ value: tag, label: tag }))}
					/>
				{/if}
			</div>
		</div>

		{#if prompts === null || loading}
			<div class="w-full h-full flex justify-center items-center my-16 mb-24">
				<Spinner className="size-5" />
			</div>
		{:else if (prompts ?? []).length !== 0}
			<!-- Before they call, I will answer; while they are yet speaking, I will hear. -->
			<div class="gap-2 grid my-2 px-3 lg:grid-cols-2">
				{#each prompts as prompt (prompt.id)}
					<a
						class=" flex space-x-4 cursor-pointer text-left w-full px-3 py-2.5 dark:hover:bg-gray-850/50 hover:bg-gray-50 transition rounded-2xl"
						href={`/workspace/prompts/${prompt.id}`}
					>
						<div class=" flex flex-col flex-1 space-x-4 cursor-pointer w-full pl-1">
							<div class="flex items-center justify-between w-full mb-0.5">
								<div class="flex items-center gap-2">
									<div class="font-medium line-clamp-1 capitalize">{prompt.name}</div>
									<div class="text-xs overflow-hidden text-ellipsis line-clamp-1 text-gray-500">
										/{prompt.command}
									</div>
								</div>
								{#if !prompt.write_access}
									<Badge type="muted" content={$i18n.t('Read Only')} />
								{/if}
							</div>

							<div class="flex gap-1 text-xs">
								<Tooltip
									content={prompt?.user?.email ?? $i18n.t('Deleted User')}
									className="flex shrink-0"
									placement="top-start"
								>
									<div class="shrink-0 text-gray-500">
										{$i18n.t('By {{name}}', {
											name: capitalizeFirstLetter(
												prompt?.user?.name ?? prompt?.user?.email ?? $i18n.t('Deleted User')
											)
										})}
									</div>
								</Tooltip>

								<div>·</div>

								{#if prompt.content}
									<Tooltip content={prompt.content} placement="top">
										<div class="line-clamp-1">
											{prompt.content}
										</div>
									</Tooltip>
								{/if}
							</div>
						</div>
						<div class="flex flex-row gap-0.5 self-center">
							{#if shiftKey}
								<Tooltip content={$i18n.t('Delete')}>
									<button
										class="self-center w-fit text-sm px-2 py-2 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
										type="button"
										aria-label={$i18n.t('Delete')}
										on:click={() => {
											deleteHandler(prompt);
										}}
									>
										<GarbageBin />
									</button>
								</Tooltip>
							{:else}
								<Tooltip content={$i18n.t('Copy Prompt')}>
									<button
										class="self-center w-fit text-sm p-1.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
										type="button"
										aria-label={$i18n.t('Copy Prompt')}
										on:click={(e) => {
											e.preventDefault();
											e.stopPropagation();
											copyHandler(prompt);
										}}
									>
										{#if copiedId === prompt.command}
											<Check className="size-4" strokeWidth="1.5" />
										{:else}
											<Clipboard className="size-4" strokeWidth="1.5" />
										{/if}
									</button>
								</Tooltip>
								<PromptMenu
								shareHandler={() => {
									shareHandler(prompt);
								}}
								cloneHandler={() => {
									cloneHandler(prompt);
								}}
								exportHandler={() => {
									exportHandler(prompt);
								}}
								deleteHandler={async () => {
									deletePrompt = prompt;
									showDeleteConfirm = true;
								}}
								// 仅当 prompt 尚未被标记为角色时，才传入“升级为角色”回调（已是角色的不显示升级按钮）
								upgradeHandler={prompt.is_role
									? undefined
									: () => openUpgradeRoleModal(prompt)}
								onClose={() => {}}
							>
									<button
										class="self-center w-fit text-sm p-1.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
										type="button"
									>
										<EllipsisHorizontal className="size-5" />
									</button>
								</PromptMenu>

								<button on:click|stopPropagation|preventDefault>
									<Tooltip
										content={prompt.is_active !== false ? $i18n.t('Enabled') : $i18n.t('Disabled')}
									>
										<Switch
											bind:state={prompt.is_active}
											on:change={async () => {
												togglePromptById(localStorage.token, prompt.id);
											}}
										/>
									</Tooltip>
								</button>
							{/if}
						</div>
					</a>
				{/each}
			</div>

			{#if total > 30}
				<div class="flex justify-center mt-4 mb-2">
					<Pagination bind:page count={total} perPage={30} />
				</div>
			{/if}
		{:else}
			<div class=" w-full h-full flex flex-col justify-center items-center my-16 mb-24">
				<div class="max-w-md text-center">
					<div class=" text-3xl mb-3">😕</div>
					<div class=" text-lg font-medium mb-1">{$i18n.t('No prompts found')}</div>
					<div class=" text-gray-500 text-center text-xs">
						{$i18n.t('Try adjusting your search or filter to find what you are looking for.')}
					</div>
				</div>
			</div>
		{/if}
	</div>
	{:else if activeTab === 'roles'}
	<!-- ===== Part B: 角色提示词列表 ===== -->
	<div class="py-2 bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30">
		{#if rolesLoading}
			<div class="w-full h-full flex justify-center items-center my-16 mb-24">
				<Spinner className="size-5" />
			</div>
		{:else if roles.length === 0}
			<div class="w-full h-full flex flex-col justify-center items-center my-16 mb-24">
				<div class="max-w-md text-center">
					<div class="text-3xl mb-3">🎭</div>
					<div class="text-lg font-medium mb-1">暂无角色提示词</div>
					<div class="text-gray-500 text-center text-xs">
						切换到 "Prompts" 标签，从已有提示词的菜单中选择"升级为角色"。
					</div>
				</div>
			</div>
		{:else}
			<div class="gap-2 grid my-2 px-3 lg:grid-cols-2">
				{#each roles as role (role.id)}
					<div
						class="flex space-x-4 cursor-pointer text-left w-full px-3 py-2.5 dark:hover:bg-gray-850/50 hover:bg-gray-50 transition rounded-2xl"
						on:click={() => openEditRoleModal(role)}
						on:keydown={(e) => { if (e.key === 'Enter') openEditRoleModal(role); }}
						role="button"
						tabindex="0"
					>
						<div class="flex flex-col flex-1 space-x-4 cursor-pointer w-full pl-1">
							<div class="flex items-center justify-between w-full mb-0.5">
								<div class="flex items-center gap-2">
									<div class="font-medium line-clamp-1">{role.name}</div>
									{#if role.tools && role.tools.length > 0}
										<Badge type="muted" content={`${role.tools.length} tools`} />
									{/if}
								</div>
								<button
									class="self-center w-fit text-sm p-1.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
									type="button"
									aria-label="取消角色"
									on:click={(e) => {
										e.preventDefault();
										e.stopPropagation();
										handleRemoveRole(role);
									}}
									title="取消角色标记"
								>
									<GarbageBin />
								</button>
							</div>
							{#if role.description}
								<div class="text-xs text-gray-500 line-clamp-1">{role.description}</div>
							{/if}
							{#if role.system_prompt}
								<div class="text-xs text-gray-400 line-clamp-2 mt-0.5">{role.system_prompt}</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
	{/if}

	{#if $config?.features.enable_community_sharing}
		<div class=" my-16">
			<div class=" text-xl font-medium mb-1 line-clamp-1">
				{$i18n.t('Made by Open WebUI Community')}
			</div>

			<a
				class=" flex cursor-pointer items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-850 w-full mb-2 px-3.5 py-1.5 rounded-xl transition"
				href="https://openwebui.com/prompts"
				target="_blank"
			>
				<div class=" self-center">
					<div class=" font-medium line-clamp-1">{$i18n.t('Discover a prompt')}</div>
					<div class=" text-sm line-clamp-1">
						{$i18n.t('Discover, download, and explore custom prompts')}
					</div>
				</div>

				<div>
					<div>
						<ChevronRight />
					</div>
				</div>
			</a>
		</div>
	{/if}

	<!-- Part B: 角色编辑/升级弹窗 -->
	{#if showRoleModal}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
			on:click={closeRoleModal}
			on:keydown={(e) => { if (e.key === 'Escape') closeRoleModal(); }}
			role="presentation"
		>
			<div
				class="bg-white dark:bg-gray-900 dark:text-gray-100 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-5 m-4"
				on:click={(e) => e.stopPropagation()}
				role="dialog"
				aria-modal="true"
				aria-label={editingRole ? '编辑角色' : '升级为角色'}
			>
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-semibold">
						{editingRole ? '编辑角色：' + editingRole.name : '升级为角色'}
					</h3>
					<button
						class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
						on:click={closeRoleModal}
						aria-label="关闭"
					>
						<XMark />
					</button>
				</div>

				<div class="space-y-3">
					<!-- 描述 -->
					<div>
						<label for="role-description" class="text-sm font-medium block mb-1">描述</label>
						<input
							id="role-description"
							type="text"
							class="w-full text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent px-3 py-2 outline-none focus:border-blue-500"
							placeholder="角色的简短描述（例如：资深产品经理）"
							bind:value={roleForm.description}
						/>
					</div>

					<!-- 系统提示词 -->
					<div>
						<label for="role-system-prompt" class="text-sm font-medium block mb-1">
							系统提示词 (System Prompt)
						</label>
						<textarea
							id="role-system-prompt"
							rows="6"
							class="w-full text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent px-3 py-2 outline-none focus:border-blue-500 font-mono resize-y"
							placeholder="将注入到对话 params.system 的提示词内容..."
							bind:value={roleForm.system_prompt}
						></textarea>
						<p class="text-xs text-gray-400 mt-1">
							此内容会作为 system message 注入到对话窗口，仅影响后续消息。
						</p>
					</div>

					<!-- 工具多选 -->
					<div>
						<label class="text-sm font-medium block mb-1">启用工具 ({roleForm.tools.length})</label>
						{#if availableTools.length === 0}
							<p class="text-xs text-gray-400">暂无可用工具</p>
						{:else}
							<div class="max-h-40 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 p-2 space-y-1">
								{#each availableTools as tool (tool.id)}
									<label class="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 px-2 py-1 rounded">
										<input
											type="checkbox"
											checked={roleForm.tools.includes(tool.id)}
											on:change={() => toggleTool(tool.id)}
										/>
										<span class="flex-1 truncate">{tool.name}</span>
										{#if tool.type === 'skill'}
											<Badge type="muted" content="skill" />
										{/if}
									</label>
								{/each}
							</div>
						{/if}
					</div>

					<!-- 建议模型（简化版：用逗号分隔的输入框） -->
					<div>
						<label for="role-suggested-models" class="text-sm font-medium block mb-1">
							建议模型（逗号分隔，可选）
						</label>
						<input
							id="role-suggested-models"
							type="text"
							class="w-full text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent px-3 py-2 outline-none focus:border-blue-500"
							placeholder="例如：gpt-4, claude-3-opus"
							value={roleForm.suggested_models.join(', ')}
							on:input={(e) => {
								roleForm = {
									...roleForm,
									suggested_models: e.target.value
										.split(',')
										.map((s: string) => s.trim())
										.filter((s: string) => s.length > 0)
								};
							}}
						/>
					</div>
				</div>

				<div class="flex justify-end gap-2 mt-5">
					<button
						class="px-4 py-2 text-sm rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
						on:click={closeRoleModal}
					>
						取消
					</button>
					<button
						class="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white"
						on:click={handleRoleSubmit}
					>
						{editingRole ? '保存' : '升级为角色'}
					</button>
				</div>
			</div>
		</div>
	{/if}
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<Spinner className="size-5" />
	</div>
{/if}
