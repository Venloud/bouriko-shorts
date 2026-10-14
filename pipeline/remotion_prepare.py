"""Turn story + narration + media into Remotion props: timed beats, captions, SFX, mastered voice.

Rules enforced here (and re-checked in qa.py):
- a new visual every 2-4 s (visual_rules.beat_min/max_seconds), never the same shot twice in a row
- footage/photos are cropped to the evidence box; callouts are placed on that crop
- captions: 3-5 words, real word timings, spoken word highlighted (Remotion side)
- narration mastered to audio.voice_lufs (-17 LUFS), stereo 48 kHz; SFX 20 dB under the voice,
  trimmed to the silence they sit in, max audio.max_sfx
"""
import json
import math
import re
import shutil
import subprocess
import wave
from pathlib import Path

from common import ROOT, CONFIG, log

REMOTION = ROOT / "remotion"
PUBLIC = REMOTION / "public"
GENERATED = PUBLIC / "generated"
VR = CONFIG.get("visual_rules", {})
AU = CONFIG.get("audio", {})
BEAT_MIN = float(VR.get("beat_min_seconds", 2.0))
BEAT_MAX = float(VR.get("beat_max_seconds", 4.0))
# Evidence box fills y 200-1250; captions sit under it; nothing in the bottom 300 px.
BOX = {"x": 120, "y": 200, "w": 840, "h": 1050}
BOXES = {
    "default": BOX,
    "portrait": {"x": 190, "y": 200, "w": 700, "h": 1050},
    "wide": {"x": 120, "y": 300, "w": 840, "h": 900},
}
TAG_RE = re.compile(r"\[[^\]]*\]")


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def wav_dur(path):
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / f.getframerate()


