"""
Henko Mission Control v0.1 — unified observability dashboard.

A tiny Python aggregator that:
- Polls Ollama, Paperclip, DeerFlow, n8n server-side (no browser CORS issues).
- Reads briefings directly from \\\\wsl.localhost\\Ubuntu\\... (Windows native path
  to WSL filesystem).
- Calls nvidia-smi for live GPU utilization + VRAM.
- Calls schtasks for the daily-briefing scheduled task state.
- Tails the Ollama server log for recent traffic.

Serves a single static HTML page that polls /api/snapshot every few seconds.
No external dependencies — uses only Python stdlib so it runs under any
Python 3.10+ install on Windows.

Run:
    python modules/dashboard/server.py
    # then open http://localhost:7654
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ---- Configuration ----------------------------------------------------------

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 7654

OLLAMA_URL    = "http://localhost:11434"
PAPERCLIP_URL = "http://localhost:3100"
DEERFLOW_URL  = "http://localhost:2026"
N8N_URL       = "http://localhost:5678"

HENKO_COMPANY_ID = "770e612d-18f1-4f6e-acb5-2b621914ef21"

# Path to WSL filesystem from Windows host (UNC). \\wsl.localhost\<distro>\...
BRIEFINGS_PATH = Path(r"\\wsl.localhost\Ubuntu\home\daniel\briefings")

# AppData paths. Microsoft Store Python sandboxes %LOCALAPPDATA% to a
# per-package cache (PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\
# LocalCache\Local), where Ollama/HenkoSysX01 don't exist. Path.home()
# returns the real profile path on every Python flavor we tested, so derive
# from there. If you launch with a non-Store Python, env-var $LOCALAPPDATA
# also works — but Path.home() is sandbox-safe and identical in both cases.
APPDATA_LOCAL = Path.home() / "AppData" / "Local"
OLLAMA_LOG_PATH = APPDATA_LOCAL / "Ollama" / "server.log"
SCHEDULER_LOG_DIR = APPDATA_LOCAL / "HenkoSysX01" / "logs"

SCHEDULED_TASK_NAME = "Henko-INTEL-DailyBriefing"

# Where this script lives (so we can serve dashboard.html alongside it).
HERE = Path(__file__).resolve().parent

# Cache GPU reads briefly — nvidia-smi takes ~500ms and we don't need 3-second
# resolution on a metric that changes slowly. Same logic for the slow Paperclip
# agents fetch on slow days.
_cache: dict[str, tuple[float, object]] = {}
_cache_lock = threading.Lock()


def _cached(key: str, ttl_s: float, producer):
    now = dt.datetime.now().timestamp()
    with _cache_lock:
        entry = _cache.get(key)
        if entry and now - entry[0] < ttl_s:
            return entry[1]
    value = producer()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


# ---- Probes -----------------------------------------------------------------

def _http_json(url: str, timeout: float = 3.0) -> object | None:
    """GET JSON via stdlib urllib. Returns None on any failure."""
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8")
        return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _http_alive(url: str, timeout: float = 2.0) -> bool:
    """HEAD/GET a URL and return True if it responded with any 2xx/3xx/4xx."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 500
    except urllib.error.HTTPError:
        return True  # 4xx still means the server is up
    except Exception:
        return False


def probe_ollama() -> dict:
    version = _http_json(f"{OLLAMA_URL}/api/version")
    ps      = _http_json(f"{OLLAMA_URL}/api/ps")
    tags    = _http_json(f"{OLLAMA_URL}/api/tags")
    if not version:
        return {"ok": False, "url": OLLAMA_URL}
    loaded = []
    for m in (ps or {}).get("models", []) if isinstance(ps, dict) else []:
        size = m.get("size", 0)
        size_vram = m.get("size_vram", 0)
        expires_at = m.get("expires_at", "")
        expires_in_min = None
        if expires_at:
            try:
                # expires_at is e.g. "2026-04-27T00:30:21.5422952-04:00"
                exp = dt.datetime.fromisoformat(expires_at)
                now = dt.datetime.now(exp.tzinfo)
                expires_in_min = round((exp - now).total_seconds() / 60, 1)
            except (ValueError, TypeError):
                pass
        loaded.append({
            "name": m.get("name", "?"),
            "size_gb": round(size / 1e9, 2),
            "vram_gb": round(size_vram / 1e9, 2),
            "vram_pct": round(100 * size_vram / size, 1) if size > 0 else 0,
            "ctx": m.get("context_length", 0),
            "expires_in_min": expires_in_min,
            "quantization": (m.get("details") or {}).get("quantization_level", ""),
        })
    available_count = len((tags or {}).get("models", [])) if isinstance(tags, dict) else 0
    return {
        "ok": True,
        "url": OLLAMA_URL,
        "version": (version or {}).get("version", "?"),
        "loaded_models": loaded,
        "available_models_count": available_count,
    }


