<script lang="ts">
	import DOMPurify from 'dompurify';
	import { toast } from 'svelte-sonner';

	import { marked } from 'marked';
	import { v4 as uuidv4 } from 'uuid';
	import dayjs from '$lib/dayjs';
	import duration from 'dayjs/plugin/duration';
	import relativeTime from 'dayjs/plugin/relativeTime';

	dayjs.extend(duration);
	dayjs.extend(relativeTime);

	import { onMount, tick, getContext, createEventDispatcher } from 'svelte';

	import { createPicker, getAuthToken } from '$lib/utils/google-drive-picker';
	import { pickAndDownloadFile } from '$lib/utils/onedrive-file-picker';
	import { KokoroWorker } from '$lib/workers/KokoroWorker';

	const dispatch = createEventDispatcher();

	import {
		type Model,
		mobile,
		settings,
		models,
		config,
		showCallOverlay,
		tools,
		skills,
		toolServers,
		terminalServers,
		user as _user,
		showControls,
		showSettings,
		selectedTerminalId,
		TTSWorker,
		temporaryChatEnabled
	} from '$lib/stores';

	import {
		convertHeicToJpeg,
		compressImage,
		createMessagesList,
		extractContentFromFile,
		extractCurlyBraceWords,
		extractInputVariables,
		getAge,
		getCurrentDateTime,
		getFormattedDate,
		getFormattedTime,
		getUserPosition,
		getUserTimezone,
		getWeekday
	} from '$lib/utils';
	import { uploadFile } from '$lib/apis/files';
	import { generateAutoCompletion } from '$lib/apis';
	import { deleteFileById } from '$lib/apis/files';
	import { getChatById } from '$lib/apis/chats';
	import { getSessionUser } from '$lib/apis/auths';
	import { getTools } from '$lib/apis/tools';
	import { getSkills } from '$lib/apis/skills';
	import { getWorkflows, getWorkflow, executeWorkflow, getExecutionStatus } from '$lib/apis/workflow';
	import { getRoles, type RolePrompt } from '$lib/apis/prompts';
	import { currentProject } from '$lib/stores/pm/projectStore';
	import { chatWorkflowState } from '$lib/stores/chatWorkflowState';
	import { getEntries as getPMEntries } from '$lib/apis/pm';

	import { WEBUI_BASE_URL, WEBUI_API_BASE_URL, PASTED_TEXT_CHARACTER_LIMIT } from '$lib/constants';
	import { getOAuthClientAuthorizationUrl } from '$lib/apis/configs';

	import { createNoteHandler } from '../notes/utils';
	import { getSuggestionRenderer } from '../common/RichTextInput/suggestions';

	import InputMenu from './MessageInput/InputMenu.svelte';
	import VoiceRecording from './MessageInput/VoiceRecording.svelte';

	import ToolServersModal from './ToolServersModal.svelte';
	import SkillsModal from './SkillsModal.svelte';

	import RichTextInput from '../common/RichTextInput.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import FileItem from '../common/FileItem.svelte';
	import Image from '../common/Image.svelte';
	import Spinner from '../common/Spinner.svelte';

	import XMark from '../icons/XMark.svelte';
	import GlobeAlt from '../icons/GlobeAlt.svelte';
	import Photo from '../icons/Photo.svelte';
	import Wrench from '../icons/Wrench.svelte';
	import Keyframes from '../icons/Keyframes.svelte';
	import Sparkles from '../icons/Sparkles.svelte';

	import InputVariablesModal from './MessageInput/InputVariablesModal.svelte';
	import Voice from '../icons/Voice.svelte';
	import Terminal from '../icons/Terminal.svelte';
	import IntegrationsMenu from './MessageInput/IntegrationsMenu.svelte';
	import TerminalMenu from './MessageInput/TerminalMenu.svelte';
	import Component from '../icons/Component.svelte';
	import PlusAlt from '../icons/PlusAlt.svelte';
	import Dropdown from '../common/Dropdown.svelte';

	import CommandSuggestionList from './MessageInput/CommandSuggestionList.svelte';
	import Knobs from '../icons/Knobs.svelte';
	import ValvesModal from '../workspace/common/ValvesModal.svelte';
	import Note from '../icons/Note.svelte';
	import { goto } from '$app/navigation';
	import InputModal from '../common/InputModal.svelte';
	import Expand from '../icons/Expand.svelte';
	import QueuedMessageItem from './MessageInput/QueuedMessageItem.svelte';
	import TaskList from './Messages/ResponseMessage/TaskList.svelte';
	import PMDataSelector from '../pm/PMDataSelector.svelte';
	import WorkflowSelector from './WorkflowSelector.svelte';

	const i18n = getContext('i18n');

	export let onUpload: Function = (e) => {};
	export let onChange: Function = () => {};

	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;
	export let generating = false;
	export let uploadPending = false;

	export let atSelectedModel: Model | undefined = undefined;
	export let selectedModels: [''];

	let selectedModelIds = [];
	$: selectedModelIds = atSelectedModel !== undefined ? [atSelectedModel.id] : selectedModels;

	export let history;
	export let taskIds = null;

	$: isActive =
		(taskIds && taskIds.length > 0) ||
		(history.currentId && history.messages[history.currentId]?.done != true) ||
		generating;

	export let prompt = '';
	export let files = [];

	export let selectedToolIds = [];
	export let selectedSkillIds = [];
	export let selectedFilterIds = [];

	export let imageGenerationEnabled = false;
	export let webSearchEnabled = false;
	export let codeInterpreterEnabled = false;
	export let pmWorkbenchEnabled = false;

	export let pendingOAuthTools = [];

	let showTerminalMenu = false;

	export let messageQueue: { id: string; prompt: string; files: any[] }[] = [];
	export let onQueueSendNow: (id: string) => void = () => {};
	export let onQueueEdit: (id: string) => void = () => {};
	export let onQueueDelete: (id: string) => void = () => {};

	export let chatTasks = [];

	// Part B: 角色提示词
	// 当前选中的角色（由父组件 Chat.svelte 通过 bind 双向绑定）
	export let selectedRole: RolePrompt | null = null;
	// 角色列表（在 onMount 时加载）
	let roles: RolePrompt[] = [];
	let showRoleMenu = false;

	let inputContent = null;

	let showInputVariablesModal = false;
	let inputVariablesModalCallback = (variableValues) => {};
	let inputVariables = {};
	let inputVariableValues = {};

	let showValvesModal = false;
	let selectedValvesType = 'tool'; // 'tool' or 'function'
	let selectedValvesItemId = null;
	let integrationsMenuCloseOnOutsideClick = true;
	let showPMDataSelector = false;

	$: if (!showValvesModal) {
		integrationsMenuCloseOnOutsideClick = true;
	}

	$: onChange({
		prompt,
		files: files
			.filter((file) => file.type !== 'image')
			.map((file) => {
				return {
					...file,
					user: undefined,
					access_grants: undefined
				};
			}),
		selectedToolIds,
		selectedSkillIds,
		selectedFilterIds,
		imageGenerationEnabled,
		webSearchEnabled,
		codeInterpreterEnabled
	});

	const inputVariableHandler = async (text: string): Promise<string> => {
		inputVariables = extractInputVariables(text);

		// No variables? return the original text immediately.
		if (Object.keys(inputVariables).length === 0) {
			return text;
		}

		// Show modal and wait for the user's input.
		showInputVariablesModal = true;
		return await new Promise<string>((resolve) => {
			inputVariablesModalCallback = (variableValues) => {
				inputVariableValues = { ...inputVariableValues, ...variableValues };
				replaceVariables(inputVariableValues);
				showInputVariablesModal = false;
				resolve(text);
			};
		});
	};

	const textVariableHandler = async (text: string) => {
		if (text.includes('{{CLIPBOARD}}')) {
			const clipboardText = await navigator.clipboard.readText().catch((err) => {
				toast.error($i18n.t('Failed to read clipboard contents'));
				return '{{CLIPBOARD}}';
			});

			const clipboardItems = await navigator.clipboard.read().catch((err) => {
				console.error('Failed to read clipboard items:', err);
				return [];
			});

			for (const item of clipboardItems) {
				for (const type of item.types) {
					if (type.startsWith('image/')) {
						const blob = await item.getType(type);
						const file = new File([blob], `clipboard-image.${type.split('/')[1]}`, {
							type: type
						});

						inputFilesHandler([file]);
					}
				}
			}

			text = text.replaceAll('{{CLIPBOARD}}', clipboardText.replaceAll('\r\n', '\n'));
		}

		if (text.includes('{{USER_LOCATION}}')) {
			let location;
			try {
				location = await getUserPosition();
			} catch (error) {
				toast.error($i18n.t('Location access not allowed'));
				location = 'LOCATION_UNKNOWN';
			}
			text = text.replaceAll('{{USER_LOCATION}}', String(location));
		}

		const sessionUser = await getSessionUser(localStorage.token);

		if (text.includes('{{USER_NAME}}')) {
			const name = sessionUser?.name || 'User';
			text = text.replaceAll('{{USER_NAME}}', name);
		}

		if (text.includes('{{USER_EMAIL}}')) {
			const email = sessionUser?.email || '';

			if (email) {
				text = text.replaceAll('{{USER_EMAIL}}', email);
			}
		}

		if (text.includes('{{USER_BIO}}')) {
			const bio = sessionUser?.bio || '';

			if (bio) {
				text = text.replaceAll('{{USER_BIO}}', bio);
			}
		}

		if (text.includes('{{USER_GENDER}}')) {
			const gender = sessionUser?.gender || '';

			if (gender) {
				text = text.replaceAll('{{USER_GENDER}}', gender);
			}
		}

		if (text.includes('{{USER_BIRTH_DATE}}')) {
			const birthDate = sessionUser?.date_of_birth || '';

			if (birthDate) {
				text = text.replaceAll('{{USER_BIRTH_DATE}}', birthDate);
			}
		}

		if (text.includes('{{USER_AGE}}')) {
			const birthDate = sessionUser?.date_of_birth || '';

			if (birthDate) {
				// calculate age using date
				const age = getAge(birthDate);
				text = text.replaceAll('{{USER_AGE}}', age);
			}
		}

		if (text.includes('{{USER_LANGUAGE}}')) {
			const language = localStorage.getItem('locale') || 'en-US';
			text = text.replaceAll('{{USER_LANGUAGE}}', language);
		}

		if (text.includes('{{CURRENT_DATE}}')) {
			const date = getFormattedDate();
			text = text.replaceAll('{{CURRENT_DATE}}', date);
		}

		if (text.includes('{{CURRENT_TIME}}')) {
			const time = getFormattedTime();
			text = text.replaceAll('{{CURRENT_TIME}}', time);
		}

		if (text.includes('{{CURRENT_DATETIME}}')) {
			const dateTime = getCurrentDateTime();
			text = text.replaceAll('{{CURRENT_DATETIME}}', dateTime);
		}

		if (text.includes('{{CURRENT_TIMEZONE}}')) {
			const timezone = getUserTimezone();
			text = text.replaceAll('{{CURRENT_TIMEZONE}}', timezone);
		}

		if (text.includes('{{CURRENT_WEEKDAY}}')) {
			const weekday = getWeekday();
			text = text.replaceAll('{{CURRENT_WEEKDAY}}', weekday);
		}

		return text;
	};

	const replaceVariables = (variables: Record<string, any>) => {
		console.log('Replacing variables:', variables);

		const chatInput = document.getElementById('chat-input');

		if (chatInput) {
			chatInputElement.replaceVariables(variables);
			chatInputElement.focus();
		}
	};

	export const setText = async (text?: string, cb?: (text: string) => void) => {
		const chatInput = document.getElementById('chat-input');

		if (chatInput) {
			if (text !== '') {
				text = await textVariableHandler(text || '');
			}

			chatInputElement?.setText(text);
			if (!$showCallOverlay) {
				chatInputElement?.focus();
			}

			if (text !== '') {
				text = await inputVariableHandler(text);
			}

			await tick();
			if (cb) await cb(text);
		}
	};

	const getCommand = () => {
		const chatInput = document.getElementById('chat-input');
		let word = '';

		if (chatInput) {
			word = chatInputElement?.getWordAtDocPos();
		}

		return word;
	};

	const replaceCommandWithText = (text) => {
		const chatInput = document.getElementById('chat-input');
		if (!chatInput) return;

		chatInputElement?.replaceCommandWithText(text);
	};

	const insertTextAtCursor = async (text: string) => {
		const chatInput = document.getElementById('chat-input');
		if (!chatInput) return;

		text = await textVariableHandler(text);

		if (command) {
			replaceCommandWithText(text);
		} else {
			chatInputElement?.insertContent(text);
		}

		await tick();
		text = await inputVariableHandler(text);
		await tick();

		const chatInputContainer = document.getElementById('chat-input-container');
		if (chatInputContainer) {
			chatInputContainer.scrollTop = chatInputContainer.scrollHeight;
		}

		await tick();
		if (chatInput) {
			chatInput.focus();
			chatInput.dispatchEvent(new Event('input'));

			const words = extractCurlyBraceWords(prompt);

			if (words.length > 0) {
				const word = words.at(0);
				await tick();
			} else {
				chatInput.scrollTop = chatInput.scrollHeight;
			}
		}
	};

	let command = '';
	export let showCommands = false;
	$: showCommands =
		['/', '#', '@', '$', ':'].includes(command?.charAt(0)) || '\\#' === command?.slice(0, 2);
	let suggestions = null;

	let showTools = false;
	let showSkills = false;

	let loaded = false;
	let recording = false;

	let isComposing = false;
	// Safari has a bug where compositionend is not triggered correctly #16615
	// when using the virtual keyboard on iOS.
	let compositionEndedAt = -2e8;
	const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
	function inOrNearComposition(event: Event) {
		if (isComposing) {
			return true;
		}
		// See https://www.stum.de/2016/06/24/handling-ime-events-in-javascript/.
		// On Japanese input method editors (IMEs), the Enter key is used to confirm character
		// selection. On Safari, when Enter is pressed, compositionend and keydown events are
		// emitted. The keydown event triggers newline insertion, which we don't want.
		// This method returns true if the keydown event should be ignored.
		// We only ignore it once, as pressing Enter a second time *should* insert a newline.
		// Furthermore, the keydown event timestamp must be close to the compositionEndedAt timestamp.
		// This guards against the case where compositionend is triggered without the keyboard
		// (e.g. character confirmation may be done with the mouse), and keydown is triggered
		// afterwards- we wouldn't want to ignore the keydown event in this case.
		if (isSafari && Math.abs(event.timeStamp - compositionEndedAt) < 500) {
			compositionEndedAt = -2e8;
			return true;
		}
		return false;
	}

	let chatInputContainerElement;
	let chatInputElement;

	let filesInputElement;
	let commandsElement;

	let inputFiles;

	let showInputModal = false;

	export let dragged = false;
	let shiftKey = false;

	let user = null;
	export let placeholder = '';

	let visionCapableModels = [];
	$: visionCapableModels = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.vision ?? true
	);

	let fileUploadCapableModels = [];
	$: fileUploadCapableModels = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.file_upload ?? true
	);

	let webSearchCapableModels = [];
	$: webSearchCapableModels = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.web_search ?? true
	);

	let imageGenerationCapableModels = [];
	$: imageGenerationCapableModels = (
		atSelectedModel?.id ? [atSelectedModel.id] : selectedModels
	).filter(
		(model) =>
			$models.find((m) => m.id === model)?.info?.meta?.capabilities?.image_generation ?? true
	);

	let codeInterpreterCapableModels = [];
	$: codeInterpreterCapableModels = (
		atSelectedModel?.id ? [atSelectedModel.id] : selectedModels
	).filter(
		(model) =>
			$models.find((m) => m.id === model)?.info?.meta?.capabilities?.code_interpreter ?? true
	);

	let terminalCapableModels = [];
	$: terminalCapableModels = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).filter(
		(model) => $models.find((m) => m.id === model)?.info?.meta?.capabilities?.terminal ?? true
	);

	let toggleFilters = [];
	$: toggleFilters = (atSelectedModel?.id ? [atSelectedModel.id] : selectedModels)
		.map((id) => ($models.find((model) => model.id === id) || {})?.filters ?? [])
		.reduce((acc, filters) => acc.filter((f1) => filters.some((f2) => f2.id === f1.id)));

	let showToolsButton = false;
	$: showToolsButton = ($tools ?? []).length > 0 || ($toolServers ?? []).length > 0;

	let showSkillsButton = false;
	$: showSkillsButton = ($skills ?? []).some((skill) => skill.is_active);

	let showWebSearchButton = false;
	$: showWebSearchButton =
		(atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).length ===
			webSearchCapableModels.length &&
		$config?.features?.enable_web_search &&
		($_user.role === 'admin' || $_user?.permissions?.features?.web_search);

	let showImageGenerationButton = false;
	$: showImageGenerationButton =
		(atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).length ===
			imageGenerationCapableModels.length &&
		$config?.features?.enable_image_generation &&
		($_user.role === 'admin' || $_user?.permissions?.features?.image_generation);

	let showCodeInterpreterButton = false;
	$: showCodeInterpreterButton =
		!$selectedTerminalId &&
		(atSelectedModel?.id ? [atSelectedModel.id] : selectedModels).length ===
			codeInterpreterCapableModels.length &&
		$config?.features?.enable_code_interpreter &&
		($_user.role === 'admin' || $_user?.permissions?.features?.code_interpreter);

	let showPMWorkbenchButton = false;
	$: showPMWorkbenchButton =
		$config?.features?.enable_pm_workbench !== false;

	let showWorkflowButton = false;
	// Re-enabled: chat-scoped workflow execution reuses the existing
	// POST /workflows/{id}/execute + GET status routes (real engine).
	// Coexists with PM Workbench button — PM Workbench provides context
	// (Agent CRUD on PM data), WorkflowSelector runs a fixed flow inline.
	$: showWorkflowButton = workflows.length > 0;

	let hasRealProject = false;
	$: hasRealProject = $currentProject && $currentProject.id !== 'default';

	// Workflow state
	// D32: selectedWorkflowId / pinnedWorkflowIds 通过 store 跨 MessageInput 实例持久化，
	// 解决 Chat.svelte {#if} 分支切换导致组件卸载重挂载时状态丢失的问题。
	let workflows = [];
	let selectedWorkflowId = '';
	let pinnedWorkflowIds: string[] = [];
	// 订阅 store：组件重挂载时从 store 恢复状态（store → 局部变量单向同步）
	// L5: [Bug4-Diag] 标签 + 恢复日志，便于排查「发送后工作流被自动取消」
	$: {
		const newState = $chatWorkflowState;
		const prevSelected = selectedWorkflowId;
		selectedWorkflowId = newState.selectedWorkflowId;
		pinnedWorkflowIds = newState.pinnedWorkflowIds;
		if (prevSelected !== newState.selectedWorkflowId) {
			console.log('[Bug4-Diag] store restored:', {
				prevSelected,
				selectedWorkflowId: newState.selectedWorkflowId,
				pinnedWorkflowIds: newState.pinnedWorkflowIds,
			});
		}
	}
	let showWorkflowSelector = false;
	let workflowExecuting = false;

	// 写入时同时更新局部变量和 store（确保跨实例同步）
	function setSelectedWorkflowId(id: string) {
		selectedWorkflowId = id;
		chatWorkflowState.update((s) => ({ ...s, selectedWorkflowId: id }));
	}
	function setPinnedWorkflowIds(ids: string[]) {
		pinnedWorkflowIds = ids;
		chatWorkflowState.update((s) => ({ ...s, pinnedWorkflowIds: ids }));
	}

	// Load workflows on mount
	const loadWorkflows = async () => {
		try {
			workflows = await getWorkflows(localStorage.token);
		} catch (e) {
			console.error('Failed to load workflows:', e);
		}
	};

	// Parse workflow command from prompt
	const parseWorkflowCommand = (text: string): { workflowId: string | null; cleanText: string } => {
		const match = text.match(/^\/workflow-([a-zA-Z0-9_-]+)\s*(.*)$/);
		if (match) {
			return { workflowId: match[1], cleanText: match[2] || '' };
		}
		return { workflowId: null, cleanText: text };
	};

	// D5: 选择工作流后不再自动执行，改为将工作流信息 + 项目条目摘要注入 prompt，
	// 由 AI 在下一次发送时决定是否调用工作流（避免误触执行和 disconnected nodes 报错）。
	const handleWorkflowSelect = async (workflowId: string) => {
		// L4: 空 id 表示用户取消选择（点 × 按钮或反选同一工作流）
		if (!workflowId) {
			setSelectedWorkflowId('');
			console.log('[Bug4-Diag] handleWorkflowSelect: cleared selection');
			toast.info('已取消工作流选择');
			return;
		}
		if (!$currentProject || $currentProject.id === 'default') {
			toast.error('请先选择真实项目');
			return;
		}
		setSelectedWorkflowId(workflowId);

		const wf = workflows.find((w: any) => w.id === workflowId);
		const wfName = wf?.name || workflowId;
		const wfDesc = wf?.description || '';

		const token = localStorage.token;
		if (!token) {
			toast.error('未登录');
			return;
		}

		// D5: 注入工作流基础信息
		let contextHint = `\n[已选择工作流「${wfName}」(id: ${workflowId})]`;
		if (wfDesc) contextHint += `\n描述：${wfDesc}`;
		contextHint += `\n项目上下文：${$currentProject.name}（id: ${$currentProject.id}）`;

		// D12: 加载工作流定义，提取输入参数 schema 和节点摘要
		try {
			const wfDef = await getWorkflow(token, workflowId);
			const nodes = wfDef?.nodes || [];
			// 兼容 nodes 是字符串（JSON）或数组
			const nodesArr: any[] = typeof nodes === 'string' ? safeJsonParse(nodes, []) : nodes;
			const startNode = nodesArr.find((n: any) => n.type === 'start' || n.type === 'start_node');
			const inputSchema =
				startNode?.data?.inputs ||
				startNode?.config?.inputs ||
				startNode?.input_schema ||
				[];
			if (Array.isArray(inputSchema) && inputSchema.length > 0) {
				contextHint += `\n工作流输入参数（必填项必须填入 inputs）：`;
				for (const inp of inputSchema) {
					const name = inp.name || inp.key || inp.id;
					const type = inp.type || 'string';
					const desc = inp.description || '';
					const req = inp.required ? ' [必填]' : '';
					contextHint += `\n- ${name}（${type}）${desc ? '：' + desc : ''}${req}`;
				}
			}
			// 节点摘要（让 AI 知道工作流做什么）
			const nodeSummary = nodesArr
				.filter((n: any) => !['start', 'end', 'start_node', 'end_node'].includes(n.type))
				.map((n: any) => `- ${n.type}：${n.data?.label || n.name || n.id}`)
				.slice(0, 10)
				.join('\n');
			if (nodeSummary) {
				contextHint += `\n工作流节点：\n${nodeSummary}`;
			}
		} catch (e) {
			console.warn('[chat] load workflow def failed:', e);
		}

		// D5: 加载项目条目摘要（让 AI 能"在项目找到我要的文档"）
		try {
			const entries = await getPMEntries(token, $currentProject.id);
			const list = Array.isArray(entries) ? entries.slice(0, 20) : [];
			if (list.length > 0) {
				const entriesSummary = list
					.map((e: any) => `- ${e.title || '(无标题)'} [${e.module_type || 'unknown'}] (id: ${e.id})`)
					.join('\n');
				contextHint += `\n项目条目摘要（最多 20 条，可作为工作流输入的数据源）：\n${entriesSummary}`;
			}
		} catch (e) {
			console.warn('[chat] load entries failed:', e);
		}

		// D16: 编排协议指令 — AI 决定执行时输出结构化 JSON
		contextHint += `\n\n编排协议（重要）：`;
		contextHint += `\n- 若用户的问题需要执行该工作流，请在回复中输出 JSON 块（用 \`\`\`json 包裹）：`;
		contextHint += `\n  \`\`\`json`;
		contextHint += `\n  {"action":"execute_workflow","workflow_id":"${workflowId}","inputs":{"参数名":"值"}}`;
		contextHint += `\n  \`\`\``;
		contextHint += `\n- inputs 必须填入所有必填参数；可从项目条目中提取内容作为参数值。`;
		contextHint += `\n- JSON 块前后可有解释性文字（向用户说明你为什么决定执行该工作流、从哪里取了什么数据），但 JSON 必须是有效的单个对象。`;
		contextHint += `\n- 若用户未明确要求执行工作流，或工作流不适合解决用户问题，正常回复即可，不要输出该 JSON。`;

		prompt = prompt ? `${prompt}\n${contextHint}` : contextHint;
		toast.info(`已选择工作流「${wfName}」，AI 将根据您的下一个问题决定是否执行`);
	};

	// 辅助函数：安全 JSON 解析（用于兼容 nodes 字段是字符串或数组）
	function safeJsonParse<T>(s: string, fallback: T): T {
		try {
			return JSON.parse(s);
		} catch (_) {
			return fallback;
		}
	}

	// Handle workflow pin
	const handleWorkflowPin = (workflowId: string) => {
		if (!pinnedWorkflowIds.includes(workflowId)) {
			setPinnedWorkflowIds([...pinnedWorkflowIds, workflowId]);
		}
	};

	// Handle workflow unpin
	const handleWorkflowUnpin = (workflowId: string) => {
		setPinnedWorkflowIds(pinnedWorkflowIds.filter(id => id !== workflowId));
	};

	// Disable code interpreter when terminal is active (mutually exclusive)
	$: if ($selectedTerminalId && codeInterpreterEnabled) {
		codeInterpreterEnabled = false;
	}

	// Clear selected terminal when model doesn't support terminal
	$: if ($selectedTerminalId && terminalCapableModels.length === 0) {
		selectedTerminalId.set(null);
	}

	const scrollToBottom = () => {
		const element = document.getElementById('messages-container');
		element.scrollTo({
			top: element.scrollHeight,
			behavior: 'smooth'
		});
	};

	const screenCaptureHandler = async () => {
		try {
			// Request screen media
			const mediaStream = await navigator.mediaDevices.getDisplayMedia({
				video: { cursor: 'never' },
				audio: false
			});
			// Once the user selects a screen, temporarily create a video element
			const video = document.createElement('video');
			video.srcObject = mediaStream;
			// Ensure the video loads without affecting user experience or tab switching
			await video.play();
			// Set up the canvas to match the video dimensions
			const canvas = document.createElement('canvas');
			canvas.width = video.videoWidth;
			canvas.height = video.videoHeight;
			// Grab a single frame from the video stream using the canvas
			const context = canvas.getContext('2d');
			context.drawImage(video, 0, 0, canvas.width, canvas.height);
			// Stop all video tracks (stop screen sharing) after capturing the image
			mediaStream.getTracks().forEach((track) => track.stop());

			// bring back focus to this current tab, so that the user can see the screen capture
			window.focus();

			// Convert the canvas to a Base64 image URL
			const imageUrl = canvas.toDataURL('image/png');
			const blob = await (await fetch(imageUrl)).blob();
			const file = new File([blob], `screen-capture-${Date.now()}.png`, { type: 'image/png' });
			inputFilesHandler([file]);
			// Clean memory: Clear video srcObject
			video.srcObject = null;
		} catch (error) {
			// Handle any errors (e.g., user cancels screen sharing)
			console.error('Error capturing screen:', error);
		}
	};

	const uploadFileHandler = async (file, process = true, itemData = {}) => {
		if ($_user?.role !== 'admin' && !($_user?.permissions?.chat?.file_upload ?? true)) {
			toast.error($i18n.t('You do not have permission to upload files.'));
			return null;
		}

		if (fileUploadCapableModels.length !== selectedModels.length) {
			toast.error($i18n.t('Model(s) do not support file upload'));
			return null;
		}

		const tempItemId = uuidv4();
		const fileItem = {
			type: 'file',
			file: '',
			id: null,
			url: '',
			name: file.name,
			collection_name: '',
			status: 'uploading',
			size: file.size,
			error: '',
			itemId: tempItemId,
			...itemData
		};

		if (fileItem.size == 0) {
			toast.error($i18n.t('You cannot upload an empty file.'));
			return null;
		}

		files = [...files, fileItem];

		if (!$temporaryChatEnabled) {
			try {
				// If the file is an audio file, provide the language for STT.
				let metadata = null;
				if (
					(file.type.startsWith('audio/') || file.type.startsWith('video/')) &&
					$settings?.audio?.stt?.language
				) {
					metadata = {
						language: $settings?.audio?.stt?.language
					};
				}

				// During the file upload, file content is automatically extracted.
				const uploadedFile = await uploadFile(localStorage.token, file, metadata, process);

				if (uploadedFile) {
					console.log('File upload completed:', {
						id: uploadedFile.id,
						name: fileItem.name,
						collection: uploadedFile?.meta?.collection_name
					});

					if (uploadedFile.error) {
						console.warn('File upload warning:', uploadedFile.error);
						toast.warning(uploadedFile.error);
					}

					fileItem.status = 'uploaded';
					fileItem.file = uploadedFile;
					fileItem.id = uploadedFile.id;
					fileItem.collection_name =
						uploadedFile?.meta?.collection_name || uploadedFile?.collection_name;
					fileItem.content_type = uploadedFile.meta?.content_type || uploadedFile.content_type;
					fileItem.url = `${uploadedFile.id}`;

					files = files;
				} else {
					files = files.filter((item) => item?.itemId !== tempItemId);
				}
			} catch (e) {
				toast.error(`${e}`);
				files = files.filter((item) => item?.itemId !== tempItemId);
			}
		} else {
			// If temporary chat is enabled, we just add the file to the list without uploading it.

			const content = await extractContentFromFile(file).catch((error) => {
				toast.error(
					$i18n.t('Failed to extract content from the file: {{error}}', { error: error })
				);
				return null;
			});

			if (content === null) {
				toast.error($i18n.t('Failed to extract content from the file.'));
				files = files.filter((item) => item?.itemId !== tempItemId);
				return null;
			} else {
				console.log('Extracted content from file:', {
					name: file.name,
					size: file.size,
					content: content
				});

				fileItem.status = 'uploaded';
				fileItem.type = 'text';
				fileItem.content = content;
				fileItem.id = uuidv4(); // Temporary ID for the file

				files = files;
			}
		}
	};

	const inputFilesHandler = async (inputFiles) => {
		console.log('Input files handler called with:', inputFiles);

		if (
			($config?.file?.max_count ?? null) !== null &&
			files.length + inputFiles.length > $config?.file?.max_count
		) {
			toast.error(
				$i18n.t(`You can only chat with a maximum of {{maxCount}} file(s) at a time.`, {
					maxCount: $config?.file?.max_count
				})
			);
			return;
		}

		inputFiles.forEach(async (file) => {
			console.log('Processing file:', {
				name: file.name,
				type: file.type,
				size: file.size,
				extension: file.name.split('.').at(-1)
			});

			if (
				($config?.file?.max_size ?? null) !== null &&
				file.size > ($config?.file?.max_size ?? 0) * 1024 * 1024
			) {
				console.log('File exceeds max size limit:', {
					fileSize: file.size,
					maxSize: ($config?.file?.max_size ?? 0) * 1024 * 1024
				});
				toast.error(
					$i18n.t(`File size should not exceed {{maxSize}} MB.`, {
						maxSize: $config?.file?.max_size
					})
				);
				return;
			}

			if (file['type'].startsWith('image/')) {
				if (visionCapableModels.length === 0) {
					toast.error($i18n.t('Selected model(s) do not support image inputs'));
					return;
				}

				const compressImageHandler = async (imageUrl, settings = {}, config = {}) => {
					// Quick shortcut so we don’t do unnecessary work.
					const settingsCompression = settings?.imageCompression ?? false;
					const configWidth = config?.file?.image_compression?.width ?? null;
					const configHeight = config?.file?.image_compression?.height ?? null;

					// If neither settings nor config wants compression, return original URL.
					if (!settingsCompression && !configWidth && !configHeight) {
						return imageUrl;
					}

					// Default to null (no compression unless set)
					let width = null;
					let height = null;

					// If user/settings want compression, pick their preferred size.
					if (settingsCompression) {
						width = settings?.imageCompressionSize?.width ?? null;
						height = settings?.imageCompressionSize?.height ?? null;
					}

					// Apply config limits as an upper bound if any
					if (configWidth && (width === null || width > configWidth)) {
						width = configWidth;
					}
					if (configHeight && (height === null || height > configHeight)) {
						height = configHeight;
					}

					// Do the compression if required
					if (width || height) {
						return await compressImage(imageUrl, width, height);
					}
					return imageUrl;
				};

				let reader = new FileReader();

				reader.onload = async (event) => {
					let imageUrl = event.target.result;

					// Compress the image if settings or config require it
					imageUrl = await compressImageHandler(imageUrl, $settings, $config);

					if ($temporaryChatEnabled) {
						files = [
							...files,
							{
								type: 'image',
								url: imageUrl
							}
						];
					} else {
						const blob = await (await fetch(imageUrl)).blob();
						const compressedFile = new File([blob], file.name, { type: file.type });

						uploadFileHandler(compressedFile, false);
					}
				};

				reader.readAsDataURL(file['type'] === 'image/heic' ? await convertHeicToJpeg(file) : file);
			} else {
				uploadFileHandler(file);
			}
		});
	};

	const createNote = async () => {
		if (inputContent?.md.trim() === '' && inputContent?.html.trim() === '') {
			toast.error($i18n.t('Cannot create an empty note.'));
			return;
		}

		const res = await createNoteHandler(
			dayjs().format('YYYY-MM-DD'),
			inputContent?.md,
			inputContent?.html
		);

		if (res) {
			// Clear the input content saved in session storage.
			sessionStorage.removeItem('chat-input');
			goto(`/notes/${res.id}`);
		}
	};

	const onDragOver = (e: DragEvent) => {
		e.preventDefault();

		// Check if a file or a sidebar chat item is being dragged.
		if (e.dataTransfer?.types?.includes('Files') || e.dataTransfer?.types?.includes('text/plain')) {
			dragged = true;
		} else {
			dragged = false;
		}
	};

	const onDragLeave = (e: DragEvent) => {
		if ((e.currentTarget as HTMLElement)?.contains(e.relatedTarget as Node)) {
			return;
		}
		dragged = false;
	};

	const onDrop = async (e: DragEvent) => {
		e.preventDefault();
		console.log(e);

		// Check if the dropped data is a sidebar chat item
		const textData = e.dataTransfer?.getData('text/plain');
		if (textData) {
			try {
				const data = JSON.parse(textData);
				if (data.type === 'chat' && data.id) {
					// Fetch the chat to get its title, then add as a reference chat
					const chat = await getChatById(localStorage.token, data.id);
					if (chat) {
						const chatItem = {
							type: 'chat',
							id: chat.id,
							name: chat.title,
							collection_name: '',
							status: 'processed'
						};
						if (!files.find((f) => f.id === chatItem.id)) {
							files = [...files, chatItem];
						}
					}
					dragged = false;
					e.stopPropagation();
					return;
				}
			} catch (_) {
				// Not valid JSON — fall through to file handling
			}
		}

		if (e.dataTransfer?.files) {
			const inputFiles = Array.from(e.dataTransfer?.files);
			if (inputFiles && inputFiles.length > 0) {
				console.log(inputFiles);
				inputFilesHandler(inputFiles);
			}
		}

		dragged = false;
	};

	const onKeyDown = (e: KeyboardEvent) => {
		if (e.key === 'Shift') {
			shiftKey = true;
		}

		// Cmd/Ctrl+Shift+L to toggle dictation
		if (e.key.toLowerCase() === 'l' && (e.metaKey || e.ctrlKey) && e.shiftKey) {
			e.preventDefault();
			if (recording) {
				// Confirm and stop recording
				document.getElementById('confirm-recording-button')?.click();
			} else {
				// Start recording (same logic as voice-input-button click)
				document.getElementById('voice-input-button')?.click();
			}
			return;
		}

		if (e.key === 'Escape') {
			console.log('Escape');
			dragged = false;
		}
	};

	const onKeyUp = (e: KeyboardEvent) => {
		if (e.key === 'Shift') {
			shiftKey = false;
		}
	};

	const onFocus = () => {};

	const onBlur = () => {
		shiftKey = false;
	};

	// ===== Part B: 角色提示词 =====

	// 加载当前用户可见的角色列表
	const loadRoles = async () => {
		try {
			roles = await getRoles(localStorage.token);
		} catch (err) {
			console.error('Failed to load roles:', err);
			roles = [];
		}
	};

	// 选择角色：将角色的 tools 合并进 selectedToolIds，并通过事件通知父组件
	// 更新 params.system。仅影响后续消息，历史消息不变（由父组件控制）。
	const handleRoleSelect = (role: RolePrompt) => {
		// 取消之前选中角色的工具（如果有的话），避免叠加
		if (selectedRole && selectedRole.id !== role.id) {
			const prevTools = selectedRole.tools || [];
			selectedToolIds = selectedToolIds.filter((id) => !prevTools.includes(id));
		}
		// 合并新角色的工具（去重）
		const newTools = role.tools || [];
		selectedToolIds = [...new Set([...selectedToolIds, ...newTools])];
		selectedRole = role;
		showRoleMenu = false;
		// 通知父组件（Chat.svelte）更新 params.system
		dispatch('roleChange', role);
	};

	// 取消角色：移除该角色的工具，清空 params.system（通过事件）
	const handleRoleClear = () => {
		if (selectedRole) {
			const prevTools = selectedRole.tools || [];
			selectedToolIds = selectedToolIds.filter((id) => !prevTools.includes(id));
		}
		selectedRole = null;
		showRoleMenu = false;
		dispatch('roleChange', null);
	};

	onMount(() => {
		// 加载角色提示词列表（用于角色选择器）
		loadRoles();

		suggestions = [
			{
				char: '@',
				render: getSuggestionRenderer(CommandSuggestionList, {
					i18n,
					onSelect: (e) => {
						const { type, data } = e;

						if (type === 'model') {
							atSelectedModel = data;
						}

						document.getElementById('chat-input')?.focus();
					},

					insertTextHandler: insertTextAtCursor,
					onUpload: (e) => {
						const { type, data } = e;

						if (type === 'file') {
							if (files.find((f) => f.id === data.id)) {
								return;
							}
							files = [
								...files,
								{
									...data,
									status: 'processed'
								}
							];
						} else {
							if (files.find((f) => f.url === data || f.name === data)) {
								return;
							}
							onUpload(e);
						}
					}
				})
			},
			{
				char: '/',
				render: getSuggestionRenderer(CommandSuggestionList, {
					i18n,
					onSelect: (e) => {
						const { type, data } = e;

						if (type === 'model') {
							atSelectedModel = data;
						}

						document.getElementById('chat-input')?.focus();
					},

					insertTextHandler: insertTextAtCursor,
					onUpload: (e) => {
						const { type, data } = e;

						if (type === 'file') {
							if (files.find((f) => f.id === data.id)) {
								return;
							}
							files = [
								...files,
								{
									...data,
									status: 'processed'
								}
							];
						} else {
							if (files.find((f) => f.url === data || f.name === data)) {
								return;
							}
							onUpload(e);
						}
					}
				})
			},
			{
				char: '#',
				render: getSuggestionRenderer(CommandSuggestionList, {
					i18n,
					onSelect: (e) => {
						const { type, data } = e;

						if (type === 'model') {
							atSelectedModel = data;
						}

						document.getElementById('chat-input')?.focus();
					},

					insertTextHandler: insertTextAtCursor,
					onUpload: (e) => {
						const { type, data } = e;

						if (type === 'file') {
							if (files.find((f) => f.id === data.id)) {
								return;
							}
							files = [
								...files,
								{
									...data,
									status: 'processed'
								}
							];
						} else if (type === 'pm') {
							const pmRef = {
								id: `pm-${data.projectId}${data.id ? '-' + data.id : ''}`,
								name: data.name,
								type: data.type === 'pm-project' ? 'pm-project' : 'pm-entry',
								status: 'processed',
								url: `/pm/${data.projectId}`,
								data: {
									projectId: data.projectId,
									projectName: data.projectName,
									entryId: data.id,
									entryTitle: data.name,
									moduleType: data.moduleType
								}
							};
							if (files.find((f) => f.id === pmRef.id)) {
								return;
							}
							files = [...files, pmRef];
						} else {
							if (files.find((f) => f.url === data || f.name === data)) {
								return;
							}
							onUpload(e);
						}
					}
				})
			},
			{
				char: '$',
				render: getSuggestionRenderer(CommandSuggestionList, {
					i18n,
					onSelect: (e) => {
						document.getElementById('chat-input')?.focus();
					},

					insertTextHandler: insertTextAtCursor,
					onUpload: () => {}
				})
			},
			{
				char: ':',
				allowSpaces: false,
				command: ({ editor, range, props }) => {
					// Convert the Unicode hex codepoint (e.g. "1F44B") to the actual emoji character (👋)
					const codepoint = props.id;
					const emoji = String.fromCodePoint(parseInt(codepoint, 16));
					editor.chain().focus().deleteRange(range).insertContent(emoji).run();
				},
				render: getSuggestionRenderer(CommandSuggestionList, {
					i18n,
					onSelect: (e) => {
						document.getElementById('chat-input')?.focus();
					},

					insertTextHandler: insertTextAtCursor,
					onUpload: () => {}
				})
			}
		];
		loaded = true;

		window.setTimeout(() => {
			const chatInput = document.getElementById('chat-input');
			chatInput?.focus();
		}, 0);

		window.addEventListener('keydown', onKeyDown);
		window.addEventListener('keyup', onKeyUp);

		window.addEventListener('focus', onFocus);
		window.addEventListener('blur', onBlur);

		let isDestroyed = false;
		let dropzoneElement: HTMLElement | null = null;
		const initialize = async () => {
			await tick();
			if (isDestroyed) return;

			dropzoneElement = document.getElementById('chat-pane');
			if (dropzoneElement) {
				dropzoneElement.addEventListener('dragover', onDragOver, true);
				dropzoneElement.addEventListener('drop', onDrop, true);
				dropzoneElement.addEventListener('dragleave', onDragLeave);
			}

			tools.set(await getTools(localStorage.token));
			skills.set(await getSkills(localStorage.token));
			await loadWorkflows();
		};
		initialize();

		return () => {
			isDestroyed = true;

			window.removeEventListener('keydown', onKeyDown);
			window.removeEventListener('keyup', onKeyUp);

			window.removeEventListener('focus', onFocus);
			window.removeEventListener('blur', onBlur);

			if (dropzoneElement) {
				dropzoneElement.removeEventListener('dragover', onDragOver, true);
				dropzoneElement.removeEventListener('drop', onDrop, true);
				dropzoneElement.removeEventListener('dragleave', onDragLeave);
			}
		};
	});
