from pathlib import Path
import json,hashlib
D=Path(__file__).parent;M=D/'measurement';plan=json.loads((M/'plan.json').read_text());rows=json.loads((M/'rounds.json').read_text());blocks=json.loads((M/'blocks.json').read_text())
assert len(blocks)==15 and all(b['complete'] for b in blocks)
assert sum(x['warmup'] for x in rows)==4
assert sum(not x['warmup'] for x in rows)==30
assert len({x['name'] for x in rows})==34
assert hashlib.file_digest((M/'plan.json').open('rb'),'sha256').hexdigest()==json.loads((M/'plan-receipt.json').read_text())['sha256']
for file,key in [('measure.sh','measure_script_sha256'),('statistics_pilot.py','statistics_script_sha256'),('oracle-variants.sh','oracle_script_sha256')]:assert hashlib.file_digest((D/file).open('rb'),'sha256').hexdigest()==plan[key]
ref=json.loads((D/'stage2/oracles.json').read_text())['plat-tos']['caps'][0].split('caps = ',1)[1]
records=[];incomplete=[]
keys={'/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq','/sys/devices/system/cpu/cpufreq/policy0/cpuinfo_cur_freq','/sys/class/thermal/thermal_zone0/temp','/sys/class/hwmon/hwmon0/in0_lcrit_alarm'}
for row in rows:
 p=M/row['name'];receipt=json.loads((M/('receipt-'+row['name']+'.json')).read_text())
 actual={str(f.relative_to(p)):hashlib.file_digest(f.open('rb'),'sha256').hexdigest() for f in p.rglob('*') if f.is_file()};assert actual==receipt['files']
 caps=[l.split('caps = ',1)[1] for l in (p/'gst.log').read_text().splitlines() if 'GstFakeSink' in l and 'caps = ' in l];assert caps==[ref],(row['name'],caps)
 assert 'Got EOS' in (p/'gst.log').read_text()
 lines=(p/'telemetry.txt').read_text().splitlines()
 for i,l in enumerate(lines,1):
  xs=dict(t.rsplit('=',1) for t in l.split()[1:]);missing=keys-xs.keys();bad={k:v for k,v in xs.items() if not v.isdecimal()}
  if missing or bad:
   incomplete.append(dict(round=row['name'],line=i,missing=sorted(missing),invalid=bad,last_line=i==len(lines)));assert 'telemetry_unknown' in row['flags'],'unmarked incomplete telemetry'
 records.append(dict(name=row['name'],receipt_verified=True,caps_equal_oracle=True,eos=True,flags=row['flags']))
for prefix in ['', 'forensic/']:
 x=json.loads((D/'build'/prefix/'afdo/consumption.json').read_text());assert x['sha256']==x['expected']==plan['profile_sha256']
for b,o in zip(blocks,plan['order']):
 selected=[r for r in rows if not r['warmup'] and r['block']==b['block'] and r['attempt']==b['selected_attempt']]
 assert ''.join('A' if x['variant']=='base' else 'B' for x in selected)==o
out=dict(passed=True,plan_unchanged=True,scripts_unchanged=True,paired_blocks=15,timed_rounds=30,warmup_rounds=4,records=records,incomplete_telemetry=incomplete)
(M/'final-round-audit.json').write_text(json.dumps(out,indent=2)+'\n');print('15 blocks, receipts, scripts, order, caps/EOS and all telemetry records audited; partial rows',len(incomplete))
