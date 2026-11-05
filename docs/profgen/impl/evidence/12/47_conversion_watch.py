from pathlib import Path
import json,subprocess,hashlib,time,re,os,datetime
w=Path.cwd();d=w/'temp/board-round1-patch8';r=w/'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0';l=w/'temp/llvm-profgen-enh';tool=l/'build/bin/llvm-profgen'
sha=hashlib.sha256(tool.read_bytes()).hexdigest();assert sha=='41440292c7cf3a380a6779dfea6d06ff74a22e18537127561829bf989bb16413'
art={x['id']:x for x in json.loads((w/'temp/eval-prep11/artifact-summary.json').read_text())};manifest={x.split('\t')[0]:x.split('\t') for x in (w/'temp/eval-prep11/payload-rpi4/eval-manifest.tsv').read_text().splitlines()}
result=json.loads((d/'reconverted.json').read_text());seen={x['source'] for x in result['runs']};success=False;reason=None
try:
 while True:
  try:rows=json.loads((d/'runs.json').read_text())
  except (FileNotFoundError,json.JSONDecodeError):rows=[]
  for row in rows:
   if not row['mode'].startswith('sample') or row['rc'] or row['local'] in seen:continue
   source=Path(row['local']);variant=row['variant'];out=d/'converted'/source.name;out.mkdir(exist_ok=True);a=art[variant];target=manifest[variant][6]
   cmd=['nice','-n','19','ionice','-c3',str(r/'lib64/ld-linux-x86-64.so.2'),'--library-path',f'{l}/build/lib64:{r}/lib64:{r}/usr/lib64',str(tool),'--ip-samples','--binary='+a['runtime']['path'],'--debug-binary='+a['debug']['path'],'--binary-match-regex=^'+re.escape(target)+'$','--perfscript='+str(source/'perfscript.txt'),'--perf-buildid-list='+str(source/'buildid-list.txt'),'--ip-weight=sample','--ip-aggregation=sum','--ip-head-samples=none','--ip-zero-fill=none','--ip-skid=none','--format=extbinary','--show-ip-address-counts','--output='+str(out/'profile.extbinary'),'--quality-report='+str(out/'quality.json')]
   t=time.monotonic()
   with (out/'stdout').open('w') as o,(out/'stderr').open('w') as e:p=subprocess.run(cmd,stdout=o,stderr=e)
   q=json.loads((out/'quality.json').read_text());x=dict(source=str(source),variant=variant,command=cmd,exit=p.returncode,seconds=time.monotonic()-t,expected_target=row['target_samples'],quality=q,old_classification=None,profile_sha256=hashlib.sha256((out/'profile.extbinary').read_bytes()).hexdigest() if (out/'profile.extbinary').exists() else None,diagnostic_counts=[line for line in (out/'stdout').read_text().splitlines() if line.startswith('IP-GENERATION ')])
   result['runs'].append(x);tmp=d/'reconverted.json.tmp';tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(d/'reconverted.json')
   assert p.returncode==0,(out/'stderr').read_text()
   assert q['identity']['grade']=='verified' and q['samples']['target']['counts']['sample_count']==row['target_samples']
   if row['mode']=='sample-freq':
    period=[v.replace('--ip-weight=sample','--ip-weight=period').replace(str(out/'profile.extbinary'),str(out/'profile-period.extbinary')).replace(str(out/'quality.json'),str(out/'quality-period.json')) for v in cmd]+['--ip-period-unit=1000003']
    with (out/'period.stdout').open('w') as o,(out/'period.stderr').open('w') as e:p=subprocess.run(period,stdout=o,stderr=e)
    (out/'period-command.json').write_text(json.dumps(dict(command=period,exit=p.returncode),indent=2)+'\n');assert not p.returncode
   seen.add(str(source));print('CONVERTED',source.name,'target',row['target_samples'],'normalizations',q['thumb_dwarf_normalization']['range_count'],'aliases',q['thumb_dwarf_normalization']['alias_query_count'],flush=True)
  if (d/'matrix.status').exists() and 'ALL-END' in (d/'matrix.status').read_text():break
  time.sleep(20)
 success=True
except BaseException as e:
 reason=repr(e);(d/'STOP_REQUESTED').write_text('host conversion failed: '+reason+'\n');print('HOST_CONVERSION_FAILED',reason,flush=True)
finally:
 (d/'conversion-watch.status').write_text('ALL-END '+datetime.datetime.now().astimezone().isoformat()+' '+('OK' if success else 'FAILED')+' '+str(reason)+'\n')
