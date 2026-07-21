"""SSRF 防护模块 — 校验出站 HTTP 请求目标.

#32 安全治理: 阻断 workflow HTTP 节点对内网/元数据/保留地址的访问.

设计:
- 协议白名单: 仅 http/https
- IP 黑名单: 私有 / 保留 / 链路本地 / 云元数据地址 (RFC1918 + RFC6598 + 169.254/16 + 其他保留段)
- DNS 解析后校验真实 IP (防 DNS rebinding)
- 调用方需禁用 redirect 或自校验每跳 (本模块不处理 redirect)
- 提供响应头脱敏 (剔除 Set-Cookie / 内部 trace 等)
"""

import ipaddress
import logging
import socket
from typing import Tuple
from urllib.parse import urlparse

log = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}

# IPv4 黑名单网络段
BLOCKED_NETWORKS_V4 = [
    ipaddress.ip_network("0.0.0.0/8"),        # 本网络
    ipaddress.ip_network("10.0.0.0/8"),       # RFC1918
    ipaddress.ip_network("100.64.0.0/10"),    # CGNAT (RFC6598)
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("169.254.0.0/16"),   # 链路本地 + 云元数据 (AWS/GCP/Azure)
    ipaddress.ip_network("172.16.0.0/12"),    # RFC1918
    ipaddress.ip_network("192.0.0.0/24"),     # IETF 协议分配
    ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),   # 6to4 中继
    ipaddress.ip_network("192.168.0.0/16"),   # RFC1918
    ipaddress.ip_network("198.18.0.0/15"),    # 网络基准测试
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),      # 多播
    ipaddress.ip_network("240.0.0.0/4"),      # 保留
]

# IPv6 黑名单网络段
BLOCKED_NETWORKS_V6 = [
    ipaddress.ip_network("::1/128"),          # loopback
    ipaddress.ip_network("fc00::/7"),         # ULA
    ipaddress.ip_network("fe80::/10"),        # 链路本地
    ipaddress.ip_network("ff00::/8"),         # 多播
]

BLOCKED_NETWORKS = BLOCKED_NETWORKS_V4 + BLOCKED_NETWORKS_V6


class SSRFError(ValueError):
    """URL 校验失败."""


def validate_url(url: str) -> Tuple[str, str]:
    """校验 URL 是否允许出站请求.

    校验流程:
    1. 协议必须在 ALLOWED_SCHEMES (http/https)
    2. host 必须存在
    3. DNS 解析 host, 对所有返回的 IP 校验是否在 BLOCKED_NETWORKS

    Args:
        url: 待校验的完整 URL

    Returns:
        (host, first_resolved_ip) 元组

    Raises:
        SSRFError: 校验失败 (协议不允许 / host 缺失 / DNS 失败 / IP 在黑名单)
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise SSRFError(f"scheme not allowed: {parsed.scheme!r} (allowed: {sorted(ALLOWED_SCHEMES)})")
    host = parsed.hostname
    if not host:
        raise SSRFError("missing hostname in URL")

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise SSRFError(f"DNS resolve failed for {host!r}: {e}")

    ips = {info[4][0] for info in infos}
    if not ips:
        raise SSRFError(f"DNS resolve returned empty for {host!r}")

    for ip_str in ips:
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError as e:
            raise SSRFError(f"invalid IP {ip_str!r} for host {host!r}: {e}")
        for net in BLOCKED_NETWORKS:
            if ip in net:
                raise SSRFError(f"resolved IP {ip} (host={host!r}) in blocked network {net}")

    return host, next(iter(ips))


# aiohttp 请求默认限制
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024  # 1 MiB

# 响应头中需剔除的字段 (小写匹配)
SANITIZE_RESPONSE_HEADERS = {
    "set-cookie",
    "x-internal-trace",
    "x-debug",
    "server",
    "x-powered-by",
    "via",
    "x-forwarded-for",
    "x-real-ip",
    "x-request-id",
    "x-trace-id",
}


def sanitize_response_headers(headers: dict) -> dict:
    """剔除响应头中的敏感字段.

    Args:
        headers: aiohttp 响应头 dict (key 大小写不敏感)

    Returns:
        新 dict, 移除了 SANITIZE_RESPONSE_HEADERS 中的字段
    """
    return {
        k: v for k, v in headers.items()
        if k.lower() not in SANITIZE_RESPONSE_HEADERS
    }
