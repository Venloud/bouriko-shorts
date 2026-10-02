import json
from pathlib import Path
from common import ROOT
STATE=ROOT/"data/checkpoint.json"
def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}
def save(**kwargs):
    s=load(); s.update(kwargs); STATE.parent.mkdir(parents=True,exist_ok=True); STATE.write_text(json.dumps(s,indent=2))
