# Anime Commentary: Viral-Style Training Guide (Originality-First)
Version: 2026-10-08
Scope: Bouriko Shorts anime commentary, reviews, recaps and educational explainers.
Status: Reference/training specification, NOT proof of implemented automation.

## Training sample and provenance
User supplied a transcript of a viral-style commentary on *Last One Standing* that compares it to *Solo Leveling*. This file extracts storytelling/editing techniques, not the creator's exact voice, phrases, insults, or script. The source transcript is a single anecdotal example: virality, view/like numbers, show identities, and on-screen footage have not been independently verified. Do not treat this transcript as a licensed media source, a canon fact sheet, or permission to reuse the creator's footage/audio.

## Why the sample holds attention
1. **Immediate provocative hook**: A strong comparison creates a reason to watch. The opening claims similarity between two shows and suggests the audience was fooled. Distinguish commentary/opinion from factual accusations; do not assert copying without evidence.
2. **Curiosity gap + promised test**: The narrator promises to inspect the actual show instead of merely complaining, setting up a test viewers want to see resolved.
3. **Fast verdict and reversal**: A short unexpected answer punctures the promise and creates a joke, then the story continues.
4. **Footage-locked narration**: The narrator describes the serpent fight as the serpent strikes, sword breaks, and legs are bitten. Every joke is tied to a visible event. No generic clip montage.
5. **Concrete comic analogies**: An ineffective sword becomes an absurdly weak object; a creature eating becomes exaggerated food commentary. This creates visual imagery, but analogy must not obscure what happened.
6. **Escalation**: Each new beat is worse than the previous one. Commentary moves from 'fight looks bad' to 'weapon fails' to 'character loses ability to escape'.
7. **Live reaction / self-correction**: The narrator admits uncertainty over pronunciation and makes a mistaken cross-anime name reference, then corrects it. Authentic uncertainty is more engaging than invented certainty. Never intentionally falsify canon as an unexplained joke.
8. **Comedic timing**: Pause or freeze the action for a reaction image, zoom, meme or short silence; then resume immediately at the relevant visual. Humor is a rhythm tool, not constant interruption.
9. **Conversational flow**: Short clauses, interruptions, questions, callbacks and tonal shifts make it sound like someone watching with the viewer, not reading an encyclopedia.
10. **Loop / callback ending**: The closing phrase returns to the opening comparison, giving the segment a memorable structure.

## What to transfer and what NOT to copy
TRANSFER: hook, curiosity, evidence-backed observation, stakes, escalation, contextual analogy, clip-to-line synchronization, controlled surprise, selective reaction meme, callback, and accessible explanations.
DO NOT COPY: exact lines, punchlines, running catchphrases, cadence fingerprint, identity, repeated signature insults, invented claims, or protected video/audio. Avoid derogatory language and slurs as an automatic style requirement. Original voice and independent humor are mandatory.

## Core editing principle: show what the narrator means
- Character named -> verified matching character still or licensed/eligible short shot; if unavailable, show a clear original diagram with identity and context, not just a name inside a decorative circle.
- Fight or physical action -> matching shot exactly during that line; cut to freeze-frame/zoom at the relevant impact, not before or after.
- Location or world-building -> labeled animated map; Japan map when discussing colonies.
- Numeric rule -> animated counter plus a concrete example that explains the consequence.
- Hidden motive or abstract lore -> causal diagram (action -> cursed energy -> ritual goal) with clear labels.
- Joke -> a relevant original reaction graphic or appropriately licensed meme; keep brief and return to source.
- Captions -> synchronized to spoken words, flexible placement, within platform-safe region, never cover important faces/maps/diagrams. Verify readability in a rendered frame.

## Narrative structure for a 45–65 second anime explainer
- 0–3 s: stakes-driven question, contradiction or compelling claim.
- 3–10 s: minimal context; identify who wants what and why.
- 10–35 s: 2–4 key rules/events, each illustrated with footage/diagram and concrete consequences; one situational analogy if useful.
- 35–50 s: escalation, twist or deeper motive. Reveal the connection between earlier details.
- 50–60 s: crisp takeaway that changes how the viewer understands the topic; optional original callback.
Keep the factual details necessary for understanding. Don't simply repeat previous narration or stack facts without causal links. A viewer should be able to answer: who is involved, what happens, why it matters, what is at stake?