def media_dur(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", str(path)]).decode().strip()
    return float(out or 0)


def loudness(path):
    """Integrated loudness (LUFS) via ffmpeg's ebur128."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
    return float(m[-1]) if m else None


def mean_volume(path):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"mean_volume:\s+(-?[\d.]+) dB", p.stderr)
    return float(m.group(1)) if m else None


def master_narration(concat_list, out):
    """Two-pass loudnorm to the target (default -17 LUFS, TP -1.5), stereo 48 kHz."""
    target = float(AU.get("voice_lufs", -17))
    raw = out.with_name("narration_raw.wav")
    ff("-f", "concat", "-safe", "0", "-i", str(concat_list), "-ar", "48000", "-ac", "1", str(raw))
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(raw), "-af",
                        f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    if m:
        s = json.loads(m.group(0))
        af = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={s['input_i']}:measured_TP={s['input_tp']}:"
              f"measured_LRA={s['input_lra']}:measured_thresh={s['input_thresh']}:offset={s['target_offset']}:linear=true")
    else:
        af = f"loudnorm=I={target}:TP=-1.5:LRA=11"
    ff("-i", str(raw), "-af", af, "-ar", "48000", "-ac", "2", str(out))
    raw.unlink(missing_ok=True)
    return loudness(out)


# ---------------------------------------------------------------- beats
def word_time(words, idx, default):
    if not words:
        return default
    idx = max(0, min(len(words) - 1, int(idx)))
    return words[idx]["start"]


def cue_time(cue, words, beat_start, default=0.0):
    """A cue is a word index, {"word": n, "offset": s} or {"t": seconds-from-beat-start}."""
    if cue is None:
        return default
    if isinstance(cue, dict):
        if "t" in cue:
            return float(cue["t"])
        return max(0.0, word_time(words, cue.get("word", 0), beat_start) + float(cue.get("offset", 0)) - beat_start)
    return max(0.0, word_time(words, cue, beat_start) - beat_start)


def keyword_card(text):
    """Fallback visual: the line's key phrase drawn on (used when a line runs out of footage)."""
    stop = {"the", "a", "an", "and", "or", "to", "of", "it", "is", "that", "this", "your", "you", "in",
            "on", "can", "for", "with", "when", "then", "but", "so", "just", "be", "are", "its", "it's"}
    ws = [re.sub(r"[^A-Za-z0-9'%-]", "", w) for w in TAG_RE.sub(" ", text).split()]
    key = [w for w in ws if w and w.lower() not in stop][:3] or ws[:3]
    return {"name": "keyword", "params": {"text": " ".join(key).upper(), "size": 92}}


def auto_segments(ls, le, words):
    dur = le - ls
    n = max(1, math.ceil(dur / BEAT_MAX - 1e-6))
    while n > 1 and dur / n < BEAT_MIN:
        n -= 1
    cuts = [ls]
    for k in range(1, n):
        target = ls + dur * k / n
        cand = min((w["start"] for w in words), key=lambda s: abs(s - target), default=target) if words else target
        if cand - cuts[-1] < 1.0:
            cand = target
        cuts.append(cand)
    cuts.append(le)
    return list(zip(cuts[:-1], cuts[1:]))


def snap_to_chunk(t, chunk_starts, lo, hi, prev):
    """Move a scene cut onto the start of a caption chunk, so no caption phrase spans a cut."""
    cands = [c for c in chunk_starts if lo <= c < hi - 0.8 and c > prev + 0.8]
    if not cands:
        return t
    best = min(cands, key=lambda c: abs(c - t))
    return best if abs(best - t) <= 1.6 else t


def build_beats(story, line_starts, total, words_by_line, chunk_starts=()):
    resolved = story.get("resolved_assets", {})
    beats = []
    for i, line in enumerate(story["lines"]):
        ls = line_starts[i]
        le = line_starts[i + 1] if i + 1 < len(line_starts) else total
        words = words_by_line.get(i, [])
        plan_beats = [b for b in line.get("beats", []) if b.get("asset") or b.get("diagram")]
        if plan_beats:
            starts = []
            for k, b in enumerate(plan_beats):
                if k == 0:
                    starts.append(ls)
                    continue
                t = word_time(words, b.get("word", 0), ls) + float(b.get("offset", 0))
                starts.append(snap_to_chunk(t, chunk_starts, ls, le, starts[-1]))
            for k, b in enumerate(plan_beats):
                s, e = starts[k], (starts[k + 1] if k + 1 < len(starts) else le)
                beat = {"start": s, "end": e, "line": i, "plan": b}
                if b.get("asset"):
                    beat["asset"] = resolved[b["asset"]]
                    beat["asset_name"] = b["asset"]
                    if b.get("asset2") and b["asset2"] in resolved:  # two characters side by side
                        beat["asset2"] = resolved[b["asset2"]]
                        beat["asset_name"] += "+" + b["asset2"]
                else:
                    beat["diagram"] = b["diagram"]
                beats.append(beat)
            continue
        # automatic: this line's media first, then a second clip, then a keyword card
        visuals = []
        if line.get("media_asset"):
            visuals.append({**(line.get("media_source") or {}), "local_path": line["media_asset"],
                            "kind": (line.get("media_source") or {}).get("kind") or line.get("media_kind") or "image"})
        if line.get("media_asset_2"):
            visuals.append({**(line.get("media_source_2") or {}), "local_path": line["media_asset_2"],
                            "kind": line.get("media_kind_2") or "image"})
        segs = auto_segments(ls, le, words)
        cuts = [segs[0][0]]
        for s0, _ in segs[1:]:
            cuts.append(snap_to_chunk(s0, chunk_starts, ls, le, cuts[-1]))
        segs = list(zip(cuts, cuts[1:] + [le]))
        for k, (s, e) in enumerate(segs):
            beat = {"start": s, "end": e, "line": i, "plan": {}}
            if k < len(visuals) and (ROOT / visuals[k]["local_path"]).exists():
                v = dict(visuals[k])
                v["credit"] = v.get("credit") or credit(v)
                beat["asset"], beat["asset_name"] = v, v["local_path"]
            else:
                beat["diagram"] = keyword_card(" ".join(w["word"] for w in words if s - 0.05 <= w["start"] < e) or line["text"])
            beats.append(beat)
    # never the same shot twice in a row
    for a, b in zip(beats, beats[1:]):
        if b.get("asset_name") and a.get("asset_name") == b.get("asset_name") and "start" not in b["plan"]:
            b.pop("asset"), b.pop("asset_name")
            words = words_by_line.get(b["line"], [])
            b["diagram"] = keyword_card(" ".join(w["word"] for w in words if b["start"] - 0.05 <= w["start"] < b["end"]))
    return beats


def credit(rec):
    from visual_plan import credit_of
    return credit_of(rec)


def crop_image(src, dst, w, h, focus=(0.5, 0.5), fit="cover", zoom=1.0):
    from PIL import Image, ImageFilter, ImageEnhance
    im = Image.open(src).convert("RGB")
    if fit == "contain":
        scale = min(w / im.width, h / im.height)
        fg = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
        bg = im.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
        bg.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2))
        out = bg
    else:
        scale = max(w / im.width, h / im.height) * max(1.0, float(zoom))
        rs = im.resize((max(w, round(im.width * scale)), max(h, round(im.height * scale))), Image.LANCZOS)
        x = int((rs.width - w) * focus[0])
        y = int((rs.height - h) * focus[1])
        out = rs.crop((x, y, x + w, y + h))
    out.save(dst, quality=92)
    return out


