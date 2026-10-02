"""Rhubarb lip-sync wrapper. Uses a preinstalled/downloaded rhubarb binary when available."""
import json, shutil, subprocess
from pathlib import Path
from common import ROOT
def sync(wav,out):
    exe=shutil.which("rhubarb") or shutil.which("Rhubarb")
    if not exe: raise RuntimeError("Rhubarb binary not installed")
    p=subprocess.run([exe,"-f","json","-o",str(out),str(wav)],capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr[-3000:])
    return json.loads(out.read_text())
