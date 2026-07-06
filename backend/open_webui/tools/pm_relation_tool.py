"""
PM 关系/追溯 Tool - Open WebUI Tool
提供项目内实体关系管理、影响分析和追溯链查询
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

    async def list_relations(self, project_id: str, __user__: dict = None) -> str:
        """
        列出指定项目中的所有关系

        :param project_id: 项目 ID
        :return: JSON 格式的关系列表
        """
        result = await self._request("GET", f"/pm/projects/{project_id}/relations")
        return json.dumps(result, ensure_ascii=False)

    async def create_relation(self, project_id: str, entity_a_id: str, entity_b_id: str, relation_type: str, confidence: int = 100, __user__: dict = None) -> str:
        """
        在项目中创建两个实体之间的关系

        :param project_id: 项目 ID
        :param entity_a_id: 实体 A ID
        :param entity_b_id: 实体 B ID
        :param relation_type: 关系类型
        :param confidence: 置信度 (0-100, 默认 100)
        :return: 创建的关系信息
        """
        data = {
            "entity_a_id": entity_a_id,
            "entity_b_id": entity_b_id,
            "relation_type": relation_type,
            "confidence": confidence
        }
        result = await self._request("POST", f"/pm/projects/{project_id}/relations", data)
        return json.dumps(result, ensure_ascii=False)

    async def delete_relation(self, relation_id: str, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        删除关系（需要确认）

        :param relation_id: 要删除的关系 ID
        :return: 删除结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认删除关系",
                    "message": f"确定要删除关系 {relation_id} 吗？此操作不可撤销。"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了删除操作"}, ensure_ascii=False)
        
        result = await self._request("DELETE", f"/pm/relations/{relation_id}")
        return json.dumps(result, ensure_ascii=False)

    async def get_impact_analysis(self, project_id: str, entity_id: str, __user__: dict = None) -> str:
        """
        获取指定实体的影响分析结果

        :param project_id: 项目 ID
        :param entity_id: 实体 ID
        :return: 影响分析结果
        """
        params = {"entity_id": entity_id}
        result = await self._request("GET", f"/pm/projects/{project_id}/traceability/impact", params=params)
        return json.dumps(result, ensure_ascii=False)

    async def get_trace_chain(self, project_id: str, entity_id: str, direction: str = "both", max_depth: int = 5, __user__: dict = None) -> str:
        """
        获取指定实体的追溯链

        :param project_id: 项目 ID
        :param entity_id: 实体 ID
        :param direction: 追溯方向 (both/forward/backward, 默认 both)
        :param max_depth: 最大深度 (默认 5)
        :return: 追溯链结果
        """
        params = {
            "entity_id": entity_id,
            "direction": direction,
            "max_depth": max_depth
        }
        result = await self._request("GET", f"/pm/projects/{project_id}/traceability/chain", params=params)
        return json.dumps(result, ensure_ascii=False)
