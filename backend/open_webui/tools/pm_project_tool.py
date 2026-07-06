"""
PM 项目管理 Tool - Open WebUI Tool
提供项目 CRUD 操作
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

    async def list_projects(self, __user__: dict = None) -> str:
        """
        列出当前用户的所有 PM 项目

        :return: JSON 格式的项目列表
        """
        result = await self._request("GET", "/pm/projects")
        return json.dumps(result, ensure_ascii=False)

    async def create_project(self, name: str, description: str = "", __user__: dict = None) -> str:
        """
        创建新的 PM 项目

        :param name: 项目名称
        :param description: 项目描述 (可选)
        :return: 创建的项目信息
        """
        result = await self._request("POST", "/pm/projects", {"name": name, "description": description})
        return json.dumps(result, ensure_ascii=False)

    async def get_project(self, project_id: str, __user__: dict = None) -> str:
        """
        获取指定项目的详细信息

        :param project_id: 项目 ID
        :return: 项目详情
        """
        result = await self._request("GET", f"/pm/projects/{project_id}")
        return json.dumps(result, ensure_ascii=False)

    async def update_project(self, project_id: str, name: str = None, description: str = None, status: str = None, __user__: dict = None) -> str:
        """
        更新项目信息

        :param project_id: 项目 ID
        :param name: 新项目名称 (可选)
        :param description: 新项目描述 (可选)
        :param status: 新项目状态 (可选: active/archived)
        :return: 更新后的项目信息
        """
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        result = await self._request("POST", f"/pm/projects/{project_id}", data)
        return json.dumps(result, ensure_ascii=False)

    async def delete_project(self, project_id: str, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        删除 PM 项目（需要确认）

        :param project_id: 要删除的项目 ID
        :return: 删除结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认删除项目",
                    "message": f"确定要删除项目 {project_id} 吗？此操作不可撤销。"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了删除操作"}, ensure_ascii=False)
        
        result = await self._request("DELETE", f"/pm/projects/{project_id}")
        return json.dumps(result, ensure_ascii=False)

    async def archive_project(self, project_id: str, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        归档 PM 项目（需要确认）

        :param project_id: 要归档的项目 ID
        :return: 归档结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认归档项目",
                    "message": f"确定要归档项目 {project_id} 吗？归档后项目将不再显示在列表中。"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了归档操作"}, ensure_ascii=False)
        
        result = await self._request("POST", f"/pm/projects/{project_id}", {"status": "archived"})
        return json.dumps(result, ensure_ascii=False)
