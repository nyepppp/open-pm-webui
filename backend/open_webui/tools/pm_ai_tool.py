"""
PM AI Tool - Open WebUI Tool
提供 AI 驱动的 PM 操作：条目分析、测试用例生成、质量检查、关系建议、PRD 生成
"""

import json
import logging
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


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
    pm_model: str = Field(
        default="gpt-4o",
        description="AI 模型名称 (可选，用于 AI 生成任务)"
    )


class Tools:
    def __init__(self):
        self.valves = Valves()

    async def _request(self, method: str, endpoint: str, data: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        """发送 HTTP 请求到 PM API"""
        url = f"{self.valves.pm_api_base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.valves.pm_api_key:
            headers["Authorization"] = f"Bearer {self.valves.pm_api_key}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status >= 400:
                            return {"error": f"API error {resp.status}", "detail": await resp.text()}
                        return await resp.json()
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data) as resp:
                        if resp.status >= 400:
                            return {"error": f"API error {resp.status}", "detail": await resp.text()}
                        return await resp.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers) as resp:
                        if resp.status >= 400:
                            return {"error": f"API error {resp.status}", "detail": await resp.text()}
                        return await resp.json()
                else:
                    return {"error": f"Unsupported HTTP method: {method}"}
        except Exception as e:
            log.error(f"PM API request failed: {e}")
            return {"error": str(e)}

    async def _emit_preview(self, content: str, __event_emitter__: callable = None):
        if __event_emitter__:
            await __event_emitter__({"type": "message", "data": {"content": content}})

    async def analyze_entry(self, entry_id: str, __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        分析需求条目（分类、优先级、冲突检测）

        :param entry_id: 条目 ID
        :param __event_emitter__: 事件发射器 (可选，用于预览分析结果)
        :return: 分析结果，包含分类、优先级建议和冲突信息
        """
        result = await self._request("POST", f"/pm/entries/{entry_id}/analyze")
        if "error" not in result and __event_emitter__:
            preview = result.get("content", result.get("analysis", json.dumps(result, ensure_ascii=False)))
            await self._emit_preview(f"**分析结果预览**\n\n{preview}", __event_emitter__)
        return json.dumps(result, ensure_ascii=False)

    async def generate_testcases(self, entry_id: str, __event_call__: callable = None, __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        从需求条目生成测试用例（预览后确认写入）

        :param entry_id: 条目 ID
        :param __event_call__: 事件回调 (可选，用于确认流程)
        :param __event_emitter__: 事件发射器 (可选，用于预览生成内容)
        :return: 生成的测试用例列表
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认生成测试用例",
                    "message": f"确定要为条目 {entry_id} 生成测试用例吗？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了生成操作"}, ensure_ascii=False)
        
        result = await self._request("POST", f"/pm/entries/{entry_id}/generate-testcases")

        if "error" not in result:
            preview_content = result.get("content", result.get("testcases", json.dumps(result, ensure_ascii=False)))
            await self._emit_preview(f"**测试用例预览**\n\n{preview_content}", __event_emitter__)
            if __event_call__:
                write_confirm = await __event_call__({
                    "type": "confirmation",
                    "data": {
                        "title": "确认写入测试用例",
                        "message": "以上测试用例将写入项目。确认写入？"
                    }
                })
                if not write_confirm:
                    return json.dumps({"status": "cancelled", "message": "用户取消了写入操作", "preview": result}, ensure_ascii=False)

        return json.dumps(result, ensure_ascii=False)

    async def check_entry(self, entry_id: str, __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        质量检查需求条目（完整性、一致性、可测试性）

        :param entry_id: 条目 ID
        :param __event_emitter__: 事件发射器 (可选，用于预览检查结果)
        :return: 质量检查结果，包含评分和改进建议
        """
        result = await self._request("POST", f"/pm/entries/{entry_id}/check")
        if "error" not in result and __event_emitter__:
            preview = result.get("content", result.get("report", json.dumps(result, ensure_ascii=False)))
            await self._emit_preview(f"**质量检查结果预览**\n\n{preview}", __event_emitter__)
        return json.dumps(result, ensure_ascii=False)

    async def suggest_relations(self, project_id: str, entry_id: str, __user__: dict = None) -> str:
        """
        为条目建议关联关系（基于实体关系图分析）

        :param project_id: 项目 ID
        :param entry_id: 条目 ID
        :return: 条目的关联关系列表
        """
        result = await self._request("GET", f"/pm/entries/{entry_id}/suggest-relations")
        return json.dumps(result, ensure_ascii=False)

    async def generate_prd(self, entry_id: str, instructions: str = "", __event_call__: callable = None, __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        生成 PRD 文档（预览后确认写入）

        :param entry_id: 条目 ID (基于该条目生成 PRD)
        :param instructions: 生成指令 (可选)
        :param __event_call__: 事件回调 (可选，用于确认流程)
        :param __event_emitter__: 事件发射器 (可选，用于预览生成内容)
        :return: 生成的 PRD 文档内容
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认生成 PRD",
                    "message": f"确定要为条目 {entry_id} 生成 PRD 文档吗？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了生成操作"}, ensure_ascii=False)
        
        data = {
            "module_type": "prd",
            "instructions": instructions
        }
        result = await self._request("POST", f"/pm/entries/{entry_id}/generate", data)

        if "error" not in result:
            preview_content = result.get("content", result.get("prd", json.dumps(result, ensure_ascii=False)))
            await self._emit_preview(f"**PRD 预览**\n\n{preview_content}", __event_emitter__)
            if __event_call__:
                write_confirm = await __event_call__({
                    "type": "confirmation",
                    "data": {
                        "title": "确认写入 PRD",
                        "message": "以上 PRD 内容将写入项目。确认写入？"
                    }
                })
                if not write_confirm:
                    return json.dumps({"status": "cancelled", "message": "用户取消了写入操作", "preview": result}, ensure_ascii=False)

        return json.dumps(result, ensure_ascii=False)

    async def extract_parameters(self, entry_id: str, __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        从条目中提取结构化参数（参数名、类型、默认值、描述等）

        :param entry_id: 条目 ID
        :param __event_emitter__: 事件发射器 (可选，用于预览提取结果)
        :return: 提取的参数列表
        """
        result = await self._request("POST", f"/pm/entries/{entry_id}/extract-parameters")
        if "error" not in result and __event_emitter__:
            preview = result.get("content", result.get("parameters", json.dumps(result, ensure_ascii=False)))
            await self._emit_preview(f"**参数提取结果预览**\n\n{preview}", __event_emitter__)
        return json.dumps(result, ensure_ascii=False)
