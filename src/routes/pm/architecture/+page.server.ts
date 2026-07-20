import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  try {
    // Fetch all architecture data
    const [modulesRes, functionsRes, parametersRes] = await Promise.all([
      fetch('/api/pm/modules'),
      fetch('/api/pm/functions'),
      fetch('/api/pm/parameters')
    ]);

    const [modules, functions, parameters] = await Promise.all([
      modulesRes.json(),
      functionsRes.json(),
      parametersRes.json()
    ]);

    return {
      modules,
      functions,
      parameters
    };
  } catch (error) {
    console.error('Failed to load architecture data:', error);
    return {
      modules: [],
      functions: [],
      parameters: [],
      error: 'Failed to load architecture data'
    };
  }
};