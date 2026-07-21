# 第三方依赖许可证合规评估 (#38)

**评估日期**: 2026-07-21
**评估范围**: open-pm-webui 仓库
**评估者**: Phase 6 安全治理
**关联 Issue**: #38

---

## 1. 评估范围

本评估覆盖 open-pm-webui 项目的全部第三方依赖:

- **后端 Python 依赖**: `backend/requirements.txt` 中列出的所有包
- **前端 npm 依赖**: `package.json` 中列出的所有包
- **容器基础镜像**: `Dockerfile` 中引用的官方镜像

---

## 2. 本项目许可证

**文件**: `LICENSE` (仓库根)

**许可证类型**: Open WebUI License (BSD-3-Clause 风格的自定义许可)

**关键条款**:
- Copyright (c) 2023- Open WebUI Inc.
- 允许使用、修改、分发, 条件是保留版权声明
- 禁止使用项目名称进行背书
- 不提供任何担保

**兼容性**: 与 BSD-3-Clause 等价, 兼容 MIT/Apache-2.0/BSD/ISC 等宽松许可证.

---

## 3. 许可证兼容性矩阵

| 许可证类型 | 与本项目兼容 | 备注 |
|-----------|------------|------|
| MIT | 是 | 宽松, 无 copyleft |
| Apache-2.0 | 是 | 宽松, 含专利授权 |
| BSD-2-Clause | 是 | 宽松 |
| BSD-3-Clause | 是 | 宽松 (本项目同等) |
| ISC | 是 | 宽松 |
| MPL-2.0 | 是 | 弱 copyleft (文件级) |
| LGPL-2.1/3.0 | 是 | 弱 copyleft (库级), 需注意动态链接 |
| GPL-2.0/3.0 | **需法务复核** | 强 copyleft, 若静态链接可能传染 |
| AGPL-3.0 | **需法务复核** | 网络服务也需开源, 高风险 |
| Unlicense | 是 | 公共领域 |
| CC0-1.0 | 是 | 公共领域 |

---

## 4. 后端 Python 依赖清单

基于 `backend/requirements.txt` 的主要依赖 (按字母序):

| 依赖 | 版本范围 | 许可证 | 状态 |
|------|---------|--------|------|
| aiohttp | >=3.9 | Apache-2.0 | 无问题 |
| alembic | >=1.13 | MIT | 无问题 |
| asyncpg | >=0.29 | Apache-2.0 | 无问题 |
| boto3 | >=1.34 | Apache-2.0 | 无问题 |
| celery | >=5.3 | BSD-3-Clause | 无问题 |
| chromadb | >=0.4 | Apache-2.0 | 无问题 |
| fastapi | >=0.109 | MIT | 无问题 |
| httpx | >=0.26 | BSD-3-Clause | 无问题 |
| langchain | >=0.1 | MIT | 无问题 |
| langfuse | >=2.0 | MIT | 无问题 |
| numpy | >=1.26 | BSD-3-Clause | 无问题 |
| openai | >=1.0 | MIT | 无问题 |
| pandas | >=2.1 | BSD-3-Clause | 无问题 |
| pillow | >=10.0 | MIT-CMU | 无问题 |
| psycopg2-binary | >=2.9 | LGPL-3.0 | **需法务复核** (LGPL, 动态链接应安全) |
| pydantic | >=2.5 | MIT | 无问题 |
| python-jose | >=3.3 | MIT | 无问题 |
| pyyaml | >=6.0 | MIT | 无问题 |
| redis | >=5.0 | MIT | 无问题 |
| requests | >=2.31 | Apache-2.0 | 无问题 |
| sentry-sdk | >=1.40 | MIT | 无问题 |
| sqlalchemy | >=2.0 | MIT | 无问题 |
| starlette | >=0.35 | BSD-3-Clause | 无问题 |
| tiktoken | >=0.5 | MIT | 无问题 |
| uvicorn | >=0.25 | BSD-3-Clause | 无问题 |

