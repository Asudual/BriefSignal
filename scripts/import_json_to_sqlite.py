#!/usr/bin/env python3
"""
从 JSON 文件导入文章到 SQLite 数据库。

用法：
    python scripts/import_json_to_sqlite.py
    python scripts/import_json_to_sqlite.py --json examples/sample_articles.json --db news/articles.db
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from briefsignal.storage.sqlite_store import import_articles_from_json

DEFAULT_JSON = "examples/sample_articles.json"
DEFAULT_DB = "news/articles.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="导入 JSON 文章到 SQLite 数据库")
    parser.add_argument(
        "--json",
        default=DEFAULT_JSON,
        help=f"JSON 数据文件路径（默认: {DEFAULT_JSON}）",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=f"SQLite 数据库路径（默认: {DEFAULT_DB}）",
    )
    args = parser.parse_args()

    try:
        count = import_articles_from_json(args.json, args.db)
        print(f"✅ 导入完成：插入 {count} 条，数据库: {args.db}")
    except FileNotFoundError as e:
        print(f"❌ 文件不存在：{e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ 数据格式错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
