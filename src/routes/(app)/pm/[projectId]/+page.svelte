<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	let projectId = $derived($page.params.projectId);

	let moduleGroups = $derived([
		{
			id: 'plan',
			label: '🗺️ 规划',
			modules: [
				{ id: 'prd', label: 'PRD 文档', desc: '产品需求文档', href: `/pm/${projectId}/prd` },
				{ id: 'requirement', label: '需求管理', desc: '需求收集与分析', href: `/pm/${projectId}/requirement` },
				{ id: 'roadmap', label: '产品路线图', desc: '版本规划', href: `/pm/${projectId}/roadmap` }
			]
		},
		{
			id: 'design',
			label: '🎨 设计',
			modules: [
				{ id: 'parameter', label: '参数配置', desc: '参数清单管理', href: `/pm/${projectId}/parameter` },
				{ id: 'product-architecture', label: '产品架构', desc: '架构设计', href: `/pm/${projectId}/product-architecture` },
				{ id: 'competitor', label: '竞品分析', desc: '竞品对比矩阵', href: `/pm/${projectId}/competitor` }
			]
		},
		{
			id: 'execute',
			label: '⚡ 执行',
			modules: [
				{ id: 'testcase', label: '测试用例', desc: '用例管理', href: `/pm/${projectId}/testcase` },
				{ id: 'risk', label: '风险分析', desc: '风险管控', href: `/pm/${projectId}/risk` },
				{ id: 'meeting', label: '会议纪要', desc: '评审记录', href: `/pm/${projectId}/meeting` }
			]
		},
		{
			id: 'review',
			label: '📊 复盘',
			modules: [
				{ id: 'acceptance', label: '验收报告', desc: '验收检查', href: `/pm/${projectId}/acceptance` },
				{ id: 'faq', label: 'FAQ', desc: '常见问题', href: `/pm/${projectId}/faq` }
			]
		}
	]);
</script>

<div class="p-4 md:p-6 max-w-5xl mx-auto">
	<div class="mb-6">
		<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">工作台</h2>
		<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">选择模块开始工作</p>
	</div>

	<div class="grid gap-6">
		{#each moduleGroups as group (group.id)}
			<div>
				<h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">{group.label}</h3>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each group.modules as mod (mod.id)}
						<button
							class="flex flex-col p-4 bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 hover:shadow-sm transition text-left"
							onclick={() => goto(mod.href)}
						>
							<span class="text-sm font-medium text-gray-900 dark:text-gray-100">{mod.label}</span>
							<span class="text-xs text-gray-500 dark:text-gray-400 mt-1">{mod.desc}</span>
						</button>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>
