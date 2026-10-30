"""Local web UI for the HomeTownTalks pipeline (stdlib only, no Flask needed).

Run:   python3 app.py
Open:  http://localhost:8711

Endpoints:
  GET  /                 -> dashboard (web/index.html)
  POST /api/run          -> start a pipeline run (background thread)
  GET  /api/status       -> current run status + live log
  GET  /api/leads        -> latest results (outputs/latest.json)
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import config
import pipeline

ROOT = Path(__file__).parent
WEB = ROOT / "web"
# Render (and most hosts) inject $PORT; fall back to 8711 for local use.
PORT = int(os.environ.get("PORT", "8711"))
HOST = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"

# single-run state (local single-user tool)
JOB = {"running": False, "log": [], "done": False, "error": None, "stats": None}
_LOCK = threading.Lock()


def _log(msg: str):
    JOB["log"].append(str(msg))


def _run(params: dict):
    JOB.update(running=True, log=[], done=False, error=None, stats=None)
    try:
        res = pipeline.run_pipeline(
            sources=tuple(params.get("sources", ["x", "linkedin"])),
            max_items=int(params.get("max_items", config.MAX_TWEETS)),
            lookback_days=int(params.get("lookback_days", config.LOOKBACK_DAYS)),
            queries_limit=params.get("queries_limit") or None,
            city_booster=bool(params.get("city_booster", False)),
            enable_enrichment=bool(params.get("enable_enrichment", True)),
            model=params.get("model") or None,
            progress=_log,
        )
        JOB["stats"] = res["stats"]
    except Exception as e:  # noqa: BLE001
        JOB["error"] = str(e)
        _log(f"ERROR: {e}")
    finally:
        JOB.update(running=False, done=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = (WEB / "index.html").read_text(encoding="utf-8")
            return self._send(200, html, "text/html; charset=utf-8")
        if self.path == "/api/status":
            return self._send(200, json.dumps(JOB))
        if self.path == "/api/leads":
            f = config.OUTPUT_DIR / "latest.json"
            if f.exists():
                return self._send(200, f.read_text(encoding="utf-8"))
            return self._send(200, json.dumps({"x": [], "linkedin": [], "combined": [], "stats": {}}))
        if self.path == "/api/config":
            return self._send(200, json.dumps({
                "has_apify": bool(config.APIFY_TOKEN),
                "has_openrouter": bool(config.OPENROUTER_API_KEY),
                "model": config.OPENROUTER_MODEL,
                "defaults": {"max_items": config.MAX_TWEETS, "lookback_days": config.LOOKBACK_DAYS},
            }))
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/run":
            return self._send(404, json.dumps({"error": "not found"}))
        length = int(self.headers.get("Content-Length", 0))
        try:
            params = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            params = {}
        with _LOCK:
            if JOB["running"]:
                return self._send(409, json.dumps({"error": "a run is already in progress"}))
            threading.Thread(target=_run, args=(params,), daemon=True).start()
        return self._send(202, json.dumps({"ok": True}))


def main():
    where = "localhost" if HOST == "127.0.0.1" else HOST
    print(f"HomeTownTalks UI -> http://{where}:{PORT}")
    print(f"  Apify key: {'set' if config.APIFY_TOKEN else 'MISSING'} | "
          f"OpenRouter key: {'set' if config.OPENROUTER_API_KEY else 'MISSING'}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
