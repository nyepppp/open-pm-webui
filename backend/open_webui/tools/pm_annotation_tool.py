"""
PM Annotation Tool - Open WebUI Tool
提供标注生成和管理功能
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
                elif method.upper() == "PUT":
                    async with session.put(url, headers=headers, json=data) as resp:
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

    async def generate_annotation(
        self, 
        entry_id: str, 
        annotation_type: str = "prototype",
        format_template: str = None,
        __event_emitter__: callable = None,
        __user__: dict = None
    ) -> str:
        """
        基于 PM 条目数据生成标注文本

        :param entry_id: 条目 ID
        :param annotation_type: 标注类型 (prototype/requirement/spec/feature)
        :param format_template: 格式模板 (可选，使用默认模板)
        :param __event_emitter__: 事件发射器 (可选，用于预览生成内容)
        :return: 生成的标注文本
        """
        # 获取条目详情
        entry_result = await self._request("GET", f"/pm/entries/{entry_id}")
        if "error" in entry_result:
            return json.dumps({"error": "Failed to fetch entry data", "detail": entry_result}, ensure_ascii=False)
        
        entry = entry_result.get("entry", entry_result)
        
        # 获取条目关联的需求和 SPEC
        project_id = entry.get("project_id")
        related_entries = await self._request("GET", f"/pm/projects/{project_id}/entries", params={"module_type": "requirement"})
        
        # 构建标注文本
        default_template = """# {title} 标注

## 基本信息
- **条目 ID**: {entry_id}
- **模块类型**: {module_type}
- **状态**: {status}
- **优先级**: {priority}

## 需求描述
{content}

## 功能参数
{parameters}

## 关联需求
{related_requirements}

## 默认值
{default_values}

## 边界条件
{boundary_conditions}
"""
        
        template = format_template or default_template
        
        # 提取参数信息
        data = entry.get("data", {})
        parameters = data.get("parameters", [])
        param_text = "\n".join([f"- **{p.get('name', '')}**: {p.get('description', '')} (默认值: {p.get('default', 'N/A')})" for p in parameters]) if parameters else "无参数"
        
        # 提取关联需求
        related_reqs = []
        if isinstance(related_entries, list):
            for req in related_entries[:3]:  # 最多取3个
                related_reqs.append(f"- {req.get('title', '')}: {req.get('content', '')[:100]}...")
        related_text = "\n".join(related_reqs) if related_reqs else "无关联需求"
        
        # 生成标注文本
        annotation_text = template.format(
            title=entry.get("title", "未命名"),
            entry_id=entry_id,
            module_type=entry.get("module_type", "未知"),
            status=entry.get("status", "未知"),
            priority=entry.get("priority", "未设置"),
            content=entry.get("content", "无内容"),
            parameters=param_text,
            related_requirements=related_text,
            default_values=data.get("defaults", "未设置"),
            boundary_conditions=data.get("boundaries", "未设置")
        )
        
        if __event_emitter__:
            await self._emit_preview(f"**标注生成预览**\n\n{annotation_text}", __event_emitter__)
        
        return json.dumps({
            "content": annotation_text,
            "format": "markdown",
            "entry_id": entry_id,
            "annotation_type": annotation_type
        }, ensure_ascii=False)

    async def save_annotation(
        self,
        entry_id: str,
        content: str,
        annotation_type: str = "prototype",
        project_id: str = None,
        __event_emitter__: callable = None,
        __user__: dict = None
    ) -> str:
        """
        保存标注到 PM 数据库

        :param entry_id: 条目 ID
        :param content: 标注内容
        :param annotation_type: 标注类型
        :param project_id: 项目 ID (可选，如果未提供会尝试从条目获取)
        :param __event_emitter__: 事件发射器
        :return: 保存结果
        """
        if not project_id:
            entry_result = await self._request("GET", f"/pm/entries/{entry_id}")
            if "error" not in entry_result:
                entry = entry_result.get("entry", entry_result)
                project_id = entry.get("project_id")
        
        data = {
            "entry_id": entry_id,
            "project_id": project_id,
            "annotation_type": annotation_type,
            "content": content,
            "source_data": {"generated_by": "ai", "timestamp": __user__.get("created_at") if __user__ else None}
        }
        
        result = await self._request("POST", f"/pm/entries/{entry_id}/annotations", data)
        
        if "error" not in result and __event_emitter__:
            await self._emit_preview("**标注已保存**\n\n标注内容已成功保存到 PM 工作台。", __event_emitter__)
        
        return json.dumps(result, ensure_ascii=False)

    async def list_annotations(
        self,
        project_id: str,
        entry_id: str = None,
        annotation_type: str = None,
        __user__: dict = None
    ) -> str:
        """
        查询项目的标注列表

        :param project_id: 项目 ID
        :param entry_id: 条目 ID (可选，用于过滤)
        :param annotation_type: 标注类型 (可选，用于过滤)
        :return: 标注列表
        """
        params = {}
        if annotation_type:
            params["annotation_type"] = annotation_type
        
        if entry_id:
            result = await self._request("GET", f"/pm/entries/{entry_id}/annotations", params=params)
        else:
            result = await self._request("GET", f"/pm/projects/{project_id}/annotations", params=params)
        
        return json.dumps(result, ensure_ascii=False)

    async def copy_annotation(
        self,
        annotation_id: str,
        __event_emitter__: callable = None,
        __user__: dict = None
    ) -> str:
        """
        获取标注内容并返回可复制格式

        :param annotation_id: 标注 ID
        :param __event_emitter__: 事件发射器
        :return: 标注内容 (Markdown 格式)
        """
        result = await self._request("GET", f"/pm/annotations/{annotation_id}")
        
        if "error" in result:
            return json.dumps({"error": "Failed to fetch annotation", "detail": result}, ensure_ascii=False)
        
        annotation = result.get("annotation", result)
        content = annotation.get("content", "")
        
        if __event_emitter__:
            await self._emit_preview(f"**标注内容 (已复制)**\n\n{content}", __event_emitter__)
        
        return json.dumps({
            "content": content,
            "format": "markdown",
            "annotation_id": annotation_id,
            "copied": True
        }, ensure_ascii=False)