import { writable } from 'svelte/store';

/**
 * 跨 MessageInput 实例持久化的工作流选择状态。
 *
 * D32: 解决 Chat.svelte 的 {#if} 分支切换导致 MessageInput 组件卸载重挂载时
 * selectedWorkflowId / pinnedWorkflowIds 局部状态丢失的问题。
 *
 * 用户报告「对话选择工作流后点击发送，工作流被自动取消」—— 实际上是
 * Chat.svelte L3163 的 {#if} 分支条件 createMessagesList(history, history.currentId).length > 0
 * 在发送消息后从 false 变 true，导致 Placeholder 卸载、内嵌的 MessageInput #A 销毁，
 * 分支 A 挂载新的 MessageInput #B，selectedWorkflowId 重置为 ''。
 *
 * 用 store 持久化状态，让组件重挂载时从 store 恢复。
 */
export const chatWorkflowState = writable<{
	selectedWorkflowId: string;
	pinnedWorkflowIds: string[];
}>({
	selectedWorkflowId: '',
	pinnedWorkflowIds: []
});
