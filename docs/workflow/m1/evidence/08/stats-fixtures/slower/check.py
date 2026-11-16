import pathlib,json,math,random,statistics as S
D=pathlib.Path(__file__).parent
plan=json.loads((D/'plan.json').read_text());rows=json.loads((D/'rounds.json').read_text());blocks=json.loads((D/'blocks.json').read_text())
T=[None,12.706204736,4.302652730,3.182446305,2.776445105,2.570581836,2.446911851,2.364624252,2.306004135,2.262157163,2.228138852,2.200985160,2.178812830,2.160368656,2.144786688,2.131449546]
def percentile(a,p):
 x=(len(a)-1)*p;i=math.floor(x);j=math.ceil(x);return a[i]+(a[j]-a[i])*(x-i)
def analyze(pairs):
 if len(pairs)<2:return {'n':len(pairs),'verdict':'inconclusive','reason':'fewer than two complete pairs'}
 rs=[math.log(b['wall_seconds']/a['wall_seconds']) for a,b in pairs];rng=random.Random(plan['bootstrap_seed']);n=len(rs);bs=sorted(S.mean(rng.choices(rs,k=n)) for _ in range(20000));ci=[math.expm1(percentile(bs,p)) for p in [.025,.975]]
 mu=S.mean(rs);half=T[n-1]*S.stdev(rs)/math.sqrt(n);tc=[math.expm1(mu-half),math.expm1(mu+half)];eps=plan['epsilon']
 verdict='faster' if ci[1]<-eps else 'slower' if ci[0]>eps else 'equivalent' if ci[0]>-eps and ci[1]<eps else 'inconclusive'
 return dict(n=n,log_ratios=rs,estimate=math.expm1(mu),bootstrap_CI95=ci,t_CI95=tc,median_ratio_minus_one=S.median(b['wall_seconds'] for a,b in pairs)/S.median(a['wall_seconds'] for a,b in pairs)-1,verdict=verdict)
pairs=[];clean=[];flagged=[];missing=[]
for b in blocks:
 if not b['complete']:missing.append(b['block']);continue
 r=[r for r in rows if not r['warmup'] and r['block']==b['block'] and r['attempt']==b['selected_attempt']];assert len(r)==2
 a=next(x for x in r if x['variant']=='base');c=next(x for x in r if x['variant']=='afdo');pairs.append((a,c))
 if a['flags'] or c['flags']:flagged.append(b['block'])
 else:clean.append((a,c))
out=dict(primary=analyze(pairs),clean_sensitivity=analyze(clean),flagged_blocks=flagged,missing_blocks=missing,bootstrap_seed=plan['bootstrap_seed'],epsilon=plan['epsilon'])
if missing or len(flagged)+len(missing)>3:out['primary']['verdict']='inconclusive';out['primary']['cap_reason']='incomplete or >20% flagged/missing'
freq={}
for v in ['base','afdo']:
 vals=[]
 for pair in pairs:
  x=next(z for z in pair if z['variant']==v);tc=x['perf']['task-clock'];assert tc['unit'].strip()=='msec';vals.append(x['perf']['cycles']['value']/tc['value']/1000)
 freq[v]=S.median(vals) if vals else None
out['effective_frequency_MHz']=freq
if all(freq.values()):out['effective_frequency_relative_difference']=freq['afdo']/freq['base']-1;out['confounding_risk']=abs(out['effective_frequency_relative_difference'])>.005
base=[a['wall_seconds'] for a,b in pairs];out['baseline_CV']=S.stdev(base)/S.mean(base) if len(base)>=2 else None
(D/'statistics.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
