# SignalFlow 数据 Schema

采集文章的标准化 JSON 结构，用于 RSS 源和知乎平台采集结果。

## Article（单篇文章）

```json
{
  "id": "sha256(title + source + published_at)[:16]",
  "title": "文章标题",
  "source": {
    "name": "iThome",
    "priority": "P0",
    "type": "rss"
  },
  "url": "https://example.com/article/123",
  "published_at": "2026-05-25T08:00:00+08:00",
  "collected_at": "2026-05-25T08:05:00+08:00",
  "author": "作者名",
  "tags": ["AI", "大模型", "推理优化"],
  "summary": "文章摘要（长度 ≤ 500 字）",
  "content_length": 3200,
  "quality_score": 0.82,
  "grade": "fire",
  "notes": "可选：标注、提醒"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 内容指纹，SHA256(title+source+published_at) 取前 16 位，用于去重 |
| `title` | string | ✅ | 文章原文标题 |
| `source` | object | ✅ | 信源信息（见下方 Source） |
| `url` | string | ✅ | 原文链接 |
| `published_at` | string | ✅ | 原文发布时间，ISO 8601 |
| `collected_at` | string | ✅ | 采集时间，ISO 8601 |
| `author` | string | 否 | 作者名（RSS 无作者时可省略） |
| `tags` | string[] | 否 | 分类标签 |
| `summary` | string | ✅ | 文章摘要，≤ 500 字 |
| `content_length` | integer | 否 | 正文长度（字符数） |
| `quality_score` | float | ✅ | 质量评分 0.0 ~ 1.0（见评分公式） |
| `grade` | string | ✅ | 分级：`fire` / `important` / `brief` / `discard` |
| `notes` | string | 否 | 标注或提醒 |

## Source（信源）

```json
{
  "name": "iThome",
  "priority": "P0",
  "type": "rss"
}
```

### 字段说明

| 字段 | 类型 | 可选值 |
|------|------|--------|
| `name` | string | 信源名称 |
| `priority` | string | `P0` / `P1` / `P2` |
| `type` | string | `rss` / `webpage` / `zhihu_open_api` / `zhihu_hot_list` |

## 质量评分公式

```
score = source_weight × 0.5 + timeliness × 0.3 + info_density × 0.2
```

### 参数

| 参数 | 说明 | 取值 |
|------|------|------|
| `source_weight` | 信源权重 | P0: 0.95, P1: 0.75, P2: 0.60 |
| `timeliness` | 时效性 | 当天: 1.0, 前一天: 0.7, 更早: 0.3 |
| `info_density` | 信息密度 | >500 字: 1.0, 200-500: 0.7, <200: 0.4 |

### 分级

| grade | score 范围 | 标签 |
|-------|-----------|------|
| `fire` | ≥ 0.85 | 🔥 重大新闻 |
| `important` | ≥ 0.70 | 🔔 重要新闻 |
| `brief` | ≥ 0.50 | 📌 简略新闻 |
| `discard` | < 0.50 | 丢弃 |

## 四维评分（知乎文章）

知乎文章使用独立的四维评分体系，详见 `skills/article-rating/SKILL.md`。

```
总分 = 深度 × 0.35 + 原创性 × 0.25 + 实操性 × 0.25 + 标题质量 × 0.15
```

| grade | 范围 | 策略 |
|-------|------|------|
| A | ≥ 75 | 优先推送 |
| B | 60-74 | 备选 |
| C | < 60 | 不推送 |

## Report（完整日报）

```json
{
  "report_date": "2026-05-25",
  "report_type": "daily",
  "generated_at": "2026-05-25T08:00:00+08:00",
  "summary": "本日摘要",
  "keywords": ["MCP", "Agent", "推理优化"],
  "sections": {
    "fire": [Article, ...],
    "important": [Article, ...],
    "brief": [Article, ...]
  },
  "sources_summary": {
    "total": 8,
    "p0_count": 2,
    "p1_count": 3,
    "p2_count": 3
  },
  "notes": "..."
}
```

## 事件追踪

事件状态机：`active → cooling → closed`。

```json
{
  "id": "event_001",
  "keyword": "MCP 协议更新",
  "status": "active",
  "first_seen": "2026-05-23",
  "last_updated": "2026-05-25",
  "articles": ["<article_id>", ...],
  "timeline": [
    { "date": "2026-05-23", "summary": "..." },
    { "date": "2026-05-24", "summary": "..." }
  ]
}
```

| 状态 | 说明 |
|------|------|
| `active` | 正在进行的重大事件，每日追踪 |
| `cooling` | 已无新进展，观察 2 天后关闭 |
| `closed` | 事件收尾，存档 |
