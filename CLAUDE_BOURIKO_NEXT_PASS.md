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
