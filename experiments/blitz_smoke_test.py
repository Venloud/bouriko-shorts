"""Real Blitz API integration smoke test. No episode video downloaded."""
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "http://127.0.0.1:3000"
RESULTS = {"checks": {}, "search_title": "Jujutsu Kaisen", "passed": False}
OUT = Path("output/blitz_smoke_results.json")
OUT.parent.mkdir(exist_ok=True)

def request(path, params=None, timeout=35):
    url = BASE + path + ("?" + urlencode(params) if params else "")
    with urlopen(url, timeout=timeout) as r:
        data = r.read(4_000_000)
        return json.loads(data)

def check(name, path, params=None):
    data = request(path, params)
    RESULTS["checks"][name] = {"ok": True, "response_keys": list(data)[:12] if isinstance(data, dict) else []}
    return data

def entries(d, *keys):
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for key in keys:
            v = d.get(key)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                for nested in ("results", "items", "units", "episodes", "data"):
                    if isinstance(v.get(nested), list):
                        return v[nested]
    return []

try:
    for attempt in range(35):
        try:
            check("health", "/health")
            break
        except Exception:
            if attempt == 34:
                raise
            time.sleep(2)
    providers = check("providers", "/api/v1/providers")
    print("Providers response type:", type(providers).__name__, flush=True)
    search = check("search", "/api/v1/search", {"q": "Jujutsu Kaisen", "provider": "allmanga"})
    matches = entries(search, "results", "data", "items")
    if not matches:
        raise RuntimeError("Blitz returned no JJK results on allmanga")
    anime = next((x for x in matches if isinstance(x, dict) and "jujutsu" in str(x.get("title", x.get("name", ""))).lower()), matches[0])
    if not isinstance(anime, dict) or not anime.get("id"):
        raise RuntimeError("Search returned no usable anime ID")
    RESULTS["anime"] = {"id": anime["id"], "title": anime.get("title", anime.get("name"))}
    content = check("content", "/api/v1/content", {"id": anime["id"]})
    units = entries(content, "units", "episodes", "results", "data")
    if not units:
        raise RuntimeError("Blitz returned no episode units")
    unit = next((x for x in units if isinstance(x, dict) and x.get("id")), None)
    if unit is None:
        raise RuntimeError("Episode units had no IDs")
    RESULTS["episode_id"] = unit["id"]
    stream = check("stream", "/api/v1/stream", {"id": unit["id"], "language": "sub"})
    RESULTS["stream_response_type"] = type(stream).__name__
    RESULTS["passed"] = True
    print("PASS: Blitz health, providers, JJK search, episode listing, stream endpoint", flush=True)
except Exception as exc:
    RESULTS["error"] = str(exc)
    print("FAIL:", exc, flush=True)
finally:
    OUT.write_text(json.dumps(RESULTS, indent=2))
if not RESULTS["passed"]:
    raise SystemExit(1)
