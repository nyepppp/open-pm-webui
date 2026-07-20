/**
 * Workflow Performance Optimization Utilities
 *
 * Provides performance optimization for large workflows and canvas rendering.
 */

export interface PerformanceConfig {
	maxNodesForFullRender: number;
	debounceMs: number;
	throttleMs: number;
	batchSize: number;
	virtualizationThreshold: number;
}

export const DEFAULT_PERFORMANCE_CONFIG: PerformanceConfig = {
	maxNodesForFullRender: 50,
	debounceMs: 16, // ~60fps
	throttleMs: 16,
	batchSize: 100,
	virtualizationThreshold: 100
};

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
	func: T,
	wait: number
): (...args: Parameters<T>) => void {
	let timeout: ReturnType<typeof setTimeout> | null = null;

	return function (...args: Parameters<T>) {
		if (timeout) {
			clearTimeout(timeout);
		}
		timeout = setTimeout(() => {
			func(...args);
		}, wait);
	};
}

/**
 * Throttle function for performance optimization
 */
export function throttle<T extends (...args: any[]) => any>(
	func: T,
	limit: number
): (...args: Parameters<T>) => void {
	let inThrottle = false;

	return function (...args: Parameters<T>) {
		if (!inThrottle) {
			func(...args);
			inThrottle = true;
			setTimeout(() => {
				inThrottle = false;
			}, limit);
		}
	};
}

/**
 * Batch array operations for better performance
 */
export function batchArray<T>(array: T[], batchSize: number): T[][] {
	const batches: T[][] = [];
	for (let i = 0; i < array.length; i += batchSize) {
		batches.push(array.slice(i, i + batchSize));
	}
	return batches;
}

/**
 * Virtual list calculator for large datasets
 */
export interface VirtualListState {
	startIndex: number;
	endIndex: number;
	visibleItems: number;
	scrollTop: number;
}

export function calculateVirtualList(
	totalItems: number,
	itemHeight: number,
	containerHeight: number,
	scrollTop: number,
	bufferItems: number = 5
): VirtualListState {
	const visibleItems = Math.ceil(containerHeight / itemHeight);
	const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferItems);
	const endIndex = Math.min(totalItems, startIndex + visibleItems + bufferItems * 2);

	return {
		startIndex,
		endIndex,
		visibleItems,
		scrollTop
	};
}

/**
 * Optimize canvas rendering for large workflows
 */
export class CanvasOptimizer {
	private config: PerformanceConfig;
	private visibleNodes: Set<string> = new Set();
	private nodePositions: Map<string, { x: number; y: number }> = new Map();

	constructor(config: Partial<PerformanceConfig> = {}) {
		this.config = { ...DEFAULT_PERFORMANCE_CONFIG, ...config };
	}

	/**
	 * Calculate visible nodes based on viewport
	 */
	calculateVisibleNodes(
		nodes: Array<{ id: string; position: { x: number; y: number } }>,
		viewport: { x: number; y: number; width: number; height: number },
		padding: number = 100
	): string[] {
		const visible: string[] = [];

		for (const node of nodes) {
			const pos = node.position;
			if (
				pos.x >= viewport.x - padding &&
				pos.x <= viewport.x + viewport.width + padding &&
				pos.y >= viewport.y - padding &&
				pos.y <= viewport.y + viewport.height + padding
			) {
				visible.push(node.id);
			}
		}

		return visible;
	}

	/**
	 * Check if full rendering should be used
	 */
	shouldUseFullRender(nodeCount: number): boolean {
		return nodeCount <= this.config.maxNodesForFullRender;
	}

	/**
	 * Get optimization strategy for node count
	 */
	getOptimizationStrategy(nodeCount: number): 'full' | 'virtualized' | 'simplified' {
		if (nodeCount <= this.config.maxNodesForFullRender) {
			return 'full';
		} else if (nodeCount <= this.config.virtualizationThreshold) {
			return 'virtualized';
		} else {
			return 'simplified';
		}
	}

	/**
	 * Optimize edge rendering for large graphs
	 */
	optimizeEdges(
		edges: Array<{ id: string; source: string; target: string }>,
		visibleNodes: Set<string>
	): Array<{ id: string; source: string; target: string }> {
		return edges.filter(
			edge => visibleNodes.has(edge.source) && visibleNodes.has(edge.target)
		);
	}

