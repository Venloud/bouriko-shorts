# Bouriko — Claude Handoff: Creative/Renderer Direction After First-Clip Review

This is the implementation handoff for the next Bouriko pass. The first rendered clip proved the pipeline works, but the creative format needs redesign.

## Already changed

- `pipeline/qa.py`: duration is now reported as data instead of blocking the build when outside 61–68s.
- `.github/workflows/build.yml`: artifact upload uses `always()`.
- Pose-library Pillow/ImageChops issue is fixed.
- Kokoro voice generation works.

## Core creative direction

**Bouriko asks the question. The world/diagram demonstrates the answer. Rock Phone explains it.**

Bouriko is the mascot/host, not the literal visual explanation. He can stand off to the side, watch, point, react, or briefly appear. Do not write jokes like “there is a tiny man inside every traffic light” as the default explanation style.

The conversation should be natural, short, and dynamic. Do not force long alternating speeches. Use follow-up questions and short answers.

Example:

BOURIKO: “How do traffic lights actually know when a car is there?”

ROCK PHONE: “Many of them use a sensor buried in the road.”

BOURIKO: “Buried in the road?”

ROCK PHONE: “Look at the pavement. See that rectangular cut?”

BOURIKO: “Yeah.”

ROCK PHONE: “That’s often an induction loop. Electricity runs through the wire and creates a magnetic field.”

BOURIKO: “So when my car stops there?”

ROCK PHONE: “The metal in your car changes the field. The controller detects it and tells the signal a vehicle is waiting.”

Bouriko can then ask about bicycles, cameras, radar, or timers.

## Voice direction

Current voices are Bouriko `am_fenrir` and Rock Phone `bf_emma`, but they need another pass.

Bouriko: curious, youthful/energetic, slightly goofy, conversational, understandable.

Rock Phone: calm, intelligent, concise, assistant-like, confident.

Do not use filler words to inflate runtime. Avoid “um”, “like”, repeated phrases, and long pauses unless they are genuinely useful.

Do not rely on the current 0.42s line pause as a runtime solution. Runtime should come from useful dialogue and visual storytelling.

## Visual format

The current “character + diagram + caption card -> next card” format is not the target.

The target is a short-form tutorial/explainer:

- show the thing
- point at the thing
- draw/highlight the important part
- zoom into it
- explain it
- switch to another visual
- return to Bouriko
- continue the conversation

Use Cloudflare image generation for environment plates when useful. Examples for the traffic-light video: street intersection, close traffic signal, pavement/stop line, car at intersection, bicycle waiting, traffic camera, or simple blank environments.

Cloudflare environments should match the Bouriko visual language. They must not replace the consistent Bouriko character.

Do not require an AI-generated environment for every shot. Blank/off-white scenes are valid when a clean explainer graphic works better.

## Draw-on tutorial graphics

Do NOT simply pop a traffic-light PNG on the right.

If the narration says “Look at the pavement. See that rectangular cut?”:

1. Show the road/intersection.
2. Move/zoom toward the stop line.
3. Draw the rectangular loop onto the scene.
4. Highlight it in Bouriko electric blue.
5. Draw a handwritten-style label such as `INDUCTION LOOP`.
6. Keep the annotation visible while the explanation continues.

Build reusable renderer primitives for:

- traffic lights: housing + red/yellow/green circles
- induction loops: road + loop + car + blue magnetic-field effect
- detection flow: `CAR -> ROAD SENSOR -> CONTROLLER -> TRAFFIC LIGHT`
- cameras: camera + mounting point + detection zone + vehicle
- bicycles and detection zones
- arrows, circles, rectangles, labels, highlights
- zoom/pan/draw-on animation

The graphics should feel hand-drawn and native to the Bouriko channel, not like random stock PNGs.

## Story format

The current single `visual` string per line should evolve toward richer visual actions.

Example:

```json
{
  "speaker": "ROCK PHONE",
  "text": "That's often an induction loop.",
  "visual_actions": [
    {"type": "environment", "asset": "intersection"},
    {"type": "zoom", "target": "road_stop_line"},
    {"type": "draw", "shape": "rectangle", "target": "loop"},
    {"type": "highlight", "target": "loop", "color": "#2EA8FF"},
    {"type": "label", "text": "INDUCTION LOOP"}
  ]
}
```

A single dialogue line may have multiple visual actions.

Useful action types include: `environment`, `cutout`, `draw`, `highlight`, `arrow`, `label`, `zoom`, `pan`, `diagram`, `reaction`, `overlay`, `real_clip` (future), and `blank`.

## Bouriko's screen time

Bouriko does not need to perform an action every second.

He can:

- stand
- look
- point
- react
- watch the explanation
- appear during transitions

The educational visual can occupy most of the screen.

Example rhythm:

1. Bouriko asks beside an intersection.
2. Full-screen road diagram while Rock Phone explains.
3. Bouriko returns for a reaction/follow-up.
4. Traffic-light close-up/diagram.
5. Bicycle scene.
6. Camera/radar scene.
7. Bouriko asks the next question.

## Traffic-light video

Main question:

“How do traffic lights actually know when a car is there?”

Suggested flow:

1. Normal intersection opening.
2. Rock Phone introduces sensors.
3. Zoom into pavement.
4. Draw/highlight induction loop.
5. Show car over loop.
6. Animate detection: car -> loop -> controller -> signal.
7. Bouriko asks about bicycles.
8. Show bicycle/detection zone.
9. Briefly explain cameras, radar, and timers.
10. End with a teaser: “What about those cameras above the traffic lights?” -> next video: “How do traffic-light cameras actually work?”

