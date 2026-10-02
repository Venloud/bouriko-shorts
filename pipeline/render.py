"""Media-first vertical explainer renderer.

The video is narration + real/free media + centered captions + occasional
simple explanatory graphics. The mascot is branding for the page, not a
required on-screen character.
"""
import json
import math
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import ROOT, CONFIG, run

W, H, FPS = 1080, 1920, 30
BG = CONFIG.get("style", {}).get("background", "#F4EFE4")
INK = CONFIG.get("style", {}).get("ink", "#1B1B1B")
BLUE = CONFIG.get("style", {}).get("tech_glow", "#2EA8FF")


def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
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
    f = font(58, True)
    lines = wrap(d, text, f, 900)
    line_h = 72
    block_h = len(lines) * line_h
    top = (H - block_h) // 2

    # Centered captions: readable over both bright photos and dark footage.
    shadow = 8
    for j, line in enumerate(lines):
        box = d.textbbox((0, 0), line, font=f)
        tw = box[2] - box[0]
        x = (W - tw) // 2
        y = top + j * line_h
        d.text((x + shadow, y + shadow), line, font=f, fill=(0, 0, 0, 190), stroke_width=5, stroke_fill=(0, 0, 0, 170))
        d.text((x, y), line, font=f, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 210))
    return im


def fallback_graphic(line):
    """Clean diagram fallback when no free/real media asset was found."""
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    title = str(line.get("visual") or "EXPLAINER").upper()
    d.text((60, 80), title, font=font(42, True), fill=INK)
    d.line((60, 145, 1020, 145), fill=INK, width=3)

    visual = str(line.get("visual", "")).lower()
    if "traffic" in visual:
        x, y = 180, 300
        d.rounded_rectangle((x, y, x + 180, y + 470), 30, fill="#D0CCC1", outline=INK, width=8)
        for i, col in enumerate(("#E64B4B", "#D8A72D", "#55A85A")):
            d.ellipse((x + 45, y + 45 + i * 130, x + 135, y + 135 + i * 130), fill=col, outline=INK, width=5)
        d.line((x + 90, y + 470, x + 90, 1100), fill=INK, width=8)
    elif "bicycle" in visual:
        d.ellipse((190, 600, 360, 770), outline=INK, width=10)
        d.ellipse((600, 600, 770, 770), outline=INK, width=10)
        d.line((275, 685, 480, 610), fill=INK, width=10)
        d.line((480, 610, 685, 685), fill=INK, width=10)
        d.ellipse((455, 675, 490, 710), fill=BLUE)
    elif "camera" in visual:
        d.rounded_rectangle((260, 480, 820, 820), 35, fill="#D0CCC1", outline=INK, width=8)
        d.ellipse((455, 565, 625, 735), fill=BLUE, outline=INK, width=6)
        d.line((540, 820, 540, 1080), fill=INK, width=8)
    else:
        d.rounded_rectangle((160, 520, 920, 950), 40, fill="#DDD8CC", outline=INK, width=8)
        d.text((245, 680), "VISUAL EXPLANATION", font=font(48, True), fill=INK)
    return im


def media_clip(asset_path, text, out, dur):
    """Turn a local image/video into a clean 9:16 captioned segment."""
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
        source = base
        args = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-loop", "1", "-i", str(source),
            "-loop", "1", "-i", str(overlay_path),
            "-t", f"{dur:.3f}",
            "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)
        ]
    else:
        args = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-stream_loop", "-1", "-i", str(asset_path),
            "-loop", "1", "-i", str(overlay_path),
            "-t", f"{dur:.3f}",
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];"
            "[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)
        ]
    run(args)


def graphic_clip(line, out, dur):
    graphic = fallback_graphic(line)
    overlay = caption_overlay(line["text"])
    graphic.alpha_composite(overlay)
    png = out.with_suffix(".png")
    graphic.save(png)
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png),
        "-t", f"{dur:.3f}", "-vf", "format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)
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
        if asset:
            media_path = ROOT / asset
            if media_path.exists():
                media_clip(media_path, line["text"], out, dur)
            else:
                graphic_clip(line, out, dur)
        else:
            graphic_clip(line, out, dur)

        # Short fade at the boundaries, but no camera movement or pose animation.
        faded = render_dir / f"{i:02}_faded.mp4"
        fade = min(0.12, max(0.04, dur / 8))
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(out),
            "-vf", f"fade=t=in:st=0:d={fade:.3f},fade=t=out:st={max(0,dur-fade):.3f}:d={fade:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(faded)
        ])
        clips.append(faded)

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
