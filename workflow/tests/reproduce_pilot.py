"""Explicit historical regression, separate from synthetic unittest discovery.
Reads only the authorized saved measurement JSON; never opens a profile/perf file.
"""
from pathlib import Path
import argparse
import json
import math
from afdo_wf import stats
from afdo_wf.common import save,sha256

p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--output',required=True);a=p.parse_args()
d=Path(a.evidence);plan=json.loads((d/'plan.json').read_text());rounds=json.loads((d/'rounds.json').read_text());blocks=json.loads((d/'blocks.json').read_text())
pairs=[];clean=[];rows=[]
for b in blocks:
    assert b['complete']
    selected=[r for r in rounds if not r['warmup'] and r['block']==b['block'] and r['attempt']==b['selected_attempt']]
    base=next(r for r in selected if r['variant']=='base');afdo=next(r for r in selected if r['variant']=='afdo')
    pair=(base['wall_seconds'],afdo['wall_seconds']);pairs.append(pair)
    if not base['flags'] and not afdo['flags']:clean.append(pair)
    rows.append(dict(block=b['block'],control=pair[0],candidate=pair[1]))
x=stats.paired(pairs,plan['bootstrap_seed'],plan['epsilon'],plan['bootstrap_repetitions']);y=stats.paired(clean,plan['bootstrap_seed'],plan['epsilon'],plan['bootstrap_repetitions'])
assert round(100*x['estimate'],3)==-2.565
assert [round(100*v,3) for v in x['bootstrap_CI95']]==[-2.859,-2.256]
assert x['verdict']=='faster'
assert [round(100*v,3) for v in y['bootstrap_CI95']]==[-2.868,-2.194]
order=['AB' if o[0]=='BASE' else 'BA' for o in stats.order(15,plan['order_seed'])];assert order==plan['order']
save(a.output,dict(passed=True,purpose='historical numeric regression, not a new qualification decision',inputs={str(d/n):sha256(d/n) for n in ['plan.json','rounds.json','blocks.json']},primary=x,clean_sensitivity=y,order=order,blocks=rows))
print(json.dumps(dict(primary=x,clean=y),indent=2))
