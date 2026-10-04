# Media Library & Clip Sources Research

Last researched: 2026-10-04

## Purpose

This document is the handoff for the next automation session. The goal is to give all video bots one reusable media-source strategy for stock footage, archival footage, memes, reactions, streamer clips, anime clips, and sound effects.

The key design rule is: **the script asks for a visual intent, not a specific website.** The media engine chooses the best eligible provider, records provenance, downloads the asset when permitted, and hands it to the renderer.

Example visual intent:

```json
{
  "type": "reaction",
  "query": "shocked streamer",
  "duration_seconds": 2.5,
  "placement": "after_punchline"
}
```

---

## 1. Stock video and image libraries

### Pexels
Website: https://www.pexels.com/
API: https://www.pexels.com/api/

Use for:
- general stock video
- technology
- people
- locations
- lifestyle
- backgrounds and B-roll

Automation:
- API search is the preferred route.
- Keep provider metadata with every asset.
- API access is free, but current availability and key issuance can change.

Role: **primary stock provider.**

### Pixabay
Website: https://pixabay.com/
API docs: https://pixabay.com/api/docs/

Use for:
- stock video
- images
- illustrations
- backgrounds
- generic B-roll

Automation:
- Very useful fallback when Pexels has no match.
- Store the source URL and license-related metadata.

Role: **primary stock fallback.**

### Coverr
Website: https://coverr.co/
API docs: https://api.coverr.co/docs

Use for:
- short stock video
- cinematic backgrounds
- technology/lifestyle footage

Automation:
- Investigate current API eligibility and usage restrictions before production use.

Role: **secondary stock provider.**

### Mixkit
Website: https://mixkit.co/

Use for:
- manual stock footage
- music
- sound effects

Automation:
- No reliable public production API was established in this research.

Role: **manual library / fallback.**

---

## 2. Open and archival media

### Openverse
Website: https://openverse.org/

Use for:
- openly licensed images
- openly licensed audio
- broad Creative Commons discovery

Automation:
- Strong candidate for a license-aware fallback search provider.
- The engine should retain the individual work's license instead of assuming the whole catalog has one license.

Role: **open-license discovery layer.**

### Wikimedia Commons
Website: https://commons.wikimedia.org/

Use for:
- historical footage
- diagrams
- photographs
- public-domain media
- scientific material
- places and people

Automation:
- Search through Wikimedia APIs.
- License metadata is attached to individual files.
- Build a filter that rejects unclear licenses for automated publishing.

Role: **high-value factual/archival source.**

### Internet Archive
Website: https://archive.org/

Use for:
- old films
- historical footage
- public-domain collections
- documentaries
- commercials
- archival video
- audio

Automation:
- Excellent long-tail source.
- License/public-domain status must be checked at the individual item level.
- Don't assume every Archive item is reusable.

Role: **archival super-library.**

### Library of Congress
Website: https://www.loc.gov/

Use for:
- historical photography
- archival video
- government records
- historical events
- culture and technology history

Automation:
- API/search infrastructure makes it a strong factual-video source.
- License/rights status needs to be retained per item.

Role: **authoritative historical source.**

### NASA Image & Video Library
Website: https://images.nasa.gov/

Use for:
- launches
- spacecraft
- astronauts
- satellites
- Mars
- Earth
- engineering
- science

Automation:
- Excellent for tech/science videos.
- Particularly useful for Bouriko and Night Files.

Role: **specialized science/space provider.**

### NOAA and other U.S. government media
Website: https://www.noaa.gov/

Use for:
- weather
- ocean
- climate
- storms
- Earth science

Automation:
- Candidate source for specialized factual videos.
- Rights should still be recorded from the source page.

Role: **specialized factual provider.**

---

## 3. Meme, reaction, and viral clip libraries

These should be a separate class from stock footage.

### KLIPY
Website: https://klipy.com/
Docs: https://docs.klipy.com/
GitHub: https://github.com/KLIPY-com/Klipy-GIF-API

Important capabilities:
- GIF API
- Sticker API
- Clip API
- Meme API

