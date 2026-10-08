"""Opt-in JJK stream decode probe. Never uploads or publishes episode footage."""
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "http://127.0.0.1:3000"
OUT = Path("output/blitz_decode_results.json")
OUT.parent.mkdir(parents=True, exist_ok=True)
REPORT = {"provider": "animeparadise", "passed": False, "steps": {}}

def api(path, params=None):
    url = BASE + path + ("?" + urlencode(params) if params else "")
    with urlopen(url, timeout=35) as response:
        return json.loads(response.read(4_000_000))

def entries(obj, key):
    if isinstance(obj, list):
        return obj
    value = obj.get(key, []) if isinstance(obj, dict) else []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for nested in ("results", "items", "units", "episodes", "data"):
            if isinstance(value.get(nested), list):
                return value[nested]
    return []

def candidates(stream):
    payload = stream.get("stream", stream)
    if not isinstance(payload, dict):
        return []
    sources = payload.get("streams", [])
    if isinstance(sources, dict):
        sources = list(sources.values())
    found = []
    for item in sources if isinstance(sources, list) else []:
        if isinstance(item, str):
            found.append((item, {}))
        elif isinstance(item, dict):
            url = next((item.get(k) for k in ("url", "file", "src", "link") if isinstance(item.get(k), str)), None)
            if url:
                found.append((url, item.get("headers") or payload.get("headers") or {}))
    return found

try:
    for attempt in range(25):
        try:
            api("/health")
            break
        except Exception:
            if attempt == 24:
                raise
            time.sleep(2)
    search = api("/api/v1/search", {"q": "Jujutsu Kaisen", "provider": "animeparadise"})
    shows = entries(search, "results")
    show = next((s for s in shows if isinstance(s, dict) and "jujutsu" in str(s.get("title", s.get("name", ""))).lower()), None)
    if not show or not show.get("id"):
        raise RuntimeError("AnimeParadise JJK search returned no usable show")
    REPORT["steps"]["search"] = "passed"
    content = api("/api/v1/content", {"id": show["id"], "provider": "animeparadise"})
    episodes = entries(content, "units")
    ep = next((e for e in episodes if isinstance(e, dict) and e.get("id")), None)
    if not ep:
        raise RuntimeError("No episode ID returned")
    REPORT["steps"]["episodes"] = "passed"
    response = api("/api/v1/stream", {"id": ep["id"], "provider": "animeparadise", "language": "sub"})
    sources = candidates(response)
    REPORT["steps"]["stream_candidates"] = len(sources)
    if not sources:
        raise RuntimeError("Stream response has no usable URL")
    # Decode directly into the null muxer: no anime footage stored, published, or uploaded.
    # Limit to 3 seconds of decoded input and a 45-second wall-clock timeout.
    errors = []
    for i, (url, headers) in enumerate(sources[:4]):
        cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
               "-rw_timeout", "12000000"]
        if isinstance(headers, dict) and headers:
            safe_headers = {str(k): str(v) for k, v in headers.items() if isinstance(v, (str, int, float))}
            cmd += ["-headers", "".join(f"{k}: {v}\\r\\n" for k, v in safe_headers.items())]
        cmd += ["-i", url, "-t", "3", "-map", "0:v:0", "-f", "null", "-"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if p.returncode == 0:
                REPORT["passed"] = True
                REPORT["steps"]["decode"] = "passed"
                REPORT["steps"]["successful_candidate_index"] = i
                print("PASS: AnimeParadise JJK stream decoded by FFmpeg", flush=True)
                break
            errors.append(f"candidate {i}: ffmpeg exit {p.returncode}: {p.stderr[-450:]}")
        except subprocess.TimeoutExpired:
            errors.append(f"candidate {i}: ffmpeg timeout")
    if not REPORT["passed"]:
        raise RuntimeError("All tested sources failed decoding: " + " | ".join(errors))
except Exception as exc:
    REPORT["error"] = str(exc)[:3000]
    print("FAIL:", REPORT["error"], flush=True)
finally:
    # Intentionally do not record URLs or headers: they can be temporary or sensitive.
    OUT.write_text(json.dumps(REPORT, indent=2) + "\n")
if not REPORT["passed"]:
    raise SystemExit(1)