def backdrop_from(im, dst):
    from PIL import ImageFilter, ImageEnhance
    small = im.resize((270, 480))
    small = small.filter(ImageFilter.GaussianBlur(14))
    ImageEnhance.Brightness(small).enhance(0.55).save(dst, quality=80)


def render_media(beats):
    """Crop every footage/photo beat to its box; cut video segments; make blurred backdrops."""
    from PIL import Image
    outdir = GENERATED / "beats"
    outdir.mkdir(parents=True, exist_ok=True)
    video_cursor = {}
    for n, beat in enumerate(beats):
        if "asset" not in beat:
            continue
        a, plan = beat["asset"], beat["plan"]
        box_spec = plan.get("box") or a.get("box") or "default"
        box = dict(BOXES.get(box_spec, BOX)) if isinstance(box_spec, str) else {**BOX, **box_spec}
        beat["box"] = box
        focus = tuple(plan.get("focus") or a.get("focus") or (0.5, 0.5))
        fit = plan.get("fit") or a.get("fit") or "cover"
        src = ROOT / a["local_path"]
        if a.get("kind") == "video":
            dur = beat["end"] - beat["start"] + 0.4
            length = media_dur(src) or dur
            start = float(plan.get("start", a.get("start", 0)) if "start" in plan or "start" in a else 0)
            if "start" not in plan:
                start = video_cursor.get(a["local_path"], start)
            if start + dur > length:
                start = max(0.0, length - dur) if length > dur else 0.0
            video_cursor[a["local_path"]] = start + dur
            dst = outdir / f"b{n:02}.mp4"
            vf = (f"scale={box['w']}:{box['h']}:force_original_aspect_ratio=increase,"
                  f"crop={box['w']}:{box['h']}:(iw-{box['w']})*{focus[0]}:(ih-{box['h']})*{focus[1]},fps=30,format=yuv420p")
            loop = ["-stream_loop", "-1"] if length < dur else []
            ff(*loop, "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{dur:.3f}", "-an", "-vf", vf,
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(dst))
            frame = outdir / f"b{n:02}_f.jpg"
            ff("-i", str(dst), "-frames:v", "1", str(frame))
            im = Image.open(frame).convert("RGB")
            beat["video_start"] = round(start, 3)
            kind = "video"
        elif "asset2" in beat:
            from PIL import Image as _I
            half = (box["w"] - 12) // 2
            left = crop_image(src, outdir / f"b{n:02}_l.jpg", half, box["h"], focus, fit, plan.get("zoom", 1.0))
            right = crop_image(ROOT / beat["asset2"]["local_path"], outdir / f"b{n:02}_r.jpg", half, box["h"],
                               tuple(plan.get("focus2") or (0.5, 0.5)), plan.get("fit2", "cover"), plan.get("zoom2", 1.0))
            im = _I.new("RGB", (box["w"], box["h"]), (255, 59, 107))
            im.paste(left, (0, 0))
            im.paste(right, (box["w"] - half, 0))
            dst = outdir / f"b{n:02}.jpg"
            im.save(dst, quality=92)
            kind = "image"
        else:
            dst = outdir / f"b{n:02}.jpg"
            im = crop_image(src, dst, box["w"], box["h"], focus, fit, plan.get("zoom", 1.0))
            kind = "image"
        bg = outdir / f"b{n:02}_bg.jpg"
        backdrop_from(im, bg)
        # red media frame = anime character art (handoff); references/stock keep the white frame
        third_party = bool(a.get("character")) or any(x in str(a.get("provider")) for x in ("anilist", "jikan", "local_vetted"))
        beat["media"] = {"src": str(dst.relative_to(PUBLIC)), "kind": kind, "fit": "cover",
                         "backdrop": str(bg.relative_to(PUBLIC)),
                         "credit": plan.get("credit", a.get("credit")),
                         # anime images get the red media frame (handoff), stock/photos the white one
                         "frame": "red" if third_party else "white"}


