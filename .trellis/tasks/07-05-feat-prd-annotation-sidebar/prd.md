# 功能: PRD编辑器去掉文章章节+批注侧边栏

## Goal

1. 去掉 PRD 编辑器中的"文章章节"切换功能（需求文档不需要此切换）
2. 为批注功能添加侧边栏，支持查看、修改、定位批注

## Requirements

- 批注 #5: 去掉文章章节，需求文档不需要这个来切换
  - 选择器: `div[class="px-4 py-3 border-b border-gray-200 dark:border-gray-700"]`（章节切换区域）
- 批注 #6: 批注功能需要一个侧边栏可以查看、修改、定位
  - 选择器: `div[class="pm-editor-content p-4 max-w-none s-YwVp-yALFlPZ"]`（编辑器内容区）
  - 相关组件: `PMAnnotationPanel.svelte`, `pmAnnotationExtension.ts`

## Acceptance Criteria

- [ ] PRD 编辑器不再显示"文章章节"切换
- [ ] 批注侧边栏可打开/关闭
- [ ] 侧边栏中可查看所有批注列表
- [ ] 点击批注可定位到编辑器中对应位置
- [ ] 侧边栏中可修改批注内容
