"""v1.8 5.8.5/6 statistics, shared by future simulation and gated analysis.

Pure data API: no profile reader and no simulation driver. Callers of real-data
analysis must first obtain a permit from registration_protocol. Unit fixtures
are explicitly synthetic. Standard-library numerical routines only.
"""
import collections
import math
import random
import statistics
from fractions import Fraction

EPSILON = 0.02
RESOLUTION = 1e-9
SEED = 20261104
BOOTSTRAPS = 20000


def finite(values):
    if any(isinstance(v, bool) or not math.isfinite(float(v)) for v in values):
        raise ValueError('nonfinite_or_boolean_numeric_input')


def ranks(values):
    finite(values)
    order=sorted(range(len(values)),key=values.__getitem__)
    out=[0.0]*len(values);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        for k in range(i,j):out[order[k]]=(i+1+j)/2
        i=j
    return out


def rho(reference, sample):
    a,b=ranks(reference),ranks(sample)
    am,bm=statistics.mean(a),statistics.mean(b)
    aa=math.fsum((x-am)**2 for x in a);bb=math.fsum((x-bm)**2 for x in b)
    if aa==0:return None
    if bb==0:return 0.0
    return math.fsum((x-am)*(y-bm) for x,y in zip(a,b))/math.sqrt(aa*bb)


def hot_reference(reference):
    """Integer 5*c >= 4*T, including the full cutoff tie. Empty/zero -> null K."""
    if any(type(v) is not int or v<0 for v in reference.values()):
        raise ValueError('reference_counts_must_be_nonnegative_integers')
    total=sum(reference.values())
    if not reference or total==0:return set(),None
    cumulative=0
    for v in sorted(reference.values(),reverse=True):
        cumulative+=v
        if 5*cumulative>=4*total:
            return {k for k,x in reference.items() if x>=v},v
    raise AssertionError('unreachable')


def line_metrics(reference, sample, functions, min_lines=5):
    """U is exactly reference.keys(); missing observations become zero in memory.

No file IO. Synthetic callers can compute freely; formal callers must hold the
protocol permit. No selection or weighting depends on the sample dictionary.
"""
    finite(sample.values())
    if any(v<0 for v in sample.values()):raise ValueError('negative_sample')
    hot,cutoff=hot_reference(reference)
    if cutoff is None:
        return dict(M1=None,M2=None,M2b=None,n_eff=None,K=None,T=sum(reference.values()),
                    equal_function_median=None,functions=[],excluded_constant=[])
    K=len(hot); buckets=collections.defaultdict(list)
    for key in reference:buckets[functions[key]].append(key)
    chosen=[];constant=[]
    for f,keys in sorted(buckets.items()):
        if len(keys)<min_lines:continue
        ref=[reference[k] for k in keys];obs=[sample.get(k,0) for k in keys]
        score=rho(ref,obs)
        if score is None:
            constant.append(dict(function=f,lines=len(keys),reference_weight=sum(ref)));continue
        chosen.append(dict(function=f,score=score,weight=sum(ref),lines=len(keys)))
    weight=sum(x['weight'] for x in chosen);squares=sum(x['weight']**2 for x in chosen)
    m1=math.fsum(x['weight']*x['score'] for x in chosen)/weight if weight else None
    positives=collections.defaultdict(list)
    for k in reference:
        if sample.get(k,0)>0:positives[sample[k]].append(k)
    remaining=K; overlap=Fraction(0)
    for value in sorted(positives,reverse=True):
        group=positives[value];take=min(remaining,len(group))
        overlap+=Fraction(take,len(group))*sum(k in hot for k in group)
        remaining-=take
        if remaining==0:break
    return dict(M1=m1,M2=float(overlap/K),M2b=sum(sample.get(k,0)>0 for k in hot)/K,
                n_eff=weight**2/squares if squares else None,K=K,T=sum(reference.values()),
                equal_function_median=statistics.median(x['score'] for x in chosen) if chosen else None,
                functions=chosen,excluded_constant=constant)


def merge_lines(entries):
    """S=max_d sum_context; S_alt=sum_context max_d; S_sum=sum both.

Each input carries its independently classified source owner, region boundaries
and reference-execution status. Rejected entries are not allowed to borrow an
executed instance's physical line. Counts are aggregated by context/discriminator.
"""
    values=collections.defaultdict(lambda:collections.defaultdict(lambda:collections.defaultdict(int)))
    rejected=[];regions=[]
    for e in entries:
        finite([e['count']])
        if e['count']<0:raise ValueError('negative_body_count')
        regions.extend(e.get('regions',[]))
        if not e['reference_executed']:
            rejected.append(dict(entry=e,reason='unexecuted_reference_source'));continue
        if e['source_owner']!=e['line_owner']:
            rejected.append(dict(entry=e,reason='source_function_mismatch'));continue
        line=tuple(e['line']);ctx=tuple(e['context']);disc=e['discriminator']
        values[line][ctx][disc]+=e['count']
    result={}
    for line,contexts in values.items():
        ds=collections.defaultdict(int)
        for counts in contexts.values():
            for d,n in counts.items():ds[d]+=n
        result[line]=dict(S=max(ds.values()),S_alt=sum(max(c.values()) for c in contexts.values()),S_sum=sum(ds.values()))
    return dict(lines=result,rejected=rejected,coverage_regions=regions)


