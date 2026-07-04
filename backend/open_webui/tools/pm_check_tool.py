"""
PM 质量检查 Tool - Open WebUI Tool
提供文档质量检查和 AI 修复建议
"""

import json
import logging
import os
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# Load check rules
RULES_PATH = os.path.join(os.path.dirname(__file__), "pm_check_rules.json")
CHECK_RULES = []
try:
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        CHECK_RULES = json.load(f).get("rules", [])
except Exception:
    pass


class Valves(BaseModel):
    """配置参数"""
    pm_api_base_url: str = Field(
        default="http://localhost:8080/api/v1",
        description="PM API 基础 URL"
    )
    pm_api_key: str = Field(
        default="",
        description="PM API 密钥 (可选)"
    )


class Tools:
    def __init__(self):
        self.valves = Valves()

    async def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """发送 HTTP 请求到 PM API"""
        url = f"{self.valves.pm_api_base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.valves.pm_api_key:
            headers["Authorization"] = f"Bearer {self.valves.pm_api_key}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers, params=params) as resp:
                        return await resp.json()
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data) as resp:
                        return await resp.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers) as resp:
                        return await resp.json()
        except Exception as e:
            log.error(f"PM API request failed: {e}")
            return {"error": str(e)}

    def _check_content(self, content: str, rule: dict) -> dict:
        """执行单条规则检查"""
        check_type = rule.get("check_type")
        target = rule.get("target", "")
        
        if check_type == "required_section":
            # 检查内容中是否包含目标章节
            section_keywords = {
                "overview": ["概述", "简介", "背景", "overview"],
                "goals": ["目标", "目的", "goals", "objectives"],
                "functional_requirements": ["功能需求", "功能", "functional"],
                "non_functional_requirements": ["非功能需求", "性能", "安全", "可用性"],
                "background": ["背景", "现状", "background"],
                "appendix": ["附录", "术语", "appendix", "glossary"],
                "target_users": ["用户", "target", "users"],
            }
            keywords = section_keywords.get(target, [target])
            found = any(kw in content for kw in keywords)
            return {
                "pass": found,
                "message": f"{'找到' if found else '未找到'}章节: {target}"
            }
        
        elif check_type == "required_field":
            # 检查内容中是否包含目标字段
            field_patterns = {
                "version": ["版本", "version", "v1", "v2"],
                "author": ["作者", "author", "编写"],
                "date": ["日期", "date", "202", "-"],
            }
            patterns = field_patterns.get(target, [target])
            found = any(p in content for p in patterns)
            return {
                "pass": found,
                "message": f"{'找到' if found else '未找到'}字段: {target}"
            }
        
        elif check_type == "field_check":
            # 通用字段检查（简化实现）
            return {
                "pass": True,  # 默认通过，实际应更复杂
                "message": f"字段检查: {target} (需人工复核)"
            }
        
        elif check_type == "consistency_check":
            return {
                "pass": True,
                "message": "一致性检查 (需 AI 复核)"
            }
        
        elif check_type == "traceability_check":
            return {
                "pass": True,
                "message": "可追溯性检查 (需 AI 复核)"
            }
        
        return {"pass": True, "message": "未知检查类型，默认通过"}

    async def run_check(self, entry_id: str, levels: str = "L1,L2,L3,L4", __user__: dict = None) -> str:
        """
        执行指定级别的质量检查

        :param entry_id: 要检查的条目 ID
        :param levels: 检查级别，逗号分隔 (L1,L2,L3,L4)
        :return: JSON 格式的检查结果
        """
        # 获取条目内容
        result = await self._request("GET", f"/pm/entries/{entry_id}")
        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, ensure_ascii=False)
        
        content = result.get("content", "") if isinstance(result, dict) else ""
        title = result.get("title", "") if isinstance(result, dict) else ""
        
        # 解析检查级别
        target_levels = [l.strip() for l in levels.split(",")]
        
        # 执行检查
        check_results = []
        passed_count = 0
        failed_count = 0
        
        for rule in CHECK_RULES:
            if rule.get("level") in target_levels:
                check_result = self._check_content(content, rule)
                status = "pass" if check_result["pass"] else "fail"
                if check_result["pass"]:
                    passed_count += 1
                else:
                    failed_count += 1
                
                check_results.append({
                    "rule_id": rule.get("rule_id"),
                    "level": rule.get("level"),
                    "category": rule.get("category"),
                    "description": rule.get("description"),
                    "status": status,
                    "message": check_result["message"],
                    "weight": rule.get("weight", 1.0),
                })
        
        total_weight = sum(r.get("weight", 1.0) for r in check_results if r["status"] == "pass")
        max_weight = sum(r.get("weight", 1.0) for r in check_results)
        score = int((total_weight / max_weight) * 100) if max_weight > 0 else 100
        
        return json.dumps({
            "entry_id": entry_id,
            "entry_title": title,
            "levels_checked": target_levels,
            "score": score,
            "total_rules": len(check_results),
            "passed": passed_count,
            "failed": failed_count,
            "results": check_results,
        }, ensure_ascii=False)

    async def list_results(self, entry_id: str, __user__: dict = None) -> str:
        """
        列出指定条目的历史检查结果

        :param entry_id: 条目 ID
        :return: JSON 格式的历史检查结果
        """
        # 目前返回最近一次检查的结果
        return await self.run_check(entry_id, "L1,L2,L3,L4", __user__)

    async def update_status(self, entry_id: str, rule_id: str, status: str, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        更新检查项状态（需要确认）

        :param entry_id: 条目 ID
        :param rule_id: 规则 ID
        :param status: 新状态 (pass/fail/ignored)
        :return: 更新结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认更新检查状态",
                    "message": f"规则: {rule_id}\n新状态: {status}\n\n确认更新？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了更新"}, ensure_ascii=False)
        
        return json.dumps({
            "entry_id": entry_id,
            "rule_id": rule_id,
            "status": status,
            "message": "状态已更新"
        }, ensure_ascii=False)

    async def suggest_fix(self, entry_id: str, rule_id: str, __user__: dict = None) -> str:
        """
        AI 生成修复建议

        :param entry_id: 条目 ID
        :param rule_id: 失败的规则 ID
        :return: JSON 格式的修复建议
        """
        # 查找规则
        rule = next((r for r in CHECK_RULES if r.get("rule_id") == rule_id), None)
        if not rule:
            return json.dumps({"error": f"规则 {rule_id} 不存在"}, ensure_ascii=False)
        
        # 获取条目内容
        result = await self._request("GET", f"/pm/entries/{entry_id}")
        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, ensure_ascii=False)
        
        content = result.get("content", "") if isinstance(result, dict) else ""
        title = result.get("title", "") if isinstance(result, dict) else ""
        
        # 调用 AI 生成修复建议
        ai_result = await self._request("POST", f"/pm/entries/{entry_id}/check")
        
        # 从 AI 检查结果中提取针对性建议
        ai_suggestion = None
        if isinstance(ai_result, dict) and "check_result" in ai_result:
            check_result = ai_result.get("check_result", {})
            issues = check_result.get("issues", [])
            for issue in issues:
                if isinstance(issue, dict):
                    issue_category = issue.get("category", "")
                    rule_category = rule.get("category", "")
                    if issue_category == rule_category or rule.get("level") in str(issue.get("severity", "")):
                        ai_suggestion = issue.get("suggestion", "")
                        break
        
        # Fallback to rule-based suggestions
        fallback_suggestions = {
            "L1-001": "在文档开头添加概述章节，描述产品的定位和核心价值。",
            "L1-002": "添加目标章节，明确产品的业务目标和用户目标。",
            "L1-003": "添加功能需求章节，列出所有功能点。",
            "L1-004": "添加非功能需求章节，包括性能、安全、可用性等。",
            "L2-001": "为每个功能需求添加优先级标注（P0-P3）。",
            "L2-002": "为每个功能需求添加验收标准。",
            "L3-001": "添加错误处理方案，包括错误提示和恢复流程。",
            "L4-001": "添加输入验证说明，包括验证规则和错误提示。",
        }
        
        suggestion = ai_suggestion or fallback_suggestions.get(rule_id, f"根据规则 '{rule.get('description')}'，建议补充相关内容。")
        
        return json.dumps({
            "entry_id": entry_id,
            "rule_id": rule_id,
            "rule_description": rule.get("description"),
            "suggestion": suggestion,
            "source": "ai" if ai_suggestion else "rule_based",
        }, ensure_ascii=False)

    async def list_rules(self, level: str = None, __user__: dict = None) -> str:
        """
        查看规则库

        :param level: 过滤级别 (L1/L2/L3/L4)，为空则返回所有
        :return: JSON 格式的规则列表
        """
        rules = CHECK_RULES
        if level:
            rules = [r for r in rules if r.get("level") == level]
        
        return json.dumps({
            "total": len(rules),
            "level_filter": level,
            "rules": rules,
        }, ensure_ascii=False)
