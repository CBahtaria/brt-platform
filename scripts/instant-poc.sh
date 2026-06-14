#!/bin/bash
set -euo pipefail

TTL_SECONDS=14400
PROSPECT_NAME=""
DOCS_DIR=""

usage() { echo "Usage: $0 --prospect 'Company Name' [--docs ./docs/] [--ttl 14400]"; exit 1; }

while [[ $# -gt 0 ]]; do
    case $1 in
        --prospect) PROSPECT_NAME="$2"; shift 2 ;;
        --docs)     DOCS_DIR="$2"; shift 2 ;;
        --ttl)      TTL_SECONDS="$2"; shift 2 ;;
        -h|--help)  usage ;;
        *) echo "Unknown: $1"; usage ;;
    esac
done

[[ -z "$PROSPECT_NAME" ]] && { echo "Error: --prospect required"; usage; }

# Self-Heal Loop 2: Input sanitization
SLUG=$(echo "$PROSPECT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | tr -s '-')
SLUG="${SLUG:0:50}"
[[ -z "$SLUG" ]] && { echo "Error: Invalid prospect name '$PROSPECT_NAME'"; exit 1; }

TIMESTAMP=$(date +%s)
TENANT_ID="poc-${SLUG}-${TIMESTAMP}"
PROJECT_DIR="deployments/${TENANT_ID}"
TUNNEL_LOG="/tmp/cloudflared-${TENANT_ID}.log"
RUNTIME=$(which podman 2>/dev/null || which docker 2>/dev/null || echo "docker")
COMPOSE="${RUNTIME}-compose"

echo "🚀 BRT Platform POC"
echo "   Prospect : $PROSPECT_NAME"
echo "   Tenant ID: $TENANT_ID"
echo "   Dir      : $PROJECT_DIR"
echo "   TTL      : $((TTL_SECONDS / 3600))h"

mkdir -p "$PROJECT_DIR/custom-plugins"
cp deployments/client-template/docker-compose.yml "$PROJECT_DIR/"
cp deployments/client-template/.env.template "$PROJECT_DIR/.env"
sed -i "s/BRT_TENANT_ID=.*/BRT_TENANT_ID=${TENANT_ID}/" "$PROJECT_DIR/.env"

$COMPOSE -f "$PROJECT_DIR/docker-compose.yml" -p "${TENANT_ID}" up -d
echo "⏳ Waiting for API..."
for i in $(seq 1 30); do
    curl -sf "http://localhost:8000/health" > /dev/null 2>&1 && break
    sleep 2
done

API_PORT=$(${COMPOSE} -p "${TENANT_ID}" port brt-api 8000 2>/dev/null | cut -d: -f2 || echo "8000")
API_URL="http://localhost:${API_PORT}"
echo "   API live: $API_URL"

if command -v cloudflared &>/dev/null; then
    echo "🌐 Starting tunnel..."
    cloudflared tunnel --url "$API_URL" > "$TUNNEL_LOG" 2>&1 &
    TUNNEL_PID=$!

    TUNNEL_URL=""
    for i in $(seq 1 30); do
        TUNNEL_URL=$(grep -oE 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -1 || true)
        [[ -n "$TUNNEL_URL" ]] && break
        sleep 1
    done

    if [[ -z "$TUNNEL_URL" ]]; then
        echo "⚠️  Tunnel URL not found. Log:"
        cat "$TUNNEL_LOG"
        kill "$TUNNEL_PID" 2>/dev/null || true
        TUNNEL_URL="$API_URL (no tunnel)"
    fi
else
    echo "⚠️  cloudflared not installed. Using local URL only."
    TUNNEL_PID=""
    TUNNEL_URL="$API_URL"
fi

if [[ -n "$DOCS_DIR" && -d "$DOCS_DIR" ]]; then
    echo "📄 Ingesting documents..."
    for f in "$DOCS_DIR"/*; do
        [[ -f "$f" ]] || continue
        echo "   → $(basename "$f")"
        curl -sf -X POST "${API_URL}/api/v1/ingest" \
             -H "X-Tenant-ID: ${TENANT_ID}" \
             -F "file=@${f}" > /dev/null || echo "   [WARN] Upload failed: $f"
    done
fi

# Self-destruct timer
(
    sleep "$TTL_SECONDS"
    echo "💣 Self-destruct: $TENANT_ID"
    ${COMPOSE} -p "${TENANT_ID}" down -v 2>/dev/null || true
    [[ -n "$TUNNEL_PID" ]] && kill "$TUNNEL_PID" 2>/dev/null || true
    rm -rf "$PROJECT_DIR" "$TUNNEL_LOG" 2>/dev/null || true
    echo "   Cleaned up."
) &

echo ""
echo "✅ POC LIVE"
echo "   Share: $TUNNEL_URL"
echo "   Query: curl -X POST ${API_URL}/api/v1/query -H 'X-Tenant-ID: ${TENANT_ID}' -H 'Content-Type: application/json' -d '{\"query\":\"test\"}'"
echo "   Logs : ${COMPOSE} -p ${TENANT_ID} logs -f brt-api"
