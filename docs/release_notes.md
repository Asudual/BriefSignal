# BriefSignal Release Notes

---

## v0.3.1 — 2026-05-26

### 概述

v0.3.1 在现有 JSON 本地检索基础上新增了 SQLite 存储层和实验性 FastAPI SQLite 路由。
**BriefSignal 仍然是 AI 技术资讯筛选与检索系统原型，不是完整的 RAG 系统或 Agent 平台。**

---

### 新增功能

#### SQLite 存储层（`briefsignal/storage/`）

- 新增 `briefsignal/storage/sqlite_store.py`，使用 Python 标准库 `sqlite3` 实现
- 数据库 schema：`articles`、`scores`、`sources` 三张表，含常用索引
- 公开函数：
  - `init_db(db_path)` — 建表（幂等）
  - `import_articles_from_json(json_path, db_path)` — 批量导入，支持幂等（已存在 id 跳过）
  - `search_articles(db_path, ...)` — 关键词 / 信源 / 评分阈值 / 分页检索
  - `list_sources(db_path)` — 列出已启用信源
  - `get_article_by_id(db_path, article_id)` — 按 id 查单篇文章
- `search_articles` 参数边界检查：`limit` 必须为 int 且 1–100，`offset` 必须为 int 且 ≥ 0
- `get_article_by_id` 使用 `LEFT JOIN scores`，scores 行缺失时不崩溃，缺失维度返回 `None`

#### JSON → SQLite 导入脚本（`scripts/import_json_to_sqlite.py`）

- CLI 脚本，将 JSON 文章数组导入指定 SQLite 数据库
- 兼容 `examples/sample_articles.json`，`content` 字段缺失时使用空字符串，不报错

#### 实验性 FastAPI SQLite 路由（`app/sqlite_api.py`）

> **⚠️ 实验性功能，接口结构可能变更，不替换现有 JSON 检索 API。**

新增路由前缀 `/sqlite`：

| 端点 | 说明 |
|------|------|
| `GET /sqlite/search` | 检索文章（支持 query / source / min_score / limit / offset） |
| `GET /sqlite/sources` | 列出已启用信源 |
| `GET /sqlite/articles/{article_id}` | 按 id 获取单篇文章 |

响应结构包含 `"backend": "sqlite"` 标识，错误响应统一格式：

```json
{
  "detail": {
    "error": {
      "code": "...",
      "message": "..."
    }
  }
}
```

错误码：`DB_NOT_CONFIGURED` / `DB_NOT_AVAILABLE` / `NOT_FOUND` / `INVALID_API_KEY` / `INVALID_PARAMS` / `INTERNAL_ERROR`

#### 可选 API Key 认证

- 通过环境变量 `BRIEFSIGNAL_API_KEY` 配置，未设置时不启用（本地开发友好）
- 设置后请求须携带 `X-API-Key` 标头
- 使用 `hmac.compare_digest` 防止计时攻击

#### 数据库路径配置

- 通过环境变量 `BRIEFSIGNAL_DB_PATH` 指定 SQLite 文件路径
- 未设置时 `/sqlite/*` 路由返回 `503 DB_NOT_CONFIGURED`
- 文件不存在时返回 `503 DB_NOT_AVAILABLE`，不暴露服务器路径

---

### 不变内容

- 现有 `/health`、`/sources`、`/search` 路由**完全未修改**
- `news/scripts/search_local.py` JSON 本地检索逻辑**未修改**
- JSON local search 与 SQLite storage 并存，互不影响

---

### 测试

- 测试总数从 17 增至 **87 passed**
- 新增：`tests/test_sqlite_store.py`（39 项，覆盖存储层、边界检查、scores 缺失稳定性）
- 新增：`tests/test_sqlite_api.py`（30 项，覆盖 API 响应结构、分页、认证、DB 未配置、旧路由不受影响）
- 开发依赖新增 `httpx>=0.27.0`（FastAPI TestClient 所需）

---

### 变更文件清单

| 文件 | 操作 |
|------|------|
| `briefsignal/__init__.py` | 新增 |
| `briefsignal/storage/__init__.py` | 新增 |
| `briefsignal/storage/sqlite_store.py` | 新增 |
| `scripts/import_json_to_sqlite.py` | 新增 |
| `app/sqlite_api.py` | 新增 |
| `app/main.py` | 修改（注册 sqlite_router） |
| `tests/test_sqlite_store.py` | 新增 |
| `tests/test_sqlite_api.py` | 新增 |
| `docs/api.md` | 修改（追加 experimental SQLite API 章节） |
| `requirements-dev.txt` | 修改（添加 httpx） |
| `.gitignore` | 修改（添加 `*.db`） |

---

### 已知限制

- SQLite `search_articles` 使用 `LIKE` 匹配，不支持全文索引（FTS），大数据量下性能有限
- FastAPI query 参数校验失败返回 FastAPI 原生 `422`，格式与自定义错误结构不同（计划后续统一）
- `import_articles_from_json` 不做字段类型校验，坏数据可能触发 SQLite 写入异常
- SQLite 路由仅做数据层原型验证，尚未接入生产数据源

---

## v0.3.0 — 2026-05-01（基线）

- FastAPI 服务：`/health` `/sources` `/search`
- `search_local.py` JSON 本地关键词检索
- 四维质量评分（depth / originality / practicality / title_quality）
- pytest 测试套件（17 项）
- `scripts/security_scan.sh` 安全扫描脚本
