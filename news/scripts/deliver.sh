#!/bin/bash
# SignalFlow News - Deliver Module v2
# 记录投递状态，检查报告质量，失败时触发告警

set -euo pipefail

TODAY=$(date +%Y-%m-%d)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$WORKSPACE/logs"
TARGET="${DELIVERY_TARGET:?Please set DELIVERY_TARGET}"

REPORT_FILE="${1:-}"

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOGDIR/deliver_${TODAY}.log"
}

mkdir -p "$LOGDIR"

if [ -z "$REPORT_FILE" ]; then
    # 自动找今天的最新报告
    REPORT_FILE=$(ls -t "$WORKSPACE"/{早报,晚报}_${TODAY}.md 2>/dev/null | head -1)
fi

if [ -z "$REPORT_FILE" ] || [ ! -f "$REPORT_FILE" ]; then
    log "❌ 报告文件不存在: ${REPORT_FILE:-未找到今天($TODAY)的报告}"
    exit 1
fi

# 质量检查
BYTES=$(wc -c < "$REPORT_FILE")
CHARS=$(wc -m < "$REPORT_FILE")
FIRE_COUNT=$(grep -c '^**\d\.' "$REPORT_FILE" 2>/dev/null || echo 0)

log "📋 投递检查: $REPORT_FILE"
log "   大小: ${BYTES} bytes, ${CHARS} chars"
log "   🔥条: $(grep -c '^## 🔥' "$REPORT_FILE" || true)"

if [ "$BYTES" -lt 500 ]; then
    log "⚠️ 报告异常过短 (<500 bytes)，可能生成失败"
    exit 1
fi

log "✅ 投递状态记录完成（实际发送由 agentTurn 的 message 工具完成）"
log "   目标: $TARGET"
