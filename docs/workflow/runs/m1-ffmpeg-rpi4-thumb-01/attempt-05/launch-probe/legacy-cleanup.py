import sys,json,os,subprocess,time
from pathlib import Path
w=Path.cwd();sys.path.insert(0,str(w/'workflow'))
from afdo_wf.transport import SDB
from afdo_wf.receipts import Cleanup
from afdo_wf.common import save,sha256,require
p=Path(__file__).parent;old=w/'temp/m1-ffmpeg-rpi4-thumb-01/attempt-04/formal'
t=SDB('192.168.108.26:26101',p/'legacy-transport');expected=json.loads((old.parent/'job.json').read_text())['identity'];require(t.identity()==expected,'wrong board')
c=Cleanup(p/'legacy-cleanup.json',expected);initial=dict(root=t.root_state(),governors=t.governors());save(p/'legacy-initial.json',initial)
error=None
try:
 if not initial['root']:c.register(dict(kind='root',previous=False));t.root(True)
 root=old/'stages/build/002/extracted';members={}
 for f in sorted((root/'usr/lib').glob('*.so*')):
  members[str(f.relative_to(root))]=dict(kind='link',target=os.readlink(f)) if f.is_symlink() else dict(kind='file',source=str(f),sha256=sha256(f))
 a=dict(kind='host_artifact',remote='/opt/afdo_agent/variants/m1-ffmpeg-rpi4-thumb-01-BASE',directory=True,members=members,verification=str(p/'legacy-BASE-verified.json'));c.register(a)
 # All old source scripts are materialized from the recorded commit, never from modified working files.
 members={};sources={}
 for log in old.glob('transport-*/*.json'):
  d=json.loads(log.read_text());argv=d.get('argv',[])
  if 'push' in argv and '/tools/workflow-' in argv[-1]:
   key=argv[-1].split('/')[-1]
   if key not in sources or d['start']>sources[key][0]:sources[key]=(d['start'],Path(argv[-2]))
 for name,(_,source) in sources.items():
  if source.is_relative_to(w/'workflow'):
   dest=p/'old-scripts'/name;dest.parent.mkdir(exist_ok=True)
   dest.write_bytes(subprocess.check_output(['git','show','e3b8409:'+str(source.relative_to(w))]));source=dest.resolve()
  members[name]=dict(kind='file',source=str(source),sha256=sha256(source))
 b=dict(kind='host_artifact',remote='/opt/afdo_agent/tools/workflow-m1-ffmpeg-rpi4-thumb-01',directory=True,members=members,verification=str(p/'legacy-tools-verified.json'));c.register(b)
 # Restore verifies every member before deleting either exact directory.
except BaseException as e:error=repr(e)
finally:
 errors=c.restore(t.identity(),t.undo)
 save(p/'legacy-final.json',dict(time=time.time(),error=error,errors=errors,pending=c.data['cleanup_pending'],root=t.root_state(),governors=t.governors()))
 print(error,errors,c.data['cleanup_pending'])
 if error or errors:sys.exit(1)
