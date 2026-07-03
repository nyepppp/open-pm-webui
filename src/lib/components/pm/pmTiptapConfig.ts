import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Highlight from '@tiptap/extension-highlight';
import Typography from '@tiptap/extension-typography';
import Underline from '@tiptap/extension-underline';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import { TableKit } from '@tiptap/extension-table';
import { ListKit } from '@tiptap/extension-list';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
import Mention from '@tiptap/extension-mention';
import BubbleMenu from '@tiptap/extension-bubble-menu';
import FloatingMenu from '@tiptap/extension-floating-menu';
import { createLowlight } from 'lowlight';
import hljs from 'highlight.js';
import { AnnotationExtension } from './pmAnnotationExtension';

const lowlight = createLowlight(
	hljs.listLanguages().reduce(
		(obj, lang) => {
			obj[lang] = () => hljs.getLanguage(lang);
			return obj;
		},
		{} as Record<string, any>
	)
);

export function getPMExtensions(placeholderText: string = '开始输入内容...') {
	return [
		StarterKit.configure({
			heading: { levels: [1, 2, 3, 4, 5, 6] },
			codeBlock: false
		}),
		Placeholder.configure({ placeholder: placeholderText }),
		Highlight.configure({ multicolor: true }),
		Typography,
		Underline,
		Link.configure({
			openOnClick: false,
			autolink: true,
			HTMLAttributes: { rel: 'noopener noreferrer', target: '_blank' }
		}),
		Image.configure({
			HTMLAttributes: { class: 'pm-editor-image' }
		}),
		TableKit,
		ListKit,
		CodeBlockLowlight.configure({ lowlight }),
		Mention.configure({
			suggestion: {
				items: () => [],
				render: () => ({
					onStart: () => {},
					onUpdate: () => {},
					onKeyDown: () => false,
					onExit: () => {}
				})
			}
		}),
		BubbleMenu,
		FloatingMenu,
		AnnotationExtension
	];
}

export type HeadingItem = {
	id: string;
	level: number;
	text: string;
};

export function extractHeadings(editor: Editor): HeadingItem[] {
	const headings: HeadingItem[] = [];
	const doc = editor.state.doc;

	doc.descendants((node, pos) => {
		if (node.type.name === 'heading') {
			const level = node.attrs.level as number;
			const text = node.textContent;
			const id = `heading-${pos}`;
			headings.push({ id, level, text });
		}
	});

	return headings;
}
