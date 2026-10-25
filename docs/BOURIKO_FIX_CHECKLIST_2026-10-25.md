# Bouriko video repair checklist (temporary)
Started: 2026-10-25. Preserve until every item is verified using an actual MP4, then write a permanent what/how/why final report in Venloud/claudevandam and only afterward delete this temporary file from Bouriko.

## Run comparison, evidence
- October 12 success: https://github.com/Venloud/bouriko-shorts/actions/runs/38196376914 ; older main, 65.94-second MP4, audio and video QA passed, visual-plan/beat steps present.
- October 25 failed: https://github.com/Venloud/bouriko-shorts/actions/runs/40219086406 ; main at 8fd80a18a7ca00c5e1afd43b4aafcb0da4501fec. Script and media stages ran; image fallback returned 401 disabled service account; Kokoro failed in spaCy tokenizer loading with OverflowError (Python int too large to convert to C ssize_t). Render and QA never ran. Tiny 10 KB artifact is NOT a valid video buffer item.
- Fail mechanism: spaCy tokenizer loading reached via misaki -> Kokoro KPipeline; investigate dependency incompatibility/version pins and repeated initialization, reproduce and test before checking this item.
- These are two runs on **main**, not the same Git commit or workflow behavior.

## Five-phase generalization roadmap
These are separate acceptance gates alongside F01–F17. Check a phase only when its implementation and tests are verified, not when documentation is written.

- [ ] **Phase 1: Universal scene planner.** Every scene records its purpose, narration, relevant footage, graphics, captions and audio cues. No topic-specific editing code. Verify with JJK, traffic lights, GPS and history fixture inputs.
- [ ] **Phase 2: Upgraded footage selection.** Reuse validated Horror Shorts media discovery, relevance scoring, clip trimming and licensing checks. Verify every chosen clip matches what the narrator actually discusses.
- [ ] **Phase 3: Integrated editing engine.** Add meaningful hard cuts, visual overlays, animated diagrams, caption styles, music mixing and contextual SFX to Bouriko's existing renderer. Follow Vandam's editorial rules and retain the owner publishing lock.
- [ ] **Phase 4: Learn through testing.** Use JJK as the storytelling and visual-quality regression baseline. Test unrelated topics with the exact same engine, document failures and improve reusable components instead of one-off hardcoded edits.
- [ ] **Phase 5: End-to-end validation.** Render complete videos, inspect frames, confirm narration/caption sync, verify media rights and repair findings. Acceptance requires actual MP4 evidence and a final report in Vandam.

## Owner-requested YouTube media acceptance test (NOT PASSED)
- [ ] Y01 Obtain a permitted real video source showing a car approaching a traffic signal. Record source URL and permission/license; personal ownership of a YouTube page is not by itself permission to reuse every third-party clip.
- [ ] Y02 Extract and store real `01_car_arrives.mp4` showing one car arriving, duration >0 and <=3.0 seconds.
- [ ] Y03 Extract and store real `02_light_turns_red.mp4` showing the light turning red, duration >0 and <=3.0 seconds.
- [ ] Y04 Extract and store real `03_light_turns_green.mp4` showing the light turning green, duration >0 and <=3.0 seconds.
- [ ] Y05 Extract and store real `04_car_leaves.mp4` showing car departure, duration >0 and <=3.0 seconds.
- [ ] Y06 Commit four verified clips to `assets/video_reference/traffic_light_detector/clips/`, with `review.json` recording actual visual confirmation, source and permission for every clip. Run `python tools/verify_traffic_light_clips.py`. **No partial success**.
- [ ] Y07 Validate optional Windows media retrieval worker with explicit user-side execution, authorized sources only, no cookies/secrets in GitHub and no uploads to social platforms.

## Current attempted fixes, not yet accepted
- 2026-10-25: `pipeline/voice.py` now initializes Kokoro once instead of once per line; the existing build adds pinned dependency and tokenizer preflight. **F02 is still unchecked** until complete workflow and audio are verified.
- 2026-10-25: `tools/verify_traffic_light_clips.py` added for four real videos and metadata. No clips were extracted from YouTube and no success is claimed.

## Tracked repairs
- [ ] F01 Restore successful working single-build pipeline from last passing behavior, maintaining disabled social publishing and no extra test workflows. Verify relevant visual-plan and beat steps.
- [ ] F02 Fix Kokoro spaCy tokenizer OverflowError with dependency pin/repro and instantiate synthesis pipeline once if appropriate. Prove real generated audio and successful full workflow.
- [ ] F03 Fix disabled/deleted Google AI image service account failure with non-paid alternate or safe licensed media fallback. Never expose tokens in logs.
- [ ] F04 Correct buffer detection to require a complete valid MP4 (manifest, QA receipt and file evidence), never count failed tiny artifact ZIP as finished buffer.
- [ ] F05 Add supplied traffic detection reference images to topic-specific asset folder with attribution/license provenance and correct purpose. First is **inductive vehicle detection roadway cutaway**, second is **multiple green traffic signal intersection**. Author supplied images; public reuse permission/source not established. Do not imply both illustrate the same sensor mechanism.
- [ ] F06 Remove mechanical ~0.65s pauses between narration lines; use timing-aware trims and optionally replace a portion of recovered ~8.72s with ONE relevant extra detail if it genuinely improves comprehension, not filler.
- [ ] F07 Fix captions exceeding 1080x1920 safe bounds, support automatic wrapping and useful typography size; verify real phone-size frames.
- [ ] F08 Remove excessive empty vertical space, improve framing and shot-specific responsive layouts without requiring animation.
- [ ] F09 Rank clips/photos by actual narrated concept and source evidence, avoid unrelated generic footage. Use first-party provided technical image where pertinent.
- [ ] F10 Disable repetitive YouTube yt-dlp anti-bot attempts in cloud; design optional owner-Windows machine source retrieval with legal-use, explicit opt-in, read-only intake, allowlists, no cookies pushed to GitHub, no media publishing.
- [ ] F11 Configure and verify Pexels and Pixabay keys from official dashboards as GitHub Actions secrets, never commit keys; test provider results and attribution/licensing. Check whether Coverr has a suitable authorized API plan before implementation.
- [ ] F12 Strengthen speech word timing and scene alignment, add transcript/speech alignment QA.
- [ ] F13 Create topic-independent animations and scene primitives, JJK/traffic/GPS/history must run through same code path.
- [ ] F14 Add unobtrusive ambient beds and relevant SFX with ducking, volume and clipping tests; avoid automatic whooshes, silence is allowed intentionally.
- [ ] F15 Add visual relevance, prolonged silence, frozen visuals, source rights, mobile caption clipping and negative-space QA; block false PASS.
- [ ] F16 Run one manual Bouriko Build test and inspect full MP4/audio/frames/logs; nothing uploaded to TikTok, YouTube or Buffer.com.
- [ ] F17 Independently verify all fixes, create Vandam permanent closing report with each fix, how, why, exact commits/tests, limitations and lessons. Only then delete this Bouriko checklist.

## Constraints
Owner-approved: single test workflow; social publishing remains disabled until explicit instruction. No account cookies, API secrets, authorization sessions, personal data or unlicensed media placed in git. Do not mark a checkbox based on a plan or syntax-only check. For every completion add commit and evidence in this file.
