# SignalFlow Design Decisions

关键设计取舍和背后的思考。

---

## 1. Why SignalFlow

**为什么从自动化 AI 资讯筛选开始，而不是直接做 AI Search / RAG / Agent？**

SignalFlow 的起点是一个每天 08:00 自动运行的日报系统。选择这个切入点的原因：

1. **每天一次的真实反馈循环** — 日报系统每天产生一次输出，你可以每天检查质量，发现问题后第二天就能修正。这比搭建一个复杂的 RAG 系统后才发现方向错了要快得多。

2. **多信源集成是最好的起点** — 任何一个 AI 搜索或知识系统的质量上限取决于它索引的内容质量。在搭建 RAG 之前，先搞清楚怎么稳定采集、筛选、评分，是更务实的路径。

3. **先有数据，再有智能** — v0.2 的 local search 直接在结构化 JSON 上做关键词检索，数据和你后续要做 RAG 的数据结构完全一致（data_schema.md）。embedding 和向量检索可以在同一份数据上叠加。

**这和后续 AI Search / RAG / Agent 的关系：**

```
v0.1 日报 pipeline  →  稳定的内容采集和质量标准
v0.2 结构化 + 检索  →  数据 schema 和本地搜索能力
v0.3 测试 + CI      →  工程基础
v0.4 embedding/RAG  →  在已有数据上叠加语义搜索
v0.5 Agent          →  将搜索和生成能力组合为智能工作流
```

每一层都依赖前一层。跳级会引入不必要的复杂度。

---

## 2. Source Priority Design

信源分三级（P0 / P1 / P2），每级对应不同的采集策略和权重。

### P0 — 核心主源

稳定性最高、信噪比最高的信源。日报生成时至少需要 1 个 P0 源成功。

- iThome：台湾繁体 IT 媒体，AI 覆盖全面，RSS 稳定
- VentureBeat AI：英文 AI 深度产业报道
- 橘鸦：AI 精选博客聚合，日更

**如果 P0 全部失败，日报标记异常但不阻塞发布** — 用 P1 源的内容补位。

### P1 — 专业补充

覆盖单一信源无法触达的信息面。至少需要 2 个 P1 源成功。

- BestBlogs：中文 AI 独立博客精选
- InfoQ 中国：技术社区新闻，AI 工程化实践
- 36氪：科技投融资，仅收录 AI/ML/算力相关
- Qwen Blog：通义千问官方技术博客

### P2 — 广度补充

低优先级，辅助覆盖信噪比不高但偶尔有独家内容的信源。

- 雷锋网：AI 科技媒体

### 设计原则

- **分级不是静态的** — 信源的可用性和信噪比会变化。原量子位因 403 被替换，表明分级需要维护。
- **权重对应采集优先级和评分权重** — 高权重信源的内容在日报评分中天然占优。
- **真实配置在本地 sources.json 中管理** — Git 公开仓库只保留脱敏示例。

---

## 3. Two-layer Scoring Design

两套评分体系，服务不同阶段。详见 `docs/scoring.md`。

### 第一层：Runtime Filtering Score

- **触发时机**：日报生成时，采集到文章后立即计算
- **计算方式**：自动化规则（信源权重 × 时效性 × 信息密度）
- **范围**：0 ~ 1 浮点
- **目的**：快速过滤，决定哪些内容进入日报候选池
- **不需要 LLM**：纯规则判定，低延迟

### 第二层：Article Quality Score

- **触发时机**：内容入库 / 结构化评估时
- **计算方式**：四维评分（depth / originality / practicality / title_quality），各维度 0-100
- **范围**：`total` 0-100，`grade` A/B/C
- **目的**：决定内容的长期价值和检索优先级
- **存储**：`quality_score` 对象，作为 Article schema 的一部分

### 为什么需要两层？

运行时筛选层是为了在有限时间窗口内快速决定推送内容。文章质量评分层是为了在历史数据中做持久化排序。前者像一个值班编辑，后者像一个档案管理员，职能不同。

