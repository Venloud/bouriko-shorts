# Bouriko general-purpose video engine, approved direction
Date: 2026-10-25
Status: Canonical product direction, implementation and real MP4 acceptance pending.

## Goal
Generate an accurate, coherent, original video about ANY supported topic: technology, science, history, anime, games, explanations and future niches. JJK Culling Game is the **regression baseline** for complex lore and visual alignment, not an anime-only architecture or a hardcoded example to output.

## Authority and precedence
1. Owner's latest directives and the Vandam video-editing master guide (`Venloud/claudevandam/docs/VIDEO_EDITING_MASTER_INSTRUCTIONS_2026-10-24.md`).
2. Bouriko's October 2 narrator-led format override in `CLAUDE.md`.
3. Night Files (`Venloud/horror-shorts`) reusable general-purpose editing architecture and proven QA patterns, adapted without repository coupling.
4. Existing Bouriko pipeline contracts and working `main` behavior.
5. JJK experimental code as a source of independently reviewed, reusable primitives only.
Historical mascot/Rock Phone dialogues and the earlier two-voice renderer are NOT default pipeline requirements.

## One content-independent workflow
Topic/request -> source discovery and rights research -> claim/fact ledger -> narrative objective, audience, hook, causal explanation and ending -> verified script -> semantic scene plan -> asset discovery with rights and relevance evidence -> timed single-narrator voice -> caption alignment -> Remotion scene composition -> soundtrack/SFX mix -> technical + editorial QA -> reviewable MP4 -> optional separately approved publishing.

Separate the topic-specific **content** from reusable **editing** capabilities. Scene plans should express purpose, not anime-specific implementation. Renderer primitives accept generic entities, locations, concepts, actions, measurements and sources.

Each scene should specify at minimum:
- scene_id, narration/text span, claim identifiers, learning objective, subject/entity and narrative significance;
- visual intent (e.g., relevant real clip, permitted image, contextual diagram, location map, annotated UI, original explanation animation, counter, comparison, chronology, reaction);
- asset reference, provenance, licensing status, matching confidence and fallback plan;
- caption words/times and safe placement, SFX/music cues, duration and verification results.

No generic unrelated footage or decorative static slides to mask missing media. If a real clip cannot be legally used, create a truthful original diagram or annotate an allowed visual rather than pretending it is source footage. Never invent asset rights or source timestamps.

## Editing rules, all subjects
- Hard cuts by default. Dissolve only for genuine elapsed narrative time. Fade to black only at the actual end, if useful. Never inject ornamental transitions.
- Purposeful movement within graphics is allowed. Use restrained non-linear easing on motivated UI/diagram motion, subtle overshoot only where appropriate. Do not animate each word or scene boundary by default.
- Captions always, synchronized to actual speech, readable on a phone, and kept off key evidence/faces and platform UI regions.
- Show the thing being discussed, when the voice discusses it. Maps for geography; timelines for chronology; counters for numbers; concrete examples and mechanism diagrams for abstract processes. No scene may be accepted merely because it is visually busy.
- Original hook -> understandable cause/effect narrative -> demonstrated conclusion/payoff. Correct facts first, jokes and tension where helpful, not forced.
- Meaningful cuts and sound cues, not a mandatory transition or effect quota. Honor visual rights and accurately label hypotheses, lore, legends and fact.
- Preserve a free offline Kokoro single-narrator path. Optional ElevenLabs must never be required for render, since experimental API access returned HTTP 402. Do not introduce paid-only dependencies.
- No production scheduler, credentials, publishing behavior or unrelated sibling repository files change from this document.

## JJK as regression fixture, not the only supported topic
Compare reference expectations on (1) canon/claim fidelity, (2) causal stakes, (3) named-character and action alignment, (4) verified visual sources or honest explanatory alternatives, (5) subtitle timing, (6) musical/SFX timing, (7) quality of Remotion scenes and (8) final rendered MP4. The legacy `experiment/anime-motion-kokoro` has an identified `mediaCenterY` bug. The later `claude/inspiring-goodall-8iff31` branch has JJK V4 scene and narration experiments and an unresolved voice/provider gate. Cherry-pick only individually validated modules, never the whole branch over the current renderer.

## Required generalization acceptance cases
1. JJK Culling Game, complex fictional rules and characters, canon-grounded, no falsely claimed licensed anime footage.
2. Traffic light vehicle detection, accurate physical mechanism and annotated road/loop/controller diagrams.
3. GPS positioning and arrival-time estimation, clearly distinguish satellites locating the receiver from navigation systems estimating routes, traffic and ETA.
4. A history/true-event explainer, date and location traceability with uncertainty labeled.

All four must use the SAME scene-planning, voice, rendering, caption and QA contracts with no topic-specific code edits. Review the actual full videos and representative mobile-size frames; do not claim readiness from passing syntax checks.

## Branch integration policy
- `main` remains the sole stable engine. Experiments stay recoverable until independently evaluated.
- `claude/inspiring-goodall-8iff31`: selectively port scene abstractions, diagrams, visual plans and QA after tests; avoid its mandatory voice/provider coupling and broad workflow overwrites.
- `experiment/anime-motion-kokoro`: archive as historical R&D after checking unique working primitives and the identified render bug; do not merge directly.
- `claude/gifted-wozniak-eeemiy`: old connection work, do not revive authorization flows without security review.
- `cleanup/workflows-readme-20261022`: review against already-present `main` documentation, do not duplicate.
- `integration/ecc-20261025` PR #4: manual, scoped skill integration; independently review draft acceptance and owner machine compatibility before merging.
- Never force, reset, delete or blindly merge divergent histories. Verify exact diff, current controls, tests and evidence; merge safe changes, leave unsafe changes tracked.

## Next implementation increments
A. Extract generic JSON scene plan schema and its validation tests without changing scheduling/publishing.
B. Add generic diagram/map/timeline/counter/UI primitives to the existing Remotion engine.
C. Port JJK-specific visual alignment features behind data-driven templates, not `if topic == JJK`.
D. Render JJK and traffic-light tests, evaluate mobile-scale frames, audio, captions and rights.
E. Add GPS and history regression fixtures, then assess production readiness and optional publisher path.

Completion definition: same pipeline produces 4 topic-distinct, source-grounded, engaging, playable vertical MP4s with verified captions, rights-safe visuals and human review, without custom editing code per episode.