def phase_diagnostics(phases):
    out={}
    for h,values in phases.items():
        finite(values)
        if len(values)<2:raise ValueError('phase_has_fewer_than_two_runs')
        values=list(map(float,values));lo,hi=min(values),max(values)
        out[h]=dict(min=lo,max=hi,range=hi-lo,degenerate=hi-lo<=RESOLUTION,
                    reason='numerically_flat' if hi-lo<=RESOLUTION else None)
    return out


# Regularized incomplete beta by the convergent modified Lentz continued
# fraction. No scipy dependency. Quantiles are checked against exact df=1/2
# and standard published df=14 values in the synthetic fixture suite.
def _betacf(a,b,x):
    tiny=1e-300;qab=a+b;qap=a+1;qam=a-1
    c=1.0;d=1-qab*x/qap
    if abs(d)<tiny:d=tiny
    d=1/d;h=d
    for m in range(1,10001):
        m2=2*m
        aa=m*(b-m)*x/((qam+m2)*(a+m2))
        d=1+aa*d;c=1+aa/c
        if abs(d)<tiny:d=tiny
        if abs(c)<tiny:c=tiny
        d=1/d;h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2))
        d=1+aa*d;c=1+aa/c
        if abs(d)<tiny:d=tiny
        if abs(c)<tiny:c=tiny
        d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<=3e-14:return h
    raise ArithmeticError('incomplete_beta_did_not_converge')


def _beta(a,b,x):
    if x<=0:return 0.0
    if x>=1:return 1.0
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    if x<(a+1)/(a+b+2):return bt*_betacf(a,b,x)/a
    return 1-bt*_betacf(b,a,1-x)/b


def t_cdf(t,df):
    finite([t,df])
    if df<=0:raise ValueError('invalid_t_df')
    tail=.5*_beta(df/2,.5,df/(df+t*t))
    return 1-tail if t>=0 else tail


def t_quantile(df,p=.975):
    if not 0.5<p<1:raise ValueError('unsupported_quantile')
    lo=0.;hi=1.
    while t_cdf(hi,df)<p:
        hi*=2
        if hi>1e12:raise ArithmeticError('t_quantile_unbounded')
    for _ in range(90):
        mid=(lo+hi)/2
        if t_cdf(mid,df)<p:lo=mid
        else:hi=mid
    return (lo+hi)/2


def stratified_t(phases):
    diagnostic=phase_diagnostics(phases)
    n=sum(map(len,phases.values()));a=[];means=[]
    for values in phases.values():
        lam=len(values)/n
        means.append(lam*statistics.mean(values))
        a.append((lam**2*statistics.variance(values)/len(values),len(values)))
    mean=math.fsum(means);se2=math.fsum(x for x,_ in a)
    flat=any(d['degenerate'] for d in diagnostic.values())
    if se2==0:return dict(mean=mean,interval=None,df=None,SE=0.0,degenerate=True,phases=diagnostic)
    df=se2**2/math.fsum(x*x/(n-1) for x,n in a)
    width=t_quantile(df)*math.sqrt(se2)
    return dict(mean=mean,interval=[mean-width,mean+width],df=df,SE=math.sqrt(se2),degenerate=flat,phases=diagnostic)


def percentile(values,p):
    """Linear empirical percentile (rank (B-1)*p); fixed, not data-selected."""
    s=sorted(values);r=(len(s)-1)*p;i=int(r);f=r-i
    return s[i] if i+1==len(s) else s[i]*(1-f)+s[i+1]*f


def paired_differences(left,right,slots):
    """One logical RUN record can list multiple acquisition segments."""
    if len({s['run_id'] for s in slots})!=len(slots):raise ValueError('duplicate_run_slot')
    phases=collections.defaultdict(list);missing=[]
    for s in slots:
        rid=s['run_id'];a=left.get(rid);b=right.get(rid)
        if not a or not b or a['conversion']!='ok' or b['conversion']!='ok' or a['value'] is None or b['value'] is None:
            missing.append(rid);continue
        finite([a['value'],b['value']]);phases[s['phase']].append(float(a['value'])-float(b['value']))
    allowed={s['run_id'] for s in slots}
    if left.keys()-allowed or right.keys()-allowed:raise ValueError('unregistered_run')
    return dict(phases=dict(phases),missing=missing)


