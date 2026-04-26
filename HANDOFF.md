# Henko Sys x01 — Session Handoff

> Last updated: 2026-04-26
> Phase 1 status: ✅ Complete
> Next phase: Phase 2 — INTEL MVP

This document is the canonical resume point for a new Claude Code session.
**It points to authoritative content elsewhere — don't duplicate.**

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

### Phase 2 task suggestions (issues to create)

```
1. "Compile a Spanish-language briefing of major AI/ML news from the last 24h.
    Sources: Hacker News, Hugging Face daily papers, GitHub trending. Output:
    /home/daniel/briefings/YYYY-MM-DD.md"

2. "Monitor arXiv cs.LG and cs.CL for papers about agent frameworks. Save the
    top 5 most relevant to /home/daniel/intel/papers/YYYY-MM-DD.json"

3. "Track the top 20 GitHub repos in 'AI agents' topic. Output a weekly delta
    of new entries to /home/daniel/intel/github-trends/YYYY-WW.md"
```

Use the API snippet in `CLAUDE.md` § "Working with agents — quick reference"
to create these issues.

### Hard prerequisites still missing for Phase 2

- **Appwrite is not installed** but Phase 2 requires it for the persistent
  knowledge base / vector store. Either:
  - Install Appwrite first (Phase 1b), or
  - Defer the knowledge graph and have INTEL write Markdown files instead.
- **No `infrastructure/scripts/setup-appwrite.sh` exists.** It needs to be created.
- **No vector store / RAG layer is wired.** `nomic-embed-text` is installed in
  Ollama but no consumer uses it yet.

### Hard prerequisites already met

- Ollama keep-alive (use 30m param when triggering long agent runs).
- Hermes-via-Paperclip is the stable entry point (issues + wakeup pattern).
- Hardware-aware model selection rules documented (see CLAUDE.md).

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
