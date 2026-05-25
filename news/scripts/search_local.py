#!/usr/bin/env python3
"""
SignalFlow 本地检索脚本 — v0.2 预研版

从本地 JSON 文件（符合 data_schema.md 的 Article 格式）中
按关键词、信源、最低评分过滤，输出匹配结果。

用途：
- 快速检索历史采集文章的标题/摘要/标签
- 验证 data_schema 和采样数据的结构正确性
- 作为未来 AI Search / RAG 的前置原型

依赖：仅 Python 3 标准库
"""

import json
import argparse
import sys
from pathlib import Path


def load_articles(path: str) -> list:
    """从 JSON 文件加载文章列表"""
    path = Path(path)
    if not path.exists():
        print(f"❌ 文件不存在: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, "r", encoding="utf-8") as f:
            articles = json.load(f)
        if not isinstance(articles, list):
            print("❌ JSON 须为数组格式", file=sys.stderr)
            sys.exit(1)
        return articles
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)


def get_total(scores: dict) -> float:
    """从 quality_score 对象提取 total"""
    if not isinstance(scores, dict):
        return 0.0
    return float(scores.get("total", 0))


def get_grade(scores: dict) -> str:
    """从 quality_score 对象提取 grade"""
    if not isinstance(scores, dict):
        return "?"
    return str(scores.get("grade", "?"))


def match_keywords(text: str, keywords: list[str]) -> bool:
    """关键词匹配（大小写不敏感）"""
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


def search(
    articles: list,
    query: str | None = None,
    source: str | None = None,
    min_score: float = 0.0,
) -> list[dict]:
    """
    搜索主函数。

    参数：
        query:     检索关键词（匹配 title + summary + tags）
        source:    按信源名称过滤
        min_score: 最低 quality_score.total 阈值
    """
    keywords = query.strip().split() if query else []

    results = []
    for art in articles:
        scores = art.get("quality_score", {})
        total = get_total(scores)

        # 过滤：最低评分
        if total < min_score:
            continue

        # 过滤：信源
        if source:
            src_name = art.get("source", {}).get("name", "")
            if source.lower() not in src_name.lower():
                continue

        # 过滤：关键词
        if keywords:
            title = art.get("title", "")
            summary = art.get("summary", "")
            tags = " ".join(art.get("tags", []))
            haystack = f"{title} {summary} {tags}"
            if not match_keywords(haystack, keywords):
                continue

        results.append(art)

    # 按 total 评分降序排列
    results.sort(key=lambda x: get_total(x.get("quality_score", {})), reverse=True)
    return results


def format_results(results: list) -> str:
    """格式化输出结果"""
    if not results:
        return "📭 无匹配结果"

    lines = [f"📊 匹配到 {len(results)} 条结果：\n"]
    for i, art in enumerate(results, 1):
        scores = art.get("quality_score", {})
        total = get_total(scores)
        grade = get_grade(scores)
        source_name = art.get("source", {}).get("name", "?")
        title = art.get("title", "?")
        summary = art.get("summary", "")
        summary_short = summary[:120] + "..." if len(summary) > 120 else summary

        lines.append(f"{'─' * 50}")
        lines.append(f"#{i}  [{grade}] {title}")
        lines.append(f"    total: {total:.1f}  |  来源: {source_name}")
        lines.append(f"    摘要: {summary_short}")

    lines.append(f"\n{'═' * 50}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="SignalFlow 本地检索脚本 — 四维评分体系",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s --query MCP\n"
            "  %(prog)s --query Agent --source \"InfoQ 中国\"\n"
            "  %(prog)s --query 融资 --min-score 60\n"
            "  %(prog)s --source 雷锋网 --min-score 60\n"
            "  %(prog)s --query 推理 量化 --min-score 75\n"
        ),
    )
    parser.add_argument(
        "--data",
        default="examples/sample_articles.json",
        help="JSON 数据文件路径（默认: examples/sample_articles.json）",
    )
    parser.add_argument(
        "--query", "-q",
        default=None,
        help="检索关键词（空格分隔，匹配 title + summary + tags）",
    )
    parser.add_argument(
        "--source", "-s",
        default=None,
        help="按信源名称过滤（部分匹配）",
    )
    parser.add_argument(
        "--min-score", "-m",
        type=float,
        default=0.0,
        help="最低 quality_score.total 阈值（0-100，A级≥75, B级≥60）",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="列出所有可用信源",
    )

    args = parser.parse_args()

    articles = load_articles(args.data)

    # --list-sources 模式
    if args.list_sources:
        sources = set()
        for art in articles:
            name = art.get("source", {}).get("name", "未知")
            sources.add(name)
        print("📡 可用信源：")
        for s in sorted(sources):
            print(f"  - {s}")
        return

    # 没有任何过滤参数时，显示帮助
    if not args.query and not args.source and args.min_score == 0.0:
        parser.print_help()
        print("\n💡 提示：请指定 --query、--source 或 --min-score 至少一个参数")
        sys.exit(0)

    results = search(
        articles,
        query=args.query,
        source=args.source,
        min_score=args.min_score,
    )

    print(format_results(results))


if __name__ == "__main__":
    main()
