import type { FlowchartData } from '$lib/apis/pm/types';

/**
 * Export flowchart data to CSV format
 */
export function exportFlowchartToCSV(data: FlowchartData): string {
	const headers = ['节点ID', '节点名称', '节点类型', '绑定实体类型', '绑定实体名称', '绑定版本', '输入参数', '输出参数', '描述'];
	
	const rows = data.nodes.map(node => {
		const traceability = node.data.traceability;
		return [
			node.id,
			node.data.label,
			node.type,
			traceability ? traceability.entityType : '',
			traceability ? traceability.entityName : '',
			traceability ? traceability.versionNumber || '' : '',
			(node.data.inputParams || []).join(', '),
			(node.data.outputParams || []).join(', '),
			node.data.description || ''
		];
	});

	const csvContent = [
		headers.join(','),
		...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
	].join('\n');

	return csvContent;
}

/**
 * Export flowchart data to Excel format (using xlsx library)
 */
export async function exportFlowchartToExcel(data: FlowchartData): Promise<Uint8Array> {
	// Dynamic import to avoid bundling xlsx in the main chunk
	const XLSX = await import('xlsx');
	
	const headers = ['节点ID', '节点名称', '节点类型', '绑定实体类型', '绑定实体名称', '绑定版本', '输入参数', '输出参数', '描述'];
	
	const rows = data.nodes.map(node => {
		const traceability = node.data.traceability;
		return [
			node.id,
			node.data.label,
			node.type,
			traceability ? traceability.entityType : '',
			traceability ? traceability.entityName : '',
			traceability ? traceability.versionNumber || '' : '',
			(node.data.inputParams || []).join(', '),
			(node.data.outputParams || []).join(', '),
			node.data.description || ''
		];
	});

	const worksheet = XLSX.utils.aoa_to_sheet([headers, ...rows]);
	const workbook = XLSX.utils.book_new();
	XLSX.utils.book_append_sheet(workbook, worksheet, '流程图数据');
	
	return XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
}

/**
 * Trigger file download
 */
export function downloadFile(data: string | Uint8Array, filename: string, mimeType: string = 'text/csv') {
	const blob = new Blob([data as BlobPart], { type: mimeType });
	
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
}
