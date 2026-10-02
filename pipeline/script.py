"""Bouriko writer with topic rotation, source ledger and critic."""
import json,os,requests
from common import ROOT,CONFIG,load_history,log
TOPICS=ROOT/"data/topics.json"; HISTORY=ROOT/"data/history.json"
def pick():
    data=json.loads(TOPICS.read_text()); hist={x.get("topic") for x in load_history()}; rot=CONFIG["pillar_rotation"]; n=sum(1 for x in load_history() if x.get("pillar")); pillar=rot[n%len(rot)]
    choices=[x for x in data.get(pillar,[]) if x not in hist] or data.get(pillar,[])
    return pillar,choices[0]
def source_text(topic):
    r=requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/"+requests.utils.quote(topic),timeout=20)
    if not r.ok:
        r=requests.get("https://en.wikipedia.org/w/api.php",params={"action":"query","list":"search","srsearch":topic,"format":"json","srlimit":1},timeout=20)
        hits=r.json().get("query",{}).get("search",[]) if r.ok else []
        if not hits:return []
        r=requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/"+requests.utils.quote(hits[0]["title"]),timeout=20)
    if not r.ok:return []
    d=r.json(); return [{"id":"s1","title":d.get("title"),"url":d.get("content_urls",{}).get("desktop",{}).get("page"),"text":d.get("extract","")}]
def gemini(prompt):
    key=os.getenv("GEMINI_API_KEY")
    if not key:return None
    model=CONFIG.get("llm_models",["gemini-3.8-flash"])[0]
    r=requests.post("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent?key="+key,json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.6,"responseMimeType":"application/json"}},timeout=90)
    if r.ok:return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    log("Gemini request failed: "+str(r.status_code)); return None
def write(pillar,topic,sources):
    ledger="\n".join(s["id"]+": "+s["title"]+" — "+s["text"] for s in sources)
    prompt=(ROOT/"prompts/script.txt").read_text()
    vals={"pillar":pillar,"topic":topic,"ledger":ledger,"poses":"talking, pointing, confused, phone, thinking","words_lo":str(CONFIG["script_words"][0]),"words_hi":str(CONFIG["script_words"][1])}
    for k,v in vals.items(): prompt=prompt.replace("{"+k+"}",v)
    raw=gemini(prompt)
    if not raw: raise RuntimeError("Gemini writer failed")
    story=json.loads(raw)
    critic=(ROOT/"prompts/critic.txt").read_text().replace("{words_lo}",str(CONFIG["script_words"][0])).replace("{words_hi}",str(CONFIG["script_words"][1]))
    checked=gemini(critic+"\nSOURCE LEDGER:\n"+ledger+"\nDRAFT:\n"+json.dumps(story))
    if checked:
        try: story=json.loads(checked).get("script",story)
        except Exception: pass
    story["pillar"]=pillar; story["sources"]=[s["url"] for s in sources if s.get("url")]
    return story
def main():
    pillar,topic=pick()
    for p in sorted((ROOT/"inbox").glob("*.txt")):
        lines=p.read_text(errors="ignore").splitlines()
        if not lines: continue
        kind=lines[0].strip().upper()
        if kind=="TOPIC" and len(lines)>1: topic=lines[1].strip(); break
        if kind=="SCRIPT": break
    sources=source_text(topic)
    if not sources: raise RuntimeError("No source found for "+topic)
    story=write(pillar,topic,sources); story["topic"]=topic
    out=ROOT/"output/story.json";out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(story,indent=2))
    h=load_history();h.append({"topic":topic,"pillar":pillar,"title":story.get("title",""),"built":True});HISTORY.parent.mkdir(exist_ok=True);HISTORY.write_text(json.dumps(h,indent=2))
if __name__=="__main__":main()
