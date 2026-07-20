"""Timbal configuration for PM Skills integration.

Timbal is embedded as a Python library (NOT as independent service).
Usage: from timbal import Workflow
       from timbal.state import get_run_context

PROHIBITED: timbal start (violates Constitution Principle VI)
"""

import os
from typing import Optional

# Timbal configuration
TIMBAL_CONFIG = {
    # Model settings for Timbal workflow steps
    "model": {
        "provider": os.getenv("TIMBAL_MODEL_PROVIDER", "openai"),
        "model": os.getenv("TIMBAL_MODEL_NAME", "gpt-4"),
        "temperature": float(os.getenv("TIMBAL_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("TIMBAL_MAX_TOKENS", "4096")),
    },
    # Workflow execution settings
    "workflow": {
        "timeout": int(os.getenv("TIMBAL_WORKFLOW_TIMEOUT", "300")),  # seconds
        "max_retries": int(os.getenv("TIMBAL_MAX_RETRIES", "3")),
        "retry_delay": float(os.getenv("TIMBAL_RETRY_DELAY", "1.0")),  # seconds
    },
    # Logging
    "logging": {
        "level": os.getenv("TIMBAL_LOG_LEVEL", "INFO"),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}


def get_timbal_config() -> dict:
    """Get Timbal configuration."""
    return TIMBAL_CONFIG.copy()


def get_model_config() -> dict:
    """Get model configuration for Timbal workflow steps."""
    return TIMBAL_CONFIG["model"].copy()


def get_workflow_config() -> dict:
    """Get workflow execution configuration."""
    return TIMBAL_CONFIG["workflow"].copy()
