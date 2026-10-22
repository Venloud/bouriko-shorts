# Bouriko workflows

Audited 2026-10-22. **`daily.yml` builds and uploads an artifact but does not publish.** `breaking-tech.yml` can publish immediately if a qualifying news item is detected. The workflow documentation describes configured behavior, not a successful real-world post.

| Workflow | Trigger | Role |
|---|---|---|
| `daily.yml` | schedule 15:00 UTC, manual | Daily build, render, QA and artifact upload only, no publishing step |
| `breaking-tech.yml` | schedule every 5 min, manual | Breaking tech watch; may generate, render and publish immediately when news is detected |
| `build.yml` | manual | Build a video without the daily schedule |
| `connect-tiktok.yml` | manual | One-time TikTok OAuth connection |
| `yt_check.yml` | manual | YouTube refresh-token check |
| `anime-clip-pull-test.yml` | manual | JJK experiment: clip retrieval probe (no publishing) |
| `anime-provider-connectivity.yml` | manual, or a push changing this file | JJK experiment: provider reachability (no publishing) |
| `anime-youtube-scene-test.yml` | manual, or a push to `main` changing this file | JJK experiment: authorized YouTube scene test (no publishing) |
| `jjk-culling-game-experimental.yml` | manual, or a push to `main` changing this file | JJK experiment: render preview (no publishing) |

The JJK experiment workflows stay isolated until the JJK video is approved. The JJK V4 pipeline work
(ElevenLabs narrator, visual plans, diagram and caption components) is on `claude/inspiring-goodall-8iff31`.
It is not merged because it makes ElevenLabs the only narrator, and `docs/JJK_PHASE1_STATUS.md` on that branch
records an unresolved ElevenLabs HTTP 402 blocker. See the Vandam integration debt register.

Safety note: Reviewing this README does not authorize altering these scheduled workflows or changing publishing behavior. Check each workflow source and current run evidence before any automation changes.
