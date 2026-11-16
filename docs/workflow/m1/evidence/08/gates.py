exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
from collections import Counter
D=D/'build';OPS_FILE='gate-operations.json';ops=[];result={'passed':False}
try:
 assert json.loads((D/'result.json').read_text())['success']
 assert json.loads((D/'forensic/result.json').read_text())['success']
 baseline=(D/'BASE.rpm-lock.txt').read_text()
 for v in ['base-r','afdo']:
  assert (D/v/'rpm-lock.txt').read_text()==baseline
  assert (D/'forensic'/v/'rpm-lock.txt').read_text()==baseline
  main=json.loads((D/v/'artifacts.json').read_text());forensic=json.loads((D/'forensic'/v/'artifacts.json').read_text())
  assert main==forensic,'forensic artifact mismatch '+v
 # Full actual commands are captured by separate V=1 builds; equality to main build files checked above.
 commands={};details={}
 for v in ['base-r','afdo']:
  cmd=[];records=[];unhandled=[]
  for i,l in enumerate((D/'forensic'/v/'build.log').read_text().splitlines(),1):
   l=re.sub(r'^\[\s*\d+s\]\s?','',l)
   if not re.match(r'^(clang(?:\+\+)?|gcc|g\+\+|cc|c\+\+|ld|as)(?:\s)',l):continue
   a=shlex.split(l)
   if '-o' not in a:continue
   records.append(dict(line=i,argv=a))
   normalized=[x for x in a if not x.startswith('-fprofile-sample-use=')];cmd.append(normalized)
  assert len(cmd)>600,('command capture incomplete',v,len(cmd))
  commands[v]=Counter(json.dumps(a,ensure_ascii=False) for a in cmd);details[v]=records;save(v+'/compile-link-commands.json',records)
 removed_a=list((commands['base-r']-commands.get('afdo',Counter())).elements()) if False else []
 differences={'base_r_only':list((commands['base-r']-commands['afdo']).elements()),'afdo_only':list((commands['afdo']-commands['base-r']).elements())};save('command-differences.json',differences)
 assert not any(differences.values()),'compile/link gate failed'
 baselinefiles=json.loads((W/'temp/m1-pilot-v02-20261116/base-manifest.json').read_text());r=json.loads((D/'base-r/artifacts.json').read_text());a=json.loads((D/'afdo/artifacts.json').read_text())
 assert all(x['sha256']==next(y for y in r if y['name']==P.Path(x['path']).name)['sha256'] for x in baselinefiles),'BASE-r differs'
 for x in a:
  if 'build_id' in x:
   y=next(t for t in r if t['name']==x['name']);assert x['build_id']!=y['build_id'] and x['text_sha256']!=y['text_sha256']
 consumption=json.loads((D/'afdo/consumption.json').read_text());assert consumption['sha256']==consumption['expected']
 flags=sum(any(x.startswith('-fprofile-sample-use=') for x in r['argv']) for r in details['afdo']);assert flags>0
 result.update(passed=True,control='BASE',packages=len(baseline.splitlines()),commands={k:len(v) for k,v in details.items()},afdo_profile_flag_commands=flags,forensic_artifacts_equal_primary=True,base_r_equal_base=True,target_code_changed=True)
except BaseException as e:result['error']=repr(e)
save('gates.json',result);print(json.dumps(result,indent=2))
