# Night Files to Bouriko editor migration
2026-10-25. Source inspected: Venloud/horror-shorts main, Venloud/claudevandam main.
Status: precise integration reference, NOT a claim that all code is already ported.

## Decision
Reuse all **general-purpose capabilities** of Night Files editing, visuals, clips, sound and quality assurance. Do not copy a horror aesthetic or story genre, Night Files FFmpeg rendering as a replacement for Bouriko's working Remotion renderer, production secrets, schedules, TikTok inbox automation, Buffer.com workflows, or posting modules. **Publishing stays owner-locked.** Keep **one** manual Bouriko Build video workflow and its empty-buffer gate. JJK is a regression fixture, not a topic switch.

## Exact source and destination inventory
| Capability | Night Files source inspected | Bouriko target | Porting requirement |
| --- | --- | --- | --- |
| Relevant free real footage, archive images, retries, source attribution | `pipeline/media.py` | `pipeline/media.py` | Consolidate candidate ranking, shot matching, resolution/aspect checks, rights-safe fallback; keep current free-media providers |
| Story, claim-grounded shots and meaningful narrative arcs | `pipeline/story.py` | `pipeline/script.py`, generic scene plan | Extract topic-independent planning and story QA only, strip genre prompts and horror word lists |
| Clip trimming, scene assembly, matched editing beats | `pipeline/render.py` | `remotion/src/BourikoShort.tsx`, `pipeline/remotion_prepare.py` | Port shot schedules, exact alignment, purposeful inserts and hard-cut decisions as data, not FFmpeg-specific glue |
| Synchronized captions, readable grouping, font fallback | `pipeline/captions.py` | Remotion caption components, `pipeline/voice.py` | Port timing and phrase grouping behavior, use phone-safe caption tests, preserve accurate timings |
| Motivated environmental motion, optional depth and atmosphere | `pipeline/effects.py`, `pipeline/ai_motion.py` | optional Remotion primitives | Port as explicit opt-in visual semantics, not automatic zoom, fog, shake, AI motion or decorative transitions |
| Reusable character cutouts, phone/UI text and diagram inserts | `pipeline/cutout.py` | generic Remotion diagram/UI overlays | Extract generic primitives only, retain Bouriko mascot as branding rather than mandatory presenter |
| Sound effects and ambience | Night Files asset library + renderer | `pipeline/sfx.py`, Remotion sound mix | Bouriko already references Night Files SFX; normalize volumes, source/provenance and timing, remove automatic whooshes |
| Rendering and gate checks | `pipeline/render.py` and source manifests | `pipeline/qa.py` | Add narrative relevance, source and licensing, caption safe zones, black gaps/frozen scenes, audio peaks, clip duration, no publisher side effects |
| Owner editorial rules | Vandam `docs/VIDEO_EDITING_MASTER_INSTRUCTIONS_2026-10-24.md` | this doc and `docs/GENERAL_PURPOSE_VIDEO_ENGINE.md` | Hard cut default; dissolve only time passage; fade only ending; controlled easing; meaningful graphics and sound |

## Migration contract
Build around one generic time-coded scene schema with fact/reference IDs, narration span, media candidates, verified chosen media, licensing/attribution, shot duration, semantic editing action, graphics/caption/SFX cues, and gate verdict. Modules must consume this same schema for JJK, traffic lights, GPS and a historical explainer, no subject-specific code branches. Preserve renderer and video QA contracts while transplanting verified reusable logic.

## No unsafe direct copies
`pipeline/story.py` (122k) includes horror prompts, channel stories and provider logic. `pipeline/render.py` (45k) is FFmpeg-first with genre-dependent look and optional motion. `pipeline/cutout.py` (45k) concerns a recurring illustrated character. `pipeline/media.py` (58k) uses Night Files configuration and channel grading. These are reference implementations, not drop-in file replacements. Whole-file substitution would break existing Bouriko interfaces and introduce genre leakage.

## Ordered code work
1. Schema and tests: generic shot manifest and compatibility adapter for existing `output/story.json`. JJK reference and three unrelated fixtures.
2. Clips: transplant Night Files candidate sourcing, source matching, trimming and selection with licensing evidence; rerun current Bouriko media tests.
3. Editing: port hard cuts, timing semantics, contextual inserts and restrained overlays into existing Remotion components; no automated FX quota.
4. Captions + audio: word timing, phrase grouping, safe zones, music ducking and contextual SFX.
5. QA: automated media validity checks plus frame contact sheet, source-rights manifest, scene/narration relevance and actual human MP4 review.
6. Render four genres with same code paths; compare to JJK baseline. No publication or workflow proliferation.

## Acceptance checklist
- One manual build workflow. Empty finished review buffer skips generation unless user requests fresh. No scheduled triggers or posting.
- Each source clip has enough metadata to independently check relevance, reuse rights and duration.
- Every spoken explanation has a relevant matching picture, evidence clip, UI drawing or truthful diagram.
- No automatic decorative transition, Ken Burns, generic whoosh or slideshow fallback.
- Captions are synchronized, visually safe and readable on a phone.
- JJK and unrelated topics use same production contracts.
- Actual MP4, frames and logs reviewed. Code merges without render proof are only partial integration.

## Source review limitations
Source structure and several files were inspected through the GitHub connector. No runtime renderer execution, end-to-end complete clip-port, or production media QA occurred in this inspection. Integration milestones must be reported as implemented only after precise code changes and tests.
