"""
INTEL briefing generator (sovereign, no Hermes loop).

Generates a daily Spanish AI briefing via Ollama qwen3:8b, grounded in
real-time public sources (Hacker News, HuggingFace daily papers, GitHub
recent repos), and writes to /home/daniel/briefings/YYYY-MM-DD.md.

Usage (run from WSL2 Ubuntu):
    python3 modules/intel/generate-briefing.py [YYYY-MM-DD]
    (defaults to today)

Why this exists:
    Phase 2 INTEL agentic via Hermes+Paperclip is blocked by hardware/config
    mismatch (Hermes 64K-min ctx > 8GB VRAM). This script bypasses the agent
    loop and generates a usable briefing directly via Ollama API.

    Pre-2026-04-26 the briefing relied entirely on model knowledge, which
    produced fluent but hallucinated content (fictional papers, etc.).
    Now the prompt is grounded in real fetched sources via fetch_sources.py.

    See HANDOFF.md "Phase 2 starting points" for the agentic plan.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time

from fetch_sources import fetch_all_sources

OLLAMA_URL = "http://localhost:11434/api/generate"
# qwen3:8b: native 40K ctx, fits 5.7GB VRAM at small ctx, runs 19-37 tok/s on RTX 4060 8GB.
# Verified 2026-04-26: Hermes rejects this model (40K < 64K Hermes min) but Ollama direct is fine.
MODEL = "qwen3:8b"
# NUM_CTX is REQUESTED but Ollama uses the model's currently-loaded ctx if any
# other client already loaded it (e.g. ctx 4096 if DeerFlow loaded it first).
# 8192 is our preferred ceiling — the prompt is ~2400 tokens grounded + room for
# 1500-2000 token Spanish briefing response. Leave as a hint; do not over-trust.
NUM_CTX = 8192
KEEP_ALIVE = "30m"
# Generation timeout. Realistic warm cost on this hardware:
#   ~30s prefill (2400 prompt tokens) + ~1500 tokens × 19 tok/s ≈ 80s = ~2 min total.
# 600s ceiling gives margin for cold load + light contention. If another client
# is hammering /v1/chat/completions, we WILL timeout — see CLAUDE.md "Ollama
# Operational Notes" for the contention-detection playbook.
TIMEOUT_S = 600
OUTPUT_DIR = "/home/daniel/briefings"


def _format_sources_block(sources: dict) -> str:
    """Render fetched sources as a compact text block to inject into the prompt.

    Compact format optimized for token efficiency — bullets only, no JSON
    syntax noise. Each item carries enough context (title + url + signal
    metric) for the model to write a useful sentence about it.
    """
    parts: list[str] = []

    hn = sources.get("hacker_news") or []
    parts.append("### Hacker News (top AI stories last 24h, sorted by points)")
    if hn:
        for item in hn:
            parts.append(f"- [{item['points']} pts] {item['title']}  →  {item['url']}")
    else:
        parts.append("- (no items returned)")
    parts.append("")

    hf = sources.get("hf_papers") or []
    parts.append("### HuggingFace Daily Papers (latest batch, sorted by upvotes)")
    if hf:
        for p in hf:
            summary = (p.get("summary") or "").strip()
            if len(summary) > 280:
                summary = summary[:280] + "..."
            parts.append(
                f"- [{p['upvotes']} upvotes] {p['title']}  →  {p['url']}\n"
                f"  abstract: {summary}"
            )
    else:
        parts.append("- (no items returned)")
    parts.append("")

    gh = sources.get("github_repos") or []
    parts.append("### GitHub Recent AI Repos (created in last 7 days, sorted by stars)")
    if gh:
        for r in gh:
            lang = f", {r['language']}" if r.get("language") else ""
            desc = (r.get("description") or "").strip()
            parts.append(
                f"- [{r['stars']} ⭐{lang}] {r['name']}  →  {r['url']}\n"
                f"  description: {desc}"
            )
    else:
        parts.append("- (no items returned)")
    parts.append("")

    return "\n".join(parts)


def build_prompt(date_str: str, sources: dict) -> str:
    """Strict-citation briefing prompt — Spanish output, grounded in real sources.

    Strategy: option A (strict citation). The model is told to use ONLY the
    provided sources, never invent. Each bullet must link back to a source
    URL. Sections with sparse sources are flagged as such rather than padded
    with hallucinated content.

    Why English meta + Spanish output: the model follows instructions better
    when meta is in English, but produces more natural Spanish when the
    output target is explicit. Forcing the model to start with the H1
    header reduces meta-commentary preamble.

    To switch to a more synthesis-friendly variant later (option B/C/D),
    change the CRITICAL CONSTRAINTS block — the source-data injection
    machinery and structure stay identical.
    """
    sources_block = _format_sources_block(sources)
    return f"""Generate a daily AI news briefing in SPANISH for {date_str}.

You have been given REAL source data fetched from public APIs (Hacker News,
HuggingFace daily papers, GitHub recent repos). The data appears at the end
of this prompt under "SOURCE DATA".

CRITICAL CONSTRAINTS:
- Use ONLY items present in SOURCE DATA. DO NOT invent items, papers, or repos.
- DO NOT add background context from your training data — the briefing must
  be verifiable, every claim traceable to a listed source.
- Each bullet MUST end with the source URL in markdown link form.
- Translate titles and descriptions to NEUTRAL SPANISH (no regional variants).
- Write 400-700 words total. Output ONLY the briefing markdown — no preamble,
  no meta-commentary, no "here is your briefing", no closing remarks.
