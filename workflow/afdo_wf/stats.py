"""Paired log-ratio inference; verdicts use transformed relative-time intervals."""
import math
import random
import statistics as st
from .common import require, positive

def order(n,seed,variants=('BASE','AFDO')):
    positive(n,'N',True);require(len(variants)>=2 and len(set(variants))==len(variants),'variant list')
    rows=[]
    for i in range(len(variants)):
        rows += [list(variants[i:]+variants[:i]) for _ in range(n//len(variants)+(i<n%len(variants)))]
    random.Random(seed).shuffle(rows);return rows

def budget(base):
    require(len(base)>=10,'ten pilot rounds required')
    for x in base:positive(x,'pilot time')
    cv=st.stdev(base)/st.mean(base)
    return min(40,max(10,math.ceil(2*(1.96*1.2533*cv/.005)**2)))

def percentile(a,p):
    q=(len(a)-1)*p;i=math.floor(q);j=math.ceil(q);return a[i]+(a[j]-a[i])*(q-i)

def verdict(ci,epsilon=.01):
    positive(epsilon,'epsilon');require(epsilon<1 and len(ci)==2,'CI/epsilon shape')
    require(all(type(x) in [int,float] and math.isfinite(x) for x in ci) and ci[0]<=ci[1],'invalid CI')
    lo,hi=ci
    return 'faster' if hi < -epsilon else 'slower' if lo>epsilon else 'equivalent' if -epsilon<lo and hi<epsilon else 'inconclusive'

def log_verdict(ci,epsilon=.01):return verdict([math.expm1(x) for x in ci],epsilon)

def beta_fraction(a,b,x):
    # Lentz continued fraction for regularized incomplete beta.
    qab=a+b;qap=a+1;qam=a-1;c=1.;d=1-qab*x/qap
    if abs(d)<1e-300:d=1e-300
    d=1/d;h=d
    for m in range(1,501):
        aa=m*(b-m)*x/((qam+2*m)*(a+2*m))
        d=1+aa*d;c=1+aa/c
        if abs(d)<1e-300:d=1e-300
        if abs(c)<1e-300:c=1e-300
        d=1/d;h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m))
        d=1+aa*d;c=1+aa/c
        if abs(d)<1e-300:d=1e-300
        if abs(c)<1e-300:c=1e-300
        d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<3e-14:return h
    require(False,'t quantile did not converge')

def ibeta(a,b,x):
    if x<=0:return 0.
    if x>=1:return 1.
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    if x<(a+1)/(a+b+2):return bt*beta_fraction(a,b,x)/a
    return 1-bt*beta_fraction(b,a,1-x)/b

def t975(df):
    require(df>=1,'df');lo=0.;hi=1000.
    for _ in range(80):
        mid=(lo+hi)/2;cdf=1-.5*ibeta(df/2,.5,df/(df+mid*mid))
        if cdf<.975:lo=mid
        else:hi=mid
    return (lo+hi)/2

def paired(pairs,seed,epsilon=.01,repetitions=20000):
    for a,b in pairs:positive(a,'control time');positive(b,'candidate time')
    if len(pairs)<2:return dict(n=len(pairs),verdict='inconclusive',reason='fewer than two complete blocks')
    require(type(repetitions) is int and repetitions>=2,'bootstrap count')
    r=[math.log(b/a) for a,b in pairs];n=len(r);mu=st.mean(r);rng=random.Random(seed)
    bs=sorted(st.mean(rng.choices(r,k=n)) for _ in range(repetitions))
    ci=[math.expm1(percentile(bs,p)) for p in [.025,.975]]
    half=t975(n-1)*st.stdev(r)/math.sqrt(n)
    return dict(n=n,estimate=math.expm1(mu),bootstrap_CI95=ci,t_CI95=[math.expm1(mu-half),math.expm1(mu+half)],
                median_ratio_minus_one=st.median(b for a,b in pairs)/st.median(a for a,b in pairs)-1,
                baseline_CV=st.stdev(a for a,b in pairs)/st.mean(a for a,b in pairs),verdict=verdict(ci,epsilon))

def analyze(blocks,n,seed,epsilon=.01,repetitions=20000):
    positive(n,"N",True)
    require(len({b['id'] for b in blocks})==len(blocks),'duplicate block')
    require(all(type(b['id']) is int and 1<=b['id']<=n for b in blocks),'block outside plan')
    complete=[b for b in blocks if b.get('complete')];missing=n-len(complete)
    for b in complete:require(b.get('correctness',True),'correctness failure','correctness',3)
    flagged=[b for b in complete if b.get('control_flag','clean')!='clean' or b.get('candidate_flag','clean')!='clean']
    pairs=lambda bs:[(b['control'],b['candidate']) for b in bs]
    out=dict(primary=paired(pairs(complete),seed,epsilon,repetitions),clean_sensitivity=paired(pairs([b for b in complete if b not in flagged]),seed,epsilon,repetitions),missing=missing,flagged=len(flagged),sampling='random.Random.choices; linear percentiles',seed=seed,repetitions=repetitions)
    caps=[]
    if missing:caps.append('incomplete')
    if (len(flagged)+missing)/n>.2:caps.append('more than 20% flagged/missing')
    # PM decision 2026-11-17: round-count difference, inclusive threshold.
    counts={v:sum(b.get(v+'_flag','clean')!='clean' for b in complete)
            for v in ['control','candidate']}
    threshold=max(2,math.ceil(.1*n))
    out['flag_imbalance']=dict(counts=counts,threshold=threshold,
        difference=abs(counts['control']-counts['candidate']),
        decision='PM decision 2026-11-17')
    if out['flag_imbalance']['difference']>=threshold:caps.append('flag imbalance')
    if caps:out['primary'].update(verdict='inconclusive',cap_reasons=caps)
    return out

