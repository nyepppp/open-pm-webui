<script lang="ts">
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { tick, getContext, onMount, onDestroy } from 'svelte';

	import { folders } from '$lib/stores';
	import { getFolders } from '$lib/apis/folders';
	import { searchKnowledgeBases, searchKnowledgeFiles } from '$lib/apis/knowledge';
	import { getProjects, getEntries } from '$lib/apis/pm';
	import { removeLastWordFromString, isValidHttpUrl, isYoutubeUrl, decodeString } from '$lib/utils';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import DocumentPage from '$lib/components/icons/DocumentPage.svelte';
	import Database from '$lib/components/icons/Database.svelte';
	import GlobeAlt from '$lib/components/icons/GlobeAlt.svelte';
	import Youtube from '$lib/components/icons/Youtube.svelte';
	import Folder from '$lib/components/icons/Folder.svelte';

	const i18n = getContext('i18n');

	export let query = '';
	export let onSelect = (e) => {};

	let selectedIdx = 0;
	let items = [];
	let searchDebounceTimer: ReturnType<typeof setTimeout>;

	export let filteredItems = [];
	$: filteredItems = [
		...(query.startsWith('http')
			? isYoutubeUrl(query)
				? [{ type: 'youtube', name: query, description: query }]
				: [
						{
							type: 'web',
							name: query,
							description: query
						}
					]
			: []),
		...items
	];

	$: if (query) {
		selectedIdx = 0;
	}

	export const selectUp = () => {
		selectedIdx = Math.max(0, selectedIdx - 1);
	};

	export const selectDown = () => {
		selectedIdx = Math.min(selectedIdx + 1, filteredItems.length - 1);
	};

	export const select = async () => {
		// find item with data-selected=true
		const item = document.querySelector(`[data-selected="true"]`);
		if (item) {
			// click the item
			item.click();
		}
	};

	let folderItems = [];
	let knowledgeItems = [];
	let fileItems = [];
	let pmItems = [];

	$: items = [...pmItems, ...folderItems, ...knowledgeItems, ...fileItems];

	$: if (query !== undefined) {
		clearTimeout(searchDebounceTimer);
		searchDebounceTimer = setTimeout(() => {
			getItems();
		}, 200);
	}

	onDestroy(() => {
		clearTimeout(searchDebounceTimer);
	});

	const getItems = () => {
		getPMItems();
		getFolderItems();
		getKnowledgeItems();
		getKnowledgeFileItems();
	};

	const getPMItems = async () => {
		if (!query) {
			pmItems = [];
			return;
		}
		try {
			const token = localStorage.token || '';
			const projects = await getProjects(token);
			const matchingProjects = (projects || [])
				.filter((p) => p.name?.toLowerCase().includes(query.toLowerCase()))
				.slice(0, 5)
				.map((p) => ({
					type: 'pm-project',
					name: p.name,
					description: 'PM 项目',
					id: p.id,
					projectId: p.id,
					projectName: p.name
				}));

			let matchingEntries = [];
			for (const project of (projects || []).slice(0, 5)) {
				try {
					const entries = await getEntries(token, project.id);
					const filtered = (entries || [])
						.filter((e) => e.title?.toLowerCase().includes(query.toLowerCase()))
						.slice(0, 3)
						.map((e) => ({
							type: 'pm-entry',
							name: e.title,
							description: `${project.name} - PM 条目`,
							id: e.id,
							projectId: project.id,
							projectName: project.name,
							moduleType: e.moduleType || e.module_type,
							entryTitle: e.title
						}));
					matchingEntries = [...matchingEntries, ...filtered];
				} catch {
					/* skip if project entries fail */
				}
			}

			pmItems = [...matchingProjects, ...matchingEntries].slice(0, 8);
		} catch {
			pmItems = [];
		}
	};

	const getFolderItems = async () => {
		folderItems = $folders
			.map((folder) => ({
				...folder,
				type: 'folder',
				description: $i18n.t('Folder'),
				title: folder.name
			}))
			.filter((folder) => folder.name.toLowerCase().includes(query.toLowerCase()));
	};

	const getKnowledgeItems = async () => {
		const res = await searchKnowledgeBases(localStorage.token, query).catch(() => {
			return null;
		});

		if (res) {
			knowledgeItems = res.items.map((item) => {
				return {
					...item,
					type: 'collection'
				};
			});
		}
	};

	const getKnowledgeFileItems = async () => {
		const res = await searchKnowledgeFiles(localStorage.token, query).catch(() => {
			return null;
		});

		if (res) {
			fileItems = res.items.map((item) => {
				return {
					...item,
					type: 'file',
					name: item.filename,
					description: item.collection ? item.collection.name : ''
				};
			});
		}
	};

	onMount(async () => {
		if ($folders === null) {
			await folders.set(await getFolders(localStorage.token));
		}

		await tick();
	});