- If a section has fewer than 2 source items available, write what's available
  and add the line "_(pocas señales hoy en esta categoría)_" right after the heading.
- Start your response with EXACTLY the first line shown in REQUIRED FORMAT.

REQUIRED FORMAT (output exactly this structure, in Spanish):

# Briefing IA — {date_str}

## Lo más importante (Hacker News)

- **Título traducido** — 1-2 frases que resumen el ángulo. ([N pts]({{url}}))
  (3-5 items, los de mayor "points")

## Papers destacados (HuggingFace)

- **Título original en inglés** — 1-2 frases del abstract, traducidas al español. ([N upvotes]({{url}}))
  (3-4 papers)

## Repos en tendencia (GitHub, últimos 7 días)

- **autor/repo** (lenguaje, ⭐ N stars) — qué hace, traducido. ([repo]({{url}}))
  (3-5 repos)

## Para vigilar

- 2-3 bullets cortos sobre patrones que aparecen en MÚLTIPLES fuentes hoy
  (por ejemplo: tema repetido en HN + GitHub, o paper + repo relacionados).
  Si no hay overlap claro, escribí "_(no hay patrones cruzados claros hoy)_".

---

SOURCE DATA (real, fetched at briefing generation time — do not modify URLs):

{sources_block}

---

START NOW with the first line "# Briefing IA — {date_str}". Do not write anything before it."""


def stream_generate(prompt: str) -> tuple[str, dict]:
    """Generate via Ollama using curl subprocess.

    Why curl instead of urllib: under WSL2 mirrored networking, Python's
    urllib hangs in `_read_status()` waiting for the HTTP status line —
    apparently a Python+mirrored-network buffering issue. curl handles it
    fine. We use stream=False and accept the full latency upfront because
    the request is one-shot and we don't need progressive UI here.
    """
    body = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": KEEP_ALIVE,
        "options": {"num_ctx": NUM_CTX, "temperature": 0.6},
    }
    body_json = json.dumps(body)
    print(f"  POST {OLLAMA_URL}  (prompt {len(prompt)} chars, num_ctx={NUM_CTX})")
    print(f"  Waiting for model... (no streaming, expect 3-8 min on CPU)")
    proc = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--max-time",
            str(TIMEOUT_S),
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            "@-",
            OLLAMA_URL,
        ],
        input=body_json,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S + 30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed (exit {proc.returncode}): {proc.stderr.strip()}")
    if not proc.stdout.strip():
        raise RuntimeError("Ollama returned empty response")
    obj = json.loads(proc.stdout)
    return obj.get("response", ""), obj


def write_briefing(text: str, date_str: str, stats: dict, sources: dict) -> str:
    """Write briefing with YAML frontmatter for future RAG ingestion."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{date_str}.md")
    gen_s = stats.get("eval_duration", 0) / 1e9
    eval_count = stats.get("eval_count", 0)
    tok_per_s = eval_count / gen_s if gen_s > 0 else 0
    n_hn = len(sources.get("hacker_news") or [])
    n_hf = len(sources.get("hf_papers") or [])
    n_gh = len(sources.get("github_repos") or [])
    # Use timezone-aware UTC timestamp so future RAG ingestion can sort/compare
    # briefings across timezones unambiguously. Naive timestamps create
    # painful ambiguity once you're aggregating runs from cron, manual, etc.
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    frontmatter = (
        "---\n"
        f"date: {date_str}\n"
        f"generated_at: {generated_at}\n"
        f"model: {MODEL}\n"
        f"generator: modules/intel/generate-briefing.py\n"
        f"agentic: false\n"
        f"web_access: true\n"
        f"sources_fetched_at: {sources.get('fetched_at', '')}\n"
        f"sources_anchor_utc: {sources.get('anchor_utc', '')}\n"
        f"sources_hacker_news: {n_hn}\n"
        f"sources_hf_papers: {n_hf}\n"
        f"sources_github_repos: {n_gh}\n"
        f"sources_total: {n_hn + n_hf + n_gh}\n"
        f"tokens_generated: {eval_count}\n"
        f"throughput_tok_per_s: {tok_per_s:.2f}\n"
        f"total_duration_s: {stats.get('total_duration', 0) / 1e9:.2f}\n"
        "---\n\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(frontmatter + text.strip() + "\n")
    return path


def main() -> int:
    date_str = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    # Validate format early — silent acceptance of malformed dates would
    # cascade into bad filenames and confused source-fetch anchors.
    try:
        dt.date.fromisoformat(date_str)
    except ValueError:
        print(f"Invalid date '{date_str}'. Expected YYYY-MM-DD.", file=sys.stderr)
        return 4
    print(f"Generating briefing for {date_str} via {MODEL} (ctx={NUM_CTX})...")
    print("=" * 60)
    sources = fetch_all_sources(date_str)
    total = sum(len(sources.get(k) or []) for k in ("hacker_news", "hf_papers", "github_repos"))
    if total == 0:
        print("All sources returned 0 items — aborting (won't generate hallucinated briefing).", file=sys.stderr)
        return 3
    print("=" * 60)
    start = time.monotonic()
    try:
        text, stats = stream_generate(build_prompt(date_str, sources))
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"\nGeneration failed: {e}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - start
    print("=" * 60)
    print(f"Generated {stats.get('eval_count', 0)} tokens in {elapsed:.1f}s")
    path = write_briefing(text, date_str, stats, sources)
    print(f"Wrote {len(text)} chars to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
