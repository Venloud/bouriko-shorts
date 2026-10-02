"""Shared Bouriko pipeline helpers."""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CONFIG=json.loads((ROOT/"config.json").read_text())
HISTORY=ROOT/"data/history.json"
def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}",flush=True)
def env(name,required=True,default=""):
    v=os.getenv(name,default).strip()
    if required and not v: raise RuntimeError(f"Missing required env: {name}")
    return v
def retry(fn,attempts=3,wait=3):
    last=None
    for i in range(attempts):
        try:return fn()
        except Exception as e:
            last=e; log(f"retry {i+1}/{attempts}: {e}")
            if i+1<attempts: time.sleep(wait*(i+1))
    raise last
def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr[-4000:])
    return p.stdout
def duration(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)]).strip())
def load_history():
    return json.loads(HISTORY.read_text()) if HISTORY.exists() else []
def save_history(h):
    HISTORY.parent.mkdir(parents=True,exist_ok=True); HISTORY.write_text(json.dumps(h,indent=2))
def choose_model():
    return CONFIG.get("llm_models",["gemini-3.8-flash"])[0]
