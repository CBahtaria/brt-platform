#!/bin/bash
# Enforces Project A (Phase 0) / Project B boundary
set -euo pipefail
FAIL=0

check() {
    local pattern="$1"
    local file="$2"
    local label="$3"
    if grep -qr "$pattern" "$file" 2>/dev/null; then
        echo "❌ FAIL: $label — '$pattern' found in $file"
        FAIL=1
    else
        echo "✅ OK: $label"
    fi
}

# Checks for unguarded (top-level) hard imports only — try/except guarded imports are allowed
check_no_unguarded_import() {
    local pattern="$1"
    local file="$2"
    local label="$3"
    # Match the import line only when it is NOT preceded by a 'try:' block (i.e. indented)
    if grep -rP "^from $pattern|^import $pattern" "$file" 2>/dev/null | grep -qv "^#"; then
        echo "❌ FAIL: $label — unguarded '$pattern' import found in $file"
        FAIL=1
    else
        echo "✅ OK: $label"
    fi
}

echo "Checking Project A/B boundary..."
check_no_unguarded_import "brt_platform.analytics.clickhouse" "brt_platform/core/rag_engine.py" "No hard ClickHouse import in RAG"
check "from brt_platform.billing" "brt_platform/core/" "No billing in core"
check "import kafka" "brt_platform/core/" "No Kafka in core"
check "import airflow" "brt_platform/core/" "No Airflow in core"
check "import faust" "brt_platform/core/" "No Faust in core"
check "brt_platform.plugins.connectors.whatsapp" "brt_platform/core/alerting.py" "No plugin import in alerting"

if [ $FAIL -eq 1 ]; then
    echo ""
    echo "❌ Scope discipline FAILED. Fix the above before building."
    exit 1
else
    echo ""
    echo "✅ All scope checks passed."
fi
