# SignalFlow 本地检索

本地检索是 SignalFlow v0.2 的功能之一，提供对历史采集文章的快速关键词检索。它是未来 AI Search / RAG 前置功能的原型版本。

## 用途

- 在本地 JSON 数据中按关键词搜索文章标题、摘要和标签
- 按信源过滤：查看特定来源的历史文章
- 按质量评分过滤：只展示高分文章（A/B 级）
- 快速验证 data_schema 和采集数据的结构完整性
- 为后续 AI Search（结合 LLM 语义理解）和 RAG（知识库检索）提供基础架构

## 运行方式

### 基本用法

```bash
# 在项目根目录执行
python3 news/scripts/search_local.py --query 关键词

# 默认数据文件为 examples/sample_articles.json
# 可通过 --data 指定其他 JSON 文件
```

### 参数说明

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--data` | — | JSON 数据文件路径 | `--data data/my_articles.json` |
| `--query` | `-q` | 检索关键词，空格分隔多词 | `--query MCP Agent` |
| `--source` | `-s` | 按信源名称过滤（部分匹配） | `--source iThome` |
| `--min-score` | `-m` | 最低 quality_score.total 阈值 | `--min-score 60` |
| `--list-sources` | — | 列出数据中所有可用信源 | `--list-sources` |

### 示例

```bash
# 搜索 MCP 相关文章
python3 news/scripts/search_local.py --query MCP

# 搜索 Agent 相关，限 InfoQ 来源
python3 news/scripts/search_local.py --query Agent --source "InfoQ 中国"

# 搜索投融资，仅展示 B 级以上
python3 news/scripts/search_local.py --query 融资 --min-score 60

# 列出所有信源
python3 news/scripts/search_local.py --list-sources

# 查看 A 级（≥75）以上的所有文章
python3 news/scripts/search_local.py --min-score 75
```

**评分体系说明：**
- `quality_score.total` 满分 100，A 级 ≥ 75，B 级 ≥ 60，C 级 < 60
- `--min-score 75` = 只看 A 级，`--min-score 60` = A+B 级

> **评分体系说明**：search_local.py 使用的是 `quality_score.total`（0-100 范围），这是 Article Quality Score（文章质量评分）。
> 它不同于 `news/GENERATE_PROMPT.md` 中的 runtime filtering score（0~1 范围）。两层评分的关系见 `docs/scoring.md` 的 Two-Layer Scoring Design 节。

## 数据格式

数据文件须符合 `docs/data_schema.md` 中定义的 Article schema。

```json
{
  "id": "sha256(title+source+date)[:16]",
  "title": "文章标题",
  "source": { "name": "...", "priority": "P0", "type": "rss" },
  "url": "https://...",
  "published_at": "2026-05-25T08:00:00+08:00",
  "collected_at": "2026-05-25T08:05:00+08:00",
  "author": "作者",
  "tags": ["AI", "大模型"],
  "summary": "摘要内容",
  "content_length": 3200,
  "quality_score": {
    "depth": 4,
    "originality": 3,
    "practicality": 4,
    "title_quality": 4,
    "total": 75.0,
    "grade": "A"
  },
  "notes": ""
}
```

## 技术细节

- 仅依赖 Python 3 标准库（无需 pip install）
- 关键词匹配当前为**子串匹配**（大小写不敏感）
- 结果按 `quality_score` 降序排列
- 输出为人类可读格式（通过管道可接其他工具做 JSON 处理）

## 未来扩展

当前为 v0.2 原型版本。后续计划：

| 版本 | 特性 |
|------|------|
| v0.2（当前） | 关键词匹配、信源过滤、四维评分过滤 |
| v0.3 | 多词 AND/OR 组合、日期范围过滤 |
| v0.4 | JSON 输出模式（--json）、管道友好 |
| v0.5+ | 集成 LLM 语义搜索 → AI Search |
| v1.0 | 向量化 + RAG 知识库检索 |
