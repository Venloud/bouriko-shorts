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


## CURRENT IMPLEMENTATION — OCTOBER 2, 2026

The media-first narrator direction is now implemented with a Remotion renderer.

### What is live
- narrator-only format
- free-media discovery via pipeline/media.py
- real stock SFX via pipeline/sfx.py
- timed asset preparation via pipeline/remotion_prepare.py
- Remotion/React renderer under remotion/
- 1080x1920 H.264 output
- centered captions
- hard scene cuts
- no mascot presenter, Rock Phone overlay, Ken Burns/zoompan, or fade-to-black slideshow behavior
- build and daily workflows now route through Remotion

### First test
Run GitHub Actions -> Bouriko Build -> Run workflow -> enable the traffic-light test input. The artifact is named bouriko-remotion-test.

### Important
This is the first Remotion integration pass. If the test render exposes timing, media-format, caption, or visual-quality issues, fix those before adding ComfyUI/PersonaLive/AutoClip/Ruflo as runtime dependencies.

### Architecture roadmap
1. Remotion = production renderer.
2. AutoClip = future clip/highlight selection logic.
3. ComfyUI = optional fallback for missing explanatory visuals.
4. MuMuAINovel = optional story-planning inspiration.
5. Ruflo = optional orchestration layer.
6. PersonaLive = optional research module only; not part of the default narrator format.


# CURRENT MASTER HANDOFF — OCTOBER 2, 2026 — LATEST LOG

This section supersedes older sections where they conflict. It is the current implementation state and the exact next-pass target.

## 1. Product direction — LOCKED

Bouriko is the channel/page brand. **Bouriko is NOT the on-video mascot by default anymore.**

The Shorts are:
- narrator-led
- factual and fast
- built around real-world footage, free/permissioned photos and videos, screenshots, diagrams, and simple explanatory graphics
- centered captions
- one consistent narrator voice
- real sound effects
- scene changes driven by the subject, not by sentence-card templates

Do NOT return to:
- Bouriko pose cards
- character movement systems
- Rock Phone presenter dialogue
- Rock Phone overlays by default
- Ken Burns / zoompan
- mascot animation as the core video format
- fade-to-black between every sentence
- static PowerPoint/card presentation
- formal/bookish presentation styling

The intended visual rhythm is:

**HOOK → relevant footage → cut → relevant footage → diagram/graphic when needed → SFX → new visual → occasional 1–2 second reaction/meme beat → continue**

The video should feel like a modern TikTok/Shorts explainer, not a narrated slideshow.

## 2. First-publish goal

The explicit project goal is:

**Do not stop until the first video is rendered, QA-passed, and ready for publishing.**

The traffic-light story is the current test case.

Do not add OmniVoice, Gstack, AutoClip, ComfyUI, PersonaLive, Ruflo, or other optional systems to the production path before the first publishable video exists.

Current shortest production path:

**story → free/permissioned media → Kokoro narrator → real SFX → Remotion → QA → publish**

## 3. Current implementation

### Renderer

Remotion/React is the production renderer.

Current path:
- `remotion/src/BourikoShort.tsx`
- `remotion/src/Root.tsx`
- `remotion/src/index.ts`
- `remotion/render.mts`
- `pipeline/remotion_prepare.py`

Target:
- 1080x1920
- 30 fps
- H.264
- narration audio
- real SFX
- hard visual cuts
- centered captions
- full-screen media
- fallback graphic only when media genuinely cannot be obtained

The Remotion integration has already rendered a ~61.7 second MP4 successfully in an earlier run. Therefore the current blocker is media retrieval, not basic Remotion rendering.

### Narration

Current narrator pipeline is `pipeline/voice.py` using Kokoro.

Current config:
- narrator: `am_liam`
- speed: `0.98`
- `NIGHTFILES_VOICE` can override the voice through GitHub Variables.

Important:
- keep one narrator voice
- do not restore two-voice Bouriko/Rock Phone dialogue
- user wants the voice direction to be close to the Night Files voice if that can be verified
- do not claim a specific Night Files voice ID unless it is actually verified

The latest successful run showed Kokoro generating narration; its Hugging Face unauthenticated-rate warning is informational, not the current blocker.

### SFX

The real SFX system is working.

The latest successful log showed:

- whoosh downloaded from Night Files
- sweep downloaded from Night Files
- click downloaded from Night Files
- camera downloaded from Night Files
- interface downloaded from Night Files
- beep downloaded from Night Files
- impact downloaded from Night Files
- glitch downloaded from Night Files
- 8 usable SFX assets
- 10 SFX events

Current intended priority:

**Night Files SFX → Mixkit fallback → no effect**