def probe_paperclip() -> dict:
    health = _http_json(f"{PAPERCLIP_URL}/api/health")
    if not isinstance(health, dict):
        return {"ok": False, "url": PAPERCLIP_URL, "agents": []}
    # Agent list — cache 8s since this is the heaviest call.
    def _fetch_agents():
        agents = _http_json(f"{PAPERCLIP_URL}/api/companies/{HENKO_COMPANY_ID}/agents")
        if not isinstance(agents, list):
            return []
        return [{
            "id": a.get("id"),
            "name": a.get("name", "?"),
            "role": a.get("role", ""),
            "status": a.get("status", "?"),
            "model": (a.get("adapterConfig") or {}).get("model", ""),
            "url_key": a.get("urlKey", ""),
            "last_heartbeat": a.get("lastHeartbeatAt"),
            "heartbeat_enabled": (a.get("runtimeConfig") or {}).get("heartbeat", {}).get("enabled", False),
        } for a in agents]
    agents = _cached("paperclip_agents", 8.0, _fetch_agents)
    return {
        "ok": True,
        "url": PAPERCLIP_URL,
        "version": health.get("version", "?"),
        "deployment_mode": health.get("deploymentMode", "?"),
        "auth_ready": health.get("authReady", False),
        "agents": agents,
    }


def probe_deerflow() -> dict:
    return {"ok": _http_alive(DEERFLOW_URL, timeout=2), "url": DEERFLOW_URL}


def probe_n8n() -> dict:
    return {"ok": _http_alive(N8N_URL, timeout=2), "url": N8N_URL}


def probe_gpu() -> dict:
    """Call nvidia-smi for one-line GPU snapshot. Cache 2s."""
    def _fetch():
        try:
            proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=4,
            )
            if proc.returncode != 0:
                return {"ok": False, "error": proc.stderr.strip()[:200]}
            line = proc.stdout.strip().splitlines()[0]
            name, util, used, total = [p.strip() for p in line.split(",")]
            return {
                "ok": True,
                "name": name,
                "utilization_pct": int(util),
                "vram_used_mib": int(used),
                "vram_total_mib": int(total),
                "vram_pct": round(100 * int(used) / int(total), 1) if int(total) else 0,
            }
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError) as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return _cached("gpu", 2.0, _fetch)


def probe_task_scheduler() -> dict:
    """Read the daily-briefing scheduled task state via PowerShell."""
    def _fetch():
        try:
            ps_cmd = (
                f"$t = Get-ScheduledTask -TaskName '{SCHEDULED_TASK_NAME}' -ErrorAction Stop; "
                f"$i = Get-ScheduledTaskInfo -TaskName '{SCHEDULED_TASK_NAME}'; "
                "[pscustomobject]@{ "
                "  state=$t.State.ToString(); "
                "  next_run=if($i.NextRunTime){$i.NextRunTime.ToString('o')}else{$null}; "
                "  last_run=if($i.LastRunTime -gt (Get-Date '1970-01-01')){$i.LastRunTime.ToString('o')}else{$null}; "
                "  last_result=$i.LastTaskResult "
                "} | ConvertTo-Json -Compress"
            )
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=8,
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                return {"ok": False, "error": proc.stderr.strip()[:200] or "task not found"}
            data = json.loads(proc.stdout.strip())
            return {"ok": True, "name": SCHEDULED_TASK_NAME, **data}
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return _cached("task_scheduler", 30.0, _fetch)


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_briefing_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter as a flat dict. Tolerant — never raises."""
    out: dict = {}
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            head = f.read(4096)
    except OSError:
        return out
    m = _FRONTMATTER_RE.match(head)
    if not m:
        return out
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def probe_briefings() -> dict:
    """List briefings + extract today's metadata."""
    out = {"path": str(BRIEFINGS_PATH), "available": False, "list": []}
    try:
        if not BRIEFINGS_PATH.exists():
            return out
        files = sorted(
            (p for p in BRIEFINGS_PATH.iterdir() if p.suffix == ".md"),
            reverse=True,
        )
    except OSError as e:
        out["error"] = str(e)
        return out
    out["available"] = True
    today = dt.date.today().isoformat()
    items = []
    for p in files[:30]:
        meta = _parse_briefing_frontmatter(p)
        try:
            size_kb = round(p.stat().st_size / 1024, 1)
            mtime = dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")
        except OSError:
            size_kb, mtime = 0, ""
        items.append({
            "date": p.stem,
            "size_kb": size_kb,
            "mtime": mtime,
            "tokens": int(meta.get("tokens_generated", "0") or 0),
            "throughput": float(meta.get("throughput_tok_per_s", "0") or 0),
            "sources_total": int(meta.get("sources_total", "0") or 0),
            "web_access": meta.get("web_access", "") == "true",
            "is_today": p.stem == today,
        })
    out["list"] = items
    out["today_exists"] = any(it["is_today"] for it in items)
    return out


