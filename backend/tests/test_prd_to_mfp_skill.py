"""
Unit tests for PRDToMFPSkill (D44: PRD → 模块-功能-参数 原子化转换).

Tests cover:
1. Hierarchy creation: modules → features → parameters with correct data shape
2. Rollback on failure (hard delete created entries)
3. Name-based linking: data.moduleName / data.featureName / data.parent_entry_id
4. Tool wrapper: pm_prd_to_mfp_transform registration & signature
"""

import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

import pytest

# Ensure backend is importable
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


# ============================================================================
# Mock helpers
# ============================================================================

class MockEntry:
    """Mock PMEntry returned by PMEntries.insert_new_entry."""
    def __init__(self, entry_id: str, title: str, module_type: str, data: dict = None):
        self.id = entry_id
        self.title = title
        self.module_type = module_type
        self.data = data or {}


def _make_structured_json() -> dict:
    """2 modules / 3 features / 5 parameters structured JSON for testing."""
    return {
        "modules": [
            {
                "name": "部门管理",
                "description": "管理部门层级与权限继承",
                "features": [
                    {
                        "name": "创建部门",
                        "description": "新建部门节点",
                        "parameters": [
                            {
                                "key": "deptName",
                                "paramType": "输入参数",
                                "dataType": "string",
                                "required": "是",
                                "defaultValue": "",
                                "description": "部门名称",
                            },
                            {
                                "key": "parentDeptId",
                                "paramType": "输入参数",
                                "dataType": "string",
                                "required": "否",
                                "defaultValue": "",
                                "description": "父部门 ID",
                            },
                        ],
                    },
                    {
                        "name": "删除部门",
                        "description": "删除部门节点",
                        "parameters": [
                            {
                                "key": "cascadeDelete",
                                "paramType": "配置参数",
                                "dataType": "boolean",
                                "required": "否",
                                "defaultValue": "false",
                                "description": "是否级联删除子部门",
                            },
                        ],
                    },
                ],
            },
            {
                "name": "角色管理",
                "description": "管理角色与权限绑定",
                "features": [
                    {
                        "name": "创建角色",
                        "description": "新建角色",
                        "parameters": [
                            {
                                "key": "roleName",
                                "paramType": "输入参数",
                                "dataType": "string",
                                "required": "是",
                                "defaultValue": "",
                                "description": "角色名称",
                            },
                            {
                                "key": "roleCode",
                                "paramType": "输入参数",
                                "dataType": "string",
                                "required": "是",
                                "defaultValue": "",
                                "description": "角色编码",
                            },
                        ],
                    },
                ],
            },
        ],
    }


