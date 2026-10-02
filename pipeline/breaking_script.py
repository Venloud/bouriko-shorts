"""Turn a verified breaking-tech article into a Bouriko short."""
import json,os,requests
from pathlib import Path
from common import ROOT
def gemini(prompt):
    key=os.environ["GEMINI_API_KEY"]; model="gemini-3.8-flash"
    r=requests.post("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent?key="+key,json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.5,"responseMimeType":"application/json"}},timeout=90)
    r.raise_for_status(); return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
def main():
    n=json.loads((ROOT/"output/breaking_news.json").read_text())
    p=f"""Write a Bouriko breaking-tech short about this VERIFIED article.
Title: {n['title']}
Description: {n['description']}
URL: {n['url']}
Rules: 140-155 words; 61-68 seconds; facts only from supplied article; clearly say when a detail is preliminary; no invented specs; no hype; Bouriko is curious and Rock Phone explains. Return JSON only:
{{"title":"...","pillar":"tech_news","lines":[{{"speaker":"BOURIKO","text":"...","visual":"..."}},...],"sources":["{n['url']}"],"caption":"...","hashtags":["#Bouriko","#TechNews"]}}"""
    story=gemini(p)
    story["topic"]=n["title"]; story["breaking"]=True
    (ROOT/"output/story.json").write_text(json.dumps(story,indent=2))
if __name__=="__main__":main()
