from pathlib import Path
import subprocess,json,hashlib
W=Path.cwd();D=W/'temp/profgen-release-20261114c';g=['git','-c','gc.auto=0','-c','maintenance.auto=false']
url=subprocess.check_output(g+['-C',str(W/'src/llvm'),'remote','get-url','origin'],text=True).strip();branch='refs/heads/sandbox/lhmax2025/afdo_profgen';head='c8942ae1b53099a78a97dca2b64427af6e58432b'
q=subprocess.run(g+['ls-remote',url,branch],capture_output=True,text=True);assert q.returncode==0;assert q.stdout.split()[0]==head;qout=q.stdout
V=W/'temp/llvm-profgen-sandbox-verify-20261114';assert not V.exists();subprocess.run(g+['init',str(V)],check=True);subprocess.run(g+['-C',str(V),'remote','add','origin',url],check=True)
commands=[['fetch','--depth=10','--no-tags','origin',branch+':refs/remotes/origin/sandbox/lhmax2025/afdo_profgen'],['checkout','--detach',head]]
for cmd in commands:subprocess.run(g+['-C',str(V)]+cmd,check=True)
source=json.loads((D/'postbuild-source-equivalence.json').read_text())['files']
for f in source:assert hashlib.sha256((V/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
assert subprocess.check_output(g+['-C',str(V),'status','--porcelain']).strip()==b''
result=dict(remote_ref=branch,remote_tip=head,ls_remote=qout,clone=str(V),fetch_commands=commands,verified_files=len(source),all_file_sha256_equal=True)
(D/'sandbox-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
