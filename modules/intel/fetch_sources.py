"""
INTEL source fetchers — pulls AI-relevant news from public APIs.

Used by generate-briefing.py to ground briefings in real content instead
of relying on model knowledge cutoff. All fetchers fail-soft: a single
broken source returns an empty list and logs the error, never raises.

Sources (all public, no auth):
- Hacker News top stories (Algolia HN Search API)
- HuggingFace daily papers (HF API)
- GitHub recent AI repos (official GitHub Search API, no auth, 60 req/h)

Why subprocess curl instead of urllib/requests:
    Same as generate-briefing.py — under WSL2 mirrored networking,
    Python's urllib stack hangs in _read_status() waiting for the HTTP
    status line. curl is reliable for both localhost and public internet.

Usage (standalone smoke test):
    python3 modules/intel/fetch_sources.py [YYYY-MM-DD]
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
import urllib.parse

USER_AGENT = "henko-intel/0.1 (+https://github.com/i02202/henko-sys-x01)"
HTTP_TIMEOUT_S = 30

# AI-relevance keyword filter. Lowercase, substring match.
# Tunable: add Spanish-relevant terms, trading-AI niches, specific lab names.
AI_KEYWORDS: tuple[str, ...] = (
    # Generic
    "ai", "ml", "llm", "neural", "deep learning", "machine learning",
    "transformer", "diffusion", "embedding", "rag", "agent", "agentic",
    "fine-tun", "inference", "training", "rlhf", "dpo", "reasoning",
    "multimodal", "vision", "tts", "stt", "speech",
    # Frameworks / runtimes
    "pytorch", "tensorflow", "jax", "huggingface", "ollama", "vllm",
    "llama.cpp", "lora", "qlora", "mlx", "ggml", "gguf",
    # Vendors / labs / models
    "openai", "anthropic", "claude", "gpt", "gemini", "google deepmind",
    "deepseek", "qwen", "gemma", "llama", "mistral", "phi", "yi",
    "cohere", "stability", "stable diffusion", "midjourney", "runway",
    "groq", "openrouter", "perplexity", "nvidia", "cuda", "tpu",
)


def _http_get_json(url: str, timeout_s: int = HTTP_TIMEOUT_S) -> object | None:
    """GET JSON via curl subprocess. Returns parsed JSON or None on failure.

    Uses curl --fail-with-body so HTTP 4xx/5xx returns non-zero exit code
    AND keeps the response body in stdout (useful for debugging API errors
    like "rate limit exceeded" or "invalid query").
    """
    try:
        proc = subprocess.run(
            [
                "curl", "--silent", "--show-error", "--fail-with-body",
                "--max-time", str(timeout_s),
                "-A", USER_AGENT,
                "-H", "Accept: application/json",
                url,
            ],
            capture_output=True, text=True, timeout=timeout_s + 10,
        )
        if proc.returncode != 0:
            # Show both stderr (curl-side) and a snippet of stdout (server response body).
            err = proc.stderr.strip()[:120]
            body_snippet = proc.stdout.strip()[:200].replace("\n", " ")
            print(f"  ! HTTP fail {url}: exit={proc.returncode} stderr='{err}' body='{body_snippet}'", flush=True)
            return None
        if not proc.stdout.strip():
            print(f"  ! Empty body from {url}", flush=True)
            return None
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        print(f"  ! Timeout {url}", flush=True)
        return None
    except json.JSONDecodeError as e:
        print(f"  ! Bad JSON from {url}: {e}", flush=True)
        return None


_AI_KEYWORD_REGEX = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in AI_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def _is_ai_relevant(text: str) -> bool:
    """Keyword-based AI relevance check with word boundaries.

    Word boundaries (\\b) avoid false positives where short keywords like
    "ai" or "ml" match inside unrelated words ("domain", "html"). The
    regex is compiled once at module load.

    Trade-offs vs. alternatives we considered:
      - Embedding similarity: more recall, but adds nomic-embed dep + per-call cost
      - LLM-as-judge (qwen3:8b score): best quality, but ~5s/item × 100 items = 8 min
      - Pure keyword (this): fast, deterministic, misses subtle phrasings

    For a daily briefing where one missed story is recoverable, keyword
    filter is the right cost/value point.
    """
    return bool(_AI_KEYWORD_REGEX.search(text))


def _anchor_datetime(date_str: str | None) -> dt.datetime:
    """Resolve the anchor datetime for source fetching.

    For today (or no date passed), use real "now" so HN/GitHub windows
    end at the moment of fetch. For backfill (date_str != today), anchor
    to 23:59 UTC of that date so the windows reflect what was current
    at the end of that day, not at script runtime.
    """
    today_iso = dt.date.today().isoformat()
    if not date_str or date_str == today_iso:
        return dt.datetime.now(dt.timezone.utc)
    target = dt.date.fromisoformat(date_str)
    return dt.datetime.combine(target, dt.time(23, 59, 59), tzinfo=dt.timezone.utc)


def fetch_hn_top(limit: int = 15, anchor: dt.datetime | None = None) -> list[dict]:
    """Top Hacker News stories from the 24h ending at `anchor`, filtered for AI.

    Uses Algolia HN Search API. We over-fetch (limit*4) and post-filter
    to ensure we get `limit` AI-relevant items even on slow news days.
    For backfill, pass an `anchor` datetime in UTC; defaults to now-UTC.
    """
    if anchor is None:
        anchor = dt.datetime.now(dt.timezone.utc)
    since = int((anchor - dt.timedelta(days=1)).timestamp())
    until = int(anchor.timestamp())
    # Algolia rejects raw `>` in numericFilters — must URL-encode comparison ops.
    numeric_filters = urllib.parse.quote(
        f"created_at_i>{since},created_at_i<{until},points>10", safe=","
    )
    url = (
        "https://hn.algolia.com/api/v1/search_by_date"
        f"?tags=story&numericFilters={numeric_filters}"
        f"&hitsPerPage={limit * 4}"
    )
    data = _http_get_json(url)
    if not isinstance(data, dict):
        return []
    items: list[dict] = []
    for hit in data.get("hits", []):
        title = hit.get("title") or hit.get("story_title") or ""
        if not title or not _is_ai_relevant(title):
            continue
        obj_id = hit.get("objectID", "")
        items.append({
            "title": title,
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}",
            "points": hit.get("points", 0) or 0,
            "comments_url": f"https://news.ycombinator.com/item?id={obj_id}",
        })
    items.sort(key=lambda x: x["points"], reverse=True)
    return items[:limit]


def fetch_hf_daily_papers(date_str: str | None = None) -> list[dict]:
    """HuggingFace daily papers — latest available batch.

    Endpoint: https://huggingface.co/api/daily_papers
    No relevance filter — HF daily papers are AI-only by definition.

    Why we ignore date_str by default: HF publishes daily batches in UTC
    on weekdays. Asking for "today" before the batch lands (or on a
    weekend) returns []. The bare endpoint always returns the most
    recent available batch, which is what a daily briefing needs.
    Pass an explicit date only for historical backfill.
    """
    url = "https://huggingface.co/api/daily_papers"
    if date_str and date_str != dt.date.today().isoformat():
        url += f"?date={date_str}"
    data = _http_get_json(url)
    if not isinstance(data, list):
        return []
    items: list[dict] = []
    for entry in data[:20]:
        p = entry.get("paper", {}) if isinstance(entry, dict) else {}
        title = p.get("title", "")
        arxiv_id = p.get("id", "")
        if not title or not arxiv_id:
            continue
        items.append({
            "title": title,
            "url": f"https://huggingface.co/papers/{arxiv_id}",
            "arxiv_id": arxiv_id,
            "summary": (p.get("summary") or "").strip().replace("\n", " ")[:400],
            "upvotes": entry.get("upvotes", 0) or p.get("upvotes", 0) or 0,
        })
    items.sort(key=lambda x: x["upvotes"], reverse=True)
    return items[:10]


def fetch_github_recent_ai_repos(
    days: int = 7,
    limit: int = 8,
    anchor: dt.datetime | None = None,
) -> list[dict]:
    """Recently-created repos that mention AI/ML keywords, sorted by stars.

    Uses GitHub Search API — official, no auth, 60 req/h unauth limit
    (we use 1 per day, so safe). Search query targets repos created in
    the `days`-day window ending at `anchor` (UTC, defaults to now).
    """
    if anchor is None:
        anchor = dt.datetime.now(dt.timezone.utc)
    since = (anchor.date() - dt.timedelta(days=days)).isoformat()
    until = anchor.date().isoformat()
    # GitHub search query syntax — OR keywords + created-date range.
    # Encode the whole query string properly via urllib (handles : > = etc).
    query = f"ai OR llm OR agent created:{since}..{until}"
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": str(limit * 2),
    })
    data = _http_get_json(url)
    if not isinstance(data, dict):
        return []
    items: list[dict] = []
    for repo in data.get("items", [])[: limit * 2]:
        name = repo.get("full_name", "")
        desc = repo.get("description") or ""
        if not name:
            continue
        # Re-filter — GitHub search OR is permissive, ensure AI relevance.
        if not _is_ai_relevant(f"{name} {desc}"):
            continue
        items.append({
            "name": name,
            "url": repo.get("html_url") or f"https://github.com/{name}",
            "description": desc[:200],
            "stars": repo.get("stargazers_count", 0) or 0,
            "language": repo.get("language") or "",
        })
        if len(items) >= limit:
            break
    return items


def fetch_all_sources(date_str: str) -> dict:
    """Fetch all sources for the briefing of `date_str`. Each source fail-soft.

    All time-windowed sources (HN last 24h, GitHub last 7d) are anchored to
    the requested date so backfill returns data current as of that date,
    not as of script runtime.
    """
    anchor = _anchor_datetime(date_str)
    print(f"Fetching sources for {date_str} (anchor={anchor.isoformat()})...", flush=True)
    print("  [1/3] Hacker News (last 24h ending at anchor, AI-filtered)...", flush=True)
    hn = fetch_hn_top(limit=12, anchor=anchor)
    print(f"        -> {len(hn)} items", flush=True)
    print("  [2/3] HuggingFace daily papers...", flush=True)
    hf = fetch_hf_daily_papers(date_str)
    print(f"        -> {len(hf)} papers", flush=True)
    print("  [3/3] GitHub recent AI repos (last 7d ending at anchor)...", flush=True)
    gh = fetch_github_recent_ai_repos(days=7, limit=8, anchor=anchor)
    print(f"        -> {len(gh)} repos", flush=True)
    total = len(hn) + len(hf) + len(gh)
    print(f"Total source items: {total}", flush=True)
    return {
        "hacker_news": hn,
        "hf_papers": hf,
        "github_repos": gh,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "anchor_utc": anchor.isoformat(timespec="seconds"),
    }


if __name__ == "__main__":
    arg_date = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    sources = fetch_all_sources(arg_date)
    print()
    print(json.dumps(sources, indent=2, ensure_ascii=False))
