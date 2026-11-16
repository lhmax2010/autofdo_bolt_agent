from common import *
D=D/'stage2';D.mkdir(exist_ok=True)
uid=None;gov={};result={}
try:
 ev=json.loads((D.parent/'cycles-evlist.json').read_text())
 assert re.search(r'^cycles:',ev) and re.search(r'\btype:\s*0\b',ev) and re.search(r'\bconfig:\s*0\b',ev)
 save('cycles-parser-correction.json',{'valid':True,'reason':'type/config fields have colons; stage1 parser false rejection; original bytes retained'})
 uid=shell('initial-uid','id -u');gov=dict(l.split('=',1) for l in shell('initial-governors','for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do printf "%s=" "$p"; cat "$p"; done').splitlines());save('initial-state.json',dict(uid=uid,governors=gov))
 # restore() is defined in common globals; explicitly propagate state.
 import common
 common.D=D;common.uid=uid;common.gov=gov;common.result=result
 if uid!='0':run('root-on',['sdb','-s','192.168.108.26:26101','root','on'])
 tele=shell('telemetry-capability','set -e; for p in /sys/devices/system/cpu/cpufreq/policy*; do for f in scaling_governor scaling_cur_freq cpuinfo_cur_freq scaling_min_freq scaling_max_freq; do printf "%s=" "$p/$f"; cat "$p/$f"; done; done; for z in /sys/class/thermal/thermal_zone*; do printf "%s " "$z"; cat "$z/type" "$z/temp"; done; for h in /sys/class/hwmon/hwmon*; do printf "%s " "$h"; cat "$h/name"; if test -e "$h/in0_lcrit_alarm"; then cat "$h/in0_lcrit_alarm"; fi; done')
 save('telemetry-capability.json',tele)
 push(D.parent/'oracle.sh',R+'/oracle.sh')
 oracles={}
 for variant in ['PLAT','BASE']:
  for clip in ['bbb','tos']:
   name=variant.lower()+'-'+clip
   shell('oracle-'+name,'bash '+R+'/oracle.sh '+name+' '+B+'/inputs/'+clip+'_720p_h264_60s.mp4 '+variant,600)
   local=D/name;local.mkdir(exist_ok=True)
   run('pull-'+name,['sdb','-s','192.168.108.26:26101','pull',R+'/'+name,str(local)],120)
   # sdb may add final directory component.
   fs=list(local.rglob('decoded.sha256'));assert len(fs)==1; p=fs[0].parent
   maps=(p/'decoder.maps').read_text();paths=sorted(set(l.split()[-1] for l in maps.splitlines() if 'libavcodec.so' in l or 'libavutil.so' in l))
   assert len(paths)==2
   for path in paths:
    if variant=='BASE':assert path.startswith(B+'/variants/m1p-base/lib/')
    else:assert path.startswith('/usr/lib/')
   log=(p/'gst.log').read_text(); caps=[l for l in log.splitlines() if 'GstFileSink' in l and 'caps =' in l]
   nbytes=int((p/'decoded.bytes').read_text());count=int((p/'frame-notifications.count').read_text());digest=fs[0].read_text().split()[0]
   assert nbytes>0 and caps and 'Got EOS' in log
   oracles[name]=dict(bytes=nbytes,frame_notifications=count,sha256=digest,caps=caps,paths=paths)
   save('oracles.json',oracles)
   if variant=='BASE':
    ref=oracles['plat-'+clip]
    assert (digest,nbytes,count)==(ref['sha256'],ref['bytes'],ref['frame_notifications']),'BASE vs PLAT mismatch '+clip
 result['success']=True
except BaseException as e:result['success']=False;result['error']=repr(e)
finally:
 common.restore();save('result.json',result)
print(json.dumps(result,indent=2))
