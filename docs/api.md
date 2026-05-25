# SignalFlow API v0.3.0

本地检索服务 API。使用 FastAPI 提供 HTTP 接口。

**版本：** v0.3.0 — 本地检索服务化阶段。不接 LLM API、不接真实知乎 API、不使用 GitHub Secrets。

---

## 启动方式

```bash
# 安装依赖
pip install -r app/requirements.txt

# 启动服务（开发模式，热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# 启动服务（生产模式）
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

访问 http://localhost:8080/docs 可查看交互式 API 文档（Swagger UI）。

---

## 端点

### GET /health

服务健康检查。

**请求：**
```bash
curl http://localhost:8080/health
```

**响应：**
```json
{
  "status": "ok",
  "version": "0.3.0"
}
```

---

### GET /sources

列出数据中所有可用信源。

**请求：**
```bash
curl http://localhost:8080/sources
```

**响应：**
```json
{
  "sources": [
    "36氪",
    "BestBlogs",
    "InfoQ 中国",
    "Qwen Blog",
    "iThome",
    "橘鸦AI早报",
    "雷锋网"
  ]
}
```

---

### GET /search

检索文章。支持关键词、信源、评分阈值过滤。

**参数：**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `query` | string | 否 | — | 检索关键词（空格分隔多词，匹配 title + summary + tags） |
| `source` | string | 否 | — | 按信源名称过滤（部分匹配） |
| `min_score` | float | 否 | 0.0 | 最低 quality_score.total 阈值，范围 0-100（A级≥75, B级≥60） |
| `limit` | integer | 否 | 20 | 最多返回条数，范围 1-100 |

**请求示例：**

```bash
# 搜索 MCP 相关文章
curl --get --data-urlencode "query=MCP" http://localhost:8080/search

# 搜索推理相关，只看 A 级
curl --get --data-urlencode "query=推理" --data-urlencode "min_score=75" http://localhost:8080/search

# 按信源过滤
curl --get --data-urlencode "source=InfoQ 中国" http://localhost:8080/search

# 查看评分 75 以上的所有文章
curl --get --data-urlencode "min_score=75" http://localhost:8080/search

# 限定返回 3 条
curl --get --data-urlencode "query=Agent" --data-urlencode "limit=3" http://localhost:8080/search
```

**响应结构：**

```json
{
  "query": "MCP",
  "filters": {
    "source": null,
    "min_score": 0.0,
    "limit": 20
  },
  "total": 1,
  "results": [
    {
      "id": "a1b2...",
      "title": "MCP 协议迎来 v2.0 更新...",
      "source": {
        "name": "橘鸦AI早报",
        "priority": "P0",
        "type": "rss"
      },
      "url": "https://example.com/...",
      "published_at": "2026-05-25T07:30:00+08:00",
      "collected_at": "2026-05-25T07:35:00+08:00",
      "author": "示例作者",
      "tags": ["MCP", "Agent", "协议"],
      "summary": "文章摘要内容...",
      "content_length": 2800,
      "quality_score": {
        "depth": 80,
        "originality": 75,
        "practicality": 95,
        "title_quality": 80,
        "total": 82.3,
        "grade": "A"
      },
      "notes": "技术突破类"
    }
  ]
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | string/null | 请求时传入的查询词 |
| `filters` | object | 请求时传入的过滤条件 |
| `filters.source` | string/null | 请求时传入的信源过滤 |
| `filters.min_score` | float | 请求时传入的最低评分阈值 |
| `filters.limit` | integer | 请求时传入的数量限制 |
| `total` | integer | 本次匹配的结果总数 |
| `results` | array | 文章列表，按 total 降序排列 |

**results 中的文章字段符合 `docs/data_schema.md` 中的 Article schema。** 其中 `quality_score` 对象包含：

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `depth` | integer | 0-100 | 内容深度 |
| `originality` | integer | 0-100 | 原创性 |
| `practicality` | integer | 0-100 | 实操价值 |
| `title_quality` | integer | 0-100 | 标题质量 |
| `total` | float | 0-100 | 加权总分 |
| `grade` | string | A/B/C | A ≥ 75, B ≥ 60, C < 60 |

---

## 错误处理

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 正常返回 |
| 400 | 参数错误（如 min_score < 0 或 > 100） |
| 500 | 服务端错误（如数据文件缺失） |

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

---

## 边界说明

- **v0.3.0 不接 LLM API** — FastAPI 不调用任何外部模型，只做本地检索
- **v0.3.0 不使用 GitHub Secrets** — 在配置好 .github/workflows 前不会用到 secrets
- **v0.3.0 使用脱敏 mock 数据** — 默认加载 `examples/sample_articles.json`，可通过 `--data` 参数指定其他 JSON 文件
- **不接真实知乎 API** — 搜索范围限于本地 JSON 数据