## Culling Game application (creative example, NOT final canon-approved script)
Hook: "Imagine being thrown into a game where standing still can get you killed. That's the Culling Game."
Then introduce Kenjaku's plan with a character visual, Japan/ten-colony map, rules explained through examples (five points vs one; 100 points to propose a rule; 19-day penalty), Yuji and Megumi's stakes, and the larger cursed-energy ritual. Use a funny original analogy only if it clarifies a rule. Avoid making the game sound like an ordinary voluntary tournament. Fact-check the exact rule wording, chronology, and consequences against trusted canon references before rendering.
Creative tone: urgent, animated, invested, slightly playful, NOT nonstop shouting or a documentary monotone. TTS direction: purposeful emphases on danger/turning points, slightly quicker setup, micro-pause before reveal, varied sentence lengths, impact SFX at matched beats. Voice is acceptable; tune delivery and editing rather than replacing it.

## Proposed machine-readable scene fields
```json
{
  "scene_id": "s03",
  "narration": "original educational sentence",
  "learning_goal": "understand why 100 points matter",
  "claim_sources": [],
  "stakes": "rule change can affect survival",
  "visual_type": "animated_counter",
  "entity": "Culling Game",
  "asset_query": "verified character or scene query",
  "asset_id": null,
  "source_url": null,
  "rights_status": "pending",
  "anime_episode": null,
  "anime_timestamp": null,
  "match_confidence": null,
  "caption_safe_region": "validated",
  "joke_type": "optional situational analogy",
  "comedy_trigger_frame": null,
  "qa_status": "pending"
}
```
Source identifiers and licensing metadata must be real, never fabricated. A video with all generic text circles fails character visual relevance. User-supplied episode screenshots can be checked with trace.moe for scene identity, but trace.moe is reverse search, NOT a searchable licensed clip catalog. AniList/Jikan provide metadata and images, not episode footage or redistribution rights.

## Automation workflow (required global contract)
For every stage: generate -> QA -> save verified checkpoint -> next stage. On failure, log BAD with reason and preserve last good checkpoint. Next run first checks unfinished buffer and resumes from last verified stage. Store durable artifact refs, hashes, version and source provenance; do not treat GitHub ephemeral workspace as persistence.
Stages:
1. Story research/canon QA -> script checkpoint.
2. Story comprehension/hook originality QA -> narration plan checkpoint.
3. Clip/image discovery, character/episode/time matching, rights QA -> approved asset manifest checkpoint.
4. Voice synthesis and word-level timing QA -> audio checkpoint.
5. Remotion animated graphics, contextual meme/reaction timing and caption composition QA -> render checkpoint.
6. Final visual/audio/story QA -> release-ready artifact only if PASS.
Each stage must be actually implemented and tested before claiming it works.

## Concrete acceptance rubric (0–5 each; minimum 4 per category for publication)
1. **Accuracy**: facts, characters, episode/timestamps, causality verified.
2. **Clarity**: unfamiliar viewer can explain the main concept and stakes.
3. **Hook and payoff**: compelling opening, fulfilled promise, satisfying ending.
4. **Visual relevance**: named characters visibly represented when assets are available; action aligns with narration; no empty generic placeholders.
5. **Timing**: jokes and edits hit the correct event; pacing varies, no dead air.
6. **Original humor**: apt situational analogy and irony, not copied jokes or forced meme spam.
7. **Voice**: urgent but intelligible, expressive but not exhausting.
8. **Design**: vivid blue/red neon motion-graphic identity, legible responsive captions, platform-safe placement.
9. **Asset integrity**: traceable source, permitted use, no mislabeled clips or unverified provenance.
10. **Technical**: playable vertical video, no missing assets, sync errors, clipping or broken render.
Hard-fail regardless of score: unlicensed/unknown-rights footage in publishable output, false character identity, major canon error, text covering critical visual, inaccessible/missing artifact, or a generic-placeholder character scene presented as final.

