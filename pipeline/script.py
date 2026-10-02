"""Bouriko writer: pillar rotation, topic dedupe, source ledger, Gemini critic."""
import json,os,re,requests
from common import ROOT,CONFIG,load_history,log
TOPICS=ROOT/"data/topics.json"; HISTORY=ROOT/"data/history.json"
def _topics():
    data=json.loads(TOPICS.read_text()); return data
def pick():
    data=_topics(); hist={x.get("topic") for x in load_history()}
    rotation=CONFIG.get("pillar_rotation",[])
    n=sum(1 for x in load_history() if x.get("pillar"))
    pillar=rotation[n%len(rotation)] if rotation else "hidden"
    choices=[x for x in data.get(pillar,[]) if x not in hist]
    return pillar,(choices[0] if choices else data.get(pillar,[None])[0])
def source_text(topic):
    q=requests.utils.quote(topic)
    r=requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/"+q,timeout=20)
    if r.ok:
        d=r.json(); return [{"id":"s1","title":d.get("title"),"url":d.get("content_urls",{}).get("desktop",{}).get("page"),"text":d.get("extract","")}]
    return []
def gemini(prompt):
    key=os.getenv("GEMINI_API_KEY")
    if not key:return None
    model=CONFIG.get("llm_models",["gemini-3.8-flash"])[0]
    u=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    r=requests.post(u,json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.6,"responseMimeType":"application/json"}},timeout=90)
    if r.ok:return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    log(f"Gemini {r.status_code}")
def write(pillar,topic,sources):
    ledger="\n".join(f'{s["id"]}: {s["title"]} — {s["text"]}' for s in sources)
    rule=CONFIG.get("pillar_rules",{}).get(pillar,"")
    prompt=(ROOT/"prompts/script.txt").read_text().format(pillar=pillar,topic=topic,ledger=ledger,poses="talking,pointing,confused,phone,thinking")
    raw=gemini(prompt)
    if not raw: raise RuntimeError("GEMINI_API_KEY unavailable or request failed")
    story=json.loads(raw); story["pillar"]=pillar; story["sources"]=[s["url"] for s in sources if s.get("url")]
    critic=(ROOT/"prompts/critic.txt").read_text().format(words_lo=CONFIG["script_words"][0],words_hi=CONFIG["script_words"][1])
    checked=gemini(critic+"\nSOURCE LEDGER:\n"+ledger+"\nDRAFT:\n"+json.dumps(story))
    if checked:
        try:
            c=json.loads(checked); story=c.get("script",story)
        except Exception: pass
    return story
def main():
    inbox=sorted((ROOT/"inbox").glob("*.txt"))
    pillar,topic=pick()
    for p in inbox:
        first=p.read_text(errors="ignore").splitlines()[0].strip().upper() if p.read_text(errors="ignore").splitlines() else ""
        if first in {"TOPIC","SCRIPT"}:
            if first=="TOPIC": topic=p.read_text().splitlines()[1].strip() if len(p.read_text().splitlines())>1 else topic
            break
    sources=source_text(topic)
    if not sources: raise RuntimeError("No source found for topic")
    story=write(pillar,topic,sources); story["topic"]=topic
    out=ROOT/"output/story.json";out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(story,indent=2))
    h=load_history();h.append({"topic":topic,"pillar":pillar,"title":story.get("title",""),"built":True});ROOT.joinpath("data").mkdir(exist_ok=True);HISTORY.write_text(json.dumps(h,indent=2))
if __name__=="__main__": main()