def run_async(coro):
    """Run an async coroutine synchronously (avoids pytest-asyncio dependency)."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ============================================================================
# Tests
# ============================================================================


class TestPRDToMFPSkill:
    """Tests for PRDToMFPSkill class."""

    def test_skill_transform_creates_hierarchy(self):
        """Test 1: skill creates 2 modules / 3 features / 5 parameters with correct data shape."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        structured = _make_structured_json()
        skill = PRDToMFPSkill()

        # Mock the entry creator to return mock entries with incremental IDs
        created_entries = []

        async def mock_insert(user_id, form):
            entry_id = f"entry-{len(created_entries) + 1}"
            entry = MockEntry(entry_id, form.title, form.module_type, form.data)
            created_entries.append(entry)
            return entry

        # Run _create_hierarchy_atomically directly (skip LLM)
        async def _run():
            with patch(
                "open_webui.models.pm.PMEntries.insert_new_entry",
                new=AsyncMock(side_effect=mock_insert),
            ):
                return await skill._create_hierarchy_atomically(
                    structured=structured,
                    pid="test-project-id",
                    user_obj=MagicMock(id="user-1"),
                    created_ids=[],
                )

        result = run_async(_run())

        # Assertions on summary
        assert result["success"] is True
        assert result["created_modules"] == 2
        assert result["created_functions"] == 3
        assert result["created_parameters"] == 5
        assert result["total"] == 10
        assert result["rolled_back"] is False
        assert result["error"] is None

        # by_module structure
        assert "部门管理" in result["by_module"]
        assert "角色管理" in result["by_module"]
        assert result["by_module"]["部门管理"]["functions"] == 2
        assert result["by_module"]["部门管理"]["parameters"] == 3
        assert result["by_module"]["角色管理"]["functions"] == 1
        assert result["by_module"]["角色管理"]["parameters"] == 2

        # Verify entry data shapes
        modules = [e for e in created_entries if e.module_type == "product-architecture" and e.data.get("node_type") == "module"]
        features = [e for e in created_entries if e.module_type == "product-architecture" and e.data.get("node_type") == "function"]
        params = [e for e in created_entries if e.module_type == "parameter"]

        assert len(modules) == 2
        assert len(features) == 3
        assert len(params) == 5

        # Module entry: data.node_type == "module"
        for m in modules:
            assert m.data["node_type"] == "module"
            assert "description" in m.data

        # Feature entry: data.node_type == "function" + parent_entry_id + moduleName
        for f in features:
            assert f.data["node_type"] == "function"
            assert "parent_entry_id" in f.data
            assert "moduleName" in f.data
            # parent_entry_id must point to one of the modules
            module_ids = [m.id for m in modules]
            assert f.data["parent_entry_id"] in module_ids

        # Parameter entry: parent_entry_id + moduleName + featureName + key
        for p in params:
            assert "key" in p.data
            assert "paramType" in p.data
            assert "dataType" in p.data
            assert "required" in p.data
            assert "defaultValue" in p.data
            assert "description" in p.data
            assert "parent_entry_id" in p.data
            assert "moduleName" in p.data
            assert "featureName" in p.data
            # parent_entry_id must point to one of the features
            feature_ids = [f.id for f in features]
            assert p.data["parent_entry_id"] in feature_ids

    def test_skill_transform_writes_name_based_linking(self):
        """Test 3: parameter entries have data.moduleName + data.featureName + data.parent_entry_id."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        structured = _make_structured_json()
        skill = PRDToMFPSkill()

        created_entries = []

        async def mock_insert(user_id, form):
            entry_id = f"entry-{len(created_entries) + 1}"
            entry = MockEntry(entry_id, form.title, form.module_type, form.data)
            created_entries.append(entry)
            return entry

        async def _run():
            with patch(
                "open_webui.models.pm.PMEntries.insert_new_entry",
                new=AsyncMock(side_effect=mock_insert),
            ):
                return await skill._create_hierarchy_atomically(
                    structured=structured,
                    pid="test-project-id",
                    user_obj=MagicMock(id="user-1"),
                    created_ids=[],
                )

        run_async(_run())

        params = [e for e in created_entries if e.module_type == "parameter"]
        assert len(params) == 5

        # All parameters must have name-based linking fields
        for p in params:
            assert p.data.get("moduleName") in ("部门管理", "角色管理"), \
                f"Parameter {p.title} has invalid moduleName: {p.data.get('moduleName')}"
            assert p.data.get("featureName") in (
                "创建部门", "删除部门", "创建角色"
            ), f"Parameter {p.title} has invalid featureName: {p.data.get('featureName')}"
            assert p.data.get("parent_entry_id"), \
                f"Parameter {p.title} missing parent_entry_id"

        # Specifically verify cross-module consistency:
        # 部门管理 params must have moduleName="部门管理"
        dept_params = [p for p in params if p.data["moduleName"] == "部门管理"]
        assert len(dept_params) == 3
        role_params = [p for p in params if p.data["moduleName"] == "角色管理"]
        assert len(role_params) == 2

        # Verify featureName consistency per module
        dept_feature_names = {p.data["featureName"] for p in dept_params}
        assert dept_feature_names == {"创建部门", "删除部门"}
        role_feature_names = {p.data["featureName"] for p in role_params}
        assert role_feature_names == {"创建角色"}

    def test_skill_transform_rolls_back_on_failure(self):
        """Test 2: skill rolls back (hard delete) on step 3 failure."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        structured = _make_structured_json()
        skill = PRDToMFPSkill()

        call_count = {"insert": 0}
        rollback_calls = []

        # Mock PMEntries.get_entry_by_id to return a fake PRD
        async def mock_get_by_id(entry_id):
            return MockEntry(entry_id, "测试 PRD", "prd", {})

        # Mock _verify_project_access to return True
        async def mock_verify(pid, user):
            return True

        async def mock_insert_v2(user_id, form):
            call_count["insert"] += 1
            # Let modules (2) + features (3) succeed (5 entries), then fail on parameter
            if call_count["insert"] > 5:
                return None
            entry_id = f"entry-{call_count['insert']}"
            return MockEntry(entry_id, form.title, form.module_type, form.data)

        async def _run():
            with patch(
                "open_webui.models.pm.PMEntries.insert_new_entry",
                new=AsyncMock(side_effect=mock_insert_v2),
            ), patch(
                "open_webui.models.pm.PMEntries.delete_entry_by_id",
                new=AsyncMock(side_effect=lambda eid: rollback_calls.append(eid)),
            ), patch(
                "open_webui.models.pm.PMEntries.get_entry_by_id",
                new=AsyncMock(side_effect=mock_get_by_id),
            ), patch(
                "open_webui.pm.chat_context._verify_project_access",
                new=AsyncMock(side_effect=mock_verify),
            ):
                # Mock LLM extraction to skip actual LLM call
                with patch.object(
                    PRDToMFPSkill,
                    "_extract_structure_with_llm",
                    new=AsyncMock(return_value=structured),
                ):
                    return await skill.transform(
                        prd_entry_id="prd-1",
                        user=MagicMock(id="user-1"),
                        metadata={"pm_project_id": "test-project-id"},
                        request=MagicMock(),
                    )

        result = run_async(_run())

        # Assertions
        assert result["success"] is False
        assert result["rolled_back"] is True
        assert "创建失败已回滚" in result["error"]
        assert result["created_modules"] == 0
        assert result["created_functions"] == 0
        assert result["created_parameters"] == 0

        # Verify rollback was called for 5 successful inserts (2 modules + 3 features)
        assert len(rollback_calls) == 5, f"Expected 5 rollback calls, got {len(rollback_calls)}"

    def test_skill_parse_llm_json_tolerates_codeblock(self):
        """Test: _parse_llm_json handles ```json``` wrapped responses."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        skill = PRDToMFPSkill()
        structured = _make_structured_json()

        # Plain JSON
        parsed = skill._parse_llm_json(json.dumps(structured))
        assert parsed["modules"][0]["name"] == "部门管理"

        # ```json``` wrapped
        wrapped = f"```json\n{json.dumps(structured, ensure_ascii=False)}\n```"
        parsed = skill._parse_llm_json(wrapped)
        assert parsed["modules"][0]["name"] == "部门管理"

        # Plain text prefix + JSON
        prefixed = f"好的，这是结果：\n{json.dumps(structured, ensure_ascii=False)}"
        parsed = skill._parse_llm_json(prefixed)
        assert parsed["modules"][0]["name"] == "部门管理"

    def test_skill_fail_methods(self):
        """Test: _fail() returns standardized failure response."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        skill = PRDToMFPSkill()
        result = skill._fail("test error", rolled_back=True)

        assert result["success"] is False
        assert result["error"] == "test error"
        assert result["rolled_back"] is True
        assert result["created_modules"] == 0
        assert result["created_functions"] == 0
        assert result["created_parameters"] == 0
        assert result["total"] == 0
        assert result["by_module"] == {}


