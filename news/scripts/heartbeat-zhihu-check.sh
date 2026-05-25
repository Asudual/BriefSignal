#!/bin/bash
# SignalFlow 突发新闻监控 — 心跳用
# 每30分钟检查一次知乎热榜+全球搜索，发现新AI话题对比事件库
# 用法: bash heartbeat-zhihu-check.sh

set -euo pipefail

export ZHIHU_ACCESS_SECRET="${ZHIHU_ACCESS_SECRET:?Please set ZHIHU_ACCESS_SECRET}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/../../skills" && pwd)"
TRACKER="$SCRIPT_DIR/../event_tracker.json"
STATE_FILE="$SCRIPT_DIR/../logs/heartbeat-state.json"

AI_KW=("AI" "大模型" "DeepSeek" "OpenAI" "ChatGPT" "GPT" "Gemini" "Claude" "Qwen" 
       "通义" "文心" "混元" "算力" "GPU" "NVIDIA" "英特尔" "AMD" "量子" 
       "机器人" "LLM" "Agent" "MCP" "token" "开源" "SpaceX" "特斯拉" 
       "自动驾驶" "模型" "芯片")

# 加载上次状态
LAST_HOT_TITLES=""
if [ -f "$STATE_FILE" ]; then
    LAST_HOT_TITLES=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print('\n'.join(d.get('last_hot_titles',[])))" 2>/dev/null || echo "")
fi

# 1. 获取热榜
HOT_JSON=$(python3 "${SKILLS_DIR}/zhihu-hot-list/scripts/hot-list.py" '{}' 2>/dev/null || echo '{"code":-1}')

# 2. 提取AI相关条目
NEW_AI_TITLES=$(echo "$HOT_JSON" | python3 -c "
import json,sys
d=json.load(sys.stdin)
items=d.get('items',[])
kw='''$AI_KW'''
for item in items:
    t=item.get('title','')
    for k in kw.split():
        if k in t:
            print(t)
            break
" 2>/dev/null)

# 3. 对比事件追踪库，找新事件
EXISTING_TITLES=$(python3 -c "
import json
try:
    events=json.load(open('$TRACKER')).get('events',{})
    for e in events.values():
        print(e.get('title',''))
except: pass
" 2>/dev/null)

# 4. 发现新的AI话题
NEW_FOUND=""
while IFS= read -r title; do
    [ -z "$title" ] && continue
    # 检查是否已在追踪库
    if ! echo "$EXISTING_TITLES" | grep -qF "$title" 2>/dev/null; then
        # 检查是否上次已经出现过
        if ! echo "$LAST_HOT_TITLES" | grep -qF "$title" 2>/dev/null; then
            NEW_FOUND="${NEW_FOUND}${title}\n"
        fi
    fi
done <<< "$NEW_AI_TITLES"

# 5. 保存当前状态
python3 -c "
import json,sys
titles=[t for t in '''$NEW_AI_TITLES'''.strip().split('\n') if t]
json.dump({'last_hot_titles':titles,'checked_at':'$(date -Iseconds)'},open('$STATE_FILE','w'))
" 2>/dev/null

# 6. 如果有新AI话题，输出
if [ -n "$NEW_FOUND" ]; then
    echo "🔔 知乎热榜新AI话题 ($(date '+%H:%M')):"
    echo -e "$NEW_FOUND" | while IFS= read -r t; do [ -n "$t" ] && echo "  • $t"; done
fi
