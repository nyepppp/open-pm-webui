# PoC 设计: 扩展凭证隔离 (#35)

**状态**: 设计阶段 (Phase 5)
**评估日期**: 2026-07-21
**关联 Issue**: #35
**Feature Flag**: `EXTENSION_CREDENTIAL_ISOLATION` (默认 `false`)

---

## 1. 问题陈述

### 当前状态

Open WebUI 的扩展系统 (skills / tools / functions) 通过以下方式访问外部服务:

- **环境变量**: 主进程 `os.environ` 中存储所有 API key (OpenAI / Anthropic / GitHub / 数据库连接串等)
- **配置表**: `configs` 表中持久化部分 key (加密存储, 但解密后注入进程内存)
- **工具调用**: tools 通过 `subprocess` 执行, 继承父进程环境变量

### 暴露面

| 扩展类型 | 当前凭证访问方式 | 风险 |
|---------|----------------|------|
| Skills (`pm/api/skills.py`) | 通过 `request` 上下文间接访问 user 配置 | Med - Phase 3 已加 RBAC |
| Tools (`routers/tools.py`) | `subprocess` 继承全部 env | High - 任何 tool 可读所有 key |
| Functions (`routers/functions.py`) | 在主进程内执行, 直接读 env | High - 任意 function 可读所有 key |
| Workflow code 节点 | subprocess 继承 env | High - 用户代码可读所有 key |

### 攻击场景

1. **恶意 function**: 攻击者上传一个 function, 在 `__init__` 中读取 `os.environ['OPENAI_API_KEY']` 并通过 HTTP 外传
2. **Workflow 滥用**: 用户创建 workflow, code 节点读取 `DATABASE_URL` 并通过 Phase 2 的 HTTP 节点 (合法 URL) 外传
3. **Tool 滥用**: 任何 tool 通过 `subprocess` 调 `env` 命令列出所有环境变量

### 不解决的代价

凭证泄露 = 服务账户被接管. 即使 Phase 3 RBAC 限制扩展调用, 已授权的扩展仍可读全部凭证.

---

## 2. 备选方案对比

### 方案 A: per-extension secret store

**实现**:
- 引入 HashiCorp Vault / AWS Secrets Manager / Docker Secret
- 每个扩展在注册时声明所需凭证, 由 admin 在 secret store 中配置
- 扩展执行时通过 SDK 临时拉取凭证, 不进入主进程 env

**优势**:
- 业界标准做法
- 凭证生命周期可审计 (Vault audit log)
- 支持凭证轮转

**劣势**:
- 引入外部依赖 (Vault 部署/运维成本)
- 集成复杂度高
- 非云环境部署难度大

**工作量**: XL (8+ 工程师周, 含 Vault 部署)

### 方案 B: per-execution ephemeral token

**实现**:
- 主进程持有一份"长期凭证" (如 OpenAI API key), 但不直接暴露给扩展
- 扩展执行时, 主进程生成一个"短期 token" (如 JWT, TTL=5min):
  ```json
  {
    "sub": "extension:tool-X",
    "exp": 1700000300,
    "scope": ["llm:call"]
  }
  ```
  签名用 `WEBUI_SECRET_KEY`
- 扩展用 token 调用一个内部代理端点 (`/api/v1/internal/llm/proxy`), 代理用长期凭证转发请求
- 扩展无法直接读取长期凭证

**优势**:
- 无外部依赖 (JWT 用现有 secret 签)
- 与 Phase 4 审计日志天然集成 (每次 token 使用都被记录)
- 与 Phase 5 沙箱方案 A 配合: 沙箱内代码只能用 token, 无法读 env

**劣势**:
- 需要实现内部代理 (HTTP/LLM 转发)
- 现有扩展需要改造 (从读 env 改为用 token 调代理)
- token 仍可能被扩展在有效期内转发 (但已限定 scope + TTL)

**工作量**: L (5-7 工程师周)

### 方案 C: 进程级环境变量隔离