Keep the explanation factual and source-backed.

## Real clips

Support for real-world clips can be added later, but the pipeline must not depend on stock-footage websites. Priority is code-drawn graphics + Cloudflare environments + Bouriko cutouts. Real clips are optional future inputs.

## Files to change

### pipeline/script.py
- Replace the overly literal traffic-light exact-story direction.
- Support natural conversations.
- Evolve from a single `visual` string to richer `visual_actions`.
- Treat Bouriko as host/question/reaction and Rock Phone as concise explainer.
- Humor should come from personality/reactions, not absurd factual explanations.

### pipeline/render.py
Move beyond static cards toward:
- environment plates
- draw-on annotations
- animated arrows/labels
- diagrams
- highlights
- zooms/pans
- Bouriko reaction shots
- blank explainer scenes

Keep 1080x1920, ink/hand-drawn feel, and electric-blue tech accent.

### pipeline/voice.py
- Reduce/remove artificial line padding.
- Keep conversation tight.
- Test better Bouriko/Rock Phone voices.
- Preserve word timings.

### config.json
Keep `target_seconds: [61, 68]` as target/reporting data during this development phase. Do not block visual review because a test is shorter.

## First goal

Do not rebuild the entire production system at once.

Make ONE new traffic-light test that demonstrates:

- natural conversation
- Bouriko asking the main question
- Cloudflare environment/background
- Bouriko as mascot/host
- hand-drawn traffic-light graphic
- draw-on annotation
- induction-loop diagram
- car detection animation
- concise captions
- faster visual changes
- no artificial 0.42s dead-air padding
- duration reported but not blocking

Then watch that test before expanding the renderer further.

## Reference

User supplied this YouTube Shorts reference for the intended explainer principle:

https://www.youtube.com/shorts/mytYzlemg-s?feature=share

The reference was described as an explainer using changing visuals such as simple/blank backgrounds, illustrative graphics/emojis, relevant images, real-world clips, and text/labels.

Use the principle of visual explanation, not the creator’s branding, artwork, wording, or exact editing.

## Bottom line

The basic pipeline works. The next phase is creative-system redesign, not basic pipeline debugging.

**Bouriko asks the question. The world/diagram demonstrates the answer. Rock Phone explains it.**

**Do not stretch a conversation to hit 61–68 seconds. Make the video good first; duration is measurement data until the format is locked.**


## Real-world footage is now implemented as an optional renderer path

The renderer now supports a `real_clip` visual action. It can take a local permitted clip or a permitted downloadable URL, convert it to the 1080x1920 canvas, and composite the Bouriko cutout, Rock Phone, label, and captions over the footage.

Files:
- `pipeline/broll.py` resolves local clips or URLs and prepares vertical footage.
- `pipeline/render.py` detects `real_clip` actions and overlays Bouriko/Rock Phone on the real footage.
- `.github/workflows/build.yml` installs `yt-dlp` so this optional path can work in CI.

Example story action:

```json
{
  "type": "real_clip",
  "source": "assets/broll/traffic_intersection.mp4",
  "label": "REAL INTERSECTION"
}
```

Use only footage the channel is allowed to use. Real footage is an enhancement, not a required dependency: if a story has no `real_clip` action, the build remains fully local and uses diagrams/environment plates/cutouts.

This means the format can now deliberately mix:
1. real-world footage
2. generated/environment plates
3. hand-drawn explainer graphics
4. Bouriko cutouts
5. Rock Phone overlays

The current traffic-light test is still primarily the explainer/diagram test. Future story plans can insert real clips wherever they genuinely clarify the explanation.


# NEW DIRECTION — OCTOBER 2, 2026

The previous mascot-led video format is SCRAPPED.

## Video format now
- Bouriko remains the face/branding of the page, not the on-screen presenter.
- Videos are narrator-led.
- Use centered captions in the middle of the frame.
- Main visuals are real footage and free photos.
- Also use screenshots, simple diagrams, and generated/constructed graphics when they explain something better.
- Change visuals when the subject changes.
- Use short fades/crossfades between visual sections.
- NO pose animation.
- NO character movement system.
- NO Ken Burns / zoompan camera movement.
- NO Bouriko cutout in the video by default.
- NO Rock Phone overlay in the video by default.
- Do not build runtime around mascot poses.

## Free media system
Automated media discovery is now in pipeline/media.py.

Primary sources:
- Pixabay photos + videos
- Coverr stock video
- Pexels optional

Selected media is downloaded locally and recorded in output/media_manifest.json.

Required provider secrets, when available:
- PIXABAY_API_KEY
- COVERR_API_KEY
- PEXELS_API_KEY

The build must still work without them by falling back to local/simple graphics.

## Voice
Use ONE consistent narrator voice for the whole video.
The voice can be overridden with NIGHTFILES_VOICE.
The exact Night Files voice ID is not currently recorded in the accessible Night Files GitHub repository, so the current fallback is configurable rather than pretending a specific ID was verified.

Do not create separate Bouriko/phone dialogue voices anymore.

## Phone
The CSS-looking Rock Phone is no longer required in the video format. Do not spend time improving the old drawn phone unless it is later needed for page branding or a specific visual.

## Writer
prompts/script.txt now asks for a narrator-led factual explainer with media/search ideas instead of Bouriko/Rock Phone dialogue.

The traffic-light test in inbox/traffic_light.txt is now a narrator script.

## Goal for the next visual test
The test should look like a modern documentary/tutorial Short:
NARRATION -> real/free footage -> centered caption -> another real/free image/video -> diagram when useful -> centered caption -> next visual.

It should NOT look like a slideshow of mascot pose cards.
