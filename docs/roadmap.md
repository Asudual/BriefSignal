# SignalFlow 路线图

## 当前状态 (v0.1)

自动化 AI 资讯筛选与推送 pipeline，每日 08:00 执行。

**已完成：**
- [x] 三层信源架构（RSS + 知乎搜索 + 热榜）
- [x] 质量评分与四维筛选
- [x] 事件追踪状态机
- [x] 知乎 API 集成与限速控制
- [x] 容错与失败告警
- [x] crontab 定时调度

---

## 近期计划

### v0.2 — 结构化数据与本地检索
- [x] sources.example.json（脱敏信源示例）
- [x] data_schema.md（统一 JSON schema）
- [x] scoring.md（四维评分判据文档）
- [x] sample_articles.json（脱敏模拟示例数据）
- [x] search_local.py（关键词/信源/评分过滤检索）
- [x] 评分体系统一为 0-100 四维评分

### v0.3 — 安全与开发体验
- [ ] 完善 .env 配置体系
- [ ] 添加单元测试与集成测试
- [ ] 脚本参数校验与帮助信息
- [ ] CI（GitHub Actions）：lint + shellcheck + 安全扫描
- [ ] Contribution guide

### v0.3 — 搜索引擎升级
- [ ] 接入 Brave / SerpAPI 作为知乎备选
- [ ] 本地缓存层，减少重复 API 调用
- [ ] 多语言搜索（英文/日文源）
- [ ] 搜索历史与去重优化

---

## 中期计划

### v0.4 — 知识库与记忆
- [ ] 引入 RAG 存储每日抓取内容
- [ ] 事件追踪升级为向量记忆
- [ ] 支持用户追问历史新闻
- [ ] 热点趋势周报自动生成

### v0.5 — Agent 化
- [ ] 将 pipeline 重构为 Agent 架构
- [ ] 支持自然语言指令：「帮我找找这周 GPU 相关的新闻」
- [ ] 多 Agent 协作（采集 Agent / 评分 Agent / 推送 Agent）

---

## 长期计划

### v1.0 — 产品化
- [ ] FastAPI 后端，暴露 REST API
- [ ] Web 管理界面（新闻查看、评分调整、配置）
- [ ] Docker 容器化一键部署
- [ ] 多推送渠道（Telegram / Discord / Email）
- [ ] 用户自定义信源和评分权重

### v1.5+ — 社区
- [ ] 公开 Docker 镜像
- [ ] Python SDK 或 CLI 工具
- [ ] 插件式信源架构（第三方可贡献）
- [ ] 多用户多租户支持

---

> **说明**：以上计划按优先顺序排列，非承诺。实际进度取决于维护者时间。
