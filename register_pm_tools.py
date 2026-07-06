"""
PM Tool 注册脚本
用于将 PM Tool 注册到 Open WebUI 的 Tool 系统

Usage:
    python register_pm_tools.py [--api-key KEY] [--base-url URL]
"""

import argparse
import json
import time
import uuid


# Tool definitions
PM_TOOLS = [
    {
        "id": "pm_project_tool",
        "name": "PM 项目管理",
        "description": "PM 项目的 CRUD 操作：创建、查询、更新、删除、归档项目",
        "file": "pm_project_tool.py",
        "functions": ["list_projects", "create_project", "get_project", "update_project", "delete_project", "archive_project"],
    },
    {
        "id": "pm_entry_tool",
        "name": "PM 条目管理",
        "description": "PM 条目的 CRUD 操作：创建、查询、更新、删除、搜索条目，支持多维度筛选",
        "file": "pm_entry_tool.py",
        "functions": ["list_entries", "create_entry", "get_entry", "update_entry", "delete_entry", "search_entries", "get_entry_versions", "create_entry_version"],
    },
    {
        "id": "pm_version_tool",
        "name": "PM 版本管理",
        "description": "PM 版本管理：创建版本、切换版本、对比版本差异",
        "file": "pm_version_tool.py",
        "functions": ["list_versions", "create_version", "get_version", "switch_version", "compare_versions"],
    },
    {
        "id": "pm_relation_tool",
        "name": "PM 关系管理",
        "description": "PM 条目关系管理：创建关系、影响分析、追溯链查询",
        "file": "pm_relation_tool.py",
        "functions": ["list_relations", "create_relation", "delete_relation", "get_impact_analysis", "get_trace_chain"],
    },
    {
        "id": "pm_workflow_tool",
        "name": "PM 工作流",
        "description": "PM 工作流管理：获取下一步建议、进度统计、执行工作流",
        "file": "pm_workflow_tool.py",
        "functions": ["get_next_steps", "get_progress", "execute_workflow"],
    },
    {
        "id": "pm_import_export_tool",
        "name": "PM 导入导出",
        "description": "PM 数据导入导出：批量导入条目、导出条目、参数提取、内容生成",
        "file": "pm_import_export_tool.py",
        "functions": ["import_entries", "export_entry", "extract_parameters", "generate_content"],
    },
    {
        "id": "pm_ai_tool",
        "name": "PM AI 助手",
        "description": "PM AI 功能：需求分析、测试用例生成、质量检查、关系建议、PRD 生成",
        "file": "pm_ai_tool.py",
        "functions": ["analyze_entry", "generate_testcases", "check_entry", "suggest_relations", "generate_prd"],
    },
    {
        "id": "pm_flow_tool",
        "name": "PM 跨模块流转",
        "description": "PM 跨模块流转：预览流转、执行流转、管理流转模板",
        "file": "pm_flow_tool.py",
        "functions": ["list_templates", "preview_flow", "execute_flow", "create_template"],
    },
    {
        "id": "pm_roadmap_tool",
        "name": "PM 路线图",
        "description": "PM 路线图管理：节点 CRUD、AI 排期建议、冲突检测",
        "file": "pm_roadmap_tool.py",
        "functions": ["list_roadmap_nodes", "create_roadmap_node", "update_roadmap_node", "suggest_schedule", "detect_conflicts"],
    },
    {
        "id": "pm_check_tool",
        "name": "PM 质量检查",
        "description": "PM 质量检查：4 级检查、规则管理、修复建议",
        "file": "pm_check_tool.py",
        "functions": ["run_check", "list_results", "update_status", "suggest_fix", "list_rules"],
    },
]


