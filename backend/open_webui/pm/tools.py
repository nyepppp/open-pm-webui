"""PM Tools for OpenWebUI Agent integration.

These tools allow the OpenWebUI agent to interact with PM workspace data.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class PMEntryCreateInput(BaseModel):
    """Input for creating a PM entry."""
    project_id: str = Field(..., description="Project ID")
    module_type: str = Field(..., description="Module type (requirement, parameter, testcase, etc.)")
    title: str = Field(..., description="Entry title")
    content: Optional[str] = Field(None, description="Entry content")
    data: Optional[dict] = Field(None, description="Module-specific data")
    priority: Optional[str] = Field("p2", description="Priority (p0, p1, p2, p3)")
    status: Optional[str] = Field("draft", description="Status (draft, review, approved, archived)")


class PMEntryUpdateInput(BaseModel):
    """Input for updating a PM entry."""
    entry_id: str = Field(..., description="Entry ID")
    title: Optional[str] = Field(None, description="New title")
    content: Optional[str] = Field(None, description="New content")
    data: Optional[dict] = Field(None, description="Module-specific data to merge")
    status: Optional[str] = Field(None, description="New status")
    priority: Optional[str] = Field(None, description="New priority")


class PMEntryQueryInput(BaseModel):
    """Input for querying PM entries."""
    project_id: str = Field(..., description="Project ID")
    module_type: Optional[str] = Field(None, description="Filter by module type")
    status: Optional[str] = Field(None, description="Filter by status")


class PMVersionCreateInput(BaseModel):
    """Input for creating a version snapshot."""
    project_id: str = Field(..., description="Project ID")
    entry_id: str = Field(..., description="Entry ID to snapshot")
    change_summary: Optional[str] = Field(None, description="Description of changes")


class PMRelationCreateInput(BaseModel):
    """Input for creating a relation between entries."""
    project_id: str = Field(..., description="Project ID")
    entity_a_id: str = Field(..., description="Source entity ID")
    entity_b_id: str = Field(..., description="Target entity ID")
    relation_type: str = Field("references", description="Relation type (contains, references, derives, modifies, conflicts)")


class PMTraceabilityAnalyzeInput(BaseModel):
    """Input for traceability analysis."""
    project_id: str = Field(..., description="Project ID")
    entry_id: Optional[str] = Field(None, description="Optional entry ID to analyze")


class PMWorkflowSuggestInput(BaseModel):
    """Input for workflow suggestions."""
    project_id: str = Field(..., description="Project ID")
    current_module: Optional[str] = Field(None, description="Current module type")
    current_status: Optional[str] = Field(None, description="Current status")
