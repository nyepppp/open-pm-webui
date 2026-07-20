// Ambient module declaration for frappe-gantt src entry.
// frappe-gantt 1.2.2 发布包只有 src/ 无 dist/，需用 src/index.js 入口
// （详见 GanttChart.svelte 顶部注释 D15）
declare module 'frappe-gantt/src/index.js' {
	const Gantt: any;
	export default Gantt;
}

declare module 'frappe-gantt/src/styles/gantt.css';
