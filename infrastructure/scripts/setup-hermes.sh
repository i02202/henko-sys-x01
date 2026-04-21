#!/bin/bash
# ==============================================================================
# Henko Sys x01 — Hermes Agent Setup (WSL2)
# ==============================================================================
# Installs Hermes Agent in WSL2 Ubuntu and connects it to local Ollama.
#
# Prerequisites:
# - WSL2 Ubuntu installed (wsl --install -d Ubuntu)
# - Mirrored networking configured in ~/.wslconfig
# - Ollama running on Windows host (localhost:11434 via mirrored networking)
#
# Run from Windows (PowerShell/Git Bash):
#   wsl -d Ubuntu -- bash -c "$(cat infrastructure/scripts/setup-hermes.sh)"
# ==============================================================================
set -e

echo "🌟 Henko Sys x01 — Hermes Agent Setup"
echo ""

# 1. Install uv if not present
if ! command -v uv &>/dev/null; then
  echo "📦 Installing uv (Python package manager)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "✓ uv already installed"
fi

# 2. Verify Ollama is reachable from WSL2
echo ""
echo "🔌 Testing Ollama connectivity..."
if ! curl -s --connect-timeout 3 http://localhost:11434/ | grep -q "Ollama is running"; then
  echo "❌ Cannot reach Ollama on localhost:11434"
  echo "   Check that:"
  echo "   1. Ollama is running on Windows host"
  echo "   2. ~/.wslconfig has networkingMode=mirrored"
  echo "   3. WSL was restarted after config change: wsl --shutdown"
  exit 1
fi
echo "✓ Ollama reachable"

# 3. Clone and setup Hermes (if not already installed)
if [ ! -d "$HOME/.hermes/hermes-agent" ]; then
  echo ""
  echo "📥 Cloning Hermes Agent..."
  cd ~
  [ -d hermes-agent ] || git clone https://github.com/NousResearch/hermes-agent.git
  cd hermes-agent
  echo ""
  echo "⚙️  Running Hermes setup..."
  bash setup-hermes.sh
else
  echo "✓ Hermes Agent already installed at ~/.hermes/hermes-agent"
fi

# 4. Configure Hermes for Ollama local
echo ""
echo "🔧 Configuring Hermes for Ollama..."

# Backup existing config
[ -f ~/.hermes/config.yaml ] && cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%s)

# Update config.yaml: provider=custom, base_url=localhost:11434, default=qwen3:8b, context=65536
sed -i \
  -e 's|default: "anthropic/claude-opus-4.6"|default: "qwen3:8b"|' \
  -e 's|provider: "auto"|provider: "custom"|' \
  -e 's|provider: "ollama"|provider: "custom"|' \
  -e 's|base_url: "https://openrouter.ai/api/v1"|base_url: "http://localhost:11434/v1"|' \
  -e 's|# context_length: 131072|context_length: 65536|' \
  ~/.hermes/config.yaml

# Add fake API keys to .env (Ollama local doesn't need auth but OpenAI SDK requires something)
if ! grep -q "Henko Sys x01" ~/.hermes/.env 2>/dev/null; then
  cat >> ~/.hermes/.env <<'EOF'

# Henko Sys x01 — Ollama local (no real auth needed)
OPENROUTER_API_KEY=ollama-local-no-key-needed
OLLAMA_API_KEY=ollama-local-no-key-needed
OPENAI_API_KEY=ollama-local-no-key-needed
OPENAI_BASE_URL=http://localhost:11434/v1
EOF
fi

echo "✓ Config updated:"
grep -E '^  (default|provider|base_url|context_length):' ~/.hermes/config.yaml | head -4

# 5. Smoke test
echo ""
echo "🧪 Smoke test: asking Hermes to respond 'HELLO'..."
export PATH="$HOME/.local/bin:$PATH"
if hermes chat -q 'Reply in one word only: HELLO' -m qwen3:8b 2>&1 | grep -q "HELLO"; then
  echo "✓ Hermes Agent is working with Ollama!"
else
  echo "⚠️  Smoke test didn't find 'HELLO' in output — check logs manually with: hermes chat"
fi

echo ""
echo "🎉 Hermes Agent setup complete!"
echo ""
echo "Next steps:"
echo "  hermes chat                 # Interactive session"
echo "  hermes chat -q 'your query' # Single query"
echo "  hermes config               # View configuration"
echo "  hermes doctor               # Diagnose issues"