	/**
	 * Batch DOM updates for better performance
	 */
	batchDOMUpdates(updates: (() => void)[]): void {
		const batches = batchArray(updates, this.config.batchSize);

		let batchIndex = 0;
		const processBatch = () => {
			if (batchIndex >= batches.length) return;

			const batch = batches[batchIndex];
			requestAnimationFrame(() => {
				for (const update of batch) {
					update();
				}
				batchIndex++;
				processBatch();
			});
		};

		processBatch();
	}
}

/**
 * Memory management for workflow data
 */
export class WorkflowMemoryManager {
	private cache: Map<string, any> = new Map();
	private maxCacheSize: number;
	private accessTimes: Map<string, number> = new Map();

	constructor(maxCacheSize: number = 100) {
		this.maxCacheSize = maxCacheSize;
	}

	/**
	 * Get cached item
	 */
	get<T>(key: string): T | undefined {
		if (this.cache.has(key)) {
			this.accessTimes.set(key, Date.now());
			return this.cache.get(key);
		}
		return undefined;
	}

	/**
	 * Set cached item
	 */
	set(key: string, value: any): void {
		if (this.cache.size >= this.maxCacheSize) {
			this.evictLRU();
		}

		this.cache.set(key, value);
		this.accessTimes.set(key, Date.now());
	}

	/**
	 * Remove cached item
	 */
	remove(key: string): void {
		this.cache.delete(key);
		this.accessTimes.delete(key);
	}

	/**
	 * Clear cache
	 */
	clear(): void {
		this.cache.clear();
		this.accessTimes.clear();
	}

	/**
	 * Evict least recently used items
	 */
	private evictLRU(): void {
		let oldestKey: string | null = null;
		let oldestTime = Infinity;

		for (const [key, time] of this.accessTimes.entries()) {
			if (time < oldestTime) {
				oldestTime = time;
				oldestKey = key;
			}
		}

		if (oldestKey) {
			this.remove(oldestKey);
		}
	}
}

/**
 * Measure and report performance metrics
 */
export class PerformanceMonitor {
	private metrics: Map<string, number[]> = new Map();
	private enabled: boolean;

	constructor(enabled: boolean = true) {
		this.enabled = enabled;
	}

	/**
	 * Start timing an operation
	 */
	startTimer(name: string): () => number {
		if (!this.enabled) return () => 0;

		const startTime = performance.now();
		return () => {
			const duration = performance.now() - startTime;
			this.recordMetric(name, duration);
			return duration;
		};
	}

	/**
	 * Record a metric
	 */
	recordMetric(name: string, value: number): void {
		if (!this.enabled) return;

		if (!this.metrics.has(name)) {
			this.metrics.set(name, []);
		}
		this.metrics.get(name)!.push(value);
	}

	/**
	 * Get metric statistics
	 */
	getMetricStats(name: string): { avg: number; min: number; max: number; count: number } | null {
		const values = this.metrics.get(name);
		if (!values || values.length === 0) return null;

		const sum = values.reduce((a, b) => a + b, 0);
		return {
			avg: sum / values.length,
			min: Math.min(...values),
			max: Math.max(...values),
			count: values.length
		};
	}

	/**
	 * Get all metrics
	 */
	getAllMetrics(): Record<string, { avg: number; min: number; max: number; count: number }> {
		const result: Record<string, { avg: number; min: number; max: number; count: number }> = {};
		for (const [name] of this.metrics.entries()) {
			const stats = this.getMetricStats(name);
			if (stats) {
				result[name] = stats;
			}
		}
		return result;
	}

	/**
	 * Clear metrics
	 */
	clearMetrics(): void {
		this.metrics.clear();
	}
}

/**
 * Request animation frame helper with fallback
 */
export function requestAnimationFrameHelper(callback: () => void): number {
	if (typeof requestAnimationFrame !== 'undefined') {
		return requestAnimationFrame(callback);
	}
	return setTimeout(callback, 16) as unknown as number;
}

/**
 * Cancel animation frame helper
 */
export function cancelAnimationFrameHelper(id: number): void {
	if (typeof cancelAnimationFrame !== 'undefined') {
		cancelAnimationFrame(id);
	} else {
		clearTimeout(id);
	}
}
