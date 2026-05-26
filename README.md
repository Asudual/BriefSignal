# BriefSignal 🏛️

> automated AI information filtering and briefing pipeline

## 中文简介

BriefSignal 是面向 AI 技术资讯的自动化筛选、评分与检索系统原型。

**当前能力：**
- 自动化 pipeline：多信源采集、质量评分、日报生成、定时推送
- 结构化 schema：标准化文章、信源、评分 JSON 结构
- 四维质量评分：深度 / 原创性 / 实操性 / 标题质量，0-100 分 + A/B/C 等级
- 本地检索：CLI 关键词搜索 + FastAPI 服务（/health /sources /search）
- SQLite 存储层：文章导入、检索、评分查询（实验性）
- 实验性 SQLite API：/sqlite/search、/sqlite/sources、/sqlite/articles/{id}
- 可选 API Key 认证：BRIEFSIGNAL_API_KEY 环境变量
- 测试与安全：pytest 测试套件（87 项）+ 自动化安全扫描脚本

**后续计划：** 探索 AI Search、RAG 与 Agent 化能力。

---

## Current Status (v0.3.1)

- ✅ automated AI information filtering and briefing pipeline
- ✅ structured article schema (docs/data_schema.md)
- ✅ four-dimensional content quality scoring (depth/originality/practicality/title_quality)
- ✅ local keyword search baseline (search_local.py)
- ✅ FastAPI service: /health /sources /search
- ✅ SQLite storage layer (briefsignal/storage/)
- ✅ JSON to SQLite import script (scripts/import_json_to_sqlite.py)
- ✅ experimental SQLite API under /sqlite/* (search / sources / article detail)
- ✅ optional API key support via BRIEFSIGNAL_API_KEY
- ✅ pytest test suite (87 tests)
- ✅ security scan script (scripts/security_scan.sh)
- 🔜 AI Search / RAG / Agent (see roadmap)

> The experimental SQLite API does not replace the existing JSON local search API.
> Existing `/search`, `/sources`, `/health` routes remain unchanged.

---

## 架构概览

```
┌─ RSS 固定源 (P0/P1/P2) ─────┐
│  iThome / VentureBeat / 橘鸦 │
│  BestBlogs / InfoQ / 36氪  │
│  Qwen Blog / 雷锋网         │
└─────────┬─────────────────┘
          ▼
┌─ 知乎开放平台 ────────────┐
│  global_search (5组查询)   │
│  hot_list (热榜 AI 过滤)   │
│  zhida (🔥新闻核实)       │
└─────────┬─────────────────┘
          ▼
    ┌───────────┐
    │ 质量评分   │ ← 四维评分 (深度/原创/实操/标题)
    │ 筛选去重   │
    └─────┬─────┘
          ▼
    ┌───────────┐
    │ 事件追踪   │ ← active → cooling → closed
    │ 报告生成   │
    └─────┬─────┘
          ▼
      推送 (QQ)
```

## 快速开始

### 前置条件

- Bash 5+
- Python 3.10+
- 可选：如需运行知乎相关采集模块，需自行配置知乎开放平台凭证

### 安装

```bash
git clone https://github.com/Asudual/BriefSignal.git
cd BriefSignal
cp .env.example .env
# 编辑 .env 填入 ZHIHU_ACCESS_SECRET
```

### 运行

```bash
# 手动执行一次日报生成
bash news/scripts/generate.sh daily

# 手动执行一次知乎荐读
bash news/scripts/zhihu-recommend.sh

# 设置 crontab（自行添加到系统 crontab）
0 8 * * * cd /path/to/BriefSignal && bash news/scripts/generate.sh daily >> news/logs/cron_$(date +\%Y-\%m-\%d).log 2>&1
30 12 * * * cd /path/to/BriefSignal && bash news/scripts/zhihu-recommend.sh >> news/logs/cron_zhihu_$(date +\%Y-\%m-\%d).log 2>&1
```

## 文件说明

```text
news/
├── scripts/              # 核心脚本
│   ├── generate.sh       # 日报生成（主入口）
│   ├── fetch.sh          # 信息源采集
│   ├── deliver.sh        # QQ 推送
│   ├── zhihu-recommend.sh # 知乎荐读（次入口）
│   ├── zhihu-fetch.sh    # 知乎 API 封装
│   ├── heartbeat-zhihu-check.sh  # 心跳巡检
│   └── zhihu-quality-scorer.py   # 质量评分
├── GENERATE_PROMPT.md    # 日报生成模板（模型指令）
├── sources.example.json  # 信息源配置示例（脱敏）
```

> 真实运行时可在本地复制 `news/sources.example.json` 为 `news/sources.json`，并自行配置；`sources.json` 不进入公开仓库。

```text
skills/
└── article-rating/       # 四维评分 skill
    └── SKILL.md
```

## 当前能力 (v0.3.1)

### CLI 本地检索

```bash
python3 news/scripts/search_local.py --query MCP
python3 news/scripts/search_local.py --source "InfoQ 中国" --min-score 60
python3 news/scripts/search_local.py --list-sources
```

### FastAPI 检索服务

```bash
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8080
```

| 端点 | 说明 |
|------|------|
| `GET /health` | 服务健康检查 |
| `GET /sources` | 列出可用信源 |
| `GET /search?query=MCP` | 检索文章（支持 query/source/min_score/limit） |

**实验性 SQLite API**（需设置 `BRIEFSIGNAL_DB_PATH`，不替换上方 JSON 检索）：

| 端点 | 说明 |
|------|------|
| `GET /sqlite/search` | SQLite 检索（支持 query/source/min_score/limit/offset） |
| `GET /sqlite/sources` | SQLite 信源列表 |
| `GET /sqlite/articles/{id}` | 按 id 查单篇文章 |

### 测试与安全

```bash
# 运行测试
pip install -r requirements-dev.txt
pytest tests/

# 安全扫描
bash scripts/security_scan.sh
```

详见 `docs/api.md`。

## 技术栈

| 组件 | 技术 |
|------|------|
| 脚本 | Bash |
| 评分 | Python |
| 定时 | crontab |
| 数据 | JSON 文件系统 + SQLite（experimental） |
| 推送 | QQ 开放平台 |

## 知乎 API 配额

免费版每日 1000 次调用。日报生成使用约 5-15 次，荐读使用约 4 次。
超出会触发 `second limit exceeded`，需降低并发。

## License

MIT
