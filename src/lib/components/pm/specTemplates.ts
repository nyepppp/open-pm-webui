/**
 * SPEC Module — Template and Glossary Data
 * Built-in templates for SPEC document creation and glossary terms for reference panel
 */

// ============================================================================
// Template Types & Data
// ============================================================================

export interface SpecTemplate {
	id: string;
	name: string;
	category: 'functional' | 'prototype';
	content: string;
	isBuiltIn: boolean;
}

export const SPEC_TEMPLATES: SpecTemplate[] = [
	{
		id: 'builtin-functional',
		name: '功能 SPEC',
		category: 'functional',
		isBuiltIn: true,
		content: `<h2>概述</h2>
<p>描述此功能的目的、范围和目标用户。</p>
<h2>需求追溯</h2>
<p><em>关联的需求文档和参数配置将在此处展示。</em></p>
<ul>
<li>关联需求：（选择关联的需求条目）</li>
<li>关联参数：（选择关联的参数条目）</li>
</ul>
<h2>功能规格</h2>
<h3>输入</h3>
<p>描述输入条件、数据来源和约束。</p>
<h3>处理逻辑</h3>
<p>描述核心业务规则和处理流程。</p>
<h3>输出</h3>
<p>描述预期输出、状态变更和下游影响。</p>
<h3>异常处理</h3>
<p>描述边界条件、异常场景和错误处理策略。</p>
<h2>验收标准</h2>
<ul>
<li>验收条件 1：</li>
<li>验收条件 2：</li>
<li>验收条件 3：</li>
</ul>`
	},
	{
		id: 'builtin-prototype',
		name: '前端原型 SPEC',
		category: 'prototype',
		isBuiltIn: true,
		content: `<h2>设计规范追溯</h2>
<p><em>本规范遵循的设计规范参考。</em></p>
<ul>
<li>布局排版规范：（参考布局排版 SPEC 术语）</li>
<li>文字排版规范：（参考文字排版 SPEC 术语）</li>
<li>色彩系统规范：（参考色彩系统 SPEC 术语）</li>
</ul>
<h2>页面结构</h2>
<p>描述页面布局模式、栅格划分和区域划分。</p>
<h3>布局模式</h3>
<p>选择适用的布局模式：单栏 / 侧边栏 / 分栏 / 卡片网格 / 仪表盘 / 主从布局</p>
<h3>栅格规格</h3>
<p>描述列数、槽距、断点等栅格参数。</p>
<h2>交互规格</h2>
<p>描述用户操作流程、反馈方式和状态变更。</p>
<h3>操作流程</h3>
<p>描述主要用户操作路径和交互步骤。</p>
<h3>反馈方式</h3>
<p>描述操作反馈：加载态、成功/失败提示、过渡动效。</p>
<h2>组件规格</h2>
<p>描述页面使用的组件属性、状态和样式约束。</p>
<h3>组件清单</h3>
<ul>
<li>组件 1：（属性、状态、样式说明）</li>
<li>组件 2：（属性、状态、样式说明）</li>
</ul>
<h2>响应式策略</h2>
<p>描述断点设置和不同屏幕尺寸下的适配方案。</p>
<h3>断点定义</h3>
<ul>
<li>移动端（&lt;640px）：</li>
<li>平板（640px-1024px）：</li>
<li>桌面端（&gt;1024px）：</li>
</ul>`
	}
];

// ============================================================================
// Glossary Types & Data
// ============================================================================

export interface GlossaryTerm {
	term: string;
	termEn: string;
	definition: string;
}

