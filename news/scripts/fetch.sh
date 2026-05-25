#!/bin/bash
# SignalFlow News - Fetch Module v2
# 根据 sources.json 配置抓取所有源，输出到 tmp/ 目录
# 支持 RSS 和 webpage 两种类型

set -euo pipefail

TODAY=$(date +%Y-%m-%d)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NEWS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMPDIR="$NEWS_DIR/tmp"
LOGDIR="$NEWS_DIR/logs"
SOURCES_FILE="$NEWS_DIR/sources.json"

mkdir -p "$TMPDIR" "$LOGDIR"

# 辅助函数：从 JSON 提取字段（简单 grep，避免 jq 依赖）
extract_json_field() {
    local file="$1"
    local field="$2"
    grep "\"$field\"" "$file" | head -1 | sed 's/.*": "*//;s/".*//' | xargs
}

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOGDIR/fetch_${TODAY}.log"
}

log "========== SignalFlow Fetch v2 开始 =========="

fetch_rss() {
    local name="$1"
    local url="$2"
    local output="$TMPDIR/${TODAY}_$(echo "$name" | sed 's/[ /]/_/g').xml"
    
    log "  📡 $name ..."
    if content=$(curl -s -L --max-time 20 -H "User-Agent: SignalFlowNewsBot/2.0" "$url" 2>/dev/null); then
        if [ -n "$content" ] && [ "$(echo "$content" | wc -c)" -gt 100 ]; then
            echo "$content" > "$output"
            local bytes=$(wc -c < "$output")
            log "    ✅ $(echo "$content" | grep -o '<title>[^<]*</title>' | head -5 | sed 's/<[^>]*>//g' | wc -l) 条标题, ${bytes} bytes"
            return 0
        else
            log "    ⚠️ 内容过短 ($(echo "$content" | wc -c) bytes)"
            return 1
        fi
    else
        log "    ❌ curl 失败"
        return 1
    fi
}

fetch_webpage() {
    local name="$1"
    local url="$2"
    local output="$TMPDIR/${TODAY}_$(echo "$name" | sed 's/[ /]/_/g').html"
    
    log "  🌐 $name ..."
    if content=$(curl -s -L --max-time 20 -H "User-Agent: Mozilla/5.0" "$url" 2>/dev/null); then
        if [ -n "$content" ] && [ "$(echo "$content" | wc -c)" -gt 200 ]; then
            echo "$content" > "$output"
            log "    ✅ $(wc -c < "$output") bytes"
            return 0
        else
            log "    ⚠️ 内容过短"
            return 1
        fi
    else
        log "    ❌ curl 失败"
        return 1
    fi
}

# 主抓取循环
SUCCESS=0
FAIL=0

while IFS= read -r line; do
    # 简单解析 JSON 行，提取 name/url/type
    name=$(echo "$line" | grep -o '"name": *"[^"]*"' | head -1 | sed 's/.*": *"//;s/"//')
    url=$(echo "$line" | grep -o '"url": *"[^"]*"' | head -1 | sed 's/.*": *"//;s/"//')
    type=$(echo "$line" | grep -o '"type": *"[^"]*"' | head -1 | sed 's/.*": *"//;s/"//')
    
    if [ -z "$name" ] || [ -z "$url" ]; then
        continue
    fi
    
    # 默认 type=rss
    type="${type:-rss}"
    
    case "$type" in
        rss|html)
            if fetch_rss "$name" "$url"; then
                SUCCESS=$((SUCCESS + 1))
            else
                FAIL=$((FAIL + 1))
            fi
            ;;
        webpage)
            if fetch_webpage "$name" "$url"; then
                SUCCESS=$((SUCCESS + 1))
            else
                FAIL=$((FAIL + 1))
            fi
            ;;
        *)
            log "  ⏭️ 未知类型 $type: $name"
            ;;
    esac
done < <(grep -E '"(name|url|type)"' "$SOURCES_FILE" | paste - - -)

log "========== 抓取完成: $SUCCESS 成功 / $FAIL 失败 =========="
echo "$SUCCESS $FAIL" > "$TMPDIR/.fetch_status"
