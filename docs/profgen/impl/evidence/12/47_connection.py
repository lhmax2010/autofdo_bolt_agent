import subprocess,json,datetime,pathlib,re
W=pathlib.Path('/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent'); D=W/'temp/board-round1-patch8'; device='192.168.108.26:26101'
def call(args,timeout=60):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 r=dict(time=datetime.datetime.now().astimezone().isoformat(),command=args,rc=p.returncode,stdout=p.stdout,stderr=p.stderr)
 with (D/'operations.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
 return p
def shell(c,timeout=60):
 p=call(['sdb','-s',device,'shell','( '+c+' ); r=$?; printf "\\n__REMOTE_RC=%s\\n" "$r"'],timeout)
 m=re.search(r'\n__REMOTE_RC=(\d+)\s*$',p.stdout)
 if p.returncode or not m or int(m[1]):raise RuntimeError(str((c,p.returncode,p.stdout,p.stderr)))
 return p.stdout[:m.start()].replace('\x00','').strip()
