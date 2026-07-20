<script lang="ts">
	import { getContext } from 'svelte';
	import { fly } from 'svelte/transition';
	import { toast } from 'svelte-sonner';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let mode: 'import' | 'export' = 'export';
	export let entries: any[] = [];
	export let moduleType: string = '';
	export let moduleConfig: any = null;
	export let versionId: string = '';
	export let onImport: (data: any[], importMode: 'append' | 'overwrite' | 'merge') => void = () => {};
	export let onClose: () => void = () => {};

	let importFormat: 'csv' | 'json' | 'xlsx' = 'csv';
	let exportFormat: 'csv' | 'json' | 'xlsx' = 'csv';
	let importData = '';
	let importFile: File | null = null;
	let isProcessing = false;
	let previewData: any[] = [];
	let showPreview = false;
	let importMode: 'append' | 'overwrite' | 'merge' = 'append';

	function close() {
		show = false;
		onClose();
		resetState();
	}

	function resetState() {
		importData = '';
		importFile = null;
		previewData = [];
		showPreview = false;
		isProcessing = false;
	}

	function getExportColumns(): string[] {
		let cols: string[] = [];

		if (moduleConfig?.tableColumns) {
			cols = moduleConfig.tableColumns.map((col: any) => col.key);
		} else if (moduleConfig?.formFields) {
			cols = moduleConfig.formFields.map((field: any) => field.key);
		} else {
			cols = ['title', 'content', 'status', 'priority'];
		}

		// D10: 始终追加版本列（即使 moduleConfig 未声明），避免版本信息丢失
		if (!cols.includes('currentVersionNumber')) cols.push('currentVersionNumber');
		if (!cols.includes('createdVersionNumber')) cols.push('createdVersionNumber');
		if (!cols.includes('versionId')) cols.push('versionId');

		return cols;
	}

	function getExportHeaders(): string[] {
		let headers: string[] = [];

		if (moduleConfig?.tableColumns) {
			headers = moduleConfig.tableColumns.map((col: any) => col.label);
		} else if (moduleConfig?.formFields) {
			headers = moduleConfig.formFields.map((field: any) => field.label);
		} else {
			headers = ['标题', '内容', '状态', '优先级'];
		}

		// D10: 始终追加版本表头（与 getExportColumns 对应）
		const keys = moduleConfig?.tableColumns
			? moduleConfig.tableColumns.map((col: any) => col.key)
			: moduleConfig?.formFields
				? moduleConfig.formFields.map((field: any) => field.key)
				: ['title', 'content', 'status', 'priority'];

		if (!keys.includes('currentVersionNumber')) headers.push('当前版本');
		if (!keys.includes('createdVersionNumber')) headers.push('创建版本');
		if (!keys.includes('versionId')) headers.push('版本ID');

		return headers;
	}

	function flattenEntry(entry: any): Record<string, any> {
		const flat: Record<string, any> = {};
		const columns = getExportColumns();

		columns.forEach(col => {
			if (col === 'title') flat[col] = entry.title || '';
			else if (col === 'content') flat[col] = entry.content || '';
			else if (col === 'status') flat[col] = entry.status || '';
			else if (col === 'priority') flat[col] = entry.priority || '';
			else if (col === 'updatedAt') flat[col] = entry.updated_at || entry.updatedAt || '';
			else if (col === 'currentVersionNumber') flat[col] = entry.current_version_number || entry.currentVersionNumber || '';
			else if (col === 'createdVersionNumber') flat[col] = entry.created_version_number || entry.createdVersionNumber || '';
			else if (col === 'versionId') flat[col] = entry.versionId || entry.version_id || '';
			else {
				// 优先从 data 字段取；data 缺失时回退到 content（避免内容列全空）
				flat[col] = entry.data?.[col] ?? entry.content ?? '';
			}
		});

		// D10: 始终追加版本字段（即使 moduleConfig 未声明，确保版本信息不丢）
		if (!columns.includes('currentVersionNumber')) {
			flat['currentVersionNumber'] = entry.current_version_number || entry.currentVersionNumber || '';
		}
		if (!columns.includes('createdVersionNumber')) {
			flat['createdVersionNumber'] = entry.created_version_number || entry.createdVersionNumber || '';
		}
		if (!columns.includes('versionId') && (entry.versionId || entry.version_id)) {
			flat['versionId'] = entry.versionId || entry.version_id;
		}

		// 追加 data_json 列：把整个 entry.data 序列化为 JSON 字符串，保证自定义字段不丢
		// 参考后端 _entry_to_row 的实现
		if (entry.data && Object.keys(entry.data).length > 0) {
			flat['data_json'] = JSON.stringify(entry.data);
		} else {
			flat['data_json'] = '';
		}

		return flat;
	}

	async function exportToXLSX(): Promise<Blob> {
		const XLSX = await import('xlsx');
		const columns = getExportColumns();
		const headers = getExportHeaders();
		// 始终追加 data_json 列以保留自定义字段（与后端 _entry_to_row 行为一致）
		// D5: 表头用中文 label，列 key 保持 'data_json' 用于导入识别
		const allHeaders = [...headers, '数据JSON'];
		const allColumns = [...columns, 'data_json'];

		const rows = entries.map(entry => {
			const flat = flattenEntry(entry);
			return allColumns.map(col => flat[col] ?? '');
		});

		const worksheet = XLSX.utils.aoa_to_sheet([allHeaders, ...rows]);
		const workbook = XLSX.utils.book_new();
		XLSX.utils.book_append_sheet(workbook, worksheet, moduleType || 'data');
		const arrayBuffer = XLSX.write(workbook, { type: 'array', bookType: 'xlsx' });
		return new Blob([arrayBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
	}

	function exportToCSV(): string {
		const columns = getExportColumns();
		const headers = getExportHeaders();
		// D5: 与 XLSX 一致，追加 data_json 列
		const allHeaders = [...headers, '数据JSON'];
		const allColumns = [...columns, 'data_json'];

		let csv = allHeaders.join(',') + '\n';

		entries.forEach(entry => {
			const flat = flattenEntry(entry);
			const row = allColumns.map(col => {
				let val = flat[col] || '';
				// Escape quotes and wrap in quotes if contains comma
				if (typeof val === 'string' && (val.includes(',') || val.includes('"') || val.includes('\n'))) {
					val = '"' + val.replace(/"/g, '""') + '"';
				}
				return val;
			}).join(',');
			csv += row + '\n';
		});

		return csv;
	}

	function exportToJSON(): string {
		const exportData = entries.map(entry => flattenEntry(entry));
		return JSON.stringify(exportData, null, 2);
	}

	async function handleExport() {
		if (entries.length === 0) {
			toast.error('没有数据可导出');
			return;
		}

		let blob: Blob;
		let extension: string;

		try {
			if (exportFormat === 'csv') {
				const content = exportToCSV();
				blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
				extension = 'csv';
			} else if (exportFormat === 'json') {
				const content = exportToJSON();
				blob = new Blob([content], { type: 'application/json' });
				extension = 'json';
			} else {
				// xlsx
				blob = await exportToXLSX();
				extension = 'xlsx';
			}

			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `${moduleType}_export_${new Date().toISOString().split('T')[0]}.${extension}`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);

			toast.success(`已导出 ${entries.length} 条数据`);
			close();
		} catch (e: any) {
			toast.error('导出失败: ' + (e?.message || '未知错误'));
		}
	}

	function parseCSV(csvText: string): any[] {
		const lines = csvText.trim().split('\n');
		if (lines.length < 2) return [];

		const headers = lines[0].split(',').map(h => h.trim());
		const result: any[] = [];

		for (let i = 1; i < lines.length; i++) {
			const line = lines[i];
			if (!line.trim()) continue;

			// Simple CSV parsing (doesn't handle all edge cases but works for basic cases)
			const values: string[] = [];
			let current = '';
			let inQuotes = false;

			for (let j = 0; j < line.length; j++) {
				const char = line[j];
				if (char === '"') {
					if (inQuotes && line[j + 1] === '"') {
						current += '"';
						j++;
					} else {
						inQuotes = !inQuotes;
					}
				} else if (char === ',' && !inQuotes) {
					values.push(current.trim());
					current = '';
				} else {
					current += char;
				}
			}
			values.push(current.trim());

			const row: Record<string, any> = {};
			headers.forEach((header, index) => {
				row[header] = values[index] || '';
			});
			result.push(row);
		}

		return result;
	}

	function parseJSON(jsonText: string): any[] {
		try {
			const data = JSON.parse(jsonText);
			return Array.isArray(data) ? data : [data];
		} catch (e) {
			toast.error('JSON 格式错误');
			return [];
		}
	}

	async function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		importFile = file;

		// Auto-detect format
		if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
			importFormat = 'xlsx';
			// Parse xlsx file
			try {
				const XLSX = await import('xlsx');
				const arrayBuffer = await file.arrayBuffer();
				const workbook = XLSX.read(arrayBuffer, { type: 'array' });
				const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
				previewData = XLSX.utils.sheet_to_json(firstSheet);
				showPreview = true;
				toast.success(`预览: 发现 ${previewData.length} 条数据`);
			} catch (err: any) {
				toast.error('解析 Excel 文件失败: ' + (err?.message || ''));
			}
		} else {
			const text = await file.text();
			importData = text;
			if (file.name.endsWith('.json')) {
				importFormat = 'json';
			} else {
				importFormat = 'csv';
			}
			previewImport();
		}
	}

	function previewImport() {
		if (!importData.trim()) {
			toast.error('请输入导入数据');
			return;
		}

		try {
			if (importFormat === 'csv') {
				previewData = parseCSV(importData);
			} else {
				previewData = parseJSON(importData);
			}
			showPreview = true;
			toast.success(`预览: 发现 ${previewData.length} 条数据`);
		} catch (e: any) {
			toast.error('解析失败: ' + e.message);
		}
	}

	function handleImport() {
		if (previewData.length === 0) {
			toast.error('没有要导入的数据');
			return;
		}

		isProcessing = true;

		try {
			// Transform preview data to entry format
			const importEntries = previewData.map(row => {
				const entry: any = {
					title: row['标题'] || row['title'] || row['名称'] || row['name'] || '未命名',
					status: row['状态'] || row['status'] || 'draft',
					priority: row['优先级'] || row['priority'] || 'p2',
					content: row['内容'] || row['content'] || '',
					data: {}
				};

				// Preserve versionId if present in import data
				if (row['versionId'] || row['version_id'] || row['版本ID']) {
					entry.versionId = row['versionId'] || row['version_id'] || row['版本ID'];
				} else if (versionId) {
					entry.versionId = versionId;
				}

				// Map all other fields to data
				Object.keys(row).forEach(key => {
					if (!['title', 'status', 'priority', 'content', 'updatedAt', 'currentVersionNumber', 'versionId', 'version_id', '版本ID'].includes(key)) {
						entry.data[key] = row[key];
					}
				});

				return entry;
			});

			// Pass importMode to parent — it controls append/overwrite/merge behavior
			onImport(importEntries, importMode);
			toast.success(`已提交导入 ${importEntries.length} 条数据 (${importMode === 'append' ? '追加' : importMode === 'overwrite' ? '覆盖' : '合并'})`);
			close();
		} catch (e: any) {
			toast.error('导入失败: ' + e.message);
		} finally {
			isProcessing = false;
		}
	}

	function downloadTemplate() {
		const columns = getExportColumns();
		const headers = getExportHeaders();
		
		let content: string;
		let mimeType: string;
		let extension: string;

		if (importFormat === 'csv') {
			content = headers.join(',') + '\n';
			// Add example row
			const exampleRow = columns.map(() => '示例数据').join(',');
			content += exampleRow + '\n';
			mimeType = 'text/csv;charset=utf-8;';
			extension = 'csv';
		} else {
			const template: Record<string, any>[] = [{}];
			columns.forEach((col, index) => {
				template[0][headers[index]] = '示例数据';
			});
			content = JSON.stringify(template, null, 2);
			mimeType = 'application/json';
			extension = 'json';
		}

		const blob = new Blob([content], { type: mimeType });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${moduleType}_template.${extension}`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);

		toast.success('模板已下载');
	}
</script>

{#if show}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		on:click={close}
	>
		<div
			class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden"
			on:click|stopPropagation
			in:fly={{ y: 20, duration: 200 }}
		>
			<!-- Header -->
			<div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
					{mode === 'import' ? '批量导入' : '批量导出'}
					<span class="text-sm font-normal text-gray-500 ml-2">
						({moduleConfig?.name || moduleType})
					</span>
				</h2>
				<button
					on:click={close}
					class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
				>
					<XMark className="size-5" />
				</button>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto p-4 space-y-4">
				{#if mode === 'export'}
					<!-- Export Mode -->
					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								导出格式
							</label>
							<div class="flex gap-2">
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {exportFormat === 'csv' ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => exportFormat = 'csv'}
								>
									CSV
								</button>
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {exportFormat === 'json' ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => exportFormat = 'json'}
								>
									JSON
								</button>
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {exportFormat === 'xlsx' ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => exportFormat = 'xlsx'}
								>
									Excel (xlsx)
								</button>
							</div>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								导出字段
							</label>
							<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
								<div class="flex flex-wrap gap-2">
									{#each getExportHeaders() as header}
										<span class="px-2 py-1 text-xs bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300">
											{header}
										</span>
									{/each}
								</div>
							</div>
						</div>

						<div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
							<div class="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-400">
								<svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								<span>将导出 {entries.length} 条数据</span>
							</div>
						</div>
					</div>
				{:else}
					<!-- Import Mode -->
					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								导入格式
							</label>
							<div class="flex gap-2">
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {importFormat === 'csv' ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => { importFormat = 'csv'; showPreview = false; }}
								>
									CSV
								</button>
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {importFormat === 'json' ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => { importFormat = 'json'; showPreview = false; }}
								>
									JSON
								</button>
							</div>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								导入模式
							</label>
							<div class="flex gap-2">
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {importMode === 'append' ? 'bg-green-50 border-green-300 text-green-700 dark:bg-green-900/20 dark:border-green-700 dark:text-green-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => importMode = 'append'}
									title="在现有数据后追加"
								>
									追加
								</button>
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {importMode === 'overwrite' ? 'bg-red-50 border-red-300 text-red-700 dark:bg-red-900/20 dark:border-red-700 dark:text-red-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => importMode = 'overwrite'}
									title="清空现有数据后导入"
								>
									覆盖
								</button>
								<button
									class="px-3 py-2 text-sm rounded-lg border transition {importMode === 'merge' ? 'bg-yellow-50 border-yellow-300 text-yellow-700 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-400' : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
									on:click={() => importMode = 'merge'}
									title="根据标题合并更新现有数据"
								>
									合并
								</button>
							</div>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								导入数据
							</label>
							<div class="space-y-2">
								<div class="flex gap-2">
									<input
										type="file"
										accept=".csv,.json,.xlsx,.xls"
										on:change={handleFileSelect}
										class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900/20 dark:file:text-blue-400"
									/>
								</div>
								<textarea
									bind:value={importData}
									placeholder={importFormat === 'csv' ? '粘贴 CSV 数据...' : '粘贴 JSON 数据...'}
									class="w-full h-32 px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white font-mono"
								></textarea>
								<div class="flex gap-2">
									<button
										on:click={previewImport}
										class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition"
									>
										预览数据
									</button>
									<button
										on:click={downloadTemplate}
										class="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg transition"
									>
										下载模板
									</button>
								</div>
							</div>
						</div>

						{#if showPreview && previewData.length > 0}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									数据预览 ({previewData.length} 条)
								</label>
								<div class="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-auto max-h-48">
									<table class="min-w-full text-sm">
										<thead class="bg-gray-100 dark:bg-gray-700 sticky top-0">
											<tr>
												{#each Object.keys(previewData[0]) as key}
													<th class="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
														{key}
													</th>
												{/each}
											</tr>
										</thead>
										<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
									{#each previewData.slice(0, 5) as row}
											<tr>
												{#each Object.values(row) as val}
														<td class="px-3 py-2 text-gray-700 dark:text-gray-300 truncate max-w-32">
															{val}
														</td>
												{/each}
											</tr>
										{/each}
										</tbody>
									</table>
									{#if previewData.length > 5}
										<div class="px-3 py-2 text-xs text-gray-500 text-center">
											还有 {previewData.length - 5} 条数据...
										</div>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-800">
				<div class="text-sm text-gray-500">
					{#if mode === 'export'}
						共 {entries.length} 条数据
					{:else}
						{#if showPreview}
							预览 {previewData.length} 条数据
						{/if}
					{/if}
				</div>
				<div class="flex gap-2">
					<button
						on:click={close}
						class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
					>
						取消
					</button>
					{#if mode === 'export'}
						<button
							on:click={handleExport}
							disabled={entries.length === 0}
							class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
						>
							导出
						</button>
					{:else}
						<button
							on:click={handleImport}
							disabled={previewData.length === 0 || isProcessing}
							class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
						>
							{#if isProcessing}
								<Spinner className="size-4" />
							{/if}
							导入
						</button>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}
