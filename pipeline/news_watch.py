"""Find genuinely major tech news and emit one breaking-news job."""
import json,os,re,time,xml.etree.ElementTree as ET
from pathlib import Path
import requests
from common import ROOT,log
STATE=ROOT/"data/news_seen.json"
FEEDS=[
 "https://www.techmeme.com/feed.xml",
 "https://feeds.arstechnica.com/arstechnica/technology-lab",
 "https://www.theverge.com/rss/index.xml",
 "https://www.wired.com/feed/rss",
 "https://www.engadget.com/rss.xml",
]
MAJOR=re.compile(r"\b(launch|launched|unveil|unveiled|announce|announced|release|released|acquire|acquisition|breach|hack|outage|recall|chip|gpu|iphone|android|windows|playstation|xbox|nvidia|openai|google|apple|microsoft|meta|anthropic|amazon|amd|samsung|sony|tesla|spacex|gemini|chatgpt|claude|copilot|ai model|robot|quantum)\b",re.I)
def seen():
    return json.loads(STATE.read_text()) if STATE.exists() else []
def save(x):
    STATE.parent.mkdir(parents=True,exist_ok=True); STATE.write_text(json.dumps(x[-500:],indent=2))
def feed(url):
    r=requests.get(url,headers={"User-Agent":"BourikoNews/1.0"},timeout=20); r.raise_for_status()
    root=ET.fromstring(r.content); out=[]
    for item in root.findall(".//item"):
        title=(item.findtext("title") or "").strip(); link=(item.findtext("link") or "").strip(); desc=re.sub("<[^>]+>"," ",item.findtext("description") or "").strip()
        if title and link: out.append({"title":title,"url":link,"description":desc[:1200]})
    return out
def classify(c):
    key=os.getenv("GEMINI_API_KEY")
    if not key:
        return bool(MAJOR.search(c["title"])) and len(c["title"])>25
    prompt=f"""You are the breaking-news editor for a short-form tech channel.
Article title: {c['title']}
Description: {c['description']}
Answer JSON only: {{"major":true/false,"reason":"short","topic":"specific topic"}}
MAJOR means a material, confirmed technology development that ordinary tech viewers would care about immediately:
major product/model launch, major security incident, major outage, major acquisition, major chip/hardware announcement, major platform change, or major company technology announcement.
Do NOT mark rumors, minor updates, opinion pieces, routine earnings, reviews, or recycled coverage as major."""
    model="gemini-3.8-flash"
    r=requests.post("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent?key="+key,json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0,"responseMimeType":"application/json"}},timeout=45)
    if not r.ok:return False
    try:return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"]).get("major",False)
    except:return False
def main():
    old=seen(); oldset={x["url"] for x in old}; candidates=[]
    for u in FEEDS:
        try:candidates.extend(feed(u))
        except Exception as e:log("feed failed: "+u+" "+str(e))
    fresh=[]
    for c in candidates:
        if c["url"] not in oldset and classify(c): fresh.append(c)
    for c in candidates:
        if c["url"] not in oldset: old.append({"url":c["url"],"title":c["title"],"seen":int(time.time())})
    save(old)
    if not fresh:
        print("NO_BREAKING_TECH_NEWS"); return 0
    # Pick the first major item from the feed ordering; sources are independently curated.
    c=fresh[0]
    out=ROOT/"output/breaking_news.json"; out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(c,indent=2))
    print("BREAKING_TECH_NEWS="+json.dumps(c))
    return 0
if __name__=="__main__":raise SystemExit(main())
