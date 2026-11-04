#!/usr/bin/env python3
"""Percentile bootstrap 95% CI; fixed seed, caller-specified epsilon/estimand.

Difference = candidate - reference. Relative benefit (percent) is
100*(reference-candidate)/reference: positive means a lower candidate metric.
Independent resampling is default. Use --paired only for a predeclared paired
experiment; merely interleaving execution does not establish pairing.
"""
import argparse
import json
import math
from pathlib import Path
import random
import statistics


def percentile(values, q):
    values = sorted(values)
    at = (len(values) - 1) * q
    lo = int(at)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (at - lo)


def evaluate(reference, candidate, epsilon, *, metric='difference', statistic='median',
             paired=False, seed=20261104, resamples=20000):
    if min(len(reference), len(candidate)) < 5:
        raise ValueError('At least five independent observations per configuration required')
    if paired and len(reference) != len(candidate):
        raise ValueError('Paired samples must have equal length')
    if not math.isfinite(epsilon) or epsilon < 0:
        raise ValueError('epsilon must be finite and nonnegative')
    if any(not math.isfinite(x) for x in reference + candidate):
        raise ValueError('All observations must be finite')
    if resamples < 1000:
        raise ValueError('At least 1000 bootstrap resamples required')
    if statistic not in ('mean', 'median') or metric not in ('difference', 'relative-benefit-percent'):
        raise ValueError('Unknown statistic or equivalence metric')
    calc = statistics.mean if statistic == 'mean' else statistics.median
    rng = random.Random(seed)
    diffs, relative = [], []
    undefined_relative = 0
    r0, c0 = calc(reference), calc(candidate)
    for _ in range(resamples):
        ix = [rng.randrange(len(reference)) for _ in reference]
        iy = ix if paired else [rng.randrange(len(candidate)) for _ in candidate]
        r, c = calc([reference[i] for i in ix]), calc([candidate[i] for i in iy])
        diffs.append(c - r)
        if r <= 0:
            undefined_relative += 1
        else:
            relative.append(100 * (r - c) / r)
    interval = lambda xs: [percentile(xs, .025), percentile(xs, .975)]
    result = dict(schema_version=1, seed=seed, resamples=resamples, paired=paired,
                  statistic=statistic, sample_counts=[len(reference), len(candidate)],
                  reference=r0, candidate=c0,
                  difference=dict(estimate=c0-r0, ci95=interval(diffs)),
                  relative_benefit_percent=dict(estimate=100*(r0-c0)/r0 if r0 > 0 else None,
                                               ci95=interval(relative) if not undefined_relative and r0 > 0 else None,
                                               undefined_resamples=undefined_relative,
                                               reason='nonpositive_reference' if undefined_relative or r0 <= 0 else None),
                  equivalence_metric=metric, epsilon=epsilon)
    ci = result['difference' if metric == 'difference' else 'relative_benefit_percent']['ci95']
    result['verdict'] = 'equivalent' if ci is not None and -epsilon <= ci[0] and ci[1] <= epsilon else 'insufficient_evidence'
    result['note'] = 'No observations silently dropped; no claim about absolute execution counts or causal speedup.'
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path, help='JSON object with reference/candidate numeric arrays')
    p.add_argument('--epsilon', type=float, required=True)
    p.add_argument('--metric', choices=['difference', 'relative-benefit-percent'], default='difference')
    p.add_argument('--statistic', choices=['mean', 'median'], default='median')
    p.add_argument('--paired', action='store_true')
    p.add_argument('--seed', type=int, default=20261104)
    p.add_argument('--resamples', type=int, default=20000)
    a = p.parse_args()
    try:
        data = json.loads(a.input.read_text())
        result = evaluate(data['reference'], data['candidate'], a.epsilon, metric=a.metric,
                          statistic=a.statistic, paired=a.paired, seed=a.seed, resamples=a.resamples)
    except (ValueError, KeyError, TypeError) as e:
        p.error(str(e))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
