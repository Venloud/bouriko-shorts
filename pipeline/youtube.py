import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
def upload(path,title,description="",tags=None,privacy="public"):
    c=Credentials(None,refresh_token=os.environ["YT_REFRESH_TOKEN"],client_id=os.environ["YT_CLIENT_ID"],client_secret=os.environ["YT_CLIENT_SECRET"],token_uri="https://oauth2.googleapis.com/token",scopes=["https://www.googleapis.com/auth/youtube.upload"])
    yt=build("youtube","v3",credentials=c)
    body={"snippet":{"title":title[:100],"description":description[:5000],"tags":tags or []},"status":{"privacyStatus":privacy,"selfDeclaredMadeForKids":False}}
    r=yt.videos().insert(part="snippet,status",body=body,media_body=MediaFileUpload(str(path),chunksize=-1,resumable=True)).execute()
    return "https://youtu.be/"+r["id"]
