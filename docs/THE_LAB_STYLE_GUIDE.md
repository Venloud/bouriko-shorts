# The Lab style guide: drawing timing and storytelling

Written 2026-11-06 from nine sample videos and four recent Lab plans. Nothing here changes The Lab's code yet.

Study only: use these videos to learn technique. Never copy their footage, characters, art or designs. The Lab keeps its own blueprint look and Tory.

## The short version

1. One idea, one picture.
2. Start the picture as its key word is spoken, not before and not long after.
3. Build on the same board, then clear it when the idea changes.
4. Vary the rhythm: quick builds, then one held picture for the point that matters.
5. Open with a question or impossible situation. Close with a turn, not a summary.

## Timing rules for The Lab

These are recommended starting values, to be tested on real Lab renders.

| Rule | Starting value | Why |
|---|---|---|
| Picture starts | 0 to 0.2 s after its key word begins | In most samples, visual changes sat close to a spoken phrase |
| Drawing finishes | Within about 1.2 s | The picture should be readable while the sentence is still about it |
| Quick build beat | 1.5 to 3 s | Adds one element to the current board |
| Normal beat | 3 to 5 s | The Lab's current median is 3.6 to 4 s, so this already fits |
| Held beat | 6 to 8 s, about once every 20 to 30 s | Gives big points room. The Lab's longest beat is about 6 s |
| Word labels | 1 to 3 words | Label the key idea, do not caption the sentence |
| Narration pace | 150 to 175 words per minute | Matches most of the short explainers measured |

## How to tell the story

1. **Hook, first 3 to 5 seconds:** ask a direct question or put the viewer in a situation. Examples from the samples: "Are you free?" and "Imagine you're watching a runaway trolley".
2. **Setup:** introduce one person, object or rule. Draw it simply.
3. **Build:** add one step per beat, keeping earlier drawings on screen when they still matter.
4. **Turn:** show the problem or contradiction. This is the held beat.
5. **Payoff:** end on a consequence or open question. Avoid repeating what was just said.

For a 60-second video, aim for about one setup beat, three to five build beats, one held turn and one payoff.

## What each channel teaches

**After Skool: the growing board.** A hand draws in view on white, and the drawing grows sideways into one long scene. Words sit beside pictures, and color is added after the line art. Lesson for The Lab: stop replacing the whole picture on every beat. Move across a growing blueprint when the topic continues.

**60 Second Adventures: simple line art and plain gags.** It has one fixed background, simple black line drawings and short handwritten labels with arrows. Characters return in the same room as the idea develops. Lesson: reuse one room or object throughout, and use a small visual joke for the absurd moment.

**TED-Ed: one metaphor per idea.** The trolley sample uses simple shapes for people, strong color changes between ideas and very sparse text. Lesson: reduce a person or concept to the simplest symbol that works, and let a background color change mark a new section.

**Kurzgesagt: one world, one recurring character.** The free will sample follows one small character through a consistent world and turns abstract ideas into actions. Lesson: Tory should do something in the scene, not just stand beside it. Keep a fixed palette and a fixed character scale.

## Suggested Lab changes, in priority order

These need Venloud's approval and a separate test.

1. **Growing board:** when consecutive beats share a subject, add to the current drawing rather than replacing it.
2. **Held beats:** mark the turn in the script and give it 6 to 8 seconds.
3. **Tory interaction:** have Tory point at, carry or react to the drawing.
4. **Section color:** tint the blueprint background when the idea changes.
5. **Key-word sync:** start each drawing on its key word. `plan_edits` currently starts labels 0.12 s after the beat starts, not at the word.

## Measured results

Downloaded from YouTube at 360p and analyzed on 2026-11-06. Cuts came from FFmpeg's scene filter at threshold 0.10. Speech came from YouTube captions.

| Sample | Length | Changes per min | Median hold (s) | Words per min | Changes within 0.5 s of a phrase start |
|---|---|---:|---:|---:|---:|
| After Skool, 10 Years of Wisdom | 10:13 | 38.2 | 0.25 | 189 | 59% |
| After Skool, Alan Watts | 14:20 | 20.5 | 0.75 | 131 | 53% |
| TED-Ed, Mary's Room | 4:39 | 48.1 | 0.12 | 134 | 75% |
| TED-Ed, Trolley problem | 4:43 | 0.2 | 220 | 140 | Not usable |
| Kurzgesagt, Optimistic Nihilism | 7:12 | 1.7 | 7.17 | 176 | 92% |
| Kurzgesagt, Free Will | 12:01 | 11.2 | 1.43 | 167 | 72% |
| 60 Second, Achilles | 1:09 | 29.4 | 0.90 | 173 | 53% |
| 60 Second, Grandfather Paradox | 1:15 | 13.7 | 2.20 | 157 | 71% |
| 60 Second, Chinese Room | 1:11 | 14.5 | 3.68 | 160 | 82% |

The Lab's recent 30 to 60 second plans have median beats of 3.6 to 4.0 s, ranging from about 2.1 to 6.3 s.

## Limits of this evidence

- **The change counts are noisy.** The detector counts drawing and transitions as well as real cuts. It missed nearly every change in the trolley video, though the frames clearly show many. Use the table for rough comparison only.
- **The sync figure is not proof of word-perfect drawing.** Phrase starts are common in fast speech, so some matches are chance. It also does not measure the gap to one specific word.
- **Frames were read from four videos only,** at one frame per 2.5 seconds across the first 75 seconds: After Skool 10 Years, TED-Ed Trolley, Kurzgesagt Free Will and 60 Second Chinese Room. The other five contributed numbers only.
- **The samples are small and mostly long-form or older.** The channels' current work may differ, and The Lab is vertical while these are widescreen.
- **The timing values are judgment calls,** not channel rules. No rule here has been tested on a Lab render.
