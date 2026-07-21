"""LLM 响应脱敏模块 — 对 agent_call 节点输出做正则脱敏.

#34 安全治理: 阻断 LLM 响应中的敏感信息泄露 (API key / 私钥 / PII).

策略 (D4 默认开, 不可关):
- API key 模式: sk- / AKIA / ghp_ / gho_ / github_pat 等
- 私钥标记: -----BEGIN ... PRIVATE KEY-----
- 邮箱 / 中国手机号 / 信用卡号
- 内部路径: /root/ / /home/ / C:\\\\Users\\\\

误杀可接受 (脱敏后文本仍可读), 漏杀不可接受.
"""

import logging
import re

log = logging.getLogger(__name__)

# (pattern, replacement) 元组列表
PATTERNS: list[tuple[re.Pattern, str]] = [
    # OpenAI / Anthropic API key (sk- 前缀 + 至少 20 位字母数字)
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "sk-***REDACTED***"),
    # AWS Access Key ID (AKIA + 16 位大写字母数字)
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AKIA***REDACTED***"),
    # GitHub Personal Access Token (ghp_/gho_/ghu_/ghs_/ghr_ + 36+ 位)
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"), "ghp_***REDACTED***"),
    # GitHub fine-grained PAT
    (re.compile(r"github_pat_[A-Za-z0-9_]{22,}"), "github_pat_***REDACTED***"),
    # PEM 私钥块 (含 BEGIN/END)
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
        ),
        "-----PRIVATE KEY REDACTED-----",
    ),
    # 邮箱
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "***@***.***",
    ),
    # 中国手机号 (1[3-9] + 9 位数字)
    (re.compile(r"\b1[3-9]\d{9}\b"), "1**-****-***"),
    # 信用卡号 (13-19 位连续数字, 含空格/连字符变体)
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "***CARD-REDACTED***"),
    # 内部 Unix 路径
    (re.compile(r"(?:/root/|/home/)[^\s'\"]+"), "/home/***REDACTED***"),
    # Windows 用户路径
    (re.compile(r"[A-Z]:\\\\Users\\\\[^\s'\"]+"), "C:\\\\Users\\\\***REDACTED***"),
]


def sanitize_text(text: str) -> str:
    """对字符串做正则脱敏.

    Args:
        text: 待脱敏的字符串

    Returns:
        脱敏后的字符串. 若输入非字符串, 原样返回.
    """
    if not isinstance(text, str):
        return text
    out = text
    for pattern, replacement in PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def sanitize(obj):
    """递归对 dict / list / str 做脱敏.

    Args:
        obj: 任意 Python 对象 (通常为 LLM 响应解析后的 dict/list/str)

    Returns:
        同结构的新对象, 所有字符串字段已脱敏. 非 str/dict/list 原样返回.
    """
    if isinstance(obj, str):
        return sanitize_text(obj)
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj
