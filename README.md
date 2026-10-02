# Bouriko

*A prehistoric mind trying to understand the modern world.*

Fully automated faceless shorts channel (TikTok + YouTube Shorts). Bouriko, an original cartoon caveman who
woke up in 2026, has wrong theories about everyday tech. His talking **Rock Phone** corrects him with the real,
fact-checked explanation, drawn as a hand-sketched diagram that draws itself.

- Spec and rules: [CLAUDE.md](CLAUDE.md)
- First build task: [FIRST_TASK.md](FIRST_TASK.md)
- Secrets and setup: [SETUP.md](SETUP.md)
- Notes for ChatGPT (reviewer): [CHATGPT.md](CHATGPT.md)
- Character image prompts: [CHARACTER_PROMPTS.md](CHARACTER_PROMPTS.md)

Status: standalone (starts from a snapshot copy of horror-shorts, never imports from it). Waiting on the owner's
go before the pipeline build starts. $0 budget, free tiers only.


## Current video format

Bouriko is channel branding; the Shorts are narrator-led. The production path uses free/permissioned real media, centered captions, real stock SFX, and a Remotion/React renderer. The old mascot/Rock Phone presenter format is no longer the default.

## Test

Open GitHub Actions -> Bouriko Build -> Run workflow -> enable the traffic-light test. Download the **bouriko-remotion-test** artifact and review the MP4 before expanding the renderer.

See CLAUDE_BOURIKO_NEXT_PASS.md for the current implementation handoff.
