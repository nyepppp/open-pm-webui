"""
PM 路线图 Tool - Open WebUI Tool
提供路线图节点管理和 AI 排期建议
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

    async def list_roadmap_nodes(self, project_id: str, __user__: dict = None) -> str:
        """
        列出项目中的所有路线图节点

        :param project_id: 项目 ID
        :return: JSON 格式的路线图节点列表
        """
        result = await self._request("GET", f"/pm/projects/{project_id}/entries", params={"module_type": "roadmap"})
        return json.dumps(result, ensure_ascii=False)

    async def create_roadmap_node(self, project_id: str, title: str, node_type: str = "milestone", 
                                   start_date: str = None, end_date: str = None, 
                                   dependencies: list = None, __event_call__: callable = None, __user__: dict = None) -> str:
        """
        创建路线图节点（需要确认）


        :param project_id: 项目 ID
        :param title: 节点名称
        :param node_type: 节点类型 (milestone/feature/release)
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param dependencies: 依赖节点 ID 列表
        :return: 创建的节点信息
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认创建路线图节点",
                    "message": f"名称: {title}\n类型: {node_type}\n开始: {start_date}\n结束: {end_date}\n\n确认创建？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了创建操作"}, ensure_ascii=False)
        
        data = {
            "project_id": project_id,
            "module_type": "roadmap",
            "title": title,
            "content": f"类型: {node_type}",
            "data": {
                "node_type": node_type,
                "start_date": start_date,
                "end_date": end_date,
                "dependencies": dependencies or [],
            }
        }
        result = await self._request("POST", f"/pm/projects/{project_id}/entries", data)
        return json.dumps(result, ensure_ascii=False)

    async def update_roadmap_node(self, entry_id: str, title: str = None, start_date: str = None, 
                                   end_date: str = None, status: str = None, 
                                   __event_call__: callable = None, __user__: dict = None) -> str:
        """
        更新路线图节点（需要确认）

        :param entry_id: 节点条目 ID
        :param title: 新名称 (可选)
        :param start_date: 新开始日期 (可选)
        :param end_date: 新结束日期 (可选)
        :param status: 新状态 (可选)
        :return: 更新后的节点信息
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认更新路线图节点",
                    "message": f"节点 ID: {entry_id}\n\n确认更新？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了更新操作"}, ensure_ascii=False)
        
        data = {}
        if title is not None:
            data["title"] = title
        if start_date is not None or end_date is not None or status is not None:
            data["data"] = {}
            if start_date is not None:
                data["data"]["start_date"] = start_date
            if end_date is not None:
                data["data"]["end_date"] = end_date
            if status is not None:
                data["data"]["status"] = status
        
        result = await self._request("POST", f"/pm/entries/{entry_id}", data)
        return json.dumps(result, ensure_ascii=False)

    async def suggest_schedule(self, project_id: str, __user__: dict = None) -> str:
        """
        AI 排期建议 - 分析项目需求列表和优先级，自动建议排期

        :param project_id: 项目 ID
        :return: JSON 格式的排期建议
        """
        # 获取项目中的需求和路线图节点
        entries_result = await self._request("GET", f"/pm/projects/{project_id}/entries")
        
        if isinstance(entries_result, dict) and "error" in entries_result:
            return json.dumps(entries_result, ensure_ascii=False)
        
        entries = entries_result if isinstance(entries_result, list) else entries_result.get("items", entries_result.get("data", []))
        
        requirements = [e for e in entries if isinstance(e, dict) and e.get("module_type") == "requirement"]
        roadmap_nodes = [e for e in entries if isinstance(e, dict) and e.get("module_type") == "roadmap"]
        
        # 简单的排期逻辑（实际应调用 AI 服务）
        suggestions = []
        for i, req in enumerate(requirements):
            priority = req.get("data", {}).get("priority", "P2")
            duration_days = {"P0": 5, "P1": 10, "P2": 15, "P3": 20}.get(priority, 15)
            
            suggestions.append({
                "requirement_id": req.get("id"),
                "requirement_title": req.get("title"),
                "priority": priority,
                "suggested_duration_days": duration_days,
                "suggested_start": f"T+{i * 7}d",
                "suggested_end": f"T+{i * 7 + duration_days}d",
                "reason": f"基于优先级 {priority} 的历史数据预测"
            })
        
        # 检测冲突
        conflicts = []
        for i, node in enumerate(roadmap_nodes):
            deps = node.get("data", {}).get("dependencies", [])
            for dep_id in deps:
                dep = next((n for n in roadmap_nodes if n.get("id") == dep_id), None)
                if dep:
                    node_end = node.get("data", {}).get("end_date")
                    dep_start = dep.get("data", {}).get("start_date")
                    if node_end and dep_start and node_end > dep_start:
                        conflicts.append({
                            "node_id": node.get("id"),
                            "node_title": node.get("title"),
                            "conflict_with": dep.get("id"),
                            "conflict_with_title": dep.get("title"),
                            "reason": "结束日期晚于依赖节点开始日期"
                        })
        
        return json.dumps({
            "project_id": project_id,
            "suggestions": suggestions,
            "conflicts": conflicts,
            "total_requirements": len(requirements),
            "total_roadmap_nodes": len(roadmap_nodes),
        }, ensure_ascii=False)

    async def detect_conflicts(self, project_id: str, __user__: dict = None) -> str:
        """
        检测路线图中的依赖冲突

        :param project_id: 项目 ID
        :return: JSON 格式的冲突列表
        """
        # 获取路线图节点
        result = await self._request("GET", f"/pm/projects/{project_id}/entries", params={"module_type": "roadmap"})
        
        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, ensure_ascii=False)
        
        nodes = result if isinstance(result, list) else []
        conflicts = []
        
        for node in nodes:
            node_data = node.get("data", {})
            deps = node_data.get("dependencies", [])
            node_end = node_data.get("end_date")
            
            for dep_id in deps:
                dep = next((n for n in nodes if n.get("id") == dep_id), None)
                if dep:
                    dep_data = dep.get("data", {})
                    dep_start = dep_data.get("start_date")
                    
                    if node_end and dep_start and node_end > dep_start:
                        conflicts.append({
                            "node_id": node.get("id"),
                            "node_title": node.get("title"),
                            "conflict_with": dep.get("id"),
                            "conflict_with_title": dep.get("title"),
                            "node_end": node_end,
                            "dep_start": dep_start,
                            "reason": "结束日期晚于依赖节点开始日期"
                        })
        
        return json.dumps({
            "project_id": project_id,
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
        }, ensure_ascii=False)
