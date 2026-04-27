"""
INTEL briefing generator (sovereign, no Hermes loop).

Generates a daily Spanish AI briefing via Ollama gemma4:e4b and writes
to /home/daniel/briefings/YYYY-MM-DD.md.

Usage (run from WSL2 Ubuntu):
    python3 modules/intel/generate-briefing.py [YYYY-MM-DD]
    (defaults to today)

Why this exists:
    Phase 2 INTEL agentic via Hermes+Paperclip is blocked by hardware/config
    mismatch (Hermes 64K-min ctx > 8GB VRAM). This script bypasses the agent
    loop and generates a usable briefing directly via Ollama API. Same model,
    same Spanish output target, no agentic overhead.

    See HANDOFF.md "Phase 2 starting points" for the agentic plan.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
# qwen3:8b: native 40K ctx, fits 5.7GB VRAM at small ctx, runs ~14 tok/s on RTX 4060 8GB.
# Verified 2026-04-26: Hermes rejects this model (40K < 64K Hermes min) but Ollama direct is fine.
MODEL = "qwen3:8b"
NUM_CTX = 8192  # Keep small so KV cache + model fits in 8GB VRAM with margin.
KEEP_ALIVE = "30m"
TIMEOUT_S = 600  # 10 min hard ceiling — at ~14 tok/s, 800 tokens completes in <1 min.
OUTPUT_DIR = "/home/daniel/briefings"


def build_prompt(date_str: str) -> str:
    """Briefing prompt — English meta-instructions, Spanish output target.

    Why English meta + Spanish output: the model follows instructions better
    when meta is in English, but produces more natural Spanish when the output
    target is explicit. Forcing the model to start the response with the
    H1 header reduces meta-commentary preamble.
    """
    return f"""Generate a daily AI news briefing in SPANISH for {date_str}.

CRITICAL CONSTRAINTS:
- You DO NOT have internet access. Use ONLY your model knowledge (cutoff ~2024-2025).
- Mark each section's intro line with: "_(basado en conocimiento del modelo, sin acceso web)_"
- Write 300-600 words total in NEUTRAL SPANISH (not regional variants).
- Output ONLY the briefing markdown. No preamble, no meta-commentary, no "here is your briefing", no closing remarks.
- Start your response with EXACTLY the first line below.

REQUIRED FORMAT (output exactly this structure, in Spanish):

# Briefing IA — {date_str}

## Lo más importante
_(basado en conocimiento del modelo, sin acceso web)_

- (3-5 bullets de tendencias generales en IA/ML que estaban activas a tu fecha de corte: nuevos modelos grandes, regulación, agentes autónomos, etc.)

## Papers destacados
_(basado en conocimiento del modelo, sin acceso web)_

- **Título del paper** — autores principales — relevancia (1-2 frases por paper, 2-3 papers)

## Repos y herramientas en tendencia
_(basado en conocimiento del modelo, sin acceso web)_

- **nombre/repo** — qué hace, por qué importa (2-3 entradas)

## Para vigilar
_(basado en conocimiento del modelo, sin acceso web)_

- 1-3 items: temas o lanzamientos a seguir en los próximos días/semanas

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


def write_briefing(text: str, date_str: str, stats: dict) -> str:
    """Write briefing with YAML frontmatter for future RAG ingestion."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{date_str}.md")
    gen_s = stats.get("eval_duration", 0) / 1e9
    eval_count = stats.get("eval_count", 0)
    tok_per_s = eval_count / gen_s if gen_s > 0 else 0
    frontmatter = (
        "---\n"
        f"date: {date_str}\n"
        f"generated_at: {dt.datetime.now().isoformat(timespec='seconds')}\n"
        f"model: {MODEL}\n"
        f"generator: modules/intel/generate-briefing.py\n"
        f"agentic: false\n"
        f"web_access: false\n"
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
    print(f"Generating briefing for {date_str} via {MODEL} (ctx={NUM_CTX})...")
    print("=" * 60)
    start = time.monotonic()
    try:
        text, stats = stream_generate(build_prompt(date_str))
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"\nGeneration failed: {e}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - start
    print("=" * 60)
    print(f"Generated {stats.get('eval_count', 0)} tokens in {elapsed:.1f}s")
    path = write_briefing(text, date_str, stats)
    print(f"Wrote {len(text)} chars to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