# ---------------------------------------------------------------- captions
def caption_chunks(words, total):
    """3-5 word chunks that never run across a sentence end. Each sentence is split into
    near-equal chunks; a 1-2 word sentence ("One.") joins its neighbour when that stays <= 5."""
    lo, hi = VR.get("caption_words", [3, 5])
    words = [{**w, "word": TAG_RE.sub("", w["word"]).strip()} for w in words]
    words = [w for w in words if w["word"]]
    sentences, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None or re.search(r"[.!?]['\"”]?$", w["word"]) or nxt.get("line") != w.get("line"):
            sentences.append(cur)
            cur = []
    chunks = []
    for sent in sentences:
        n = len(sent)
        if n < lo:
            if chunks and len(chunks[-1]) + n <= hi:
                chunks[-1] = chunks[-1] + sent
            else:
                chunks.append(list(sent))  # merged with the next sentence below if possible
            continue
        k = math.ceil(n / hi)
        size = n / k
        # prefer to cut after a comma near each equal split point
        cuts, start = [], 0
        for j in range(1, k):
            target = round(j * size)
            best = target
            for d in (0, -1, 1):
                t = target + d
                if lo <= t - start and n - t >= lo and re.search(r"[,;:—]$", sent[t - 1]["word"]):
                    best = t
                    break
            cuts.append(best)
            start = best
        bounds = [0, *cuts, n]
        if any(not (lo <= bounds[j + 1] - bounds[j] <= hi) for j in range(len(bounds) - 1)):
            bounds = [round(j * size) for j in range(k)] + [n]  # plain equal split
        chunks += [sent[bounds[j]:bounds[j + 1]] for j in range(len(bounds) - 1)]
    # a leftover short chunk joins the following one when that stays within the limit
    merged = []
    for c in chunks:
        if merged and len(merged[-1]) < lo and len(merged[-1]) + len(c) <= hi:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    chunks = merged
    out = []
    for n, c in enumerate(chunks):
        start = c[0]["start"] - 0.05
        nxt = chunks[n + 1][0]["start"] - 0.05 if n + 1 < len(chunks) else total
        end = nxt if nxt - c[-1]["end"] < 0.7 else c[-1]["end"] + 0.3
        out.append({"start": round(max(0, start), 3), "end": round(min(total, end), 3),
                    # a 1-2 word sentence ("Non-sorcerers, one.") is shown alone rather than glued to another
                    "whole_sentence": bool(re.search(r"[.!?]['\"”]?$", c[-1]["word"])) and len(c) < lo,
                    "words": [{"text": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3)} for w in c]})
    return out