class TestPRDToMFPValidateStructure:
    """Tests for PRDToMFPSkill._validate_structure (D44-fix)."""

    def test_validate_structure_rejects_empty_modules(self):
        """D44-fix: empty modules array must be rejected."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        skill = PRDToMFPSkill()
        # Case 1: modules is missing
        ok, reason = skill._validate_structure({})
        assert ok is False
        assert "modules" in reason

        # Case 2: modules is empty list
        ok, reason = skill._validate_structure({"modules": []})
        assert ok is False
        assert "modules" in reason

        # Case 3: modules is not a list
        ok, reason = skill._validate_structure({"modules": "not a list"})
        assert ok is False

    def test_validate_structure_rejects_uncategorized_module(self):
        """D44-fix: module named '未分类模块' or 'Uncategorized' must be rejected."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        skill = PRDToMFPSkill()
        structured = {
            "modules": [
                {
                    "name": "未分类模块",
                    "features": [{"name": "f1", "parameters": []}],
                }
            ]
        }
        ok, reason = skill._validate_structure(structured)
        assert ok is False
        assert "未分类模块" in reason or "兜底" in reason

        # Also rejects English variant
        structured["modules"][0]["name"] = "Uncategorized"
        ok, reason = skill._validate_structure(structured)
        assert ok is False

    def test_validate_structure_rejects_module_without_features(self):
        """D44-fix: module without features array must be rejected."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        skill = PRDToMFPSkill()
        # Case 1: features missing
        structured = {"modules": [{"name": "部门管理"}]}
        ok, reason = skill._validate_structure(structured)
        assert ok is False
        assert "features" in reason

        # Case 2: features is empty list
        structured["modules"][0]["features"] = []
        ok, reason = skill._validate_structure(structured)
        assert ok is False
        assert "features" in reason

    def test_validate_structure_rejects_module_with_direct_parameters(self):
        """D44-fix: module must not directly carry parameters (must be in feature)."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        skill = PRDToMFPSkill()
        structured = {
            "modules": [
                {
                    "name": "部门管理",
                    "features": [{"name": "创建部门", "parameters": []}],
                    # Sneak parameters at module level (should be rejected)
                    "parameters": [{"key": "forbiddenParam"}],
                }
            ]
        }
        ok, reason = skill._validate_structure(structured)
        assert ok is False
        assert "parameters" in reason or "feature" in reason

    def test_validate_structure_accepts_valid_structure(self):
        """D44-fix: well-formed structure from _make_structured_json must pass."""
        from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill

        skill = PRDToMFPSkill()
        structured = _make_structured_json()
        ok, reason = skill._validate_structure(structured)
        assert ok is True, f"Valid structure rejected: {reason}"
        assert reason == ""


