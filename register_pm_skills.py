"""
PM Skill & Prompt 注册脚本
用于将 PM Skill 和 Prompt 注册到 Open WebUI

Usage:
    python register_pm_skills.py [--api-key KEY] [--base-url URL]
"""

import argparse
import json
import os


# Skill definitions
PM_SKILLS = [
    {
        "id": "pm-prd-generation",
        "name": "PRD 生成流程",
        "description": "基于需求生成完整 PRD 文档，包含概述、背景、目标、功能需求、非功能需求、附录等章节",
        "file": "skills/pm-prd-generation.md",
    },
    {
        "id": "pm-requirement-analysis",
        "name": "需求分析流程",
        "description": "分析需求条目，给出分类建议、优先级建议和潜在冲突分析",
        "file": "skills/pm-requirement-analysis.md",
    },
    {
        "id": "pm-parameter-extraction",
        "name": "参数提取流程",
        "description": "从 PRD 或需求文档中提取关键参数，包括参数名、类型、默认值、描述等",
        "file": "skills/pm-parameter-extraction.md",
    },
    {
        "id": "pm-cross-module-flow",
        "name": "跨模块流转编排",
        "description": "执行 PM 模块间的数据流转编排，支持需求→PRD→参数→测试用例的链式流转",
        "file": "skills/pm-cross-module-flow.md",
    },
    {
        "id": "pm-check-quality",
        "name": "PRD 质量检查",
        "description": "对 PRD 文档执行 4 级质量检查（内容存在性、逻辑完整性、UX 启发式、安全性），生成修复建议",
        "file": "skills/pm-check-quality.md",
    },
    {
        "id": "pm-roadmap-planning",
        "name": "产品路线图规划",
        "description": "帮助用户规划和管理工作路线图，包括节点创建、AI 排期建议和冲突检测",
        "file": "skills/pm-roadmap-planning.md",
    },
]

# Prompt definitions
PM_PROMPTS = [
    {
        "id": "pm-assistant",
        "name": "产品经理助手",
        "description": "PM 工作流全域助手指令，帮助用户完成产品工作流的各个环节",
        "file": "prompts/pm-assistant.md",
    },
    {
        "id": "pm-review-expert",
        "name": "需求评审专家",
        "description": "PRD 检查和需求完整性分析指令，专注于检查文档的完整性、一致性和可测试性",
        "file": "prompts/pm-review-expert.md",
    },
]


def read_file(base_dir: str, relative_path: str) -> str:
    """Read a file from the base directory"""
    full_path = os.path.join(base_dir, relative_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def register_skill(api_base_url: str, api_key: str, skill: dict, content: str):
    """Register a skill via Open WebUI API"""
    import requests
    
    url = f"{api_base_url}/api/v1/skills/create"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "id": skill["id"],
        "name": skill["name"],
        "content": content,
        "meta": {
            "description": skill["description"],
            "version": "1.0.0",
            "author": "PM Workflow Platform",
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def register_prompt(api_base_url: str, api_key: str, prompt: dict, content: str):
    """Register a prompt via Open WebUI API"""
    import requests
    
    url = f"{api_base_url}/api/v1/prompts/create"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "id": prompt["id"],
        "name": prompt["name"],
        "content": content,
        "meta": {
            "description": prompt["description"],
            "version": "1.0.0",
            "author": "PM Workflow Platform",
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Register PM Skills and Prompts to Open WebUI")
    parser.add_argument("--api-key", default="", help="Open WebUI API Key")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Open WebUI Base URL")
    parser.add_argument("--base-dir", default="./backend/open_webui", help="Base directory for skills/prompts")
    args = parser.parse_args()
    
    print("=" * 60)
    print("PM Skill & Prompt Registration")
    print("=" * 60)
    
    # Register Skills
    print("\n## Registering Skills ##\n")
    for skill in PM_SKILLS:
        print(f"Registering: {skill['id']} ({skill['name']})")
        try:
            content = read_file(args.base_dir, skill["file"])
            result = register_skill(args.base_url, args.api_key, skill, content)
            if result:
                print(f"  SUCCESS: {skill['id']} registered")
            else:
                print(f"  FAILED: {skill['id']}")
        except FileNotFoundError:
            print(f"  ERROR: File not found: {skill['file']}")
    
    # Register Prompts
    print("\n## Registering Prompts ##\n")
    for prompt in PM_PROMPTS:
        print(f"Registering: {prompt['id']} ({prompt['name']})")
        try:
            content = read_file(args.base_dir, prompt["file"])
            result = register_prompt(args.base_url, args.api_key, prompt, content)
            if result:
                print(f"  SUCCESS: {prompt['id']} registered")
            else:
                print(f"  FAILED: {prompt['id']}")
        except FileNotFoundError:
            print(f"  ERROR: File not found: {prompt['file']}")
    
    print("\n" + "=" * 60)
    print("Registration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