Night Files source:
`https://github.com/Venloud/horror-shorts`

Mixkit source:
`https://mixkit.co/free-sound-effects/`

Do not replace the working Night Files SFX path unless necessary.

### Media

`pipeline/media.py` is responsible for free/permissioned media discovery and downloading.

Configured providers, when secrets exist:
- Pixabay
- Pexels
- Coverr

No-key fallback:
- Wikimedia Commons
- Mixkit stock video

Required optional secrets:
- `PIXABAY_API_KEY`
- `PEXELS_API_KEY`
- `COVERR_API_KEY`

The build must remain usable without those keys.

Every downloaded asset must be recorded in:
`output/media_manifest.json`

Each record should preserve:
- provider
- source URL
- creator when available
- title
- license
- license URL
- local path

Do not silently substitute generated cards for failed media and call that a successful visual build. QA exists specifically to prevent this.

## 4. LATEST LOG — OCTOBER 2, 2026

Latest uploaded run checked out:

`62251cf75dd370a747d8ec8e6ba26e7c2271a6bc`

The run used repository:
`Venloud/bouriko-shorts`

Runner:
- Ubuntu 24.04.5
- Python 3.11.16
- Node 20.20.2

### Actual failure

The workflow reached:

`python pipeline/media.py`

and failed immediately with a Python syntax error:

```
File "/home/runner/work/bouriko-shorts/bouriko-shorts/pipeline/media.py", line 91
raw_urls = re.findall(r"https://assets\.mixkit\.co/videos[^\s\\"\']+?\.mp4", html)
SyntaxError: unexpected character after line continuation character
```

So the Mixkit implementation was **not actually tested successfully in this run**.

This is the immediate blocker.

### Consequence

Because `pipeline/media.py` crashed, the workflow did not proceed through the normal media → voice → SFX → Remotion → QA chain in this latest run.

Do not report this run as a successful media test.

The previous run had already demonstrated:
- Remotion rendered successfully
- duration was 61.72 seconds
- QA correctly blocked publication because media count was 0

That previous QA result was:

```
DURATION DATA: 61.72s (target 61-68s)
MEDIA DATA: 0 downloaded assets (0 video)
AssertionError: not enough real media; refusing to publish a slideshow
```

That QA failure was correct.

## 5. Immediate next implementation

### FIX #1 — repair the Mixkit regex

The current `pipeline/media.py` on `main` contains an invalid Python raw-string regex.

Replace the malformed expression with valid Python syntax, for example:

```python
raw_urls = re.findall(
    r'https://assets\.mixkit\.co/videos[^\s"\']+?\.mp4',
    html,
)
```

The exact implementation can use an equivalent safe parser, but it must first pass `python -m py_compile pipeline/media.py`.

### FIX #2 — do not rely only on exact natural-language Mixkit slugs

The current Mixkit function constructs:

`https://mixkit.co/free-stock-video/<entire-query-slug>/`

Many story queries are long phrases such as:
- traffic light changing at busy intersection
- cars driving through intersection road traffic
- induction loop detector road pavement traffic

Those exact slugs may not exist.

After fixing the syntax, Mixkit discovery should try:
1. exact query slug
2. shorter keyword/category slugs
3. deduplicate MP4 URLs
4. return a small candidate set
5. let `ensure_asset()` try candidates until one downloads successfully

For the traffic-light test, useful fallback keywords include:
- traffic-light
- traffic
- intersection
- road
- bicycle
- traffic-camera
- street
- car

Do not scrape huge catalogs. Keep retrieval modest and respect provider terms.

### FIX #3 — test the actual download path

The next workflow must prove all of these:

```
Media assets downloaded: >= 8
Video assets: >= 4
```

The QA gate currently expects at least 8 real assets and at least 4 videos to prevent slideshow-style publishing.

Do not weaken those checks merely to make the build green.

### FIX #4 — verify the produced media manifest

The successful test should produce a non-empty:

`output/media_manifest.json`

and each story line that receives media should have a usable local `media_asset`.

The artifact should contain:
- `output/bouriko.mp4`
- `output/story.json`
- `output/word_timings.json`
- `output/media_manifest.json`

## 6. Traffic-light test story

Current test concept:

**How does a traffic light actually know you're there?**

Core factual points:
1. Many intersections use vehicle detection.
2. A common method is an induction loop in/under the pavement.
3. The loop contains wire and creates a magnetic field.
4. A vehicle's metal changes the loop's electrical/magnetic characteristics.
5. The controller detects the change and knows a vehicle is waiting.
6. Not every signal uses induction loops.
7. Some use cameras, radar, other sensors, timers, or programmed schedules.
8. Bicycle detection can require different treatment because a bicycle has much less metal than a car.

