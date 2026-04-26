#!/usr/bin/env bash
# ==============================================================================
# Henko Sys x01 — DeerFlow Bootstrap
# ==============================================================================
# Initializes DeerFlow submodule and applies Henko-specific patches.
#
# Run from project root:
#   bash infrastructure/scripts/bootstrap-deerflow.sh
#
# This script is idempotent: safe to re-run.
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEERFLOW_DIR="$REPO_ROOT/core/deerflow/deer-flow"
PATCHES_DIR="$REPO_ROOT/infrastructure/patches"

echo "🌟 Henko Sys x01 — DeerFlow Bootstrap"
echo ""

# 1. Ensure submodule is initialized
if [ ! -d "$DEERFLOW_DIR/.git" ] && [ ! -f "$DEERFLOW_DIR/.git" ]; then
  echo "📥 Initializing DeerFlow submodule..."
  cd "$REPO_ROOT"
  git submodule update --init --recursive core/deerflow/deer-flow
else
  echo "✓ DeerFlow submodule already initialized"
fi

# 2. Apply Henko patches (idempotent — patches must be reverse-checkable)
echo ""
echo "🔧 Applying Henko patches..."
cd "$DEERFLOW_DIR"

for patch in "$PATCHES_DIR"/*.patch; do
  [ -f "$patch" ] || continue
  name=$(basename "$patch")

  if git apply --reverse --check "$patch" 2>/dev/null; then
    echo "  ⟳ Already applied: $name (skipping)"
  elif git apply --check "$patch" 2>/dev/null; then
    git apply "$patch"
    echo "  ✓ Applied: $name"
  else
    echo "  ⚠️  Cannot apply $name — file conflicts (skipping)" >&2
  fi
done

echo ""
echo "✅ DeerFlow ready at: $DEERFLOW_DIR"
echo ""
echo "Next steps:"
echo "  cd $DEERFLOW_DIR"
echo "  cd backend && uv sync && cd .."
echo "  cd frontend && pnpm install && cd .."
echo "  bash scripts/docker.sh start --gateway"
