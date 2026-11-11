"""Refine only the saved smoke entry classification, without reopening profiles."""
import collections
import json
from registration_address_check import BASE, rows, dump
from run_scoped import sha, WORK
from pack_static_evidence import tables

OUT=BASE/'registration-checks/batch2'

def main():
    results=[]
    for tag in ['cal-thumb','cal-a32','cal-ffmpeg-thumb','cal-ffmpeg-a32']:
        dest=OUT/tag;summary=json.loads((dest/'classification.json').read_text());obj=summary['object']
        exclusion={(r['file'],int(r['line'])):json.loads(r['reasons']) for r in rows(BASE/'identity-gate/v18-gates'/(obj+'-static'),'C0-exclusions-*.csv')}
        counts=collections.Counter();details=[]
        for r in rows(dest,'entries-*.csv'):
            why=[r['reason']]
            if r['reason'] in ('excluded_line','outside_U'):
                vals=json.loads(r['map_values']);why=sorted({why for status,file,line,ref in vals for why in exclusion.get((file,line),['outside_C0'])})
                if len(vals)>1:why=sorted(set(why)|{'key_ambiguity'})
            label=r['category']+':'+','.join(why);counts[label]+=1
            details.append([r['profile_line'],json.loads(r['raw_key']),r['category'],why])
        assert sum(counts.values())==summary['entries']
        parts=tables(dest,'reason-detail',['profile_line','raw_key','category','reasons'],details)
        dump(dest/'reason-counts.json',dict(entry_counts=counts,parts=parts,entries=summary['entries'],unaligned=summary['unaligned_entries'],profile_reopened=False))
        results.append(dict(tag=tag,object=obj,entries=summary['entries'],entry_counts=counts,unaligned=summary['unaligned_entries'],conversion_exit_code=0,classification_exit_code=summary['classification_exit_code']))
    dump(OUT/'smoke-summary.json',dict(runs=results,controlled_quantities_computed=[],U_denominator_ratios_computed=[],old_profiles_opened=[],perf_data_opened=[]))
    print(json.dumps(results))

if __name__=='__main__':main()