# ---------------------------------------------------------------- sfx
def prepare_music(story, narration_out, total):
    """Light music bed, looped to length, ~22 dB under the voice and ducked further while he talks."""
    cfg = story.get("music") or {}
    if not cfg.get("enabled"):
        return None
    src = ROOT / cfg.get("file", "assets/music/investigations_kevin_macleod.mp3")
    if not src.exists():
        log(f"MUSIC: {src} missing, no bed")
        return None
    meta_path = src.with_name(src.name + ".json")
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    looped = GENERATED / "music_loop.wav"
    length = media_dur(src)
    reps = int(total // max(1.0, length - 2)) + 1
    # loop with a 2 s crossfade between repeats, then fade in/out
    inputs = []
    for _ in range(reps):
        inputs += ["-i", str(src)]
    chain = "[0:a]"
    filt = []
    for k in range(1, reps):
        filt.append(f"{chain}[{k}:a]acrossfade=d=2[a{k}]")
        chain = f"[a{k}]"
    filt.append(f"{chain}atrim=0:{total:.3f},afade=t=in:d=1.5,afade=t=out:st={max(0, total - 2.5):.3f}:d=2.5,aresample=48000,aformat=channel_layouts=stereo[m]")
    ff(*inputs, "-filter_complex", ";".join(filt), "-map", "[m]", str(looped))
    voice_mean = mean_volume(narration_out) or -24.0
    music_mean = mean_volume(looped) or -20.0
    gain = (voice_mean - float(cfg.get("below_voice_db", 22))) - music_mean
    out = GENERATED / "music.wav"
    # sidechain ducking: the narration pushes the bed down a further few dB while he speaks
    ff("-i", str(looped), "-i", str(narration_out), "-filter_complex",
       f"[0:a]volume={gain:.2f}dB[m];[1:a]apad,atrim=0:{total:.3f}[k];"
       f"[m][k]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=300[d]",
       "-map", "[d]", "-ar", "48000", "-ac", "2", str(out))
    looped.unlink(missing_ok=True)
    log(f"MUSIC: {src.name} bed at {gain:.1f} dB gain (~{cfg.get('below_voice_db', 22)} dB under the voice), ducked")
    return {"file": str(out.relative_to(PUBLIC)), "source": str(src.relative_to(ROOT)), "credit": meta.get("credit"),
            "license": meta.get("license"), "gain_db": round(gain, 2)}


def prepare_sfx(narration_out, max_sfx=None):
    path = ROOT / "output/sfx_events.json"
    if not path.exists():
        return []
    voice_mean = mean_volume(narration_out) or -24.0
    below = float(AU.get("sfx_below_voice_db", 20))
    outdir = GENERATED / "sfx"
    outdir.mkdir(parents=True, exist_ok=True)
    events = []
    for n, e in enumerate(json.loads(path.read_text())[: int(max_sfx or AU.get("max_sfx", 8))]):
        src = ROOT / e["file"]
        if not src.exists():
            continue
        length = max(0.12, float(e.get("max_len", 0.6)))
        fade = min(0.08, length / 3)
        trimmed = outdir / f"e{n:02}_raw.wav"
        ff("-i", str(src), "-t", f"{length:.3f}", "-af", f"afade=t=out:st={length - fade:.3f}:d={fade:.3f}",
           "-ar", "48000", "-ac", "2", str(trimmed))
        sfx_mean = mean_volume(trimmed)
        gain = (voice_mean - below) - (sfx_mean if sfx_mean is not None else -20.0)
        dst = outdir / f"e{n:02}.wav"
        ff("-i", str(trimmed), "-af", f"volume={gain:.2f}dB", str(dst))
        trimmed.unlink(missing_ok=True)
        events.append({"time": e["time"], "file": str(dst.relative_to(PUBLIC)), "volume": 1,
                       "type": e.get("type"), "gain_db": round(gain, 2), "length": round(length, 3)})
    return events


def voice_envelope(wav_path, total, fps=30):
    """0-1 loudness per video frame from the mastered narration (drives the voice orb)."""
    import numpy as np
    with wave.open(str(wav_path), "rb") as f:
        sr, ch, n = f.getframerate(), f.getnchannels(), f.getnframes()
        data = np.frombuffer(f.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    hop = sr / fps
    env = []
    for k in range(int(math.ceil(total * fps))):
        seg = data[int(k * hop): int((k + 1) * hop)]
        rms = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
        db = 20 * math.log10(rms + 1e-9)
        env.append(round(max(0.0, min(1.0, (db + 45) / 33)), 3))
    smooth = []
    for v in env:  # fast attack, slower release
        prev = smooth[-1] if smooth else 0.0
        smooth.append(round(v if v > prev else prev * 0.8 + v * 0.2, 3))
    return smooth


def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    if GENERATED.exists():
        shutil.rmtree(GENERATED)
    GENERATED.mkdir(parents=True, exist_ok=True)

    audio = ROOT / "output/audio"
    starts, concat, cursor = [], [], 0.0
    for i, _ in enumerate(story["lines"]):
        wav = audio / f"{i:02}.wav"
        if not wav.exists():
            raise RuntimeError(f"Missing narration audio: {wav}")
        starts.append(round(cursor, 4))
        concat.append(f"file '{wav.resolve().as_posix()}'")
        cursor += wav_dur(wav)
    audio_total = round(cursor, 4)
    # optional hold after the last word (JJK: pause on the final question so viewers can read it)
    total = round(audio_total + float(story.get("audio_tail_seconds", 0)), 4)
    concat_path = ROOT / "output/audio_concat.txt"
    concat_path.write_text("\n".join(concat) + "\n")
    narration = GENERATED / "narration.wav"
    lufs = master_narration(concat_path, narration)
    log(f"Narration mastered: {lufs} LUFS (target {AU.get('voice_lufs', -17)}), stereo 48 kHz")

    words = json.loads((ROOT / "output/word_timings.json").read_text())
    by_line = {}
    for w in words:
        by_line.setdefault(w.get("line", 0), []).append(w)

    captions = caption_chunks(words, total)
    chunk_starts = [c["start"] for c in captions]
    beats = build_beats(story, starts, total, by_line, chunk_starts)
    render_media(beats)
    props_beats = []
    for n, b in enumerate(beats):
        plan = b["plan"]
        words_i = by_line.get(b["line"], [])
        out = {"start": round(b["start"], 3), "end": round(b["end"], 3), "line": b["line"],
               "kind": "media" if "media" in b else ("orb" if plan.get("orb") else "diagram"),
               "tag": plan.get("tag"), "hold": bool(plan.get("hold"))}
        if "media" in b:
            out["media"] = b["media"]
            out["box"] = b["box"]
            # a re-framed crop of the same photo (different focus/box) counts as a new shot
            out["key"] = f"{b['asset_name']}@{b.get('video_start', 0)}|{plan.get('focus')}|{json.dumps(b['box'], sort_keys=True)}"
            out["source"] = {k: b["asset"].get(k) for k in ("provider", "title", "source_url", "license",
                                                             "creator", "sha256", "rights_status", "character")}
        else:
            d = dict(b["diagram"])
            d["steps"] = [round(cue_time(c, words_i, b["start"]), 3) for c in d.get("steps", [0])]
            out["diagram"] = d
            out["box"] = BOX if not plan.get("box") else (BOXES.get(plan["box"], BOX) if isinstance(plan["box"], str) else {**BOX, **plan["box"]})
            out["key"] = "diagram:" + d["name"] + ":" + json.dumps(d.get("params", {}), sort_keys=True)[:60] + f":{d.get('stage', '')}"
        ann = []
        for a in plan.get("annotations", []):
            a = dict(a)
            if "word" in a:
                a["at"] = round(cue_time(a.pop("word"), words_i, b["start"]) + float(a.pop("offset", 0)), 3)
            else:
                a["at"] = float(a.get("at", 0.0))
            ann.append(a)
        out["annotations"] = ann
        props_beats.append(out)

    sfx = prepare_sfx(narration, int(story.get("max_sfx", AU.get("max_sfx", 8))))

    def at(cue):  # (line, word index) -> seconds
        lw = by_line.get(cue["line"], [])
        return round(lw[max(0, min(len(lw) - 1, int(cue.get("word", 0))))]["start"], 3) if lw else 0.0

    effects = [{"type": e["type"], "time": at(e), "dur": e.get("dur", 0.8)} for e in story.get("effects", [])]
    reactions = [{"text": r["text"], "time": at(r), "dur": float(r.get("dur", 1.4))} for r in story.get("reactions", [])]
    music = prepare_music(story, narration, total)
    props = {"durationSeconds": total, "theme": story.get("theme", "tech"), "beats": props_beats,
             "captions": captions, "sfxEvents": sfx, "narration": "generated/narration.wav",
             "voiceEnv": voice_envelope(narration, total), "effects": effects, "reactions": reactions}
    if music:
        props.update(music=music["file"], musicVolume=1)
    (REMOTION / "props.json").write_text(json.dumps(props, indent=2))
    (ROOT / "output/beats.json").write_text(json.dumps({"beats": props_beats, "captions": captions, "sfx": sfx,
                                                        "effects": effects, "reactions": reactions, "music": music,
                                                        "narration_lufs": lufs, "line_starts": starts,
                                                        "audio_seconds": audio_total, "total_seconds": total}, indent=2))
    log(f"Remotion prepared: {len(props_beats)} beats, {len(captions)} caption chunks, {len(sfx)} SFX, {total:.2f}s")


if __name__ == "__main__":
    main()
