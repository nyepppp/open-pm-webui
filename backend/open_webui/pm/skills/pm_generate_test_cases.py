"""PM Agent skills for workspace data operations.

These skills enable the agent to perform cross-module operations
like generating test cases from requirements or extracting parameters from PRDs.
"""

import json
from typing import Any, Optional

from open_webui.pm.skills.base import BaseSkill


class PMGenerateTestCasesSkill(BaseSkill):
    """Skill for generating test cases from requirements."""

    id = "pm-generate-test-cases"
    name = "生成测试用例"
    description = "从需求文档自动生成测试用例"
    icon = "test-case"

    @property
    def system_prompt(self) -> str:
        return """你是测试用例生成专家。你的任务是根据提供的需求文档，
生成全面、结构化的测试用例。

请遵循以下规则：
1. 为每个功能需求生成至少一个测试用例
2. 包含正向测试和边界条件测试
3. 测试用例格式：
   - 用例ID
   - 用例名称
   - 前置条件
   - 测试步骤
   - 预期结果
   - 优先级（P0/P1/P2）
4. 标记与原始需求的关联关系

输出格式为结构化的JSON数组。"""

    def build_user_message(
        self,
        user_message: str,
        project_id: str,
        module_type: Optional[str] = None,
        entry_id: Optional[str] = None,
        entry_title: Optional[str] = None,
        entry_content_summary: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> str:
        """Build user message with requirement context."""
        parts = [
            f"项目ID: {project_id}",
            "任务: 根据以下需求生成测试用例",
        ]
        if entry_title:
            parts.append(f"需求标题: {entry_title}")
        if entry_content_summary:
            parts.append(f"需求内容:\n{entry_content_summary}")
        if extra_data and "requirements" in extra_data:
            parts.append(f"关联需求:\n{json.dumps(extra_data['requirements'], ensure_ascii=False)}")
        parts.append(f"\n用户指令: {user_message}")
        return "\n".join(parts)

    def parse_response(self, llm_response: str) -> dict:
        """Parse LLM response into test cases with traceability links."""
        # Extract JSON test cases from response
        import re

        test_cases = []
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(json_pattern, llm_response)

        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    test_cases.extend(data)
                elif isinstance(data, dict):
                    test_cases.append(data)
            except json.JSONDecodeError:
                continue

        result = super().parse_response(llm_response)
        result["test_cases"] = test_cases
        result["skillId"] = self.id
        return result


class PMExtractParametersSkill(BaseSkill):
    """Skill for extracting parameters from PRD documents."""

    id = "pm-extract-parameters"
    name = "提取参数"
    description = "从PRD文档中提取关键参数和配置项"
    icon = "parameter"

    @property
    def system_prompt(self) -> str:
        return """你是参数提取专家。你的任务是从PRD（产品需求文档）中
n提取所有关键参数和配置项。

请提取以下类型的参数：
1. 数值参数（阈值、限制、配额等）
2. 配置项（开关、选项、模式等）
3. 时间参数（周期、超时、延迟等）
4. 业务规则参数（规则条件、权重等）

输出格式为结构化的JSON数组，每个参数包含：
- name: 参数名称
- type: 参数类型（number/string/boolean/array/object）
- description: 参数描述
- default_value: 默认值（如果有）
- source: 在PRD中的来源位置
- priority: 优先级（P0/P1/P2）"""

    def build_user_message(
        self,
        user_message: str,
        project_id: str,
        module_type: Optional[str] = None,
        entry_id: Optional[str] = None,
        entry_title: Optional[str] = None,
        entry_content_summary: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> str:
        """Build user message with PRD context."""
        parts = [
            f"项目ID: {project_id}",
            "任务: 从PRD文档中提取关键参数",
        ]
        if entry_title:
            parts.append(f"PRD标题: {entry_title}")
        if entry_content_summary:
            parts.append(f"PRD内容:\n{entry_content_summary}")
        parts.append(f"\n用户指令: {user_message}")
        return "\n".join(parts)

    def parse_response(self, llm_response: str) -> dict:
        """Parse LLM response into extracted parameters."""
        import re

        parameters = []
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(json_pattern, llm_response)

        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    parameters.extend(data)
                elif isinstance(data, dict) and "parameters" in data:
                    parameters.extend(data["parameters"])
            except json.JSONDecodeError:
                continue

        result = super().parse_response(llm_response)
        result["parameters"] = parameters
        result["skillId"] = self.id
        return result
