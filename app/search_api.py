"""
BriefSignal Search API — FastAPI 路由

封装 search_local 的检索函数，返回标准化 JSON 响应。
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException

# 确保可 import search_local
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "news" / "scripts"))
import search_local

# 默认数据路径（相对于项目根）
DEFAULT_DATA = str(Path(__file__).resolve().parents[1] / "examples" / "sample_articles.json")

router = APIRouter()

# 在模块加载时缓存文章数据
_articles = None


def get_articles():
    global _articles
    if _articles is None:
        _articles = search_local.load_articles(DEFAULT_DATA)
    return _articles


@router.get("/health")
def health():
    """服务健康检查"""
    return {"status": "ok", "version": "0.3.0"}


@router.get("/sources")
def sources():
    """列出数据中所有可用信源"""
    articles = get_articles()
    return {"sources": search_local.list_sources(articles)}


@router.get("/search")
def search(
    query: str | None = Query(None, description="检索关键词（空格分隔多词）"),
    source: str | None = Query(None, description="按信源名称过滤"),
    min_score: float = Query(0.0, ge=0, le=100, description="最低 quality_score.total 阈值（0-100）"),
    limit: int = Query(20, ge=1, le=100, description="最多返回条数"),
):
    """
    检索文章。

    返回值符合 docs/data_schema.md 中的 Article schema。
    quality_score 包含 depth/originality/practicality/title_quality/total/grade。
    """
    try:
        articles = get_articles()

        if not query and not source and min_score == 0.0:
            # 无过滤条件时返回所有（按评分降序）
            pass

        results = search_local.search(
            articles,
            query=query,
            source=source,
            min_score=min_score,
            limit=limit,
        )

        return {
            "query": query,
            "filters": {
                "source": source,
                "min_score": min_score,
                "limit": limit,
            },
            "total": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
