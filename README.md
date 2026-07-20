# Open PM WebUI 📋

![Version](https://img.shields.io/badge/version-0.1.0--pm-blue)
![Upstream](https://img.shields.io/badge/based%20on-OpenWebUI%200.9.6%20%2B%20Timbal-blue)
![License](https://img.shields.io/badge/license-Open%20WebUI%20License-orange)

![Open PM WebUI Banner](./banner.png)

**Open PM WebUI** 是一个面向产品经理的 AI 协作工作台，把 PRD、产品架构、需求池、参数清单、测试用例、风险问题、会议纪要、验收复盘、FAQ 等产品管理模块整合到统一界面中，并通过 AI Agent 自动化完成需求拆解、模块-功能-参数结构化、版本对比、影响分析等高价值任务。

---

## 🧱 项目身份与上游声明

本项目是 [OpenWebUI](https://github.com/open-webui/open-webui) v0.9.6 的衍生项目，并在两个方向上做了扩展：

1. **PM 工作台层** —— 在 OpenWebUI 之上叠加了一套完整的产品管理工作台，包含 9 大业务模块、版本控制、模块间关联追溯、思维导图 / 甘特图等多种可视化编辑器。
2. **Timbal 工作流引擎** —— 集成 [Timbal](https://github.com/timbal-ai/timbal) 作为工作流执行引擎，让 AI Agent 能够通过显式工作流完成 PRD→模块-功能-参数结构化转换、批量条目创建、二阶段确认删除等复杂操作。

### 上游致谢

- **[OpenWebUI](https://github.com/open-webui/open-webui)** by Timothy Jaeryang Baek —— 提供了聊天界面、模型管理、用户权限、RAG、Pipelines 等基础设施。本项目复用了 OpenWebUI 的全部基础设施层，仅在其上添加 PM 工作台和 Timbal 集成。
- **[Timbal](https://github.com/timbal-ai/timbal)** —— 提供了 Python 工作流执行引擎，作为 PM Agent 调用工具的运行时。
- **[pm-skills](https://github.com/phuryn/pm-skills)** v2.1.0 by phuryn —— 提供 68+ PM 技能定义（PRD、需求、参数、测试用例等），vendored 在 `backend/open_webui/pm/skills/pm-skills/`。本项目按原 License 使用，未做修改。

### License 声明

本仓库沿用 OpenWebUI 的多许可证策略，详见：
- [LICENSE](./LICENSE) —— Open WebUI License（适用于当前及之后的所有提交）
- [LICENSE_HISTORY](./LICENSE_HISTORY) —— 早期 MIT / BSD-3-Clause 提交的许可证历史
- [LICENSE_NOTICE](./LICENSE_NOTICE) —— 多许可证切换的 commit 边界说明

按 Open WebUI License 第 4 条，本衍生项目在终端用户数 ≤ 50（30 天滚动窗口）的场景下保留原品牌权利；如超出此范围需获得 Open WebUI Inc. 的书面许可。

---

## ✨ PM 平台核心特性

### 1. 模块化工作台

按规划 / 设计 / 执行 / 复盘 4 大业务分类组织 9 大模块：

| 分类 | 模块 |
|------|------|
| 🗺️ 规划 | PRD 文档、需求池、竞品分析、路线图 |
| 🎨 设计 | 参数清单、测试用例 |
| ⚡ 执行 | 风险问题、会议纪要 |
| 📊 复盘 | 验收复盘、FAQ / 培训、产品架构 |

### 2. 差异化编辑器

- 富文本（TipTap）：PRD、竞品、会议、验收、FAQ
- 结构化表单（zod 验证）：需求、参数、测试用例
- 混合编辑器：风险（表单 + 富文本）
- 思维导图（@xyflow/svelte）：路线图、产品架构
- 甘特图（frappe-gantt）

### 3. 版本控制

项目级版本快照 + 模块级增量标记，支持版本对比与回滚。

### 4. 数据关联与追溯

模块间双向可见的关联关系（参数 → PRD、测试用例 → 需求 / 参数），可视化追溯图，删除引用保护。

### 5. AI Agent 智能辅助

PM Agent 通过 9 个内置工具完成：
- PRD → 模块-功能-参数结构化转换
- 批量条目创建与预览
- 二阶段确认删除（危险操作先 preview 再执行）
- 多轮工具调用（基于 OpenWebUI 标准 chat loop）
- 模块间关联创建

### 6. Timbal 工作流集成

- 显式调用：通过 `/pm-write-prd` 等命令直接触发工作流
- Agent 调用：PM Agent 在 chat 中自主选择并调用工作流
- 双重持久化：执行结果同时写入执行日志和 PM 工作台

---

## 🚀 快速开始

### 前置依赖

- Python 3.11
- Node.js 18.13+（≤22.x）
- pnpm

### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
./start.sh  # Windows: start_windows.bat
```

### 前端启动

```bash
pnpm install
pnpm dev
```

访问 http://localhost:8080

---

## 📚 文档

- [PM 工作台设计](./docs/pm-workspace.md)
- [PM 开发者指南](./docs/pm-developer-guide.md)
- [Workflow Designer v2](./docs/workflow-designer-v2.md)
- [Trae Agent Code Wiki](./docs/trae-agent-code-wiki.md)

---

## 🗂️ 项目结构

```
open-pm-webui/
├── backend/
│   ├── lib/timbal/                   # Timbal 框架（vendored）
│   └── open_webui/
│       ├── pm/                       # PM 平台核心
│       │   ├── agent/                # PM Agent
│       │   ├── api/                  # PM API routes
│       │   ├── chat_context.py       # D42 系统消息
│       │   ├── models/               # PM 数据模型
│       │   ├── services/             # PM 业务服务
│       │   ├── skills/               # PM skills 集成
│       │   ├── tools/                # PM 内置工具
│       │   └── workflows/            # PM 工作流定义
│       ├── routers/                  # OpenWebUI + PM + Timbal 路由
│       └── ...                       # OpenWebUI 基础设施（复用）
├── src/
│   ├── lib/
│   │   ├── apis/pm/                  # PM 前端 API
│   │   ├── apis/timbal/              # Timbal 前端 API
│   │   ├── components/pm/            # PM UI 组件
│   │   └── stores/pm/                # PM 状态管理
│   └── routes/(app)/pm/              # PM 页面路由
├── docs/                             # PM 平台文档
├── LICENSE                           # Open WebUI License
├── LICENSE_HISTORY                   # 早期 license 历史
└── LICENSE_NOTICE                    # 多 license 切换说明
```

---

## 🤝 贡献

本项目当前不接受外部贡献。如需反馈或报告问题，请通过 GitHub Issues。

---

## 📄 License

本项目沿用 [Open WebUI License](./LICENSE)。详见 [LICENSE_HISTORY](./LICENSE_HISTORY) 和 [LICENSE_NOTICE](./LICENSE_NOTICE)。

Copyright (c) 2023- Open WebUI Inc. [Created by Timothy Jaeryang Baek]
PM 平台扩展部分 Copyright (c) 2026 open-pm-webui contributors.