def intervals_joint(metrics,seed=SEED,repeats=BOOTSTRAPS):
    """Shared per-phase resampling indices for M1/M2 and paired differences."""
    if repeats!=BOOTSTRAPS or seed!=SEED:raise ValueError('registered_bootstrap_parameters_required')
    phase_names=sorted(next(iter(metrics.values())))
    sizes={h:len(next(iter(metrics.values()))[h]) for h in phase_names}
    for phases in metrics.values():
        if set(phases)!=set(sizes) or any(len(phases[h])!=sizes[h] for h in sizes):raise ValueError('unpaired_metric_runs')
        phase_diagnostics(phases)
    n=sum(sizes.values());rng=random.Random(seed);draws={k:[] for k in metrics}
    for _ in range(repeats):
        idx={h:[rng.randrange(sizes[h]) for _ in range(sizes[h])] for h in phase_names}
        for k,phases in metrics.items():
            draws[k].append(math.fsum(phases[h][i]/n for h in phase_names for i in idx[h]))
    result={}
    for k,phases in metrics.items():
        t=stratified_t(phases);boot=[percentile(draws[k],.025),percentile(draws[k],.975)]
        envelope=None if t['interval'] is None else [min(boot[0],t['interval'][0]),max(boot[1],t['interval'][1])]
        result[k]=dict(t=t,bootstrap=boot,envelope=envelope,seed=seed,repeats=repeats)
    return result


def outliers(phases):
    marked=[]
    for phase,values in phases.items():
        finite(values);med=statistics.median(values);mad=statistics.median(abs(x-med) for x in values)
        marked.extend(dict(phase=phase,index=i,value=x) for i,x in enumerate(values) if abs(x-med)>max(EPSILON,5*mad))
    return marked


def interpretation(table,results,*,terminal_slots,complete_pairs,model,quality_enabled,sensitivity=False):
    """Decision gate only. A separate v18 writer validates domain/table SHA first."""
    if type(quality_enabled) is not bool:raise ValueError('quality_switch_must_be_boolean')
    if not model or not model.get('id') or not model.get('unverified_assumptions') or 'scenario_failures' not in model:
        raise ValueError('model_label_required')
    result=dict(result='insufficient_evidence',model=model,nominal_confidence=.95,
                sensitivity=sensitivity,equivalent=False)
    if not table['U_lines'] or not table['T'] or table['K'] is None:return result
    finite([table['K'],table['T']])
    if table['K']<50:return dict(result, result='descriptive_only')
    if table['n_eff'] is not None:finite([table['n_eff']])
    wanted=['M2'] if table['n_eff'] is None or table['n_eff']<3 else ['M1','M2']
    if terminal_slots!=15 or not complete_pairs or not quality_enabled:return result
    for metric in wanted:
        r=results.get(metric)
        if not r or r['t']['degenerate'] or r['envelope'] is None:return result
        finite(r['envelope'])
        if r['envelope'][0]>r['envelope'][1]:raise ValueError('inverted_interval')
        if not (-EPSILON<=r['envelope'][0] and r['envelope'][1]<=EPSILON):return result
    return dict(result,result='登记工作模型条件下的'+('M2等价，M1未判读' if wanted==['M2'] else 'M1、M2联合等价'),equivalent=True)


def comparisons(frequency_mode):
    return ['sum','avg','prev-inst']+(['sample_weight'] if frequency_mode else [])


def assess_paired_metrics(left,right,slots,table,*,terminal_slots,model,quality_enabled):
    """Common final-analysis and synthetic-fixture adapter; never a #9 driver.

Preserves planned phase counts on missing/undefined inputs. No silently reduced
sample-size or reweighted interval is produced. Caller uses compute_guarded for
real inputs and v18_rules.write_conclusion for an output document.
"""
    if len(slots)!=15:raise ValueError('registered_15_slot_plan_required')
    planned=collections.Counter(s['phase'] for s in slots)
    if any(n<2 for n in planned.values()):raise ValueError('invalid_phase_plan')
    paired={m:paired_differences(left[m],right[m],slots) for m in ['M1','M2']}
    required=['M2'] if table['n_eff'] is None or table['n_eff']<3 else ['M1','M2']
    complete=all(not paired[m]['missing'] for m in required)
    eligible={m:p['phases'] for m,p in paired.items() if not p['missing']}
    estimates=intervals_joint(eligible) if eligible else {}
    decision=interpretation(table,estimates,terminal_slots=terminal_slots,complete_pairs=complete,
                            model=model,quality_enabled=quality_enabled)
    return dict(planned_phase_counts=dict(planned),paired=paired,intervals=estimates,decision=decision,
                outliers={m:outliers(p['phases']) for m,p in paired.items() if p['phases']},
                runs_above_epsilon={m:sum(abs(x)>EPSILON for vs in p['phases'].values() for x in vs) for m,p in paired.items()},
                max_absolute_difference={m:max((abs(x) for vs in p['phases'].values() for x in vs),default=None) for m,p in paired.items()})
