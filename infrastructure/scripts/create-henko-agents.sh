#!/bin/bash
# ==============================================================================
# Henko Sys x01 — Create Initial Agent Team via Paperclip API
# ==============================================================================
# Creates the 3 core Henko agents (INTEL, FORGE, ALPHA) in Paperclip,
# all using hermes_local adapter → local Ollama models.
#
# Prerequisites:
# - Paperclip running on http://localhost:3100
# - Hermes Agent installed in the same WSL2 user as Paperclip
# - Ollama running with qwen3:8b and qwen3:32b models
#
# Run from Windows (Git Bash):
#   bash infrastructure/scripts/create-henko-agents.sh
# ==============================================================================
set -e

PAPERCLIP_URL="${PAPERCLIP_URL:-http://localhost:3100}"
COMPANY_NAME="${COMPANY_NAME:-Henko Sys x01}"

# Use curl.exe on Windows Git Bash (standard curl has routing issues with WSL2 mirrored networking)
if [ -n "$WINDIR" ]; then
  CURL=curl.exe
else
  CURL=curl
fi

echo "🌟 Henko Sys x01 — Create Agent Team"
echo ""

# 1. Create or find company
echo "📋 Creating company: $COMPANY_NAME"
COMPANY_RESPONSE=$($CURL -s -X POST -H "Content-Type: application/json" \
  -d "{\"name\":\"$COMPANY_NAME\"}" \
  "$PAPERCLIP_URL/api/companies")
COMPANY_ID=$(echo "$COMPANY_RESPONSE" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$COMPANY_ID" ]; then
  echo "❌ Failed to create company. Response: $COMPANY_RESPONSE"
  exit 1
fi
echo "  ✓ Company ID: $COMPANY_ID"

# 2. Create INTEL Researcher
echo ""
echo "🔭 Creating INTEL Researcher (qwen3:8b, researcher)..."
$CURL -s -X POST -H "Content-Type: application/json" -d '{
  "name": "INTEL Researcher",
  "role": "researcher",
  "title": "Geopolitical & Tech Intelligence Analyst",
  "icon": "telescope",
  "capabilities": "Monitors geopolitical events, scans AI/ML papers, analyzes GitHub trends, generates daily briefings in Spanish",
  "adapterType": "hermes_local",
  "adapterConfig": {
    "model": "qwen3:8b",
    "provider": "custom",
    "baseUrl": "http://localhost:11434/v1",
    "maxIterations": 50,
    "timeoutSec": 300,
    "persistSession": true,
    "enabledToolsets": ["terminal", "file", "web"]
  }
}' "$PAPERCLIP_URL/api/companies/$COMPANY_ID/agents" | python3 -c "import json,sys;a=json.load(sys.stdin);print(f'  ✓ {a[\"name\"]} ({a[\"urlKey\"]}) — {a[\"id\"]}')"

# 3. Create FORGE Engineer
#    NOTE: Uses gemma4:e4b (~7GB Q4) — fits 8GB VRAM completely. qwen3:32b
#    was tested but times out on this hardware (60% CPU offload kills latency).
#    See CLAUDE.md "Hardware-Aware Model Selection" for details.
echo ""
echo "💻 Creating FORGE Engineer (gemma4:e4b, engineer)..."
$CURL -s -X POST -H "Content-Type: application/json" -d '{
  "name": "FORGE Engineer",
  "role": "engineer",
  "title": "BMAD Software Developer",
  "icon": "code",
  "capabilities": "Implements features using BMAD methodology (Analysis/Planning/Solutioning/Implementation), builds apps with Next.js, writes tests, deploys via Dokploy",
  "adapterType": "hermes_local",
  "adapterConfig": {
    "model": "gemma4:e4b",
    "provider": "custom",
    "baseUrl": "http://localhost:11434/v1",
    "maxIterations": 50,
    "timeoutSec": 900,
    "persistSession": true,
    "enabledToolsets": ["terminal", "file", "web", "code_execution"]
  }
}' "$PAPERCLIP_URL/api/companies/$COMPANY_ID/agents" | python3 -c "import json,sys;a=json.load(sys.stdin);print(f'  ✓ {a[\"name\"]} ({a[\"urlKey\"]}) — {a[\"id\"]}')"

# 4. Create ALPHA Trader
echo ""
echo "🎯 Creating ALPHA Trader (qwen3:8b, general)..."
$CURL -s -X POST -H "Content-Type: application/json" -d '{
  "name": "ALPHA Trader",
  "role": "general",
  "title": "Autonomous Crypto Trading Strategist",
  "icon": "target",
  "capabilities": "Generates trading hypotheses, backtests strategies with Jesse framework, executes paper trades on Hyperliquid, builds skill files from successful patterns",
  "adapterType": "hermes_local",
  "adapterConfig": {
    "model": "qwen3:8b",
    "provider": "custom",
    "baseUrl": "http://localhost:11434/v1",
    "maxIterations": 50,
    "timeoutSec": 300,
    "persistSession": true,
    "enabledToolsets": ["terminal", "file", "web"]
  }
}' "$PAPERCLIP_URL/api/companies/$COMPANY_ID/agents" | python3 -c "import json,sys;a=json.load(sys.stdin);print(f'  ✓ {a[\"name\"]} ({a[\"urlKey\"]}) — {a[\"id\"]}')"

echo ""
echo "🎉 Henko Sys x01 team is ready!"
echo ""
echo "View agents: $PAPERCLIP_URL/#/company/$COMPANY_ID"
echo "Wake up an agent via API:"
echo "  curl -X POST $PAPERCLIP_URL/api/agents/<AGENT_ID>/wakeup \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"prompt\":\"your task here\"}'"
