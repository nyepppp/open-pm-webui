# Research: Timbal-OpenWebUI Integration

**Date**: 2026-07-12
**Feature**: Timbal-OpenWebUI Integration
**Spec**: [spec.md](spec.md)

## Research Questions

### Q1: How does Timbal's API work?

**Findings**:
- Timbal exposes a Python-based workforce with a Bun/Elysia API layer
- Key endpoints: `POST /run`, `POST /stream`, `GET /healthcheck`
- Workflows are defined as Python DAGs (code-defined, not visual)
- Timbal UI is a standalone React app, not embeddable as a component
- Integration must be API-only

**Decision**: Use HTTP client to call Timbal API; do not attempt to embed Timbal UI

### Q2: How does Dify's workflow system work?

**Findings**:
- Dify uses a visual workflow editor with nodes and edges
- Nodes represent: LLM calls, tool calls, conditionals, loops, variables
- Workflows can be triggered via API or chat interface
- Supports version control and execution history
- Input/output mapping via JSON Schema

**Decision**: Adopt similar patterns: visual editor, API triggers, version control, JSON Schema inputs/outputs

### Q3: How should PM workspace data be exposed as tools?

**Findings**:
- PM workspace has entities: projects, requirements, documents, test cases
- Each entity has CRUD operations
- Timbal tools need: name, description, parameters, return schema
- OpenWebUI has skills, prompts, and tools that can be mapped

**Decision**: Create a tool registry that maps PM operations and OpenWebUI resources to Timbal-compatible tool definitions

### Q4: What are the best practices for workflow versioning?

**Findings**:
- Git-style versioning (commit hashes) provides full audit trail
- Branching allows draft workflows without affecting production
- Merging publishes drafts to production
- Rollback to any previous version must be supported

**Decision**: Implement Git-style versioning with commit hashes, branching, and merging

### Q5: How should the plugin bridge work?

**Findings**:
- Plugin bridge must provide a standard interface for tool registration
- Tools need: initialize, execute, validate methods
- Bridge handles authentication, routing, and response formatting
- Must support both PM operations and OpenWebUI resources

**Decision**: Implement a plugin bridge with a standard interface: `initialize(config)`, `execute(inputs)`, `validate(parameters)`

## Conclusion

All research questions have been resolved. The design decisions align with industry best practices and the user's explicit requirements. No blocking issues remain.
