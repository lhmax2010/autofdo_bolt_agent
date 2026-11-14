from pathlib import Path
import hashlib,json,subprocess,struct,zlib,re
W=Path.cwd();D=W/'temp/profgen-release-20261114c';B=W/'temp/GBS-ROOT-LLVM-RELEASE-20261114c';R=B/'local/repos/tizen_unified_standard/x86_64';X=D/'extracted';X.mkdir()
assert json.loads((D/'build-result.json').read_text())['gbs_exit']==0
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
rpms=[dict(path=str(p.relative_to(W)),size=p.stat().st_size,sha256=sha(p)) for p in sorted(R.glob('*/*.rpm'))]
(D/'rpm-manifest.json').write_text(json.dumps(rpms,indent=2))
jobs=[('llvm',['./usr/bin/llvm-profgen','./usr/bin/llvm-profdata']),('libllvm',['./usr/lib64/libLLVM*']),('llvm-debuginfo',['./usr/lib/debug/usr/bin/llvm-profgen.debug'])]
extract=[]
for name,patterns in jobs:
 rpm=R/'RPMS'/(name+'-22.1.8-1.x86_64.rpm');listing=subprocess.run(['rpm','-qlp',str(rpm)],capture_output=True,text=True);assert listing.returncode==0,listing.stderr
 (D/(name+'-rpm-files.txt')).write_text(listing.stdout+listing.stderr)
 with (D/(name+'-extract.log')).open('wb') as log:
  a=subprocess.Popen(['rpm2cpio',str(rpm)],stdout=subprocess.PIPE,stderr=log)
  b=subprocess.run(['cpio','-idm','--no-absolute-filenames']+patterns,cwd=X,stdin=a.stdout,stdout=log,stderr=log);a.stdout.close();ar=a.wait()
 assert ar==0 and b.returncode==0,(name,ar,b.returncode)
 extract.append(dict(rpm=str(rpm),patterns=patterns,rpm2cpio_exit=ar,cpio_exit=b.returncode))
tool=X/'usr/bin/llvm-profgen';debug=X/'usr/lib/debug/usr/bin/llvm-profgen.debug';assert tool.exists() and debug.exists()
notes={}
for name,path in [('runtime',tool),('debug',debug)]:
 q=subprocess.run(['readelf','-n',str(path)],capture_output=True,text=True);(D/(name+'-notes.txt')).write_text(q.stdout+q.stderr);assert q.returncode==0
 notes[name]=re.findall(r'Build ID: (\w+)',q.stdout)
data=tool.read_bytes();assert data[:6]==b'\x7fELF\x02\x01'
shoff=struct.unpack_from('<Q',data,40)[0];entsize,num,strings=struct.unpack_from('<HHH',data,58)
headers=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+i*entsize) for i in range(num)]
s=headers[strings];names=data[s[4]:s[4]+s[5]]
sections={names[h[0]:].split(b'\0',1)[0].decode():data[h[4]:h[4]+h[5]] for h in headers}
d=sections['.gnu_debuglink'];filename=d.split(b'\0',1)[0].decode();offset=(len(filename)+1+3)&~3;crc=struct.unpack_from('<I',d,offset)[0];actual=zlib.crc32(debug.read_bytes());assert filename==debug.name and crc==actual
settings=dict(tool=str(tool),root=str(B/'local/BUILD-ROOTS/scratch.x86_64.0'),libdir=str(X/'usr/lib64'),sha256=sha(tool))
(D/'release-tool.json').write_text(json.dumps(settings,indent=2))
root=Path(settings['root']);prefix=[str(root/'lib64/ld-linux-x86-64.so.2'),'--library-path',':'.join(map(str,[X/'usr/lib64',root/'lib64',root/'usr/lib64'])),str(tool)]
runs=[]
for flag in ['--version','--help']:
 q=subprocess.run(prefix+[flag],capture_output=True,text=True);(D/(flag[2:]+'.txt')).write_text(q.stdout+q.stderr);assert q.returncode==0,(flag,q.stderr);runs.append(dict(command=prefix+[flag],exit=q.returncode))
helptext=(D/'help.txt').read_text()
expected=['--ip-samples','--ip-event','--binary-match-regex','--ip-weight','--ip-aggregation','--ip-head-samples','--ip-zero-fill','--ip-skid','--quality-report','--ip-max-lost-ratio']
assert all(x in helptext for x in expected)
result=dict(tool_sha256=settings['sha256'],debug_sha256=sha(debug),build_ids=notes,debuglink=dict(name=filename,recorded_crc=crc,actual_crc=actual,match=crc==actual),extract=extract,tool_checks=runs,help_options=expected,rpm_count=len(rpms),rpm_bytes=sum(r['size'] for r in rpms))
(D/'artifact-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
