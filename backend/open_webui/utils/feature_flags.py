"""Feature flag 工具 - 基于环境变量的开关.

#31 / #35 安全治理 Phase 5: 引入两个 flag 控制未来安全特性的启用.
Phase 5 仅产出 flag + PoC 设计文档, 实际沙箱/隔离实现排到 Phase 7+.

Flags:
- WORKFLOW_SANDBOX_ENABLED (default: false): 启用工作流执行沙箱
  当 true 时, 工作流 engine 应通过 subprocess + seccomp 隔离执行 code/http 节点.
  详见 docs/poc-design/workflow-sandbox-poc.md
- EXTENSION_CREDENTIAL_ISOLATION (default: false): 启用扩展凭证隔离
  当 true 时, 扩展 (skills/tools/functions) 不再从主进程环境变量读取凭证,
  改为通过 per-execution ephemeral token 注入.
  详见 docs/poc-design/extension-credential-isolation-poc.md
"""

import os


def is_workflow_sandbox_enabled() -> bool:
    """检查 WORKFLOW_SANDBOX_ENABLED flag.

    Returns:
        True 当环境变量设为 'true' (大小写不敏感). 默认 False.
    """
    return os.environ.get("WORKFLOW_SANDBOX_ENABLED", "false").lower() == "true"


def is_extension_credential_isolation_enabled() -> bool:
    """检查 EXTENSION_CREDENTIAL_ISOLATION flag.

    Returns:
        True 当环境变量设为 'true' (大小写不敏感). 默认 False.
    """
    return os.environ.get("EXTENSION_CREDENTIAL_ISOLATION", "false").lower() == "true"
