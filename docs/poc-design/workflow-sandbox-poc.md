# PoC 设计: 工作流执行沙箱隔离 (#31)

**状态**: 设计阶段 (Phase 5)
**评估日期**: 2026-07-21
**关联 Issue**: #31
**Feature Flag**: `WORKFLOW_SANDBOX_ENABLED` (默认 `false`)

---

## 1. 问题陈述

### 当前状态

`backend/open_webui/services/workflow/engine.py` 的工作流执行引擎直接以服务进程身份运行:

- **Code 节点** (`_execute_code_node`, engine.py L1409+): 通过 `subprocess` 执行用户代码, 但子进程继承主进程的:
  - 文件系统访问权限 (可读 `/etc/passwd`, `/app/backend/data/` 等)
  - 网络访问权限 (无出站过滤)
  - 环境变量 (含 `WEBUI_SECRET_KEY`, `DATABASE_URL`, 各种 API key)
  - 系统调用权限 (无 seccomp 限制)
- **HTTP 节点** (`_execute_http_request_node`, L1342): Phase 2 已加 SSRF 防护 (`network_guard.validate_url`), 但仍以主进程身份发起请求
- **Agent 节点** (`_execute_agent_call_node`, L837): 通过 `generate_chat_completion` 调用本地 LLM, 风险较低

### 攻击面

| 攻击向量 | 当前防护 | 影响 |
|---------|---------|------|
| Code 节点读敏感文件 | 无 | 泄露 `DATABASE_URL`, `WEBUI_SECRET_KEY` 等 |
| Code 节点发起内网请求 | Phase 2 SSRF (仅 HTTP 节点) | Code 节点用 `socket` 绕过 |
| Code 节点写文件 | 无 | 篡改 `/app/backend/data/` |
| Code 节点 fork bomb | 无 | DoS |
| 环境变量泄露 | 无 | Code 节点 `os.environ` 直接读取 |

### 不解决的代价

若不实施沙箱, 工作流执行可被滥用获取服务器完全控制权. 这是一个 P0 级安全问题, 但实现成本高, 需先评估方案.

---

## 2. 备选方案对比

### 方案 A: subprocess + seccomp (Linux only)

**实现**:
- Code 节点改为通过 `subprocess.run(...)` 启动独立进程
- 父进程 fork 后, 子进程调用 `seccomp(SECCOMP_MODE_FILTER)` 限制系统调用:
  - 允许: `read`, `write`, `exit`, `brk`, `mmap`, `munmap`, `rt_sigreturn`
  - 禁止: `open` (除 stdin/stdout/stderr 外), `socket`, `fork`, `execve`, `ptrace`
- 通过 `prctl(PR_SET_NO_NEW_PRIVS)` 阻止提权
- 通过 cgroups 限制 CPU/内存

**优势**:
- 轻量, 启动开销 <50ms
- Linux 原生, 无额外依赖
- 与现有 `_execute_code_node` 的 subprocess 模式契合

**劣势**:
- 仅 Linux (macOS/Windows 开发体验差)
- seccomp filter 配置复杂, 容易误杀合法 syscall
- 不隔离文件系统 (需配合 chroot/bind mount)

**工作量**: M (2-3 工程师周)

### 方案 B: Docker container per execution

**实现**:
- 每次执行启动一个临时 Docker 容器:
  ```bash
  docker run --rm --network none --read-only \
    --memory 512m --cpus 0.5 \
    -v /tmp/script.py:/script.py:ro \
    sandbox-image python /script.py
  ```
- 容器内无网络, 只读文件系统, 资源限制

**优势**:
- 隔离最强 (内核级 namespace + cgroups)
- 跨平台 (Docker Desktop on macOS/Windows)
- 配置简单, Dockerfile 即文档

**劣势**:
- 启动开销 ~1-2s (容器创建 + Python 解释器冷启动)
- 需要宿主机 Docker daemon 访问权限
- 容器镜像管理 (CVE patch)
- 并发执行时资源消耗大

**工作量**: L (4-6 工程师周, 含镜像构建与 CI)

### 方案 C: Firecracker microVM

**实现**:
- 使用 Firecracker (AWS 开源的 microVM) 启动轻量级 VM:
  - 启动时间 ~125ms
  - 内存开销 ~5MiB
  - 完整内核隔离

**优势**:
- 启动快 (相比方案 B)
- 隔离最强 (VM 级)
- 资源开销小

**劣势**:
- 需要 KVM 支持 (部署受限)
- 需要构建 rootfs 与内核镜像
- 集成复杂度高
- 与 Open WebUI 现有架构差异大

**工作量**: XL (8+ 工程师周, 含基础设施)

### 方案 D: WASM runtime (wasmtime)

**实现**:
- 将用户代码通过 Pyodide (Python on WASM) 在 wasmtime 中执行
- WASM 沙箱天然隔离系统调用

**优势**:
- 跨平台
- 启动快
- 安全性高 (默认无 I/O 能力)

**劣势**:
- Python 生态不成熟 (Pyodide 仅支持部分包)
- 无法执行非 Python 代码
- 性能开销 (JIT 编译)

**工作量**: L (5-7 工程师周, 主要是兼容性调试)

---

## 3. 推荐方案: A (subprocess + seccomp)

**理由**:

1. **与现有架构契合**: `_execute_code_node` 已用 subprocess, 改动范围最小
2. **启动开销可接受**: <50ms vs 方案 B 的 1-2s, 用户体验差异显著
3. **依赖最少**: 无需 Docker daemon, 无需 KVM, 仅 Linux 原生
4. **覆盖率足够**: 解决 Code 节点的核心威胁 (FS / env / 网络), 不追求完美隔离
5. **可渐进增强**: 后续可在方案 A 基础上加 chroot / bind mount 进一步收紧 FS

