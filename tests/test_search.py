"""
BriefSignal 本地检索功能测试

测试数据使用脱敏 mock 数据（tests/test_data/sample_articles.json）。
不连接任何外部服务，不读取真实数据。
"""

import json
import sys
from pathlib import Path

# 确保可以 import search_local
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "news" / "scripts"))
import search_local

TEST_DATA = Path(__file__).resolve().parent / "test_data" / "sample_articles.json"


def setup_module():
    """预检查测试数据存在"""
    assert TEST_DATA.exists(), f"测试数据不存在: {TEST_DATA}"


def load_test_articles():
    return search_local.load_articles(str(TEST_DATA))


class TestSearchByKeyword:
    def test_search_mcp(self):
        articles = load_test_articles()
        results = search_local.search(articles, query="MCP")
        assert len(results) == 1
        assert "MCP" in results[0]["title"]

    def test_search_qwen(self):
        articles = load_test_articles()
        results = search_local.search(articles, query="Qwen3")
        assert len(results) == 1
        assert results[0]["quality_score"]["grade"] == "A"

    def test_search_without_match(self):
        articles = load_test_articles()
        results = search_local.search(articles, query="nosuchtermlikely")
        assert len(results) == 0


class TestSearchBySource:
    def test_search_source_infoq(self):
        articles = load_test_articles()
        results = search_local.search(articles, source="InfoQ 中国")
        assert len(results) == 1
        assert results[0]["source"]["name"] == "InfoQ 中国"

    def test_search_source_ithome(self):
        articles = load_test_articles()
        results = search_local.search(articles, source="iThome")
        assert len(results) == 1
        assert results[0]["source"]["name"] == "iThome"


class TestSearchByMinScore:
    def test_search_min_score_75(self):
        """min_score 75 = 只看 A 级"""
        articles = load_test_articles()
        results = search_local.search(articles, min_score=75)
        # 样本数据中 A 级有 3 条：MCP(82.3), KV Cache(75.3), Qwen3(82.8)
        assert len(results) == 3
        for r in results:
            assert r["quality_score"]["grade"] == "A"

    def test_search_min_score_60(self):
        """min_score 60 = A 级 + B 级"""
        articles = load_test_articles()
        results = search_local.search(articles, min_score=60)
        assert len(results) >= 5  # 3 A + 至少 2 B

    def test_search_min_score_0(self):
        """min_score 0 = 全部"""
        articles = load_test_articles()
        results = search_local.search(articles, min_score=0)
        assert len(results) == len(articles)


class TestSearchAllWithoutFilters:
    def test_search_no_filters_returns_all(self):
        articles = load_test_articles()
        results = search_local.search(articles)
        assert len(results) == len(articles)

    def test_search_no_filters_sorted_by_score(self):
        articles = load_test_articles()
        results = search_local.search(articles)
        scores = [search_local.get_total(r.get("quality_score", {})) for r in results]
        assert scores == sorted(scores, reverse=True), "结果应按 total 降序排列"


class TestSearchWithLimit:
    def test_search_limit_1(self):
        articles = load_test_articles()
        results = search_local.search(articles, min_score=0, limit=1)
        assert len(results) == 1

    def test_search_limit_exceeds_data(self):
        articles = load_test_articles()
        results = search_local.search(articles, limit=999)
        assert len(results) == len(articles)


class TestListSources:
    def test_list_sources(self):
        articles = load_test_articles()
        sources = search_local.list_sources(articles)
        expected = {"36氪", "BestBlogs", "InfoQ 中国", "Qwen Blog", "iThome", "橘鸦AI早报", "雷锋网"}
        assert set(sources) == expected
        assert sources == sorted(sources)


class TestGetTotal:
    def test_get_total_valid(self):
        assert search_local.get_total({"total": 82.3, "grade": "A"}) == 82.3

    def test_get_total_invalid(self):
        assert search_local.get_total(None) == 0.0
        assert search_local.get_total({}) == 0.0
        assert search_local.get_total("not_a_dict") == 0.0


class TestGetGrade:
    def test_get_grade_valid(self):
        assert search_local.get_grade({"total": 82.3, "grade": "A"}) == "A"

    def test_get_grade_invalid(self):
        assert search_local.get_grade(None) == "?"
        assert search_local.get_grade({}) == "?"
