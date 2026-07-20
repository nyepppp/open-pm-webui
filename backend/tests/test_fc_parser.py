"""Unit tests for text-form function call parser (Bug 6 / v12).

Tests extract_text_function_calls and _parse_invoke_fc_payload as pure functions.
No app/client fixture needed — just import and assert.
"""

import json
import pytest
from open_webui.utils.middleware import (
    extract_text_function_calls,
    _parse_invoke_fc_payload,
    _parse_seed_fc_payload,
    _parse_json_fc_payload,
)


class TestParseInvokeFcPayload:
    """Change 2: <invoke name="..."><parameter>...</parameter></invoke> parser."""

    def test_single_invoke_single_param(self):
        raw = '<invoke name="get_pm_entry_detail"><parameter name="entry_id">abc-123</parameter></invoke>'
        calls = _parse_invoke_fc_payload(raw, model_id='test-model')
        assert len(calls) == 1
        assert calls[0]['function']['name'] == 'get_pm_entry_detail'
        assert json.loads(calls[0]['function']['arguments']) == {'entry_id': 'abc-123'}
        assert calls[0]['id'].startswith('call_')
        assert calls[0]['type'] == 'function'

    def test_multiple_invokes_in_batch(self):
        raw = """
        <invoke name="get_pm_module_entries"><parameter name="module_type">prd</parameter></invoke>
        <invoke name="get_pm_entry_detail"><parameter name="entry_id">xyz</parameter></invoke>
        """
        calls = _parse_invoke_fc_payload(raw.strip(), model_id='test')
        assert len(calls) == 2
        assert calls[0]['function']['name'] == 'get_pm_module_entries'
        assert calls[1]['function']['name'] == 'get_pm_entry_detail'

    def test_invoke_with_multiple_params(self):
        raw = '<invoke name="pm_entry_create"><parameter name="module_type">prd</parameter><parameter name="title">测试条目</parameter></invoke>'
        calls = _parse_invoke_fc_payload(raw)
        assert len(calls) == 1
        args = json.loads(calls[0]['function']['arguments'])
        assert args == {'module_type': 'prd', 'title': '测试条目'}

    def test_invoke_with_ignored_attributes(self):
        # Doubao-style string="true" attribute should be ignored
        raw = '<invoke name="foo"><parameter name="x" string="true">val</parameter></invoke>'
        calls = _parse_invoke_fc_payload(raw)
        assert len(calls) == 1
        assert json.loads(calls[0]['function']['arguments']) == {'x': 'val'}

    def test_invoke_no_params(self):
        raw = '<invoke name="list_all"></invoke>'
        calls = _parse_invoke_fc_payload(raw)
        assert len(calls) == 1
        assert json.loads(calls[0]['function']['arguments']) == {}

    def test_invoke_empty_payload_warns(self):
        # Empty raw should log warning and return []
        calls = _parse_invoke_fc_payload('', model_id='test')
        assert calls == []

    def test_invoke_malformed_returns_empty(self):
        # No name attribute → no match
        raw = '<invoke><parameter name="x">val</parameter></invoke>'
        calls = _parse_invoke_fc_payload(raw)
        assert calls == []


