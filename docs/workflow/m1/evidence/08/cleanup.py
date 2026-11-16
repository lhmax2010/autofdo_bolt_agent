exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
D=D/'cleanup';D.mkdir(exist_ok=True);ops=[];result={}
original=json.loads((D.parent/'stage3/initial-state.json').read_text());uid=original['uid'];gov=original['governors']
try:
 now=shell('cleanup-entry-uid','id -u')
 if now!='0':run('root-on',['sdb','-s','192.168.108.26:26101','root','on'])
 shell('remaining-task-processes',"ps -eo pid,args | grep -E 'gst-launch|oracle-variants.sh|measure.sh|collect.sh|watchdog.sh' || true")
 assert R=='/opt/afdo_agent/work/m1p-v02-20261116'
 assert shell('canonical-work','readlink -f '+R)==R
 manifest=shell('remaining-manifest','cd '+R+' && find . -type f -exec sha256sum {} \\;');save('remaining-manifest.json',manifest)
 tar=B+'/work/m1p-v02-20261116-cleanup.tar'
 shell('archive-remaining','test ! -e '+tar+' && tar -cf '+tar+' -C '+R+' .',180)
 h=shell('archive-sha','sha256sum '+tar).split()[0]
 local=D/'remaining-board-work.tar';run('pull-remaining',['sdb','-s','192.168.108.26:26101','pull',tar,str(local)],180);assert sha(local)==h
 save('verified-pull-receipt.json',dict(time=datetime.datetime.now().astimezone().isoformat(),remote=R,archive=tar,local=str(local),sha256=h,verified=True,manifest_sha256=sha(D/'remaining-manifest.json')))
 assert shell('recheck-remaining-manifest','cd '+R+' && find . -type f -exec sha256sum {} \\;')==manifest
 shell('delete-own-work','rm -rf -- '+R+' && rm -- '+tar+' && test ! -e '+R)
 result['work_removed']=True
 result['retained_variants']=shell('retained-variants','find '+B+'/variants/m1p-base '+B+'/variants/m1p-afdo -type f -exec sha256sum {} \\;')
 result['rpm_count']=shell('rpm-count','rpm -qa | wc -l')
 result['success']=True
except BaseException as e:result['success']=False;result['error']=repr(e)
finally:
 restore()
 try:result['final_governors']=shell('final-governors','for p in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor; do printf "%s=" "$p"; cat "$p"; done')
 except Exception as e:result.setdefault('cleanup_pending',[]).append(repr(e))
 save('result.json',result)
print(json.dumps(result,indent=2))
