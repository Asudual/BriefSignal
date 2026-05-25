#!/bin/bash
# BriefSignal Security Scan v0.3.0
# 执行安全扫描，检查仓库中是否含有敏感字段。
# 正常: exit 0 | 发现风险: exit 1
#
# 用法:
#   cd <project_root>
#   bash scripts/security_scan.sh

set -euo pipefail

errors=0
SCAN_DIR="${1:-.}"

scan_pattern() {
    local pattern="$1"
    local label="$2"
    local file_filter="${3:-}"
    
    local cmd="grep -rn '$pattern' '$SCAN_DIR' --include='*'"
    if [ -n "$file_filter" ]; then
        cmd="grep -rn '$pattern' '$SCAN_DIR' $file_filter"
    fi
    
    local matches
    matches=$(eval "$cmd" 2>/dev/null \
        | grep -v './.git/' \
        | grep -v './.gitignore' \
        | grep -v './skills/' \
        | grep -v 'Authorization: Bearer <YOUR_TOKEN>' \
        | grep -v 'qqbot:c2c:<YOUR_TARGET_ID>' \
        | grep -v 'scripts/security_scan.sh' \
        || true)
    
    if [ -n "$matches" ]; then
        echo "[FAIL] $label"
        echo "$matches" | while IFS= read -r line; do
            echo "       $(echo "$line" | cut -d: -f1,2)"
        done
        errors=$((errors + 1))
    fi
}

echo "=== BriefSignal Security Scan ==="
echo ""

# 硬编码知乎 Secret
scan_pattern 'EXAMPLE_SERVICE_SECRET' 'Hardcoded ZHIHU_ACCESS_SECRET'

# 硬编码 Bearer token（超过 32 位的不明字符串）
scan_pattern 'Bearer [A-Za-z0-9_\-]\{32,\}' 'Hardcoded Bearer token'

# 服务器绝对路径
scan_pattern '/root/\.openclaw/workspace' 'Server file path (/root/.openclaw/workspace)'

# 真实 QQ 推送目标 ID
scan_pattern 'EXAMPLE_DELIVERY_TARGET' 'QQ target ID'

# .env 是否被 git 跟踪
if git ls-files .env 2>/dev/null | grep -q '.env'; then
    echo "[FAIL] .env is tracked by git"
    errors=$((errors + 1))
fi

# 检查是否有 .env 文件（不应受版本控制）
if [ -f "$SCAN_DIR/.env" ]; then
    echo "[WARN] .env file exists locally (excluded by .gitignore)"
fi

# 检查是否有真实日志目录
if [ -d "$SCAN_DIR/news/logs" ] && git ls-files "$SCAN_DIR/news/logs" 2>/dev/null | grep -q .; then
    echo "[FAIL] news/logs/ is tracked by git"
    errors=$((errors + 1))
fi

# 检查是否有 raw 目录
if [ -d "$SCAN_DIR/news/raw" ] && git ls-files "$SCAN_DIR/news/raw" 2>/dev/null | grep -q .; then
    echo "[FAIL] news/raw/ is tracked by git"
    errors=$((errors + 1))
fi

echo ""
if [ "$errors" -gt 0 ]; then
    echo "[RESULT] ❌ $errors issue(s) found"
    exit 1
fi

echo "[RESULT] ✅ Clean — no sensitive content detected"
exit 0