export const GLOSSARY_DATA: Record<string, GlossaryTerm[]> = {
	layout: [
		{ term: '布局', termEn: 'Layout', definition: '处理界面元素放在哪里，导航、正文、侧边栏等在屏幕上的位置关系' },
		{ term: '构图', termEn: 'Composition', definition: '元素放在一起后的画面关系，视线先落在哪里，哪个区域更重' },
		{ term: '视觉层级', termEn: 'Visual Hierarchy', definition: '用尺寸、字重、颜色对比和留白拉开信息优先级' },
		{ term: '栅格', termEn: 'Grid', definition: '由行、栏、槽距和页面边距组成的参考线系统，12栏栅格在Web中很常见' },
		{ term: '页面容器', termEn: 'Container', definition: '承载页面主要内容的外层区域，通常设置max-width后在视口中居中' },
		{ term: '页面外边距', termEn: 'Margin', definition: '容器边缘到浏览器边缘之间的空白，给内容和屏幕边缘留出缓冲' },
		{ term: '行', termEn: 'Row', definition: '水平方向上的布局带，把多个内容块放在同一层' },
		{ term: '栏', termEn: 'Column', definition: '垂直方向的分栏基准，内容可以占一栏也可以跨多栏' },
		{ term: '槽距', termEn: 'Gutter', definition: '相邻栏或行之间的空白，把内容隔开避免相邻信息粘在一起' },
		{ term: '模块', termEn: 'Module', definition: '落在栅格里的实际内容块，可以占一栏也可以跨多栏' },
		{ term: '基线网格', termEn: 'Baseline Grid', definition: '纵向排版的参考线，让文本行高和段落间距落在同一套节奏上' },
		{ term: '断点', termEn: 'Breakpoint', definition: '布局规则发生变化的宽度位置，到达断点后页面可能切换结构' },
		{ term: '响应式布局', termEn: 'Responsive Design', definition: '随可用空间连续调整，容器变窄时元素先压缩或换行，再通过断点切换结构' },
		{ term: '弹性布局', termEn: 'Flexbox', definition: '一维布局模型，处理一条轴线上的排列、分布和对齐，适合导航栏、按钮组、工具栏' },
		{ term: 'CSS 栅格布局', termEn: 'CSS Grid', definition: '二维布局模型，可以同时控制行和列，适合页面骨架、卡片矩阵和仪表盘' },
		{ term: '定位', termEn: 'Positioning', definition: '决定元素如何确定位置：static跟随文档流，relative相对自身偏移，absolute脱离文档流' },
		{ term: '层级', termEn: 'Z-index', definition: '控制重叠元素在视觉上的前后顺序，只在特定层叠环境中比较' },
		{ term: '溢出', termEn: 'Overflow', definition: '内容超出盒子边界时的处理方式：继续显示、截断或提供滚动' },
		{ term: '侧边栏布局', termEn: 'Sidebar', definition: '一侧放导航或筛选项，另一侧放主要内容，后台和文档站常用' },
		{ term: '卡片网格', termEn: 'Card Grid', definition: '把信息封装在独立卡片里再按矩阵排列，卡片边界清楚便于扫视比较' }
	],
	typography: [
		{ term: '文字排版', termEn: 'Typography', definition: '文本的字体选择、间距调整、版面布局及最终阅读呈现方式' },
		{ term: '字体', termEn: 'Font', definition: '特定样式、粗细和尺寸的字形集合，通常指.ttf/.otf数据文件' },
		{ term: '衬线体', termEn: 'Serif', definition: '笔画末端带有装饰性尖角的字体，视觉偏传统正式，常用于长文阅读' },
		{ term: '无衬线体', termEn: 'Sans-Serif', definition: '笔画末端平滑无装饰的字体，视觉简洁清晰，是界面常用选择' },
		{ term: '等宽字体', termEn: 'Monospace', definition: '每个字符占用相同水平宽度的字体，常用于代码编辑器和终端' },
		{ term: '字间距', termEn: 'Tracking', definition: '均匀应用在整段文本中所有字符之间的水平间距，CSS通过letter-spacing控制' },
		{ term: '字距微调', termEn: 'Kerning', definition: '调整特定两个字母之间的间距，修正因字母形状产生的视觉空隙' },
		{ term: '行间距', termEn: 'Leading', definition: '文本行之间的垂直距离，CSS通过line-height控制，影响连续阅读体验' },
		{ term: '对齐方式', termEn: 'Alignment', definition: '文本沿基准线水平排列的规则：左对齐、右对齐、居中、两端对齐' },
		{ term: '基线', termEn: 'Baseline', definition: '大多数英文字母排列所在的水平基准线，是文本垂直对齐的基准' },
		{ term: 'x 字高', termEn: 'X-height', definition: '小写字母主体部分的垂直高度，两个字体同字号看起来大小不同常因x-height不同' },
		{ term: '像素', termEn: 'PX', definition: '屏幕显示的基本度量单位，CSS中作为逻辑像素，最终物理像素由DPR决定' },
		{ term: '相对单位', termEn: 'EM', definition: '1em等于当前元素font-size计算值，会随嵌套层级字号变化累乘' },
		{ term: '根相对单位', termEn: 'REM', definition: '1rem相对于HTML根元素font-size，避免深度嵌套字号累乘，设计系统常用' },
		{ term: '字符单位', termEn: 'CH', definition: '等于当前字体中数字0的宽度，输入框宽度和代码块行长可用它对应字符数' },
		{ term: '字体回退', termEn: 'Font Fallback', definition: '浏览器依次检索备用字体的机制，合理字体栈可降低加载失败和跨平台差异风险' },
		{ term: '连字', termEn: 'Ligature', definition: '将两个或多个相邻字母合并为一个字形显示的技术，如fi连字或=>符号' },
		{ term: '升部', termEn: 'Ascender', definition: '小写字母中超出x字高向上延伸的笔画，如b、d、h的上半部分' },
		{ term: '降部', termEn: 'Descender', definition: '小写字母向下延伸超出基线的部分，如g、j、p的下半部分' },
		{ term: '大写字高', termEn: 'Cap Height', definition: '从基线到大写英文字母顶端的垂直高度，与x字高共同决定字体视觉比例' }
	],
	color: [
		{ term: '色相', termEn: 'Hue', definition: '颜色属于哪一类——红黄绿蓝紫，HSL/HSV中用0°到360°的圆环表示' },
		{ term: '饱和度', termEn: 'Saturation', definition: '颜色的鲜艳程度，饱和度高更亮眼，饱和度低往灰里走' },
		{ term: '彩度', termEn: 'Chroma', definition: 'OKLCH模型中描述颜色离灰轴有多远，彩度稳定则颜色阶梯更容易成套' },
		{ term: '明度', termEn: 'Lightness', definition: '颜色在调色模型里的明暗，HSL中0%接近黑色，100%接近白色' },
		{ term: '透明通道', termEn: 'Alpha', definition: '描述颜色的透明度，Alpha为1完全盖住下层，降低后下层内容透出' },
		{ term: 'RGB', termEn: 'RGB', definition: '用红绿蓝三个发光通道混出屏幕颜色，每个通道0-255' },
		{ term: '十六进制色码', termEn: 'Hex Code', definition: '以#开头的6位十六进制颜色码，每两位控制一个RGB通道' },
		{ term: 'HSL', termEn: 'HSL', definition: '把颜色拆成色相、饱和度和明度，更接近日常调色的话语' },
		{ term: 'OKLCH', termEn: 'OKLCH', definition: 'L更接近人眼感知亮度，适合做颜色阶梯、主题切换和对比度控制' },
		{ term: '调色盘', termEn: 'Palette', definition: '项目允许使用的一组颜色，避免每个页面自己挑色，方便团队对齐' },
		{ term: '色阶', termEn: 'Color Scale', definition: '把一个基础色做成深浅阶梯，浅色做背景，基础色做按钮，深色做hover/文字' },
		{ term: '主色', termEn: 'Primary Color', definition: '产品最常用最易被记住的颜色，出现在主按钮、选中项和品牌区域' },
		{ term: '语义色', termEn: 'Semantic Color', definition: '带含义的状态颜色：绿色成功、红色危险、黄色警告，最好配合文字/图标使用' },
		{ term: '设计令牌', termEn: 'Design Tokens', definition: '把设计决策存成变量，设计稿和代码用同一套名字，而非互相猜色值' },
		{ term: '对比度', termEn: 'Contrast Ratio', definition: '前景色和背景色的亮度差，WCAG AA要求普通文本不低于4.5:1' },
		{ term: 'WCAG', termEn: 'WCAG', definition: '网页无障碍标准，AA级要求普通文本对比度≥4.5:1，大号文本≥3:1' },
		{ term: '渐变色', termEn: 'Gradient', definition: '两种或多种颜色平滑过渡，浏览器计算中间颜色实现连续变化' },
		{ term: '混合模式', termEn: 'Blending Mode', definition: '决定上层颜色和下层颜色怎么混合，不同模式用不同算法计算交界颜色' },
		{ term: '前景色', termEn: 'Foreground', definition: '通常是文字、图标和边框的颜色，要和背景保持足够对比度' },
		{ term: '背景色', termEn: 'Background', definition: '文字、图标、按钮下面的底色，影响整体明暗和内容可读性' }
	]
};