def probe_ollama_log_tail(n: int = 12) -> dict:
    """Tail the Ollama server.log — useful for spotting silent tenants."""
    if not OLLAMA_LOG_PATH.exists():
        return {"ok": False, "path": str(OLLAMA_LOG_PATH)}
    try:
        # Read last ~16 KB (Ollama lines are short, this gets >> n lines).
        with OLLAMA_LOG_PATH.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 16384), os.SEEK_SET)
            tail = f.read().decode("utf-8", errors="replace")
        lines = [ln for ln in tail.splitlines() if ln.strip()]
        # Filter out the noisy /api/tags health pings — they crowd out signal.
        signal = [ln for ln in lines if not (
            "/api/tags" in ln or 'HEAD     "/"' in ln
        )]
        return {"ok": True, "lines": signal[-n:]}
    except OSError as e:
        return {"ok": False, "error": str(e)}


def probe_scheduler_logs() -> dict:
    """Most recent dashboard wrapper log (briefing run trail)."""
    if not SCHEDULER_LOG_DIR.exists():
        return {"ok": False, "path": str(SCHEDULER_LOG_DIR)}
    try:
        logs = sorted(SCHEDULER_LOG_DIR.glob("briefing-*.log"), reverse=True)
        if not logs:
            return {"ok": True, "logs": []}
        latest = logs[0]
        with latest.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        return {
            "ok": True,
            "latest_path": str(latest),
            "latest_mtime": dt.datetime.fromtimestamp(latest.stat().st_mtime).isoformat(timespec="seconds"),
            "latest_tail": lines[-10:],
            "log_count": len(logs),
        }
    except OSError as e:
        return {"ok": False, "error": str(e)}


# ---- Snapshot builder -------------------------------------------------------

def build_snapshot() -> dict:
    """Run all probes in parallel and return the combined JSON snapshot."""
    probes = {
        "ollama":          probe_ollama,
        "paperclip":       probe_paperclip,
        "deerflow":        probe_deerflow,
        "n8n":             probe_n8n,
        "gpu":             probe_gpu,
        "task_scheduler":  probe_task_scheduler,
        "briefings":       probe_briefings,
        "ollama_log":      probe_ollama_log_tail,
        "scheduler_logs":  probe_scheduler_logs,
    }
    results: dict = {}
    with ThreadPoolExecutor(max_workers=len(probes)) as ex:
        futures = {ex.submit(fn): name for name, fn in probes.items()}
        for fut in futures:
            name = futures[fut]
            try:
                results[name] = fut.result(timeout=10)
            except Exception as e:
                results[name] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        **results,
    }


# ---- HTTP server ------------------------------------------------------------

class DashboardHandler(BaseHTTPRequestHandler):
    # Silence default request logging — we don't need it spamming stderr.
    def log_message(self, fmt: str, *args) -> None:  # noqa: D401, N802
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/" or self.path == "/index.html":
            self._serve_file(HERE / "dashboard.html", "text/html; charset=utf-8")
            return
        if self.path == "/api/snapshot":
            self._serve_json(build_snapshot())
            return
        if self.path.startswith("/api/briefing/"):
            date = self.path[len("/api/briefing/"):]
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                self._serve_text("invalid date", 400)
                return
            path = BRIEFINGS_PATH / f"{date}.md"
            if not path.exists():
                self._serve_text("not found", 404)
                return
            try:
                self._serve_file(path, "text/markdown; charset=utf-8")
            except OSError as e:
                self._serve_text(f"read error: {e}", 500)
            return
        self._serve_text("not found", 404)

    def _serve_file(self, path: Path, content_type: str) -> None:
        try:
            data = path.read_bytes()
        except OSError as e:
            self._serve_text(f"read error: {e}", 500)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _serve_json(self, obj: object) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_text(self, msg: str, status: int = 200) -> None:
        body = msg.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    # Force stdout/stderr to UTF-8 so the startup banner survives non-ASCII
    # characters even when the Windows console codepage is cp1252.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(f"Henko Mission Control v0.1 - listening on http://{LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    print(f"  python:     {sys.executable}", flush=True)
    # Startup probe: warn loudly if log paths are inaccessible so the user
    # knows to switch Python before pinning the dashboard open.
    for label, p, kind in [
        ("Ollama log",      OLLAMA_LOG_PATH,   "file"),
        ("Wrapper logs",    SCHEDULER_LOG_DIR, "dir"),
        ("Briefings (WSL)", BRIEFINGS_PATH,    "dir"),
    ]:
        ok = p.is_file() if kind == "file" else p.is_dir()
        marker = "[OK]" if ok else "[--]"
        print(f"  {marker} {label:18s} {p}", flush=True)
        if not ok and "WindowsApps" in sys.executable:
            print("    -> Microsoft Store Python sandboxes %LOCALAPPDATA%. "
                  "Re-launch via infrastructure\\scripts\\start-dashboard.ps1.", flush=True)
    print(f"  dashboard:  http://{LISTEN_HOST}:{LISTEN_PORT}/", flush=True)
    print(f"  snapshot:   http://{LISTEN_HOST}:{LISTEN_PORT}/api/snapshot", flush=True)
    print("  Ctrl+C to stop.", flush=True)
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping...", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
