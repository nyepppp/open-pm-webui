"""Documentation for pm-skills integration."""

# PM Skills Integration Documentation

## Overview

The PM Skills Integration enables Open WebUI to invoke 68+ pm-skills commands via Timbal Workflows embedded as Python library.

## Architecture

```
backend/open_webui/pm/
├── skills/
│   ├── pm-skills/              # Local copy of pm-skills repository
│   ├── pm_skills_loader.py     # Skill loading from local files
│   ├── skill_wrappers.py       # Timbal workflow wrappers
│   └── explicit_invocation.py  # Explicit command handler
├── workflows/
│   ├── base_workflow.py        # Base Timbal Workflow class
│   ├── discover_workflow.py    # Discovery workflow
│   └── write_prd_workflow.py   # PRD generation workflow
├── models/
│   ├── pm_skills_mapping.py    # Mapping model
│   └── pm_skills_version.py   # Version tracking model
├── services/
│   ├── pm_skills_mapping_service.py  # Mapping CRUD
│   ├── output_validator.py     # Output validation
│   ├── confirmation_service.py # Confirmation gates
│   ├── module_entry_service.py # ModuleEntry persistence
│   ├── command_resolver.py     # Command resolution
│   ├── context_analyzer.py     # Context analysis
│   ├── skill_relevance.py     # Skill relevance scoring
│   ├── mapping_validator.py    # Mapping validation
│   └── version_service.py      # Version management
└── timbal_config.py            # Timbal configuration
```

## Usage

### Explicit Invocation

```python
from open_webui.pm.skills.explicit_invocation import explicit_invocation_handler

# Handle /pm-write-prd command
result = await explicit_invocation_handler.handle("write-prd", {
    "feature_idea": "Smart notification system"
})
```

### Workflow Execution

```python
from open_webui.pm.workflows.discover_workflow import DiscoverWorkflow

# Run discovery workflow
workflow = DiscoverWorkflow()
results = await workflow.run(idea="AI-powered meeting summarizer")
```

### Agent Integration

```python
from open_webui.pm.agent.pm_skills_agent import pm_skills_agent

# Invoke skill via Agent
result = await pm_skills_agent.discover("AI-powered meeting summarizer")
```

## Configuration

### Timbal Settings

Edit `backend/open_webui/pm/timbal_config.py`:

```python
TIMBAL_CONFIG = {
    "model": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "workflow": {
        "timeout": 300,
        "max_retries": 3,
        "retry_delay": 1.0,
    },
}
```

### Environment Variables

- `TIMBAL_MODEL_PROVIDER`: Model provider (default: "openai")
- `TIMBAL_MODEL_NAME`: Model name (default: "gpt-4")
- `TIMBAL_TEMPERATURE`: Temperature (default: 0.7)
- `TIMBAL_MAX_TOKENS`: Max tokens (default: 4096)
- `TIMBAL_WORKFLOW_TIMEOUT`: Workflow timeout in seconds (default: 300)

## Performance

- Tool calls: ≤ 3s
- Skill loading: ≤ 1s
- Workflow execution: ≤ 5s

## Constitution Compliance

- **Principle I (Manual-First)**: Skills can be invoked manually via `/pm-<id>` commands
- **Principle II (Module-Centric)**: Skills are generic modules
- **Principle III (Human-Confirmed)**: All write operations require confirmation
- **Principle IV (Data Isolation)**: All operations scoped by `project_id`
- **Principle V (Version-Controlled)**: pm-skills versions pinned
- **Principle VI (Skill-as-Generic-Module)**: All pm-skills are SkillContract modules
