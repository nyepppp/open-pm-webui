# Bug: 路线图同步到日程失败 + 版本号显示ID

## Goal

1. 修复路线图同步功能无法导入到 Open WebUI 日程的问题（可能缺少时间参数）
2. 修复版本号展示为 UUID 而不是版本号的问题

## Requirements

- 批注 #18: 路线图同步功能不能导入到 Open WebUI 日程，检查是否缺少时间等参数
- 批注 #19: 展示信息应该是版本号而不是 UUID 代码（如 `9f4d8fbc-5999-4567-9312-399848621816`）
- 版本号选择器: `span[class="px-2 py-1 rounded text-xs bg-blue-50 text-blue-600"]`

## Acceptance Criteria

- [ ] 路线图同步到日程功能正常工作，里程碑/版本能正确导入
- [ ] 版本号显示为可读的版本号（如 v1.0），而非 UUID