</script>

<ToolServersModal bind:show={showTools} {selectedToolIds} />
<SkillsModal bind:show={showSkills} {selectedSkillIds} />

<InputVariablesModal
	bind:show={showInputVariablesModal}
	variables={inputVariables}
	onSave={inputVariablesModalCallback}
/>

<ValvesModal
	bind:show={showValvesModal}
	userValves={true}
	type={selectedValvesType}
	id={selectedValvesItemId ?? null}
	onsave={async () => {
		await tick();
	}}
	onclose={() => {
		integrationsMenuCloseOnOutsideClick = true;
	}}
/>

<InputModal
	bind:show={showInputModal}
	bind:value={prompt}
	bind:inputContent
	onChange={(content) => {
		console.log(content);
		chatInputElement?.setContent(content?.json ?? null);
	}}
	onClose={async () => {
		await tick();
		chatInputElement?.focus();
	}}
/>

{#if loaded}
	<div class="w-full font-primary">
		<div class=" mx-auto inset-x-0 bg-transparent flex justify-center">
			<div
				class="flex flex-col px-3 {($settings?.widescreenMode ?? null)
					? 'max-w-full'
					: 'max-w-6xl'} w-full"
			>
				<div class="relative">
					{#if autoScroll === false && history?.currentId}
						<div
							class=" absolute -top-12 left-0 right-0 flex justify-center z-30 pointer-events-none"
						>
							<button
								class=" bg-white border border-gray-100 dark:border-none dark:bg-white/20 p-1.5 rounded-full pointer-events-auto"
								onclick={() => {
									autoScroll = true;
									scrollToBottom();
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-5 h-5"
								>
									<path
										fill-rule="evenodd"
										d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<div class="bg-transparent">
			<div
				class="{($settings?.widescreenMode ?? null)
					? 'max-w-full'
					: 'max-w-6xl'} px-2.5 mx-auto inset-x-0"
			>
				<div class="">
					<input
						bind:this={filesInputElement}
						bind:files={inputFiles}
						type="file"
						hidden
						multiple
						onchange={async () => {
							if (inputFiles && inputFiles.length > 0) {
								const _inputFiles = Array.from(inputFiles);
								inputFilesHandler(_inputFiles);
							} else {
								toast.error($i18n.t(`File not found.`));
							}

							filesInputElement.value = '';
						}}
					/>

					<div class={recording ? '' : 'hidden'}>
						<VoiceRecording
							bind:recording
							onCancel={async () => {
								recording = false;

								await tick();
								document.getElementById('chat-input')?.focus();
							}}
							onConfirm={async (data) => {
								const { text, filename } = data;

								recording = false;

								await tick();
								await insertTextAtCursor(`${text}`);
								await tick();
								document.getElementById('chat-input')?.focus();

								if ($settings?.speechAutoSend ?? false) {
									dispatch('submit', prompt);
								}
							}}
						/>
					</div>
					<form
					class="w-full flex flex-col gap-1.5 {recording ? 'hidden' : ''}"
					onsubmit={(e) => {
					e.preventDefault();
					// check if selectedModels support image input
					dispatch('submit', prompt);
				}}
				>
						<button
							id="generate-message-pair-button"
							class="hidden"
							onclick={() => createMessagePair(prompt)}
						/>

						<!-- Task list display -->
						{#if isActive && chatTasks.length > 0}
							<div class="mx-1">
								<TaskList tasks={chatTasks} />
							</div>
						{/if}

						<!-- Queued messages display -->
						{#if messageQueue.length > 0}
							<div
								class="mb-1 mx-2 py-0.5 px-1.5 rounded-2xl bg-white dark:bg-gray-900/60 border border-gray-100 dark:border-gray-800/50 overflow-x-hidden overflow-y-auto max-h-[25vh]"
							>
								{#each messageQueue as queuedMessage (queuedMessage.id)}
									<QueuedMessageItem
										id={queuedMessage.id}
										content={queuedMessage.prompt}
										files={queuedMessage.files}
										onSendNow={onQueueSendNow}
										onEdit={onQueueEdit}
										onDelete={onQueueDelete}
									/>
								{/each}
							</div>
						{/if}

						<div
							id="message-input-container"
							class="flex-1 flex flex-col relative w-full shadow-lg rounded-3xl border {$temporaryChatEnabled
								? 'border-dashed border-gray-100 dark:border-gray-800 hover:border-gray-200 focus-within:border-gray-200 hover:dark:border-gray-700 focus-within:dark:border-gray-700'
								: ' border-gray-100/30 dark:border-gray-850/30 hover:border-gray-200 focus-within:border-gray-100 hover:dark:border-gray-800 focus-within:dark:border-gray-800'}  transition px-1 bg-white/5 dark:bg-gray-500/5 backdrop-blur-sm dark:text-gray-100"
							dir={$settings?.chatDirection ?? 'auto'}
						>
							<!-- Part B: 角色提示词选择器（顶部"当前角色：xxx"标签 + 下拉切换） -->
							{#if selectedRole}
								<div class="px-3 pt-3 text-left w-full flex flex-col z-10">
									<div class="flex items-center justify-between w-full">
										<div class="pl-[1px] flex items-center gap-2 text-sm dark:text-gray-500">
											<svg class="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
											</svg>
											<div class="translate-y-[0.5px]">
												<span class="text-gray-500">{$i18n.t('Role')}:</span>
												<span class="ml-1 font-medium">{selectedRole.name}</span>
												{#if selectedRole.tools && selectedRole.tools.length > 0}
													<span class="ml-1 text-xs text-gray-400">({selectedRole.tools.length} tools)</span>
												{/if}
											</div>
										</div>
										<div class="flex items-center gap-1">
											<!-- 切换角色按钮 -->
											<div class="relative">
												<button
												class="flex items-center text-xs px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 dark:text-gray-500 transition"
												onclick={() => (showRoleMenu = !showRoleMenu)}
												title={$i18n.t('Switch Role')}
											>
													<svg class="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
													</svg>
												</button>
												{#if showRoleMenu}
													<div
														class="absolute right-0 top-full mt-1 z-50 min-w-[200px] max-h-[240px] overflow-y-auto rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-xl py-1"
												onmouseleave={() => (showRoleMenu = false)}
											>
														{#each roles as r (r.id)}
															<button
																class="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 {r.id === selectedRole.id ? 'font-medium text-blue-600 dark:text-blue-400' : ''}"
															onclick={() => handleRoleSelect(r)}
															>
																<div class="truncate">{r.name}</div>
																{#if r.description}
																	<div class="text-xs text-gray-400 truncate">{r.description}</div>
																{/if}
															</button>
														{/each}
														{#if roles.length === 0}
															<div class="px-3 py-2 text-xs text-gray-400">无可用角色</div>
														{/if}
														<hr class="my-1 border-gray-100 dark:border-gray-800" />
														<button
															class="w-full text-left px-3 py-1.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
														onclick={handleRoleClear}
														>
															{$i18n.t('Clear Role')}
														</button>
													</div>
												{/if}
											</div>
											<!-- 取消角色按钮 -->
											<button
											class="flex items-center dark:text-gray-500"
											onclick={handleRoleClear}
											title={$i18n.t('Clear Role')}
											>
												<XMark />
											</button>
										</div>
									</div>
								</div>
							{:else if roles.length > 0}
								<!-- 未选角色时显示"选择角色"入口 -->
								<div class="px-3 pt-3 text-left w-full flex flex-col z-10">
									<div class="relative inline-block">
										<button
											class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
										onclick={() => (showRoleMenu = !showRoleMenu)}
										>
											<svg class="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
											</svg>
											{$i18n.t('Select Role')}
										</button>
										{#if showRoleMenu}
											<div
												class="absolute left-0 top-full mt-1 z-50 min-w-[200px] max-h-[240px] overflow-y-auto rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-xl py-1"
											onmouseleave={() => (showRoleMenu = false)}
										>
												{#each roles as r (r.id)}
													<button
														class="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
													onclick={() => handleRoleSelect(r)}
													>
														<div class="truncate">{r.name}</div>
														{#if r.description}
															<div class="text-xs text-gray-400 truncate">{r.description}</div>
														{/if}
													</button>
												{/each}
											</div>
										{/if}
									</div>
								</div>
							{/if}

							{#if atSelectedModel !== undefined}
								<div class="px-3 pt-3 text-left w-full flex flex-col z-10">
									<div class="flex items-center justify-between w-full">
										<div class="pl-[1px] flex items-center gap-2 text-sm dark:text-gray-500">
											<img
												alt="model profile"
												class="size-3.5 max-w-[28px] object-cover rounded-full"
												src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${$models.find((model) => model.id === atSelectedModel.id).id}&lang=${$i18n.language}`}
											/>
											<div class="translate-y-[0.5px]">
												<span class="">{atSelectedModel.name}</span>
											</div>
										</div>
										<div>
											<button
												class="flex items-center dark:text-gray-500"
												onclick={() => {
													atSelectedModel = undefined;
												}}
											>
												<XMark />
											</button>
										</div>
									</div>
								</div>
							{/if}

							{#if files.length > 0}
								<div
									class="mx-2 mt-2.5 pb-1.5 flex items-center flex-wrap gap-2"
									dir={$settings?.chatDirection ?? 'auto'}
								>
									{#each files as file, fileIdx}
										{#if file.type === 'image' || (file?.content_type ?? '').startsWith('image/')}
											{@const fileUrl =
												file.url.startsWith('data') || file.url.startsWith('http')
													? file.url
													: `${WEBUI_API_BASE_URL}/files/${file.url}${file?.content_type ? '/content' : ''}`}
											<div class=" relative group">
												<div class="relative flex items-center">
													<Image
														src={fileUrl}
														alt=""
														imageClassName=" size-10 rounded-xl object-cover"
													/>
													{#if atSelectedModel ? visionCapableModels.length === 0 : selectedModels.length !== visionCapableModels.length}
														<Tooltip
															className=" absolute top-1 left-1"
															content={$i18n.t('{{ models }}', {
																models: [...(atSelectedModel ? [atSelectedModel] : selectedModels)]
																	.filter((id) => !visionCapableModels.includes(id))
																	.join(', ')
															})}
														>
															<svg
																xmlns="http://www.w3.org/2000/svg"
																viewBox="0 0 24 24"
																fill="currentColor"
																aria-hidden="true"
																class="size-4 fill-yellow-300"
															>
																<path
																	fill-rule="evenodd"
																	d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003ZM12 8.25a.75.75 0 0 1 .75.75v3.75a.75.75 0 0 1-1.5 0V9a.75.75 0 0 1 .75-.75Zm0 8.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
																	clip-rule="evenodd"
																/>
															</svg>
														</Tooltip>
													{/if}
												</div>
												<div class=" absolute -top-1 -right-1">
													<button
														class=" bg-white text-black border border-white rounded-full {($settings?.highContrastMode ??
														false)
															? ''
															: 'outline-hidden focus:outline-hidden group-hover:visible invisible transition'}"
														type="button"
														aria-label={$i18n.t('Remove file')}
														onclick={() => {
															files.splice(fileIdx, 1);
															files = files;
														}}
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 20 20"
															fill="currentColor"
															aria-hidden="true"
															class="size-4"
														>
															<path
																d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
															/>
														</svg>
													</button>
												</div>
											</div>
										{:else}
											<FileItem
												item={file}
												name={file.name}
												type={file.type}
												size={file?.size}
												loading={file.status === 'uploading'}
												dismissible={true}
												edit={true}
												small={true}
												modal={['file', 'collection'].includes(file?.type)}
												on:dismiss={async () => {
													// Remove from UI state
													files.splice(fileIdx, 1);
													files = files;
												}}
												onclick={() => {
													console.log(file);
												}}
											/>
										{/if}
									{/each}
								</div>
							{/if}

							<div class="px-2.5">
								<div
									class="scrollbar-hidden rtl:text-right ltr:text-left bg-transparent dark:text-gray-100 outline-hidden w-full pb-1 px-1 resize-none h-fit max-h-96 overflow-auto {files.length ===
									0
										? atSelectedModel !== undefined
											? 'pt-1.5'
											: 'pt-2.5'
										: ''}"
									id="chat-input-container"
								>
									{#if prompt.split('\n').length > 2}
										<div class="fixed top-0 right-0 z-20">
											<div class="mt-2.5 mr-3">
											<button
												type="button"
												class="p-1 rounded-lg hover:bg-gray-100/50 dark:hover:bg-gray-800/50"
												aria-label="Expand input"
												onclick={async () => {
													showInputModal = true;
												}}
											>
													<Expand />
												</button>
											</div>
										</div>
									{/if}

									{#if suggestions}
										{#key $settings?.richTextInput ?? true}
											{#key $settings?.showFormattingToolbar ?? false}
												<RichTextInput
													bind:this={chatInputElement}
													id="chat-input"
													editable={!showInputModal}
													onChange={(content) => {
														prompt = content.md;
														inputContent = content;
														command = getCommand();
													}}
													json={true}
													richText={false}
													messageInput={true}
													showFormattingToolbar={$settings?.showFormattingToolbar ?? false}
													floatingMenuPlacement={'top-start'}
													insertPromptAsRichText={$settings?.insertPromptAsRichText ?? false}
													shiftEnter={!($settings?.ctrlEnterToSend ?? false) &&
														!$mobile &&
														!(
															'ontouchstart' in window ||
															navigator.maxTouchPoints > 0 ||
															navigator.msMaxTouchPoints > 0
														)}
													placeholder={placeholder ? placeholder : $i18n.t('Send a Message')}
													largeTextAsFile={($settings?.largeTextAsFile ?? false) && !shiftKey}
													autocomplete={$config?.features?.enable_autocomplete_generation &&
														($settings?.promptAutocomplete ?? false)}
													generateAutoCompletion={async (text) => {
														if (selectedModelIds.length === 0 || !selectedModelIds.at(0)) {
															toast.error($i18n.t('Please select a model first.'));
														}

														const res = await generateAutoCompletion(
															localStorage.token,
															selectedModelIds.at(0),
															text,
															history?.currentId
																? createMessagesList(history, history.currentId)
																: null
														).catch((error) => {
															console.log(error);

															return null;
														});

														console.log(res);
														return res;
													}}
													{suggestions}
													oncompositionstart={() => (isComposing = true)}
													oncompositionend={(e) => {
														compositionEndedAt = e.timeStamp;
														isComposing = false;
													}}
													onkeydown={async (e) => {
														e = e.detail.event;

														const isCtrlPressed = e.ctrlKey || e.metaKey; // metaKey is for Cmd key on Mac
														const suggestionsContainerElement =
															document.getElementById('suggestions-container');

														if (e.key === 'Escape') {
															stopResponse();
														}

														if (prompt === '' && e.key == 'ArrowUp') {
															e.preventDefault();

															const userMessageElement = [
																...document.getElementsByClassName('user-message')
															]?.at(-1);

															if (userMessageElement) {
																userMessageElement.scrollIntoView({ block: 'center' });
																const editButton = [
																	...document.getElementsByClassName('edit-user-message-button')
																]?.at(-1);

																editButton?.click();
															}
														}

														if (!suggestionsContainerElement) {
															if (
																!$mobile ||
																!(
																	'ontouchstart' in window ||
																	navigator.maxTouchPoints > 0 ||
																	navigator.msMaxTouchPoints > 0
																)
															) {
																if (inOrNearComposition(e)) {
																	return;
																}

																// Uses keyCode '13' for Enter key for chinese/japanese keyboards.
																//
																// Depending on the user's settings, it will send the message
																// either when Enter is pressed or when Ctrl+Enter is pressed.
																const enterPressed =
																	($settings?.ctrlEnterToSend ?? false)
																		? (e.key === 'Enter' || e.keyCode === 13) && isCtrlPressed
																		: (e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey;

																if (enterPressed) {
																	e.preventDefault();
																	if (prompt !== '' || files.length > 0) {
																		dispatch('submit', prompt);
																	}
																}
															}
														}

														if (e.key === 'Escape') {
															console.log('Escape');
															atSelectedModel = undefined;
															selectedToolIds = [];
															selectedFilterIds = [];

															webSearchEnabled = false;
															imageGenerationEnabled = false;
															codeInterpreterEnabled = false;
														}
													}}
													onpaste={async (e) => {
														e = e.detail.event;
														console.log(e);

														const clipboardData = e.clipboardData || window.clipboardData;

														if (clipboardData && clipboardData.items) {
															for (const item of clipboardData.items) {
																if (item.type === 'text/plain') {
																	if (($settings?.largeTextAsFile ?? false) && !shiftKey) {
																		const text = clipboardData.getData('text/plain');

																		if (text.length > PASTED_TEXT_CHARACTER_LIMIT) {
																			e.preventDefault();
																			const blob = new Blob([text], { type: 'text/plain' });
																			const file = new File(
																				[blob],
																				`Pasted_Text_${Date.now()}.txt`,
																				{
																					type: 'text/plain'
																				}
																			);

																			await uploadFileHandler(file, true, { context: 'full' });
																		}
																	}
																} else {
																	const file = item.getAsFile();
																	if (file) {
																		await inputFilesHandler([file]);
																		e.preventDefault();
																	}
																}
															}
														}
													}}
												/>
											{/key}
										{/key}
									{/if}
								</div>
							</div>

							<div class=" flex justify-between mt-0.5 mb-2.5 mx-0.5 max-w-full" dir="ltr">
								<div class="ml-1 self-end flex items-center flex-1 max-w-[80%]">
									<InputMenu
										bind:files
										selectedModels={atSelectedModel ? [atSelectedModel.id] : selectedModels}
										{fileUploadCapableModels}
										{screenCaptureHandler}
										{inputFilesHandler}
										uploadFilesHandler={() => {
											filesInputElement.click();
										}}
										uploadGoogleDriveHandler={async () => {
											try {
												const fileData = await createPicker();
												if (fileData) {
													const file = new File([fileData.blob], fileData.name, {
														type: fileData.blob.type
													});
													await uploadFileHandler(file);
												} else {
													console.log('No file was selected from Google Drive');
												}
											} catch (error) {
												console.error('Google Drive Error:', error);
												toast.error(
													$i18n.t('Error accessing Google Drive: {{error}}', {
														error: error.message
													})
												);
											}
										}}
										uploadOneDriveHandler={async (authorityType) => {
											try {
												const fileData = await pickAndDownloadFile(authorityType);
												if (fileData) {
													const file = new File([fileData.blob], fileData.name, {
														type: fileData.blob.type || 'application/octet-stream'
													});
													await uploadFileHandler(file);
												} else {
													console.log('No file was selected from OneDrive');
												}
											} catch (error) {
												console.error('OneDrive Error:', error);
											}
										}}
										{onUpload}
										onClose={async () => {
											await tick();

											const chatInput = document.getElementById('chat-input');
											chatInput?.focus();
										}}
									>
										<button
											type="button"
											id="input-menu-button"
											class="bg-transparent hover:bg-gray-100 text-gray-700 dark:text-white dark:hover:bg-gray-800 rounded-full size-8 flex justify-center items-center outline-hidden focus:outline-hidden"
											aria-label={$i18n.t('More')}
										>
											<PlusAlt className="size-5.5" />
										</button>
									</InputMenu>

									{#if showWebSearchButton || showImageGenerationButton || showCodeInterpreterButton || showPMWorkbenchButton || showToolsButton || showSkillsButton || (toggleFilters && toggleFilters.length > 0)}
										<div
											class="flex self-center w-[1px] h-4 mx-1 bg-gray-200/50 dark:bg-gray-800/50"
										/>

										<IntegrationsMenu
											selectedModels={atSelectedModel ? [atSelectedModel.id] : selectedModels}
											{toggleFilters}
											{showWebSearchButton}
											{showImageGenerationButton}
											{showCodeInterpreterButton}
											{showPMWorkbenchButton}
											bind:selectedToolIds
											bind:selectedSkillIds
											bind:selectedFilterIds
											bind:webSearchEnabled
											bind:imageGenerationEnabled
											bind:codeInterpreterEnabled
											bind:pmWorkbenchEnabled
											closeOnOutsideClick={integrationsMenuCloseOnOutsideClick}
											onShowValves={(e) => {
												const { type, id } = e;
												selectedValvesType = type;
												selectedValvesItemId = id;
												showValvesModal = true;
												integrationsMenuCloseOnOutsideClick = false;
											}}
											onClose={async () => {
												await tick();

												const chatInput = document.getElementById('chat-input');
												chatInput?.focus();
											}}
										>
										<button
											type="button"
											id="integration-menu-button"
											class="bg-transparent hover:bg-gray-100 text-gray-700 dark:text-white dark:hover:bg-gray-800 rounded-full size-8 flex justify-center items-center outline-hidden focus:outline-hidden"
											aria-label={$i18n.t('Integrations')}
											onclick={(e) => {
												// Let the Dropdown component handle the toggle
												// The Dropdown trigger action will handle the toggle
											}}
										>
													<Component className="size-4.5" strokeWidth="1.5" />
												</button>
									</IntegrationsMenu>
									
									<!-- Project Selector Badge -->
									<Tooltip content={hasRealProject ? `当前项目: ${$currentProject?.name}` : '选择项目'} placement="top">
										<button
											type="button"
											class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-sm {!hasRealProject ? 'border border-yellow-400/50' : ''}"
											aria-label="选择项目"
											onclick={() => {
												showPMDataSelector = true;
											}}
										>
											<svg class="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5a2 2 0 012-2h4a2 2 0 012 2v2H8V5z" />
											</svg>
											<span class="text-gray-700 dark:text-gray-300 max-w-[120px] truncate">
												{$currentProject?.name || '选择项目'}
											</span>
											{#if !hasRealProject}
												<span class="text-xs text-yellow-500">未选择</span>
											{/if}
										</button>
									</Tooltip>

									<!-- Workflow Selector -->
									{#if showWorkflowButton && workflows.length > 0}
										<WorkflowSelector
											{workflows}
											{selectedWorkflowId}
											{pinnedWorkflowIds}
											requiredProjectId={hasRealProject ? $currentProject.id : null}
											onSelect={handleWorkflowSelect}
											onPin={handleWorkflowPin}
											onUnpin={handleWorkflowUnpin}
										/>
									{/if}
								
								{/if}

								{#if selectedModelIds.length === 1 && $models.find((m) => m.id === selectedModelIds[0])?.has_user_valves}
									<div class="ml-1 flex gap-1.5">
										<Tooltip content={$i18n.t('Valves')} placement="top">
											<button
												type="button"
												id="model-valves-button"
												class="bg-transparent hover:bg-gray-100 text-gray-700 dark:text-white dark:hover:bg-gray-800 rounded-full size-8 flex justify-center items-center outline-hidden focus:outline-hidden"
												onclick={() => {
													selectedValvesType = 'function';
													selectedValvesItemId = selectedModelIds[0]?.split('.')[0];
													showValvesModal = true;
												}}
											>
												<Knobs className="size-4" strokeWidth="1.5" />
											</button>
										</Tooltip>
									</div>
								{/if}

								<div class="ml-1 flex gap-1.5">
										{#if (selectedToolIds ?? []).length > 0}
											<Tooltip
												content={$i18n.t('{{COUNT}} Available Tools', {
													COUNT: (selectedToolIds ?? []).length
												})}
											>
												<button
													class="translate-y-[0.5px] px-1 flex gap-1 items-center text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg self-center transition"
													aria-label="Available Tools"
													type="button"
													onclick={() => {
														showTools = !showTools;
													}}
												>
													<Wrench className="size-4" strokeWidth="1.75" />

													<span class="text-sm">
														{(selectedToolIds ?? []).length}
													</span>
												</button>
											</Tooltip>
										{/if}

										{#if (selectedSkillIds ?? []).length > 0}
											<Tooltip
												content={$i18n.t('{{COUNT}} Available Skills', {
													COUNT: (selectedSkillIds ?? []).length
												})}
											>
												<button
													class="translate-y-[0.5px] px-1 flex gap-1 items-center text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg self-center transition"
													aria-label="Available Skills"
													type="button"
													onclick={() => {
														showSkills = !showSkills;
													}}
												>
													<Keyframes className="size-4" strokeWidth="1.75" />

													<span class="text-sm">
														{(selectedSkillIds ?? []).length}
													</span>
												</button>
											</Tooltip>
										{/if}

										{#each selectedFilterIds as filterId (filterId)}
											{@const filter = toggleFilters.find((f) => f.id === filterId)}
											{#if filter}
												<Tooltip content={filter?.name} placement="top">
											<button
												onclick={(e) => {
													e.preventDefault();
													if (
														filter?.has_user_valves &&
														($_user?.role === 'admin' ||
															($_user?.permissions?.chat?.valves ?? true))
													) {
														selectedValvesType = 'function';
														selectedValvesItemId = filterId;
														showValvesModal = true;
													} else {
														selectedFilterIds = selectedFilterIds.filter(
															(id) => id !== filterId
														);
															}
														}}
														type="button"
														class="group p-[7px] flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden {selectedFilterIds.includes(
															filterId
														)
															? 'text-sky-500 dark:text-sky-300 bg-sky-50 hover:bg-sky-100 dark:bg-sky-400/10 dark:hover:bg-sky-600/10 border border-sky-200/40 dark:border-sky-500/20'
															: 'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 '} capitalize"
													>
														{#if filter?.icon}
															<div class="size-4 items-center flex justify-center">
																<img
																	src={filter.icon}
																	class="size-3.5 {filter.icon.includes('data:image/svg')
																		? 'dark:invert-[80%]'
																		: ''}"
																	style="fill: currentColor;"
																	alt={filter.name}
																/>
															</div>
														{:else}
															<Sparkles className="size-4" strokeWidth="1.75" />
														{/if}
														<!-- svelte-ignore a11y-click-events-have-key-events -->
														<!-- svelte-ignore a11y-no-static-element-interactions -->
													<div
														class="hidden group-hover:block"
														onclick={(e) => {
															e.stopPropagation();
															e.preventDefault();
															selectedFilterIds = selectedFilterIds.filter(
																(id) => id !== filterId
															);
														}}
													>
															<XMark className="size-4" strokeWidth="1.75" />
														</div>
													</button>
												</Tooltip>
											{/if}
										{/each}

										{#if webSearchEnabled}
											<Tooltip content={$i18n.t('Web Search')} placement="top">
												<button
													onclick={(e) => {
														e.preventDefault();
														webSearchEnabled = !webSearchEnabled;
													}}
													type="button"
													class="group p-[7px] flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden {webSearchEnabled ||
													($settings?.webSearch ?? false) === 'always'
														? ' text-sky-500 dark:text-sky-300 bg-sky-50 hover:bg-sky-100 dark:bg-sky-400/10 dark:hover:bg-sky-600/10 border border-sky-200/40 dark:border-sky-500/20'
														: 'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 '}"
												>
													<GlobeAlt className="size-4" strokeWidth="1.75" />
													<div class="hidden group-hover:block">
														<XMark className="size-4" strokeWidth="1.75" />
													</div>
												</button>
											</Tooltip>
										{/if}

										{#if imageGenerationEnabled}
											<Tooltip content={$i18n.t('Image')} placement="top">
												<button
													onclick={(e) => {
														e.preventDefault();
														imageGenerationEnabled = !imageGenerationEnabled;
													}}
													type="button"
													class="group p-[7px] flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden {imageGenerationEnabled
														? ' text-sky-500 dark:text-sky-300 bg-sky-50 hover:bg-sky-100 dark:bg-sky-400/10 dark:hover:bg-sky-700/10 border border-sky-200/40 dark:border-sky-500/20'
														: 'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 '}"
												>
													<Photo className="size-4" strokeWidth="1.75" />
													<div class="hidden group-hover:block">
														<XMark className="size-4" strokeWidth="1.75" />
													</div>
												</button>
											</Tooltip>
										{/if}

										{#if codeInterpreterEnabled}
											<Tooltip content={$i18n.t('Code Interpreter')} placement="top">
												<button
													aria-label={codeInterpreterEnabled
														? $i18n.t('Disable Code Interpreter')
														: $i18n.t('Enable Code Interpreter')}
													aria-pressed={codeInterpreterEnabled}
													onclick={(e) => {
															e.preventDefault();
															codeInterpreterEnabled = !codeInterpreterEnabled;
														}}
														type="button"
													class=" group p-[7px] flex gap-1.5 items-center text-sm transition-colors duration-300 max-w-full overflow-hidden {codeInterpreterEnabled
														? ' text-sky-500 dark:text-sky-300 bg-sky-50 hover:bg-sky-100 dark:bg-sky-400/10 dark:hover:bg-sky-700/10 border border-sky-200/40 dark:border-sky-500/20'
														: 'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 '} {($settings?.highContrastMode ??
													false)
														? 'm-1'
														: 'focus:outline-hidden rounded-full'}"
												>
													<Terminal className="size-3.5" strokeWidth="2" />

													<div class="hidden group-hover:block">
														<XMark className="size-4" strokeWidth="1.75" />
													</div>
												</button>
											</Tooltip>
										{/if}

										{#each pendingOAuthTools as pendingTool (pendingTool.id)}
											<Tooltip content={$i18n.t('Click to connect')} placement="top">
											<button
													onclick={(e) => {
															e.preventDefault();
															sessionStorage.setItem('pendingOAuthToolId', pendingTool.id);
															const authUrl = getOAuthClientAuthorizationUrl(
																pendingTool.serverId,
																pendingTool.authType ?? 'mcp'
															);
															window.open(authUrl, '_self', 'noopener');
														}}
														type="button"
													class="group px-2 py-[5px] flex gap-1.5 items-center text-xs rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden
														text-amber-600 dark:text-amber-400 bg-amber-50 hover:bg-amber-100 dark:bg-amber-400/10 dark:hover:bg-amber-600/10 border border-amber-200/40 dark:border-amber-500/20"
												>
													<Wrench className="size-3.5" strokeWidth="1.75" />
													<span class="truncate">{pendingTool.name}</span>
												</button>
											</Tooltip>
										{/each}
									</div>
								</div>

								<div class="self-end flex space-x-1 mr-1 shrink-0 gap-[0.5px]">
									{#if isActive && prompt === '' && files.length === 0}
										<div class=" flex items-center">
											<Tooltip content={$i18n.t('Stop')}>
												<button
													class="bg-white hover:bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-800 transition rounded-full p-1.5"
													onclick={() => {
														stopResponse();
													}}
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														viewBox="0 0 24 24"
														fill="currentColor"
														class="size-5"
													>
														<path
															fill-rule="evenodd"
															d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm6-2.438c0-.724.588-1.312 1.313-1.312h4.874c.725 0 1.313.588 1.313 1.313v4.874c0 .725-.588 1.313-1.313 1.313H9.564a1.312 1.312 0 01-1.313-1.313V9.564z"
															clip-rule="evenodd"
														/>
													</svg>
												</button>
											</Tooltip>
										</div>
									{:else}
										{#if prompt !== '' && !history?.currentId && !$selectedTerminalId && ($config?.features?.enable_notes ?? false) && ($_user?.role === 'admin' || ($_user?.permissions?.features?.notes ?? true))}
											<!-- {$i18n.t('Create Note')}  -->
											<Tooltip content={$i18n.t('Create note')} className=" flex items-center">
												<button
													id="create-note-button"
													class=" text-gray-500 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 transition rounded-full p-1.5 -mr-1 self-center"
													type="button"
													disabled={prompt === '' && files.length === 0}
													onclick={() => {
														createNote();
													}}
												>
													<Note className="size-4.5 translate-y-[0.5px]" />
												</button>
											</Tooltip>
										{/if}

										{#if !history?.currentId || history.messages[history.currentId]?.done == true}
											<!-- Terminal Server Selector -->
											{@const hasDirectToolServerAccess =
												$_user?.role === 'admin' ||
												($_user?.permissions?.features?.direct_tool_servers ?? true)}
											{#if terminalCapableModels.length > 0 && (($terminalServers ?? []).some((t) => t.id) || (hasDirectToolServerAccess && (($terminalServers ?? []).some((t) => !t.id) || ($settings?.terminalServers ?? []).some((s) => s.url))))}
												<TerminalMenu bind:show={showTerminalMenu} />
											{/if}

											{#if $_user?.role === 'admin' || ($_user?.permissions?.chat?.stt ?? true)}
												<!-- {$i18n.t('Record voice')} -->
												<Tooltip content={$i18n.t('Dictate')}>
													<button
														id="voice-input-button"
														class=" text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 transition rounded-full p-1.5 self-center mr-0.5"
														type="button"
															onclick={async () => {
																try {
																	let stream = await navigator.mediaDevices
																			.getUserMedia({ audio: true })
																			.catch(function (err) {
																				toast.error(
																					$i18n.t(
																							`Permission denied when accessing microphone: {{error}}`,
																							{
																								error: err
																							}
																						)
																					);
																					return null;
																				});

																if (stream) {
																	recording = true;
																	const tracks = stream.getTracks();
																	tracks.forEach((track) => track.stop());
																}
																stream = null;
															} catch {
																toast.error($i18n.t('Permission denied when accessing microphone'));
															}
														}}
														aria-label="Voice Input"
													>
														<svg
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 20 20"
															fill="currentColor"
															class="size-5 translate-y-[0.5px]"
														>
															<path d="M7 4a3 3 0 016 0v6a3 3 0 11-6 0V4z" />
															<path
																d="M5.5 9.643a.75.75 0 00-1.5 0V10c0 3.06 2.29 5.585 5.25 5.954V17.5h-1.5a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-1.5v-1.546A6.001 6.001 0 0016 10v-.357a.75.75 0 00-1.5 0V10a4.5 4.5 0 01-9 0v-.357z"
															/>
														</svg>
													</button>
												</Tooltip>
											{/if}
										{/if}

										{#if prompt === '' && files.length === 0 && ($_user?.role === 'admin' || ($_user?.permissions?.chat?.call ?? true))}
											<div class=" flex items-center">
												<!-- {$i18n.t('Call')} -->
												<Tooltip content={$i18n.t('Voice mode')}>
													<button
														class=" bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full p-1.5 self-center"
														type="button"
															onclick={async () => {
															if (selectedModels.length > 1) {
																toast.error($i18n.t('Select only one model to call'));

																return;
															}

															if ($config.audio.stt.engine === 'web') {
																toast.error(
																	$i18n.t('Call feature is not supported when using Web STT engine')
																);

																return;
															}
															// check if user has access to getUserMedia
															try {
																let stream = await navigator.mediaDevices.getUserMedia({
																	audio: true
																});
																// If the user grants the permission, proceed to show the call overlay

																if (stream) {
																	const tracks = stream.getTracks();
																	tracks.forEach((track) => track.stop());
																}

																stream = null;

																if ($settings.audio?.tts?.engine === 'browser-kokoro') {
																	// If the user has not initialized the TTS worker, initialize it
																	if (!$TTSWorker) {
																		await TTSWorker.set(
																			new KokoroWorker({
																				dtype: $settings.audio?.tts?.engineConfig?.dtype ?? 'fp32'
																			})
																		);

																		await $TTSWorker.init();
																	}
																}

																showCallOverlay.set(true);
																showControls.set(true);
															} catch (err) {
																// If the user denies the permission or an error occurs, show an error message
																toast.error(
																	$i18n.t('Permission denied when accessing media devices')
																);
															}
														}}
														aria-label={$i18n.t('Voice mode')}
													>
														<Voice className="size-5" strokeWidth="2.5" />
													</button>
												</Tooltip>
											</div>
										{:else}
											<div class=" flex items-center">
												<Tooltip
													content={uploadPending
														? $i18n.t('Waiting for upload...')
														: $i18n.t('Send message')}
												>
													<button
														id="send-message-button"
														class="{!(prompt === '' && files.length === 0) || uploadPending
															? 'bg-black text-white hover:bg-gray-900 dark:bg-white dark:text-black dark:hover:bg-gray-100 '
															: 'text-white bg-gray-200 dark:text-gray-900 dark:bg-gray-700 disabled'} transition rounded-full p-1.5 self-center"
														type="submit"
														disabled={(prompt === '' && files.length === 0) || uploadPending}
													>
														{#if uploadPending}
															<Spinner className="size-5" />
														{:else}
															<svg
																xmlns="http://www.w3.org/2000/svg"
																viewBox="0 0 16 16"
																fill="currentColor"
																class="size-5"
															>
																<path
																	fill-rule="evenodd"
																	d="M8 14a.75.75 0 0 1-.75-.75V4.56L4.03 7.78a.75.75 0 0 1-1.06-1.06l4.5-4.5a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1-1.06 1.06L8.75 4.56v8.69A.75.75 0 0 1 8 14Z"
																	clip-rule="evenodd"
																/>
															</svg>
														{/if}
													</button>
												</Tooltip>
											</div>
										{/if}
									{/if}
								</div>
							</div>
						</div>

						{#if $config?.license_metadata?.input_footer}
							<div class=" text-xs text-gray-500 text-center line-clamp-1 marked">
								{@html DOMPurify.sanitize(marked($config?.license_metadata?.input_footer))}
							</div>
						{:else}
							<div class="mb-1" />
						{/if}
					</form>
				</div>
			</div>
		</div>
	</div>
{/if}

<PMDataSelector
	bind:show={showPMDataSelector}
	onSelect={(data) => {
		// Pure project selection — just set context, no file attachment
		if (data.type === 'project-only') {
			showPMDataSelector = false;
			toast.success(`已选择项目: ${data.projectName || data.name || ''}`);
			return;
		}
		// Entry selection — attach as file reference
		const pmRef = {
			id: `pm-${data.projectId || data.project_id}${data.entryId || data.id ? '-' + (data.entryId || data.id) : ''}`,
			name: data.projectName || data.name || 'Untitled',
			type: 'pm-entry',
			status: 'processed',
			url: `/pm/${data.projectId || data.project_id}`,
			data: {
				projectId: data.projectId || data.project_id,
				projectName: data.projectName || data.project_name,
				entryId: data.entryId || data.id,
				entryTitle: data.entryTitle || data.name,
				moduleType: data.moduleType || data.module_type
			}
		};
		if (!files.find((f) => f.id === pmRef.id)) {
			files = [...files, pmRef];
		}
		showPMDataSelector = false;
	}}
	onClose={() => {
		showPMDataSelector = false;
	}}
/>
