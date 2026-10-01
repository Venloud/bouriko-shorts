# Handoff: start a new Claude chat with this

Paste or attach this file as the first message of a new chat. It's everything the new chat needs to pick up.

---

## Who I am and how I work
- I'm Van (GitHub **Venloud**). CS student (Python, Java, web), can debug, work a day job.
- **Budget is $0.** I already pay for Claude, ChatGPT and Replit. Never plan around a paid API/service.
- Keep answers short and direct. Hand me ready-to-paste prompts. Don't re-explain things I've done 2-3 times.
- Secrets go ONLY in GitHub repo secrets. Never ask me to paste keys in chat.
- TikTok accounts stay **Personal** (no Business account).

## How the AI team works
- **Claude Code** is the ONLY AI that edits/commits to my repos. It ends every change with an
  **UPDATE REPORT** block; I paste those here.
- **ChatGPT** is reviewer + web researcher; I paste its research here.
- **This chat (you)**: analysis, reviewing reports/videos/logs, and writing prompts for Claude Code and ChatGPT.
  Order of work matters: one focused change at a time so I can tell what fixed what.

## Project 1: Night Files (live)
- Repo **Venloud/horror-shorts** (public on purpose so ChatGPT can read it). GitHub Actions, all free.
- Faceless AI horror / true crime / legends shorts. YouTube channel **@MonkeyTellsStories**
  (display name to be changed to "Night Files"); TikTok @istwatrajiks (drafts via API, I post manually).
  YouTube auto-uploads public via Data API.
- Architecture: build.yml ("Build video (buffer)") makes videos into a GitHub Release "buffer";
  daily.yml posts 2/day (11:40 AM, 8:40 PM New York). Test builds are zero-config: tick "test", Run
  (reuses the last story/images; `fresh_images` checkbox for new ones).
- Stack: Gemini (free) -> Groq fallback, Kokoro TTS (am_michael 1.1), Cloudflare FLUX (10k neurons/day,
  resets 8 PM NY) -> HF ZeroGPU -> SD-Turbo; Pexels/Pixabay/Wikimedia/Smithsonian real media; FFmpeg render;
  visual modes classic/fast/analog (A/B); QA gate (length, visual variety, frozen-frame check).
- Recent state (Sept 30, 2026):
  - Fixed: frozen-frame bug in fast mode (38ec5bc); Gemini 503/per-minute limits no longer treated as
    daily quota; Groq TPM waits instead of switching topics; notify crash (26234ae).
  - Videos now **61-68 s** (TikTok Creator Rewards needs >1 min) (5238fc5).
  - Experimental **cutout render mode** committed off by default (ca62667); cutout test build still pending.
  - Next: test build with fresh_images after 8 PM, then cutout test.
- Content rules: I'm Christian: no occult/Illuminati/all-seeing-eye/floating-eyes imagery unless the video is
  about that topic (hooded figures OK). Never depict real victims' bodies. Adults only. Real people: normal
  faces matching public facts, consistent across shots. No copying others' characters/IP.

## Project 2: Bouriko (new, parked until Night Files' cutout test passes)
- New repo from the starter zip (**bouriko-shorts**): CLAUDE.md = full spec, FIRST_TASK.md = the build prompt
  for Claude Code (don't send until unparked).
- Faceless tech shorts. **Bouriko** (boo-REE-ko; Kreyol "bourik" = donkey): an original cartoon caveman who
  woke up in 2026. Brand line: "A prehistoric mind trying to understand the modern world."
- Look: lean, oversized head, messy dark-brown hair, stubble, **light fair skin**, **electric-blue stripe on
  both cheeks**, stone necklace with a saber-tooth fang, one-shoulder **striped saber-tooth pelt (no spots)**,
  club used as a pointer, bare feet. Hand-drawn iPad sketch style, black ink, flat colors.
- **Rock Phone**: his talking stone slab (calm, dry, deadpan). It's the explainer; no second character.
- Rule: modern tech always glows electric blue; everything prehistoric = ink + earth tones.
  Gadgets per episode only, generic (no logos). Avoid resembling GEICO caveman, Flintstones, Croods/Grug,
  Wojak grug, Captain Caveman. Don't brand as "Caveman Explains".
- Voice: Bouriko speaks full correct sentences (no "me smart" grammar); his ideas are wrong, not his grammar.
- Format: hook = absurd wrong theory (<15 words) -> Rock Phone deadpan correction -> real explanation + one
  surprising fact -> Bouriko takes it one step too far, Rock Phone gets the last word. 8-10 lines, 61-68 s.
- Pillars: hidden tech (strongest), explainers, fun facts, gaming tech, tips (Bouriko teaches), tech finds
  (rocks out of 10), comparisons, tech news (fresh, 24-48 h expiry).
- Facts: official docs -> gov/university -> reputable tech press -> Wikipedia; fact ledger + citations.
- Pending for me: regenerate the light-skin master + pose sheets (prompts in CHARACTER_PROMPTS.md), handle
  claimed = @bourikoh (TikTok personal + YouTube, same handle; plain @bouriko is not ours), make separate free API keys so it doesn't share Night Files' quotas.

## Parked ideas
- **Cashman**: finance channel, original brick-toy-style Black superhero (money-green suit, visor with
  $100-bill-blue lenses, "$" logo, blue ring). Separate repo, on hold.
- Spanish Night Files, Bible-verse channel.
