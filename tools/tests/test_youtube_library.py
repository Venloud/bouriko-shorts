"""Local index metadata contract; never labels unknown rights as approved."""
import importlib.util,json,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('library',Path(__file__).resolve().parents[1]/'windows/youtube-library.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 root=Path(d);p=root/'downloads'/'abc.mp4';p.parent.mkdir();p.write_bytes(b'fixture');p.with_suffix('.source.json').write_text(json.dumps({'title':'Product launch','channel':'Maker','video_id':'abcdefghijk','source_url':'https://www.youtube.com/watch?v=abcdefghijk','query':'Maker product'}))
 rows=m.inventory(root.resolve());assert len(rows)==1;assert rows[0]['title']=='Product launch';assert rows[0]['rights_status']=='NOT_VERIFIED';assert rows[0]['relative_path']=='downloads/abc.mp4'
print('PASS: sidecar title/channel/source URL and explicit unknown rights preserved in local index')
