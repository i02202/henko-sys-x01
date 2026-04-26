# Henko Sys x01

> **Henko** (変更, "transformation" in Japanese) — a sovereign, self-hosted, self-improving multi-agent AI platform that researches, trades, and builds software autonomously.

[![Phase 1](https://img.shields.io/badge/Phase_1-Complete-success)]() [![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

## Status

**Phase 1 (Foundation): ✅ COMPLETE**

End-to-end agent execution verified — `INTEL Researcher` and `FORGE Engineer` ran real tasks via Paperclip + Hermes + Ollama, with FORGE writing actual files to disk from a Paperclip issue.

See **[CLAUDE.md](CLAUDE.md)** for the full architecture, runbooks, learnings, and resume instructions.

## Modules

- **ALPHA** — autonomous crypto trading (Hyperliquid, Jesse backtesting, skill files)
- **FORGE** — software development (BMAD methodology, Claude Code Teams, design→code)
- **INTEL** — research & intelligence (RSS, papers, briefings in Spanish)

## Architecture (4 layers)

```
Hermes Mission Control (UI)
        ↓
DeerFlow 2.0 (long-horizon orchestrator)
        ↓
Paperclip 2026.416.0 (employee/company OS)
        ↓
Hermes Agent v0.10.0 (skills, memory, tools)
        ↓
Ollama (local models — qwen3:8b, gemma4:e4b, gemma3:12b, ...)
```

## Quick Start

**Prerequisites:** Windows 11 + WSL2 (Ubuntu) + Docker Desktop + Ollama.

```bash
# 1. Clone with submodules
git clone --recurse-submodules https://github.com/i02202/henko-sys-x01.git
cd henko-sys-x01

# 2. Apply DeerFlow patches (one-time)
bash infrastructure/scripts/bootstrap-deerflow.sh

# 3. Configure secrets
cp infrastructure/docker/.env.example infrastructure/docker/.env
# edit .env and fill in N8N_ENCRYPTION_KEY and N8N_DB_PASSWORD

# 4. Start Docker services (n8n)
cd infrastructure/docker && docker compose up -d && cd ../..

# 5. Start DeerFlow
MSYS_NO_PATHCONV=1 bash core/deerflow/deer-flow/scripts/docker.sh start --gateway

# 6. Set up Hermes Agent in WSL2 (one-time)
wsl -d Ubuntu -u daniel -- bash /mnt/c/Users/<you>/henko-sys-x01/infrastructure/scripts/setup-hermes.sh

# 7. Set up Paperclip in WSL2 (one-time)
wsl -d Ubuntu -u daniel -- bash /mnt/c/Users/<you>/henko-sys-x01/infrastructure/scripts/setup-paperclip.sh

# 8. Install Paperclip auto-start systemd service
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/c/Users/<you>/henko-sys-x01/infrastructure/scripts/install-paperclip-systemd.sh

# 9. Create the agent team
bash infrastructure/scripts/create-henko-agents.sh
```

After step 9, browse to `http://localhost:3100` to see your agent company.

## Verify it's running

```bash
curl.exe -s http://localhost:11434          # Ollama
curl.exe -s http://localhost:5678           # n8n
curl.exe -s http://localhost:2026           # DeerFlow
curl.exe -s http://localhost:3100/api/health  # Paperclip
```

All four should respond with HTTP 200.

> **Note (Windows):** use `curl.exe`, not Git Bash's `curl` — see [CLAUDE.md § Git Bash gotchas](CLAUDE.md) for why.

## What's next

- **Phase 2 — INTEL MVP:** assign real research tickets to INTEL Researcher (daily AI/crypto briefings in Spanish, paper monitoring, GitHub trends).
- **Phase 1b — backend services:** Appwrite (BaaS), PostHog (analytics), Dokploy (self-hosted deploy).
- **Phase 3 — FORGE MVP:** ship a real client project with FORGE Engineer using BMAD.
- **Phase 4 — ALPHA MVP:** paper trading on Hyperliquid via Hermes adapter.

## License

MIT
