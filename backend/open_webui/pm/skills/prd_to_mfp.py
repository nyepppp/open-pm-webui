"""PRD → 模块-功能-参数 原子化转换 skill (D44)。

读取 PRD 条目内容，内部用 task_model 调一次 LLM 提取结构化 JSON（模块/功能/参数树），
然后按层级顺序原子化创建 PMEntry：
  1. 批量创建模块条目（module_type=product-architecture, data.node_type=module）
  2. 收集模块 entry_id，按 title 映射
  3. 批量创建功能条目（module_type=product-architecture, data.node_type=function,
     data.parent_entry_id=模块ID, data.moduleName=模块名）
  4. 收集功能 entry_id，按 title 映射
  5. 批量创建参数条目（module_type=parameter, data.parent_entry_id=功能ID,
     data.moduleName=模块名, data.featureName=功能名,
     data.key/data.paramType/data.dataType/data.required/data.defaultValue/data.description 等）

任一步失败则 hard delete 已创建 entry_id 列表回滚。

双链接策略：
- data.parent_entry_id（ID-based，供工具回溯）
- data.moduleName + data.featureName（name-based，供前端 moduleFields.ts 编辑器读取）
"""

import json
import logging
import re
from typing import Any, Optional

from open_webui.pm.skills.base import BaseSkill

logger = logging.getLogger(__name__)


