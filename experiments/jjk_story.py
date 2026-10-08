"""Experimental JJK anime explainer story, isolated from the regular topic queue.

Run: python experiments/jjk_story.py
Then reuse Bouriko's existing Kokoro, media, SFX and Remotion pipeline.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = [
    ("Kenjaku created the Culling Game, a deadly ritual that turns Japan into a battlefield.", "Kenjaku", "anime_reference"),
    ("Ten colonies become arenas where sorcerers are forced to compete.", "TEN COLONIES", "animated_map"),
    ("Players earn five points for defeating another sorcerer.", "5 POINTS", "animated_counter"),
    ("Defeating a non-sorcerer awards just one point.", "1 POINT", "animated_counter"),
    ("Reach one hundred points, and you can propose a new rule.", "100 POINTS", "animated_counter"),
    ("But the game master can reject changes that would disrupt the ritual.", "GAME MASTER", "anime_reference"),
    ("If your points don't change for nineteen days, you face cursed technique removal.", "19 DAYS", "animated_timer"),
    ("Yuji and Megumi enter the game to find a way to save their friends.", "YUJI AND MEGUMI", "anime_reference"),
    ("The twist? Kenjaku never designed this game for someone to win.", "THE TWIST", "anime_reference"),
    ("The battles generate cursed energy for a much larger plan involving Tengen.", "KENJAKU'S PLAN", "energy_diagram"),
    ("The Culling Game isn't a tournament. The game itself is the ritual.", "THE GAME IS THE RITUAL", "hero_motion"),
]
story = {
    "title": "JJK Culling Game Explained",
    "pillar": "anime_explainer",
    "topic": "Jujutsu Kaisen Culling Game",
    "caption": "The Culling Game explained in 60 seconds",
    "hashtags": ["#JJK", "#JujutsuKaisen", "#Anime"],
    "sources": [],
    "exact_script": True,
    "lines": [
        {
            "speaker": "NARRATOR",
            "text": spoken,
            "visual": heading,
            "visual_prompt": "Jujutsu Kaisen " + heading,
            "visual_actions": [{"type": "media", "kind": "video", "query": "Jujutsu Kaisen " + heading}],
            "anime_visual_type": kind,
            "anime_query": "Jujutsu Kaisen " + heading,
        }
        for spoken, heading, kind in SCENES
    ],
}
if __name__ == "__main__":
    output = ROOT / "output/story.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(story, indent=2) + "\n")
    print(f"Prepared {len(SCENES)} JJK scenes: {output}")