class TestPmPrdToMfpTransformTool:
    """Tests for the pm_prd_to_mfp_transform tool wrapper."""

    def test_tool_registered_in_pm_functions(self):
        """Test 4a: pm_prd_to_mfp_transform is in pm_functions list (registered as builtin)."""
        # Read the source code to verify registration (avoid importing heavy modules)
        import os
        tools_path = os.path.join(
            backend_dir, "open_webui", "utils", "tools.py"
        )
        with open(tools_path, "r", encoding="utf-8") as f:
            source = f.read()

        assert "async def pm_prd_to_mfp_transform(" in source, \
            "pm_prd_to_mfp_transform tool not defined"
        assert "pm_prd_to_mfp_transform," in source, \
            "pm_prd_to_mfp_transform not added to pm_functions list"

    def test_tool_signature(self):
        """Test 4b: pm_prd_to_mfp_transform tool has correct signature."""
        import re
        import os

        tools_path = os.path.join(
            backend_dir, "open_webui", "utils", "tools.py"
        )
        with open(tools_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Match the async def signature
        match = re.search(
            r"async def pm_prd_to_mfp_transform\(([^)]+)\)",
            source,
            re.DOTALL,
        )
        assert match is not None, "pm_prd_to_mfp_transform signature not found"
        sig = match.group(1)

        # Required parameters
        assert "prd_entry_id: str" in sig, "Missing prd_entry_id: str parameter"
        assert "__metadata__" in sig, "Missing __metadata__ parameter"
        assert "__user__" in sig, "Missing __user__ parameter"
        assert "__request__" in sig, "Missing __request__ parameter (needed for LLM call)"

    def test_chat_context_lists_tool(self):
        """Test 4c: chat_context.py lists pm_prd_to_mfp_transform in tool table."""
        import os
        ctx_path = os.path.join(
            backend_dir, "open_webui", "pm", "chat_context.py"
        )
        with open(ctx_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Tool should be listed in the table
        assert "pm_prd_to_mfp_transform" in content, \
            "pm_prd_to_mfp_transform not listed in chat_context.py"
        # Tool count should be 10
        assert "共 10 个" in content, "Tool count not updated to 10"
        # Old lying instruction should be removed
        assert "parent_id 指向模块" not in content, \
            "Old lying 7-step instruction still present"

    def test_registry_registers_skill(self):
        """Test 4d: PRDToMFPSkill is registered in registry.py."""
        import os
        registry_path = os.path.join(
            backend_dir, "open_webui", "pm", "skills", "registry.py"
        )
        with open(registry_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "from open_webui.pm.skills.prd_to_mfp import PRDToMFPSkill" in content
        assert "PRDToMFPSkill.id: PRDToMFPSkill" in content