class PRDToMFPSkill(BaseSkill):
    """PRD → 模块-功能-参数 原子化转换 skill。"""

    id = "prd-to-mfp"
    name = "PRD 转模块-功能-参数"
    description = "读取 PRD 条目，原子化创建模块/功能/参数层级（含 parent_entry_id + moduleName/featureName 双链接）"
    icon = "hierarchy"

    EXTRACTION_SYSTEM_PROMPT = """你是 PRD → 产品架构 转换专家。

读取 PRD 内容后输出严格的 JSON schema：
{
  "modules": [
    {
      "name": "模块名",
      "description": "模块描述（一句话）",
      "features": [
        {
          "name": "功能名",
          "description": "功能描述（一句话）",
          "parameters": [
            {
              "key": "参数标识符（camelCase）",
              "paramType": "输入参数 | 输出参数 | 配置参数",
              "dataType": "string | number | boolean | object | array",
              "required": "是 | 否",
              "defaultValue": "默认值或空字符串",
              "description": "参数说明"
            }
          ]
        }
      ]
    }
  ]
}

规则：
1. 一个 PRD 通常拆出 3-8 个模块
2. 每个模块下 2-6 个功能
3. 每个功能下 0-10 个参数（输入/输出/配置三类）
4. 模块/功能名用名词短语，不要用动词
5. 参数 key 用 camelCase 英文标识符
6. **只输出 JSON，不要任何解释文字、Markdown 代码块或前后缀**

D44-fix 硬约束（违反将导致 skill 校验失败、回滚 0 条）：
7. **禁止把 parameter key（如 boundKbIds、cascadeDelete）当成 feature name** —— feature name 必须是名词短语（如「部门 CRUD」「角色绑定管理」），不能是 camelCase 标识符
8. **每个 parameter 必须挂在某个 feature 下** —— 不允许 module 直接挂 parameter（parameters 只能出现在 feature 对象内，不能出现在 module 对象内）
9. **禁止产出「未分类模块」「Uncategorized」这种兜底 module** —— 所有内容必须归到具体的业务模块；如果某个 parameter 找不到归属，宁可不输出它，也不要塞进「未分类」
"""

    @property
    def system_prompt(self) -> str:
        return self.EXTRACTION_SYSTEM_PROMPT

    async def transform(
        self,
        prd_entry_id: str,
        user,
        metadata: dict,
        request=None,
    ) -> dict:
        """原子化执行 PRD → 模块/功能/参数 转换。

        流程见模块 docstring。

        Args:
            prd_entry_id: PRD 条目 ID
            user: UserModel 实例
            metadata: 含 pm_project_id 等上下文
            request: FastAPI Request 实例（用于调 LLM）

        Returns:
            {
                'success': bool,
                'created_modules': int,
                'created_functions': int,
                'created_parameters': int,
                'total': int,
                'by_module': {模块名: {'functions': int, 'parameters': int}},
                'rolled_back': bool,
                'error': Optional[str]
            }
        """
        from open_webui.models.pm import PMEntries
        from open_webui.models.users import UserModel
        from open_webui.pm.chat_context import _verify_project_access

        user_obj = UserModel(**user) if isinstance(user, dict) else user
        pid = metadata.get('pm_project_id')
        if not pid or not await _verify_project_access(pid, user_obj):
            return self._fail('未选择项目或无权限', rolled_back=False)

        # 1. 读 PRD
        prd_entry = await PMEntries.get_entry_by_id(prd_entry_id)
        if not prd_entry:
            return self._fail(f'PRD 条目不存在: {prd_entry_id}', rolled_back=False)
        if prd_entry.module_type != 'prd':
            return self._fail(
                f'条目类型不是 prd: {prd_entry.module_type}', rolled_back=False
            )

        # 2. LLM 提取结构化 JSON
        try:
            structured = await self._extract_structure_with_llm(
                prd_entry=prd_entry,
                user=user_obj,
                metadata=metadata,
                request=request,
            )
        except Exception as e:
            logger.exception('PRDToMFPSkill: LLM 提取失败')
            return self._fail(f'LLM 提取失败: {e}', rolled_back=False)

        # 2.5 D44-fix: 校验 LLM 输出 shape —— 拒绝「parameter-key-as-feature-name」
        #     「module 直接挂 parameter」「未分类模块」等残缺结构，避免脏数据落库。
        ok, reason = self._validate_structure(structured)
        if not ok:
            logger.warning(f'[PRDToMFP] LLM 输出校验失败: {reason}')
            return self._fail(f'LLM 提取的结构无效: {reason}', rolled_back=False)

        # 3. 原子化创建
        created_ids: list[str] = []
        try:
            return await self._create_hierarchy_atomically(
                structured=structured,
                pid=pid,
                user_obj=user_obj,
                created_ids=created_ids,
            )
        except Exception as e:
            logger.exception('PRDToMFPSkill: 创建失败，回滚')
            await self._rollback(created_ids)
            return {
                'success': False,
                'error': f'创建失败已回滚: {e}',
                'created_modules': 0,
                'created_functions': 0,
                'created_parameters': 0,
                'total': 0,
                'by_module': {},
                'rolled_back': True,
            }

    async def _extract_structure_with_llm(
        self,
        prd_entry,
        user,
        metadata: dict,
        request=None,
    ) -> dict:
        """用 task_model 调 LLM 提取模块/功能/参数 JSON 树。

        默认用 request.app.state.config.TASK_MODEL，fallback 到 metadata['model_id']。
        解析时容忍 ```json``` 包裹。
        """
        # PRD 内容
        prd_content = prd_entry.content or ''
        prd_title = prd_entry.title or ''
        if not prd_content.strip():
            raise ValueError('PRD 内容为空')

        # 优先用 request 调 generate_chat_completion；如无 request 则降级
        if request is None:
            raise ValueError(
                'request 未注入，无法调用 LLM。请确认 PM agent 已升级到 v14+ 流式管道。'
            )

        from open_webui.utils.chat import generate_chat_completion
        from open_webui.utils.task import get_task_model_id

        # 解析 task_model_id（与 is_pm_related_query 同路径）
        model_id = metadata.get('model_id') or ''
        models = request.app.state.MODELS
        task_model_id = get_task_model_id(
            model_id,
            request.app.state.config.TASK_MODEL,
            request.app.state.config.TASK_MODEL_EXTERNAL,
            models,
        )
        if task_model_id not in models:
            raise ValueError(
                f'task_model_id {task_model_id} not in models，无法调 LLM'
            )

        max_tokens = (
            models[task_model_id].get('info', {}).get('params', {}).get('max_tokens', 4096)
        )

        user_prompt = (
            f'PRD 标题：{prd_title}\n\n'
            f'PRD 内容：\n{prd_content}\n\n'
            f'请按系统提示的 JSON schema 输出模块/功能/参数结构。'
        )

        payload = {
            'model': task_model_id,
            'messages': [
                {'role': 'system', 'content': self.EXTRACTION_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            'stream': False,
            **(
                {'max_tokens': max_tokens}
                if models[task_model_id].get('owned_by') == 'ollama'
                else {'max_completion_tokens': max_tokens}
            ),
            'metadata': {
                'task': 'generation',
                'chat_id': None,
            },
        }

        response = await generate_chat_completion(request, form_data=payload, user=user)

        # 解析响应
        content = None
        if hasattr(response, 'body_iterator'):
            async for chunk in response.body_iterator:
                data = json.loads(chunk.decode('utf-8', 'replace'))
                content = data['choices'][0]['message']['content']
            if response.background is not None:
                await response.background()
        elif isinstance(response, dict):
            content = response['choices'][0]['message']['content']
        else:
            # JSONResponse 等
            content = response.body.decode('utf-8', 'replace') if hasattr(response, 'body') else None
            if content:
                try:
                    parsed = json.loads(content)
                    content = parsed['choices'][0]['message']['content']
                except Exception:
                    pass

        if not content:
            raise ValueError('LLM 返回空响应')

        structured = self._parse_llm_json(content)

        # D44-fix: 诊断日志 —— 便于从后端日志直接判断是 LLM 提取问题还是 skill 创建问题
        mod_count = len(structured.get('modules', []))
        feat_count = sum(len(m.get('features', [])) for m in structured.get('modules', []))
        param_count = sum(
            len(f.get('parameters', []))
            for m in structured.get('modules', [])
            for f in m.get('features', [])
        )
        logger.info(
            f'[PRDToMFP] LLM 提取: modules={mod_count}, features={feat_count}, parameters={param_count}'
        )

        return structured

    def _validate_structure(self, structured: dict) -> tuple[bool, str]:
        """D44-fix: 校验 LLM 提取的 JSON 结构。

        5 项校验：
        1. 顶层有 modules 数组且非空
        2. 每个 module 有非空 name
        3. module 名禁止「未分类模块」「Uncategorized」
        4. 每个 module 必须有 features 数组且非空（禁止 module 直接挂 parameters）
        5. 每个 feature 必须有非空 name

        Args:
            structured: LLM 提取并解析后的 dict

        Returns:
            (ok, reason) — ok=True 时 reason 为空字符串；ok=False 时 reason 是中文说明
        """
        if not isinstance(structured, dict):
            return False, '顶层不是 dict 对象'

        modules = structured.get('modules')
        if not isinstance(modules, list) or len(modules) == 0:
            return False, 'modules 字段缺失或为空数组'

        forbidden_module_names = {'未分类模块', 'Uncategorized', 'uncategorized', '未分类'}
        for i, mod in enumerate(modules):
            if not isinstance(mod, dict):
                return False, f'modules[{i}] 不是 dict 对象'

            mod_name = mod.get('name')
            if not mod_name or not isinstance(mod_name, str) or not mod_name.strip():
                return False, f'modules[{i}].name 缺失或为空'

            if mod_name.strip() in forbidden_module_names:
                return False, (
                    f'modules[{i}].name="{mod_name}" 是禁止的兜底模块名'
                    '（应归到具体业务模块，或省略无法分类的内容）'
                )

            features = mod.get('features')
            if not isinstance(features, list) or len(features) == 0:
                return False, f'modules[{i}].features 缺失或为空数组（每个 module 必须有至少 1 个 feature）'

            # D44-fix: 禁止 module 直接挂 parameters（parameters 必须在 feature 内）
            if 'parameters' in mod and isinstance(mod.get('parameters'), list) and len(mod.get('parameters', [])) > 0:
                return False, f'modules[{i}] 直接挂了 parameters（必须挂在 feature 下）'

            for j, feat in enumerate(features):
                if not isinstance(feat, dict):
                    return False, f'modules[{i}].features[{j}] 不是 dict 对象'

                feat_name = feat.get('name')
                if not feat_name or not isinstance(feat_name, str) or not feat_name.strip():
                    return False, f'modules[{i}].features[{j}].name 缺失或为空'

                # 启发式：feature name 全是 camelCase 标识符（小写字母开头+含大写字母+长度>8）记 warning
                #   不阻断 —— 避免误判合法的 feature name（如「user CRUD」），只记日志便于排查
                if (
                    len(feat_name) > 8
                    and feat_name[0].islower()
                    and any(c.isupper() for c in feat_name[1:])
                    and '_' not in feat_name
                    and ' ' not in feat_name
                ):
                    logger.warning(
                        f'[PRDToMFP] feature name "{feat_name}" 看起来像 camelCase 参数键'
                        f'（modules[{i}].features[{j}]）—— 怀疑是 parameter key 误填为 feature name'
                    )

        return True, ''

    def _parse_llm_json(self, content: str) -> dict:
        """解析 LLM 返回的 JSON，容忍 ```json``` 包裹和前后缀文字。"""
        text = content.strip()

        # 优先尝试整体 parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # 尝试从 ```json``` 块提取
        json_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1).strip())
            except Exception:
                pass

        # 尝试找最外层 { ... }
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace >= 0 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace : last_brace + 1])
            except Exception:
                pass

        raise ValueError(f'无法从 LLM 响应解析 JSON: {text[:200]}')

    async def _create_hierarchy_atomically(
        self,
        structured: dict,
        pid: str,
        user_obj,
        created_ids: list[str],
    ) -> dict:
        """5 步原子化创建（模块→功能→参数）。"""
        from open_webui.models.pm import PMEntries, PMEntryForm

        # 3a. 模块
        module_entries = []
        for mod in structured.get('modules', []):
            mod_name = mod.get('name') or f'module-{len(module_entries) + 1}'
            mod_desc = mod.get('description', '')
            form = PMEntryForm(
                project_id=pid,
                module_type='product-architecture',
                title=mod_name,
                content=mod_desc,
                data={
                    'node_type': 'module',
                    'description': mod_desc,
                },
                status='draft',
                priority='medium',
            )
            entry = await PMEntries.insert_new_entry(user_obj.id, form)
            if not entry:
                raise RuntimeError(f'创建模块失败: {mod_name}')
            created_ids.append(entry.id)
            module_entries.append((mod, entry))

        # 3b. 功能
        feature_count = 0
        for mod, mod_entry in module_entries:
            mod_name = mod.get('name') or mod_entry.title
            for feat in mod.get('features', []):
                feat_name = feat.get('name') or f'feature-{feature_count + 1}'
                feat_desc = feat.get('description', '')
                form = PMEntryForm(
                    project_id=pid,
                    module_type='product-architecture',
                    title=feat_name,
                    content=feat_desc,
                    data={
                        'node_type': 'function',
                        'parent_entry_id': mod_entry.id,
                        'moduleName': mod_name,
                        'description': feat_desc,
                    },
                    status='draft',
                    priority='medium',
                )
                entry = await PMEntries.insert_new_entry(user_obj.id, form)
                if not entry:
                    raise RuntimeError(f'创建功能失败: {feat_name}')
                created_ids.append(entry.id)
                feat['_entry'] = entry
                feature_count += 1

        # 3c. 参数
        param_count = 0
        by_module: dict[str, dict] = {}
        for mod, mod_entry in module_entries:
            mod_name = mod.get('name') or mod_entry.title
            mod_param_count = 0
            mod_feature_count = 0
            for feat in mod.get('features', []):
                feat_name = feat.get('name') or feat['_entry'].title
                feat_entry = feat['_entry']
                mod_feature_count += 1
                for param in feat.get('parameters', []):
                    param_key = param.get('key') or f'param-{param_count + 1}'
                    param_desc = param.get('description', '')
                    form = PMEntryForm(
                        project_id=pid,
                        module_type='parameter',
                        title=param_key,
                        content=param_desc,
                        data={
                            'key': param_key,
                            'paramType': param.get('paramType', '配置参数'),
                            'dataType': param.get('dataType', 'string'),
                            'required': param.get('required', '否'),
                            'defaultValue': param.get('defaultValue', ''),
                            'description': param_desc,
                            'parent_entry_id': feat_entry.id,
                            'moduleName': mod_name,
                            'featureName': feat_name,
                        },
                        status='draft',
                        priority='medium',
                    )
                    entry = await PMEntries.insert_new_entry(user_obj.id, form)
                    if not entry:
                        raise RuntimeError(f'创建参数失败: {param_key}')
                    created_ids.append(entry.id)
                    param_count += 1
                    mod_param_count += 1
            by_module[mod_name] = {
                'functions': mod_feature_count,
                'parameters': mod_param_count,
            }

        return {
            'success': True,
            'created_modules': len(module_entries),
            'created_functions': feature_count,
            'created_parameters': param_count,
            'total': len(module_entries) + feature_count + param_count,
            'by_module': by_module,
            'rolled_back': False,
            'error': None,
        }

    async def _rollback(self, created_ids: list[str]) -> None:
        """Hard delete 已创建条目（best-effort）。"""
        from open_webui.models.pm import PMEntries
        for entry_id in created_ids:
            try:
                await PMEntries.delete_entry_by_id(entry_id)
            except Exception:
                logger.exception(f'PRDToMFPSkill._rollback: 回滚失败 {entry_id}')

    def _fail(self, error: str, rolled_back: bool = False) -> dict:
        """返回标准化失败响应。"""
        return {
            'success': False,
            'error': error,
            'created_modules': 0,
            'created_functions': 0,
            'created_parameters': 0,
            'total': 0,
            'by_module': {},
            'rolled_back': rolled_back,
        }
