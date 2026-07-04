"""
PM 跨模块流转 Tool - Open WebUI Tool
Thin wrapper that delegates to PM flow API endpoints.
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


class Tools:
    def __init__(self):
        self.valves = Valves()

    async def _request(self, method: str, endpoint: str, data: dict | None = None, params: dict | None = None) -> dict:
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
                else:
                    return {}
        except Exception as e:
            log.error(f"PM API request failed: {e}")
            return {"error": str(e)}

    async def list_templates(self, project_id: str = "", __user__: dict | None = None) -> str:
        """
        列出可用的流转模板

        :param project_id: 项目 ID（用于查询自定义模板）
        :return: JSON 格式的模板列表
        """
        params = {}
        if project_id:
            params["project_id"] = project_id

        result = await self._request("GET", "/pm/flow/templates", params=params)
        return json.dumps(result, ensure_ascii=False)

    async def preview_flow(self, template_id: str, source_entry_ids: str, project_id: str, __user__: dict | None = None) -> str:
        """
        预览流转结果（不写入）

        :param template_id: 流转模板 ID
        :param source_entry_ids: 源条目 ID 列表，逗号分隔
        :param project_id: 项目 ID
        :return: JSON 格式的预览结果
        """
        entry_ids = [eid.strip() for eid in source_entry_ids.split(",") if eid.strip()]
        data = {
            "template_id": template_id,
            "source_entry_ids": entry_ids,
            "project_id": project_id,
        }
        result = await self._request("POST", "/pm/flow/preview", data=data)
        return json.dumps(result, ensure_ascii=False)

    async def execute_flow(self, template_id: str, source_entry_ids: str, project_id: str,
                           __event_call__=None, __user__=None) -> str:
        """
        执行流转模板（需要确认）

        :param template_id: 流转模板 ID
        :param source_entry_ids: 源条目 ID 列表，逗号分隔
        :param project_id: 项目 ID
        :return: JSON 格式的执行结果
        """
        entry_ids = [eid.strip() for eid in source_entry_ids.split(",") if eid.strip()]

        # Preview first
        preview_data = {
            "template_id": template_id,
            "source_entry_ids": entry_ids,
            "project_id": project_id,
        }
        preview = await self._request("POST", "/pm/flow/preview", data=preview_data)

        # Confirm via event_call
        if __event_call__:
            template_name = preview.get("template_name", template_id)
            estimated = json.dumps(preview.get("estimated_outputs", []), ensure_ascii=False)
            source_titles = ", ".join([e.get("title", "") for e in preview.get("source_entries", [])])
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": f"确认执行流转: {template_name}",
                    "message": f"模板: {template_name}\n源条目: {source_titles}\n预计输出: {estimated}\n\n确认执行？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了流转"}, ensure_ascii=False)

        # Execute
        execute_data = {
            "template_id": template_id,
            "source_entry_ids": entry_ids,
            "project_id": project_id,
            "confirmed": True,
        }
        result = await self._request("POST", "/pm/flow/execute", data=execute_data)
        return json.dumps(result, ensure_ascii=False)

    async def create_template(self, name: str, description: str, input_module: str, output_module: str,
                              steps: str, project_id: str = "",
                              __event_call__=None, __user__=None) -> str:
        """
        创建自定义流转模板（需要确认）

        :param name: 模板名称
        :param description: 模板描述
        :param input_module: 输入模块类型
        :param output_module: 输出模块类型
        :param steps: 流转步骤列表 JSON 字符串
        :param project_id: 项目 ID
        :return: JSON 格式的创建结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认创建流转模板",
                    "message": f"名称: {name}\n描述: {description}\n输入: {input_module}\n输出: {output_module}\n步骤: {steps}\n项目: {project_id}\n\n确认创建？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了创建"}, ensure_ascii=False)

        # Parse steps from JSON string
        try:
            parsed_steps = json.loads(steps) if isinstance(steps, str) else steps
        except Exception:
            parsed_steps = [{"action": "custom", "description": steps}]

        data = {
            "name": name,
            "description": description,
            "input_module": input_module,
            "output_module": output_module,
            "steps": parsed_steps,
            "project_id": project_id,
        }
        result = await self._request("POST", "/pm/flow/templates", data=data)
        return json.dumps(result, ensure_ascii=False)
