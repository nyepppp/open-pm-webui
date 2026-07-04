"""
PM 导入导出 Tool - Open WebUI Tool
提供数据导入导出操作
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

    async def _emit_preview(self, content: str, __event_emitter__: callable = None):
        if __event_emitter__:
            await __event_emitter__({"type": "message", "data": {"content": content}})

    def _parse_import_preview(self, data: str, export_format: str) -> str:
        try:
            if export_format == "json":
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    count = len(parsed)
                    columns = list(parsed[0].keys()) if parsed else []
                    sample = parsed[:2]
                elif isinstance(parsed, dict):
                    items = parsed.get("items", parsed.get("entries", [parsed]))
                    count = len(items)
                    columns = list(items[0].keys()) if items else []
                    sample = items[:2]
                else:
                    return f"数据预览: {str(data)[:200]}"
                return f"数据预览:\n- 记录数: {count}\n- 列名: {', '.join(columns)}\n- 示例:\n{json.dumps(sample, ensure_ascii=False, indent=2)}"
            elif export_format == "csv":
                lines = data.strip().split("\n")
                total_lines = len(lines) - 1
                header = lines[0] if lines else ""
                sample_lines = lines[1:3]
                return f"数据预览:\n- 行数: {total_lines}\n- 列名: {header}\n- 示例:\n" + "\n".join(sample_lines)
            else:
                return f"数据预览 ({len(data)} 字符):\n{data[:300]}"
        except Exception:
            return f"数据预览 (原始):\n{data[:300]}"

    async def import_entries(self, project_id: str, module_type: str, format: str, data: str, __event_call__: callable = None, __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        导入条目数据到指定项目（预览后确认导入）

        :param project_id: 项目 ID
        :param module_type: 模块类型
        :param format: 导入格式 (json/csv)
        :param data: 要导入的数据内容
        :param __event_call__: 事件回调 (可选，用于确认流程)
        :param __event_emitter__: 事件发射器 (可选，用于预览数据)
        :return: 导入结果
        """
        preview = self._parse_import_preview(data, format)
        await self._emit_preview(f"**导入数据预览**\n\n{preview}", __event_emitter__)

        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认导入数据",
                    "message": f"预览数据已展示。确认导入到项目 {project_id} 的 {module_type} 模块？此操作可能会覆盖现有数据。"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了导入操作"}, ensure_ascii=False)
        
        request_data = {
            "module_type": module_type,
            "format": format,
            "data": data
        }
        result = await self._request("POST", f"/pm/projects/{project_id}/entries/import", request_data)
        return json.dumps(result, ensure_ascii=False)

    async def export_entry(self, entry_id: str, format: str = "json", __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        导出指定条目数据

        :param entry_id: 条目 ID
        :param format: 导出格式 (json/markdown/csv)
        :param __event_emitter__: 事件发射器 (可选，用于预览导出内容)
        :return: 导出的数据内容
        """
        params = {"format": format}
        result = await self._request("GET", f"/pm/entries/{entry_id}/export", params=params)
        if "error" not in result and __event_emitter__:
            preview_content = result.get("content", json.dumps(result, ensure_ascii=False))
            await self._emit_preview(f"**导出预览**\n\n{str(preview_content)[:500]}", __event_emitter__)
        return json.dumps(result, ensure_ascii=False)

    async def extract_parameters(self, entry_id: str, __user__: dict = None) -> str:
        """
        从条目中提取参数

        :param entry_id: 条目 ID
        :return: 提取的参数结果
        """
        result = await self._request("POST", f"/pm/entries/{entry_id}/extract-parameters")
        return json.dumps(result, ensure_ascii=False)

    async def generate_content(self, entry_id: str, module_type: str, instructions: str = "", __event_call__: callable = None, __event_emitter__: callable = None, __user__: dict = None) -> str:
        """
        使用 AI 生成内容（预览后确认写入）

        :param entry_id: 条目 ID
        :param module_type: 模块类型
        :param instructions: 生成指令 (可选)
        :param __event_call__: 事件回调 (可选，用于确认流程)
        :param __event_emitter__: 事件发射器 (可选，用于预览生成内容)
        :return: 生成的内容结果
        """
        if __event_call__:
            confirm = await __event_call__({
                "type": "confirmation",
                "data": {
                    "title": "确认生成内容",
                    "message": f"确定要为条目 {entry_id} 生成 {module_type} 内容吗？"
                }
            })
            if not confirm:
                return json.dumps({"status": "cancelled", "message": "用户取消了生成操作"}, ensure_ascii=False)
        
        req_data = {
            "module_type": module_type,
            "instructions": instructions
        }
        result = await self._request("POST", f"/pm/entries/{entry_id}/generate", req_data)

        if "error" not in result:
            preview_content = result.get("content", json.dumps(result, ensure_ascii=False))
            await self._emit_preview(f"**生成内容预览 ({module_type})**\n\n{preview_content}", __event_emitter__)
            if __event_call__:
                write_confirm = await __event_call__({
                    "type": "confirmation",
                    "data": {
                        "title": "确认写入内容",
                        "message": "以上生成内容将写入项目。确认写入？"
                    }
                })
                if not write_confirm:
                    return json.dumps({"status": "cancelled", "message": "用户取消了写入操作", "preview": result}, ensure_ascii=False)

        return json.dumps(result, ensure_ascii=False)
