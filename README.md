# SignalFlow 🏛️

> automated AI information filtering and briefing pipeline。

SignalFlow 是一个每日 08:00 自动运行的信息筛选与简报生成系统。它从多个信源抓取内容，经质量评分筛选后生成结构化 AI 日报，推送到 QQ。12:30 独立推送知乎荐读文章。

**当前定位**：automated AI information filtering and briefing pipeline。  
**后续计划**：升级为 AI Search / RAG / Agent 系统。

---

## 架构概览

```
┌─ RSS 固定源 (P0/P1/P2) ──┐
│  iThome / VentureBeat     │
│  InfoQ / 36氪 / 雷锋网    │
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
- 知乎开放平台 Access Secret（[申请入口](https://developer.zhihu.com)）

### 安装

```bash
git clone https://github.com/<your>/signalflow.git
cd signalflow
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
0 8 * * * <project_dir>/news/scripts/generate.sh daily >> <project_dir>/news/logs/cron_$(date +\%Y-\%m-\%d).log 2>&1
30 12 * * * <project_dir>/news/scripts/zhihu-recommend.sh >> <project_dir>/news/logs/cron_zhihu_$(date +\%Y-\%m-\%d).log 2>&1
```

## 文件说明

```
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
└── sources.json          # 信息源配置（请按 .env.example 设置）

skills/
└── article-rating/       # 四维评分 skill
    └── SKILL.md
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 脚本 | Bash |
| 评分 | Python |
| 定时 | crontab |
| 数据 | JSON 文件系统 |
| 推送 | QQ 开放平台 |

## 知乎 API 配额

免费版每日 1000 次调用。日报生成使用约 5-15 次，荐读使用约 4 次。
超出会触发 `second limit exceeded`，需降低并发。

## License

MIT
