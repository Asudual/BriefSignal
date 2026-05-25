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
  "quality_score": {
    "depth": 80,
    "originality": 60,
    "practicality": 75,
    "title_quality": 75,
    "total": 73.0,
    "grade": "B"
  },
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
| `quality_score` | object | ✅ | 四维评分（见下方 QualityScore） |
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

## QualityScore（四维评分）

```json
{
  "depth": 80,
  "originality": 60,
  "practicality": 75,
  "title_quality": 75,
  "total": 73.0,
  "grade": "B"
}
```

### 字段说明

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `depth` | integer | 0-100 | 内容深度 |
| `originality` | integer | 0-100 | 原创性 |
| `practicality` | integer | 0-100 | 实操价值 |
| `title_quality` | integer | 0-100 | 标题质量 |
| `total` | float | 0-100 | 加权总分 = depth×0.35 + originality×0.25 + practicality×0.25 + title_quality×0.15 |
| `grade` | string | A/B/C | A ≥ 75, B ≥ 60, C < 60 |

### 分级

| grade | total 范围 | 策略 |
|-------|-----------|------|
| **A** | ≥ 75 | 优先推送，进入日报/荐读 |
| **B** | 60 - 74 | 备选，可能进入候选池 |
| **C** | < 60 | 低优先级，自动过滤 |

> `quality_score` 指的是 **Article Quality Score**（第二层评分），不是 GENERATE_PROMPT.md 中的 runtime filtering score。
> 四维评分的详细判据见 `docs/scoring.md`。
> RSS 源采集的文章也使用此结构，各维度由自动化规则填充。



## Report（完整日报）

```json
{
  "report_date": "2026-05-25",
  "report_type": "daily",
  "generated_at": "2026-05-25T08:00:00+08:00",
  "summary": "本日摘要",
  "keywords": ["MCP", "Agent", "推理优化"],
  "sections": {
    "A": [Article, ...],
    "B": [Article, ...],
    "C": [Article, ...]
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
