"""
BriefSignal SQLite 存储层测试

- 全部使用 tmp_path（pytest fixture）管理临时数据库文件
- 不生成真实数据库文件进仓库
- 不连接任何外部服务
"""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from briefsignal.storage.sqlite_store import (
    get_article_by_id,
    import_articles_from_json,
    init_db,
    list_sources,
    search_articles,
)

TEST_DATA = Path(__file__).resolve().parent / "test_data" / "sample_articles.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path) -> str:
    """空数据库路径（pytest 管理生命周期，测试结束自动清理）"""
    return str(tmp_path / "test.db")


@pytest.fixture()
def populated_db(tmp_path) -> str:
    """已导入 7 条测试文章的数据库"""
    db = str(tmp_path / "populated.db")
    import_articles_from_json(str(TEST_DATA), db)
    return db


# ---------------------------------------------------------------------------
# TestInitDb
# ---------------------------------------------------------------------------


class TestInitDb:
    def test_creates_all_tables(self, tmp_db):
        init_db(tmp_db)
        conn = sqlite3.connect(tmp_db)
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "articles" in tables
        assert "scores" in tables
        assert "sources" in tables

    def test_is_idempotent(self, tmp_db):
        init_db(tmp_db)
        init_db(tmp_db)


# ---------------------------------------------------------------------------
# TestImportFromJson
# ---------------------------------------------------------------------------


class TestImportFromJson:
    def test_imports_all_articles(self, tmp_db):
        count = import_articles_from_json(str(TEST_DATA), tmp_db)
        assert count == 7

    def test_is_idempotent(self, tmp_db):
        count1 = import_articles_from_json(str(TEST_DATA), tmp_db)
        count2 = import_articles_from_json(str(TEST_DATA), tmp_db)
        assert count1 == 7
        assert count2 == 0

    def test_file_not_found(self, tmp_db):
        with pytest.raises(FileNotFoundError):
            import_articles_from_json("nonexistent_file.json", tmp_db)

    def test_invalid_json_raises(self, tmp_path, tmp_db):
        bad = tmp_path / "bad.json"
        bad.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(Exception):
            import_articles_from_json(str(bad), tmp_db)

    def test_not_list_raises(self, tmp_path, tmp_db):
        bad = tmp_path / "notlist.json"
        bad.write_text('{"key": "value"}', encoding="utf-8")
        with pytest.raises(ValueError):
            import_articles_from_json(str(bad), tmp_db)

    def test_populates_sources_table(self, tmp_db):
        import_articles_from_json(str(TEST_DATA), tmp_db)
        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        conn.close()
        assert count == 7

    def test_populates_scores_table(self, tmp_db):
        import_articles_from_json(str(TEST_DATA), tmp_db)
        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
        conn.close()
        assert count == 7


# ---------------------------------------------------------------------------
# TestGetArticleById
# ---------------------------------------------------------------------------


class TestGetArticleById:
    def test_returns_correct_title(self, populated_db):
        result = get_article_by_id(populated_db, "a1b2c3d4e5f60718")
        assert result is not None
        assert result["title"] == "MCP 协议迎来 v2.0 更新，支持动态工具发现"

    def test_returns_none_for_missing_id(self, populated_db):
        assert get_article_by_id(populated_db, "nonexistent_id_xyz") is None

    def test_quality_score_total(self, populated_db):
        result = get_article_by_id(populated_db, "a1b2c3d4e5f60718")
        assert result["quality_score"]["total"] == 82.3

    def test_quality_score_grade(self, populated_db):
        result = get_article_by_id(populated_db, "a1b2c3d4e5f60718")
        assert result["quality_score"]["grade"] == "A"

    def test_quality_score_dimensions(self, populated_db):
        result = get_article_by_id(populated_db, "a1b2c3d4e5f60718")
        qs = result["quality_score"]
        assert qs["depth"] == 80
        assert qs["originality"] == 75
        assert qs["practicality"] == 95
        assert qs["title_quality"] == 80

    def test_source_is_dict(self, populated_db):
        result = get_article_by_id(populated_db, "a1b2c3d4e5f60718")
        assert isinstance(result["source"], dict)
        assert result["source"]["name"] == "橘鸦AI早报"

    def test_result_keys(self, populated_db):
        result = get_article_by_id(populated_db, "a1b2c3d4e5f60718")
        for key in ("id", "title", "source", "url", "published_at", "summary",
                    "content", "quality_score"):
            assert key in result


# ---------------------------------------------------------------------------
# TestListSources
# ---------------------------------------------------------------------------


class TestListSources:
    def test_returns_all_sources(self, populated_db):
        sources = list_sources(populated_db)
        expected = {"36氪", "BestBlogs", "InfoQ 中国", "Qwen Blog",
                    "iThome", "橘鸦AI早报", "雷锋网"}
        assert set(sources) == expected

    def test_sorted(self, populated_db):
        sources = list_sources(populated_db)
        assert sources == sorted(sources)

    def test_empty_db(self, tmp_db):
        init_db(tmp_db)
        assert list_sources(tmp_db) == []


# ---------------------------------------------------------------------------
# TestSearchArticles
# ---------------------------------------------------------------------------


class TestSearchArticles:
    def test_no_filters_returns_all(self, populated_db):
        results = search_articles(populated_db, limit=100)
        assert len(results) == 7

    def test_default_limit_10(self, populated_db):
        results = search_articles(populated_db)
        assert len(results) == 7

    def test_sorted_by_score_desc(self, populated_db):
        results = search_articles(populated_db, limit=100)
        scores = [r["quality_score"]["total"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_keyword_mcp(self, populated_db):
        results = search_articles(populated_db, query="MCP")
        assert len(results) >= 1
        assert any("MCP" in r["title"] for r in results)

    def test_keyword_qwen3(self, populated_db):
        results = search_articles(populated_db, query="Qwen3")
        assert len(results) == 1
        assert results[0]["quality_score"]["grade"] == "A"

    def test_keyword_no_match(self, populated_db):
        results = search_articles(populated_db, query="nosuchtermlikely")
        assert len(results) == 0

    def test_filter_by_source(self, populated_db):
        results = search_articles(populated_db, source="InfoQ")
        assert len(results) == 1
        assert results[0]["source"]["name"] == "InfoQ 中国"

    def test_filter_by_source_partial_match(self, populated_db):
        results = search_articles(populated_db, source="infoq")
        assert len(results) == 1

    def test_min_score_75_returns_a_grade(self, populated_db):
        results = search_articles(populated_db, min_score=75, limit=100)
        assert len(results) == 3
        for r in results:
            assert r["quality_score"]["grade"] == "A"

    def test_min_score_0_returns_all(self, populated_db):
        results = search_articles(populated_db, min_score=0, limit=100)
        assert len(results) == 7

    def test_limit(self, populated_db):
        results = search_articles(populated_db, limit=3)
        assert len(results) == 3

    def test_offset_pagination(self, populated_db):
        page1 = search_articles(populated_db, limit=3, offset=0)
        page2 = search_articles(populated_db, limit=3, offset=3)
        ids1 = {r["id"] for r in page1}
        ids2 = {r["id"] for r in page2}
        assert ids1.isdisjoint(ids2)

    def test_result_structure(self, populated_db):
        results = search_articles(populated_db, limit=1)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r["source"], dict)
        assert "name" in r["source"]
        assert "total" in r["quality_score"]
        assert "grade" in r["quality_score"]
        assert "depth" in r["quality_score"]