Clip API:
- short video clips
- movie/TV/viral-moment database
- search
- trending endpoints
- maximum clip length currently documented as 10 seconds

Meme API:
- famous/trending memes
- search
- preview
- share
- current-events and internet-culture meme inventory

Automation:
- Strong candidate for automated reaction insert selection.
- Production access/limits and media-use terms must be verified before scale.
- Preserve provider metadata and any required attribution.

Role: **primary automated meme/reaction provider candidate.**

### Vlipsy
Website: https://vlipsy.com/

Use for:
- reaction clips
- famous video memes
- movie/TV moments
- viral expressions
- short clips with sound

Best use:
- manual editing and clip discovery

Automation:
- No dependable public API was established during this research.

Role: **manual meme/reaction library.**

### MemeScreens
Website: https://memescreens.com/

Use for:
- reaction clips
- green-screen clips
- meme inserts
- creator/streamer reactions
- recognizable reaction moments

Best use:
- manual editing
- quick punchline inserts

Automation:
- No dependable public API was established.

Role: **manual reaction library.**

### GIPHY Clips
Website: https://developers.giphy.com/docs/clips/

Use for:
- short video reactions
- viral/pop-culture clips
- sound-enabled short clips

Automation:
- Clips API exists.
- Access may require approval.

Role: **secondary reaction/video API candidate.**

### Twitch Clips API
Docs: https://dev.twitch.tv/docs/api/clips/

Use for:
- streamer reactions
- gaming moments
- funny live reactions
- specific creator moments
- game-related clips

Automation:
- Official API.
- Strong fit for streamer-content discovery.
- Query by streamer/game and retrieve clips.
- Individual clip reuse still requires rights/use judgment.

Role: **primary streamer-content discovery API.**

---

## 4. Anime-specific sources

### Blitz Anime & Manga API
GitHub: https://github.com/blitzlabx/blitz-anime-api

Capabilities documented by the project:
- search across multiple anime/manga content providers
- AniList, Jikan, Kitsu metadata
- direct stream resolution
- HLS/MP4
- episode downloads
- cross-source mapping
- self-hosting on free hosting tiers

Endpoints include:
- /api/v1/providers
- /api/v1/search
- /api/v1/content
- /api/v1/stream
- /api/v1/download/video
- /api/v1/meta/search
- /api/v1/meta/info
- /api/v1/meta/stream

Important:
- This is not a rights-cleared anime-footage library.
- It is primarily useful for discovery/stream resolution.
- For public publishing, individual anime footage can still be copyrighted.

Role: **automated anime source/resolver for Kairo and other anime bots.**

### anime-sdk
GitHub ecosystem: https://github.com/hexxt-git/anime-sdk

Use for:
- cross-provider anime source resolution
- unified anime IDs
- provider abstraction
- metadata/source mapping

Role: **underlying reusable anime abstraction.**

### animeclips.online
Website: https://animeclips.online/

Use for:
- manual anime editing
- pre-cut anime clips
- MP4 downloads
- finding precise scenes quickly

Important:
- Excellent manual workflow.
- The site's terms prohibit unauthorized scraping/mass downloading/integrations.
- Do not build an automated scraper against it unless permission is obtained.

Role: **manual anime clip library only.**

### trace.moe
GitHub: https://github.com/soruly/trace.moe

Use for:
- reverse-search an anime scene from an image/screenshot
- identify anime/episode/approximate timestamp

Important:
- It is a scene-identification engine, not a general downloadable clip library.

Role: **scene lookup / exact-scene identification.**

---

## 5. Sound-effect libraries

### Freesound
API docs: https://freesound.org/docs/api/

Capabilities:
- text search
- metadata
- similar sound search
- audio feature search
- packs/users/sounds
- API v2
- OAuth2 for certain operations

Automation:
- API credential required.
- Every downloaded sound should retain its individual license/creator metadata.

Role: **large SFX discovery source.**

### Lots of Sounds
GitHub: https://github.com/lotsofsounds/free-sound-effects-api

