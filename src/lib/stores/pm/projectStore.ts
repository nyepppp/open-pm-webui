import { writable, derived, type Writable, type Readable } from 'svelte/store';
	import type { Project } from '$lib/apis/pm/types';

	// Default project for initial use
	const DEFAULT_PROJECT: Project = {
		id: 'default',
		name: '我的项目',
		description: '默认项目',
		type: 'general',
		status: 'active',
		createdAt: Date.now(),
		updatedAt: Date.now()
	};

	export const currentProject: Writable<Project | null> = writable(DEFAULT_PROJECT);
	export const projects: Writable<Project[]> = writable([DEFAULT_PROJECT]);
	export const projectLoading: Writable<boolean> = writable(false);
	export const projectError: Writable<string | null> = writable(null);

	export const currentProjectId: Readable<string> = derived(
		currentProject,
		$project => $project?.id || 'default'
	);

	export const currentProjectName: Readable<string | null> = derived(
		currentProject,
		$project => $project?.name ?? null
	);

	export function setCurrentProject(project: Project | null) {
		currentProject.set(project);
	}

	export function setProjects(projectList: Project[]) {
		projects.set(projectList);
	}

	export function addProject(project: Project) {
		projects.update(list => [...list, project]);
	}

	export function updateProject(updated: Project) {
		projects.update(list =>
			list.map(p => (p.id === updated.id ? updated : p))
		);
		currentProject.update(current => {
			if (current?.id === updated.id) {
				return updated;
			}
			return current;
		});
	}

	export function removeProject(projectId: string) {
		projects.update(list => list.filter(p => p.id !== projectId));
		currentProject.update(current => {
			if (current?.id === projectId) {
				return null;
			}
			return current;
		});
	}

	export function setProjectLoading(loading: boolean) {
		projectLoading.set(loading);
	}

	export function setProjectError(error: string | null) {
		projectError.set(error);
	}