## Suggested evaluation loop
Generate two ORIGINAL script variants; select the one with better comprehension, stakes, visual mapping and humor. Storyboard every line with its actual scene asset or diagram. Review representative frames and a full video. Log exact failures, save only passing checkpoints. Track viewer retention/hook drop-off only when real analytics exist; never invent engagement metrics.


## Training example 2: dense lore explainer with comprehension-driven CTA (2026-10-08)
The user supplied a second viral-style Culling Game explainer transcript. Treat it as a *structural reference*, not verified canon or text to copy verbatim. The sample walks through awakened sorcerers (including Junpei as an analogy), ancient reincarnated sorcerers (Sukuna comparison), Tsumiki's personal stakes, entry via colony barriers/shikigami, Kenjaku's larger Tengen-merger objective, points, 19-day pressure, rule changes, and why killing Kenjaku alone cannot simply shut down the game. **Research and verify each lore assertion before publishing**; some rules are paraphrased and the source may simplify mechanics.

### What this example teaches beyond the first
- **Explain the causal chain**, not a disconnected list: Kenjaku awakens players -> they face an entry deadline -> Tsumiki is endangered -> Yuji/Megumi act -> points enable rule changes -> changes might help -> restrictions make that difficult.
- **Define terms before using them**: awakened vs reincarnated ancient sorcerers, cursed objects, colony, shikigami, game master, binding vow, Tengen. Introduce no more than one unfamiliar concept per breath when possible.
- **Concrete familiar anchors**: use a named character as an example immediately after defining an abstract category; show that character in footage/still at that exact line.
- **Question/answer transitions**: "Who gets forced in?", "How do you enter?", "Why can't they just stop it?", "What do 100 points buy?" Each section answers the question it raises.
- **Consequences drive retention**: don't only say "19 days"; say why that countdown creates danger and removes the option to hide. Avoid exaggerating lore beyond evidence.
- **Payoff demonstrates understanding**: the end should let viewers apply the newly learned rules, not just recall numbers.

### User's original participatory ending / creative rule proposal
The owner (Venloud) suggests the final call to action: "Knowing the rules already in place, what new Culling Game rule would YOU add?" Present an ORIGINAL, clearly hypothetical rule as an example: "If a player defeats a curse participating in the game, any unspent points held by that curse transfer automatically to the victor." The owner's reasoning: a non-cooperative curse could otherwise leave useful points inaccessible. This is a creative suggestion, **not established canon**. Before using it, verify which curses qualify as players, whether automatic transfer is compatible with existing scoring/transfer rules, and whether the proposed rule would be rejected for disrupting the ritual. Explain the tradeoff in one line, then invite viewers to propose a better rule. This CTA is designed to reveal whether viewers understood constraints and stimulate informed discussion. Avoid presenting a speculative rule as a fact.

### Two distinct anime content modes
1. **Reaction/review mode** (example 1): fast jokes, irony, contextual meme pauses, live reactions, exact on-screen action matching.
2. **Lore/explainer mode** (example 2): causal clarity, terms and examples, character motivations, rule implications, progressive revelations, and a knowledge-testing CTA.
Both retain authentic personality, selective clip-to-line synchronization, vivid motion graphics, high stakes and an original voice. Do not force comedy into serious exposition or bury the rules beneath punchlines.

### CTA and learning-outcome quality gate
For a rule-based anime explainer, require: (a) audience can explain who is affected and why; (b) audience can describe what actions change their options; (c) one closing question requires applying a rule or identifying a loophole; (d) any example rule is visibly labeled hypothetical; (e) comments prompt doesn't depend on false facts or unsupported claims. Fail and revise if the CTA is a generic engagement demand disconnected from the explanation.

### Token-conscious current operating mode
Owner currently prefers **assistant-supplied final script** to be fed to Bouriko for video production, avoiding repeated paid AI script-generation calls. Save training examples as reference/rubric; do not claim an AI model was trained. The automated script-generation integration and global stage checkpoint system must be independently implemented/tested before reporting them complete.
