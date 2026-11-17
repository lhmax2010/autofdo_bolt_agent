from pathlib import Path
import os,sys,json,time,subprocess,signal
w=Path.cwd();d=w/'temp/m1-ffmpeg-rpi4-thumb-01/attempt-04'
sys.path.insert(0,str(w/'workflow'))
from afdo_wf.common import save,sha256
from afdo_wf.build import resources
env=os.environ.copy();env['PYTHONPATH']=str(w/'workflow');env['TMPDIR']=str(w/'temp/tmp')
cmd=[sys.executable,'-m','afdo_wf','run','--job',str(d/'job.json')]
cg=Path('/sys/fs/cgroup'+next(l.split(':',2)[2] for l in Path('/proc/self/cgroup').read_text().splitlines() if l.startswith('0:')))
events=[];results=[];start=time.time();last=0
def sample():
    global last
    r=resources(w)
    for key in ['memory.current','memory.peak','memory.events']:
        p=cg/key
        if p.exists():r[key]=p.read_text().strip()
    events.append(r);save(d/'driver-resources.json',events);last=time.monotonic()
sample()
try:
    for attempt in [1,2]:
        killed=False
        with (d/('workflow-run-'+str(attempt)+'.log')).open('w') as log:
            p=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
            save(d/('workflow-launch-'+str(attempt)+'.json'),dict(argv=cmd,pid=p.pid,time=time.time(),job_sha256=sha256(d/'job.json')))
            try:
                while p.poll() is None:
                    if time.monotonic()-last>=60:sample()
                    active=d/'formal/conversion-active.json'
                    if attempt==1 and not killed and active.exists():
                        v=json.loads(active.read_text())
                        progress=json.loads((d/'formal/progress.json').read_text())
                        if progress['stage']=='convert' and progress['status']=='running':
                            assert (d/'formal/receipts/collect.json').exists()
                            os.kill(p.pid,signal.SIGTERM);killed=True
                            save(d/'recovery-interruption.json',dict(time=time.time(),host_pid=p.pid,conversion=v,signal='SIGTERM',collect_receipt_sha256=sha256(d/'formal/receipts/collect.json')))
                    time.sleep(.025)
                rc=p.wait()
            finally:
                if p.poll() is None:p.terminate();p.wait(timeout=180)
        result=dict(attempt=attempt,exit_code=rc,interrupted_for_test=killed,end=time.time());results.append(result);save(d/'driver-results.json',results)
        if not killed:break
        finals=sorted((d/'formal').glob('final-*.json'));assert finals
        final=json.loads(finals[-1].read_text());assert final['cleanup_pending']==[] and not final['errors']
        assert rc!=0
finally:
    sample();save(d/'driver-end.json',dict(start=start,end=time.time(),seconds=time.time()-start,results=results))
    with (d/'ALL-END.log').open('a') as f:f.write('ALL-END 已结束 '+str(time.time())+' '+json.dumps(results)+'\n')
print(json.dumps(results))
raise SystemExit(results[-1]['exit_code'] if results else 1)
