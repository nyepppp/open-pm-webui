"""
PM 工作流管理 Tool - Open WebUI Tool
提供项目工作流操作：获取下一步建议、进度统计、执行工作流
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
                else:
                    return {"error": f"Unsupported method: {method}"}
        except Exception as e:
            log.error(f"PM API request failed: {e}")
            return {"error": str(e)}

    async def get_next_steps(self, project_id: str, __user__: dict = None) -> str:
        """
        获取项目建议的下一步工作流步骤

        :param project_id: 项目 ID
        :return: JSON 格式的建议步骤列表
        """
        result = await self._request("GET", f"/pm/projects/{project_id}/workflow/next")
        return json.dumps(result, ensure_ascii=False)

    async def get_progress(self, project_id: str, __user__: dict = None) -> str:
        """
        获取项目进度统计信息

        :param project_id: 项目 ID
        :return: JSON 格式的进度统计
        """
        result = await self._request("GET", f"/pm/projects/{project_id}/workflow/progress")
        return json.dumps(result, ensure_ascii=False)

    async def execute_workflow(self, workflow_id: str, steps: list, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        执行工作流（需要确认）

        :param workflow_id: 工作流 ID
        :param steps: 要执行的工作流步骤列表
        :return: JSON 格式的执行结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "title": "确认执行工作流",
                "message": f"确定要执行工作流 {workflow_id} 吗？此操作将按顺序执行 {len(steps)} 个步骤。"
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了工作流执行"}, ensure_ascii=False)
        
        result = await self._request("POST", "/pm/agent/workflows/execute", {"id": workflow_id, "name": workflow_id, "steps": steps})
        return json.dumps(result, ensure_ascii=False)
