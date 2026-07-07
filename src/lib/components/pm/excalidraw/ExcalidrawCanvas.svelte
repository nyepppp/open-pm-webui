<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	// @ts-ignore - Excalidraw types are not fully exported
	import type { ExcalidrawImperativeAPI } from '@excalidraw/excalidraw';
	import '@excalidraw/excalidraw/index.css';

	interface Props {
		initialData?: any;
		onChange?: (elements: any[], appState: any) => void;
		onElementClick?: (element: any) => void;
		theme?: 'light' | 'dark';
		viewModeEnabled?: boolean;
		gridModeEnabled?: boolean;
	}

	let { initialData = { elements: [], appState: { viewBackgroundColor: '#ffffff', gridSize: 20 } }, onChange, onElementClick, theme = 'light', viewModeEnabled = false, gridModeEnabled = false }: Props = $props();

	let container: HTMLDivElement;
	let excalidrawAPI: ExcalidrawImperativeAPI | null = $state(null);
	let root: any = null;
	let isInitialized = false;

	onMount(async () => {
		if (!container) return;

		// Dynamically import React and Excalidraw
		const [{ createRoot }, { Excalidraw }] = await Promise.all([
			import('react-dom/client'),
			import('@excalidraw/excalidraw')
		]);

		// Create React root
		root = createRoot(container);

		// Render Excalidraw
		const react = await import('react');
		
		const handleChange = (elements: any[], appState: any) => {
			onChange?.(elements, appState);
		};

		const handleElementClick = (element: any) => {
			onElementClick?.(element);
		};

		root.render(
			react.createElement(Excalidraw, {
				initialData: initialData || undefined,
				onChange: handleChange,
				onPointerDown: (event: any, pointerDownState: any) => {
					// Handle element click - also handle double click for text editing
					if (pointerDownState?.hit?.element) {
						handleElementClick(pointerDownState.hit.element);
					}
				},
				onPointerUp: (event: any, pointerUpState: any) => {
					// Handle element selection on pointer up (more reliable than pointer down)
					if (pointerUpState?.hit?.element) {
						handleElementClick(pointerUpState.hit.element);
					}
				},
				excalidrawAPI: (api: ExcalidrawImperativeAPI) => {
					excalidrawAPI = api;
					isInitialized = true;
				},
				theme,
				viewModeEnabled,
				gridModeEnabled,
				UIOptions: {
					canvasActions: {
						loadScene: false,
						export: { save: true }
					}
				}
			})
		);
	});

	// Watch for initialData changes and update scene
	$effect(() => {
		const data = initialData;
		if (isInitialized && excalidrawAPI && data && data.elements && data.elements.length > 0) {
			// Only update if we have valid initialData
			try {
				excalidrawAPI.updateScene(data);
			} catch (e) {
				console.warn('Failed to update Excalidraw scene:', e);
			}
		}
	});

	onDestroy(() => {
		if (root) {
			root.unmount();
			root = null;
		}
	});
</script>

<div bind:this={container} style="width: 100%; height: 100%;"></div>
