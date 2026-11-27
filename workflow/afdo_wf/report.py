"""Versioned machine report and human rendering of the same checked payload."""
from pathlib import Path
from .common import require, finite_tree, save, atomic_write

DISCLAIMER='profgen explicit conservative strategy; defaults not statistically validated'
REQUIRED={'experiment_id','build_lock','board_identity','telemetry_manifest','tools','artifacts','quality','code_shares','consumption','oracle','measurement_plan','rounds','statistics','limitations','cleanup_pending'}

def write(directory,data):
    require(REQUIRED<=data.keys(),'incomplete report: '+str(REQUIRED-data.keys()))
    finite_tree(data)
    data=dict(data);data['schema_version']=1
    data['limitations']=list(dict.fromkeys([*data['limitations'],DISCLAIMER]))
    primary=data['statistics'].get('primary',{})
    require(primary.get('verdict') in ['faster','slower','equivalent','inconclusive'],'invalid verdict')
    publishable=(bool(data['quality']) and data['build_lock'].get('passed') is True and data['consumption'].get('passed') is True and data['oracle'].get('passed') is True
                 and not data['cleanup_pending'] and all(q.get('publishable') is True for q in data['quality'].values()))
    if not publishable:
        data['statistics']={**data['statistics'],'primary':{**primary,'verdict':'inconclusive','publication_blocked':True}}
    if data.get('method') == 'pgo':
        if not publishable:
            for inputs in data['comparisons'].values():
                for row in inputs.values():
                    row['statistics']['primary'].update(verdict='inconclusive', publication_blocked=True)
    data['publishable']=publishable
    directory=Path(directory)
    save(directory/'report.json',data)
    lines=['# Experiment '+data['experiment_id'],'',DISCLAIMER,'',
           'Verdict: **'+data['statistics']['primary']['verdict']+'**','',
           '| Section | Recorded value |','|---|---|']
    import json
    for k in sorted(REQUIRED):
        section = len(data[k]) if k=='rounds' and data.get('method')=='pgo' and isinstance(data[k],list) else data[k]
        value=json.dumps(section,ensure_ascii=False,allow_nan=False).replace('|','\\|').replace('\n',' ')
        lines.append('| '+k+' | '+value+' |')
    if data.get('method') == 'pgo':
        lines.extend(['', '## Paired comparisons', '',
                      '| Comparison | Input | N | Pilot CV | Relative time | Bootstrap 95% CI | t 95% CI | Verdict |',
                      '| --- | --- | ---: | ---: | ---: | --- | --- | --- |'])
        for group, inputs in data['comparisons'].items():
            for name, row in inputs.items():
                stat = row['statistics']['primary']
                pilot = row['plan'].get('pilot_cv')
                cv = f'{pilot:.3%}' if pilot is not None else '—'
                def interval(key):
                    bounds = stat.get(key)
                    return f'[{bounds[0]:+.3%}, {bounds[1]:+.3%}]' if bounds else '—'
                lines.append(f"| {group} | {name} | {row['plan']['N']} | {cv} | {stat['estimate']:+.3%} | "
                             f"{interval('bootstrap_CI95')} | {interval('t_CI95')} | {stat['verdict']} |")
        lines.extend(['', '## Measurement diagnostics', '',
                      '| Comparison | Input | Flagged blocks | Flag imbalance (difference / threshold) | Retries | Effective MHz (control / PGO) | Frequency confounding | Temperature °C (control / PGO range) |',
                      '| --- | --- | ---: | ---: | ---: | --- | --- | --- |'])
        for group, inputs in data['comparisons'].items():
            for name, row in inputs.items():
                result, freq = row['statistics'], row.get('effective_frequency', {})
                imbalance = result.get('flag_imbalance',{})
                mhz = freq.get('mhz')
                mhz_text = f"{mhz['control']:.2f} / {mhz['candidate']:.2f}" if mhz else '—'
                temperatures = row.get('temperature_c', {})
                spans = [f"{v['min']:.1f}–{v['max']:.1f}" if v else '—' for v in temperatures.values()]
                lines.append(f"| {group} | {name} | {result.get('flagged','—')} | {imbalance.get('difference','—')} / {imbalance.get('threshold','—')} | "
                             f"{row.get('technical_retries','—')} | {mhz_text} | {freq.get('confounding_risk','—')} | {' / '.join(spans)} |")
        lines.extend(['', '## Mechanism counts', '', 'Diagnostic counts are collected separately from paired timing.', '',
                      '| Comparison | Event | Pairs | Control median | PGO median | Median paired relative difference |',
                      '| --- | --- | ---: | ---: | ---: | ---: |'])
        for group, metrics in data['mechanism_counts'].get('paired', {}).items():
            for event, item in metrics.items():
                delta = item['median_paired_relative']
                relative = f'{delta:+.3%}' if delta is not None else '—'
                lines.append(f"| {group} | {event} | {item['complete_pairs']} | {item['control_median']} | {item['pgo_median']} | {relative} |")
        lines.extend(['', '## Registered deviations', '', '```json',
                      json.dumps(data.get('deviations', {}), indent=2, sort_keys=True), '```'])
    atomic_write(directory/'report.md','\n'.join(lines)+'\n');return data
