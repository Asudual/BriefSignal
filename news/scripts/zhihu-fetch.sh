#!/bin/bash
# BriefSignal 知乎数据开放平台数据抓取器
# 用法: ./zhihu-fetch.sh <type> [query]
# type: global | zhihu | hot

set -euo pipefail

export ZHIHU_ACCESS_SECRET="${ZHIHU_ACCESS_SECRET:?Please set ZHIHU_ACCESS_SECRET}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/../../skills" && pwd)"

case "${1:-hot}" in
  global|globalsearch)
    python3 "${SKILLS_DIR}/zhihu-global-search/scripts/global-search.py" \
      "{\"query\":\"${2:-AI 人工智能 大模型 最新进展 2026}\",\"count\":10,\"search_db\":\"realtime\"}"
    ;;
  zhihu|zhihusearch)
    python3 "${SKILLS_DIR}/zhihu-search/scripts/zhihu-search.py" \
      "{\"query\":\"${2:-AI 人工智能 大模型 最新进展}\",\"count\":10}"
    ;;
  hot|hotlist)
    python3 "${SKILLS_DIR}/zhihu-hot-list/scripts/hot-list.py" '{}'
    ;;
  *)
    echo "Usage: $0 {global|zhihu|hot} [query]"
    exit 1
    ;;
esac
