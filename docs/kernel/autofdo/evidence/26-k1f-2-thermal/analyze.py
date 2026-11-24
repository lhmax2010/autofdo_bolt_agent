import argparse
import collections
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import statistics as st
from zoneinfo import ZoneInfo

parser=argparse.ArgumentParser()
parser.add_argument('root',type=Path)
parser.add_argument('--partial',action='store_true')
args=parser.parse_args()
root=args.root
pst=ZoneInfo('America/Los_Angeles')
raw_path=root/'raw.jsonl'
got=[json.loads(line) for line in raw_path.read_bytes().splitlines(keepends=True) if line.endswith(b'\n')]
assert len(got)<=181
if not args.partial:
    assert len(got)==181
assert [r['index'] for r in got]==list(range(len(got)))
as_pst=lambda s:datetime.fromisoformat(s).astimezone(pst).isoformat(timespec='milliseconds')

def vals(seq):
    data=sorted(seq)
    if not data:
        return None
    i=(len(data)-1)*.9
    lo=int(i)
    p90=data[lo]+(data[math.ceil(i)]-data[lo])*(i-lo)
    return dict(n=len(data),minimum=min(data),median=st.median(data),p90=p90,maximum=max(data),mean=st.mean(data))

def series_value(key, rows):
    return vals([x[key] for x in rows if x.get(key) is not None])

def parse_clock(body):
    rates={}
    counts={}
    for line in body.splitlines():
        match=re.fullmatch(r'(fw-clk-(?:arm|core|v3d|isp|hevc)|h264)\t(\d+)\t(\d+)',line)
        if match:
            name=match[1].removeprefix('fw-clk-')
            rates[name]=int(match[2])
            counts[name]=int(match[3])
    return rates,counts

def parse_section(data,start,end):
    if data['rc'] or not data['output'].startswith(start+'\n') or not data['output'].endswith(end+'\n'):
        return None
    return data['output'].splitlines()[1:-1]

group_re={
    'enlightenment/compositor':re.compile(r'enlighten|wayland|comp(o|s)|weston|kwin|mutter',re.I),
    'graphics workers':re.compile(r'v3d|vc4|drm|vchiq|hvs|hdmi|kworker.*flip',re.I),
    'media workers/userspace':re.compile(r'media|gstream|(^|/)gst[-_:]|ffmpeg|pipewire|pulse|audio|video|decod|pvr|avplay|tvplayer|mm-player|omx|v4l2|hevc|h264|isp',re.I),
    'deviced':re.compile(r'^deviced$',re.I),
    'TV application/services':re.compile(r'^runner$|SystemUI|dotnet-hydra|tv-viewer|wrt|webapp|appcore|tizen-home',re.I)
}

def px(row):
    # Linux /proc/pid/stat wraps comm in parentheses and comm can contain spaces.
    left=row.index(' (')
    right=row.rindex(') ')
    tail=row[right+2:].split()
    return dict(pid=int(row[:left]),comm=row[left+2:right],utime=int(tail[11]),stime=int(tail[12]),starttime=int(tail[19]))

