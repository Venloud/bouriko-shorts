"""JJK Culling Game explainer (Phase 1): ONE canonical script, fact-locked, with its visual plan.

Script = draft v2 (experiments/jjk/JJK_CULLING_GAME_SCRIPT_V2_DRAFT.md), corrected against the
rules as cited from the manga (ch. 143 pp. 18-19 / anime ep. 49 and the chapters below), via the
Jujutsu Kaisen Wiki "Culling Game" page. Every line carries the claims it makes and their source.
The rule proposal at the end is a FAN PROPOSAL, not canon, and is labelled on screen.

Run: python experiments/jjk/jjk_story.py  (writes output/story.json). Manual workflow only.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WIKI = "https://jujutsu-kaisen.fandom.com/wiki/Culling_Game"
SRC_RULES = {"source": WIKI + "#Rules", "primary": "Jujutsu Kaisen manga ch. 143 pp. 18-19 (anime ep. 49)",
             "tier": "fan wiki citing the manga chapter/page"}

# Character images are resolved by prepare_jjk_media.py (local vetted stills first, then AniList,
# then Jikan; exact name + Jujutsu Kaisen credit required, sha256 + source logged, review only).
ASSETS = {
    "tengen": {"character": "Tengen"},
    "kenjaku": {"character": "Kenjaku"},
    "tsumiki": {"character": "Tsumiki Fushiguro"},
    "megumi": {"character": "Megumi Fushiguro"},
    "yuji": {"character": "Yuji Itadori", "aliases": ["Yuuji Itadori"]},
}


def kw(*lines, **params):
    return {"name": "keyword", "params": {"lines": list(lines), **params}, "steps": [{"t": 0}, {"t": 0.3}, {"t": 0.6}, {"t": 0.9}]}


LINES = [
    {
        "text": "Imagine waking up with a cursed technique you never asked for.",
        "tts_text": "[intense] Imagine waking up... with a cursed technique you never asked for.",
        "claims": [{"claim": "Kenjaku awakened marked non-sorcerers, giving them cursed techniques",
                    "source": WIKI + "#Kenjaku's_Preparations", "primary": "ch. 136 (ep. 47)"}],
        "beats": [{"word": 0, "diagram": {"name": "awakening", "steps": [0, 5]}}],
    },
    {
        "text": "You get nineteen days to join a death game, or that technique gets ripped out. And that would kill you.",
        "tts_text": "[urgent] You get nineteen days to join a death game — or that technique gets ripped out. [serious] And that would kill you.",
        "claims": [{"claim": "Rule 1: declare participation at a colony within 19 days of awakening", **SRC_RULES},
                   {"claim": "Rule 2: breaking rule 1 = cursed technique removal", **SRC_RULES},
                   {"claim": "Master Tengen confirms cursed technique removal would end the player's life",
                    "source": WIKI + "#Rules", "primary": "ch. 146 pp. 4-5 (ep. 50)"}],
        "beats": [
            {"word": 0, "diagram": {"name": "jjk_timer", "params": {"from": 19, "label": "DAYS TO JOIN"}, "steps": [0, 2, 8]}},
            {"word": 9, "diagram": kw("TECHNIQUE REMOVED", "= DEATH", accentLine=1, color="#FF3B6B", size=84)},
        ],
    },
    {
        "text": "This is the Culling Game, built by Kenjaku: ten barrier colonies running down Japan.",
        "tts_text": "[dramatic] This is the Culling Game — built by Kenjaku. Ten barrier colonies, running down Japan.",
        "claims": [{"claim": "The Culling Game is orchestrated by Kenjaku", "source": WIKI, "primary": "ch. 144"},
                   {"claim": "Ten barrier colonies form a line down Japan (Hokkaido excluded)", "source": WIKI + "#Colonies",
                    "primary": "ch. 145-146 (ep. 50)"}],
        "beats": [
            {"word": 0, "asset": "kenjaku", "box": "portrait", "tag": "The Culling Game", "sfx": "whoosh",
             "annotations": [{"type": "label", "word": 7, "x": 0.5, "y": 0.08, "text": "Kenjaku"}]},
            {"word": 8, "diagram": {"name": "japan_colonies", "steps": [0, 8, 13, 11]}},
        ],
    },
    {
        "text": "Inside: awakened sorcerers, and fighters reborn from a thousand years ago.",
        "tts_text": "Inside: awakened sorcerers... and fighters reborn from a thousand years ago.",
        "claims": [{"claim": "Players include newly awakened sorcerers and sorcerers from past eras incarnated in vessels",
                    "source": WIKI + "#Kenjaku's_Preparations", "primary": "ch. 136 (ep. 47)"},
                   {"claim": "Kenjaku made contracts with those sorcerers over a thousand years ago",
                    "source": WIKI + "#Kenjaku's_Preparations", "primary": "ch. 136 (ep. 47)"}],
        "beats": [
            {"word": 0, "diagram": kw("AWAKENED", "SORCERERS", accentLine=1)},
            {"word": 4, "diagram": {"name": "counter", "params": {"from": 0, "to": 1000, "label": "YEARS AGO", "prefix": "", "countDur": 1.0, "color": "#FF3B6B"}, "steps": [0, 0]}},
        ],
    },
    {
        "text": "Megumi's sister, Tsumiki, was awakened too. So Megumi and Yuji go in to get her out.",
        "tts_text": "Megumi's sister, Tsumiki, was awakened too. So Megumi and Yuji go in... to get her out.",
        "claims": [{"claim": "Tsumiki Fushiguro was one of the marked people awakened for the game",
                    "source": WIKI + "#Kenjaku's_Preparations", "primary": "ch. 144-145 (ep. 49-50)"},
                   {"claim": "Megumi and Yuji enter to get Tsumiki out", "source": WIKI + "#Plan_to_Rescue_Tsumiki_Fushiguro",
                    "primary": "ch. 146-160"}],
        "beats": [
            {"word": 0, "asset": "tsumiki", "box": "portrait", "tag": "Megumi's sister",
             "annotations": [{"type": "label", "word": 2, "x": 0.5, "y": 0.08, "text": "Tsumiki"}]},
            {"word": 6, "asset": "megumi", "box": "portrait",
             "annotations": [{"type": "label", "word": 7, "x": 0.5, "y": 0.08, "text": "Megumi"}]},
            {"word": 9, "asset": "yuji", "box": "portrait",
             "annotations": [{"type": "label", "word": 9, "x": 0.5, "y": 0.08, "text": "Yuji"}]},
        ],
    },
    {
        "text": "You score by taking a player's life. Sorcerers are worth five points. Non-sorcerers, one.",
        "tts_text": "You score by taking a player's life. Sorcerers are worth five points. Non-sorcerers... one.",
        "claims": [{"claim": "Rule 4: players score points by ending the lives of other players", **SRC_RULES},
                   {"claim": "Rule 5: as a general rule, sorcerers are worth 5 points, non-sorcerers 1", **SRC_RULES}],
        "beats": [
            {"word": 0, "diagram": kw("SCORE =", "TAKING A LIFE", accentLine=1, color="#FF3B6B")},
            {"word": 7, "diagram": {"name": "points", "steps": [0, 12]}, "sfx": "click"},
        ],
    },
    {
        "text": "Spend one hundred points and the game master must add your rule, unless it has a long-lasting effect on the game.",
        "tts_text": "Spend one hundred points... and the game master must add your rule — unless it has a long-lasting effect on the game.",
        "claims": [{"claim": "Rule 6: a player can expend 100 points to have a new rule added", **SRC_RULES},
                   {"claim": "Rule 7: the game master must accept it unless it has a long-lasting effect on the game", **SRC_RULES}],
        "beats": [
            {"word": 0, "diagram": {"name": "rule_100", "steps": [1, 9]}},
            {"word": 12, "diagram": {"name": "rule_100", "stage": "condition", "steps": [{"t": -2}, {"t": -2}, 16]}},
        ],
    },
    {
        "text": "And hiding fails. If your score stays the same for nineteen days, your technique is removed.",
        "tts_text": "And hiding? [scoffs] Fails. If your score stays the same for nineteen days, your technique is removed.",
        "claims": [{"claim": "Rule 8: if a player's score stays the same for 19 days, cursed technique removal", **SRC_RULES}],
        "beats": [
            {"word": 0, "diagram": kw("HIDING?", "IT FAILS", accentLine=0)},
            {"word": 3, "diagram": {"name": "score_freeze", "steps": [0, 6, 11]}},
            {"word": 12, "diagram": kw("TECHNIQUE", "REMOVED", accentLine=1, color="#FF3B6B")},
        ],
    },
    {
        "text": "Here's the twist. Kenjaku doesn't need a winner.",
        "tts_text": "[dramatic] Here's the twist. Kenjaku doesn't need a winner.",
        "claims": [{"claim": "Kenjaku's goal is the merger, not a champion; the game continues even if Kenjaku dies",
                    "source": WIKI + "#About_the_Culling_Game", "primary": "ch. 145 pp. 4-6, 11-12 (ep. 50)"}],
        "beats": [{"word": 0, "asset": "kenjaku", "box": "portrait", "fit": "contain", "tag": "The twist", "sfx": "whoosh",
                   "annotations": [{"type": "label", "word": 3, "x": 0.5, "y": 0.92, "text": "No winner needed"}]}],
    },
    {
        "text": "The game is a ritual. The colonies' cursed energy fuels his plan to merge Tengen with Japan's people.",
        "tts_text": "The game is a ritual. The colonies' cursed energy fuels his plan — to merge Tengen with Japan's people.",
        "claims": [{"claim": "The Culling Game is a ritual; cursed energy in the colonies prepares the merger of Tengen with the people of Japan",
                    "source": WIKI + "#Great_Merger", "primary": "ch. 145 (ep. 50); ch. 202 pp. 12-17"}],
        "beats": [
            {"word": 0, "diagram": kw("IT'S A", "RITUAL", accentLine=1, color="#FF3B6B")},
            {"word": 5, "diagram": {"name": "energy_merge", "steps": [0, 6, 11]}},
            {"word": 12, "asset": "tengen", "box": "portrait", "fit": "contain",
             "annotations": [{"type": "label", "word": 14, "x": 0.5, "y": 0.08, "text": "Tengen"}]},
        ],
    },
    {
        "text": "So the real fight is finding a loophole in the rules.",
        "tts_text": "So the real fight... is finding a loophole in the rules.",
        "claims": [{"claim": "Rules can't be removed, but can be countered with added rules",
                    "source": WIKI + "#Plan_to_Rescue_Tsumiki_Fushiguro", "primary": "ch. 146 p. 8 (ep. 50)"}],
        "beats": [
            {"word": 0, "diagram": {"name": "loophole", "steps": [0, 7]}},
        ],
    },
    {
        "text": "My fan proposal: defeat a curse that's a player, and you take all its points.",
        "tts_text": "[excited] My fan proposal: defeat a curse that's a player... and you take ALL its points.",
        "claims": [{"claim": "FAN PROPOSAL, not canon. Canon context: cursed spirit participants are worth 5 points; "
                             "points only move between players by voluntary transfer (rule 10)",
                    "source": WIKI + "#Rules", "primary": "ch. 175 p. 18; ch. 167 p. 1", "fan_proposal": True}],
        "beats": [
            {"word": 0, "diagram": {"name": "title_card", "params": {"lines": ["FAN PROPOSAL"], "sub": "NOT A REAL RULE", "accentLine": 0}, "steps": [0, 2]}, "sfx": "click"},
            {"word": 3, "diagram": {"name": "fan_proposal", "steps": [0, 11]}},
        ],
    },
    {
        "text": "Would the game master accept that? What rule would you add?",
        "tts_text": "Would the game master accept that? [curious] What rule would YOU add?",
        "claims": [{"claim": "Rule 7 decides: accepted unless it has a long-lasting effect on the game", **SRC_RULES}],
        "beats": [
            {"word": 0, "diagram": {"name": "fan_proposal", "stage": "ask", "steps": [{"t": -2}, {"t": -2}, 0]}},
            {"word": 6, "diagram": kw("WHAT RULE", "WOULD YOU ADD?", accentLine=1)},
        ],
    },
]

story = {
    "title": "JJK Culling Game: The Rules Explained",
    "pillar": "anime_explainer",
    "topic": "Jujutsu Kaisen Culling Game",
    "caption": "The Culling Game rules in 60 seconds, plus a fan rule. Would it pass?",
    "hashtags": ["#JJK", "#JujutsuKaisen", "#CullingGame", "#Anime"],
    "sources": [WIKI],
    "exact_script": True,
    "script_file": "experiments/jjk/jjk_story.py",
    "script_version": "v2-factlocked-2026-10-11",
    "theme": "jjk",
    "hook_answer_line": 2,
    # more energy than the tech videos (ElevenLabs v3/v4: lower stability = more expressive)
    "voice_settings": {"stability": 0.0, "style": 0.35, "similarity_boost": 0.8, "use_speaker_boost": True},
    "voice_speed": 1.15,
    "trim_pauses": {"lead": 0.06, "tail": 0.16},
    "assets": ASSETS,
    "lines": [{"speaker": "NARRATOR", "visual": "JJK", **line} for line in LINES],
}

if __name__ == "__main__":
    out = ROOT / "output/story.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(story, indent=2) + "\n")
    ledger = [{"line": i, "text": l["text"], "claims": l["claims"]} for i, l in enumerate(LINES)]
    (ROOT / "output/fact_ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    words = sum(len(l["text"].split()) for l in LINES)
    print(f"JJK story: {len(LINES)} lines, {words} words, fact ledger with {sum(len(l['claims']) for l in LINES)} claims")
