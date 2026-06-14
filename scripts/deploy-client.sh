#!/bin/bash
set -euo pipefail

CLIENT_USER="${CLIENT_USER:-ubuntu}"
CLIENT_HOST="${CLIENT_HOST:-}"
CLIENT_DIR="${CLIENT_DIR:-/opt/brt-platform}"
TENANT_ID="${TENANT_ID:-}"

[[ -z "$CLIENT_HOST" ]] && { echo "Error: CLIENT_HOST not set"; exit 1; }
[[ -z "$TENANT_ID" ]]   && { echo "Error: TENANT_ID not set"; exit 1; }

echo "🚀 Deploying BRT Platform"
echo "   Host     : ${CLIENT_USER}@${CLIENT_HOST}"
echo "   Directory: $CLIENT_DIR"
echo "   Tenant   : $TENANT_ID"

# Pre-flight SSH check (StrictHostKeyChecking=accept-new: adds new keys, rejects changed)
echo "⏳ Verifying SSH connection..."
if ! ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
        "${CLIENT_USER}@${CLIENT_HOST}" "echo 'SSH OK'" 2>/dev/null; then
    echo "❌ Cannot connect to ${CLIENT_HOST}. Check:"
    echo "   1. Host is reachable: ping ${CLIENT_HOST}"
    echo "   2. SSH key is set up: ssh ${CLIENT_USER}@${CLIENT_HOST}"
    exit 1
fi
echo "✅ SSH connection verified."

# Template env file
if [[ ! -f ".env" ]]; then
    envsubst < deployments/client-template/.env.template > .env.client
else
    cp .env .env.client
fi
sed -i "s/BRT_TENANT_ID=.*/BRT_TENANT_ID=${TENANT_ID}/" .env.client

# Sync files
ssh "${CLIENT_USER}@${CLIENT_HOST}" "mkdir -p ${CLIENT_DIR}"
rsync -avz --delete \
    --exclude ".git" --exclude "__pycache__" --exclude ".env" \
    --exclude "deployments/" --exclude "tests/" \
    . "${CLIENT_USER}@${CLIENT_HOST}:${CLIENT_DIR}/"
rsync -avz .env.client "${CLIENT_USER}@${CLIENT_HOST}:${CLIENT_DIR}/.env"

# Deploy
RUNTIME=$(which podman 2>/dev/null || echo "docker")
ssh "${CLIENT_USER}@${CLIENT_HOST}" "
    cd ${CLIENT_DIR}
    ${RUNTIME}-compose pull
    ${RUNTIME}-compose down || true
    ${RUNTIME}-compose up -d
    echo 'Waiting for health...'
    for i in \$(seq 1 30); do
        curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo 'Healthy!' && exit 0
        sleep 2
    done
    echo 'WARN: Health check timed out'
"

echo ""
echo "✅ Deployed to ${CLIENT_HOST}"
echo "   Test: curl http://${CLIENT_HOST}:8000/health"
