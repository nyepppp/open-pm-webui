"""
PM 条目管理 Tool - Open WebUI Tool
提供条目 CRUD 操作
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
            return {"error": "Unsupported HTTP method"}
        except Exception as e:
            log.error(f"PM API request failed: {e}")
            return {"error": str(e)}

    async def list_entries(self, project_id: str, module_type: str = None, status: str = None, priority: str = None, search: str = None, __user__: dict = None) -> str:
        """
        列出指定项目下的条目列表，支持多种过滤条件

        :param project_id: 项目 ID
        :param module_type: 模块类型过滤 (可选)
        :param status: 状态过滤 (可选)
        :param priority: 优先级过滤 (可选)
        :param search: 搜索关键词 (可选)
        :return: JSON 格式的条目列表
        """
        params = {}
        if module_type is not None:
            params["module_type"] = module_type
        if status is not None:
            params["status"] = status
        if priority is not None:
            params["priority"] = priority
        if search is not None:
            params["search"] = search
        
        result = await self._request("GET", f"/pm/projects/{project_id}/entries", params=params)
        return json.dumps(result, ensure_ascii=False)

    async def create_entry(self, project_id: str, module_type: str, title: str, content: str = "", data: dict = None, status: str = "draft", priority: str = None, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        在指定项目下创建新条目（需确认）

        :param project_id: 项目 ID
        :param module_type: 模块类型
        :param title: 条目标题
        :param content: 条目内容 (可选)
        :param data: 附加数据 (可选)
        :param status: 条目状态 (可选，默认: draft)
        :param priority: 优先级 (可选)
        :param __event_call__: 事件回调 (可选，用于确认流程)
        :return: 创建的条目信息
        """
        if __event_call__:
            summary = f"标题: {title}\n模块类型: {module_type}\n状态: {status}"
            if priority:
                summary += f"\n优先级: {priority}"
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认创建条目",
                    "message": f"{summary}\n\n确认创建？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了创建操作"}, ensure_ascii=False)

        payload = {
            "project_id": project_id,
            "module_type": module_type,
            "title": title,
            "content": content,
            "status": status
        }
        if data is not None:
            payload["data"] = data
        if priority is not None:
            payload["priority"] = priority
        
        result = await self._request("POST", f"/pm/projects/{project_id}/entries", payload)
        return json.dumps(result, ensure_ascii=False)

    async def get_entry(self, entry_id: str, __user__: dict = None) -> str:
        """
        获取指定条目的详细信息

        :param entry_id: 条目 ID
        :return: 条目详情
        """
        result = await self._request("GET", f"/pm/entries/{entry_id}")
        return json.dumps(result, ensure_ascii=False)

    async def update_entry(self, entry_id: str, title: str = None, content: str = None, data: dict = None, status: str = None, priority: str = None, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        更新指定条目的信息（需确认）

        :param entry_id: 条目 ID
        :param title: 新标题 (可选)
        :param content: 新内容 (可选)
        :param data: 附加数据 (可选)
        :param status: 新状态 (可选)
        :param priority: 新优先级 (可选)
        :param __event_call__: 事件回调 (可选，用于确认流程)
        :return: 更新后的条目信息
        """
        if __event_call__:
            changes = []
            if title is not None:
                changes.append(f"标题 → {title}")
            if content is not None:
                changes.append(f"内容 → (已更新)")
            if status is not None:
                changes.append(f"状态 → {status}")
            if priority is not None:
                changes.append(f"优先级 → {priority}")
            if data is not None:
                changes.append("附加数据 → (已更新)")
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认更新条目",
                    "message": f"条目 {entry_id} 变更:\n{chr(10).join(changes)}\n\n确认更新？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了更新操作"}, ensure_ascii=False)
        payload = {}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if data is not None:
            payload["data"] = data
        if status is not None:
            payload["status"] = status
        if priority is not None:
            payload["priority"] = priority
        
        result = await self._request("POST", f"/pm/entries/{entry_id}", payload)
        return json.dumps(result, ensure_ascii=False)

    async def delete_entry(self, entry_id: str, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        删除指定条目（需要确认）

        :param entry_id: 要删除的条目 ID
        :return: 删除结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "title": "确认删除条目",
                "message": f"确定要删除条目 {entry_id} 吗？此操作不可撤销。"
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了删除操作"}, ensure_ascii=False)
        
        result = await self._request("DELETE", f"/pm/entries/{entry_id}")
        return json.dumps(result, ensure_ascii=False)

    async def search_entries(self, project_id: str, q: str, module_type: str = None, status: str = None, priority: str = None, limit: int = 50, __user__: dict = None) -> str:
        """
        在指定项目下全文搜索条目

        :param project_id: 项目 ID
        :param q: 搜索关键词
        :param module_type: 模块类型过滤 (可选)
        :param status: 状态过滤 (可选)
        :param priority: 优先级过滤 (可选)
        :param limit: 返回结果数量限制 (可选，默认: 50)
        :return: JSON 格式的搜索结果列表
        """
        params = {"q": q, "limit": limit}
        if module_type is not None:
            params["module_type"] = module_type
        if status is not None:
            params["status"] = status
        if priority is not None:
            params["priority"] = priority
        
        result = await self._request("GET", f"/pm/projects/{project_id}/entries/search", params=params)
        return json.dumps(result, ensure_ascii=False)

    async def get_entry_versions(self, entry_id: str, __user__: dict = None) -> str:
        """
        获取指定条目的版本历史

        :param entry_id: 条目 ID
        :return: JSON 格式的版本列表
        """
        result = await self._request("GET", f"/pm/entries/{entry_id}/versions")
        return json.dumps(result, ensure_ascii=False)

    async def create_entry_version(self, entry_id: str, version_number: str = None, change_summary: str = "", __user__: dict = None) -> str:
        """
        为指定条目创建新版本

        :param entry_id: 条目 ID
        :param version_number: 版本号 (可选)
        :param change_summary: 变更摘要 (可选)
        :return: 创建的版本信息
        """
        payload = {}
        if version_number is not None:
            payload["version_number"] = version_number
        if change_summary:
            payload["change_summary"] = change_summary
        
        result = await self._request("POST", f"/pm/entries/{entry_id}/versions", payload)
        return json.dumps(result, ensure_ascii=False)

    async def interactive_create_entry(self, project_id: str, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        交互式创建条目：逐步收集参数后确认创建

        :param project_id: 项目 ID
        :param __event_call__: 事件回调 (用于参数收集和确认)
        :return: 创建的条目信息
        """
        title = ""
        module_type = "requirement"
        priority = "P2"

        if __event_call__:
            title_result = await __event_call__({
                "type": "input",
                "data": {"title": "需求标题", "message": "请输入需求标题", "placeholder": "例如：用户登录功能"}
            })
            if title_result:
                title = str(title_result)

            module_result = await __event_call__({
                "type": "input",
                "data": {"title": "模块类型", "message": "请选择模块类型", "placeholder": "requirement/prd/spec/testcase"}
            })
            if module_result:
                module_type = str(module_result)

            priority_result = await __event_call__({
                "type": "input",
                "data": {"title": "优先级", "message": "请选择优先级（P0-P3）", "placeholder": "P2"}
            })
            if priority_result:
                priority = str(priority_result)

            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认创建",
                    "message": f"标题: {title}\n模块类型: {module_type}\n优先级: {priority}\n\n确认创建？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了创建操作"}, ensure_ascii=False)

        payload = {
            "project_id": project_id,
            "module_type": module_type,
            "title": title,
            "content": "",
            "status": "draft",
            "priority": priority
        }
        result = await self._request("POST", f"/pm/projects/{project_id}/entries", payload)
        return json.dumps(result, ensure_ascii=False)
