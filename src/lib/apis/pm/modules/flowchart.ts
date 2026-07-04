import { getEntries, createEntry, updateEntry, deleteEntry, getEntry } from '../index';
import type { ModuleEntry, ApiResponse, FlowchartData } from '../types';

const MODULE = 'flowchart';

export function getFlowchartList(projectId: string, page = 1, pageSize = 20, search = '') {
	return getEntries(projectId, MODULE);
}

export function getFlowchart(projectId: string, id: string) {
	return getEntry(id);
}

export function createFlowchart(projectId: string, data: Partial<ModuleEntry>) {
	return createEntry(projectId, { ...data, module_type: MODULE });
}

export function updateFlowchart(projectId: string, id: string, data: Partial<ModuleEntry>) {
	return updateEntry(id, data);
}

export function deleteFlowchart(projectId: string, id: string) {
	return deleteEntry(id);
}