**实现**:
- 扩展执行时通过 subprocess 启动, 父进程显式构造 env dict:
  ```python
  allowed_env = {
      "PATH": os.environ["PATH"],
      "HOME": os.environ["HOME"],
      # 仅注入扩展声明的变量
      "OPENAI_API_KEY": get_extension_secret("tool-X", "openai"),
  }
  subprocess.run([cmd], env=allowed_env)
  ```

**优势**:
- 实现简单 (subprocess env 参数)
- 无外部依赖
- 与 Phase 5 沙箱方案 A 完全契合

**劣势**:
- 仅适用于 subprocess 执行的扩展 (tools), 不适用于进程内 functions
- functions 需要改造为 subprocess 执行 (破坏性变更)
- 凭证仍以明文存在于子进程 env, 子进程可读 (但限制了范围)

**工作量**: M (3-4 工程师周)

---

## 3. 推荐方案: B (per-execution ephemeral token)

**理由**:

1. **覆盖最全**: 同时适用于 subprocess 执行的 tools 和进程内 functions
2. **与现有架构契合**: Open WebUI 已有 LLM 调用代理 (`generate_chat_completion`), 扩展为通用代理即可
3. **审计友好**: Phase 4 审计日志可记录每次 token 签发与使用
4. **与沙箱方案 A 配合**: 沙箱内代码无法读 env, 但可以通过 stdin 传入 token
5. **渐进式**: 不启用 flag 时完全不影响现有行为

**取舍**:
- 放弃方案 A 的强隔离 (接受 token 在 TTL 内可被扩展转发的风险)
- 放弃方案 C 的简单实现 (接受需要实现代理的工作量)
- 接受现有扩展需要改造 (通过兼容层降低影响)

---

## 4. 实施计划 (Phase 7+, 不在 Phase 5 范围内)

### Step 7.1 - Token 签发模块

**新文件**: `backend/open_webui/utils/extension_token.py`

```python
"""扩展执行凭证 token 签发与校验 (#35, Phase 7+).

仅当 EXTENSION_CREDENTIAL_ISOLATION=true 时启用.
扩展通过 token 调用内部代理, 而非直接读取主进程凭证.
"""
import jwt
import time
import uuid
from typing import Optional

from open_webui.utils.feature_flags import is_extension_credential_isolation_enabled

DEFAULT_TTL_SECONDS = 300  # 5 分钟


def issue_token(
    extension_id: str,
    extension_type: str,  # 'skill' | 'tool' | 'function'
    user_id: str,
    scopes: list[str],
    ttl: int = DEFAULT_TTL_SECONDS,
) -> str:
    """为扩展执行签发短期 token."""
    from open_webui.config import WEBUI_SECRET_KEY  # 或同等密钥源

    payload = {
        "sub": f"{extension_type}:{extension_id}",
        "user_id": user_id,
        "scope": scopes,
        "jti": str(uuid.uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl,
    }
    return jwt.encode(payload, WEBUI_SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> Optional[dict]:
    """校验 token, 返回 payload 或 None."""
    from open_webui.config import WEBUI_SECRET_KEY
    try:
        return jwt.decode(token, WEBUI_SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
```

### Step 7.2 - 内部代理端点

**修改**: `backend/open_webui/routers/utils.py` (或新建 `routers/proxy.py`)

```python
@router.post("/internal/proxy/llm")
async def proxy_llm_call(
    request: Request,
    token: str = Header(...),
    body: dict = Body(...),
):
    """LLM 调用代理 - 扩展通过 token 调用, 不直接读 API key.

    #35: 仅当 EXTENSION_CREDENTIAL_ISOLATION=true 时启用.
    """
    if not is_extension_credential_isolation_enabled():
        raise HTTPException(404)  # 未启用时端点不存在

    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid extension token")

    if "llm:call" not in payload.get("scope", []):
        raise HTTPException(403, "Token lacks llm:call scope")

    # 用主进程的 OpenAI 配置转发请求
    # 记录审计日志 (Phase 4 集成)
    await AuditLogs.record(
        action="proxy_llm_call",
        resource_type="extension",
        actor_user_id=payload["user_id"],
        resource_id=payload["sub"],
        detail={"model": body.get("model"), "scope": payload["scope"]},
    )

    # 调用真实 LLM API...
    return await generate_chat_completion(...)
```

### Step 7.3 - 扩展执行改造

