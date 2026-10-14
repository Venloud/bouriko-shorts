"""JJK Culling Game explainer, script V4 (owner-approved, Young Jamal audio supplied as-is).

The narration text is read from JJK_CULLING_GAME_SCRIPT_V4.md (never rewritten). Each sentence
is one story line; [bracket] delivery tags stay in tts_text only (never captioned or shown).
PLAN gives every sentence its visual: the named character/reference, or a graphic for game
mechanics. Cues are phrases ("at": "Sukuna") resolved to word indices here.
Facts: experiments/jjk/fact_ledger_v4.json (every claim checked against the JJK Wiki's chapter
citations). Run: python experiments/jjk/jjk_story.py  (writes output/story.json). Manual only.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "experiments/jjk/JJK_CULLING_GAME_SCRIPT_V4.md"
TAG = re.compile(r"\[[^\]]*\]")

# Characters: exact JJK match (AniList/Jikan), red frame, review only.
# References: Fandom wiki screenshots, review only.
ASSETS = {
    "kenjaku": {"character": "Kenjaku"},
    "mahito": {"character": "Mahito"},
    "yuji": {"character": "Yuji Itadori", "aliases": ["Yuuji Itadori"]},
    "sukuna": {"character": "Ryomen Sukuna", "aliases": ["Ryoumen Sukuna", "Sukuna"]},
    "megumi": {"character": "Megumi Fushiguro"},
    "tsumiki": {"character": "Tsumiki Fushiguro"},
    "kogane": {"character": "Kogane"},
    "higuruma": {"character": "Hiromi Higuruma"},
    "tengen": {"character": "Tengen"},
    "fortnite_storm": {"fandom": "fortnite.fandom.com|File:The Wall Of Water - Storm - Fortnite.jpeg", "label": "Fortnite: the storm"},
    "fortnite_storm2": {"fandom": "fortnite.fandom.com|File:MEGA City (Tiger Tower - Storm Circle Event) - Location - Fortnite.png", "label": "Fortnite: storm circle"},
    "fortnite_bush": {"fandom": "fortnite.fandom.com|File:Bush - Item - Fortnite.png", "label": "Fortnite: bush (camping)"},
    "fortnite_lobby": {"fandom": "fortnite.fandom.com|File:Lobby (v22.00) - User Interface - Fortnite.jpg", "label": "Fortnite: battle royale lobby"},
    "fortnite_island": {"fandom": "fortnite.fandom.com|File:Battle Royale Island (v1.6) - Promo - Fortnite.jpg", "label": "Fortnite: battle royale island"},
    "squid_doll": {"fandom": "squidgame.fandom.com|File:Players Looking at Doll.png", "label": "Squid Game: players and the doll"},
}

KW = lambda *lines, **p: {"name": "keyword", "params": {"lines": list(lines), **p},  # noqa: E731
                          "steps": [{"t": 0}, {"t": 0.25}, {"t": 0.5}, {"t": 0.75}]}
PRE = {"t": -2}  # already drawn

# sentence index -> beats. "at": phrase where the beat starts (first beat starts with the line).
PLAN = {
    0: [{"diagram": {"name": "title_card", "params": {"lines": ["THE CULLING GAME"], "sub": "A TOURNAMENT?", "accentLine": 0}, "steps": [0, 3]}}],
    1: [{"asset": "fortnite_storm", "box": "wide", "label": "Fortnite", "sfx": "whoosh"},
        {"at": "camping", "asset": "fortnite_bush", "label": "camping"}],
    2: [{"diagram": KW("AFTER", "SHIBUYA", accentLine=1)},
        {"at": "fighting", "asset": "yuji", "box": "portrait", "label": "Yuji"},
        {"at": "who signed", "asset": "squid_doll", "box": "wide", "label": "Squid Game", "sfx": "impact"}],
    3: [{"asset": "kenjaku", "asset2": "mahito", "pair": ["Kenjaku", "Mahito"], "sfx": "whoosh"}],
    4: [{"asset": "mahito", "box": "portrait", "zoom": 1.5, "focus": [0.5, 0.25], "label": "Idle Transfiguration", "label_at": "Idle"},
        {"at": "activate", "diagram": KW("PREPARED", "FOR YEARS", accentLine=1)}],
    5: [{"diagram": {"name": "awakening", "params": {"pill": "cursed technique: awakened"}, "steps": [0, 4]}}],
    6: [{"diagram": {"name": "detection_flow", "params": {"labels": ["ANCIENT SORCERER", "CURSED OBJECT", "MODERN VESSEL"]}, "steps": [0, 5]}},
        {"at": "turned", "diagram": {"name": "detection_flow", "stage": "object", "params": {"labels": ["ANCIENT SORCERER", "CURSED OBJECT", "MODERN VESSEL"], "done": "centuries later"}, "steps": [PRE, PRE, 0, "ago."]}}],
    7: [{"asset": "yuji", "asset2": "sukuna", "pair": ["Yuji", "Sukuna"], "pair_at": ["Yuji", "Sukuna."], "sfx": "impact"}],
    8: [{"asset": "sukuna", "box": "portrait", "zoom": 1.5, "focus": [0.5, 0.3], "label": "old sorcerer, modern body", "label_at": "old"}],
    9: [{"asset": "kenjaku", "box": "portrait", "zoom": 1.45, "focus": [0.5, 0.25], "label": "Kenjaku"},
        {"at": "Japan", "diagram": {"name": "japan_colonies", "steps": [0, "ten", "barriers", "barriers"]}}],
    10: [{"asset": "fortnite_lobby", "box": "wide", "label": "battle royale lobby", "label_at": "battle"}],
    11: [{"diagram": KW("NO", "WINNER", accentLine=1, color="#FF3B6B")}],
    12: [{"diagram": {"name": "energy_merge", "steps": [0, "cursed", "cursed"]}},
         {"at": "Kenjaku's", "asset": "kenjaku", "box": "portrait", "zoom": 1.3, "focus": [0.35, 0.4], "label": "Kenjaku's real goal"},
         {"at": "merging", "asset": "tengen", "box": "portrait", "fit": "contain", "label": "Tengen", "label_at": "Tengen."}],
    13: [{"orb": True}],
    14: [{"diagram": {"name": "loophole", "params": {"title": "8 ORIGINAL RULES"}, "steps": [0]}}],
    15: [{"asset": "kenjaku", "box": "portrait", "zoom": 1.6, "focus": [0.5, 0.2], "label": "awakened by Kenjaku"},
         {"at": "you've", "diagram": {"name": "jjk_timer", "params": {"from": 19, "label": "DAYS TO DECLARE", "after": "timer 1: join"}, "steps": [0, "nineteen", "participation."]}}],
    16: [{"diagram": KW("TECHNIQUE REMOVED", "= IT CAN KILL YOU", accentLine=1, color="#FF3B6B", size=80)}],
    17: [{"diagram": {"name": "japan_colonies", "stage": "walk-in", "steps": [PRE, PRE, PRE, PRE]}},
         {"at": "congratulations,", "diagram": KW("YOU'RE A", "PLAYER NOW", accentLine=1)}],
    18: [{"asset": "kogane", "box": "portrait", "label": "Kogane", "sfx": "click"},
         {"at": "in-game", "asset": "fortnite_lobby", "box": "wide", "zoom": 1.6, "focus": [0.95, 0.4], "label": "in-game menu"}],
    19: [{"diagram": KW("RULES", "POINTS", "UPDATES", accentLine=-1, size=88)}],
    20: [{"diagram": KW("THE", "DISTURBING PART", accentLine=1, color="#FF3B6B")}],
    21: [{"diagram": KW("POINTS", "= KILLS", accentLine=1, color="#FF3B6B")}],
    22: [{"diagram": {"name": "points", "steps": [0, {"t": 99}]}}],
    23: [{"diagram": {"name": "points", "stage": "one", "steps": [PRE, 0]}}],
    24: [{"diagram": {"name": "rule_100", "params": {"rule": ["PROPOSE", "A NEW RULE"]}, "steps": ["hundred", "propose"]}}],
    25: [{"orb": True}],
    26: [{"diagram": {"name": "rule_100", "stage": "go-home", "params": {"rule": ["EVERYBODY CAN", "GO HOME"], "ruleNote": "proposed rule"}, "steps": [PRE, 0]}}],
    27: [{"diagram": {"name": "loophole", "stage": "no-delete", "params": {"title": "RULES CAN'T BE DELETED"}, "steps": [0]}},
         {"at": "game master", "diagram": {"name": "rule_100", "stage": "rejected", "params": {"rule": ["EVERYBODY CAN", "GO HOME"], "stamp": ["REJECTED:", "LONG-LASTING EFFECT"]}, "steps": [PRE, PRE, "reject"]}, "sfx": "impact"}],
    28: [{"asset": "fortnite_bush", "zoom": 1.3, "label": "camping"}],
    29: [{"diagram": {"name": "score_freeze", "params": {"label": "TIMER 2: NO SCORE CHANGE"}, "steps": [0, "doesn't", "days,"]}},
         {"at": "your", "diagram": KW("TECHNIQUE", "REMOVED", accentLine=1, color="#FF3B6B")}],
    30: [{"asset": "fortnite_storm2", "box": "wide", "label": "the storm", "sfx": "whoosh"}],
    31: [{"asset": "fortnite_island", "label": "last one standing? no", "label_at": "last"},
         {"at": "wait", "diagram": KW("CAN'T WAIT", "IT OUT", accentLine=1)}],
    32: [{"diagram": KW("FIGHTING", "IS THE POINT", accentLine=0, color="#FF3B6B")}],
    33: [{"diagram": {"name": "cog_machine", "params": {"label": "KENJAKU'S RITUAL"}, "steps": [0, "fuel"]}},
         {"at": "Kenjaku's", "asset": "kenjaku", "box": "portrait", "fit": "contain", "label": "Kenjaku"}],
    34: [{"diagram": KW("NOT A", "VICTORY", accentLine=1)}],
    35: [{"diagram": {"name": "cog_machine", "stage": "you", "params": {"label": "YOU = ONE COG", "you": True}, "steps": [PRE, PRE, "cog"]}}],
    36: [{"asset": "yuji", "box": "portrait", "label": "Yuji"},
         {"at": "Megumi", "asset": "megumi", "box": "portrait", "label": "Megumi"}],
    37: [{"asset": "megumi", "box": "portrait", "zoom": 1.35, "focus": [0.5, 0.3], "label": "Megumi's sister..."},
         {"at": "Tsumiki,", "asset": "tsumiki", "box": "portrait", "label": "Tsumiki"},
         {"at": "trying", "diagram": KW("SAVE HER", "NO MURDER", accentLine=1)}],
    38: [{"diagram": KW("DON'T BEAT", "THE GAME", accentLine=1)},
         {"at": "they start", "diagram": {"name": "loophole", "stage": "around", "params": {"title": "WAYS AROUND THE RULES"}, "steps": [0, "around"]}}],
    39: [{"asset": "higuruma", "box": "portrait", "label": "Higuruma", "sfx": "click"},
         {"at": "rule", "diagram": {"name": "rule_100", "stage": "rule10", "params": {"rule": ["PLAYERS MAY TRANSFER", "POINTS TO EACH OTHER"], "ruleNote": "rule 10, added with Higuruma's 100 points"}, "steps": [PRE, 0]}}],
    40: [{"diagram": KW("SCORE CHANGES", "NOBODY DIES", accentLine=1, size=84)}],
    41: [{"diagram": {"name": "loophole", "stage": "one", "params": {"title": "ONE LOOPHOLE"}, "steps": [PRE, 0]}}],
    42: [{"diagram": {"name": "cog_machine", "stage": "still", "params": {"label": "THE RITUAL KEEPS RUNNING"}, "steps": [PRE, PRE]}}],
    43: [{"asset": "kogane", "box": "portrait", "zoom": 1.4, "focus": [0.5, 0.35], "label": "Kogane"},
         {"at": "hundred", "diagram": {"name": "counter", "params": {"from": 0, "to": 100, "label": "POINTS", "countDur": 0.8}, "steps": [0, 0]}}],
    44: [{"diagram": {"name": "rule_100", "stage": "cancel", "params": {"rule": ["CANCEL", "THE GAME"], "stamp": ["NOT", "ALLOWED"]}, "steps": [PRE, PRE, 0]}},
         {"at": "your", "diagram": {"name": "rule_100", "stage": "yours", "params": {"rule": ["YOUR RULE", "HERE?"], "ruleNote": "still has to be accepted"}, "steps": [PRE, 0]}}],
    45: [{"diagram": {"name": "question", "params": {"lines": ["WHAT WOULD YOU", "PROPOSE TO GET", "EVERYBODY OUT?"], "chip": "100 POINTS"}, "steps": [0, 1, 2, 3]}, "hold": True}],
}

# Effects keyed by (sentence, phrase). Reactions max 5.
EFFECTS = [
    {"type": "punch", "line": 0, "at": "CRAZY."},
    {"type": "punch", "line": 1, "at": "KILLED."},
    {"type": "shake", "line": 1, "at": "KILLED."},
    {"type": "freeze", "line": 2, "at": "hold", "dur": 0.9},
    {"type": "punch", "line": 20, "at": "disturbing"},
    {"type": "punch", "line": 30, "at": "Bro,"},
]
REACTIONS = [
    {"line": 0, "at": "CRAZY.", "text": "CRAZY", "dur": 1.3},
    {"line": 2, "at": "hold", "text": "HOLD UP", "dur": 1.2},
    {"line": 25, "at": "where", "text": "THAT'S WHERE I GOT LOST", "dur": 1.8},
    {"line": 30, "at": "Bro,", "text": "BRO, EVEN THE STORM HAS A RULEBOOK!", "dur": 2.2},
]


def sentences():
    body = SCRIPT.read_text().split("## Tagged script (exactly as voiced)")[1].strip()
    out = []
    for para in body.split("\n\n"):
        for s in re.split(r"(?<=[.!?])\s+(?=[\[A-Z])", para.strip()):
            out.append(s.strip())
    return out


def word_index(text, phrase, start=0):
    words = [re.sub(r"[^a-z0-9'-]", "", w.lower()) for w in text.split()]
    target = [re.sub(r"[^a-z0-9'-]", "", w.lower()) for w in phrase.split()]
    for i in range(start, len(words) - len(target) + 1):
        if words[i:i + len(target)] == target:
            return i
    raise SystemExit(f"PLAN ERROR: phrase '{phrase}' not found in: {text}")


def resolve(text, beats):
    out, prev = [], 0
    for k, b in enumerate(beats):
        b = json.loads(json.dumps(b))
        if b.pop("orb", False):
            b["diagram"] = {"name": "orb_only", "steps": [0]}
            b["orb"] = True
        at = b.pop("at", None)
        b["word"] = 0 if k == 0 else word_index(text, at, prev)
        prev = b["word"]
        if "diagram" in b:
            b["diagram"]["steps"] = [word_index(text, s) if isinstance(s, str) else s for s in b["diagram"].get("steps", [0])]
        if b.get("pair"):  # two portraits side by side: one label over each half
            names, ats = b.pop("pair"), b.pop("pair_at", None) or [None, None]
            b["annotations"] = [{"type": "label", "word": word_index(text, ats[j]) if ats[j] else b["word"],
                                 "x": 0.25 + 0.5 * j, "y": 0.07, "text": names[j]} for j in range(2)]
        if b.get("label"):
            la = b.pop("label_at", None)
            b["annotations"] = [{"type": "label", "word": word_index(text, la) if la else b["word"],
                                 "x": 0.5, "y": 0.07, "text": b.pop("label")}]
        out.append(b)
    return out


def build():
    sents = sentences()
    lines = []
    for i, s in enumerate(sents):
        text = re.sub(r"\s+", " ", TAG.sub(" ", s)).strip()
        lines.append({"speaker": "NARRATOR", "visual": "JJK", "text": text, "tts_text": s,
                      "beats": resolve(text, PLAN.get(i, [{"diagram": KW(*text.upper().split()[:2])}]))})
    for e in EFFECTS + REACTIONS:
        e["word"] = word_index(lines[e["line"]]["text"], e["at"])
    missing = [i for i in range(len(sents)) if i not in PLAN]
    if missing:
        raise SystemExit(f"PLAN ERROR: sentences without a visual: {missing}")
    return {
        "title": "JJK Culling Game: It's Not a Tournament",
        "pillar": "anime_explainer",
        "topic": "Jujutsu Kaisen Culling Game",
        "caption": "The Culling Game isn't a tournament. What rule would you add?",
        "hashtags": ["#JJK", "#JujutsuKaisen", "#CullingGame", "#Anime"],
        "sources": ["https://jujutsu-kaisen.fandom.com/wiki/Culling_Game"],
        "exact_script": True,
        "script_file": "experiments/jjk/JJK_CULLING_GAME_SCRIPT_V4.md",
        "script_version": "v4-owner-approved-young-jamal",
        "theme": "jjk",
        "hook_answer_line": 1,
        "voice_source": "supplied",
        "audio_tail_seconds": 3.5,
        "max_seconds": 179.5,
        "max_sfx": 12,
        "max_reactions": 5,
        "music": {"enabled": True},
        "assets": ASSETS,
        "effects": EFFECTS,
        "reactions": REACTIONS,
        "lines": lines,
    }


if __name__ == "__main__":
    story = build()
    out = ROOT / "output/story.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(story, indent=2) + "\n")
    ledger = ROOT / "experiments/jjk/fact_ledger_v4.json"
    if ledger.exists():
        (ROOT / "output/fact_ledger.json").write_text(ledger.read_text())
    words = sum(len(l["text"].split()) for l in story["lines"])
    print(f"JJK story V4: {len(story['lines'])} sentences, {words} words, "
          f"{sum(len(l['beats']) for l in story['lines'])} beats, {len(REACTIONS)} reactions")
