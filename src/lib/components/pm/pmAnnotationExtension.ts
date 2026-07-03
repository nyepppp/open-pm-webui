import { Mark } from '@tiptap/core';

export interface AnnotationOptions {
	HTMLAttributes: Record<string, unknown>;
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		annotation: {
			/**
			 * Set an annotation mark on the current selection
			 */
			setAnnotation: (attributes: { id: string; color?: string }) => ReturnType;
			/**
			 * Toggle an annotation mark on the current selection
			 */
			toggleAnnotation: (attributes: { id: string; color?: string }) => ReturnType;
			/**
			 * Remove an annotation mark from the current selection
			 */
			unsetAnnotation: () => ReturnType;
		};
	}
}

export const AnnotationExtension = Mark.create<AnnotationOptions>({
	name: 'annotation',

	addOptions() {
		return {
			HTMLAttributes: {}
		};
	},

	addAttributes() {
		return {
			id: {
				default: null,
				parseHTML: (element) => element.getAttribute('data-annotation-id'),
				renderHTML: (attributes) => {
					if (!attributes.id) return {};
					return { 'data-annotation-id': attributes.id };
				}
			},
			color: {
				default: 'yellow',
				parseHTML: (element) => element.getAttribute('data-annotation-color') || 'yellow',
				renderHTML: (attributes) => {
					return { 'data-annotation-color': attributes.color };
				}
			}
		};
	},

	parseHTML() {
		return [
			{
				tag: 'span[data-annotation-id]'
			}
		];
	},

	renderHTML({ HTMLAttributes }) {
		return [
			'span',
			{
				style: 'background-color: #FFF9C4; border-bottom: 2px solid #FFD600',
				...HTMLAttributes
			},
			0
		];
	},

	addCommands() {
		return {
			setAnnotation:
				(attributes) =>
				({ commands }) => {
					return commands.setMark(this.name, attributes);
				},
			toggleAnnotation:
				(attributes) =>
				({ commands }) => {
					return commands.toggleMark(this.name, attributes);
				},
			unsetAnnotation:
				() =>
				({ commands }) => {
					return commands.unsetMark(this.name);
				}
		};
	}
});