samples=[]
issues=[]
for tick in got:
    n=tick['index']
    p=parse_section(tick['proc'],'SAMPLE','ENDPROC')
    s=parse_section(tick['sensors'],'SENSORS','ENDSENSORS')
    d=parse_section(tick['deviced'],'DISPLAY','END')
    result={key:tick[key] for key in ('index','scheduled_s','actual_s','utc')}
    result['command_status']={k:{name:tick[k].get(name) for name in ('rc','stderr','duration')} for k in ('proc','sensors','firmware','deviced')}
    result['firmware']=tick['firmware']['output'].strip()
    if p is not None:
        result['board_uptime_s']=float(p[0].split()[0])
        result['aggregate_proc_stat']=[int(x) for x in p[1].split()[1:]]
        result['loadavg']=p[2]
        result['boot_id']=p[3]
        assert result['boot_id']=='656d98ce-abdc-47e2-9f04-deffc0979c68'
        result['proc_counters']=[px(row) for row in p[4:]]
    if s is not None:
        result['sysfs']={}
        for sensor in s:
            name,value=sensor.split('\t',1)
            if name in result['sysfs']:
                assert result['sysfs'][name]==value
            result['sysfs'][name]=value
        result['thermal_zone_mC']=int(result['sysfs']['/sys/class/thermal/thermal_zone0/temp'])
        result['hwmon_cpu_mC']=int(result['sysfs']['/sys/class/hwmon/hwmon1/temp1_input'])
    if d is not None:
        result['display_clock_raw']='\n'.join(d)
        rates,counts=parse_clock(result['display_clock_raw'])
        result['clock_rates_Hz']=rates
        result['clock_enable_counts']=counts
        vconf=re.search(r'memory/pm/state, value = (-?\d+) \(Int32\)',result['display_clock_raw'])
        if vconf:
            result['deviced_pm_state']=int(vconf[1])
        service=result['display_clock_raw'].split('\nCLOCKS\n')[0]
        groups=service.strip().split('\n\n')
        record={}
        for group in groups:
            properties=dict(line.split('=',1) for line in group.splitlines() if '=' in line)
            if 'Id' in properties:
                record[properties['Id']]=properties
        values=[int(v) for v in re.findall(r'^i (-?\d+)$',service,re.M)]
        result['deviced_display_count']=values[0] if len(values)==2 else None
        result['deviced_display_brightness']=values[-1] if len(values)==2 else None
        result['display_services']=record
    if p is None or s is None or d is None:
        issues.append(dict(sample=n,proc=p is None,sensors=s is None,display_clocks=d is None))
    samples.append(result)

def pct(cpu_prev,cpu):
    dt=[b-a for a,b in zip(cpu_prev[:8],cpu[:8])]
    assert min(dt)>=0 and sum(dt)>0,dt
    return 100*(sum(dt)-dt[3]-dt[4])/sum(dt)

intervals=[]
for prev,cur in zip(samples,samples[1:]):
    if 'aggregate_proc_stat' not in prev or 'aggregate_proc_stat' not in cur:
        continue
    elapsed=cur['board_uptime_s']-prev['board_uptime_s']
    assert 8<=elapsed<=12,elapsed
    old={(p['pid'],p['starttime']):p for p in prev['proc_counters']}
    groups={key:[] for key in group_re}
    rows=[]
    for proc in cur['proc_counters']:
        key=(proc['pid'],proc['starttime'])
        if key not in old:
            continue
        ticks=(proc['utime']+proc['stime'])-(old[key]['utime']+old[key]['stime'])
        assert ticks>=0
        # CLK_TCK=100. Percent is relative to one CPU, not the board.
        entry=dict(pid=proc['pid'],comm=proc['comm'],starttime=proc['starttime'],ticks=ticks,cpu_pct=ticks/elapsed)
        rows.append(entry)
        for name,pat in group_re.items():
            if pat.search(proc['comm']):
                groups[name].append(entry)
    rows.sort(key=lambda p:(-p['ticks'],p['pid']))
    intervals.append(dict(index=cur['index'],seconds=elapsed,
        board_busy_pct=pct(prev['aggregate_proc_stat'],cur['aggregate_proc_stat']),
        top5=rows[:5],groups=groups))
    cur['interval']=intervals[-1]

all_top=collections.defaultdict(lambda:dict(top5_count=0,cpu_pct_sum=0,max_cpu_pct=0,ticks=0))
for v in intervals:
    for row in v['top5']:
        stat=all_top[row['comm']]
        stat['top5_count']+=1
        stat['cpu_pct_sum']+=row['cpu_pct']
        stat['max_cpu_pct']=max(stat['max_cpu_pct'],row['cpu_pct'])
        stat['ticks']+=row['ticks']
