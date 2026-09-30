# First task for Claude Code (paste this when Bouriko is unparked)

Read CLAUDE.md fully. Then build the first working version of the Bouriko pipeline in this repo,
reusing code from Venloud/horror-shorts (copy, adapt, don't import across repos).

1. **Scaffold** (copy/adapt from horror-shorts): pipeline/common.py (config, logging, retry + per-model
   quota handling for Gemini/Groq), notify.py (ntfy, handles missing story), buffer.py, publish.py
   (TikTok drafts + YouTube upload), youtube.py, checkpoint.py; workflows build.yml (buffer, zero-config
   test with a single `fresh` checkbox), daily.yml (publisher), yt_check.yml.
2. **Writer** (pipeline/script.py): pick pillar from config rotation + topic from data/topics.json
   (skip used topics in data/history.json). Fetch sources per CLAUDE.md hierarchy, build a fact ledger,
   write the script with prompts/script.txt, run prompts/critic.txt, fact-check against the ledger.
   Output story.json: title, pillar, lines [{speaker, text, visual}], sources, caption, hashtags.
   Inbox: inbox/*.txt jumps the queue (first line SCRIPT = use exact lines, TOPIC = write about it).
3. **Voices**: Kokoro, two voices (config `voices.bouriko`, `voices.rock_phone`). Pick voices and write
   voice_samples.yml so the owner can listen and choose. Word timings for captions; viseme timings via
   Rhubarb for Bouriko's lines.
4. **Renderer** (pipeline/render.py), based on horror-shorts' cutout mode:
   - Pose library: cut the owner's reference sheets in assets/reference into individual poses (rembg),
     save to assets/poses/<name>.png + a poses.json (name, tags: talking/pointing/confused/phone/...).
     Produce a review sheet so the owner can confirm the crops.
   - Mouth: 3-4 mouth shapes (closed/open/wide/O) swapped on Bouriko's head during his lines. If clean
     mouth layers aren't possible from the sheets, fall back to a subtle talking bob + open/closed swap.
   - Rock Phone: glows/pulses blue while it speaks.
   - Diagrams: code-drawn sketch diagrams (Rough.js via node or a Python rough-style renderer) that
     draw themselves (stroke reveal), driven by each line's [VISUAL] note.
   - Off-white paper background, ink style, 1080x1920, captions in Patrick Hand/Permanent Marker.
   - A new element or cut every 2-4 s; reuse the visual-variety QA gate.
5. **QA gate**: 61-68 s total, never under 61 s; audio present; captions present; visual variety;
   fact-check passed; no brand logos drawn.
6. **Docs**: README.md + SETUP.md (secrets list), keep CLAUDE.md current.
7. Test offline end to end with one Hidden-tech topic (traffic light sensors), send the owner the
   mp4 + pose review sheet. End with the UPDATE REPORT block.
