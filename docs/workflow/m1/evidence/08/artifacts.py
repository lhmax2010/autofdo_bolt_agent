exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
import sys,shutil
OPS_FILE='artifact-operations.json'
mode=sys.argv[1] if len(sys.argv)>1 else 'primary';D=D/'build';D=D/'forensic' if mode=='forensic' else D;ops=[];outputs={}
for variant in ['base-r','afdo']:
 o=D/variant
 if not (o/'result.json').exists() or json.loads((o/'result.json').read_text())['exit']!=0:continue
 root=P.Path(json.loads((o/'result.json').read_text())['buildroot']);ext=o/'extracted';ext.mkdir(exist_ok=True);rpms=[]
 for p in sorted((root/'local/repos').rglob('*.rpm')):
  n=run('rpm-name',['rpm','-qp','--qf','%{NAME}',str(p)]);rpms.append(dict(name=n,path=str(p),sha256=sha(p)))
  if n.startswith('lib') and (('-' not in n) or n in ['libavcodec-debuginfo','libavutil-debuginfo']):
   cp=o/(n+'.cpio')
   with cp.open('wb') as out:sp.run(['rpm2cpio',str(p)],stdout=out,check=True)
   run('extract-'+n,['bash','-c','cd "$1" && cpio -idm --quiet < "$2"','bash',str(ext),str(cp)])
 save(variant+'/rpms.json',rpms);files=[]
 for p in sorted((ext/'usr/lib').glob('lib*.so*')):
  row=dict(name=p.name,sha256=sha(p),symlink=os.readlink(p) if p.is_symlink() else None)
  if not p.is_symlink() and p.name.startswith(('libavcodec.','libavutil.')):
   debug=ext/'usr/lib/debug/usr/lib'/(p.name+'.debug');ids=[]
   for f in [p,debug]:
    txt=run('readelf-notes',['readelf','-n',str(f)]);ids.append(re.findall(r'Build ID: ([0-9a-f]+)',txt)[0])
   assert ids[0]==ids[1] and len(ids[0])==40;row.update(build_id=ids[0],debug_build_id=ids[1],debug_sha256=sha(debug))
   sec=run('sections',['readelf','-SW',str(p)]);m=re.search(r'\[\s*\d+\]\s+\.text\s+\S+\s+[0-9a-f]+\s+([0-9a-f]+)\s+([0-9a-f]+)',sec);assert m
   with p.open('rb') as f:f.seek(int(m[1],16));code=f.read(int(m[2],16))
   row['text_sha256']=hashlib.sha256(code).hexdigest()
  files.append(row)
 save(variant+'/artifacts.json',files);outputs[variant]=files
 if variant=='afdo':
  profile=root/'local/BUILD-ROOTS/scratch.armv7l.0/home/abuild/rpmbuild/SOURCES/autofdo.extbinary'
  save(variant+'/consumption.json',dict(chroot_profile=str(profile),sha256=sha(profile),expected=json.loads((W/'temp/m1-pilot-v02-20261116/conversion/locked-profile.json').read_text())['sha256']))
 save('artifact-operations.json',ops)
print(json.dumps({k:len(v) for k,v in outputs.items()}))
