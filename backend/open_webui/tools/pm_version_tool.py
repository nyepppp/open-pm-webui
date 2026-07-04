"""
PM 版本管理 Tool - Open WebUI Tool
提供项目版本 CRUD 操作
"""

import json
import logging
from typing import Optional, Callable

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
                        return await resp.json()
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data) as resp:
                        return await resp.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers) as resp:
                        return await resp.json()
                else:
                    return {"error": f"Unsupported HTTP method: {method}"}
        except Exception as e:
            log.error(f"PM API request failed: {e}")
            return {"error": str(e)}

    async def list_versions(self, project_id: str, __user__: Optional[dict] = None) -> str:
        """
        列出指定项目的所有版本

        :param project_id: 项目 ID
        :return: JSON 格式的版本列表
        """
        result = await self._request("GET", f"/pm/projects/{project_id}/versions")
        return json.dumps(result, ensure_ascii=False)

    async def create_version(self, project_id: str, version_number: str, label: str = "", description: str = "", __event_call__: Optional[Callable] = None, __user__: Optional[dict] = None) -> str:
        """
        创建新的版本

        :param project_id: 项目 ID
        :param version_number: 版本号
        :param label: 版本标签 (可选)
        :param description: 版本描述 (可选)
        :return: 创建的版本信息
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "title": "确认创建版本",
                "message": f"确定要在项目 {project_id} 中创建版本 {version_number} 吗？"
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了创建操作"}, ensure_ascii=False)
        
        data = {
            "version_number": version_number,
            "label": label,
            "description": description
        }
        result = await self._request("POST", f"/pm/projects/{project_id}/versions", data)
        return json.dumps(result, ensure_ascii=False)

    async def get_version(self, project_id: str, entry_id: str, version_id: str, __user__: Optional[dict] = None) -> str:
        """
        获取指定版本的详细信息

        :param project_id: 项目 ID
        :param entry_id: 条目 ID
        :param version_id: 版本 ID
        :return: 版本详情
        """
        result = await self._request("GET", f"/pm/projects/{project_id}/entries/{entry_id}/versions/{version_id}")
        return json.dumps(result, ensure_ascii=False)

    async def switch_version(self, project_id: str, entry_id: str, version_id: str, __event_call__: Optional[Callable] = None, __user__: Optional[dict] = None) -> str:
        """
        切换条目到指定版本

        :param project_id: 项目 ID
        :param entry_id: 条目 ID
        :param version_id: 目标版本 ID
        :return: 切换结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "title": "确认切换版本",
                "message": f"确定要将条目 {entry_id} 切换到版本 {version_id} 吗？"
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了切换操作"}, ensure_ascii=False)
        
        result = await self._request("POST", f"/pm/projects/{project_id}/entries/{entry_id}/versions/{version_id}/switch")
        return json.dumps(result, ensure_ascii=False)

    async def compare_versions(self, project_id: str, entry_id: str, version_a: str, version_b: str, __user__: Optional[dict] = None) -> str:
        """
        比较两个版本的差异

        :param project_id: 项目 ID
        :param entry_id: 条目 ID
        :param version_a: 版本 A ID
        :param version_b: 版本 B ID
        :return: 版本差异对比结果
        """
        result = await self._request("GET", f"/pm/projects/{project_id}/entries/{entry_id}/versions/{version_a}/diff/{version_b}")
        return json.dumps(result, ensure_ascii=False)
