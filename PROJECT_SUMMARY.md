# BriefSignal — Project Summary

> **自动化 AI 信息筛选与简报生成系统原型**

---

## 项目简介 / What It Is

BriefSignal 是一个面向 AI 技术资讯的自动化筛选、评分与检索系统原型。从多源信息流（RSS 源、知乎开放平台）中采集文章，通过结构化质量评估筛选出高质量内容，生成每日简报并推送。

在 v0.3.0 中，BriefSignal 还提供了本地检索 API（FastAPI），支持在结构化文章数据上做关键词/信源/评分阈值检索，以及 pytest 测试套件和自动化安全扫描脚本。

---

## 为什么做这个项目 / Why I Built It

原始动机很实际：在多个语言和平台上跟踪 AI 技术动态很耗时。我需要一个自动化 pipeline 来解决四个问题：

1. **采集** — 从不同信源拉取，不需要手动浏览
2. **筛选** — 用结构化质量标准判断内容好坏，不只是关键词匹配
3. **交付** — 固定时间产出可读的每日简报
4. **迭代** — 从简单的 cron 作业起步，逐步增加 search、scoring、service 层

项目从 Bash/Python cron 作业开始，逐步演进为具备结构化 schema、可复用评分 skill、本地检索 API、测试套件的系统——同时保持核心逻辑简单（无数据库、无 LLM API 调用，除了最初的日报生成步骤之外）。

---

## 当前能力 / Current Capabilities (v0.3.0)

| 层级 | 能力 | 状态 |
|------|------|------|
| **Pipeline** | RSS + 知乎开放平台多信源采集 | ✅ |
| **评分** | 双层评分：运行时筛选（自动化规则）+ 文章质量评分（四维 0-100） | ✅ |
| **Schema** | 标准化 JSON 结构：文章、信源、评分、事件追踪 | ✅ |
| **CLI 检索** | 关键词/信源/评分阈值本地检索 | ✅ |
| **API 服务** | FastAPI: `/health`, `/sources`, `/search` | ✅ |
| **测试** | 17 个 pytest 测试用例覆盖检索核心函数 | ✅ |
| **安全** | 自动化安全扫描脚本（硬编码 token/secret/path 检测） | ✅ |
| **文档** | 架构、评分、数据 schema、设计取舍、API 文档 | ✅ |

---

## 工程设计亮点 / Engineering Design Highlights

### 1. 双层评分（Two-Layer Scoring）

BriefSignal 将**运行时筛选**（快速自动化规则，决定哪些内容进入候选池）与**文章质量评分**（四维 0-100 评分，随文章一起存储）分开。这让每日生成既有速度优势，历史检索又有精度保证。

### 2. 信源优先级 P0/P1/P2

信源按可靠性和信噪比分级。P0 源始终必须采集成功；P1/P2 源增加信息广度。防止单一信源故障拖垮整个日报。

### 3. 先定义数据 Schema，再做 RAG

文章 schema（`docs/data_schema.md`）从一开始就设计为与未来 embedding 和向量检索兼容。每篇文章携带标准化的 `quality_score` 对象，后续可作为检索的相关性信号。

### 4. 安全优先的仓库设计

公开仓库只包含示例和文档。真实凭证（`ZHIHU_ACCESS_SECRET`、`DELIVERY_TARGET`）通过 `.env` 管理。安全扫描脚本（`scripts/security_scan.sh`）在 CI 前捕获意外硬编码。

---

## 为什么先做 Local Search 再做 RAG / Why Local Search Before RAG

项目有意在语义检索之前先建立关键词搜索：

1. **关键词搜索是基线** — 如果基础文本匹配都找不到需要的内容，加向量只会放大问题
2. **数据质量优先** — 向量检索的质量取决于数据结构。先结构化数据（v0.2）、然后服务化（v0.3），意味着 RAG（v0.4+）将运行在干净一致的数据上
3. **渐进式复杂度** — 每层增加一种能力，不需要重写上一层。v0.2 用于本地检索的 `examples/sample_articles.json`，v0.4 将用于 embedding

---

## 后续计划 / Next Steps

| 版本 | 重点 | 状态 |
|------|------|------|
| v0.3.1 | Dockerfile, GitHub Actions CI, shellcheck | 📅 计划中 |
| v0.4 | embedding, vector search, hybrid 检索, RAG 原型 | 📅 计划中 |
| v0.5 | Agent workflow, 多 Agent 协作 | 📅 计划中 |
| v1.0 | 产品化, 管理界面, 多渠道推送 | 📅 长期 |

---

## 适合结合的方向

BriefSignal 的架构设计使其容易与以下方向结合：

| 方向 | 结合点 |
|------|--------|
| **云计算 / DevOps** | Docker 容器化部署、Kubernetes 调度、CI/CD 自动化运维 |
| **AI4Science** | 接入 AI4Science 论文源（ArXiv/BioRxiv），生成学科领域每日文献简报 |
| **AI Search** | 在现有 keyword search 基础上叠加 embedding + rerank，构建混合检索 |
| **Agent Infrastructure** | 将 pipeline 各环节重构为可编排的 Agent 工作流（采集 Agent → 评分 Agent → 推送 Agent） |
| **LLM Ops / 评测** | 用评分系统做 LLM 输出质量评估，积累评估数据集 |

---

## Repository

https://github.com/Asudual/BriefSignal

MIT License.
