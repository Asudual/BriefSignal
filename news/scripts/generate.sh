#!/bin/bash
# BriefSignal News - Cron Wrapper v3
# 由 crontab 调用，通过 openclaw agent 触发生成
# 用法: ./generate.sh daily

set -euo pipefail

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" 2>/dev/null || true
export PATH="$HOME/.nvm/versions/node/v22.22.2/bin:$PATH"

export ZHIHU_ACCESS_SECRET="${ZHIHU_ACCESS_SECRET:?Please set ZHIHU_ACCESS_SECRET}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$WORKSPACE/news/logs"
TODAY=$(date +%Y-%m-%d)
TYPE="${1:-daily}"

log() {
    local level="$1"; shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
}

mkdir -p "$LOGDIR"

if [ "$TYPE" = "daily" ]; then
    REPORT_TYPE="日报"
    SAVE_FILE="$WORKSPACE/news/日报_${TODAY}.md"
    PROMPT_FILE="$WORKSPACE/news/GENERATE_PROMPT.md"
    TASK_MSG="请按照 GENERATE_PROMPT.md 的完整流程，生成今天（${TODAY}）的 BriefSignal AI日报。日报合并了原来的早报和晚报，每天只推一次，内容精选浓缩。严格按照模板执行全部9个步骤。把完整报告保存到 ${SAVE_FILE}，只输出最终摘要到回复。输出格式：
【日报摘要】
条目数: X🔥/Y🔔/Z📌
关键词: ...
来源: ...
⚠️: ..."
else
    log ERROR "未知类型: $TYPE (应为 daily)"
    exit 1
fi

log INFO "========== BriefSignal ${REPORT_TYPE} 触发 =========="

if ! command -v openclaw &>/dev/null; then
    log ERROR "openclaw CLI 不可用"
    exit 1
fi

QQ_TARGET="${DELIVERY_TARGET:?Please set DELIVERY_TARGET}"

log INFO "调用 openclaw agent 生成 ${REPORT_TYPE}..."
# 确保不传thinking参数——让模型用默认值，避免v4-pro不支持thinking的报错
AGENT_OUTPUT=$(openclaw agent \
    --agent main \
    --message "$TASK_MSG" \
    --timeout 600 \
    --deliver \
    --reply-channel qqbot \
    --reply-to "$QQ_TARGET" 2>&1) || true
AGENT_EXIT=${PIPESTATUS[0]:-$?}
echo "$AGENT_OUTPUT"

if [ "$AGENT_EXIT" -ne 0 ]; then
    log ERROR "❌ ${REPORT_TYPE} 生成失败 (exit=$AGENT_EXIT)"
    
    YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -j -v-1d +%Y-%m-%d 2>/dev/null)
    if [ -f "$LOGDIR/cron_${YESTERDAY}.log" ] && grep -q "❌" "$LOGDIR/cron_${YESTERDAY}.log"; then
        log ALERT "⚠️ 连续2天失败，触发告警"
        openclaw agent \
            --agent main \
            --message "⚠️ BriefSignal 执行异常：日报连续2天生成失败（${YESTERDAY} 和 ${TODAY}），请检查日志" \
            --thinking off \
            --timeout 60 \
            --deliver \
            --reply-channel qqbot \
            --reply-to "$QQ_TARGET" 2>/dev/null || true
    fi
    exit $AGENT_EXIT
fi

if [ -f "$SAVE_FILE" ]; then
    log INFO "✅ ${REPORT_TYPE} 已保存到 ${SAVE_FILE} ($(wc -c < "$SAVE_FILE") bytes)"
else
    log WARN "⚠️ ${REPORT_TYPE} 文件 ${SAVE_FILE} 不存在"
fi

log INFO "========== BriefSignal ${REPORT_TYPE} 完成 =========="
