# Skill Registry Contract

**Date**: 2026-07-11
**Feature**: PM Skills Integration (003)

---

## Overview

定义 pm-skills 在统一注册表中的注册和查询接口。

---

## Registry API

```python
def register_skill(contract: SkillContract) -> None:
    """注册 skill 到统一注册表"""
    ...

def get_skill(skill_id: str) -> SkillContract:
    """通过 ID 获取 skill"""
    ...

def list_skills(
    invocation: Optional[str] = None,
    category: Optional[str] = None
) -> list[SkillContract]:
    """列出所有 skill，支持过滤"""
    ...

def resolve_by_command(cmd: str) -> Optional[SkillContract]:
    """解析 /pm-<id> 命令到 SkillContract"""
    ...
```

---

## pm-skills 注册格式

```typescript
interface PmSkillsRegistryEntry {
  id: string;                    // "pm-skills/<command-id>"
  name: string;
  description: string;
  category: 'analysis' | 'generation' | 'extraction' | 'workflow';
  methodologyRef: string;        // "pm-skills/<plugin>/<skill>/SKILL.md"
  invocation: 'explicit' | 'autonomous' | 'both';
  requiresConfirm: boolean;
  outputContract?: Record<string, unknown>;
}
```

---

## Registry Summary (for Pipeline Injection)

```typescript
interface SkillRegistrySummary {
  id: string;
  name: string;
  description: string;
  invocation: 'explicit' | 'autonomous' | 'both';
  category: string;
}
```
