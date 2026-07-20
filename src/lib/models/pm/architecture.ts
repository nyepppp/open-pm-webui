export interface VersionRecord {
  version: string;
  operator: string;
  time: string;
  change_detail: string;
}

export interface DemandRelation {
  demand_id: string;
  demand_name: string;
  doc_link: string;
}

export interface BaseEntity {
  id: string;
  name: string;
  key: string;
  data_type: string;
  required: boolean;
  description: string;
  create_version: string;
  version_record: VersionRecord[];
  demand_relation: DemandRelation[];
  status: 'draft' | 'online' | 'offline';
  is_deleted: boolean;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Module extends BaseEntity {
  // Module-specific fields can be added here
}

export interface Function extends BaseEntity {
  module_id: string;
}

export interface Parameter extends BaseEntity {
  function_id: string;
}

export type EntityType = 'module' | 'function' | 'parameter';

export interface ArchitectureState {
  modules: Module[];
  functions: Function[];
  parameters: Parameter[];
  loading: boolean;
  error: string | null;
}