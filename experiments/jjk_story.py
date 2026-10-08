"""Experimental JJK anime explainer story, isolated from the regular topic queue.

Run: python experiments/jjk_story.py
Then reuse Bouriko's existing Kokoro, media, SFX and Remotion pipeline.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = [
    ("Imagine walking into a barrier, and a tiny shikigami asks if you're joining a death game. That's Kogane.", "KOGANE ENTRY", "anime_reference"),
    ("Yuji Itadori encounters Kogane at the colony. Entering means accepting the Culling Game's rules.", "YUJI AND KOGANE", "anime_reference"),
    ("And Megumi has a personal reason to fight: his sister Tsumiki is caught up in Kenjaku's plan.", "MEGUMI AND TSUMIKI", "anime_reference"),
    ("Kenjaku created ten colonies across Japan. Each one is part of a giant ritual.", "TEN COLONIES", "animated_map"),
    ("Here's the scoring: defeat a sorcerer, earn five points. Defeat a non-sorcerer, earn one.", "5 POINTS", "animated_counter"),
    ("Reach one hundred points, and you can request a new rule, but not one that breaks the game.", "100 POINTS", "animated_counter"),
    ("And there's a terrifying deadline. If your score doesn't change for nineteen days, your cursed technique can be removed.", "19 DAYS", "animated_timer"),
    ("So Yuji and Megumi aren't chasing a trophy. They're trying to change the rules and save people.", "YUJI AND MEGUMI", "anime_reference"),
    ("Kenjaku's real objective goes much deeper: the battles fuel his plan involving Tengen.", "KENJAKU AND TENGEN", "energy_diagram"),
    ("The Culling Game isn't just a tournament. The tournament itself powers the ritual.", "THE RITUAL", "hero_motion"),
    ("Here's my hypothetical rule: defeating a curse player transfers all their points. What rule would you add?", "YOUR RULE", "blackboard"),
]
story = {
    "title": "JJK Culling Game: Why Yuji Enters",
    "pillar": "anime_explainer",
    "topic": "Jujutsu Kaisen Culling Game",
    "caption": "Why Yuji enters the Culling Game, and the rule I would add",
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
