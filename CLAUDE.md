# Henko Sys x01 — Sovereign AI Operations Platform

## Project Identity
- **Name:** Henko Sys x01 ("Henko" = transformation in Japanese)
- **Owner:** @i02202 (Daniel Amer)
- **Purpose:** A modular, self-hosted, self-improving multi-agent system that researches, trades, and builds software autonomously.

## Architecture Overview

```
LAYER 4: INTERFACE      → Hermes Mission Control Dashboard
LAYER 3: STRATEGIC      → DeerFlow 2.0 (long-horizon orchestrator)
LAYER 2: OPERATIONAL    → Paperclip (agent-as-employee roles)
LAYER 1: AGENT RUNTIME  → Hermes Agent (self-improving, multi-platform messaging)
LAYER 0: INFRASTRUCTURE → Appwrite + Dokploy + PostHog + n8n + Inngest
```

## Modules

### ALPHA (Trading & Finance)
- Research → Strategy → Backtest → Execute → Learn → Repeat
- Execution via Hermes Agent on Hyperliquid
- Strategies as reusable skill files
- Backtesting with Jesse framework

### FORGE (Software Development)
- BMAD methodology: Analysis → Planning → Solutioning → Implementation
- Claude Code Agent Teams with worktrees for parallel dev
- Google Stitch 2.0 for design → code pipeline
- WorkOS CLI for enterprise auth
- Deploy via Dokploy (self-hosted)

### INTEL (Research & Intelligence)
- Geopolitical monitoring (sanctions, AI race, regulations)
- Tech intel (papers, GitHub trending, new models)
- Content generation (briefings, newsletters, social)
- RAG over persistent knowledge base

## Model Pool

### Tier 1: Local Models (Zero API Cost, Sovereign)
- **Gemma 4 E4B** — multimodal, lightweight (fits 8GB VRAM) — DOWNLOADING
- **Gemma 3 12B** — already installed, proven general-purpose
- **Qwen 3 32B** — already installed (20GB), strong reasoning + coding
- **Qwen 3 8B** — fast inference, good for simple/routing tasks
- **nomic-embed-text** — embeddings for RAG (274MB, installed)

### Tier 2: Cloud Models (Free or Low Cost)
- **GLM-5.1:cloud** — #1 SWE-Bench Pro coding agent (via `ollama run glm-5.1:cloud`, NOT local)
- **Gemini Agent Mode** — free research/automation via Google
- **Google Stitch 2.0** — free design generation

### Tier 3: Cloud Models (Paid, Fallback)
- **Claude** — complex reasoning, Claude Code Teams
- **GPT** — alternative for specific tasks
- **DeepSeek-R1 API** — reasoning (local 671B requires multi-node cluster, not feasible on single machine)

## Automation Layer
- **Claude Code Routines** — scheduled/webhook/API triggered tasks on Anthropic cloud
- **n8n** — visual workflow triggers
- **Inngest** — durable background jobs with retries

## Communication Channels (via Hermes Agent)
- Telegram, Discord, Slack, WhatsApp, Email

## Self-Improving Flywheel
Every trade, every project, every research session generates:
1. Skill files (reusable strategies/patterns)
2. Memory updates (persistent knowledge graph)
3. Error logs → prevention rules
4. Performance metrics → optimization targets

## Hardware (Verified)
- CPU: Intel i9-13900H (14 cores, 20 threads)
- RAM: 96GB DDR5
- GPU: NVIDIA RTX 4060 8GB VRAM (CUDA 13.1)
- Ollama: v0.20.7
- Docker: v29.2.1
- Node: v24.13.1, Python: 3.13.13

## Tech Stack
| Layer | Technology | License |
|-------|-----------|---------|
| Orchestrator | DeerFlow 2.0 (ByteDance) | MIT |
| Agent Company | Paperclip | Open Source |
| Agent Runtime | Hermes Agent (Nous Research) | Open Source |
| Dashboard | Hermes Mission Control | Open Source |
| Backend | Appwrite | BSD-3 |
| Deploy | Dokploy | Open Source |
| Analytics | PostHog | MIT (self-hosted) |
| Workflows | n8n + Inngest | Open Source |
| Project Mgmt | Plane | Open Source |
| Auth | WorkOS CLI | Free tier |
| Models | Ollama (local) | MIT |

## Implementation Phases

### Phase 1: Foundation (2-3 weeks)
- DeerFlow 2.0 setup + Ollama model pool
- Appwrite instance (Docker)
- Dokploy for self-hosted deploy
- Hermes Agent basic setup
- n8n for workflow triggers
- PostHog for analytics

### Phase 2: INTEL MVP (2 weeks)
- Research agent with RAG
- News/paper monitoring
- Daily briefings in Spanish
- Knowledge graph (Appwrite DB + embeddings)

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
- OpenClaw/Hermes trading: Across The Rubicon, Julian Goldie SEO, Michael Automates
- Claude Code: Developers Digest, WorkOS, Vaibhav Sisinty, Jack Roberts
- BMAD Method: WorldofAI
- ML Research: EDteam (Nested Learning), NVIDIA Developer (Cosmos Reason, CrewAI)
- Crypto/DeFi: Nazza Crypto, Javi Vega, Chris Yost (ICP/Caffeine AI)
- Dev Tools: Fazt (Dokploy, Appwrite, etc.), hdeleon.net (RAG)
- AI News (Spanish): Conciencia Artificial, Gustavo Entrala, AI Revolution en Espanol, Alejavi Rivera, Benjamin Cordero
- Algo Trading: Algo-trading with Saleh (Google Antigravity)
- Hardware: MINISFORUM (DeepSeek cluster)
- Education: Vida MRR (Marcos Rivas), AmalioMetria (GLM-5.1)
- DeerFlow: ByteDance open source (39K+ GitHub stars)
- Paperclip + Hermes: Julian Goldie SEO

## Conventions
- Language: English for code, Spanish for user-facing content and briefings
- Commits: conventional commits (feat:, fix:, docs:, etc.)
- Branch strategy: main + feature branches
- All infrastructure self-hosted unless explicitly noted
