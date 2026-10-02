import os,requests
from pathlib import Path
from youtube import upload as yt_upload
from common import ROOT,log
def refresh_tiktok():
    r=requests.post("https://open.tiktokapis.com/v2/oauth/token/",headers={"Content-Type":"application/x-www-form-urlencoded"},data={"client_key":os.environ["TIKTOK_CLIENT_KEY"],"client_secret":os.environ["TIKTOK_CLIENT_SECRET"],"grant_type":"refresh_token","refresh_token":os.environ["TIKTOK_REFRESH_TOKEN"]},timeout=30)
    r.raise_for_status(); d=r.json()
    if d.get("refresh_token"): (ROOT/".new_refresh_token").write_text(d["refresh_token"])
    return d["access_token"]
def tiktok_draft(path,token):
    size=path.stat().st_size
    r=requests.post("https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},json={"source_info":{"source":"FILE_UPLOAD","video_size":size,"chunk_size":size,"total_chunk_count":1}},timeout=30)
    r.raise_for_status(); d=r.json()["data"]
    with path.open("rb") as f:
        u=requests.put(d["upload_url"],headers={"Content-Range":f"bytes 0-{size-1}/{size}","Content-Type":"video/mp4"},data=f,timeout=120)
    u.raise_for_status(); return "TikTok draft uploaded"
def main():
    mp4=Path(os.getenv("VIDEO","output/bouriko.mp4"))
    if not mp4.exists(): raise SystemExit("No video to publish")
    token=refresh_tiktok(); log(tiktok_draft(mp4,token))
    title=os.getenv("VIDEO_TITLE","Bouriko")
    if all(os.getenv(k) for k in ("YT_CLIENT_ID","YT_CLIENT_SECRET","YT_REFRESH_TOKEN")):
        log("YouTube: "+yt_upload(mp4,title,os.getenv("VIDEO_DESCRIPTION",""),["Bouriko","tech","shorts"]))
if __name__=="__main__": main()