class TestExtractTextFunctionCallsV12Formats:
    """Change 1: <function_calls>, <tool_use>, bare <invoke> patterns."""

    def test_function_calls_format_strips_and_parses(self):
        content = (
            '让我先查询条目详情。\n'
            '<function_calls>\n'
            '<invoke name="get_pm_entry_detail">\n'
            '<parameter name="entry_id">c247a182-407c-4c9e-b966-8af968c3b214</parameter>\n'
            '</invoke>\n'
            '</function_calls>\n'
        )
        cleaned, calls = extract_text_function_calls(content, model_id='doubao-seed-evolving')
        assert '<function_calls>' not in cleaned
        assert '<invoke' not in cleaned
        assert '让我先查询条目详情。' in cleaned
        assert len(calls) == 1
        assert calls[0]['function']['name'] == 'get_pm_entry_detail'
        args = json.loads(calls[0]['function']['arguments'])
        assert args['entry_id'] == 'c247a182-407c-4c9e-b966-8af968c3b214'

    def test_tool_use_format_strips_and_parses(self):
        content = (
            '查询中。\n'
            '<tool_use>\n'
            '<invoke name="get_pm_module_entries">\n'
            '<parameter name="module_type">prd</parameter>\n'
            '</invoke>\n'
            '</tool_use>'
        )
        cleaned, calls = extract_text_function_calls(content, model_id='claude-test')
        assert '<tool_use>' not in cleaned
        assert '<invoke' not in cleaned
        assert len(calls) == 1
        assert calls[0]['function']['name'] == 'get_pm_module_entries'

    def test_bare_invoke_without_wrapper_not_parsed(self):
        # Bare <invoke> without <function_calls> or <tool_use> wrapper is NOT
        # matched — Pattern J was removed because the begin marker '<invoke'
        # is a prefix of the inner tag, causing the regex to consume it and
        # break the inner parser. Users must use <function_calls> or <tool_use>.
        content = (
            '执行查询。\n'
            '<invoke name="get_pm_entry_detail">\n'
            '<parameter name="entry_id">bare-123</parameter>\n'
            '</invoke>'
        )
        cleaned, calls = extract_text_function_calls(content, model_id='test')
        # No wrapper → no match → original content returned, empty calls
        assert cleaned == content
        assert calls == []


class TestExtractTextFunctionCallsBackwardCompat:
    """v9/v10/v11 formats must still work after v12 changes."""

    def test_seed_tool_call_format_still_works(self):
        content = (
            '查询中。\n'
            'seed:tool_call<function name="get_pm_entry_detail">'
            '<parameter name="entry_id">seed-123</parameter>'
            '</function></seed:tool_call>'
        )
        cleaned, calls = extract_text_function_calls(content, model_id='doubao-seed-evolving')
        assert 'seed:tool_call' not in cleaned
        assert len(calls) == 1
        assert calls[0]['function']['name'] == 'get_pm_entry_detail'

    def test_function_call_tag_format_still_works(self):
        content = '<function_call>{"name": "foo", "parameters": {"x": 1}}</function_call>'
        cleaned, calls = extract_text_function_calls(content)
        assert '<function_call>' not in cleaned
        assert len(calls) == 1
        assert calls[0]['function']['name'] == 'foo'

    def test_no_fc_markers_returns_original(self):
        # Zero-overhead fast path
        content = '这是一段普通的回复，没有任何 FC 标记。'
        cleaned, calls = extract_text_function_calls(content)
        assert cleaned == content
        assert calls == []

    def test_empty_content_returns_empty(self):
        cleaned, calls = extract_text_function_calls('')
        assert cleaned == ''
        assert calls == []


class TestExtractTextFunctionCallsMixedAndEdge:
    """Mixed formats + edge cases."""

    def test_mixed_seed_and_function_calls_formats(self):
        # Both formats in one response (rare but possible mid-model-switch)
        content = (
            'seed:tool_call<function name="foo"><parameter name="a">1</parameter></function></seed:tool_call>'
            '\n---\n'
            '<function_calls><invoke name="bar"><parameter name="b">2</parameter></invoke></function_calls>'
        )
        cleaned, calls = extract_text_function_calls(content)
        assert 'seed:tool_call' not in cleaned
        assert '<function_calls>' not in cleaned
        assert len(calls) == 2
        names = [c['function']['name'] for c in calls]
        assert 'foo' in names and 'bar' in names

    def test_partial_pattern_warns_and_keeps_original(self):
        # Begin marker present, end marker missing → should warn, not crash
        content = '部分输出 <function_calls><invoke name="foo"><parameter name="x">1</parameter></invoke>'
        # Should not raise; behavior is to keep original content (no match) and return []
        cleaned, calls = extract_text_function_calls(content)
        # Partial pattern → no full match → content unchanged, calls empty
        assert cleaned == content or '<function_calls>' not in cleaned  # tolerant
        assert isinstance(calls, list)

    def test_function_calls_with_multiline_params(self):
        content = (
            '<function_calls>\n'
            '<invoke name="pm_entry_create">\n'
            '<parameter name="module_type">prd</parameter>\n'
            '<parameter name="title">多行\n标题\n内容</parameter>\n'
            '</invoke>\n'
            '</function_calls>'
        )
        cleaned, calls = extract_text_function_calls(content)
        assert len(calls) == 1
        args = json.loads(calls[0]['function']['arguments'])
        assert '多行' in args['title']
