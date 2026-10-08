import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'output/story.json'
s=json.loads(p.read_text())
manifest=[]
for i,line in enumerate(s['lines']):
    line['media_kind']='motion_graphic'
    line.pop('media_asset',None)
    manifest.append({'scene':i,'kind':'motion_graphic','provider':'remotion','visual_type':line['anime_visual_type']})
p.write_text(json.dumps(s,indent=2))
(root/'output/media_manifest.json').write_text(json.dumps(manifest,indent=2))
(root/'output/scene_matches.json').write_text(json.dumps([{'scene':i,'status':'graphic'} for i in range(len(manifest))],indent=2))
print('Prepared',len(manifest),'animated scenes')
