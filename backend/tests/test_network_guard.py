"""
Tests for network_guard module — SSRF protection (#32).
"""

import os
import sys
import importlib.util
import pytest
from unittest.mock import patch, MagicMock
import socket

# 直接加载模块文件, 绕过 open_webui/__init__.py 的完整依赖链
_module_path = os.path.join(
    os.path.dirname(__file__), "..", "open_webui", "services", "workflow", "network_guard.py"
)
_spec = importlib.util.spec_from_file_location("network_guard", _module_path)
network_guard = importlib.util.module_from_spec(_spec)
sys.modules["network_guard"] = network_guard  # 注册到 sys.modules 以支持 @patch
_spec.loader.exec_module(network_guard)

validate_url = network_guard.validate_url
SSRFError = network_guard.SSRFError
sanitize_response_headers = network_guard.sanitize_response_headers
DEFAULT_TIMEOUT_SECONDS = network_guard.DEFAULT_TIMEOUT_SECONDS
DEFAULT_MAX_RESPONSE_BYTES = network_guard.DEFAULT_MAX_RESPONSE_BYTES
ALLOWED_SCHEMES = network_guard.ALLOWED_SCHEMES
BLOCKED_NETWORKS = network_guard.BLOCKED_NETWORKS


def _mock_resolve(host_to_ips: dict):
    """Helper: 构造一个 getaddrinfo mock, 将 host 映射到 IP 列表."""

    def fake_getaddrinfo(host, *args, **kwargs):
        ips = host_to_ips.get(host)
        if ips is None:
            raise socket.gaierror("DNS resolve failed")
        return [(None, None, None, None, (ip, 0)) for ip in ips]

    return fake_getaddrinfo


class TestValidateUrlBlocksPrivateIP:
    """#32: 阻断 RFC1918 私网地址."""

    @patch("network_guard.socket.getaddrinfo")
    def test_blocks_10_x(self, mock_gai):
        mock_gai.side_effect = _mock_resolve({"private.example.com": ["10.0.0.1"]})
        with pytest.raises(SSRFError, match="blocked network"):
            validate_url("http://private.example.com/")

    @patch("network_guard.socket.getaddrinfo")
    def test_blocks_172_16_x(self, mock_gai):
        mock_gai.side_effect = _mock_resolve({"internal.corp": ["172.16.5.5"]})
        with pytest.raises(SSRFError, match="blocked network"):
            validate_url("http://internal.corp/api")

    @patch("network_guard.socket.getaddrinfo")
    def test_blocks_192_168_x(self, mock_gai):
        mock_gai.side_effect = _mock_resolve({"router.lan": ["192.168.1.1"]})
        with pytest.raises(SSRFError, match="blocked network"):
            validate_url("http://router.lan/")


class TestValidateUrlBlocksMetadata:
    """#32: 阻断云元数据服务地址 (169.254.169.254)."""

    @patch("network_guard.socket.getaddrinfo")
    def test_blocks_aws_metadata(self, mock_gai):
        mock_gai.side_effect = _mock_resolve({"169.254.169.254": ["169.254.169.254"]})
        with pytest.raises(SSRFError, match="blocked network"):
            validate_url("http://169.254.169.254/latest/meta-data/iam/security-credentials/")


class TestValidateUrlBlocksLoopback:
    """#32: 阻断 loopback 地址."""

    @patch("network_guard.socket.getaddrinfo")
    def test_blocks_127_0_0_1(self, mock_gai):
        mock_gai.side_effect = _mock_resolve({"localhost": ["127.0.0.1"]})
        with pytest.raises(SSRFError, match="blocked network"):
            validate_url("http://localhost:8080/api/v1/admins")


class TestValidateUrlBlocksDisallowedScheme:
    """#32: 协议白名单 (仅 http/https)."""

    def test_blocks_file_scheme(self):
        with pytest.raises(SSRFError, match="scheme not allowed"):
            validate_url("file:///etc/passwd")

    def test_blocks_gopher_scheme(self):
        with pytest.raises(SSRFError, match="scheme not allowed"):
            validate_url("gopher://attacker.com/x")

    def test_blocks_ftp_scheme(self):
        with pytest.raises(SSRFError, match="scheme not allowed"):
            validate_url("ftp://example.com/file")


class TestValidateUrlAllowsPublic:
    """#32: 公网域名放行."""

    @patch("network_guard.socket.getaddrinfo")
    def test_allows_public_ip(self, mock_gai):
        mock_gai.side_effect = _mock_resolve({"example.com": ["93.184.216.34"]})
        host, ip = validate_url("https://example.com/")
        assert host == "example.com"
        assert ip == "93.184.216.34"


class TestSanitizeResponseHeaders:
    """#32: 响应头脱敏."""

    def test_strips_set_cookie(self):
        headers = {"Set-Cookie": "session=abc; HttpOnly", "Content-Type": "application/json"}
        result = sanitize_response_headers(headers)
        assert "Set-Cookie" not in result
        assert "Content-Type" in result

    def test_strips_server_header(self):
        headers = {"Server": "nginx/1.21", "Content-Length": "42"}
        result = sanitize_response_headers(headers)
        assert "Server" not in result

    def test_strips_x_powered_by(self):
        headers = {"X-Powered-By": "Express", "X-Request-Id": "abc123"}
        result = sanitize_response_headers(headers)
        assert "X-Powered-By" not in result
        assert "X-Request-Id" not in result

    def test_case_insensitive(self):
        """大小写不敏感匹配."""
        headers = {"set-cookie": "x=1", "SET-COOKIE": "y=2", "Server": "apache"}
        result = sanitize_response_headers(headers)
        assert "set-cookie" not in result
        assert "SET-COOKIE" not in result
        assert "Server" not in result

    def test_keeps_unrelated_headers(self):
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
        result = sanitize_response_headers(headers)
        assert result == headers


class TestConstants:
    """#32: 常量合理性校验."""

    def test_default_timeout_is_10s(self):
        assert DEFAULT_TIMEOUT_SECONDS == 10

    def test_default_max_response_bytes_is_1mib(self):
        assert DEFAULT_MAX_RESPONSE_BYTES == 1024 * 1024

    def test_allowed_schemes_only_http_https(self):
        assert ALLOWED_SCHEMES == {"http", "https"}

    def test_blocked_networks_includes_ipv6_loopback(self):
        import ipaddress
        loopback_v6 = ipaddress.ip_network("::1/128")
        assert loopback_v6 in BLOCKED_NETWORKS
