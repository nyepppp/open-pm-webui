"""Intent detection for PM Agent chat messages."""

INTENT_KEYWORDS: dict[str, list[str]] = {
    'prd-generation': ['prd', '产品需求文档', '需求文档', 'prd大纲', '生成prd', '写prd'],
    'requirement-analysis': ['需求分析', '分析需求', '需求分类', '优先级建议', '需求整理'],
    'competitor-research': ['竞品', '竞品分析', '竞品调研', '对比分析', '竞品对比'],
    'prototype-check': ['原型', '走查', 'ui审查', '设计走查', '原型检查'],
    'parameter-extract': ['参数', '提取参数', '参数清单', '参数提取', '配置项'],
    'testcase-generate': ['测试用例', '用例生成', '测试', '用例', 'test case'],
    'version-compare': ['版本对比', '版本比较', '版本差异', 'diff', '版本变更'],
    'relation-suggest': ['关联', '关系', '溯源', '关联建议', '依赖关系'],
    'workflow-suggest': ['流程', '工作流', '下一步', '流程建议', '进度'],
}


def detect_intent(message: str) -> tuple[str, float]:
    """Detect the most likely skill intent from a user message.

    Returns (skill_id, confidence) tuple.
    """
    msg_lower = message.lower()
    best_skill = 'general'
    best_score = 0.0
    for skill_id, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in msg_lower) / len(keywords)
        if score > best_score:
            best_score = score
            best_skill = skill_id
    confidence = min(best_score * 3, 1.0) if best_score > 0 else 0.3
    return best_skill, confidence