def telemetry(samples,start,end,fixed_khz,capabilities,t_start=60,t_max=80):
    require(end>=start,'window order');left=start-1;right=end+1;anomalies=[];missing=[]
    ordered=[s for s in samples if type(s.get('time')) in [int,float] and math.isfinite(s['time'])]
    before=[s for s in ordered if s['time']<=left]
    after=[s for s in ordered if s['time']>=right]
    relevant=([before[-1]] if before else [])+[s for s in ordered if left<s['time']<right]+([after[0]] if after else [])
    if not relevant:missing.append('empty observation window')
    times=[s['time'] for s in relevant]
    if times!=sorted(set(times)):missing.append('nonmonotonic timestamps')
    if not times or times[0]>left or times[-1]<right:missing.append('missing window edge')
    if times and any(b-a>2 for a,b in zip(times,times[1:])):missing.append('gap >2s')
    for s in relevant:
        for k,paths in capabilities.items():
            values=s.get(k,{})
            if not isinstance(values,dict):missing.append('invalid '+k);continue
            for path in paths:
                value=values.get(path)
                if type(value) not in [int,float] or not math.isfinite(value):missing.append('missing '+path);continue
                if k=='frequency' and value!=fixed_khz:anomalies.append('frequency '+path)
                if k=='temperature' and (value>=t_max or (s['time']<=start and value>t_start)):anomalies.append('temperature '+path)
                if k=='voltage' and value!=0:anomalies.append('voltage '+path)
        if s.get('truncated'):missing.append('truncated record')
    return dict(classification='telemetry_anomaly' if anomalies else 'telemetry_missing' if missing else 'clean',anomalies=sorted(set(anomalies)),missing=sorted(set(missing)),throttle_history='unknown')

def effective_frequency(rows):
    vals={}
    for variant in ['control','candidate']:
        data=[]
        for row in rows:
            positive(row[variant]['cycles'],'cycles');positive(row[variant]['task_clock_ms'],'task clock')
            data.append(row[variant]['cycles']/row[variant]['task_clock_ms']/1000)
        vals[variant]=st.median(data)
    delta=vals['candidate']/vals['control']-1
    return dict(mhz=vals,relative_difference=delta,confounding_risk=abs(delta)>.005)

def select_attempts(attempts,n):
    """Append-only raw attempts: retry once, whole block, no measured replacement."""
    chosen=[]
    for ident in range(1,n+1):
        rows=sorted([r for r in attempts if r['id']==ident],key=lambda r:r['attempt'])
        require(len(rows)<=2 and [r['attempt'] for r in rows]==list(range(1,len(rows)+1)),'invalid retry history')
        if any(r.get('failure')=='correctness' for r in rows):require(False,'correctness failure','correctness',3)
        if len(rows)==2:
            require(rows[0].get('failure') in ['crash','timeout','sdb_drop'] and not rows[0].get('measurement_obtained') and not rows[0].get('complete'),'retry replaced a measured block')
        if rows and rows[-1].get('complete'):chosen.append(rows[-1])
    require(all(1<=r['id']<=n for r in attempts),'attempt outside plan')
    return chosen

def parse_telemetry_tsv(text):
    """Strict SAMPLE/END envelopes preserve query failures and truncation."""
    rows=[];current=None
    for line in text.splitlines():
        fields=line.split('\t')
        if len(fields)==2 and fields[0]=='SAMPLE':
            if current is not None:current['truncated']=True;rows.append(current)
            current=dict(time=float(fields[1]),frequency={},temperature={},voltage={})
        elif len(fields)==2 and fields[0]=='END':
            require(current is not None and current['time']==float(fields[1]),'telemetry end mismatch')
            rows.append(current);current=None
        elif len(fields)==4 and current is not None:
            stamp,kind,path,value=fields
            require(float(stamp)==current['time'] and kind in ['frequency','temperature','voltage'],'telemetry field mismatch')
            require(path not in current[kind],'duplicate telemetry source')
            try:parsed=float(value)
            except ValueError:parsed=None
            if parsed is not None and kind=='temperature':parsed/=1000
            current[kind][path]=parsed
        elif current is not None:current['truncated']=True
        else:require(False,'orphan telemetry data')
    if current is not None:current['truncated']=True;rows.append(current)
    return rows
