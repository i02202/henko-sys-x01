# Henko Sys x01 — Sovereign AI Operations Platform

## Project Identity
- **Name:** Henko Sys x01 ("Henko" = transformation in Japanese)
- **Owner:** @i02202 (Daniel Amer)
- **GitHub:** https://github.com/i02202/henko-sys-x01
- **Purpose:** A modular, self-hosted, self-improving multi-agent system that researches, trades, and builds software autonomously.

## Architecture Overview

```
LAYER 4: INTERFACE      → Hermes Mission Control Dashboard
LAYER 3: STRATEGIC      → DeerFlow 2.0 (long-horizon orchestrator)
LAYER 2: OPERATIONAL    → Paperclip (agent-as-employee roles)
LAYER 1: AGENT RUNTIME  → Hermes Agent (self-improving, multi-platform messaging)
LAYER 0: INFRASTRUCTURE → n8n + Appwrite + Dokploy + PostHog + Inngest
```

## Modules

### ALPHA (Trading & Finance)
- Research → Strategy → Backtest → Execute → Learn → Repeat
- Execution via Hermes Agent on Hyperliquid
- Strategies as reusable skill files ("cartridges")
- Backtesting with Jesse framework
- Solana sniper for meme coins early detection
- Polymarket for prediction markets

### FORGE (Software Development)
- BMAD methodology: Analysis → Planning → Solutioning → Implementation
- Claude Code Agent Teams with worktrees for parallel dev
- Google Stitch 2.0 for design → code pipeline
- GLM-5.1:cloud for agentic coding (#1 SWE-Bench Pro)
- WorkOS CLI for enterprise auth in ~2 min
- Deploy via Dokploy (self-hosted)
- Self-improving skills: each project makes the system smarter

### INTEL (Research & Intelligence)
- Geopolitical monitoring (sanctions, AI race, regulations)
- Tech intel (papers, GitHub trending, new models)
- Content generation (briefings, newsletters, social media)
- RAG over persistent knowledge base
- Google Pomelli for brand-aware content generation

## Running Services (Phase 1 — VERIFIED)

| Service | Port | Status | Access |
|---------|------|--------|--------|
| **DeerFlow 2.0** | `localhost:2026` | ✅ Running (Docker) | UI + API via nginx reverse proxy |
| **DeerFlow Gateway** | `localhost:8001` | ✅ Running | API: `/api/models`, `/api/*` |
| **n8n** | `localhost:5678` | ✅ Running (Docker) | Workflow automation UI |
| **Ollama** | `localhost:11434` | ✅ Running | 6 local models |
| **Ubuntu WSL2** | — | ✅ Installed | Mirrored networking enabled |
| **Hermes Agent** | WSL2 CLI | ✅ Running | `hermes chat` in Ubuntu shell |
| **Paperclip** | `localhost:3100` | ✅ Running (WSL2) | AI Company OS, UI + API |

### Port Map (avoid conflicts)
- `:2026` — DeerFlow (nginx proxy)
- `:3000` — ftpa-expert (pre-existing, DO NOT use for Henko)
- `:3100` — worldstation (pre-existing, DO NOT use for Henko)
- `:5678` — n8n
- `:8001` — DeerFlow Gateway API
- `:11434` — Ollama

## Model Pool (ALL VERIFIED)

### Tier 1: Local Models (Zero API Cost, Sovereign)
| Model | Size | Capabilities | Status |
|-------|------|-------------|--------|
| **Gemma 4 E4B** | 9.6 GB | Multimodal + reasoning + vision | ✅ Installed |
| **Gemma 3 12B** | 8.1 GB | General-purpose multimodal | ✅ Installed |
| **Qwen 3 32B** | 20 GB | Strong reasoning + coding (CPU offload) | ✅ Installed |
| **Qwen 3 8B** | 5.2 GB | Fast inference, routing tasks | ✅ Installed |
| **nomic-embed-text** | 274 MB | Embeddings for RAG | ✅ Installed |
| **campus-expert** | 1.6 GB | Custom fine-tune (Qwen2 1.5B) | ✅ Installed |

### DeerFlow Config — Active Models
All 4 models configured in `core/deerflow/deer-flow/config.yaml`:
- `qwen3-32b` — primary reasoning (langchain_ollama:ChatOllama, thinking=true)
- `qwen3-8b` — fast routing (langchain_ollama:ChatOllama, thinking=true)
- `gemma3-12b` — multimodal vision (langchain_ollama:ChatOllama, vision=true)
- `gemma4-e4b` — multimodal + reasoning + vision (langchain_ollama:ChatOllama)

### Tier 2: Cloud Models (Free or Low Cost)
- **GLM-5.1:cloud** — #1 SWE-Bench Pro coding agent (via `ollama run glm-5.1:cloud`, NOT local)
- **Gemini Agent Mode** — free research/automation via Google
- **Google Stitch 2.0** — free design generation

### Tier 3: Cloud Models (Paid, Fallback)
- **Claude** — complex reasoning, Claude Code Teams, Claude Code Routines
- **GPT** — alternative for specific tasks
- **DeepSeek-R1 API** — reasoning (local 671B not feasible on single machine)

## Automation Layer
- **Claude Code Routines** — 3 types: Scheduled (cron), API (HTTP trigger), Webhook (GitHub events)
- **n8n** — visual workflow triggers (400+ integrations)
- **Inngest** — durable background jobs with retries (Phase 1b)

## Communication Channels
- DeerFlow native: Telegram, Slack, WeChat (built-in config.yaml)
- Hermes Agent: Telegram, Discord, Slack, WhatsApp, Signal, Email

## Self-Improving Flywheel
Every trade, every project, every research session generates:
1. Skill files (reusable strategies/patterns)
2. Memory updates (persistent knowledge graph via DeerFlow memory.json)
3. Error logs → prevention rules
4. Performance metrics → optimization targets
- DeerFlow `skill_evolution: enabled: true` allows autonomous skill creation

## Hardware (Verified)
- **CPU:** Intel i9-13900H (6 P-cores + 8 E-cores = 14 cores, 20 threads)
- **RAM:** 96GB DDR5 (2x 48GB)
- **GPU:** NVIDIA RTX 4060 8GB VRAM (CUDA 13.1, driver 591.86)
- **Ollama:** v0.20.7
- **Docker:** v29.2.1 (Docker Desktop)
- **Node:** v24.13.1, **pnpm:** 10.26.2
- **Python:** 3.13.13, **uv:** 0.10.12
- **MSYS2:** GCC 15.2.0 (MinGW64)
- **WSL2:** Ubuntu installed, mirrored networking (`~/.wslconfig`)
- **GitHub CLI:** authenticated as `i02202`

## Known Issues & Workarounds

### Git Bash path mangling (CRITICAL)
Git Bash on Windows converts `/api/` to `C:/Program Files/Git/api/`. 
**Fix:** Set `MSYS_NO_PATHCONV=1` before any command that uses paths starting with `/`.
Applied in: `core/deerflow/deer-flow/scripts/docker.sh` (line 238)

### curl vs curl.exe in Git Bash
With WSL2 mirrored networking, Git Bash's `curl` may fail to reach `localhost` Docker services.
**Fix:** Use `curl.exe` (Windows native) instead of `curl` for testing services.

### Port 3000 and 3100 occupied
Pre-existing projects (ftpa-expert on :3000, worldstation on :3100) use these ports.
**Fix:** DeerFlow uses :2026 via nginx. Future Henko services should avoid :3000 and :3100.

## Tech Stack
| Layer | Technology | License |
|-------|-----------|---------|
| Orchestrator | DeerFlow 2.0 (ByteDance) | MIT |
| Agent Company | Paperclip | Open Source |
| Agent Runtime | Hermes Agent (Nous Research) | Open Source |
| Dashboard | Hermes Mission Control | Community |
| Backend | Appwrite | BSD-3 |
| Deploy | Dokploy | Open Source |
| Analytics | PostHog | MIT (self-hosted) |
| Workflows | n8n + Inngest | Open Source |
| Project Mgmt | Plane | Open Source |
| Auth | WorkOS CLI | Free tier |
| Models | Ollama (local) | MIT |

## Implementation Phases

### Phase 1: Foundation — ✅ COMPLETE (2026-04-26)
- [x] Ollama model pool (6 models including Gemma 4)
- [x] DeerFlow 2.0 setup with Ollama integration (Docker, gateway mode)
- [x] n8n workflow automation (Docker)
- [x] Ubuntu WSL2 with mirrored networking
- [x] Fix nginx path mangling bug
- [x] Fix curl/curl.exe routing issue
- [x] Hermes Agent setup in WSL2 (connected to Ollama qwen3:8b, verified)
- [x] Paperclip setup in WSL2 (v2026.416.0, runs as daniel user, not root)
- [x] hermes_local adapter verified as builtin in Paperclip (no manual registration needed)
- [x] **3 Henko agents created via Paperclip API**: INTEL Researcher (qwen3:8b),
  FORGE Engineer (gemma4:e4b — empirically validated; qwen3:32b unviable),
  ALPHA Trader (qwen3:8b)
- [x] Hermes Agent v0.10.0 reinstalled as daniel user (separate from root install)
- [x] Hermes config copied + auxiliary models override (compression/vision/web_extract)
- [x] **Integration smoke test PASSED** — INTEL Researcher woke up, ran 5m13s, exit 0
- [x] **Real-task smoke test PASSED** — FORGE wrote `/home/daniel/forge-smoke-test.py`
  with `print('FORGE_OK')` from a real Paperclip issue (`640d71c3`)
- [x] systemd auto-start for Paperclip (resilient to WSL2/Docker restarts)
- [x] **Phase 1 COMPLETE — Henko Sys x01 is operational**

## Henko Agent Team (Initial Roster)

**Company:** "Henko Sys x01"
**Company ID:** `770e612d-18f1-4f6e-acb5-2b621914ef21`

| Agent | Role | Model | Agent ID | URL slug |
|-------|------|-------|----------|----------|
| 🔭 INTEL Researcher | researcher | qwen3:8b | `0e7497fe-2a86-452f-bfa4-8c060c0e5223` | `/intel-researcher` |
| 💻 FORGE Engineer | engineer | gemma4:e4b | `429a17bb-7922-4759-99e5-c56aeb9d5127` | `/forge-engineer` |
| 🎯 ALPHA Trader | general | qwen3:8b | `97c1bcd4-ec02-4742-bc9f-ef243b7227c3` | `/alpha-trader` |

All agents use `hermes_local` adapter → Ollama via `provider: custom` + `baseUrl: http://localhost:11434/v1`.

Reproducible script: `infrastructure/scripts/create-henko-agents.sh`

### Working with agents — quick reference

```bash
# 1. Create an issue assigned to an agent
curl.exe -s -X POST -H "Content-Type: application/json" -d '{
  "title": "your task title",
  "description": "exact instructions for the agent",
  "status": "todo",
  "priority": "high",
  "assigneeAgentId": "<AGENT_ID>"
}' "http://localhost:3100/api/companies/770e612d-18f1-4f6e-acb5-2b621914ef21/issues"

# 2. Wake the agent (empty body — agent reads its inbox)
curl.exe -s -X POST -H "Content-Type: application/json" -d "{}" \
  "http://localhost:3100/api/agents/<AGENT_ID>/wakeup"

# 3. Watch the run
curl.exe -s "http://localhost:3100/api/heartbeat-runs/<RUN_ID>"

# 4. If status=error, reset to idle:
curl.exe -X POST "http://localhost:3100/api/agents/<AGENT_ID>/resume"

# Pre-warm a model before heavy task (avoids 5-min cold start):
curl.exe -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen3:8b","prompt":"hi","keep_alive":"30m","stream":false}'
```

⚠️ **Don't put task instructions in the wakeup `prompt`** — Paperclip injects
employee context that overrides it. Use issues. See "Wakeup vs. Issue-Driven
Tasks" below.

## Smoke Test Results (2026-04-21)

First successful agent run:
- Agent: INTEL Researcher (`0e7497fe-2a86-452f-bfa4-8c060c0e5223`)
- Run ID: `ec30a16e-69a2-4079-99f8-b5d455b14c3c`
- Status: succeeded (exit 0)
- Duration: 5m 13s
- Model: qwen3:8b via Ollama (custom provider)
- Response: Agent correctly recognized Paperclip employee context, checked
  inbox/backlog, found no assigned issues, reported back. Confirms full
  autonomous loop: Paperclip → hermes_local adapter → Hermes CLI → Ollama
  → response → Paperclip log capture.

### Performance Notes
- First agent run took ~5 min due to model loading + skill initialization
- Workaround: pre-warm Ollama with `keep_alive: "30m"` parameter
- Agent timeout configured at 900s (default 300s was too short)
- Per-message latency drops significantly after first run (model stays in VRAM)

### Hardware-Aware Model Selection (RTX 4060 8GB VRAM)

After empirical testing on 2026-04-26, here's the **revised** truth on this hardware:

| Model | File size (Q4) | Native ctx | Total mem @ native ctx | VRAM fit (8GB) | Throughput |
|-------|----------------|------------|------------------------|----------------|------------|
| qwen3:8b | 5.2 GB | 40K | ~8.9 GB | ✅ 5.7 GB in VRAM (capped to 40K) | **13–37 tok/s** |
| gemma4:e4b | 9.6 GB | 128K | ~13 GB | ❌ CPU fallback (`size_vram: 0`) | 0.6–3.6 tok/s on CPU |
| gemma3:12b | 8.1 GB | 128K | ~12 GB | ❌ CPU fallback | slow |
| qwen3:32b | 20 GB | 32K | ~25 GB | ❌ Times out 30 min+ | not viable |
| campus-expert | 1.6 GB | 2K | ~2 GB | ✅ Fully in VRAM | ~50 tok/s |

**Critical realization (2026-04-26): Hermes Agent enforces a 64K minimum
context window** (`Failed to initialize agent: ... below the minimum 64,000
required by Hermes Agent`). qwen3:8b's native 40K is **rejected**, so
**Hermes is incompatible with the only model that fits in this VRAM**.

This was hidden by the 2026-04-21 smoke test passing with a trivial response
(~50-100 tokens, ran on degraded CPU within timeout). Real briefing/code-gen
tasks require hundreds of tokens and time out. See GitHub issue #2 for full
analysis and options forward.

**Sovereign Direct Generation Pattern (the working bypass)**

For single-shot generative tasks (briefings, summaries, translations), bypass
Hermes/Paperclip entirely and call Ollama directly. `modules/intel/generate-briefing.py`
implements this pattern:

- Uses `qwen3:8b` with `num_ctx: 8192` (small enough for VRAM, big enough for prompt)
- POSTs to `/api/generate` via `curl` subprocess (urllib hangs under WSL2 mirrored networking)
- Writes output to `/home/daniel/briefings/YYYY-MM-DD.md` with YAML frontmatter for future RAG ingestion
- Verified ~9 min cold-start (model load), ~1-2 min warm

Use this pattern for any single-shot LLM task on this hardware until either
(a) hardware upgrade to ≥16GB VRAM, or (b) Hermes patched to allow <64K ctx.

For tasks that genuinely need 32B+ reasoning, route to GLM-5.1:cloud
(Ollama Cloud) or Claude API instead of local qwen3:32b.

### Ollama Operational Notes

- **Auto-update is on by default and drifts hourly.** `app.log` confirms an
  in-process update checker firing every `1h0m0s`. Observed drift over 2 days:
  0.20.7 → 0.21.1 → 0.21.2 (logged in `%LOCALAPPDATA%\Ollama\upgrade.log`).
  Disable via systray "Allow auto-updates" toggle. There is no documented
  CLI/file flag — the setting lives in `%LOCALAPPDATA%\Ollama\db.sqlite`
  (no `sqlite3` shipped on host so direct edit isn't trivial).
- **`OLLAMA_FLASH_ATTENTION=1` and `OLLAMA_KV_CACHE_TYPE=q8_0`** are useful
  for fitting larger contexts in VRAM, but in our test the User-scope env vars
  did NOT propagate to the systray-launched serving process. To apply them
  reliably: launch `ollama serve` manually from a PowerShell session that has
  set `$env:OLLAMA_FLASH_ATTENTION = "1"` first.
- **`size_vram: 0` in `/api/ps`** means the model loaded in CPU mode. This
  causes 10–100× slowdown vs GPU mode. Always verify VRAM load before relying
  on inference speed estimates.
- **After `SIGINT` of an in-flight request, Ollama's serving process can
  enter a degraded state** where subsequent chat/generate requests hang. Full
  process kill + restart usually clears it. PowerShell:
  `Get-Process ollama* | Stop-Process -Force; Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"`.
- **Ollama is single-slot per loaded model** (`Parallel:1` in runner load
  request). A second client's request queues behind the first. Client-side
  `--max-time` does NOT abort the server-side work, so backlogged requests
  inherit the timeout — symptom is `0 bytes received` at exactly your
  configured timeout.
- **The first request after a model load decides the `KvSize`.** Subsequent
  calls passing a different `num_ctx` are silently ignored. Confirmed via
  server.log `KvSize:4096` even when the request body had `num_ctx:8192`.
  If a stricter ctx is required, unload the model first
  (`POST /api/generate {"model":"qwen3:8b","keep_alive":0}`) before reloading.
- **Identifying the noisy client.** When generation hangs and `/api/ps` shows
  unexpected models loading: `Get-NetTCPConnection -RemotePort 11434 -State Established`
  → take the `OwningProcess` IDs → `Get-CimInstance Win32_Process -Filter "ProcessId=N"`
  reveals the command line. On 2026-04-26 we identified a stray DeerFlow
  uvicorn (host process on :8001) spamming `/v1/chat/completions` every
  12-52 seconds. The Docker `deer-flow-gateway` container is separate and
  was uninvolved.

### Agent Behavior Discoveries

#### Wakeup vs. Issue-Driven Tasks
The `prompt` field in `POST /agents/:id/wakeup` **is largely ignored** because
Paperclip injects its own employee context that says "check your inbox for
assigned issues". To give an agent a real task:

1. `POST /companies/:id/issues` with `assigneeAgentId` set
2. `POST /agents/:id/wakeup` with empty body `{}`
3. Agent reads the issue, plans, executes tool calls

**Do NOT** rely on the wakeup `prompt` for task delivery. Use issues.

#### Agent Termination Issue (Hermes v0.10.0)
With `max_iterations: 100` and an open-ended task, Hermes does NOT terminate
cleanly after completing the work. Observed pattern:
- 0:00 — Agent starts, reads issue
- 1:30 — Agent makes tool call (file write succeeds)
- 1:30–15:00 — Agent loops: verifying, commenting, planning more work
- 15:00 — Paperclip kills with SIGINT (timeout)

**The actual work completes early** (~1-2 min for simple tasks), but the
agent over-thinks and never decides "done". This is a known Hermes pattern.

**Mitigations:**
- Lower `max_iterations` (e.g., `5` for simple tasks)
- Lower `timeoutSec` to fail-fast (e.g., `300s`)
- Write very specific issue descriptions: "Write file X. After writing, exit."
- Accept that timeout != failure — check the workspace/files for actual outputs

### First Real Agent Action — VERIFIED 2026-04-26
- Agent: FORGE Engineer (gemma4:e4b)
- Issue: `640d71c3` — "Smoke test: write hello-world Python file"
- Run: `aef6ad01` — status: timed_out (15m51s)
- **But: file `/home/daniel/forge-smoke-test.py` was created with `print('FORGE_OK')`**
- Conclusion: end-to-end agent action through Paperclip → Hermes → file system **works**.

## Recovery & Resilience

### After Machine Restart
Most services auto-recover thanks to:
- **Ollama**: Native Windows service, auto-starts
- **Docker containers** (`n8n`, `deer-flow-*`): `restart: unless-stopped` policy
- **Paperclip**: NOW auto-starts via `henko-paperclip.service` (systemd in WSL2)

### Manual Recovery (if needed)
1. Open Docker Desktop (auto-starts containers)
2. WSL2 Ubuntu auto-starts when Docker Desktop boots
3. Paperclip auto-starts via systemd (`systemctl status henko-paperclip`)
4. Agents may show `status=error` from interrupted runs — POST to `/api/agents/:id/resume` to reset to `idle`

### Useful Commands (WSL2)
```bash
systemctl status henko-paperclip     # Service health
journalctl -u henko-paperclip -f     # Live logs
tail -f /var/log/henko-paperclip.log # stdout from Paperclip
```

### Auto-start Setup (one-time)
```bash
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash \
  "/mnt/c/Users/Daniel Amer/henko-sys-x01/infrastructure/scripts/install-paperclip-systemd.sh"
```
- [ ] Appwrite instance (Phase 1b)
- [ ] PostHog analytics (Phase 1b)
- [ ] Dokploy self-hosted deploy (Phase 1b)

### Hermes Agent Configuration (Critical Discovery)
The provider resolver in Hermes v0.9.0 has a subtle bug: `provider: "ollama"` in config.yaml maps to "custom" during normalization but the custom-provider resolver requires a prefix like `custom:local`. The fix is to use `provider: "custom"` directly with explicit `base_url: "http://localhost:11434/v1"`.

Also required:
- `context_length: 65536` override in config.yaml (Hermes minimum is 64K, qwen3:8b native is 40K)
- Fake API keys in `~/.hermes/.env` (OpenAI SDK requires SOME key even for local)

See: `infrastructure/scripts/setup-hermes.sh` for reproducible setup.

### Paperclip Setup Notes (Critical Discoveries)
- **Cannot run as root** — embedded PostgreSQL refuses root. Create a non-root user first:
  `useradd -m -s /bin/bash daniel && usermod -aG sudo daniel`
- **`hermes_local` adapter is builtin** in Paperclip 2026.416.0 — no need to install
  `hermes-paperclip-adapter` separately (docs from NousResearch adapter repo are outdated).
- **Builtin adapters available**: claude_local, codex_local, cursor, gemini_local,
  hermes_local, http, openclaw_gateway, opencode_local, pi_local, process.
- **Must run in same environment as Hermes CLI** — `hermes_local` spawns Hermes as
  child process, not over network. Paperclip must run in WSL2 alongside Hermes.
- **Port 3100 shared with Windows** (mirrored networking) — conflicts with any Windows
  host process on 3100 (e.g., Docker containers mapped to 3100).

See: `infrastructure/scripts/setup-paperclip.sh` for reproducible setup.

### Phase 2: INTEL MVP — partially operational
- ✅ **Daily Spanish briefing via direct Ollama (sovereign, non-agentic)** — `modules/intel/generate-briefing.py` writes to `/home/daniel/briefings/YYYY-MM-DD.md`. First run: 2026-04-26.
- ✅ **Web grounding via `modules/intel/fetch_sources.py`** — pulls real items from HN (Algolia), HuggingFace daily papers, GitHub Search API. Strict-citation prompt (option A) instructs the model to use ONLY fetched items. Verified zero hallucination on 2026-04-26 generation.
- ❌ **Agentic INTEL via Hermes/Paperclip** — blocked by hardware/config mismatch (see § "Hardware-Aware Model Selection" + GitHub issue #2)
- ⏳ Research agent with RAG — needs Appwrite (Phase 1b). Briefings already carry TZ-aware frontmatter (`generated_at`, `sources_anchor_utc`, source counts) for clean ingestion.
- ⏳ Knowledge graph (Appwrite DB + embeddings)

### Phase 3: FORGE MVP (3 weeks)
- BMAD methodology agents (PM, Architect, Dev, QA)
- Claude Code Teams integration
- Google Stitch 2.0 → code pipeline
- GLM-5.1 as coding model
- Dokploy auto-deploy

### Phase 4: ALPHA MVP (3 weeks)
- Market data agents
- Strategy generation + backtesting (Jesse)
- Hermes Agent → Hyperliquid (paper trading first)
- Skill files for strategies
- Risk management rules

### Phase 5: Integration (2 weeks)
- Cross-module memory sharing
- Paperclip roles for all agents
- Mission Control dashboard
- Claude Code Routines (scheduled/webhooks)
- Self-improving flywheel activation

### Phase 6: Live Operations (Ongoing)
- ALPHA → live trading
- FORGE → real client projects
- INTEL → daily autonomous research
- Continuous skill improvement

## Key Research Sources
Videos and channels that informed this architecture:
- OpenClaw/Hermes trading: Across The Rubicon (x4), Julian Goldie SEO, Michael Automates
- Claude Code: Developers Digest (worktrees, self-improving skills), WorkOS (Agent Teams, CLI), Vaibhav Sisinty (mastery), Jack Roberts (design+code)
- BMAD Method: WorldofAI
- ML Research: EDteam (Nested Learning), NVIDIA Developer (Cosmos Reason, CrewAI+Nemotron)
- Crypto/DeFi: Nazza Crypto (Solana sniper), Javi Vega (OneKey), Chris Yost (ICP/Caffeine AI)
- Dev Tools: Fazt (Dokploy, Appwrite, PostHog, n8n, Plane), hdeleon.net (RAG personalization)
- AI News (Spanish): Conciencia Artificial, Gustavo Entrala, AI Revolution en Español (Doubao 2.0), Alejavi Rivera (Gemini), Benjamin Cordero (Claude Routines)
- Algo Trading: Algo-trading with Saleh (Google Antigravity + Gemini 3)
- Hardware: MINISFORUM (DeepSeek 671B cluster)
- Education: Vida MRR (Marcos Rivas @Microsoft), AmalioMetria (GLM-5.1+OpenClaw)
- Paperclip + Hermes: Julian Goldie SEO (PaperClip + Hermes + Gemma 4)
- DeerFlow: ByteDance open source (39K+ GitHub stars)

## Conventions
- Language: English for code, Spanish for user-facing content and briefings
- Commits: conventional commits (feat:, fix:, docs:, etc.)
- Branch strategy: main + feature branches
- All infrastructure self-hosted unless explicitly noted
- Use `curl.exe` instead of `curl` for testing services from Git Bash
- Set `MSYS_NO_PATHCONV=1` when running Docker commands from Git Bash
