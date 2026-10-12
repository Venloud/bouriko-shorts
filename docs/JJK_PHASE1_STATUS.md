# JJK Culling Game: Phase 1 status (2026-10-12)

## Branches
- `experiment/anime-motion-kokoro`: the old JJK experiment code (60 commits). Its BourikoShort.tsx
  has an escaped-newline bug that comments out `mediaCenterY`, so media scenes can't render.
- `main`: normal Bouriko + JJK *launcher* workflows that check out the experiment branch.
- Decision: JJK now lives on one branch (`claude/inspiring-goodall-8iff31`): `experiments/jjk/`
  + the shared renderer. The JJK workflow is manual only and runs the branch it is dispatched on.
  The experiment branch can be archived once this is merged.

## Pipeline (manual workflow `jjk-culling-game-experimental.yml`)
jjk_story.py (fact-locked v2 + fact ledger) -> prepare_jjk_media.py (character images, media plan;
replaces pipeline/media.py) -> visual_plan.py --strict -> voice.py -> sfx.py -> remotion_prepare.py
-> Remotion -> qa.py --frames 8. Never publishes.

## Script facts
Every rule is cited to the manga chapter/page via the Jujutsu Kaisen Wiki "Culling Game" page
(ch. 143 pp. 18-19 / ep. 49 for rules 1-8). Corrections vs draft v2: rule 7 is "must accept unless it
has a long-lasting effect on the game" (not "can't propose ending the game"); removal killing the
player is Tengen's statement (ch. 146). The curse-points rule is labelled FAN PROPOSAL / NOT CANON.

## Still missing
- ElevenLabs: HTTP 402 "Free users cannot use library voices via the API" for voice
  6OzrBCQf8cjERkYgzSg8 (eleven_v4 and eleven_v3). Needs $5 of credits / Starter, or a voice the
  account owns. Until then Kokoro (am_michael, speed 1.15) is used. 0 credits spent.
- Footage: none supplied in assets/anime/jujutsu_kaisen/footage/ (none used, none fetched).
- Character art (AniList) is review-only, not publish-cleared.
- Source tier: fan wiki citing manga pages; a reviewer with the volumes should confirm chapter pages.