**取舍**:
- 放弃方案 B/C/D 的更强隔离, 接受 Linux-only 限制
- macOS/Windows 开发环境沙箱默认关闭 (feature flag 控制)

---

## 4. 实施计划 (Phase 7+, 不在 Phase 5 范围内)

### Step 7.1 - 新建 sandbox 模块

**新文件**: `backend/open_webui/services/workflow/sandbox.py`

```python
"""工作流执行沙箱 (Phase 7+, #31).

仅当 WORKFLOW_SANDBOX_ENABLED=true 时启用.
通过 subprocess + seccomp 隔离 Code 节点执行.
"""
import os
import subprocess
import sys

from open_webui.utils.feature_flags import is_workflow_sandbox_enabled


class SandboxError(Exception):
    """沙箱执行失败."""


def execute_in_sandbox(code: str, input_data: dict, timeout: int = 10) -> dict:
    """在沙箱中执行用户代码.

    若 WORKFLOW_SANDBOX_ENABLED=true: 通过 seccomp 限制的 subprocess 执行.
    否则: 直接在当前进程执行 (向后兼容).

    Returns:
        {"status": "completed"/"failed", "output": ..., "error": ...}
    """
    if not is_workflow_sandbox_enabled():
        # 未启用沙箱, 沿用现有逻辑 (engine.py 内)
        raise SandboxError("Sandbox not enabled - caller should fall back to direct execution")

    # TODO Phase 7: 实现 seccomp filter + subprocess
    raise NotImplementedError("Sandbox execution not yet implemented (Phase 7+)")
```

### Step 7.2 - 修改 engine.py

`_execute_code_node` 在执行前检查 flag:

```python
from open_webui.utils.feature_flags import is_workflow_sandbox_enabled
from open_webui.services.workflow.sandbox import execute_in_sandbox, SandboxError

# ... 在 _execute_code_node 内:
if is_workflow_sandbox_enabled():
    try:
        return execute_in_sandbox(code, input_variables, timeout=10)
    except SandboxError:
        # 沙箱不可用 (如非 Linux), 降级为直接执行
        log.warning("Sandbox unavailable, falling back to direct execution")
# ... 原有 subprocess 逻辑
```

### Step 7.3 - seccomp filter 配置

使用 `pyseccomp` 库 (Python binding for libseccomp):

```python
import seccomp

def setup_sandbox_filter():
    f = seccomp.SyscallFilter(defaction=seccomp.KILL)
    # 允许基础 syscall
    for syscall in ['read', 'write', 'exit', 'exit_group', 'brk',
                    'mmap', 'munmap', 'mprotect', 'rt_sigreturn']:
        f.add_rule(seccomp.ALLOW, syscall)
    # 允许 stdin/stdout/stderr
    f.add_rule(seccomp.ALLOW, 'fcntl',
               seccomp.Arg(0, seccomp.EQ, 0))
    f.add_rule(seccomp.ALLOW, 'fcntl',
               seccomp.Arg(0, seccomp.EQ, 1))
    f.add_rule(seccomp.ALLOW, 'fcntl',
               seccomp.Arg(0, seccomp.EQ, 2))
    f.load()
```

### Step 7.4 - 测试与验证

- 单元测试: 沙箱内代码无法读 `/etc/passwd` (返回 EPERM)
- 单元测试: 沙箱内代码无法 `socket()` (返回 EPERM)
- 集成测试: workflow 含 code 节点, WORKFLOW_SANDBOX_ENABLED=true, 执行成功
- 性能测试: 沙箱开销 < 100ms

---

## 5. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解 |
|------|--------|------|------|
| seccomp filter 误杀合法 syscall | Med | High | 在测试环境跑完整 workflow 测试套件, 用 strace 确认 syscall 列表 |
| macOS/Windows 开发体验差 | High | Med | feature flag 默认 false, 非 Linux 平台检测到时自动降级 |
| 沙箱启动开销超预期 | Low | Med | 测量基线, 若 >200ms 则考虑方案 B |
| 用户代码依赖被禁 syscall (如 `socket`) | High | Low | 文档明确说明沙箱限制, 用户可选择禁用沙箱 (自担风险) |

---

## 6. 回滚策略

- Feature flag 默认 `false`, 部署后无影响
- 出问题时: `unset WORKFLOW_SANDBOX_ENABLED` 重启服务即可
- 沙箱代码独立模块 (`sandbox.py`), 不影响现有 engine.py 主流程

---

## 7. 验证标准

Phase 7 完成后需满足:

- [ ] `WORKFLOW_SANDBOX_ENABLED=true` 时, code 节点在沙箱内执行
- [ ] 沙箱内代码无法 `open('/etc/passwd')` (返回 EPERM)
- [ ] 沙箱内代码无法 `socket.socket()` (返回 EPERM)
- [ ] 沙箱内代码无法读 `os.environ['WEBUI_SECRET_KEY']` (env 不继承)
- [ ] 沙箱启动开销 < 100ms (基线测试)
- [ ] `WORKFLOW_SANDBOX_ENABLED=false` (默认) 时, 行为与 Phase 5 前完全一致
- [ ] 非 Linux 平台检测到 sandbox=true 时, log warning 并降级为直接执行

---

## 8. 参考资料

- seccomp: https://man7.org/linux/man-pages/man2/seccomp.2.html
- prctl(PR_SET_NO_NEW_PRIVS): https://man7.org/linux/man-pages/man2/prctl.2.html
- pyseccomp: https://github.com/seccomp/libseccomp
- Google's "沙箱设计" 文档: https://google.github.io/project-zero/
