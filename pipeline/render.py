"""Modern media-first vertical explainer renderer."""
import json
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import ROOT, CONFIG, run

W, H, FPS = 1080, 1920, 30
ACCENT = CONFIG.get("style", {}).get("tech_glow", "#2EA8FF")


def font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/lato/Lato-Black.ttf" if bold else "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def caption_overlay(text):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(62, True)
    lines = wrap(d, text, f, 900)
    line_h = 76
    block_h = len(lines) * line_h
    top = int(H * 0.46 - block_h / 2)

    pad_x, pad_y = 34, 24
    widths = [d.textbbox((0, 0), x, font=f)[2] for x in lines]
    bw = min(980, max(widths) + pad_x * 2)
    bh = block_h + pad_y * 2
    bx = (W - bw) // 2
    by = max(250, min(H - bh - 250, top - pad_y))
    d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=26, fill=(0, 0, 0, 145))

    for j, line in enumerate(lines):
        box = d.textbbox((0, 0), line, font=f)
        tw = box[2] - box[0]
        x = (W - tw) // 2
        y = top + j * line_h
        d.text((x, y), line, font=f, fill=(255, 255, 255, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 220))
    return im


def fallback_graphic(line):
    # Safety fallback only. Normal builds should be media-first.
    im = Image.new("RGB", (W, H), "#171717")
    d = ImageDraw.Draw(im)
    title = str(line.get("visual") or "EXPLAINER").upper()
    d.text((60, 80), title, font=font(40, True), fill="white")
    d.line((60, 145, 1020, 145), fill=ACCENT, width=4)
    d.text((60, 1680), "MEDIA NOT FOUND", font=font(38, True), fill=ACCENT)
    return im


def media_clip(asset_path, text, out, dur):
    overlay = caption_overlay(text)
    overlay_path = out.with_suffix(".caption.png")
    overlay.save(overlay_path)

    if asset_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
        base = out.with_suffix(".base.png")
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(asset_path),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
            "-frames:v", "1", str(base)
        ])
        args = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-loop", "1", "-i", str(base),
            "-loop", "1", "-i", str(overlay_path),
            "-t", f"{dur:.3f}",
            "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", str(out)
        ]
    else:
        # Hard cuts between scenes. No fade-to-black and no artificial slide-show pauses.
        args = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-stream_loop", "-1", "-i", str(asset_path),
            "-loop", "1", "-i", str(overlay_path),
            "-t", f"{dur:.3f}",
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];"
            "[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-pix_fmt", "yuv420p", str(out)
        ]
    run(args)


def graphic_clip(line, out, dur):
    graphic = fallback_graphic(line).convert("RGBA")
    graphic.alpha_composite(caption_overlay(line["text"]))
    png = out.with_suffix(".png")
    graphic.save(png)
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png),
        "-t", f"{dur:.3f}", "-vf", "format=yuv420p", "-c:v", "libx264",
        "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)
    ])


def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    audio_dir = ROOT / "output/audio"
    render_dir = ROOT / "output/render"
    render_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    for i, line in enumerate(story.get("lines", [])):
        wav = audio_dir / f"{i:02}.wav"
        if not wav.exists():
            raise RuntimeError(f"Missing narration audio: {wav}")
        with wave.open(str(wav), "rb") as f:
            dur = f.getnframes() / f.getframerate()

        out = render_dir / f"{i:02}.mp4"
        asset = line.get("media_asset")
        if asset and (ROOT / asset).exists():
            media_clip(ROOT / asset, line["text"], out, dur)
        else:
            graphic_clip(line, out, dur)
        clips.append(out)

    concat = render_dir / "concat.txt"
    concat.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips))
    silent = ROOT / "output/silent.mp4"
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat), "-c", "copy", str(silent)
    ])

    audio_concat = ROOT / "output/audio_all.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(ROOT / "output/audio_concat.txt"), "-ar", "24000", "-ac", "1",
        str(audio_concat)
    ])

    final = ROOT / "output/bouriko.mp4"
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(silent), "-i", str(audio_concat),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)
    ])
    print(f"Rendered {final}")


if __name__ == "__main__":
    main()
