"""PM Action registry and execution logic."""

from typing import Any


ACTION_REGISTRY: dict[str, dict[str, Any]] = {
    'pm.entry.create': {
        'label': '创建条目',
        'description': '在指定模块下创建新条目',
        'requires_confirm': True,
    },
    'pm.entry.update': {
        'label': '更新条目',
        'description': '更新已有条目的内容或属性',
        'requires_confirm': True,
    },
    'pm.relation.create': {
        'label': '创建关联',
        'description': '在两个条目间建立关联关系',
        'requires_confirm': True,
    },
    'pm.version.create': {
        'label': '创建版本',
        'description': '创建新的项目版本',
        'requires_confirm': True,
    },
    'pm.parameter.extract': {
        'label': '提取参数',
        'description': '从文档内容中提取参数配置',
        'requires_confirm': True,
    },
}


def get_action_info(action_type: str) -> dict[str, Any] | None:
    """Get action metadata by type."""
    return ACTION_REGISTRY.get(action_type)


def validate_action(action: dict) -> list[str]:
    """Validate an action payload, returning list of errors (empty if valid)."""
    errors = []
    action_type = action.get('type', '')
    if action_type not in ACTION_REGISTRY:
        errors.append(f'Unknown action type: {action_type}')
    if not action.get('label'):
        errors.append('Action must have a label')
    payload = action.get('payload', {})
    if action_type == 'pm.entry.create' and not payload.get('module_type'):
        errors.append('pm.entry.create requires module_type in payload')
    if action_type == 'pm.entry.update' and not payload.get('entry_id'):
        errors.append('pm.entry.update requires entry_id in payload')
    if action_type == 'pm.relation.create':
        if not payload.get('entity_a_id') or not payload.get('entity_b_id'):
            errors.append('pm.relation.create requires entity_a_id and entity_b_id')
    return errors
