# Bouriko: project spec for Claude Code

Read this fully before changing anything. You (Claude Code) are the ONLY AI that commits to this repo.
ChatGPT reviews and researches; the owner relays. End every change with an **UPDATE REPORT** block
(commit, files changed, new secrets/config, what you tested, not tested/risks, how to check, next step).

## What this is
A fully automated, faceless TikTok + YouTube Shorts channel starring **Bouriko**, an original cartoon caveman
who wakes up in 2026 and tries to understand the modern world. Handle: **@bourikoh** (TikTok + YouTube;
not @bouriko). Brand line:
**"A prehistoric mind trying to understand the modern world."**
Starts with tech; can later expand to space, science, money, history and inventions without a rebrand.

Sister project: **Night Files** (repo Venloud/horror-shorts). Reuse its proven architecture and code where it
fits (build -> buffer release -> publisher, Kokoro TTS, word-level captions, QA gate, retry/quota handling,
YouTube Data API upload, TikTok drafts, ntfy notifications). Bouriko is standalone: it starts from a snapshot
copy of horror-shorts and never imports from it or pushes to it; the two repos evolve independently.
Its experimental **cutout render mode** (pose set + rembg + compositor) is the base for Bouriko's renderer.

## Owner rules (hard constraints)
- **Budget is $0.** Free tiers and open-source only. Never design around a paid API, credits or scheduler.
- **TikTok account stays Personal** (no Business account). TikTok = drafts via API; owner posts manually.
  YouTube Shorts = auto-upload public via the YouTube Data API.
- Secrets live ONLY in GitHub repo secrets. Never print them in logs.
- Everything automated. The owner should never fill workflow inputs for a normal run.
- Test builds are zero-config: tick "test" and Run. They reuse the last story/assets; a single
  `fresh` checkbox (default off) forces new generation.
- **Free quotas are shared with Night Files if the same keys are used.** Prefer separate free keys
  (own Gemini/Groq/HF accounts). Bouriko should need little or no Cloudflare image generation.
- Videos must be **61-68 s** total (TikTok Creator Rewards pays only on videos over 1 minute).
  Never output under 61 s. Script ~140-150 words across both voices.

## The character (locked)
- Name: **Bouriko** (boo-REE-ko). Kreyol inside joke: *bourik* = donkey.
- Lean build, oversized head, short messy dark-brown hair, light stubble.
- Skin: **warm tan**, as on the final master sheets in assets/reference.
- **One electric-blue stripe on EACH cheek**, symmetrical, in every pose.
- Stone-bead necklace with one curved **saber-tooth fang** in the center.
- One-shoulder **saber-tooth cat pelt**: tan-orange fur, 5 bold dark-brown stripes, stitched edges, rope belt.
  **No spots** (spots = Flintstones).
- Bare feet. Smooth wooden club he uses as a **pointer**.
- Expression: curious and thoughtful, NOT dumb-looking.
- **Rock Phone**: a flat gray rock slab. Back = glowing blue camera dot; front = glowing blue app icons.
  It TALKS (see below).
- **Color rule:** modern tech ALWAYS glows electric blue. Everything prehistoric = black ink + earth tones.
- Gadgets per episode only (generic earbuds, smartwatch, smart glasses, headphones, VR headset), usually
  worn wrong. Never part of his base design. **No logos, no brand wordmarks, no exact product copies** in
  images. Real product names are fine in narration and titles.
- Must NOT resemble: GEICO caveman, Flintstones, The Croods/Grug, Wojak grug, Captain Caveman.
- Don't brand as "Caveman Explains" (crowded niche).

