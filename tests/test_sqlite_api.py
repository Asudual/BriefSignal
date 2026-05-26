"""
BriefSignal SQLite API 测试

- 使用 FastAPI TestClient（httpx 后端）
- 通过 monkeypatch 控制 BRIEFSIGNAL_DB_PATH / BRIEFSIGNAL_API_KEY 环境变量
- 不生成真实数据库文件，全部使用 tmp_path
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from briefsignal.storage.sqlite_store import import_articles_from_json

TEST_DATA = Path(__file__).resolve().parent / "test_data" / "sample_articles.json"
KNOWN_ID = "a1b2c3d4e5f60718"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app():
    from app.main import app as _app
    return _app


@pytest.fixture()
def client_no_db(app, monkeypatch):
    """未设置 BRIEFSIGNAL_DB_PATH"""
    monkeypatch.delenv("BRIEFSIGNAL_DB_PATH", raising=False)
    monkeypatch.delenv("BRIEFSIGNAL_API_KEY", raising=False)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def client(app, tmp_path, monkeypatch):
    """已设置 BRIEFSIGNAL_DB_PATH，已导入 7 条测试数据，无 API Key"""
    db = str(tmp_path / "api_test.db")
    import_articles_from_json(str(TEST_DATA), db)
    monkeypatch.setenv("BRIEFSIGNAL_DB_PATH", db)
    monkeypatch.delenv("BRIEFSIGNAL_API_KEY", raising=False)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def client_with_key(app, tmp_path, monkeypatch):
    """已设置 BRIEFSIGNAL_DB_PATH 和 BRIEFSIGNAL_API_KEY"""
    db = str(tmp_path / "api_key_test.db")
    import_articles_from_json(str(TEST_DATA), db)
    monkeypatch.setenv("BRIEFSIGNAL_DB_PATH", db)
    monkeypatch.setenv("BRIEFSIGNAL_API_KEY", "test-secret-key")
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# TestNoDbConfigured — 未设置 DB 路径
# ---------------------------------------------------------------------------


class TestNoDbConfigured:
    def test_search_returns_503(self, client_no_db):
        r = client_no_db.get("/sqlite/search")
        assert r.status_code == 503
        body = r.json()
        assert body["detail"]["error"]["code"] == "DB_NOT_CONFIGURED"

    def test_sources_returns_503(self, client_no_db):
        r = client_no_db.get("/sqlite/sources")
        assert r.status_code == 503
        assert r.json()["detail"]["error"]["code"] == "DB_NOT_CONFIGURED"

    def test_article_returns_503(self, client_no_db):
        r = client_no_db.get("/sqlite/articles/some_id")
        assert r.status_code == 503
        assert r.json()["detail"]["error"]["code"] == "DB_NOT_CONFIGURED"

    def test_db_file_missing_returns_503(self, app, monkeypatch):
        """BRIEFSIGNAL_DB_PATH 设置了但文件不存在，返回 503 DB_NOT_AVAILABLE"""
        monkeypatch.setenv("BRIEFSIGNAL_DB_PATH", "/nonexistent/path/briefsignal.db")
        monkeypatch.delenv("BRIEFSIGNAL_API_KEY", raising=False)
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/sqlite/search")
        assert r.status_code == 503
        assert r.json()["detail"]["error"]["code"] == "DB_NOT_AVAILABLE"


# ---------------------------------------------------------------------------
# TestSQLiteSearch — 正常检索
# ---------------------------------------------------------------------------


class TestSQLiteSearch:
    def test_returns_200(self, client):
        r = client.get("/sqlite/search")
        assert r.status_code == 200

    def test_response_structure(self, client):
        r = client.get("/sqlite/search")
        body = r.json()
        for key in ("backend", "query", "count", "limit", "offset", "items"):
            assert key in body
        assert body["backend"] == "sqlite"

    def test_returns_all_articles(self, client):
        r = client.get("/sqlite/search?limit=100")
        body = r.json()
        assert body["count"] == 7
        assert len(body["items"]) == 7

    def test_query_filter(self, client):
        r = client.get("/sqlite/search?query=MCP")
        body = r.json()
        assert body["count"] >= 1
        assert any("MCP" in item["title"] for item in body["items"])

    def test_source_filter(self, client):
        r = client.get("/sqlite/search?source=InfoQ")
        body = r.json()
        assert body["count"] == 1
        assert body["items"][0]["source"]["name"] == "InfoQ 中国"

    def test_min_score_filter(self, client):
        r = client.get("/sqlite/search?min_score=75&limit=100")
        body = r.json()
        for item in body["items"]:
            assert item["quality_score"]["grade"] == "A"

    def test_limit_takes_effect(self, client):
        r = client.get("/sqlite/search?limit=3")
        body = r.json()
        assert len(body["items"]) == 3
        assert body["limit"] == 3

    def test_offset_pagination_no_overlap(self, client):
        r1 = client.get("/sqlite/search?limit=3&offset=0")
        r2 = client.get("/sqlite/search?limit=3&offset=3")
        ids1 = {item["id"] for item in r1.json()["items"]}
        ids2 = {item["id"] for item in r2.json()["items"]}
        assert ids1.isdisjoint(ids2)

    def test_offset_reflected_in_response(self, client):
        r = client.get("/sqlite/search?limit=5&offset=2")
        assert r.json()["offset"] == 2

    def test_invalid_limit_fastapi_422(self, client):
        r = client.get("/sqlite/search?limit=0")
        assert r.status_code == 422

    def test_invalid_offset_fastapi_422(self, client):
        r = client.get("/sqlite/search?offset=-1")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# TestSQLiteSources
# ---------------------------------------------------------------------------


class TestSQLiteSources:
    def test_returns_200(self, client):
        r = client.get("/sqlite/sources")
        assert r.status_code == 200

    def test_response_structure(self, client):
        body = client.get("/sqlite/sources").json()
        assert body["backend"] == "sqlite"
        assert "sources" in body
        assert isinstance(body["sources"], list)

    def test_returns_all_sources(self, client):
        sources = client.get("/sqlite/sources").json()["sources"]
        expected = {"36氪", "BestBlogs", "InfoQ 中国", "Qwen Blog",
                    "iThome", "橘鸦AI早报", "雷锋网"}
        assert set(sources) == expected

    def test_sources_sorted(self, client):
        sources = client.get("/sqlite/sources").json()["sources"]
        assert sources == sorted(sources)


# ---------------------------------------------------------------------------
# TestSQLiteGetArticle
# ---------------------------------------------------------------------------


class TestSQLiteGetArticle:
    def test_existing_article_200(self, client):
        r = client.get(f"/sqlite/articles/{KNOWN_ID}")
        assert r.status_code == 200

    def test_existing_article_structure(self, client):
        body = client.get(f"/sqlite/articles/{KNOWN_ID}").json()
        assert body["backend"] == "sqlite"
        assert "item" in body
        item = body["item"]
        assert item["id"] == KNOWN_ID
        assert "quality_score" in item
        assert isinstance(item["source"], dict)

    def test_nonexistent_article_404(self, client):
        r = client.get("/sqlite/articles/definitely_not_exist_xyzabc")
        assert r.status_code == 404
        body = r.json()
        assert body["detail"]["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# TestApiKeyAuth
# ---------------------------------------------------------------------------


class TestApiKeyAuth:
    def test_no_key_configured_allows_request(self, client):
        """BRIEFSIGNAL_API_KEY 未设置时，任何请求均不被拦截"""
        r = client.get("/sqlite/sources")
        assert r.status_code == 200

    def test_key_configured_no_header_returns_401(self, client_with_key):
        r = client_with_key.get("/sqlite/sources")
        assert r.status_code == 401
        assert r.json()["detail"]["error"]["code"] == "INVALID_API_KEY"

    def test_key_configured_wrong_key_returns_401(self, client_with_key):
        r = client_with_key.get(
            "/sqlite/sources", headers={"X-API-Key": "wrong-key"}
        )
        assert r.status_code == 401

    def test_key_configured_correct_key_returns_200(self, client_with_key):
        r = client_with_key.get(
            "/sqlite/sources", headers={"X-API-Key": "test-secret-key"}
        )
        assert r.status_code == 200

    def test_key_required_on_search(self, client_with_key):
        r = client_with_key.get(
            "/sqlite/search", headers={"X-API-Key": "test-secret-key"}
        )
        assert r.status_code == 200

    def test_key_required_on_article(self, client_with_key):
        r = client_with_key.get(
            f"/sqlite/articles/{KNOWN_ID}", headers={"X-API-Key": "test-secret-key"}
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# TestExistingRoutesUnaffected — 旧路由不受影响
# ---------------------------------------------------------------------------


class TestExistingRoutesUnaffected:
    def test_health_still_works(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_sources_still_works(self, client):
        r = client.get("/sources")
        assert r.status_code == 200
        assert "sources" in r.json()

    def test_search_still_works(self, client):
        r = client.get("/search")
        assert r.status_code == 200
        assert "results" in r.json()
