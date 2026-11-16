import subprocess as sp, pathlib as P, json, hashlib, datetime, re, shlex, os, signal
W=P.Path.cwd(); D=W/'temp/m1-pilot-v02-20261116'; B='/opt/afdo_agent'; R=B+'/work/m1p-v02-20261116'; ops=[]
def save(n,x):
 p=D/n
 with p.open('w') as f: json.dump(x,f,indent=2,ensure_ascii=False); f.write('\n'); f.flush(); os.fsync(f.fileno())
def run(n,a,timeout=120,check=True):
 t=datetime.datetime.now().astimezone().isoformat()
 try:
  q=sp.run(a,capture_output=True,text=True,timeout=timeout); d=dict(name=n,time=t,argv=a,exit=q.returncode,stdout=q.stdout,stderr=q.stderr)
 except BaseException as e:
  d=dict(name=n,time=t,argv=a,error=repr(e));ops.append(d);save(globals().get('OPS_FILE','operations.json'),ops);raise
 ops.append(d);save(globals().get('OPS_FILE','operations.json'),ops)
 if check and q.returncode: raise RuntimeError(n+': '+q.stderr+q.stdout)
 return q.stdout
def shell(n,c,timeout=120):
 o=run(n,['sdb','-s','192.168.108.26:26101','shell','( '+c+' ); rc=$?; printf "\\n__M1P_RC__=%s\\n" "$rc"'],timeout)
 m=re.search(r'\n__M1P_RC__=(\d+)\s*$',o)
 if not m or m[1]!='0':raise RuntimeError(n+': '+o)
 return o[:m.start()].replace('\r\n','\n').rstrip()
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def push(p,t):run('push-'+str(p),['sdb','-s','192.168.108.26:26101','push',str(p),t])
def restore():
 global uid
 errors=[]
 if gov:
  for p,v in gov.items():
   try:
    now=shell('restore-read-governor','cat '+shlex.quote(p))
    if now!=v:shell('restore-governor','printf %s '+shlex.quote(v)+' > '+shlex.quote(p))
   except BaseException as e:errors.append(repr(e))
 if uid is not None:
  try:
   now=shell('restore-read-uid','id -u')
   if now!=uid:run('root-restore',['sdb','-s','192.168.108.26:26101','root','on' if uid=='0' else 'off'])
   result['final_uid']=shell('final-uid','id -u'); assert result['final_uid']==uid
  except BaseException as e:errors.append(repr(e))
 result['cleanup_pending']=errors
def _task_interrupt(sig,frame):
 raise KeyboardInterrupt('task signal '+str(sig))
signal.signal(signal.SIGTERM,_task_interrupt)
signal.signal(signal.SIGINT,_task_interrupt)
