"""Local YouTube inventory for bots. Metadata is discovery evidence, not reuse approval."""
import argparse,json,datetime
from pathlib import Path
VIDEO={'.mp4','.mkv','.webm','.mov'}
def inventory(root):
 records=[];seen=set()
 for folder in ('downloads','clips','jobs'):
  base=root/folder
  if not base.exists():continue
  for f in sorted(base.rglob('*')):
   if f.suffix.lower() not in VIDEO or not f.is_file():continue
   target=f.resolve()
   if root not in target.parents or target in seen:continue
   seen.add(target);meta={};sidecar=f.with_suffix('.source.json')
   if sidecar.is_file():
    try:meta=json.loads(sidecar.read_text(encoding='utf-8-sig'))
    except (ValueError,OSError):pass
   records.append({'path':str(target),'relative_path':f.relative_to(root).as_posix(),'category':folder,'video_id':meta.get('video_id',f.stem),'title':meta.get('title',f.stem),'channel':meta.get('channel',''),'query':meta.get('query',''),'source_url':meta.get('source_url',''),'bytes':f.stat().st_size,'rights_status':meta.get('rights_status','NOT_VERIFIED')})
 return records

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path.home()/'Desktop/cody/youtube');p.add_argument('--query',default='');a=p.parse_args();root=a.root.resolve();root.mkdir(parents=True,exist_ok=True)
 records=inventory(root);payload={'schema':1,'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'items':records}
 temp=root/'index.json.partial';temp.write_text(json.dumps(payload,indent=2),encoding='utf-8');temp.replace(root/'index.json')
 terms=a.query.casefold().split();matches=[r for r in records if all(t in ' '.join(str(v) for v in r.values()).casefold() for t in terms)]
 print(json.dumps({'index':str(root/'index.json'),'total':len(records),'matches':matches},indent=2))
if __name__=='__main__':main()
