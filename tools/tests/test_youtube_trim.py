"""Exercise actual FFmpeg trim and reject unsafe/invalid edits; no network."""
import hashlib,importlib.util,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d);src=p/'source.mp4'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=160x90:r=30','-f','lavfi','-i','sine=frequency=440:sample_rate=24000','-t','3','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(src)],check=True)
  original=hashlib.sha256(src.read_bytes()).hexdigest()
  base=[sys.executable,str(ROOT/'tools/windows/trim-video.py'),'--source',str(src)]
  def run(extra,ok=True):
   r=subprocess.run(base+extra,capture_output=True,text=True)
   assert (r.returncode==0)==ok,(r.stdout,r.stderr)
   return r
  out=p/'clip.mp4';r=run(['--output',str(out),'--start','00:00:00.5','--end','00:00:02']);assert abs(json.loads(r.stdout)['duration']-1.5)<.15
  streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out)],text=True))['streams'];assert any(s['codec_type']=='audio' for s in streams)
  mute=p/'mute.mp4';run(['--output',str(mute),'--start','0','--duration','1','--mute'])
  streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(mute)],text=True))['streams'];assert not any(s['codec_type']=='audio' for s in streams)
  for dest,start,duration in [(out,'0','1'),(src,'0','1'),(p/'bad.mp4','2','5'),(p/'bad.mp4','nan','1'),(p/'bad.mp4','0','0')]:run(['--output',str(dest),'--start',start,'--duration',duration],False)
  assert hashlib.sha256(src.read_bytes()).hexdigest()==original
  print('PASS: timed trim, audio retention/mute, complete decode, overwrite/source/range/nonfinite guards; source SHA256 unchanged')
if __name__=='__main__':main()
