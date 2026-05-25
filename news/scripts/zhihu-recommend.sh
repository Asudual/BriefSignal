#!/bin/bash
# SignalFlow 知乎荐读 - 独立推送脚本
# crontab: 30 12 * * * <project_dir>/news/scripts/zhihu-recommend.sh

set -euo pipefail

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" 2>/dev/null || true
export PATH="$HOME/.nvm/versions/node/v22.22.2/bin:$PATH"

export ZHIHU_ACCESS_SECRET="${ZHIHU_ACCESS_SECRET:?Please set ZHIHU_ACCESS_SECRET}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$WORKSPACE/news/logs"
TODAY=$(date +%Y-%m-%d)

log() {
    local level="$1"; shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
}

mkdir -p "$LOGDIR"

log INFO "========== 知乎荐读 触发 =========="

QQ_TARGET="${DELIVERY_TARGET:?Please set DELIVERY_TARGET}"

TASK_MSG="请执行知乎文章推荐任务：

1. 使用 zhihu_search 搜索 4 组关键词（每组 5 条）：
   - AI Agent 架构 MCP 工具链
   - 大模型应用开发 智能体 自动化
   - AI coding 编程 效率 实践
   - 多模态 大模型 训练 部署

2. 对返回结果按四维评分筛选（深度35%/原创性25%/实操性25%/标题质量15%），≥75分入选

3. 最多推荐 6 篇，格式如下：

📚 SignalFlow 荐读 · ${TODAY}

🔥 #1 [标题]
[2-3句摘要]
评分: XX分 | 链接: [URL]

🔔 #2-#4 [同上格式]
📌 #5-#6 [同上格式]

4. 筛选时排除广告/营销/知识星球推广文
5. 把推荐结果直接输出为回复，我会推送到QQ"

log INFO "调用 openclaw agent 生成知乎荐读..."
AGENT_OUTPUT=$(openclaw agent \
    --agent main \
    --message "$TASK_MSG" \
    --timeout 300 \
    --deliver \
    --reply-channel qqbot \
    --reply-to "$QQ_TARGET" 2>&1) || true
AGENT_EXIT=${PIPESTATUS[0]:-$?}
echo "$AGENT_OUTPUT"

if [ "$AGENT_EXIT" -ne 0 ]; then
    log ERROR "❌ 知乎荐读 生成失败 (exit=$AGENT_EXIT)"
    exit $AGENT_EXIT
fi

log INFO "========== 知乎荐读 完成 =========="