The test should show those ideas rather than repeat generic traffic footage for every sentence.

### Suggested visual sequence

- opening: real intersection / traffic light
- hook: red light with cars waiting
- road/pavement close-up
- rectangular induction-loop cuts
- simple under-road loop diagram
- car sitting over loop
- magnetic-field / detection diagram
- controller / traffic-signal equipment
- signal changing
- bicycle at intersection
- camera/radar detection
- programmed timer/schedule
- closing pavement shot
- optional short reaction/meme beat where it genuinely helps

Visuals should change because the explanation changes.

## 7. Current script/media mismatch to fix

The existing traffic-light media actions are still too repetitive in concept.

Examples currently include generic queries like:
- `traffic light changing at busy intersection`
- `cars driving through intersection road traffic`
- `induction loop detector road pavement traffic`
- `traffic signal controller vehicle detection intersection`
- `traffic camera mounted signal intersection`

The media system should preserve the story's intended subject but should not force every line into generic traffic footage.

For explanatory concepts that stock footage cannot show clearly:
- use a simple diagram
- use a screenshot/graphic
- use a permitted image
- use a short reaction insert
- do not invent fake footage of an invisible mechanism

## 8. Visual-quality requirements

The user specifically rejected the prior result as looking like a PowerPoint.

Required:
- no black frame between every visual
- no fade-to-black sentence transitions
- no one-image-per-sentence slideshow feeling
- no formal/bookish font
- no giant static card with a sentence
- no unnecessary visual effects
- no mascot poses
- no repeated traffic intersection clip for unrelated concepts

Required instead:
- real footage whenever it genuinely explains the subject
- free photos when they are better than video
- diagrams for invisible mechanisms
- screenshots/graphics for interfaces or factual references
- hard cuts
- centered readable captions
- sound effects at meaningful moments
- occasional very short reaction/meme insert
- visual changes tied to the story

## 9. Copyright/media rule

Use media the channel is permitted to use.

The automated pipeline should prefer:
1. licensed/free stock providers
2. public-domain or clearly reusable media
3. generated/simple graphics where stock footage is not appropriate

Do not build the system around automatically scraping random copyrighted TikTok/YouTube/movie clips.

A short clip is not automatically legal merely because it is 1–2 seconds long.

If reaction/meme inserts are later added, make the source/licensing path explicit and keep the mechanism replaceable.

## 10. QA gate

QA should continue to enforce:
- final video exists
- duration is reported
- audio exists
- enough narration lines
- all story lines have text
- visual coverage exists
- media manifest exists
- >= 8 real downloaded media assets
- >= 4 downloaded video assets
- refuse slideshow-style builds

Duration target remains 61–68 seconds for production, but during this visual-development phase duration should be treated as measurement data rather than a reason to block creative review if the implementation needs a shorter test.

## 11. Workflow notes

Current build workflow:
- checkout
- Python 3.11
- Node 20
- install ffmpeg/espeak-ng
- install Python dependencies
- generate story
- download media
- generate narrator
- generate SFX
- prepare Remotion
- npm install
- render
- QA
- upload artifact even on failure

Important:
- the `test` workflow input exists, but historically it has been descriptive rather than actually selecting a specific script. Do not assume the checkbox changes the story unless the workflow/script explicitly wires it through.
- `inbox/traffic_light.txt` is the current test story.

## 12. Research already completed

### OmniVoice
`https://github.com/k2-fsa/OmniVoice`

Candidate future TTS backend. Not required for first publish.

### Public-API
`https://github.com/davemachado/public-api`

Useful as an API discovery source. Not required for first publish.

### Gstack
`https://github.com/garrytan/gstack`

Claude Code engineering workflow/tooling. Not a production runtime dependency.

### Other considered tools

- Remotion → production renderer
- AutoClip → future clip/highlight selection
- ComfyUI → optional generated-visual fallback
- MuMuAINovel → optional story-planning inspiration
- Ruflo → optional orchestration
- PersonaLive → optional research/future module

Decision:
**Do not add optional tooling before first publish.**

## 13. Known source/verification rule

Night Files SFX usage is confirmed by the latest successful SFX log.

Do NOT claim specific Night Files voice IDs or specific SFX file paths were manually verified unless the repository was actually fetched and inspected.

The current SFX runtime log is enough to establish that the configured Night Files SFX downloads succeeded.

## 14. Commit/history relevant to the current blocker

Important recent commits:

- `40bcf0f` — RGBA fallback graphic fix
- `33ead31` — original automated sound design
- `0c55cab` — mix SFX into final audio
- `acd2e8f` — run sound design before render
- `a46c6d5` — add sound design to daily builds
- `a9dfd8f` — block slideshow-style builds
- `8100d7c` — SFX duration fix
- `f9d4eba` — replace generated SFX with real stock library
- `f2ce920` — document SFX sources/licensing
- `fa0f201` — keep narrator voice path stable
- `965e8c1` — Night Files SFX first, Mixkit fallback
- `493220c` — document Night Files/Mixkit SFX
- `8ecb28a` — resilient media downloads/rate limits
- `aa2f17e` — fix Remotion preparation Python syntax
- `a3602a9` — fix media path regex in Remotion
- `bfdc8ea` — add keyless Mixkit stock video fallback
- `62251cf` — attempted Mixkit MP4 parser fix; latest uploaded log shows the regex is still syntactically invalid, so this commit must be corrected

## 15. Definition of done for the first publish

Do not call the project ready until:

1. `pipeline/media.py` passes Python syntax/compile.
2. Traffic-light workflow completes media discovery.
3. At least 8 real media assets are downloaded.
4. At least 4 are videos.
5. Narration succeeds.
6. Night Files SFX or Mixkit fallback succeeds.
7. Remotion renders the MP4.
8. QA passes without weakening the media gate.
9. The artifact MP4 is visually checked.
10. The video no longer looks like a PowerPoint.
11. No black/fade-to-black sentence gaps.
12. Visuals actually match the narration.
13. Captions are readable and modern.
14. Audio/SFX are present and balanced.
15. The final MP4 is suitable for the next publishing step.

**First publish comes before feature expansion.**

## 16. OCTOBER 2, 2026 — FULL PYTHON/YAML SYNTAX AUDIT

The October 2 failure was reviewed as a pipeline-wide syntax problem, not treated as a one-line typo.

### Root cause

`pipeline/media.py` had a malformed raw Python regex string around the Mixkit MP4 URL parser. The previous expression mixed escaped backslashes and quote delimiters inside a raw string, which caused Python to parse the string incorrectly.

Python's documentation confirms that raw strings preserve backslashes, but the Python string delimiter still has to be syntactically valid. Regex patterns should normally use raw strings, with the quote delimiter chosen so the pattern itself remains valid.

### Corrected Mixkit parser expression

```python
raw_urls = re.findall(
    r'https://assets\.mixkit\.co/videos[^"\s]+?\.mp4',
    html,
)
```

This deliberately avoids embedding unnecessary escaped quote/backslash combinations in the raw string.

### Pipeline-wide syntax review

The Python files under `pipeline/` were reviewed, including:

- `common.py`
- `breaking_script.py`
- `broll.py`
- `buffer.py`
- `checkpoint.py`
- `connect_tiktok.py`
- `media.py`
- `news_watch.py`
- `notify.py`
- `publish.py`
- `qa.py`
- `remotion_prepare.py`
- `render.py`
- `rhubarb.py`
- `script.py`
- `sfx.py`
- `voice.py`
- `youtube.py`

No additional Python parse errors were found during source review.

### Permanent CI syntax gate

The build workflows were also updated so future syntax mistakes are caught before the media/build stages:

```bash
python -m compileall -q pipeline
```

Added to:
- `.github/workflows/build.yml`
- `.github/workflows/daily.yml`
- `.github/workflows/breaking-tech.yml`

The syntax gate is intentionally separate from dependency installation and media generation.

### Commits from this repair

- `2d963104` — **Fix Mixkit regex syntax**
  - Replaced the malformed Mixkit MP4 regex with valid Python raw-string syntax.
- `a5d22e4` — **Add full pipeline Python syntax gate**
  - Added the compileall check to the build workflow.
- `595da09` — **Add full pipeline Python syntax gate**
  - Added the compileall check to the daily workflow.
- `e03fa4d` — **Add full pipeline Python syntax gate**
  - Added the compileall check to the breaking-tech workflow.
- `aeef294` — **Fix workflow syntax gate step**
  - Corrected the build workflow so the syntax check is its own YAML step rather than creating duplicate `run:` keys.
- `3765cd6` — **Fix workflow syntax gate step**
  - Corrected the same duplicate `run:` issue in the daily workflow.

### Important verification status

The source-level syntax repair is complete, but the Mixkit download path is **not yet proven by a successful full GitHub Actions run after these commits**.

The next run must prove:

1. Python syntax gate passes.
2. `pipeline/media.py` starts successfully.
3. Media discovery downloads at least 8 assets.
4. At least 4 downloaded assets are videos.
5. Narration succeeds.
6. SFX succeeds.
7. Remotion renders.
8. QA passes.

Do not mark first-publish readiness until that run provides evidence.