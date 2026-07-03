---
name: User PM Workflow Preferences
description: User's preferences for PM module UX and feature priorities, observed from Vibe annotations
type: user
---

The user is a product manager who tests the PM workspace live and provides feedback via Vibe annotations on localhost:5173. Key preferences:

- **Version control should be Git-like**: Wants project-level version management (not just entry-level), with branch/merge/compare accessible from the version card. The version card "当前版本 v1.1" should be a gateway to full version management.
- **AI must integrate with OpenWebUI**: The AI assistant card should connect to OpenWebUI's existing chat/model infrastructure, not be a standalone feature. Unconfigured state should link to OpenWebUI model settings.
- **Parameters need hierarchical selection**: Module→Feature→Parameter cascade, with both select-from-existing and manual-input (combobox) modes. Order matters: module first, then feature, then parameter.
- **Import = full text, not chapter split**: Document import should inject complete content into the rich text editor. Chapter-based splitting is not the desired behavior.
- **Remove unnecessary UI chrome**: The PRD chapter outline sidebar was explicitly rejected ("去掉这个"). Prefers clean editing surfaces without extra navigation panels.
- **Roadmap needs time dimension**: Day/week/month toggle with prev/next navigation. Each row should show duration (days) and description. Current pure-CSS gantt is insufficient.
- **All items must show version info**: Every entry across all modules should display its version directly for quick identification.
- **Version badges must be read-only**: Version badges on entries should display which version the entry was created in — NOT be editable inline. The user does NOT want to manage versions from table/card rows. They just want to see "created in v1.0" as a read-only label. Version management happens at the project level.
- **Each content editor has its own independent version**: Saving within an editor (e.g., competitor analysis) only updates that entry's version, NOT the project-level version. The two version scopes are independent.
- **Import must populate the editor**: Document/file import should result in visible content in the rich text editor. Currently shows blank after import.
- **Parameter hierarchy is Module→Feature→Parameter**: Must be a cascading selection (combobox/dropdown) where Module is primary and pre-existing modules can be selected, then Feature under that module, then Parameter details.
- **Product-architecture = mindmap view, not table**: The product-architecture module should render as an interactive mindmap showing Project→Module(version)→Feature(version) with multi-version support.
- **Prototype module must be functional**: Users must be able to create and manage prototype/UI design entries; currently broken.
- **Schedule form must match table columns**: The "新建" form for schedule must include all fields visible in the table (assignee, dates, progress, milestone, etc.).
- **PRD editor must have section sidebar**: Contrary to earlier preference, the PRD editor MUST show a section sidebar (概述, 背景, 目标, 需求, 非功能需求, 附录) for navigating between document sections. The section sidebar should show content indicators (green dot when section has content).
- **Auto-associate version on create**: All new entries should automatically associate with the current project version on creation. This enables version filtering and traceability.
- **Calendar sync must work reliably**: Roadmap/schedule entries should sync to the calendar system with proper error handling, empty-calendar checks, and UI refresh after sync.
- **Remove fake/mock data directories**: Do not include placeholder, mock, or fake data directories in the UI. The user explicitly rejects them ("我都不要那个目录还给我弄上去了").

**How to apply:** When designing PM features, prioritize Git-like version metaphors, integration with existing OpenWebUI capabilities over new standalone systems, and hierarchical data selection over flat text inputs. Remove UI elements that duplicate functionality (like separate outline sidebars when the editor has headings). Version info on entries is display-only; version management is a project-level concern. Every module must be fully functional — no placeholder or broken editors.