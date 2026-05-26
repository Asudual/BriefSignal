"""
BriefSignal SQLite 存储层 — briefsignal/storage/sqlite_store.py

提供文章的持久化存储、导入与检索。
仅使用 Python 标准库（sqlite3, json, pathlib）。
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL_ARTICLES = """
CREATE TABLE IF NOT EXISTS articles (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    source       TEXT NOT NULL,
    url          TEXT,
    published_at TEXT,
    summary      TEXT,
    content      TEXT,
    total_score  REAL,
    grade        TEXT,
    created_at   TEXT
);
"""

_DDL_SCORES = """
CREATE TABLE IF NOT EXISTS scores (
    article_id    TEXT PRIMARY KEY,
    depth         INTEGER,
    originality   INTEGER,
    practicality  INTEGER,
    title_quality INTEGER,
    total         REAL,
    grade         TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
"""

_DDL_SOURCES = """
CREATE TABLE IF NOT EXISTS sources (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT UNIQUE NOT NULL,
    tier    TEXT,
    url     TEXT,
    enabled INTEGER DEFAULT 1
);
"""

_DDL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_articles_source      ON articles(source);",
    "CREATE INDEX IF NOT EXISTS idx_articles_total_score ON articles(total_score);",
    "CREATE INDEX IF NOT EXISTS idx_articles_grade       ON articles(grade);",
]


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db(db_path: str) -> None:
    """建表（幂等，可重复调用）。"""
    with _connect(db_path) as conn:
        conn.execute(_DDL_ARTICLES)
        conn.execute(_DDL_SCORES)
        conn.execute(_DDL_SOURCES)
        for idx_ddl in _DDL_INDEXES:
            conn.execute(idx_ddl)


def import_articles_from_json(json_path: str, db_path: str) -> int:
    """
    从 JSON 文件批量导入文章到 SQLite。

    已存在的 id 跳过（INSERT OR IGNORE），支持幂等导入。
    返回本次实际插入的记录数。
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON 文件不存在: {json_path}")

    with open(path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    if not isinstance(articles, list):
        raise ValueError("JSON 须为数组格式")

    init_db(db_path)

    inserted = 0
    with _connect(db_path) as conn:
        for art in articles:
            src = art.get("source", {})
            qs = art.get("quality_score", {})

            conn.execute(
                "INSERT OR IGNORE INTO sources (name, tier) VALUES (?, ?)",
                (src.get("name", ""), src.get("priority", "")),
            )

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO articles
                  (id, title, source, url, published_at, summary, content,
                   total_score, grade, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    art.get("id", ""),
                    art.get("title", ""),
                    src.get("name", ""),
                    art.get("url", ""),
                    art.get("published_at", ""),
                    art.get("summary", ""),
                    art.get("content") or "",
                    qs.get("total"),
                    qs.get("grade", ""),
                    art.get("collected_at", ""),
                ),
            )
            if cur.rowcount > 0:
                inserted += 1
                conn.execute(
                    """
                    INSERT OR IGNORE INTO scores
                      (article_id, depth, originality, practicality,
                       title_quality, total, grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        art.get("id", ""),
                        qs.get("depth"),
                        qs.get("originality"),
                        qs.get("practicality"),
                        qs.get("title_quality"),
                        qs.get("total"),
                        qs.get("grade", ""),
                    ),
                )

    return inserted


def get_article_by_id(db_path: str, article_id: str) -> dict | None:
    """按 id 返回 article dict（兼容 search_local 格式），不存在返回 None。"""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        if row is None:
            return None
        sc = conn.execute(
            "SELECT * FROM scores WHERE article_id = ?", (article_id,)
        ).fetchone()
        return _build_article_dict(row, sc)


def list_sources(db_path: str) -> list[str]:
    """返回所有已启用信源名称列表（按名称排序）。"""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sources WHERE enabled = 1 ORDER BY name"
        ).fetchall()
        return [r["name"] for r in rows]


def search_articles(
    db_path: str,
    query: str | None = None,
    source: str | None = None,
    min_score: float | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[dict]:
    """
    检索文章，返回 article dict 列表（兼容 search_local 格式），按 total_score 降序。

    参数：
        db_path:   SQLite 数据库路径
        query:     关键词（空格分隔，匹配 title + summary，大小写不敏感）
        source:    按信源名称过滤（部分匹配，大小写不敏感）
        min_score: 最低 total_score 阈值
        limit:     最多返回条数（默认 10）
        offset:    分页偏移（默认 0）
    """
    conditions: list[str] = []
    params: list = []

    if query:
        for kw in query.strip().split():
            conditions.append("(LOWER(a.title) LIKE ? OR LOWER(a.summary) LIKE ?)")
            params.extend([f"%{kw.lower()}%", f"%{kw.lower()}%"])

    if source:
        conditions.append("LOWER(a.source) LIKE ?")
        params.append(f"%{source.lower()}%")

    if min_score is not None:
        conditions.append("a.total_score >= ?")
        params.append(min_score)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT
            a.id, a.title, a.source, a.url, a.published_at, a.summary,
            a.content, a.total_score, a.grade,
            s.depth, s.originality, s.practicality, s.title_quality
        FROM articles a
        LEFT JOIN scores s ON a.id = s.article_id
        {where}
        ORDER BY a.total_score DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [_build_article_dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_article_dict(
    row: sqlite3.Row,
    scores_row: sqlite3.Row | None = None,
) -> dict:
    """
    将数据库行转换为与 search_local.search() 兼容的 article dict。

    - get_article_by_id 传入 (articles row, scores row)
    - search_articles 传入 (join row, None)，join row 已含 scores 列
    """
    if scores_row is not None:
        qs = {
            "depth": scores_row["depth"],
            "originality": scores_row["originality"],
            "practicality": scores_row["practicality"],
            "title_quality": scores_row["title_quality"],
            "total": scores_row["total"],
            "grade": scores_row["grade"],
        }
    else:
        qs = {
            "depth": row["depth"],
            "originality": row["originality"],
            "practicality": row["practicality"],
            "title_quality": row["title_quality"],
            "total": row["total_score"],
            "grade": row["grade"],
        }

    return {
        "id": row["id"],
        "title": row["title"],
        "source": {"name": row["source"]},
        "url": row["url"],
        "published_at": row["published_at"],
        "summary": row["summary"],
        "content": row["content"],
        "quality_score": qs,
    }