## Voices (Kokoro, two voices)
- **BOURIKO**: rougher male voice. Speaks **full sentences**. His IDEAS are wrong, never his grammar.
  NO "me smart / caveman discover" speech (that's Grug/GEICO).
  Good: "I believe there is a very small man inside this phone, and he is tired."
- **ROCK PHONE**: calm, dry, deadpan AI-assistant voice. The fact anchor and the explainer in most formats.
  Rock Phone never states anything the source doesn't support.
- Rock Phone's screen glows/pulses while it speaks; Bouriko's mouth moves (Rhubarb visemes) while he speaks.

## Episode format (every video)
1. **Hook (0-3 s):** Bouriko's wrong theory, confident and absurd, under 15 words.
   Never open with "I have discovered".
2. **Correction (3-6 s):** Rock Phone: short deadpan correction. The sketch starts drawing itself.
3. **Explanation (~35-45 s):** the real mechanism + one surprising extra fact viewers didn't expect.
4. **Ending (last ~4 s):** Bouriko gets it, then takes it one step too far (new wrong idea). Rock Phone
   gets the dry last word.
- Max 8-10 lines total. No filler lines ("Correct." "Exactly." "So...?"). Every line adds a fact or a joke.
- Each line carries a `[VISUAL: ...]` note for the renderer.
- Title pattern: "Bouriko vs. <thing>". End card: "Follow for more" + channel name.

## Content pillars (rotation)
| Pillar | Who explains | Notes |
|---|---|---|
| Hidden tech (everyday things that are secretly tech) | Rock Phone | Strongest series. Topic list in data/topics.json |
| Explainers (how X works) | Rock Phone | |
| Fun facts | Rock Phone tells, Bouriko reacts | |
| Gaming tech | Rock Phone, Bouriko playing | |
| Useful tech / tips | **Bouriko teaches** ("Rock Phone taught me this. Now I teach you.") | Roles flip |
| Tech finds (gadgets/apps) | Bouriko shows, Rock Phone adds facts | "rocks out of 10" rating |
| Comparisons | Rock Phone specs, Bouriko picks | |
| Tech news | Rock Phone reports, Bouriko reacts | Must be fresh; skips the buffer queue, expires after 24-48 h |

Suggested rotation to start: hidden, explainer, tip, hidden, fun_fact, gaming, hidden, finds.
News and comparisons come later.

## Facts (non-negotiable)
- Source hierarchy: **official docs/support pages -> government/university/institution -> reputable technical
  publication -> Wikipedia -> other secondary.**
- Extract a fact ledger from the source BEFORE writing; check the script against it BEFORE TTS
  (same fact-lock idea as Night Files). Store citations per video in history.
- Verify the exact mechanism before writing the joke; similar-looking devices use different sensors.
- If a claim isn't established by the source, Rock Phone doesn't say it as fact.
- News: RSS only finds the story; open the original article/official announcement before writing.

## Visual style
- Hand-drawn iPad sketch look: black ink linework, flat colors, off-white paper background.
- Renderer (planned): layered/cut-out Bouriko poses (rembg) + Python/FFmpeg compositor,
  Rough.js/SVG stroke-reveal for "drawing itself" diagrams, code-drawn screens/labels,
  Rhubarb Lip Sync for mouth shapes, fonts Patrick Hand / Permanent Marker / Caveat (OFL).
- Cuts or a new element every 2-4 s. No frozen stretches (reuse Night Files' visual-variety QA gate).
- Pose library comes from the owner's reference sheets (assets/reference). Plain white background poses
  for clean cut-outs; backgrounds added by the compositor.

## Free tool stack (all verified free/open)
Kokoro TTS (Apache-2.0), Rhubarb Lip Sync (MIT), rembg (MIT), Rough.js (MIT), FFmpeg, Pillow,
Gemini API free tier + Groq free tier (writer/critic with retry + per-model quota handling),
HF ZeroGPU Spaces (optional), GitHub Actions + Releases (buffer), YouTube Data API, TikTok Content Posting
API (drafts), ntfy (alerts). Optional: Chatterbox TTS (MIT).

## Status
Standalone; does NOT wait for Night Files' cutout test. Character master is final (assets/reference).
Waiting on the owner's go: don't start FIRST_TASK.md until the owner says so.