**无问题**: 23
**需法务复核**: 1 (psycopg2-binary, LGPL-3.0)

---

## 5. 前端 npm 依赖清单

基于 `package.json` 的主要依赖:

| 依赖 | 许可证 | 状态 |
|------|--------|------|
| @sveltejs/kit | MIT | 无问题 |
| svelte | MIT | 无问题 |
| tailwindcss | MIT | 无问题 |
| typescript | Apache-2.0 | 无问题 |
| vite | MIT | 无问题 |
| @iconify/svelte | MIT | 无问题 |
| chart.js | MIT | 无问题 |
| codemirror | MIT | 无问题 |
| d3 | ISC | 无问题 |
| fuse.js | Apache-2.0 | 无问题 |
| highlight.js | BSD-3-Clause | 无问题 |
| katex | MIT | 无问题 |
| marked | MIT | 无问题 |
| plotly.js | MIT | 无问题 |
| sortablejs | MIT | 无问题 |

**无问题**: 15
**需法务复核**: 0

---

## 6. 容器基础镜像

| 镜像 | 用途 | 许可证 | 状态 |
|------|------|--------|------|
| `python:3.11-slim-bookworm` | 后端运行时 | PSF-2.0 (Python) + GPL (Debian 包) | 无问题 (Python 豁免) |
| `node:22-alpine3.20` | 前端构建 | MIT (Node) + BSD (Alpine) | 无问题 |

---

## 7. 高风险依赖清单

### psycopg2-binary (LGPL-3.0)

**用途**: PostgreSQL 异步驱动
**风险**: LGPL-3.0 要求修改库本身时需开源修改, 但动态链接 (正常使用) 不传染
**建议**: 
- 当前使用方式 (动态链接) 安全, 无需替换
- 若修改 psycopg2 源码, 需开源修改部分
- 替代方案 (若法务仍担心): `asyncpg` (Apache-2.0) - 已在依赖列表中, 可逐步迁移

---

## 8. 二进制分发注意事项

若发布 Docker 镜像 (二进制分发), 需注意:

1. **LGPL 义务**: 提供 psycopg2 源码获取方式 (written offer)
2. **GPL 依赖**: Debian 基础镜像中的 GPL 包 (如 coreutils) 通过容器隔离, 不传染主程序
3. **专利授权**: Apache-2.0 依赖提供专利授权, 重新分发需保留 NOTICE 文件

---

## 9. 结论与建议

### 总结

| 类别 | 数量 |
|------|------|
| 无问题依赖 | 38 |
| 需法务复核 | 1 (psycopg2-binary, LGPL-3.0) |
| 必须替换 | 0 |

### 建议

1. **当前可发布**: 所有依赖许可证与本项目兼容, 可安全发布
2. **psycopg2-binary 复核**: 建议法务确认 LGPL-3.0 在当前使用方式下 (动态链接, 未修改源码) 的合规性
3. **长期迁移**: 考虑逐步迁移到 `asyncpg` (已在依赖中) 以彻底消除 LGPL 依赖
4. **自动化检查**: 建议在 CI 中集成 `pip-licenses` 与 `license-checker` 自动扫描, 阻止引入不兼容许可证的新依赖

### 后续行动项

- [ ] 法务复核 psycopg2-binary LGPL-3.0 使用合规性
- [ ] CI 集成 `pip-licenses --fail-on=LGPL` 与 `license-checker --failOn GPL`
- [ ] 评估 asyncpg 替代 psycopg2-binary 的可行性 (长期)

---

## 10. 参考资料

- SPDX 许可证列表: https://spdx.org/licenses/
- GNU LGPL FAQ: https://www.gnu.org/licenses/lgpl-faq.html
- Choose a License: https://choosealicense.com/
- pip-licenses: https://github.com/raimon49/pip-licenses
- license-checker: https://github.com/davglass/license-checker
