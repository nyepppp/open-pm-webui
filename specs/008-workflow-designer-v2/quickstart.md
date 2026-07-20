# Quickstart: Workflow Designer V2

**Feature**: Workflow Designer V2 - Global Access & AI Integration  
**Date**: 2026-07-11  
**Status**: Draft

---

## Prerequisites

- OpenWebUI instance running (v0.3.x or later)
- LLM model configured (OpenAI, Claude, or local)
- Modern browser (Chrome, Firefox, Safari, Edge)

---

## Scenario 1: Create and Run a Simple Workflow

### Step 1: Access the Workflow Designer

1. Log in to OpenWebUI
2. Look for "Workflows" in the global sidebar (same level as "PM Workspace")
3. Click "Workflows" to open the workflow list
4. Click "Create New" to open the designer

### Step 2: Build a Simple Workflow

1. Drag a **Start** node from the sidebar to the canvas
2. Drag an **LLM Call** node next to it
3. Drag an **End** node after the LLM Call
4. Connect nodes: Start → LLM Call → End
5. Click the LLM Call node to configure:
   - Model: Select your configured model
   - Prompt: "Summarize the following text: {{input.text}}"
   - Temperature: 0.7

### Step 3: Test Run

1. Click "Test Run" button in the toolbar
2. Enter test input: `{"text": "This is a sample text to summarize."}`
3. Click "Run"
4. Observe execution trace:
   - Start node: completed (10ms)
   - LLM Call node: running → completed (4.5s)
   - End node: completed (5ms)
5. Review output in the execution trace panel

### Expected Result

- Workflow executes successfully
- LLM Call node returns a summary
- Execution trace shows all nodes completed

---

## Scenario 2: AI-Generated Workflow

### Step 1: Generate Workflow

1. In the workflow designer, click "AI Generate"
2. Enter description: "Create a workflow that reads a URL, extracts text, summarizes it, and outputs the summary"
3. Click "Generate"
4. Wait for AI to generate the workflow (typically 5-10 seconds)

### Step 2: Review and Edit

1. Review the generated workflow on the canvas
2. Expected nodes:
   - Start
   - HTTP Request (to fetch URL)
   - Data Transform (extract text)
   - LLM Call (summarize)
   - End
3. Adjust parameters as needed
4. Save the workflow

### Expected Result

- AI generates a workflow with 4-5 nodes
- Nodes are properly connected
- Parameters are pre-filled with reasonable defaults

---

## Scenario 3: Chat Integration

### Step 1: Create a Workflow

1. Create a workflow named "Code Review"
2. Add nodes: Start → LLM Call (review code) → End
3. Configure LLM Call:
   - Prompt: "Review the following code for bugs and improvements: {{input.code}}"
   - Model: gpt-4
4. Save and activate the workflow

### Step 2: Use in Chat

1. Go to OpenWebUI chat
2. Click the workflow button (next to model selector)
3. Select "Code Review" workflow
4. Type: "Review this code: `function add(a, b) { return a + b; }`"
5. Send message

### Expected Result

- Workflow executes in chat
- Real-time execution trace visible:
  - "Running LLM Call..." (with spinner)
  - "Completed in 3.2s"
- Final output: Code review with suggestions

---

## Scenario 4: Import/Export

### Export Workflow

1. Open a workflow in the designer
2. Click "Export" → "JSON"
3. Save the `.json` file
4. Verify file contains: nodes, edges, parameters

### Import Workflow

1. In the workflow list, click "Import"
2. Select a BPMN file (e.g., from Camunda)
3. Review mapped nodes
4. Fix any warnings (unsupported elements)
5. Save the imported workflow

### Expected Result

- Exported JSON contains complete workflow definition
- Imported BPMN maps to internal node types
- Unsupported elements flagged with warnings

---

## Scenario 5: Cross-Project Sharing

### Step 1: Create Workflow in Project A

1. Switch to Project A
2. Create a workflow "Bug Report Generator"
3. Add nodes for bug report generation
4. Save

### Step 2: Use in Project B

1. Switch to Project B
2. Open workflow list
3. Search for "Bug Report Generator"
4. Click "Use in this project"
5. The workflow is now available in Project B

### Expected Result

- Workflow appears in Project B's list
- Can be executed in Project B context
- Original owner remains Project A

---

## Troubleshooting

### Workflow Execution Fails

**Symptom**: Node fails with "Model timeout"

**Solution**:
1. Check model is configured in OpenWebUI settings
2. Verify API key is valid
3. Try with a different model
4. Check network connectivity

### AI Generation Returns Invalid Workflow

**Symptom**: Generated workflow has disconnected nodes

**Solution**:
1. Click "Regenerate" to try again
2. Provide more specific description
3. Manually connect nodes after generation

### Chat Integration Not Working

**Symptom**: Workflow button not visible in chat

**Solution**:
1. Ensure workflow is in "active" status
2. Check workflow is pinned (if using pinned workflows)
3. Refresh the page
4. Check browser console for errors

---

## Performance Expectations

| Operation | Expected Time |
|-----------|--------------|
| Open designer | < 1s |
| Add node | < 100ms |
| Connect nodes | < 200ms |
| AI generate workflow | 5-10s |
| Test run (simple) | 1-5s |
| Test run (complex) | 10-30s |
| Export workflow | < 500ms |
| Import workflow | < 1s |
| Chat execution | 3-10s |

---

## Next Steps

After completing these scenarios, you can:

1. **Explore node types**: Try different node types (condition, loop, parallel)
2. **Create templates**: Save workflows as templates for reuse
3. **Share workflows**: Export and share with team members
4. **Integrate with PM modules**: Use PM module nodes in workflows
5. **Build complex pipelines**: Combine multiple workflows