groups={}
for name in group_re:
    names=sorted({p['comm'] for i in intervals for p in i['groups'][name]})
    groups[name]=dict(names=names,usage_pct=vals([sum(p['cpu_pct'] for p in i['groups'][name]) for i in intervals]))
temperature=[x['thermal_zone_mC']/1000 for x in samples if 'thermal_zone_mC' in x]
temp_hw=[x['hwmon_cpu_mC']/1000 for x in samples if 'hwmon_cpu_mC' in x]
sysfs=collections.defaultdict(collections.Counter)
clocks=collections.defaultdict(collections.Counter)
enables=collections.defaultdict(collections.Counter)
for s in samples:
    for k,v in s.get('sysfs',{}).items():
        if 'temp' not in k:
            sysfs[k][v]+=1
    for k,v in s.get('clock_rates_Hz',{}).items():
        clocks[k][v]+=1
    for k,v in s.get('clock_enable_counts',{}).items():
        enables[k][v]+=1

seen=[float(x['loadavg'].split()[0]) for x in samples if 'loadavg' in x]
bins=[]
for lo,hi in ((0,600),(600,1200),(1200,1801)):
    rng=[s for s in samples if lo<=s['scheduled_s']<hi]
    if rng:
        bins.append(dict(start=lo,end=hi,temperature=vals(s['thermal_zone_mC']/1000 for s in rng if 'thermal_zone_mC' in s),
                         busy=vals(s['interval']['board_busy_pct'] for s in rng if 'interval' in s)))
stats=dict(sample_count=len(samples),sample_errors=issues,start=as_pst(samples[0]['utc']),end=as_pst(samples[-1]['utc']),
    board_uptime_start_s=samples[0].get('board_uptime_s'),board_uptime_end_s=samples[-1].get('board_uptime_s'),
    temperature_first=temperature[0],temperature_last=temperature[-1],cpu_temperature_C=vals(temperature),
    hwmon_temperature_C=vals(temp_hw),temperature_tenths=bins,board_busy_pct=series_value('board_busy_pct',intervals),
    board_busy_below_gate=sum(i['board_busy_pct']<2.91 for i in intervals),
    board_busy_exactly_equal_gate=sum(i['board_busy_pct']==2.91 for i in intervals),loadavg1=vals(seen),period_s=series_value('seconds',intervals),
    host_lag_s=vals(g['actual_s']-g['scheduled_s'] for g in got),sysfs={k:dict(v) for k,v in sysfs.items()},
    clocks_Hz={k:dict(v) for k,v in clocks.items()},clock_enable_counts={k:dict(v) for k,v in enables.items()},
    pm_state=dict(collections.Counter(str(s.get('deviced_pm_state','missing')) for s in samples)),
    pm_first_sample=next((s['index'] for s in samples if 'deviced_pm_state' in s),None),
    display_count=dict(collections.Counter(str(s.get('deviced_display_count','missing')) for s in samples)),
    display_brightness=dict(collections.Counter(str(s.get('deviced_display_brightness','missing')) for s in samples)),
    display_service_states=dict(collections.Counter(json.dumps(s.get('display_services',{}),sort_keys=True) for s in samples)),
    top5=dict(sorted(all_top.items(),key=lambda x:-x[1]['ticks'])),gpu_cpu_groups=groups,
    process_records=vals(len(s['proc_counters']) for s in samples if 'proc_counters' in s),
    firmware_reported=sorted({s['firmware'] for s in samples}))
if not args.partial:
    assert abs(stats['board_uptime_end_s']-stats['board_uptime_start_s']-1800)<2
    assert not issues,issues
    assert len(intervals)==180
    with (root/'measurements.jsonl.gz').open('wb') as raw, gzip.GzipFile(fileobj=raw,filename='',mode='wb',mtime=0) as f:
        for s in samples:
            f.write((json.dumps(s,ensure_ascii=False,separators=(',',':'))+'\n').encode())
    (root/'summary.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(stats,indent=2,ensure_ascii=False))