`backend/open_webui/routers/tools.py` 中执行 tool 时:

```python
if is_extension_credential_isolation_enabled():
    # 签发 token, 通过 stdin 传给子进程, 而非继承 env
    token = issue_token(tool.id, "tool", user.id, scopes=["llm:call"])
    env = {
        "PATH": os.environ["PATH"],
        "HOME": os.environ["HOME"],
        "EXTENSION_TOKEN": token,  # 仅注入 token, 不注入 API key
        "PROXY_URL": "http://localhost:8080/api/v1/internal/proxy/llm",
    }
    subprocess.run([cmd], env=env)
else:
    # 现有逻辑: 继承全部 env
    subprocess.run([cmd])
```

### Step 7.4 - 兼容层

为减少破坏性变更, 提供一个 helper:

```python
def get_credential(name: str, extension_token: Optional[str] = None) -> Optional[str]:
    """扩展获取凭证的统一入口.

    若 EXTENSION_CREDENTIAL_ISOLATION=true: 通过 token 调代理, 不返回明文 key.
    否则: 直接读 os.environ (向后兼容).
    """
    if is_extension_credential_isolation_enabled() and extension_token:
        # 返回代理 URL + token, 扩展通过代理访问
        return f"proxy://{extension_token}"
    return os.environ.get(name)
```

扩展代码改为:
```python
# 旧: api_key = os.environ["OPENAI_API_KEY"]
# 新:
from open_webui.utils.extension_token import get_credential
api_key = get_credential("OPENAI_API_KEY", extension_token=os.environ.get("EXTENSION_TOKEN"))
```

### Step 7.5 - 测试与验证

- 单元测试: token 签发/校验正确
- 单元测试: 过期 token 被拒
- 单元测试: scope 不匹配被拒
- 集成测试: tool 执行时 env 中无 `OPENAI_API_KEY`, 仅 `EXTENSION_TOKEN`
- 安全测试: tool 代码尝试 `os.environ["OPENAI_API_KEY"]` -> KeyError
- 审计测试: 每次 token 使用产生审计日志

---

## 5. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解 |
|------|--------|------|------|
| token 在 TTL 内被扩展转发 | Med | Med | TTL 设为 5min, scope 限定, 审计日志记录异常使用模式 |
| 现有扩展不兼容 | High | High | 兼容层 `get_credential` 降低迁移成本; 文档提供迁移指南 |
| 代理端点成为瓶颈 | Low | Med | 代理端点无状态, 可水平扩展; 监控 P99 延迟 |
| WEBUI_SECRET_KEY 泄露 | Low | High | key 轮转流程, 监控异常 token 签发量 |
| 扩展拒绝迁移 | Med | Med | feature flag 默认 false, 渐进式启用 |

---

## 6. 回滚策略

- Feature flag 默认 `false`, 部署后无影响
- 出问题时: `unset EXTENSION_CREDENTIAL_ISOLATION` 重启服务
- 代理端点在 flag=false 时返回 404, 不消耗资源
- 兼容层在 flag=false 时直接读 env, 行为与 Phase 5 前一致

---

## 7. 验证标准

Phase 7 完成后需满足:

- [ ] `EXTENSION_CREDENTIAL_ISOLATION=true` 时, tool 执行的子进程 env 中无任何 API key
- [ ] 子进程仅有 `PATH`, `HOME`, `EXTENSION_TOKEN`, `PROXY_URL`
- [ ] token TTL 默认 5min, 可配置
- [ ] token 校验失败返回 401
- [ ] scope 不匹配返回 403
- [ ] 每次 token 使用产生审计日志 (Phase 4 集成)
- [ ] `EXTENSION_CREDENTIAL_ISOLATION=false` 时, 行为与 Phase 5 前完全一致
- [ ] 兼容层 `get_credential` 在 flag=false 时返回 `os.environ.get(name)`

---

## 8. 参考资料

- JWT RFC: https://datatracker.ietf.org/doc/html/rfc7519
- OAuth 2.0 Token Exchange: https://datatracker.ietf.org/doc/html/rfc8693
- HashiCorp Vault: https://developer.hashicorp.com/vault
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager/