Free public sample API:
- no account/API key for the curated sample surface
- searchable sample list
- temporary sample stream URLs
- structured JSON
- curated CC0 sample collection

Current documented sample endpoints:
- GET /api/v1/sounds/sample
- GET /api/v1/sounds/sample/{id}/stream

Full catalog:
- authenticated API
- larger search/download capabilities

The repository also includes:
- JavaScript example
- Python example
- AI-agent skill
- MCP server integration

Role: **easy no-key SFX source and strong agent-friendly option.**

---

## 6. Free/open-source video-clipping and discovery tools

### OpenClip
GitHub: https://github.com/aionixOS/Openclip

Purpose:
- automatically identify interesting moments in long videos
- local/self-hosted clipping
- can combine transcript, audio, visual activity and reaction signals
- exposes API-style workflow

Potential use:
1. ingest an allowed source video
2. analyze transcript/audio/video
3. score candidate moments
4. output short clips
5. attach them to a visual-intent slot

Important:
- Use only source videos we are allowed to download/edit.

Role: **automatic clip finder.**

### Clips Studio
GitHub: https://github.com/ColinGPT9/clips-studio

Purpose:
- local Opus Clip-style workflow
- score candidate clips
- consider text/audio/visual activity/reaction/engagement signals
- expose clip-processing workflow

Role: **alternative local clip-mining engine.**

### web-media-getter
GitHub: https://github.com/connerkward/web-media-getter-skill

Concept:
- media abstraction layer for agent workflows
- searches multiple web-media providers
- can return source/license metadata
- can download selected media
- can generate attribution information

Providers/project architecture investigated:
- Openverse
- Wikimedia
- Internet Archive
- NASA
- Library of Congress
- Pexels
- Pixabay
- KLIPY
- GIPHY

Role: **architecture reference for our unified media provider layer.**

---

## 7. Metadata providers

These are not clip libraries, but they matter for choosing visuals.

### AniList
Website: https://anilist.co/
API: GraphQL API

Use for:
- anime titles
- genres
- popularity
- related entries
- seasonal information
- characters

Role: **anime metadata and story-context layer.**

### MyAnimeList
API: https://api.myanimelist.net/v2

Use for:
- scores
- popularity
- rankings
- member counts
- anime/manga comparisons
- release/status information

Role: **secondary anime metadata source.**

### Jikan
Website: https://jikan.moe/

Use for:
- MyAnimeList-derived metadata
- anime search/info
- characters and related data

Role: **metadata fallback, especially useful when direct MAL auth is inconvenient.**

---

# 8. Recommended provider hierarchy

## SAFE / LICENSE-FIRST POOL

Preferred whenever the visual concept can be satisfied here:

1. Pexels
2. Pixabay
3. Openverse
4. Wikimedia Commons
5. NASA
6. Library of Congress
7. Internet Archive, only when item rights are clear
8. Other government/public-domain sources
9. Lots of Sounds CC0 samples for SFX

## SPECIALIZED POOL

1. Blitz Anime / anime-sdk
2. Twitch Clips
3. KLIPY
4. GIPHY Clips
5. trace.moe for scene identification

These require more careful rights/terms handling.

## MANUAL POOL

1. animeclips.online
2. Vlipsy
3. MemeScreens
4. Mixkit

These are useful when the editor intentionally chooses a clip instead of the bot pulling it automatically.

---

# 9. Media-provider interface we should build

The automation should NOT hard-code websites into the script generator.

Create a common provider contract:

```text
search(intent)
rank(results, intent)
validate(result)
download(result)
get_metadata(result)
get_license(result)
```

Every returned asset should be normalized into:

```json
{
  "provider": "pexels",
  "provider_asset_id": "...",
  "title": "...",
  "source_url": "...",
  "download_url": "...",
  "creator": "...",
  "license": "...",
  "license_url": "...",
  "duration_seconds": 4.2,
  "media_type": "video",
  "query": "computer server room",
  "usage_class": "licensed_stock"
}
```

---

# 10. Visual-intent types

The LLM should produce one of these instead of directly naming a provider:

