# Tool research — October 2, 2026

## OmniVoice
https://github.com/k2-fsa/OmniVoice
High-quality multilingual zero-shot TTS with voice cloning/design and controllable non-verbal tags. Candidate future narrator backend if it can run within the project's free CI/runtime constraints. For the first publish, keep the existing Kokoro path to avoid adding a heavy model dependency.

## Public-API
https://github.com/davemachado/public-api
Public API service for the public-apis project. Supports unauthenticated HTTPS requests and endpoints such as /entries, /random, /categories and /health. Useful as a discovery source for public/free APIs; not a required video-render dependency.

## Gstack
https://github.com/garrytan/gstack
AI engineering workflow/tooling for Claude Code. Candidate development/orchestration layer. Do not make the production video pipeline depend on it.

## Decision for Bouriko first publish
These tools are documented and considered, but Remotion + existing free-media + Kokoro + stock SFX remains the shortest path to a publishable first video. Add optional tools only after the first video renders, passes QA, and is ready for platform upload.
