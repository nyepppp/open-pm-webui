<script lang="ts">
	import { createBranch } from '$lib/apis/pm/version';
	import { toast } from 'svelte-sonner';

	interface Props {
		projectId: string;
		entryId: string;
		currentVersionId?: string;
		onClose?: () => void;
		onBranchCreated?: (branch: any) => void;
	}

	let { projectId, entryId, currentVersionId, onClose, onBranchCreated }: Props = $props();

	let branchName = $state('');
	let creating = $state(false);

	async function handleCreate() {
		if (!branchName.trim()) {
			toast.error('请输入分支名称');
			return;
		}
		creating = true;
		try {
			const branch = await createBranch(projectId, entryId, {
				name: branchName.trim(),
				...(currentVersionId && { sourceVersionId: currentVersionId })
			});
			onBranchCreated?.(branch);
			toast.success(`分支 "${branchName}" 创建成功`);
			onClose?.();
		} catch (e: any) {
			toast.error(e?.message || '创建分支失败');
		} finally {
			creating = false;
		}
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onclick={onClose}>
	<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-5" onclick={(e) => e.stopPropagation()}>
		<h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 mb-4">创建版本分支</h3>
		<p class="text-xs text-gray-500 dark:text-gray-400 mb-3">从当前版本创建独立分支，分支内的编辑不会影响主线内容。类似 Git 的 branch 功能。</p>

		<div class="mb-4">
			<label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">分支名称</label>
			<input
				type="text"
				class="w-full text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-xl outline-hidden focus:ring-2 focus:ring-blue-500"
				placeholder="例如: feature-v2, review-branch"
				bind:value={branchName}
				onkeydown={(e) => { if (e.key === 'Enter') handleCreate(); }}
			/>
		</div>

		<div class="flex justify-end gap-2">
			<button
				class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
				onclick={onClose}
			>取消</button>
			<button
				class="px-4 py-2 text-sm bg-black text-white dark:bg-white dark:text-black rounded-lg transition disabled:opacity-40"
				onclick={handleCreate}
				disabled={!branchName.trim() || creating}
			>
				{creating ? '创建中...' : '创建分支'}
			</button>
		</div>
	</div>
</div>
