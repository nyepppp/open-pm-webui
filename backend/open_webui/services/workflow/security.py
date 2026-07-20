"""
Workflow Security and Input Validation

Provides security hardening for workflow endpoints including input validation,
rate limiting, and security checks.
"""

import re
from typing import Any, Dict, List, Optional


class WorkflowSecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


class InputValidator:
    """Validates workflow inputs for security."""

    # Maximum allowed values
    MAX_WORKFLOW_NAME_LENGTH = 255
    MAX_WORKFLOW_DESCRIPTION_LENGTH = 10000
    MAX_NODES = 100
    MAX_EDGES = 100
    MAX_PARAMETERS = 50
    MAX_PARAMETER_NAME_LENGTH = 100
    MAX_PARAMETER_VALUE_LENGTH = 10000

    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'__import__',
        r'__subclasses__',
        r'__builtins__',
        r'__globals__',
    ]

    # Allowed node types
    ALLOWED_NODE_TYPES = {
        'start', 'end', 'llm_call', 'agent_call', 'data_transform',
        'condition', 'loop', 'parallel', 'merge', 'webhook', 'pm_module', 'custom'
    }

    @classmethod
    def validate_workflow_name(cls, name: str) -> tuple[bool, Optional[str]]:
        """Validate workflow name.

        Args:
            name: The workflow name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Workflow name is required"

        if len(name) > cls.MAX_WORKFLOW_NAME_LENGTH:
            return False, f"Workflow name must be less than {cls.MAX_WORKFLOW_NAME_LENGTH} characters"

        # Check for dangerous patterns
        if cls._contains_dangerous_patterns(name):
            return False, "Workflow name contains invalid characters"

        return True, None

    @classmethod
    def validate_workflow_description(cls, description: str) -> tuple[bool, Optional[str]]:
        """Validate workflow description.

        Args:
            description: The workflow description

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not description:
            return True, None

        if len(description) > cls.MAX_WORKFLOW_DESCRIPTION_LENGTH:
            return False, f"Description must be less than {cls.MAX_WORKFLOW_DESCRIPTION_LENGTH} characters"

        if cls._contains_dangerous_patterns(description):
            return False, "Description contains invalid content"

        return True, None

    @classmethod
    def validate_nodes(cls, nodes: List[dict]) -> tuple[bool, Optional[str]]:
        """Validate workflow nodes.

        Args:
            nodes: List of workflow nodes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not nodes:
            return False, "Workflow must have at least one node"

        if len(nodes) > cls.MAX_NODES:
            return False, f"Workflow cannot have more than {cls.MAX_NODES} nodes"

        node_ids = set()
        for i, node in enumerate(nodes):
            # Check node ID
            node_id = node.get("id")
            if not node_id:
                return False, f"Node {i} missing ID"

            if node_id in node_ids:
                return False, f"Duplicate node ID: {node_id}"
            node_ids.add(node_id)

            # Check node type
            node_type = node.get("type")
            if not node_type:
                return False, f"Node {node_id} missing type"

            if node_type not in cls.ALLOWED_NODE_TYPES:
                return False, f"Invalid node type: {node_type}"

            # Validate node name
            node_name = node.get("name", "")
            if node_name and len(node_name) > cls.MAX_WORKFLOW_NAME_LENGTH:
                return False, f"Node name too long: {node_name}"

            # Validate node config
            config = node.get("config", {})
            config_valid, config_error = cls.validate_node_config(config)
            if not config_valid:
                return False, f"Node {node_id} config error: {config_error}"

        return True, None

    @classmethod
    def validate_node_config(cls, config: dict) -> tuple[bool, Optional[str]]:
        """Validate node configuration.

        Args:
            config: Node configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(config, dict):
            return False, "Config must be an object"

        # Check parameters
        parameters = config.get("parameters", [])
        if len(parameters) > cls.MAX_PARAMETERS:
            return False, f"Too many parameters (max {cls.MAX_PARAMETERS})"

        for param in parameters:
            param_name = param.get("name", "")
            if len(param_name) > cls.MAX_PARAMETER_NAME_LENGTH:
                return False, f"Parameter name too long: {param_name}"

            param_value = param.get("value", "")
            if isinstance(param_value, str) and len(param_value) > cls.MAX_PARAMETER_VALUE_LENGTH:
                return False, f"Parameter value too long: {param_name}"

            # Check for dangerous patterns in parameter values
            if isinstance(param_value, str) and cls._contains_dangerous_patterns(param_value):
                return False, f"Parameter contains invalid content: {param_name}"

        return True, None

    @classmethod
    def validate_edges(cls, edges: List[dict], node_ids: set) -> tuple[bool, Optional[str]]:
        """Validate workflow edges.

        Args:
            edges: List of workflow edges
            node_ids: Set of valid node IDs

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not edges:
            return True, None  # Edges are optional

        if len(edges) > cls.MAX_EDGES:
            return False, f"Workflow cannot have more than {cls.MAX_EDGES} edges"

        for i, edge in enumerate(edges):
            edge_id = edge.get("id")
            if not edge_id:
                return False, f"Edge {i} missing ID"

            source = edge.get("source_node_id") or edge.get("source")
            target = edge.get("target_node_id") or edge.get("target")

            if not source:
                return False, f"Edge {edge_id} missing source"
            if not target:
                return False, f"Edge {edge_id} missing target"

            if source not in node_ids:
                return False, f"Edge {edge_id} references invalid source: {source}"
            if target not in node_ids:
                return False, f"Edge {edge_id} references invalid target: {target}"

            if source == target:
                return False, f"Edge {edge_id} cannot connect a node to itself"

        return True, None

    @classmethod
    def validate_workflow_input(cls, workflow_data: dict) -> tuple[bool, Optional[str]]:
        """Validate complete workflow input.

        Args:
            workflow_data: The workflow data

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate name
        name = workflow_data.get("name", "")
        name_valid, name_error = cls.validate_workflow_name(name)
        if not name_valid:
            return False, name_error

        # Validate description
        description = workflow_data.get("description", "")
        desc_valid, desc_error = cls.validate_workflow_description(description)
        if not desc_valid:
            return False, desc_error

        # Validate nodes
        nodes = workflow_data.get("nodes", [])
        nodes_valid, nodes_error = cls.validate_nodes(nodes)
        if not nodes_valid:
            return False, nodes_error

        # Validate edges
        edges = workflow_data.get("edges", [])
        node_ids = {n.get("id") for n in nodes}
        edges_valid, edges_error = cls.validate_edges(edges, node_ids)
        if not edges_valid:
            return False, edges_error

        return True, None

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string value.

        Args:
            value: The string to sanitize

        Returns:
            Sanitized string
        """
        if not value:
            return value

        # Remove null bytes
        value = value.replace('\x00', '')

        # Remove control characters except common whitespace
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')

        return value

    @classmethod
    def sanitize_workflow_data(cls, workflow_data: dict) -> dict:
        """Sanitize workflow data.

        Args:
            workflow_data: The workflow data

        Returns:
            Sanitized workflow data
        """
        sanitized = dict(workflow_data)

        # Sanitize strings
        if "name" in sanitized:
            sanitized["name"] = cls.sanitize_string(sanitized["name"])
        if "description" in sanitized:
            sanitized["description"] = cls.sanitize_string(sanitized["description"])

        # Sanitize nodes
        if "nodes" in sanitized:
            sanitized["nodes"] = [cls._sanitize_node(node) for node in sanitized["nodes"]]

        return sanitized

    @classmethod
    def _sanitize_node(cls, node: dict) -> dict:
        """Sanitize a node.

        Args:
            node: The node to sanitize

        Returns:
            Sanitized node
        """
        sanitized = dict(node)

        if "name" in sanitized:
            sanitized["name"] = cls.sanitize_string(sanitized["name"])

        if "config" in sanitized:
            config = dict(sanitized["config"])
            if "parameters" in config:
                config["parameters"] = [
                    cls._sanitize_parameter(param) for param in config["parameters"]
                ]
            sanitized["config"] = config

        return sanitized

    @classmethod
    def _sanitize_parameter(cls, param: dict) -> dict:
        """Sanitize a parameter.

        Args:
            param: The parameter to sanitize

        Returns:
            Sanitized parameter
        """
        sanitized = dict(param)

        if "name" in sanitized:
            sanitized["name"] = cls.sanitize_string(sanitized["name"])
        if "description" in sanitized:
            sanitized["description"] = cls.sanitize_string(sanitized["description"])
        if "value" in sanitized and isinstance(sanitized["value"], str):
            sanitized["value"] = cls.sanitize_string(sanitized["value"])

        return sanitized

    @classmethod
    def _contains_dangerous_patterns(cls, value: str) -> bool:
        """Check if a string contains dangerous patterns.

        Args:
            value: The string to check

        Returns:
            True if dangerous patterns found
        """
        if not value:
            return False

        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True

        return False


class RateLimiter:
    """Simple rate limiter for workflow operations."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed.

        Args:
            key: The rate limit key (e.g., user ID)

        Returns:
            True if request is allowed
        """
        import time
        current_time = time.time()

        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < self.window_seconds
        ]

        # Check if under limit
        if len(self.requests[key]) >= self.max_requests:
            return False

        # Add current request
        self.requests[key].append(current_time)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key.

        Args:
            key: The rate limit key

        Returns:
            Number of remaining requests
        """
        import time
        current_time = time.time()

        if key not in self.requests:
            return self.max_requests

        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < self.window_seconds
        ]

        return max(0, self.max_requests - len(self.requests[key]))


# Singleton instances
workflow_validator = InputValidator()
rate_limiter = RateLimiter()
