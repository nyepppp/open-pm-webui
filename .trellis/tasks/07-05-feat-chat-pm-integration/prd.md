# 功能: 聊天页引用PM工作台+工具集成

## Goal

在聊天首页支持引用 PM 工作台功能，并将对应工具集成到聊天工具栏。

## Requirements

- 批注 #1: 需要 PM 工作台的功能在这里就可以引用
  - 选择器: `div[class="flex items-center h-full s-FdJNS9dGDztw"]`（聊天输入区域）
- 批注 #2: 引用 PM 工作台的功能
  - 选择器: `div[class="flex"]`（功能引用按钮区域）
- 批注 #3: 对应工具等
  - 选择器: `button#integration-menu-button`（集成菜单按钮）

## Acceptance Criteria

- [ ] 聊天输入区域可引用 PM 工作台的项目/文档
- [ ] 集成菜单中包含 PM 工作台相关工具
- [ ] 引用后可在聊天中查看/讨论 PM 内容
