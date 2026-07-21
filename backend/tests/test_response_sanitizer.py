"""
Tests for response_sanitizer module — LLM response redaction (#34).
"""

import os
import importlib.util
import pytest

# 直接加载模块文件, 绕过 open_webui/__init__.py 的完整依赖链
_module_path = os.path.join(
    os.path.dirname(__file__), "..", "open_webui", "services", "workflow", "response_sanitizer.py"
)
_spec = importlib.util.spec_from_file_location("response_sanitizer", _module_path)
response_sanitizer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(response_sanitizer)

sanitize_text = response_sanitizer.sanitize_text
sanitize = response_sanitizer.sanitize
PATTERNS = response_sanitizer.PATTERNS


class TestSanitizeOpenAIKey:
    """#34: OpenAI API key (sk-...) 脱敏."""

    def test_redacts_sk_key(self):
        text = "My key is sk-abcdefghijklmnopqrstuvwxyz1234567890"
        result = sanitize_text(text)
        assert "sk-abcdefghijklmnopqrstuvwxyz" not in result
        assert "sk-***REDACTED***" in result

    def test_redacts_sk_key_in_sentence(self):
        text = "Config: api_key=sk-abc123def456ghi789jkl012mno345pqr678"
        result = sanitize_text(text)
        assert "sk-abc123" not in result


class TestSanitizeAWSKey:
    """#34: AWS Access Key ID (AKIA...) 脱敏."""

    def test_redacts_aws_key(self):
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = sanitize_text(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "AKIA***REDACTED***" in result


class TestSanitizeGitHubPAT:
    """#34: GitHub Personal Access Token 脱敏."""

    def test_redacts_ghp_token(self):
        text = "GITHUB_TOKEN=ghp_0123456789abcdef0123456789abcdef0123456789"
        result = sanitize_text(text)
        assert "ghp_0123456789" not in result
        assert "ghp_***REDACTED***" in result

    def test_redacts_github_pat(self):
        text = "github_pat_0123456789abcdef0123456789abcdef"
        result = sanitize_text(text)
        assert "github_pat_0123" not in result
        assert "github_pat_***REDACTED***" in result


class TestSanitizeEmail:
    """#34: 邮箱脱敏."""

    def test_redacts_email(self):
        text = "Contact: user@example.com for details"
        result = sanitize_text(text)
        assert "user@example.com" not in result
        assert "***@***.***" in result

    def test_redacts_complex_email(self):
        text = "Send to john.doe+test@sub.domain.org"
        result = sanitize_text(text)
        assert "john.doe+test@sub.domain.org" not in result


class TestSanitizePhone:
    """#34: 中国手机号脱敏."""

    def test_redacts_phone(self):
        text = "Phone: 13812345678"
        result = sanitize_text(text)
        assert "13812345678" not in result
        assert "1**-****-***" in result

    def test_redacts_phone_in_sentence(self):
        text = "Call 15999998888 for support"
        result = sanitize_text(text)
        assert "15999998888" not in result


class TestSanitizePrivateKey:
    """#34: PEM 私钥块脱敏."""

    def test_redacts_rsa_private_key(self):
        text = """Here is the key:
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----
Use it carefully."""
        result = sanitize_text(text)
        assert "MIIEpAIBAAKCAQEA" not in result
        assert "-----PRIVATE KEY REDACTED-----" in result

    def test_redacts_ec_private_key(self):
        text = "-----BEGIN EC PRIVATE KEY-----\nMHQCAQEE\n-----END EC PRIVATE KEY-----"
        result = sanitize_text(text)
        assert "MHQCAQEE" not in result


class TestSanitizeNestedDict:
    """#34: 递归脱敏 dict."""

    def test_redacts_nested_dict(self):
        obj = {
            "a": {
                "b": "sk-abcdefghijklmnopqrstuvwxyz1234567890",
                "c": "normal text"
            },
            "d": ["email@test.com", "keep this"]
        }
        result = sanitize(obj)
        assert "sk-***REDACTED***" in result["a"]["b"]
        assert "***@***.***" in result["d"][0]
        assert result["a"]["c"] == "normal text"
        assert result["d"][1] == "keep this"

    def test_redacts_list_of_strings(self):
        obj = ["sk-abcdefghijklmnopqrstuvwxyz1234567890", "plain"]
        result = sanitize(obj)
        assert "sk-***REDACTED***" in result[0]
        assert result[1] == "plain"


class TestSanitizeKeepsNormalText:
    """#34: 普通文本不应被误杀."""

    def test_keeps_plain_text(self):
        text = "Hello world, this is a normal message."
        assert sanitize_text(text) == text

    def test_keeps_numbers(self):
        text = "Order #12345, total $99.99"
        assert sanitize_text(text) == text

    def test_keeps_url_without_credentials(self):
        text = "Visit https://example.com/path for more info"
        # URL 本身不应被脱敏 (没有匹配任何敏感模式)
        assert "https://example.com/path" in sanitize_text(text)

    def test_non_string_input_returned_as_is(self):
        assert sanitize_text(12345) == 12345
        assert sanitize_text(None) is None
        assert sanitize_text([1, 2, 3]) == [1, 2, 3]
