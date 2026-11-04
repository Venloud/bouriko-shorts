"""Frame-accurate local trim. Preserve aspect ratio/audio; never overwrite inputs."""
import argparse,json,math,os,subprocess,tempfile
from pathlib import Path

def seconds(value):
 try:
  parts=[float(v) for v in str(value).split(':')]
  if len(parts)>3 or any(not math.isfinite(v) or v<0 for v in parts):raise ValueError()
  if len(parts)>1 and any(v>=60 for v in parts[1:]):raise ValueError()
  return sum(v*60**i for i,v in enumerate(reversed(parts)))
 except ValueError:raise argparse.ArgumentTypeError('Use nonnegative seconds or HH:MM:SS.mmm')
def probe(path):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--start',type=seconds,required=True)
 g=p.add_mutually_exclusive_group(required=True);g.add_argument('--end',type=seconds);g.add_argument('--duration',type=seconds)
 p.add_argument('--mute',action='store_true');a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
 if src==out or out.exists():p.error('Output must be a new file, different from source')
 if out.suffix.lower()!='.mp4':p.error('Output must end in .mp4')
 info=probe(src);total=float(info['format']['duration']);length=a.duration if a.duration is not None else a.end-a.start
 if not math.isfinite(length) or length<=0 or a.start+length>total+.001:p.error('Invalid trim interval or interval exceeds source')
 if not any(s['codec_type']=='video' for s in info['streams']):p.error('Source has no video')
 out.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix='trim-',suffix='.mp4',dir=out.parent);os.close(fd);tmp=Path(tmp)
 try:
  cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(src),'-ss',str(a.start),'-t',str(length),'-map','0:v:0','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p']
  cmd+=['-an'] if a.mute else ['-map','0:a:0?','-c:a','aac','-b:a','192k']
  subprocess.run(cmd+['-movflags','+faststart',str(tmp)],check=True)
  result=probe(tmp);actual=float(result['format']['duration']);video=next(s for s in result['streams'] if s['codec_type']=='video')
  if abs(actual-length)>max(.15,2/float(video.get('avg_frame_rate','30/1').split('/')[0] or 30)):raise RuntimeError('Trim duration outside tolerance')
  subprocess.run(['ffmpeg','-v','error','-i',str(tmp),'-f','null','-'],check=True)
  # Atomic exclusive publication: an existing destination cannot be overwritten.
  os.link(tmp,out)
  print(json.dumps({'status':'VERIFIED_TRIM','source':str(src),'clip':str(out),'start':a.start,'duration':actual,'dimensions':[video['width'],video['height']],'audio':'removed' if a.mute else 'preserved if source has audio'}))
 finally:tmp.unlink(missing_ok=True)
if __name__=='__main__':main()