</script>

{#if filteredItems.length > 0 || query.startsWith('http')}
	{#each filteredItems as item, idx}
		{#if idx === 0 || item?.type !== items[idx - 1]?.type}
			<div class="px-2 text-xs text-gray-500 py-1">
				{#if item?.type === 'pm-project'}
					{$i18n.t('PM 项目')}
				{:else if item?.type === 'pm-entry'}
					{$i18n.t('PM 条目')}
				{:else if item?.type === 'folder'}
					{$i18n.t('Folders')}
				{:else if item?.type === 'collection'}
					{$i18n.t('Collections')}
				{:else if item?.type === 'file'}
					{$i18n.t('Files')}
				{/if}
			</div>
		{/if}

		{#if !['youtube', 'web'].includes(item.type)}
			<button
				class=" px-2 py-1 rounded-xl w-full text-left flex justify-between items-center {idx ===
				selectedIdx
					? ' bg-gray-50 dark:bg-gray-800 dark:text-gray-100 selected-command-option-button'
					: ''}"
				type="button"
				on:click={() => {
					console.log(item);
					if (item?.type === 'pm-project' || item?.type === 'pm-entry') {
						onSelect({
							type: 'pm',
							data: item
						});
					} else {
						onSelect({
							type: 'knowledge',
							data: item
						});
					}
				}}
				on:mousemove={() => {
					selectedIdx = idx;
				}}
				data-selected={idx === selectedIdx}
			>
				<div class="  text-black dark:text-gray-100 flex items-center gap-1">
					<Tooltip
						content={item?.legacy
							? $i18n.t('Legacy')
							: item?.type === 'file'
								? `${item?.collection?.name} > ${$i18n.t('File')}`
								: item?.type === 'collection'
									? $i18n.t('Collection')
									: ''}
						placement="top"
					>
						{#if item?.type === 'pm-project'}
							<Database className="size-4" style="color: #6366f1;" />
						{:else if item?.type === 'pm-entry'}
							<DocumentPage className="size-4" style="color: #6366f1;" />
						{:else if item?.type === 'collection'}
							<Database className="size-4" />
						{:else if item?.type === 'folder'}
							<Folder className="size-4" />
						{:else}
							<DocumentPage className="size-4" />
						{/if}
					</Tooltip>

					<Tooltip content={`${decodeString(item?.name)}`} placement="top-start">
						<div class="line-clamp-1 flex-1">
							{decodeString(item?.name)}
						</div>
					</Tooltip>
				</div>
			</button>
		{/if}
	{/each}

	{#if isYoutubeUrl(query)}
		<button
			class="px-2 py-1 rounded-xl w-full text-left bg-gray-50 dark:bg-gray-800 dark:text-gray-100 selected-command-option-button"
			type="button"
			data-selected={selectedIdx === filteredItems.findIndex((i) => i.type === 'youtube')}
			on:click={() => {
				if (isValidHttpUrl(query)) {
					onSelect({
						type: 'web',
						data: query
					});
				} else {
					toast.error(
						$i18n.t('Oops! Looks like the URL is invalid. Please double-check and try again.')
					);
				}
			}}
		>
			<div class="  text-black dark:text-gray-100 line-clamp-1 flex items-center gap-1">
				<Tooltip content={$i18n.t('YouTube')} placement="top">
					<Youtube className="size-4" />
				</Tooltip>

				<div class="truncate flex-1">
					{query}
				</div>
			</div>
		</button>
	{:else if query.startsWith('http')}
		<button
			class="px-2 py-1 rounded-xl w-full text-left bg-gray-50 dark:bg-gray-800 dark:text-gray-100 selected-command-option-button"
			type="button"
			data-selected={selectedIdx === filteredItems.findIndex((i) => i.type === 'web')}
			on:click={() => {
				if (isValidHttpUrl(query)) {
					onSelect({
						type: 'web',
						data: query
					});
				} else {
					toast.error(
						$i18n.t('Oops! Looks like the URL is invalid. Please double-check and try again.')
					);
				}
			}}
		>
			<div class="  text-black dark:text-gray-100 line-clamp-1 flex items-center gap-1">
				<Tooltip content={$i18n.t('Web')} placement="top">
					<GlobeAlt className="size-4" />
				</Tooltip>

				<div class="truncate flex-1">
					{query}
				</div>
			</div>
		</button>
	{/if}
{/if}