---

## 4. Why Local Search Before RAG

**当前 v0.2 做了本地检索（search_local.py），而不是直接上 RAG。**

原因：

1. **数据质量 > 检索方式** — 向量检索解决的是语义匹配问题，但如果数据本身是脏的、schema 不一致的，再好的检索也救不了。先建立结构化数据标准。

2. **明确的搜索需求比模糊的语义搜索更常见** — 在实际操作中，"搜一下前几天那篇关于 MCP 的文章"（关键词匹配）比"帮我找一下语义上类似上个月那篇的材料"（向量检索）更频繁。

3. **keyword search 是 RAG 的 baseline** — keyword recall 是所有检索系统的基线。如果关键词搜索效果不好，加 embedding 只会放大问题。

4. **渐进式升级路径**：
   - 当前：keyword match → filter → sort by score
   - v0.3：添加 fuzzy / regex / date range
   - v0.4：embedding → vector search → hybrid search
   - v0.5：LLM-based rerank → RAG pipeline

每一步都可以独立验证效果。

---

## 5. Public Repo Safety Design

| 策略 | 原因 |
|------|------|
| **真实 sources.json 不入仓库** | 包含知乎 API Bearer Token（硬编码风险），信源 URL 和认证方式属于生产配置 |
| **使用 sources.example.json** | 公开脱敏信源结构和示例，保留文档价值 |
| **.env 不入仓库** | 环境变量配置（ZHIHU_ACCESS_SECRET / DELIVERY_TARGET 等），.gitignore 已排除 |
| **.env.example 入仓库** | 模板文件，只含字段名和占位符 |
| **logs/ / raw/ / 历史日报不入仓库** | 日志含运行时信息、历史日报含已推送内容，属于运行数据 |
| **OpenClaw 身份文件（SOUL/USER/AGENTS 等）不入仓库** | 包含个人偏好、交互习惯，属于本地配置 |
| **DELIVERY_TARGET 硬编码风险** | v0.1 修复：脚本中真实 QQ Target ID 已替换为 `${DELIVERY_TARGET:?}`，现在通过 .env 注入 |
| **团队技能（skills/ 下的第三方）不入仓库** | 各有所属，公开仓库只保留自定义 skill（article-rating） |

### 原则

- **代码入仓库，配置不进**
- **示例数据入仓库，真实运行数据不进**
- **脱敏架构入仓库，认证信息不进**
- **运行环境配置靠 .env + .gitignore**

---

## 6. Role of article-rating Skill

`skills/article-rating/SKILL.md` 是一个 **内容质量评分 skill**，不是搜索 skill。

### 它做什么

- 接收上游提供的文章标题 + 正文
- 按排除规则过滤（广告、短文、标题党）
- 在理解全文后，按四维评分（depth / originality / practicality / title_quality）逐维打分
- 输出 total（0-100）和 grade（A/B/C）

### 它不做什么

- 不主动搜索文章
- 不采集数据
- 不管理信源
- 不生成日报

### 设计原因

评分和采集是分离的责任。采集层负责把素材拿来，评分层负责判断素材好不好。合在一起会引入耦合（比如"这个 skill 会搜索吗？它是我的搜索入口吗？"），分开后每个组件职责清晰。

---

## 7. Roadmap Direction

| 版本 | 重点 | 状态 |
|------|------|------|
| v0.1 | 日报 pipeline + 多信源 + crontab + 安全清理 | ✅ 完成 |
| v0.2 | 结构化数据 + 统一评分体系 + 本地检索 | ✅ 完成 |
| v0.3 | 测试、shellcheck、安全扫描 CI、参数校验 | 📅 进行中 |
| v0.4 | embedding + vector search + hybrid 检索、RAG prototype | 规划中 |
| v0.5 | Agent workflow / tool calling / 多 Agent 协作 | 规划中 |

详见 `docs/roadmap.md`。