FUNCTION_SPECS = {
    # pm_project_tool
    "list_projects": {
        "description": "列出当前用户的所有 PM 项目",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "create_project": {
        "description": "创建新的 PM 项目",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "项目名称"},
                "description": {"type": "string", "description": "项目描述"},
            },
            "required": ["name"],
        },
    },
    "get_project": {
        "description": "获取指定项目的详细信息",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    "update_project": {
        "description": "更新项目信息",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "name": {"type": "string", "description": "新项目名称"},
                "description": {"type": "string", "description": "新项目描述"},
                "status": {"type": "string", "description": "新项目状态 (active/archived)", "enum": ["active", "archived"]},
            },
            "required": ["project_id"],
        },
    },
    "delete_project": {
        "description": "删除 PM 项目（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "要删除的项目 ID"}},
            "required": ["project_id"],
        },
    },
    "archive_project": {
        "description": "归档 PM 项目（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "要归档的项目 ID"}},
            "required": ["project_id"],
        },
    },
    # pm_entry_tool
    "list_entries": {
        "description": "列出指定项目下的条目列表，支持多种过滤条件",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "module_type": {"type": "string", "description": "模块类型过滤"},
                "status": {"type": "string", "description": "状态过滤"},
                "priority": {"type": "string", "description": "优先级过滤"},
                "search": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["project_id"],
        },
    },
    "create_entry": {
        "description": "在指定项目下创建新条目（需确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "module_type": {"type": "string", "description": "模块类型 (requirement/prd/spec/testcase/parameter)"},
                "title": {"type": "string", "description": "条目标题"},
                "content": {"type": "string", "description": "条目内容"},
                "status": {"type": "string", "description": "条目状态 (默认 draft)"},
                "priority": {"type": "string", "description": "优先级 (P0-P3)"},
            },
            "required": ["project_id", "module_type", "title"],
        },
    },
    "get_entry": {
        "description": "获取指定条目的详细信息",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "update_entry": {
        "description": "更新指定条目的信息（需确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "条目 ID"},
                "title": {"type": "string", "description": "新标题"},
                "content": {"type": "string", "description": "新内容"},
                "status": {"type": "string", "description": "新状态"},
                "priority": {"type": "string", "description": "新优先级"},
            },
            "required": ["entry_id"],
        },
    },
    "delete_entry": {
        "description": "删除指定条目（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "要删除的条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "search_entries": {
        "description": "在指定项目下全文搜索条目",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "q": {"type": "string", "description": "搜索关键词"},
                "module_type": {"type": "string", "description": "模块类型过滤"},
                "status": {"type": "string", "description": "状态过滤"},
                "priority": {"type": "string", "description": "优先级过滤"},
                "limit": {"type": "integer", "description": "返回结果数量限制 (默认 50)"},
            },
            "required": ["project_id", "q"],
        },
    },
    "get_entry_versions": {
        "description": "获取指定条目的版本历史",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "create_entry_version": {
        "description": "为指定条目创建新版本",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "条目 ID"},
                "version_number": {"type": "string", "description": "版本号"},
                "change_summary": {"type": "string", "description": "变更摘要"},
            },
            "required": ["entry_id"],
        },
    },
    # pm_version_tool
    "list_versions": {
        "description": "列出指定项目的所有版本",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    "create_version": {
        "description": "创建新的版本",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "version_number": {"type": "string", "description": "版本号"},
                "label": {"type": "string", "description": "版本标签"},
                "description": {"type": "string", "description": "版本描述"},
            },
            "required": ["project_id", "version_number"],
        },
    },
    "get_version": {
        "description": "获取指定版本的详细信息",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "entry_id": {"type": "string", "description": "条目 ID"},
                "version_id": {"type": "string", "description": "版本 ID"},
            },
            "required": ["project_id", "entry_id", "version_id"],
        },
    },
    "switch_version": {
        "description": "切换条目到指定版本",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "entry_id": {"type": "string", "description": "条目 ID"},
                "version_id": {"type": "string", "description": "目标版本 ID"},
            },
            "required": ["project_id", "entry_id", "version_id"],
        },
    },
    "compare_versions": {
        "description": "比较两个版本的差异",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "entry_id": {"type": "string", "description": "条目 ID"},
                "version_a": {"type": "string", "description": "版本 A ID"},
                "version_b": {"type": "string", "description": "版本 B ID"},
            },
            "required": ["project_id", "entry_id", "version_a", "version_b"],
        },
    },
    # pm_relation_tool
    "list_relations": {
        "description": "列出指定项目中的所有关系",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    "create_relation": {
        "description": "在项目中创建两个实体之间的关系",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "entity_a_id": {"type": "string", "description": "实体 A ID"},
                "entity_b_id": {"type": "string", "description": "实体 B ID"},
                "relation_type": {"type": "string", "description": "关系类型"},
                "confidence": {"type": "integer", "description": "置信度 (0-100, 默认 100)"},
            },
            "required": ["project_id", "entity_a_id", "entity_b_id", "relation_type"],
        },
    },
    "delete_relation": {
        "description": "删除关系（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {"relation_id": {"type": "string", "description": "要删除的关系 ID"}},
            "required": ["relation_id"],
        },
    },
    "get_impact_analysis": {
        "description": "获取指定实体的影响分析结果",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "entity_id": {"type": "string", "description": "实体 ID"},
            },
            "required": ["project_id", "entity_id"],
        },
    },
    "get_trace_chain": {
        "description": "获取指定实体的追溯链",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "entity_id": {"type": "string", "description": "实体 ID"},
                "direction": {"type": "string", "description": "追溯方向 (both/forward/backward)", "enum": ["both", "forward", "backward"]},
                "max_depth": {"type": "integer", "description": "最大深度 (默认 5)"},
            },
            "required": ["project_id", "entity_id"],
        },
    },
    # pm_workflow_tool
    "get_next_steps": {
        "description": "获取项目建议的下一步工作流步骤",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    "get_progress": {
        "description": "获取项目进度统计信息",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    "execute_workflow": {
        "description": "执行工作流（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "工作流 ID"},
                "steps": {"type": "string", "description": "工作流步骤列表 JSON 字符串"},
            },
            "required": ["workflow_id", "steps"],
        },
    },
    # pm_import_export_tool
    "import_entries": {
        "description": "导入条目数据到指定项目（预览后确认导入）",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "module_type": {"type": "string", "description": "模块类型"},
                "format": {"type": "string", "description": "导入格式 (json/csv)", "enum": ["json", "csv"]},
                "data": {"type": "string", "description": "要导入的数据内容"},
            },
            "required": ["project_id", "module_type", "format", "data"],
        },
    },
    "export_entry": {
        "description": "导出指定条目数据",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "条目 ID"},
                "format": {"type": "string", "description": "导出格式 (json/markdown/csv)", "enum": ["json", "markdown", "csv"]},
            },
            "required": ["entry_id"],
        },
    },
    "extract_parameters": {
        "description": "从条目中提取参数",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "generate_content": {
        "description": "使用 AI 生成内容（预览后确认写入）",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "条目 ID"},
                "module_type": {"type": "string", "description": "模块类型"},
                "instructions": {"type": "string", "description": "生成指令"},
            },
            "required": ["entry_id", "module_type"],
        },
    },
    # pm_ai_tool
    "analyze_entry": {
        "description": "分析需求条目（分类、优先级、冲突检测）",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "generate_testcases": {
        "description": "从需求条目生成测试用例（预览后确认写入）",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "check_entry": {
        "description": "质量检查需求条目（完整性、一致性、可测试性）",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "suggest_relations": {
        "description": "为条目建议关联关系",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "entry_id": {"type": "string", "description": "条目 ID"},
            },
            "required": ["project_id", "entry_id"],
        },
    },
    "generate_prd": {
        "description": "生成 PRD 文档（预览后确认写入）",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "条目 ID"},
                "instructions": {"type": "string", "description": "生成指令"},
            },
            "required": ["entry_id"],
        },
    },
    "extract_parameters_ai": {
        "description": "从条目中提取结构化参数（参数名、类型、默认值、描述）",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    # pm_flow_tool
    "list_templates": {
        "description": "列出可用的流转模板",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": [],
        },
    },
    "preview_flow": {
        "description": "预览流转结果（不写入）",
        "parameters": {
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "流转模板 ID"},
                "source_entry_ids": {"type": "string", "description": "源条目 ID 列表，逗号分隔"},
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["template_id", "source_entry_ids", "project_id"],
        },
    },
    "execute_flow": {
        "description": "执行流转模板（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "流转模板 ID"},
                "source_entry_ids": {"type": "string", "description": "源条目 ID 列表，逗号分隔"},
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["template_id", "source_entry_ids", "project_id"],
        },
    },
    "create_template": {
        "description": "创建自定义流转模板（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "模板名称"},
                "description": {"type": "string", "description": "模板描述"},
                "input_module": {"type": "string", "description": "输入模块类型"},
                "output_module": {"type": "string", "description": "输出模块类型"},
                "steps": {"type": "string", "description": "流转步骤列表 JSON 字符串"},
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["name", "description", "input_module", "output_module", "steps"],
        },
    },
    # pm_roadmap_tool
    "list_roadmap_nodes": {
        "description": "列出项目中的所有路线图节点",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    "create_roadmap_node": {
        "description": "创建路线图节点（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
                "title": {"type": "string", "description": "节点名称"},
                "node_type": {"type": "string", "description": "节点类型 (milestone/feature/release)", "enum": ["milestone", "feature", "release"]},
                "start_date": {"type": "string", "description": "开始日期 (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "结束日期 (YYYY-MM-DD)"},
                "dependencies": {"type": "string", "description": "依赖节点 ID 列表 JSON"},
            },
            "required": ["project_id", "title"],
        },
    },
    "update_roadmap_node": {
        "description": "更新路线图节点（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "节点条目 ID"},
                "title": {"type": "string", "description": "新名称"},
                "start_date": {"type": "string", "description": "新开始日期"},
                "end_date": {"type": "string", "description": "新结束日期"},
                "status": {"type": "string", "description": "新状态"},
            },
            "required": ["entry_id"],
        },
    },
    "suggest_schedule": {
        "description": "AI 排期建议 - 分析项目需求列表和优先级，自动建议排期",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    "detect_conflicts": {
        "description": "检测路线图中的依赖冲突",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "项目 ID"}},
            "required": ["project_id"],
        },
    },
    # pm_check_tool
    "run_check": {
        "description": "执行指定级别的质量检查",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "要检查的条目 ID"},
                "levels": {"type": "string", "description": "检查级别，逗号分隔 (L1,L2,L3,L4)"},
            },
            "required": ["entry_id"],
        },
    },
    "list_results": {
        "description": "列出指定条目的历史检查结果",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string", "description": "条目 ID"}},
            "required": ["entry_id"],
        },
    },
    "update_status": {
        "description": "更新检查项状态（需要确认）",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "条目 ID"},
                "rule_id": {"type": "string", "description": "规则 ID"},
                "status": {"type": "string", "description": "新状态 (pass/fail/ignored)", "enum": ["pass", "fail", "ignored"]},
            },
            "required": ["entry_id", "rule_id", "status"],
        },
    },
    "suggest_fix": {
        "description": "AI 生成修复建议",
        "parameters": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "条目 ID"},
                "rule_id": {"type": "string", "description": "失败的规则 ID"},
            },
            "required": ["entry_id", "rule_id"],
        },
    },
    "list_rules": {
        "description": "查看规则库",
        "parameters": {
            "type": "object",
            "properties": {"level": {"type": "string", "description": "过滤级别 (L1/L2/L3/L4)"}},
            "required": [],
        },
    },
}


