"""ElevenLabs narrator for Bouriko (its own account, voice 6OzrBCQf8cjERkYgzSg8).

Approach copied (not imported) from MoneyPrinterTurbo kindled_iron/elevenlabs_tts.py:
- the key comes ONLY from the environment (BOURIKO_ELEVENLABS_API_KEY, else ELEVENLABS_API_KEY,
  which in this repo is the Bouriko account's secret). It is never printed, written to disk or put
  in an error message. A missing key is a normal state: the caller falls back to Kokoro.
- ONE request for the whole script (consistent tone), voice settings sent per request, the voice in
  the account is never edited. Only the TTS endpoint and the subscription GET are called.

Bouriko additions:
- tagged tts_text per line ([tags], "...", "—"; no SSML <break>). Tags are spoken direction only:
  they are stripped from captions and word timings.
- /with-timestamps character alignment -> real word timings, and the single take is cut back into
  per-line WAVs at the silence between lines.
- audio + alignment cached by a hash of (model, voice, settings, text): a re-run costs 0 credits.
- credit guard: the balance is read before every paid request; too low = skip + ntfy alert.
"""
from __future__ import annotations

import base64
import difflib
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.elevenlabs.io/v1"
TAG_RE = re.compile(r"\[[^\]]*\]")
WORD_RE = re.compile(r"\S+")


class SkipElevenLabs(Exception):
    """Normal fallback reason (no key, low credits, ...). Message is safe to log."""


def key() -> str | None:
    for name in ("BOURIKO_ELEVENLABS_API_KEY", "ELEVENLABS_API_KEY"):
        k = os.environ.get(name, "").strip()
        if k:
            return k
    return None


def key_name() -> str | None:
    for name in ("BOURIKO_ELEVENLABS_API_KEY", "ELEVENLABS_API_KEY"):
        if os.environ.get(name, "").strip():
            return name
    return None


def _request(path: str, body: dict | None = None, timeout: int = 30) -> dict:
    headers = {"xi-api-key": key() or "", "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(API + path, data=data, headers=headers,
                                 method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _http_detail(e: urllib.error.HTTPError) -> str:
    """Status + ElevenLabs' own message (it never contains the key) so plan limits are readable."""
    try:
        detail = json.loads(e.read().decode()).get("detail", {})
        if isinstance(detail, dict):
            status = str(detail.get("status") or detail.get("code") or "")
            msg = str(detail.get("message") or "")
            return f"{status}: {msg}"[:220] if msg else status[:80]
        return str(detail)[:220]
    except Exception:  # noqa: BLE001
        return ""


def balance() -> dict:
    """Characters/credits left this period. {'error': ...} if the key can't read it."""
    try:
        sub = _request("/user/subscription")
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code} {_http_detail(e)}".strip()}
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}
    used = int(sub.get("character_count", 0))
    limit = int(sub.get("character_limit", 0))
    return {"used": used, "limit": limit, "remaining": max(0, limit - used),
            "resets_unix": sub.get("next_character_count_reset_unix"),
            "tier": sub.get("tier")}


def voice_info(voice_id: str) -> dict:
    """Name/category of the voice, so the log proves which voice was used (/v2/voices, v1 fallback)."""
    try:
        data = _request(f"/v2/voices?voice_ids={voice_id}&page_size=1")
        for v in data.get("voices", []):
            if v.get("voice_id") == voice_id:
                return {"name": v.get("name"), "category": v.get("category"), "source": "/v2/voices"}
    except Exception as e:  # noqa: BLE001
        first = type(e).__name__
    else:
        first = "not listed"
    try:
        v = _request(f"/v1/voices/{voice_id}")
        return {"name": v.get("name"), "category": v.get("category"), "source": f"/v1/voices ({first} on /v2)"}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code} {_http_detail(e)}".strip()}
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}


def strip_tags(text: str) -> str:
    """Caption text from a tagged tts_text: no [tags], normal spacing."""
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", text)).strip()


