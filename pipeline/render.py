"""Bouriko cutout compositor: pose changes, sketch diagrams, captions and Rock Phone."""
import json, math, subprocess, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from common import ROOT, CONFIG, run
from broll import load_action, resolve_source, prepare_vertical

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

def draw_rock_phone(draw, speaking):
    # Generic rock phone; no brand/logo.
    x, y, w, h = 745, 430, 230, 390
    if speaking:
        for pad in (14, 24, 34):
            draw.rounded_rectangle((x-pad, y-pad, x+w+pad, y+h+pad), 35+pad//2, outline=BLUE, width=4)
    draw.rounded_rectangle((x, y, x+w, y+h), 35, fill="#8C8C82", outline=INK, width=7)
    draw.ellipse((x+88, y+42, x+142, y+96), fill=BLUE, outline=INK, width=4)
    for row in range(3):
        for col in range(3):
            cx = x+48+col*66
            cy = y+145+row*66
            draw.rounded_rectangle((cx, cy, cx+38, cy+38), 9, fill=BLUE, outline=INK, width=3)
    draw.arc((x+55, y+335, x+175, y+375), 0, 180, fill=INK, width=5)

def draw_traffic_visual(draw, visual, line_no):
    cx, cy = 250, 470
    # Minimal hand-drawn traffic signal.
    draw.rounded_rectangle((cx, cy, cx+145, cy+390), 24, fill="#D0CCC1", outline=INK, width=7)
    for i, col in enumerate(("#E64B4B", "#D8A72D", "#55A85A")):
        yy = cy+35+i*110
        draw.ellipse((cx+35, yy, cx+110, yy+75), fill=col, outline=INK, width=5)
    if "loop" in visual or "wire" in visual or "car" in visual or "road" in visual:
        y = 980
        draw.rectangle((90, y, 700, y+260), fill="#77736B", outline=INK, width=6)
        draw.rectangle((120, y+55, 670, y+205), outline="#DDD8CC", width=4)
        draw.ellipse((245, y+78, 545, y+182), outline=BLUE, width=7)
        draw.text((115, y+215), "INDUCTIVE LOOP", font=font(28, True), fill=INK)
    elif "bicycle" in visual:
        draw.ellipse((175, 980, 305, 1110), outline=INK, width=8)
        draw.ellipse((470, 980, 600, 1110), outline=INK, width=8)
        draw.line((240,1045,390,995), fill=INK, width=7)
        draw.line((390,995,535,1045), fill=INK, width=7)
        draw.line((390,995,350,1090), fill=INK, width=7)
        draw.ellipse((335, 1070, 365, 1100), fill=BLUE)
        draw.text((150, 1140), "BIKE DETECTION", font=font(28, True), fill=INK)
    else:
        draw.line((cx+70, cy+390, cx+70, 900), fill=INK, width=8)

def make_card(line, pose_path, index):
    im = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(im)
    speaker = str(line.get("speaker", "")).upper()
    visual = str(line.get("visual", ""))
    text = str(line["text"])

    # Header.
    draw.text((70, 70), "BOURIKO", font=font(42, True), fill=INK)
    draw.line((70, 135, 1010, 135), fill=INK, width=4)

    if speaker == "ROCK PHONE":
        draw_rock_phone(draw, True)
        draw_traffic_visual(draw, visual, index)
        # Keep Bouriko present as a smaller reaction when the phone talks.
        if pose_path.exists():
            pose = Image.open(pose_path).convert("RGBA")
            pose.thumbnail((430, 760))
            im.alpha_composite(pose, (50, 520))
    else:
        draw_traffic_visual(draw, visual, index)
        if pose_path.exists():
            pose = Image.open(pose_path).convert("RGBA")
            pose.thumbnail((570, 980))
            im.alpha_composite(pose, (475, 360))
        draw_rock_phone(draw, False)

    # Visual label.
    label = visual.replace("_", " ").upper()
    bbox = draw.textbbox((0, 0), label, font=font(30, True))
    draw.rounded_rectangle((65, 142, 65+bbox[2]-bbox[0]+36, 142+58), 18, fill=BG, outline=INK, width=3)
    draw.text((83, 153), label, font=font(30, True), fill=INK)

    # Caption panel.
    cf = font(48, True)
    lines = wrap(draw, text, cf, 900)
    line_h = 62
    panel_h = len(lines)*line_h + 60
    top = H-panel_h-100
    draw.rounded_rectangle((45, top, 1035, H-100), 28, fill="#FFFFFF", outline=INK, width=4)
    for j, ln in enumerate(lines):
        tw = draw.textbbox((0, 0), ln, font=cf)[2]
        draw.text(((W-tw)//2, top+30+j*line_h), ln, font=cf, fill=INK)

    # Small tech glow accent.
    draw.ellipse((940, 70, 970, 100), fill=BLUE)
    return im.convert("RGB")

def make_real_clip(line, pose_path, index, dur, out_dir):
    """Compose permitted real footage with Bouriko/phone overlays and captions."""
    action = load_action(line)
    if not action:
        return None
    source = resolve_source(action.get("source"), ROOT / "output/broll")
    raw = out_dir / f"{index:02}_real_source.mp4"
    prepare_vertical(source, raw, dur)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    speaker = str(line.get("speaker", "")).upper()
    if pose_path.exists():
        pose = Image.open(pose_path).convert("RGBA")
        if speaker == "ROCK PHONE":
            pose.thumbnail((360, 640))
            overlay.alpha_composite(pose, (55, 1010))
        else:
            pose.thumbnail((500, 860))
            overlay.alpha_composite(pose, (530, 650))

    phone_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    phone_draw = ImageDraw.Draw(phone_layer)
    draw_rock_phone(phone_draw, speaker == "ROCK PHONE")
    overlay = Image.alpha_composite(overlay, phone_layer)

    label = str(action.get("label") or line.get("visual") or "REAL WORLD").upper()
    bbox = odraw.textbbox((0, 0), label, font=font(30, True))
    odraw.rounded_rectangle((55, 55, 55 + bbox[2] - bbox[0] + 36, 113), 18, fill=(244,239,228,235), outline=INK, width=3)
    odraw.text((73, 66), label, font=font(30, True), fill=INK)

    text = str(line.get("text", ""))
    cf = font(46, True)
    lines = wrap(odraw, text, cf, 900)
    line_h = 60
    panel_h = len(lines) * line_h + 54
    top = H - panel_h - 70
    odraw.rounded_rectangle((45, top, 1035, H - 70), 28, fill=(255,255,255,235), outline=INK, width=4)
    for j, ln in enumerate(lines):
        tw = odraw.textbbox((0, 0), ln, font=cf)[2]
        odraw.text(((W - tw) // 2, top + 27 + j * line_h), ln, font=cf, fill=INK)

    overlay_png = out_dir / f"{index:02}_real_overlay.png"
    overlay.save(overlay_png)
    out = out_dir / f"{index:02}.mp4"
    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(raw), "-loop", "1", "-i", str(overlay_png),
        "-t", f"{float(dur):.3f}",
        "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
        "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
    ])
    return out

def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    audio_dir = ROOT / "output/audio"
    segments = []
    for i, line in enumerate(story["lines"]):
        wav = audio_dir / f"{i:02}.wav"
        if not wav.exists():
            raise RuntimeError(f"Missing voice audio: {wav}")
        with wave.open(str(wav), "rb") as f:
            dur = f.getnframes() / f.getframerate()
        segments.append((line, dur))

    poses_file = ROOT / "assets/poses/poses.json"
    poses = json.loads(poses_file.read_text())
    if not poses:
        raise RuntimeError("Pose library is empty")

    od = ROOT / "output/render"
    od.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, (line, dur) in enumerate(segments):
        pose = poses[i % len(poses)]
        pose_path = ROOT / pose["file"]
        real_out = make_real_clip(line, pose_path, i, dur, od)
        if real_out:
            clips.append(real_out)
            continue
        card = make_card(line, pose_path, i)
        png = od / f"{i:02}.png"
        card.save(png)
        out = od / f"{i:02}.mp4"
        # Gentle camera motion keeps the cut-out scene alive without AI video generation.
        vf = (
            f"zoompan=z='min(zoom+0.0007,1.035)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={max(1,round(dur*FPS))}:s={W}x{H}:fps={FPS},"
            f"format=yuv420p"
        )
        run([
            "ffmpeg","-y","-loglevel","error","-loop","1","-i",str(png),
            "-t",f"{dur:.3f}","-vf",vf,"-c:v","libx264","-pix_fmt","yuv420p",str(out)
        ])
        clips.append(out)

    lst = od / "concat.txt"
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips))
    silent = ROOT / "output/silent.mp4"
    run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(silent)])

    concat = ROOT / "output/audio_all.wav"
    run([
        "ffmpeg","-y","-loglevel","error","-f","concat","-safe","0",
        "-i",str(ROOT/"output/audio_concat.txt"),"-ar","24000","-ac","1",str(concat)
    ])
    final = ROOT / "output/bouriko.mp4"
    run([
        "ffmpeg","-y","-loglevel","error","-i",str(silent),"-i",str(concat),
        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-shortest",str(final)
    ])
    print(f"Rendered {final}")

if __name__ == "__main__":
    main()
