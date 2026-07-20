"""Output validation service for pm-skills."""

import json
from typing import Any, Optional

from pydantic import BaseModel, ValidationError


class OutputValidationError(Exception):
    """Raised when output validation fails."""

    pass


class OutputValidator:
    """Validate pm-skills output against outputContract."""

    def __init__(self, contract: Optional[dict] = None):
        self.contract = contract or {}

    def validate(self, output: dict[str, Any]) -> bool:
        """Validate output against contract.

        Args:
            output: Skill output to validate

        Returns:
            True if valid

        Raises:
            OutputValidationError: If validation fails
        """
        if not self.contract:
            return True

        # Check required fields
        required = self.contract.get("required", [])
        for field in required:
            if field not in output:
                raise OutputValidationError(f"Missing required field: {field}")

        # Check field types
        properties = self.contract.get("properties", {})
        for field, schema in properties.items():
            if field in output:
                expected_type = schema.get("type")
                if expected_type and not self._check_type(output[field], expected_type):
                    raise OutputValidationError(
                        f"Field {field} expected type {expected_type}, got {type(output[field])}"
                    )

        return True

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type not in type_map:
            return True

        expected = type_map[expected_type]
        return isinstance(value, expected)


def validate_output(output: dict[str, Any], contract: Optional[dict] = None) -> bool:
    """Validate output against contract.

    Args:
        output: Skill output to validate
        contract: Output contract schema

    Returns:
        True if valid

    Raises:
        OutputValidationError: If validation fails
    """
    validator = OutputValidator(contract)
    return validator.validate(output)
