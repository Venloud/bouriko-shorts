"""Local output buffer. GitHub Actions can archive these files as artifacts/releases."""
from pathlib import Path
from common import ROOT
BUFFER=ROOT/"buffer"
def ensure(): BUFFER.mkdir(exist_ok=True); return BUFFER
def videos():
    ensure(); return sorted(BUFFER.glob("*.mp4"))
def oldest(): 
    v=videos()
    return v[0] if v else None