def generate_specs(tool_id: str, functions: list) -> list:
    """Generate OpenAPI-style specs for a tool using FUNCTION_SPECS lookup"""
    specs = []
    for func_name in functions:
        spec_data = FUNCTION_SPECS.get(func_name)
        if spec_data:
            specs.append({
                "name": func_name,
                "description": spec_data["description"],
                "parameters": spec_data["parameters"],
            })
        else:
            specs.append({
                "name": func_name,
                "description": f"{tool_id} tool function: {func_name}",
                "parameters": {"type": "object", "properties": {}, "required": []},
            })
    return specs


def register_tool(api_base_url: str, api_key: str, tool: dict, tool_content: str):
    """Register a single tool via Open WebUI API"""
    import requests
    
    url = f"{api_base_url}/api/v1/tools/create"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    specs = generate_specs(tool["id"], tool["functions"])
    
    payload = {
        "id": tool["id"],
        "name": tool["name"],
        "content": tool_content,
        "specs": specs,
        "meta": {
            "description": tool["description"],
            "manifest": {
                "id": tool["id"],
                "name": tool["name"],
                "description": tool["description"],
                "version": "1.0.0",
                "author": "PM Workflow Platform",
            }
        },
        "valves": {
            "pm_api_base_url": "http://localhost:8080/api/v1",
            "pm_api_key": ""
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error registering {tool['id']}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Register PM Tools to Open WebUI")
    parser.add_argument("--api-key", default="", help="Open WebUI API Key")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Open WebUI Base URL")
    parser.add_argument("--tools-dir", default="./backend/open_webui/tools", help="Tools directory")
    args = parser.parse_args()
    
    print("=" * 60)
    print("PM Tool Registration")
    print("=" * 60)
    
    for tool in PM_TOOLS:
        print(f"\nRegistering: {tool['id']} ({tool['name']})")
        
        # Read tool content
        tool_path = f"{args.tools_dir}/{tool['file']}"
        try:
            with open(tool_path, "r", encoding="utf-8") as f:
                tool_content = f.read()
        except FileNotFoundError:
            print(f"  ERROR: File not found: {tool_path}")
            continue
        
        # Register tool
        result = register_tool(args.base_url, args.api_key, tool, tool_content)
        if result:
            print(f"  SUCCESS: {tool['id']} registered")
        else:
            print(f"  FAILED: {tool['id']}")
    
    print("\n" + "=" * 60)
    print("Registration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
