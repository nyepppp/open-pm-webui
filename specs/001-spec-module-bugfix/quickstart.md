# Quickstart: SPEC Module Bug Fixes

**Date**: 2026-07-10
**Feature**: SPEC Module Bug Fixes

## Prerequisites

- Open WebUI dev server running (`npm run dev` or equivalent)
- A project with at least one SPEC entry
- The project should have some requirement and parameter entries (for testing association)

## Validation Scenarios

### Scenario 1: Real Data Association

1. Navigate to a project's SPEC module: `/pm/{projectId}/spec`
2. Click "新建 SPEC" to create a new SPEC (or edit an existing one)
3. In the SPEC editor, look for the "关联需求" and "关联参数" dropdowns
4. **Expected**: Dropdowns show real requirement/parameter entries from the project
5. Select a requirement and a parameter
6. Save the SPEC
7. Reload the page
8. **Expected**: The selected associations persist and display correctly

### Scenario 2: Glossary Insert

1. Open a SPEC entry for editing
2. Ensure the SPEC category is "前端原型 SPEC" (to show glossary panel)
3. Look for the "术语参考" panel on the right side
4. Click on any term's "插入" button
5. **Expected**: The term definition is inserted into the editor at the cursor position

### Scenario 3: Annotation Sync

1. Open a SPEC entry for editing
2. Select some text in the editor
3. Click the annotation button (or use the annotation panel)
4. Add a new annotation with some content
5. Save the SPEC
6. Reload the page
7. **Expected**: The annotation is still visible in the annotation panel

### Scenario 4: AI Modify

1. Open a SPEC entry with at least one annotation
2. In the annotation panel, click the "AI修改" button on an annotation
3. **Expected**: An AI editing workflow is initiated (e.g., a modal opens, or the agent chat panel opens with the annotation content)

## Expected Outcomes

| Scenario | Expected Result |
|---|---|
| Real Data Association | No mock data ("示例条目", "123测试测试测试") appears; all dropdowns show real entries |
| Glossary Insert | Content is inserted into the editor; no console errors |
| Annotation Sync | Annotations persist across page reloads |
| AI Modify | AI workflow triggers; graceful fallback if AI unavailable |

## Troubleshooting

- **Dropdowns empty**: Check that `getEntries` API returns data for the target module type
- **Glossary insert not working**: Check browser console for `editor is undefined` — ensure `editor` prop is passed
- **Annotations not persisting**: Check Network tab for `updateEntry` API call after annotation change
- **AI Modify not working**: Check that AI service is configured and available
