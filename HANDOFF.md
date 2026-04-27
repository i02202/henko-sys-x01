# Henko Sys x01 — Session Handoff

> Last updated: 2026-04-26 (post Phase 2 MVP discovery session)
> Phase 1 status: ⚠️ Operational with caveats — see GitHub issue #2
> Phase 2 status: ✅ INTEL briefing pipeline live (sovereign, direct Ollama). ❌ Agentic loop blocked.

This document is the canonical resume point for a new Claude Code session.
**It points to authoritative content elsewhere — don't duplicate.**

---

## ⚠️ Read this BEFORE doing anything in Phase 2

The 2026-04-21 smoke tests passed by coincidence (trivial responses fit
within timeouts on degraded CPU mode). On 2026-04-26 we discovered:

1. **Hermes Agent enforces a 64K minimum context window** at agent init.
2. **No installed model with native ≥64K ctx fits in 8GB VRAM** — all fall back to CPU at ~0.6 tok/s, which times out before generating a useful response.
3. **The only model that loads in VRAM is `qwen3:8b` (40K native ctx)** — but Hermes rejects it for being below the 64K minimum.

**Net effect: agentic INTEL/FORGE/ALPHA via Hermes/Paperclip cannot complete real tasks on this hardware.** The smoke-test plumbing works; the throughput does not.

Full diagnosis + options forward in **GitHub issue #2**: https://github.com/i02202/henko-sys-x01/issues/2

**Working bypass:** `modules/intel/generate-briefing.py` calls Ollama directly
with `qwen3:8b` (in VRAM, ~37 tok/s) and writes briefings to
`/home/daniel/briefings/YYYY-MM-DD.md`. Use this pattern for any single-shot
LLM task until hardware is upgraded or Hermes is patched.

---

## TL;DR — Where we are

Phase 1 (Foundation) is operational. A multi-layer sovereign agent stack runs
locally on your hardware:

```
Ollama (6 models) → Hermes Agent v0.10.0 → Paperclip 2026.416.0 → Henko company
                                         ↘ DeerFlow 2.0
                                         ↘ n8n
```

Three agents exist and have completed real tasks:

- **INTEL Researcher** — `qwen3:8b` — verified by autonomous wakeup run.
- **FORGE Engineer** — `gemma4:e4b` — verified by writing a Python file from a Paperclip issue.
- **ALPHA Trader** — `qwen3:8b` — created, untested.

GitHub: https://github.com/i02202/henko-sys-x01

---

## Resuming in a new Claude Code session — exact steps

### 1. Open a new Claude Code session in the repo

```bash
cd "C:\Users\Daniel Amer\henko-sys-x01"
claude
```

Claude will auto-load `CLAUDE.md` (project memory). That gives the new session
the full architecture, port map, agent IDs, and known issues.

### 2. Tell Claude what you want to do

Open with one of these (or paraphrase):

- *"Read HANDOFF.md and CLAUDE.md, then verify all services are up."*
- *"Start Phase 2: assign the INTEL Researcher a real task to generate a Spanish AI briefing for today."*
- *"Set up Appwrite as the Phase 1b backend for INTEL knowledge base."*

### 3. First commands the new session should run

```bash
# Verify everything is up
curl.exe -s http://localhost:11434                # Ollama
curl.exe -s http://localhost:5678                 # n8n
curl.exe -s http://localhost:2026                 # DeerFlow
curl.exe -s http://localhost:3100/api/health      # Paperclip

# If Paperclip is down, restart it via systemd:
wsl -d Ubuntu -- systemctl status henko-paperclip

# If Docker services are down, open Docker Desktop — they restart automatically.
```

If anything is missing, see the **Recovery & Resilience** section of `CLAUDE.md`.

---

## What's already done — don't redo

- Ollama models pulled: `qwen3:8b`, `qwen3:32b`, `gemma3:12b`, `gemma4:e4b`,
  `nomic-embed-text`, `campus-expert`. Don't re-pull.
