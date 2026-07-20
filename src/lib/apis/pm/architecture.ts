import type { Module, Function, Parameter, VersionRecord, DemandRelation } from '$lib/models/pm/architecture';

const API_BASE = '/api/pm';

// Module API
export async function getModules(): Promise<Module[]> {
  const response = await fetch(`${API_BASE}/modules`);
  if (!response.ok) throw new Error('Failed to fetch modules');
  return response.json();
}

export async function createModule(data: Partial<Module>): Promise<Module> {
  // Auto-generate version record on creation
  const now = new Date().toISOString();
  const moduleData = {
    ...data,
    create_version: data.create_version || '1.0.0',
    version_record: data.version_record || [{
      version: data.create_version || '1.0.0',
      operator: 'system',
      time: now,
      change_detail: 'Initial creation'
    }],
    status: data.status || 'draft',
    is_deleted: false,
    deleted_at: null,
    created_at: now,
    updated_at: now
  };
  const response = await fetch(`${API_BASE}/modules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(moduleData)
  });
  if (!response.ok) throw new Error('Failed to create module');
  return response.json();
}

export async function updateModule(id: string, data: Partial<Module>): Promise<Module> {
  // Append version record on update
  const now = new Date().toISOString();
  const updateData = {
    ...data,
    updated_at: now
  };
  if (data.create_version) {
    updateData.version_record = [
      ...(data.version_record || []),
      {
        version: data.create_version,
        operator: 'system',
        time: now,
        change_detail: 'Updated'
      }
    ];
  }
  const response = await fetch(`${API_BASE}/modules/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updateData)
  });
  if (!response.ok) throw new Error('Failed to update module');
  return response.json();
}

export async function deleteModule(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/modules/${id}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete module');
}

export async function copyModule(id: string, copyDemands: boolean): Promise<Module> {
  const response = await fetch(`${API_BASE}/modules/${id}/copy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ copy_demands: copyDemands })
  });
  if (!response.ok) throw new Error('Failed to copy module');
  return response.json();
}

// Function API
export async function getFunctions(moduleId?: string): Promise<Function[]> {
  const url = moduleId ? `${API_BASE}/functions?module_id=${moduleId}` : `${API_BASE}/functions`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch functions');
  return response.json();
}

export async function createFunction(data: Partial<Function>): Promise<Function> {
  const response = await fetch(`${API_BASE}/functions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to create function');
  return response.json();
}

export async function updateFunction(id: string, data: Partial<Function>): Promise<Function> {
  const response = await fetch(`${API_BASE}/functions/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to update function');
  return response.json();
}

export async function deleteFunction(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/functions/${id}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete function');
}

// Parameter API
export async function getParameters(functionId?: string): Promise<Parameter[]> {
  const url = functionId ? `${API_BASE}/parameters?function_id=${functionId}` : `${API_BASE}/parameters`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch parameters');
  return response.json();
}

export async function createParameter(data: Partial<Parameter>): Promise<Parameter> {
  const response = await fetch(`${API_BASE}/parameters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to create parameter');
  return response.json();
}

export async function updateParameter(id: string, data: Partial<Parameter>): Promise<Parameter> {
  const response = await fetch(`${API_BASE}/parameters/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to update parameter');
  return response.json();
}

export async function deleteParameter(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/parameters/${id}`, {
    method: 'DELETE'
  });
  if (!response.ok) throw new Error('Failed to delete parameter');
}

// Version History Export
export async function exportVersionHistory(entityType: string, id: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/${entityType}s/${id}/version-history/export`);
  if (!response.ok) throw new Error('Failed to export version history');
  return response.blob();
}

// Mind Map Data
export async function getMindMapData(): Promise<any> {
  const response = await fetch(`${API_BASE}/architecture/mindmap`);
  if (!response.ok) throw new Error('Failed to fetch mind map data');
  return response.json();
}

// Utility functions
export function generateVersionRecord(
  version: string,
  operator: string,
  changeDetail: string
): VersionRecord {
  return {
    version,
    operator,
    time: new Date().toISOString(),
    change_detail: changeDetail
  };
}

export function addVersionRecord(
  existingRecords: VersionRecord[],
  newRecord: VersionRecord
): VersionRecord[] {
  return [...existingRecords, newRecord];
}

export function createDemandRelation(
  demandId: string,
  demandName: string,
  docLink: string
): DemandRelation {
  return {
    demand_id: demandId,
    demand_name: demandName,
    doc_link: docLink
  };
}