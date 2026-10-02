import os, requests
def notify_text(title,message,warn=False):
    topic=os.getenv("NTFY_TOPIC","").strip()
    if not topic: return
    requests.post("https://ntfy.sh/"+topic,headers={"Title":title,"Priority":"high" if warn else "default"},data=message.encode(),timeout=15)
def notify_story_missing(): notify_text("Bouriko","No story/video was produced.",True)