- DeerFlow cloned + patched + running. **Use the submodule, don't re-clone.**
- Hermes Agent installed for both `root` and `daniel` users in WSL2 Ubuntu.
- Paperclip onboarded as `daniel` user (root won't work — Postgres rejects it).
- Three agents created with the IDs documented in `CLAUDE.md`. **Don't run
  `create-henko-agents.sh` again — it would create duplicates.**
- systemd service `henko-paperclip.service` enabled — Paperclip auto-starts.

---

## Phase 2 starting points

**Goal:** INTEL Researcher producing daily briefings.

### What works today (sovereign, non-agentic)

```bash
# Run from WSL2 Ubuntu — generates today's Spanish AI briefing in ~1-9 min
wsl -d Ubuntu -u daniel -- python3 /mnt/c/Users/Daniel\ Amer/henko-sys-x01/modules/intel/generate-briefing.py

# Pass an explicit date to backfill / replay
... generate-briefing.py 2026-04-25

# Output lands at /home/daniel/briefings/YYYY-MM-DD.md with YAML frontmatter
```

The script bypasses Hermes/Paperclip entirely and calls Ollama
`/api/generate` with `qwen3:8b` directly. See § "Sovereign Direct Generation
Pattern" in CLAUDE.md for why and how.

### Cron schedule (already installed)

The briefing runs daily at 07:00 local time via WSL crontab as user `daniel`.
Check status:

```bash
wsl -d Ubuntu -u daniel -- crontab -l
wsl -d Ubuntu -u daniel -- tail /home/daniel/briefings/.cron.log
```

### What does NOT work today (Hermes agentic path)

`POST /agents/<id>/wakeup` runs but Hermes init fails with
`Model qwen3:8b has a context window of 16,384 tokens, which is below the
minimum 64,000 required by Hermes Agent.` (or Hermes loads but Ollama times
out because no installed model fits in 8GB VRAM at 64K ctx).

**Don't waste time on agentic INTEL/FORGE/ALPHA tasks until issue #2 is
resolved.** Use the script pattern for any single-shot work.

### Next-up tasks (when ready)

1. **Web fetcher integration** — make briefing pull real news from Hacker News
   API, HuggingFace daily papers, GitHub trending. Without this the model
   hallucinates plausible-sounding but fictional content.

2. **Phase 1c hardware reconciliation (issue #2)** — pick one of:
   - Hardware upgrade to 16+ GB VRAM
   - Patch Hermes to allow <64K ctx
   - Configure Hermes to use Ollama Cloud / Claude API

3. **Appwrite installation** for persistent knowledge graph + RAG over briefings.

### Hard prerequisites already met

- `qwen3:8b` loads in VRAM (5.7 GB used, ~37 tok/s warm) on RTX 4060.
- `modules/intel/generate-briefing.py` proven end-to-end.
- Ollama keep-alive works (use `keep_alive: 30m` in API calls).
- systemd cron + WSL2 + Paperclip auto-start all stable.

---

## Known issues to be aware of in the next session

1. **Hermes loops past task completion.** Agents do the work in 1–2 min but
   keep iterating until the timeout. Mitigation: lower `maxIterations` or
   add explicit "exit immediately after writing" to issue descriptions.
2. **Wakeup `prompt` is ignored.** Always create issues for real tasks.
3. **`qwen3:32b` does not work on RTX 4060 8GB.** Don't reassign FORGE to it.
4. **Git Bash on Windows mangles `/api/`-style paths.** Always set
   `MSYS_NO_PATHCONV=1` for any command that passes a `/`-prefixed path
   to a WSL2/Linux process.
5. **Use `curl.exe`, not Git Bash's `curl`,** for any localhost service —
   WSL2 mirrored networking confuses Git Bash's curl.

All five are detailed in `CLAUDE.md`.

---

## Open follow-ups (not blocking, do when convenient)

- [ ] Empty dirs (`modules/{alpha,forge,intel}/`, `core/{hermes,paperclip}/`,
      `docs/{plans,research,specs}/`) have `.gitkeep` placeholders. Replace
      with real content as features are built.
- [ ] Decide whether `.claude/` should be gitignored (currently untracked).
- [ ] Add shellcheck to the `infrastructure/scripts/` files via CI.
- [ ] Add a verification step to `setup-hermes.sh` that fails if `sed -i`
      didn't actually patch the upstream config (catches upstream renames).
- [ ] Make `create-henko-agents.sh` idempotent (check if company / agents
      already exist before creating).

---

## How to abandon this session and start over (only if needed)

If the WSL2 Ubuntu environment is corrupted and you want a clean start:

1. `wsl --unregister Ubuntu` (DESTROYS Hermes + Paperclip data — files in
   the Henko company database will be lost).
2. `wsl --install -d Ubuntu`
3. Follow `README.md` "Quick Start" from step 6.

**Do not destroy the host filesystem `henko-sys-x01` directory** — it has
all the canonical scripts, configs, and the DeerFlow submodule.

---

## Appendix — useful one-liners

```bash
# List all Henko agents with status
curl.exe -s "http://localhost:3100/api/companies/770e612d-18f1-4f6e-acb5-2b621914ef21/agents" \
  | python3 -m json.tool

# Tail Paperclip logs (if running via systemd)
wsl -d Ubuntu -- sudo journalctl -u henko-paperclip -f

# Tail Paperclip stdout
wsl -d Ubuntu -- tail -f /var/log/henko-paperclip.log

# Check Hermes config (as daniel)
wsl -d Ubuntu -u daniel -- bash -lc "hermes config | head -40"
```
