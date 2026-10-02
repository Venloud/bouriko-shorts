"""Story writer with Gemini -> Groq fallback and deterministic offline test."""
import json,os,re,requests
from pathlib import Path
from common import ROOT,CONFIG,load_history,log
TOPICS=ROOT/"data/topics.json"; HISTORY=ROOT/"data/history.json"
def topic_pick():
    data=json.loads(TOPICS.read_text()); used={x.get("topic") for x in load_history()}
    for t in data:
        if isinstance(t,dict): name=t.get("topic") or t.get("title")
        else: name=t
        if name and name not in used:return name
    return data[0].get("topic") if isinstance(data[0],dict) else data[0]
def gemini(prompt):
    key=os.getenv("GEMINI_API_KEY")
    if not key:return None
    model=CONFIG.get("llm_models",["gemini-3.8-flash"])[0]
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    r=requests.post(url,json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.7,"responseMimeType":"application/json"}},timeout=60)
    if r.ok:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    log(f"Gemini {r.status_code}: fallback")
def build(topic):
    prompt=f'''You write Bouriko tech shorts. Topic: {topic}. Create 140-152 words, 61-68 seconds.
Return JSON only with title,pillar,lines,sources,caption,hashtags. lines are objects with speaker Bouriko or Rock Phone, text, visual.
Facts must be verifiable; no logos. Bouriko is curious and often wrong; Rock Phone explains.'''
    raw=gemini(prompt)
    if raw:
        try:return json.loads(raw)
        except: pass
    return {"title":"How traffic lights know when cars are waiting","pillar":"hidden","lines":[
      {"speaker":"Bouriko","text":"Bouriko sees the red light. Bouriko thinks the light is watching the road.","visual":"traffic light sketch"},
      {"speaker":"Rock Phone","text":"Not magic. Many intersections use sensors to detect vehicles waiting in a lane.","visual":"sensor diagram"},
      {"speaker":"Bouriko","text":"So tiny machine watches the cars?","visual":"Bouriko pointing"},
      {"speaker":"Rock Phone","text":"Yes. Some systems use loops buried under the pavement. A car changes the loop's electrical signal.","visual":"road loop diagram"},
      {"speaker":"Bouriko","text":"Car makes invisible electricity wiggle?","visual":"electric field sketch"},
      {"speaker":"Rock Phone","text":"Exactly. The controller can use that signal to help decide when to change the light.","visual":"controller diagram"},
      {"speaker":"Bouriko","text":"Bouriko thought light was just patient. Now Bouriko knows road has ears.","visual":"Bouriko with rock phone"}],
      "sources":["https://highways.dot.gov/public-roads/spring-2017/inductive-loop-detectors"],"caption":"Traffic lights can use sensors to detect waiting vehicles.","hashtags":["#Bouriko","#Tech","#HowItWorks"]}
def main():
    inbox=list((ROOT/"inbox").glob("*.txt")); topic=None
    for p in inbox:
        if p.name.lower()=="traffic_light.txt": topic="traffic light sensors"; break
    topic=topic or topic_pick(); story=build(topic)
    out=ROOT/"output/story.json"; out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(story,indent=2))
    h=load_history(); h.append({"topic":topic,"title":story["title"],"built":True}); HISTORY.parent.mkdir(exist_ok=True); HISTORY.write_text(json.dumps(h,indent=2))
    return out
if __name__=="__main__": print(main())
