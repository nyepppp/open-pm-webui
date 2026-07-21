"""
Tests for feature_flags module (#31/#35).
"""

import os
import importlib.util
import sys
import types

import pytest


# Stub open_webui 包避免触发完整依赖链
if "open_webui" not in sys.modules:
    sys.modules["open_webui"] = types.ModuleType("open_webui")
if "open_webui.utils" not in sys.modules:
    sys.modules["open_webui.utils"] = types.ModuleType("open_webui.utils")

# 直接加载模块文件
_module_path = os.path.join(
    os.path.dirname(__file__), "..", "open_webui", "utils", "feature_flags.py"
)
_spec = importlib.util.spec_from_file_location("feature_flags_under_test", _module_path)
feature_flags = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(feature_flags)


class TestWorkflowSandboxFlag:
    """#31: WORKFLOW_SANDBOX_ENABLED flag."""

    def test_default_false(self, monkeypatch):
        monkeypatch.delenv("WORKFLOW_SANDBOX_ENABLED", raising=False)
        assert feature_flags.is_workflow_sandbox_enabled() is False

    def test_true_lowercase(self, monkeypatch):
        monkeypatch.setenv("WORKFLOW_SANDBOX_ENABLED", "true")
        assert feature_flags.is_workflow_sandbox_enabled() is True

    def test_true_uppercase(self, monkeypatch):
        monkeypatch.setenv("WORKFLOW_SANDBOX_ENABLED", "TRUE")
        assert feature_flags.is_workflow_sandbox_enabled() is True

    def test_false_explicit(self, monkeypatch):
        monkeypatch.setenv("WORKFLOW_SANDBOX_ENABLED", "false")
        assert feature_flags.is_workflow_sandbox_enabled() is False

    def test_garbage_value_treated_as_false(self, monkeypatch):
        monkeypatch.setenv("WORKFLOW_SANDBOX_ENABLED", "yes")
        assert feature_flags.is_workflow_sandbox_enabled() is False


class TestExtensionCredentialIsolationFlag:
    """#35: EXTENSION_CREDENTIAL_ISOLATION flag."""

    def test_default_false(self, monkeypatch):
        monkeypatch.delenv("EXTENSION_CREDENTIAL_ISOLATION", raising=False)
        assert feature_flags.is_extension_credential_isolation_enabled() is False

    def test_true_lowercase(self, monkeypatch):
        monkeypatch.setenv("EXTENSION_CREDENTIAL_ISOLATION", "true")
        assert feature_flags.is_extension_credential_isolation_enabled() is True

    def test_true_mixed_case(self, monkeypatch):
        monkeypatch.setenv("EXTENSION_CREDENTIAL_ISOLATION", "True")
        assert feature_flags.is_extension_credential_isolation_enabled() is True

    def test_false_explicit(self, monkeypatch):
        monkeypatch.setenv("EXTENSION_CREDENTIAL_ISOLATION", "false")
        assert feature_flags.is_extension_credential_isolation_enabled() is False