def _norm(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def build_script(lines: list[dict]) -> tuple[str, list[tuple[int, int]]]:
    """Join every line's tts_text into one request text; return it + each line's char span."""
    parts, spans, pos = [], [], 0
    for line in lines:
        t = (line.get("tts_text") or line.get("text") or "").strip()
        t = re.sub(r"<break[^>]*>", " ", t)  # never send SSML breaks
        if parts:
            parts.append(" ")
            pos += 1
        spans.append((pos, pos + len(t)))
        parts.append(t)
        pos += len(t)
    return "".join(parts), spans


def cache_key(text: str, cfg: dict, model: str) -> str:
    blob = json.dumps({"text": text, "model": model, "voice": cfg.get("voice_id"),
                       "settings": cfg.get("voice_settings", {}),
                       "format": cfg.get("output_format", "mp3_44100_128")}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _tts(text: str, cfg: dict, model: str) -> dict:
    body = {"text": text, "model_id": model, "voice_settings": dict(cfg.get("voice_settings", {}))}
    fmt = cfg.get("output_format", "mp3_44100_128")
    try:
        return _request(f"/text-to-speech/{cfg['voice_id']}/with-timestamps?output_format={fmt}",
                        body, timeout=300)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs HTTP {e.code} {_http_detail(e)}".strip()) from None


def _char_times(sent: str, alignment: dict) -> list[tuple[float, float] | None]:
    """Map every character of the sent text to (start, end) seconds using the returned alignment.
    The alignment string may differ slightly from what we sent (normalisation, tags), so the two
    strings are matched instead of trusting indices."""
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    got = "".join(chars)
    times: list[tuple[float, float] | None] = [None] * len(sent)
    sm = difflib.SequenceMatcher(None, sent, got, autojunk=False)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            times[a + k] = (float(starts[b + k]), float(ends[b + k]))
    return times


def _word_spans(text: str, offset: int) -> list[tuple[str, int, int]]:
    """Spoken words of a tagged line with their char span in the full request text (tags skipped)."""
    out = []
    masked = TAG_RE.sub(lambda m: " " * len(m.group(0)), text)
    for m in WORD_RE.finditer(masked):
        out.append((m.group(0), offset + m.start(), offset + m.end()))
    return out


def line_timings(lines, sent, spans, times, total):
    """Per line: caption words with absolute times, and the line's [start, end] in the take."""
    result = []
    for line, (a, b) in zip(lines, spans):
        spoken = _word_spans(sent[a:b], a)
        timed = []
        for w, s, e in spoken:
            ts = [t for t in times[s:e] if t]
            timed.append((w, ts[0][0], ts[-1][1]) if ts else (w, None, None))
        # fill gaps by interpolation
        known = [i for i, x in enumerate(timed) if x[1] is not None]
        if not known:
            raise RuntimeError("alignment did not cover a line")
        for i, (w, s, e) in enumerate(timed):
            if s is None:
                prev = max([k for k in known if k < i], default=known[0])
                nxt = min([k for k in known if k > i], default=known[-1])
                s = timed[prev][2] if prev < i else timed[nxt][1]
                e = timed[nxt][1] if nxt > i else s + 0.2
                timed[i] = (w, s, max(s + 0.05, e))
        # map spoken (tts) words to caption words
        caption = WORD_RE.findall(line.get("text") or strip_tags(sent[a:b]))
        sm = difflib.SequenceMatcher(None, [_norm(x[0]) for x in timed], [_norm(x) for x in caption],
                                     autojunk=False)
        cap_times: list[tuple[float, float] | None] = [None] * len(caption)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    cap_times[j1 + k] = (timed[i1 + k][1], timed[i1 + k][2])
            elif j2 > j1 and i2 > i1:  # replaced words share the span
                s0, e0 = timed[i1][1], timed[i2 - 1][2]
                step = (e0 - s0) / (j2 - j1)
                for k in range(j2 - j1):
                    cap_times[j1 + k] = (s0 + k * step, s0 + (k + 1) * step)
        line_start, line_end = timed[0][1], timed[-1][2]
        for i, t in enumerate(cap_times):
            if t is None:
                prev = next((cap_times[k] for k in range(i - 1, -1, -1) if cap_times[k]), None)
                s = prev[1] if prev else line_start
                cap_times[i] = (s, s + 0.15)
        result.append({"start": line_start, "end": line_end,
                       "words": [{"word": w, "start": s, "end": e} for w, (s, e) in zip(caption, cap_times)]})
    return result


def synthesize_story(lines: list[dict], out_dir: Path, cache_dir: Path, cfg: dict, log=print) -> dict:
    """Voice every line in one take. Writes out_dir/NN.wav per line. Returns a report with
    'words' (absolute, per caption word) and credit usage. Raises SkipElevenLabs to fall back."""
    if not key():
        raise SkipElevenLabs("no BOURIKO_ELEVENLABS_API_KEY / ELEVENLABS_API_KEY secret")
    if not cfg.get("voice_id"):
        raise SkipElevenLabs("no elevenlabs.voice_id in config.json")
    sent, spans = build_script(lines)
    models = [cfg.get("model_id", "eleven_v4")] + list(cfg.get("model_fallbacks", []))
    info = voice_info(cfg["voice_id"])
    if "error" in info:
        log(f"ElevenLabs: voice {cfg['voice_id']} lookup failed: {info['error']}")
    else:
        log(f"ElevenLabs: voice {cfg['voice_id']} = \"{info['name']}\" ({info.get('category')}, via {info['source']})")
    cache_dir.mkdir(parents=True, exist_ok=True)
    report = {"engine": "elevenlabs", "voice_id": cfg["voice_id"], "key_secret": key_name(),
              "voice_name": info.get("name"), "voice_category": info.get("category"),
              "chars": len(sent), "credits_used": 0, "cache_hit": False}

    data, model = None, None
    for m in models:
        h = cache_key(sent, cfg, m)
        cached = cache_dir / f"{h}.json"
        if cached.exists():
            data, model = json.loads(cached.read_text()), m
            report.update(cache_hit=True, cache_key=h)
            log(f"ElevenLabs: cache hit ({m}, {h[:12]}), 0 credits")
            break

    if data is None:
        before = balance()
        report["balance_before"] = before
        need = int(len(sent) * float(cfg.get("credit_multiplier", 1.0)))
        reserve = int(cfg.get("min_reserve_credits", 500))
        if "error" in before:
            log(f"ElevenLabs: balance unreadable ({before['error']}); give the key 'User: read' to enable the guard")
            if not cfg.get("allow_unverified_balance", True):
                raise SkipElevenLabs(f"balance unreadable ({before['error']})")
        elif before["remaining"] < need + reserve:
            raise SkipElevenLabs(f"credits too low: {before['remaining']} left, render needs ~{need} + {reserve} reserve")
        else:
            log(f"ElevenLabs: {before['remaining']} credits left, this render needs ~{need}")
        last = None
        for m in models:
            try:
                log(f"ElevenLabs: requesting {len(sent)} chars with model {m}")
                data, model = _tts(sent, cfg, m), m
                break
            except RuntimeError as e:
                last = e
                log(f"ElevenLabs: {m} failed: {e}")
                # invalid model, or a model the plan doesn't include (402) -> try the next one;
                # auth / quota / rate errors -> stop
                if not re.search(r"HTTP (400|402|404|422)", str(e)):
                    break
        if data is None:
            raise SkipElevenLabs(str(last) if last else "no audio returned")
        h = cache_key(sent, cfg, model)
        (cache_dir / f"{h}.json").write_text(json.dumps(data))
        report["cache_key"] = h
        after = balance()
        report["balance_after"] = after
        if "error" not in before and "error" not in after:
            report["credits_used"] = before["remaining"] - after["remaining"]
        else:
            report["credits_used_estimate"] = need
        log(f"ElevenLabs: credits used this render: {report.get('credits_used') or report.get('credits_used_estimate')}")

    report["model"] = model
    out_dir.mkdir(parents=True, exist_ok=True)
    mp3 = out_dir / "elevenlabs_take.mp3"
    mp3.write_bytes(base64.b64decode(data["audio_base64"]))
    full = out_dir / "elevenlabs_take.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ac", "1", "-ar", "48000",
                    str(full)], check=True)
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "default=nw=1:nk=1", str(full)]).decode().strip())
    alignment = data.get("alignment") or data.get("normalized_alignment") or {}
    times = _char_times(sent, alignment)
    per_line = line_timings(lines, sent, spans, times, total)

    # Cut points: the middle of the silence between two lines, so concatenating the line WAVs
    # gives back the exact take.
    cuts = [0.0]
    for i in range(1, len(per_line)):
        cuts.append(round((per_line[i - 1]["end"] + per_line[i]["start"]) / 2, 3))
    cuts.append(total)
    words = []
    for i, line in enumerate(per_line):
        a, b = cuts[i], cuts[i + 1]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(full), "-ss", f"{a:.3f}",
                        "-to", f"{b:.3f}", "-c:a", "pcm_s16le", str(out_dir / f"{i:02}.wav")], check=True)
        for w in line["words"]:
            words.append({"word": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3), "line": i})
    report["words"] = words
    report["line_cuts"] = cuts
    return report
