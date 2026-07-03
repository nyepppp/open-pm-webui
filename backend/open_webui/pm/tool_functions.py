"""PM Tool functions for OpenWebUI Agent integration."""

from typing import Any, Optional

from open_webui.pm.tools import (
    PMEntryCreateInput,
    PMEntryUpdateInput,
    PMEntryQueryInput,
    PMVersionCreateInput,
    PMRelationCreateInput,
    PMTraceabilityAnalyzeInput,
    PMWorkflowSuggestInput,
)


async def pm_entry_create(input_data: PMEntryCreateInput, user_id: str, db=None) -> dict:
    """Create a new PM entry."""
    from open_webui.models.pm import PMEntries, PMEntryForm
    
    form_data = PMEntryForm(
        project_id=input_data.project_id,
        module_type=input_data.module_type,
        title=input_data.title,
        content=input_data.content,
        data=input_data.data,
        priority=input_data.priority,
        status=input_data.status,
    )
    entry = await PMEntries.insert_new_entry(user_id, form_data, db=db)
    return {
        "success": entry is not None,
        "entry_id": entry.id if entry else None,
        "title": entry.title if entry else None,
    }


async def pm_entry_update(input_data: PMEntryUpdateInput, user_id: str, db=None) -> dict:
    """Update an existing PM entry."""
    from open_webui.models.pm import PMEntries, PMEntryUpdateForm
    
    update_data = {}
    if input_data.title is not None:
        update_data["title"] = input_data.title
    if input_data.content is not None:
        update_data["content"] = input_data.content
    if input_data.data is not None:
        update_data["data"] = input_data.data
    if input_data.status is not None:
        update_data["status"] = input_data.status
    if input_data.priority is not None:
        update_data["priority"] = input_data.priority
    
    form_data = PMEntryUpdateForm(**update_data)
    entry = await PMEntries.update_entry_by_id(input_data.entry_id, form_data, db=db)
    return {
        "success": entry is not None,
        "entry_id": entry.id if entry else None,
        "title": entry.title if entry else None,
    }


async def pm_entry_query(input_data: PMEntryQueryInput, user_id: str, db=None) -> dict:
    """Query PM entries by project and optional filters."""
    from open_webui.models.pm import PMEntries
    
    entries = await PMEntries.get_entries_by_project_id(input_data.project_id, db=db)
    
    if input_data.module_type:
        entries = [e for e in entries if e.module_type == input_data.module_type]
    if input_data.status:
        entries = [e for e in entries if e.status == input_data.status]
    
    return {
        "success": True,
        "count": len(entries),
        "entries": [
            {
                "id": e.id,
                "title": e.title,
                "module_type": e.module_type,
                "status": e.status,
                "priority": e.priority,
                "created_at": e.created_at,
            }
            for e in entries
        ],
    }


async def pm_version_create(input_data: PMVersionCreateInput, user_id: str, db=None) -> dict:
    """Create a version snapshot for an entry."""
    from open_webui.models.pm import PMEntryVersions, PMEntryVersionForm, PMEntries
    
    entry = await PMEntries.get_entry_by_id(input_data.entry_id, db=db)
    if not entry:
        return {"success": False, "error": "Entry not found"}
    
    version_form = PMEntryVersionForm(
        entry_id=input_data.entry_id,
        project_id=input_data.project_id,
        module_type=entry.module_type,
        content=entry.content,
        entry_metadata=entry.data,
        change_summary=input_data.change_summary or "Version snapshot",
    )
    version = await PMEntryVersions.insert_new_version(user_id, version_form, db=db)
    return {
        "success": version is not None,
        "version_id": version.id if version else None,
        "version_number": version.version_number if version else None,
    }


async def pm_relation_create(input_data: PMRelationCreateInput, user_id: str, db=None) -> dict:
    """Create a relation between two entities."""
    from open_webui.models.pm import PMRelations, PMRelationForm
    
    relation_form = PMRelationForm(
        project_id=input_data.project_id,
        entity_a_id=input_data.entity_a_id,
        entity_b_id=input_data.entity_b_id,
        relation_type=input_data.relation_type,
        created_by=user_id,
    )
    relation = await PMRelations.insert_new_relation(user_id, relation_form, db=db)
    return {
        "success": relation is not None,
        "relation_id": relation.id if relation else None,
    }


async def pm_traceability_analyze(input_data: PMTraceabilityAnalyzeInput, user_id: str, db=None) -> dict:
    """Analyze traceability for a project or specific entry."""
    from open_webui.models.pm import PMEntries, PMEntities, PMRelations
    
    entries = await PMEntries.get_entries_by_project_id(input_data.project_id, db=db)
    entities = await PMEntities.get_entities_by_project_id(input_data.project_id, db=db)
    relations = await PMRelations.get_relations_by_project_id(input_data.project_id, db=db)
    
    # Calculate coverage
    entries_with_entities = sum(1 for e in entries if any(ent.entry_id == e.id for ent in entities))
    
    return {
        "success": True,
        "total_entries": len(entries),
        "total_entities": len(entities),
        "total_relations": len(relations),
        "traceability_coverage": f"{entries_with_entities}/{len(entries)}" if entries else "0/0",
        "coverage_percentage": round(entries_with_entities / len(entries) * 100, 1) if entries else 0,
    }


async def pm_workflow_suggest(input_data: PMWorkflowSuggestInput, user_id: str, db=None) -> dict:
    """Suggest next steps in the workflow based on current state."""
    from open_webui.models.pm import PMEntries
    
    entries = await PMEntries.get_entries_by_project_id(input_data.project_id, db=db)
    
    # Analyze project state
    modules = {}
    for entry in entries:
        if entry.module_type not in modules:
            modules[entry.module_type] = {"total": 0, "draft": 0, "approved": 0}
        modules[entry.module_type]["total"] += 1
        if entry.status == "draft":
            modules[entry.module_type]["draft"] += 1
        elif entry.status == "approved":
            modules[entry.module_type]["approved"] += 1
    
    suggestions = []
    
    # Suggest based on module progression
    if "requirement" in modules and modules["requirement"]["approved"] > 0:
        if "testcase" not in modules or modules["testcase"]["total"] == 0:
            suggestions.append("需求已批准，建议创建测试用例")
    
    if "parameter" in modules and modules["parameter"]["total"] > 0:
        if "prd" not in modules or modules["prd"]["total"] == 0:
            suggestions.append("参数已配置，建议编写PRD文档")
    
    if not suggestions:
        suggestions.append("项目正在推进中，建议定期评审各模块状态")
    
    return {
        "success": True,
        "current_module": input_data.current_module,
        "current_status": input_data.current_status,
        "module_stats": modules,
        "suggestions": suggestions,
    }
