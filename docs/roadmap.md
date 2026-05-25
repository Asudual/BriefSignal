# SignalFlow 路线图

## 当前状态 (v0.3.0)

自动化 AI 信息筛选与简报生成系统，已具备日报 pipeline、结构化数据、统一评分体系和本地检索服务。

**已完成：**
### v0.1 — 日报 pipeline
- [x] 三层信源架构（RSS + 知乎搜索 + 热榜）
- [x] 质量评分与四维筛选
- [x] 事件追踪状态机
- [x] 知乎 API 集成与限速控制
- [x] 容错与失败告警
- [x] crontab 定时调度

### v0.2 — 结构化数据与本地检索
- [x] sources.example.json（脱敏信源示例）
- [x] data_schema.md（统一 JSON schema）
- [x] scoring.md（四维评分判据文档）
- [x] sample_articles.json（脱敏模拟示例数据）
- [x] search_local.py（关键词/信源/评分过滤检索）
- [x] 评分体系统一为 0-100 四维评分

### v0.3.0 — Service & Test ✅
- [x] search_local.py 模块化重构（可 import）
- [x] FastAPI 服务（/health、/search、/sources）
- [x] pytest 测试（17 个测试用例）
- [x] scripts/security_scan.sh（安全扫描脚本）
- [x] docs/api.md（API 文档）
- [x] .gitignore 补充（app/ __pycache__/ 等）

---

## 近期计划

### v0.3.1 — CI & Container
- [ ] Dockerfile（一键启动 FastAPI 服务）
- [ ] GitHub Actions（pytest + security scan 自动运行）
- [ ] shellcheck（Bash 脚本静态检查）
- [ ] README badge（测试通过 / 安全扫描通过）

### v0.3.x — 搜索引擎升级
- [ ] 接入 Brave / SerpAPI 作为知乎备选
- [ ] 本地缓存层，减少重复 API 调用
- [ ] 多语言搜索（英文/日文源）
- [ ] 搜索历史与去重优化

---

## 中期计划

### v0.4 — 知识库与记忆
- [ ] embedding + vector search + hybrid 检索
- [ ] RAG prototype（基于已有结构化数据）
- [ ] 事件追踪升级为向量记忆
- [ ] 支持用户追问历史新闻

### v0.5 — Agent 化
- [ ] 将 pipeline 重构为 Agent 架构
- [ ] 支持自然语言指令
- [ ] 多 Agent 协作（采集 / 评分 / 推送）

---

## 长期计划

### v1.0 — 产品化
- [ ] Web 管理界面（新闻查看、评分调整、配置）
- [ ] Docker Compose 一键部署（API + 前端）
- [ ] 多推送渠道（Telegram / Discord / Email）
- [ ] 用户自定义信源和评分权重

### v1.5+ — 社区
- [ ] 公开 Docker 镜像
- [ ] Python SDK 或 CLI 工具
- [ ] 插件式信源架构
- [ ] 多用户多租户支持

---

> **说明**：以上计划按优先顺序排列，非承诺。实际进度取决于维护者时间。
