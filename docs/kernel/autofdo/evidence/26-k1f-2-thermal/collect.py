import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

out=Path(sys.argv[1])
sdb=['sdb','-s','192.168.108.26:26101']
identity='id -u; uname -rm; cat /proc/sys/kernel/random/boot_id; sha256sum /sys/kernel/notes; tr -d "\\000" </proc/device-tree/serial-number; echo'
boot='656d98ce-abdc-47e2-9f04-deffc0979c68'

def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def invoke(argv,timeout):
    try:
        p=subprocess.run(argv,capture_output=True,timeout=timeout)
        return dict(rc=p.returncode,output=p.stdout.decode('utf-8','replace').replace('\r\n','\n'),
                    stderr=p.stderr.decode('utf-8','replace').replace('\r\n','\n'))
    except subprocess.TimeoutExpired as e:
        cv=lambda data: (data or b'').decode('utf-8','replace').replace('\r\n','\n')
        return dict(rc=124,output=cv(e.stdout),stderr=cv(e.stderr))

def log(name,data):
    (out/name).write_text(json.dumps(data,indent=2)+'\n')

def identify(uid):
    r=invoke(sdb+['shell',identity],8)
    rows=r['output'].splitlines()
    if (r['rc'] or len(rows)!=5 or rows[0]!=uid or rows[1]!='6.12.80-arm-rpi4-v7l armv7l'
        or rows[2]!=boot or rows[3].split()[0]!='146a4e2d870f3f65fdc6c6f9ca738e3cabcb83bbf4dc6f96bbcdd18c6776ab35'
        or rows[4]!='100000004694d889'):
        raise RuntimeError(('identity check',r))
    return r

def listener():
    r=invoke(['ss','-ltnp','sport = :26099'],5)
    assert r['rc']==0 and 'pid=276783,' in r['output'],r
    return r

def snapshot(cmd,timeout):
    start=time.monotonic()
    r=invoke(sdb+['shell',cmd],timeout)
    r.update(duration=round(time.monotonic()-start,5))
    return r

proc=r'''printf 'SAMPLE\n'; cat /proc/uptime; head -1 /proc/stat; cat /proc/loadavg; cat /proc/sys/kernel/random/boot_id; for p in /proc/[0-9]*/stat; do IFS= read -r row <"$p" && printf '%s\n' "$row"; done 2>/dev/null; echo ENDPROC'''
sensors=r'''printf 'SENSORS\n'; for f in /sys/class/thermal/thermal_zone*/temp /sys/class/hwmon/hwmon*/temp*_input /sys/class/hwmon/hwmon*/in*_alarm /sys/class/hwmon/hwmon*/in*_lcrit_alarm /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq /sys/devices/system/cpu/cpu[0-9]*/cpufreq/cpuinfo_cur_freq /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor /sys/class/drm/card*-*/status /sys/class/drm/card*-*/enabled /sys/class/drm/card*-*/dpms; do if [ -r "$f" ]; then IFS= read -r v <"$f" && printf '%s\t%s\n' "$f" "$v"; fi; done; echo ENDSENSORS'''
firmware=r'''printf 'FIRMWARE\n'; V=$(command -v vcgencmd); for f in /opt/vc/bin/vcgencmd /usr/local/bin/vcgencmd /opt/afdo_agent/tools/vcgencmd; do if [ -z "$V" ] && [ -x "$f" ]; then V=$f; fi; done; if [ -n "$V" ]; then "$V" get_throttled; "$V" measure_temp; for x in arm core v3d h264 isp hevc; do "$V" measure_clock "$x"; done; "$V" measure_volts; else echo 'vcgencmd=unknown'; fi; echo ENDFIRMWARE'''
deviced=out/'deviced-command.txt'

log('listener-before.json',listener())
log('identity-before.json',identify('5001'))
try:
    log('root-on.json',invoke(sdb+['root','on'],10))
    log('identity-root.json',identify('0'))
    start=time.monotonic()
    with (out/'raw.jsonl').open('x') as f:
        for index in range(181):
            scheduled=index*10
            time.sleep(max(0,start+scheduled-time.monotonic()))
            tick=now()
            observed=time.monotonic()-start
            p=snapshot(proc,3)
            s=snapshot(sensors,3)
            data=dict(index=index,scheduled_s=scheduled,actual_s=round(observed,5),utc=tick,proc=p,sensors=s)
            if index==0 or not cached_fw:
                val=snapshot(firmware,2)
                cached_fw=val['output']=='FIRMWARE\nvcgencmd=unknown\nENDFIRMWARE\n'
                data['firmware']=val
            else:
                data['firmware']=data_fw
            if index==0:
                data_fw=data['firmware']
            if deviced.is_file():
                data['deviced']=snapshot(deviced.read_text().strip(),2)
            else:
                data['deviced']=dict(rc=None,output='',stderr='Using state interface discovery')
            f.write(json.dumps(data,ensure_ascii=False)+'\n')
            f.flush()
            if index%30==0 or p['rc'] or s['rc']:
                print(tick,index,p['rc'],s['rc'],flush=True)
            if p['rc']==0 and p['output'].startswith('SAMPLE\n'):
                if p['output'].splitlines()[4]!=boot:
                    raise RuntimeError('boot changed during read-only run')
finally:
    log('root-off.json',invoke(sdb+['root','off'],10))
    log('identity-after.json',identify('5001'))
    log('listener-after.json',listener())
