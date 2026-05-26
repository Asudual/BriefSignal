"""
BriefSignal SQLite Search API — 实验性 FastAPI 路由

路由前缀：/sqlite
数据库路径：BRIEFSIGNAL_DB_PATH 环境变量（未设置时返回 503）
可选认证：BRIEFSIGNAL_API_KEY 环境变量（未设置时本地开发不启用）

本模块为实验性接口，不替换现有 /search 和 /sources 行为。
"""

import hmac
import os
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from briefsignal.storage.sqlite_store import (
    get_article_by_id,
    list_sources,
    search_articles,
)

router = APIRouter(prefix="/sqlite", tags=["SQLite (experimental)"])


# ---------------------------------------------------------------------------
# Auth & config helpers
# ---------------------------------------------------------------------------


def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    """
    可选 API Key 认证。

    BRIEFSIGNAL_API_KEY 未设置时跳过（本地开发模式）。
    设置后，请求必须携带正确的 X-API-Key 标头。
    """
    required = os.environ.get("BRIEFSIGNAL_API_KEY")
    if not required:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, required):
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "INVALID_API_KEY",
                    "message": "X-API-Key 无效或缺失",
                }
            },
        )


def _get_db_path() -> str:
    """读取数据库路径环境变量，未设置或文件不存在时抛出结构化 503。"""
    db_path = os.environ.get("BRIEFSIGNAL_DB_PATH")
    if not db_path:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "DB_NOT_CONFIGURED",
                    "message": "BRIEFSIGNAL_DB_PATH 环境变量未设置，SQLite 后端不可用",
                }
            },
        )
    if not Path(db_path).exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "DB_NOT_AVAILABLE",
                    "message": "数据库文件不存在或不可读，请检查 BRIEFSIGNAL_DB_PATH 配置",
                }
            },
        )
    return db_path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/sources")
def sqlite_sources(_: None = Depends(verify_api_key)):
    """【experimental】列出 SQLite 数据库中所有已启用信源"""
    db = _get_db_path()
    try:
        sources = list_sources(db)
        return {"backend": "sqlite", "sources": sources}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )


@router.get("/search")
def sqlite_search(
    query: str | None = Query(None, description="检索关键词（空格分隔多词）"),
    source: str | None = Query(None, description="按信源名称过滤（部分匹配）"),
    min_score: float | None = Query(None, ge=0, le=100, description="最低 quality_score.total 阈值"),
    limit: int = Query(10, ge=1, le=100, description="最多返回条数（1-100）"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    _: None = Depends(verify_api_key),
):
    """【experimental】检索 SQLite 数据库文章，支持关键词、信源、评分、分页"""
    db = _get_db_path()
    try:
        items = search_articles(
            db,
            query=query,
            source=source,
            min_score=min_score,
            limit=limit,
            offset=offset,
        )
        return {
            "backend": "sqlite",
            "query": query,
            "count": len(items),
            "limit": limit,
            "offset": offset,
            "items": items,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_PARAMS", "message": str(e)}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )


@router.get("/articles/{article_id}")
def sqlite_get_article(
    article_id: str,
    _: None = Depends(verify_api_key),
):
    """【experimental】按 ID 获取单篇文章"""
    db = _get_db_path()
    try:
        article = get_article_by_id(db, article_id)
        if article is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"文章 {article_id!r} 不存在",
                    }
                },
            )
        return {"backend": "sqlite", "item": article}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": str(e)}},
        )
