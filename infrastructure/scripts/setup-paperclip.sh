#!/bin/bash
# ==============================================================================
# Henko Sys x01 — Paperclip Setup (WSL2)
# ==============================================================================
# Installs Paperclip (AI Company OS) in WSL2 Ubuntu.
#
# Prerequisites:
# - WSL2 Ubuntu with mirrored networking
# - Non-root user (Paperclip requires it for embedded Postgres)
# - Node.js 20+ and pnpm 9.15+
# - Port 3100 free on host Windows
#
# Run from Windows (PowerShell/Git Bash):
#   wsl -d Ubuntu -u daniel -- bash -c "$(cat infrastructure/scripts/setup-paperclip.sh)"
# ==============================================================================
set -e

echo "🌟 Henko Sys x01 — Paperclip Setup"
echo ""

# 1. Verify non-root user
if [ "$EUID" -eq 0 ]; then
  echo "❌ Paperclip cannot run as root (embedded Postgres requirement)."
  echo "   Run: wsl -d Ubuntu -u daniel -- bash -c \"\$(cat this-script.sh)\""
  exit 1
fi

# 2. Verify Node.js and pnpm
echo "🔍 Checking prerequisites..."
if ! command -v node &>/dev/null; then
  echo "❌ Node.js not installed. Install with:"
  echo "   curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -"
  echo "   sudo apt-get install -y nodejs"
  exit 1
fi
echo "  ✓ Node.js: $(node --version)"

if ! command -v pnpm &>/dev/null; then
  echo "  📦 Installing pnpm 9.15..."
  sudo npm install -g pnpm@9.15.0
fi
echo "  ✓ pnpm: $(pnpm --version)"

# 3. Check port 3100
if curl -s --connect-timeout 2 http://localhost:3100 &>/dev/null; then
  echo "  ⚠️  Port 3100 is in use. Paperclip default is 3100."
  echo "     If that's Paperclip already running, skip. Otherwise free the port."
fi

# 4. Run onboard
if [ ! -d "$HOME/.paperclip" ]; then
  echo ""
  echo "📥 Running Paperclip onboard (this takes ~5-10 minutes)..."
  cd ~
  npx paperclipai onboard --yes
else
  echo "✓ Paperclip already onboarded at ~/.paperclip"
  echo "  Start it with: pnpm paperclipai run"
fi

# 5. Smoke test
echo ""
echo "🧪 Smoke test: checking API health..."
sleep 2
if curl -s http://localhost:3100/api/health 2>&1 | grep -q '"status":"ok"'; then
  echo "✓ Paperclip API is healthy on http://localhost:3100"
else
  echo "⚠️  API didn't respond as expected. Check logs at ~/.paperclip/instances/default/logs/"
fi

# 6. Show adapter inventory
echo ""
echo "📋 Available agent adapters:"
curl -s http://localhost:3100/api/adapters 2>/dev/null | \
  python3 -c "import json,sys; [print(f'  • {a[\"type\"]} ({a[\"modelsCount\"]} models)') for a in json.load(sys.stdin)]" 2>/dev/null || \
  echo "  (unable to parse - check manually at http://localhost:3100)"

echo ""
echo "🎉 Paperclip setup complete!"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:3100 in your browser"
echo "  2. Complete initial setup wizard if prompted"
echo "  3. Create a Hermes agent employee with adapterType: 'hermes_local'"
echo "  4. Configure model: 'qwen3:8b' (or any Ollama model)"