- stock_video
- stock_image
- archival_video
- archival_image
- diagram
- anime
- reaction
- meme
- streamer_reaction
- sfx
- generated_visual
- youtube_cc
- manual_asset

Examples:

```json
{
  "type": "streamer_reaction",
  "query": "shocked streamer",
  "duration_seconds": 2
}
```

```json
{
  "type": "archival_video",
  "query": "early computer laboratory",
  "duration_seconds": 4
}
```

```json
{
  "type": "anime",
  "query": "dramatic sword fight",
  "duration_seconds": 3
}
```

---

# 11. Ranking strategy

For each candidate, calculate a score based on:

- semantic relevance
- visual relevance
- duration fit
- resolution
- aspect-ratio suitability
- audio availability
- source reliability
- license/use class
- duplicate penalty
- previous performance
- provider priority

Suggested order:

```text
relevance
+ license confidence
+ quality
+ timing fit
+ source reliability
+ novelty
```

Do not simply choose the first API result.

---

# 12. Provenance and audit trail

Every downloaded asset should create:

```json
{
  "asset_id": "uuid",
  "provider": "pixabay",
  "provider_asset_id": "123456",
  "source_url": "...",
  "creator": "...",
  "license": "...",
  "license_url": "...",
  "query": "...",
  "selected_for": "video_scene_07",
  "downloaded_at": "...",
  "hash": "sha256..."
}
```

Store this in a manifest such as:

```text
output/media_manifest.json
```

For manual assets, allow:

```json
{
  "manual": true,
  "source_url": "...",
  "rights_note": "Manual/editor-selected source"
}
```

---

# 13. Copyright / fair-use handling

Do not implement a fake automatic "fair use" approval.

The pipeline should instead classify source material:

- licensed / clearly permitted
- public domain
- Creative Commons, verify exact license
- platform/API content with provider terms
- copyrighted commentary/reaction candidate
- unknown

The bot can prioritize low-risk sources automatically.

For copyrighted clips used for commentary/review, keep clips short and make the original narration/commentary the actual substance of the video. Still treat this as a rights-risk category, not an automatic legal clearance.

---

# 14. Recommended architecture for ALL bots

```text
                   SCRIPT
                     |
                     v
              VISUAL INTENT
                     |
                     v
              MEDIA ORCHESTRATOR
                     |
        +------------+-------------+----------------+
        |            |             |                |
       STOCK       ARCHIVE       REACTION          ANIME
        |            |             |                |
   Pexels etc.   IA/Wiki/NASA   KLIPY/Twitch    Blitz
        |            |             |                |
        +------------+-------------+----------------+
                     |
                     v
                RANK + QA
                     |
                     v
                DOWNLOAD
                     |
                     v
              MEDIA MANIFEST
                     |
                     v
                  REMOTION
```

This should be reusable across:

- Bouriko
- Kairo
- Night Files
- Horror Shorts
- future bots

---

# 15. Tomorrow's implementation order

### Phase 1
Create a shared provider abstraction.

### Phase 2
Add:
- Pixabay
- Pexels
- Openverse
- Wikimedia
- Internet Archive

### Phase 3
Add:
- KLIPY
- Twitch Clips
- GIPHY Clips

### Phase 4
Connect:
- Blitz Anime API
- anime-sdk
- trace.moe

### Phase 5
Add:
- Freesound
- Lots of Sounds

### Phase 6
Add ranking + provenance + license classification.

### Phase 7
Wire the same media engine into all bots.

---

# Current recommendation

For automated production, prioritize:

**Pexels → Pixabay → Openverse/Wikimedia → KLIPY → Twitch → Blitz Anime → generated fallback**

For manual editing:

**animeclips.online → Vlipsy → MemeScreens → Mixkit**

For sound effects:

**Lots of Sounds → Freesound**

For archive/factual footage:

**Internet Archive → Wikimedia → Library of Congress → NASA/NOAA**

The goal is not to force every video to use external clips. The goal is to give every script scene the best available visual option while preserving provenance and keeping risky sources separated from license-clear sources.
