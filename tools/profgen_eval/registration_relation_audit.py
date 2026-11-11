"""Persist independent address relations, verify multiplicity, classify synthetic entries."""
import collections
import json
import posixpath
import sqlite3
import sys
from registration_address_check import (OUT, TEMP, BASE, rows, dump, independent_key,
                                         profile_entries, key_string, mapped_key)
from registration_mapping_checks import classify_entry, compare_relations
from run_scoped import WORK, sha
from pack_static_evidence import tables


def source_path(path):
    # Independently implement the registered four explicit debug-prefix mappings.
    path = posixpath.normpath(path)
    for isa in ['thumb', 'a32']:
        for stage in ['S', 'C']:
            prefix = '/usr/src/debug/eval-spike-1.0-1.'+isa+stage+'.arm/'
            if path.startswith(prefix):
                return '/home/abuild/rpmbuild/BUILD/eval-spike-1.0/'+path[len(prefix):]
    return path


def main(obj):
    dest = OUT/(obj+'-addresses'); temp = TEMP/obj
    dbpath = WORK/'temp/prep-ruling3-4'/(obj+'-static.sqlite')
    db = sqlite3.connect('file:'+str(dbpath)+'?mode=ro', uri=True)
    db.execute('PRAGMA cache_size=-16384')
    expected = collections.Counter()
    values = collections.defaultdict(list)
    for k, f, line, disc, n, status, ref in db.execute('SELECT k,file,line,disc,n,status,ref FROM kv'):
        expected[(k,f,line,disc)] += n
        values[k].append(dict(status=status, file=f, line=line, ref=ref))
    inventory = WORK/'temp/prep-static-gate'/(obj+'-inventory.jsonl')
    names = set()
    with inventory.open() as f:
        metadata = json.loads(next(f)); assert metadata['fs_discriminator'] is False
        for line in f:
            r = json.loads(line); names.add(r['name'])
    actual = collections.Counter(); per_group = collections.Counter(); announced = {}
    relation = temp/'independent-address-key-source.jsonl'
    exclusions = collections.Counter(); record_count = 0
    address_differences = []
    with (WORK/'temp/prep-static-gate'/(obj+'-map.jsonl')).open() as original, \
         (temp/'symbolizer.jsonl').open() as symbolized, relation.open('w') as out:
        for line in original:
            r = json.loads(line)
            if r['kind']=='group':
                announced[r['name']]=r['instruction_count'];continue
            assert r['kind']=='instruction'
            result=json.loads(next(symbolized));assert int(result['Address'],16)==r['query']
            frames=result['Symbol'];key=independent_key(frames)
            per_group[r['group']]+=1;record_count+=1
            if key:
                leaf=frames[len(frames)-len(key)]
                source=[source_path(leaf['FileName']),leaf['Line'],key[-1][2]]
                actual[(key_string(key),*source)]+=1;excluded=None
            else:
                source=None
                excluded=('leaf_line_zero' if not frames or not frames[0]['Line'] else
                          'nonleaf_line_zero' if any(not f['Line'] for f in frames) else 'invalid_name')
                exclusions[excluded]+=1
            old_key=mapped_key(r['frames_leaf_to_root'])
            if old_key:
                old_leaf=r['frames_leaf_to_root'][len(r['frames_leaf_to_root'])-len(old_key)]
                old_source=[source_path(old_leaf['file']),old_leaf['line'],old_key[-1][2]]
                old_excluded=None
            else:
                fs=r['frames_leaf_to_root'];old_source=None
                old_excluded=('leaf_line_zero' if not fs or not fs[0]['line'] else
                              'nonleaf_line_zero' if any(not f['line'] for f in fs) else 'invalid_name')
            address_differences.extend(compare_relations(
                [dict(group=r['group'],address=r['address'],key=old_key,source=old_source,excluded=old_excluded)],
                [dict(group=r['group'],address=r['address'],key=key,source=source,excluded=excluded)]))
            out.write(json.dumps(dict(group=r['group'],address=r['address'],query=r['query'],
              alias=r['alias'],key=key,source=source,excluded=excluded,
              symbolizer_frames=frames),separators=(',',':'))+'\n')
        assert not symbolized.read().strip()
    differences=[dict(key=list(k),expected=expected[k],actual=actual[k])
                 for k in sorted(expected.keys()|actual.keys()) if expected[k]!=actual[k]]
    groups_diff={k:[announced.get(k),per_group[k]] for k in announced.keys()|per_group.keys()
                 if announced.get(k)!=per_group[k]}
    parts=tables(dest,'multiplicity-differences',['record'],([d] for d in differences))
    parts+=tables(dest,'address-relation-differences',['record'],([d] for d in address_differences))
    dump(dest/'independent-relation.json',dict(path=str(relation),sha256=sha(relation),
      records=record_count,exclusions=exclusions,registered_map_key_source_pairs=len(expected),
      independent_key_source_pairs=len(actual),multiplicity_differences=len(differences),
      group_address_count_differences=groups_diff,parts=parts,
      address_relation_differences=len(address_differences),
      source_path_policy='independent explicit prefix normalization; raw FileName also retained',
      fs_discriminator=False))
    assert not differences and not groups_diff and not address_differences, (obj,'relation mismatch')
    group_roles={r['name']:r['role'] for r in rows(BASE/'identity-gate'/(obj+'-groups'),'groups-*.csv')}
    u={(r['file'],int(r['line'])) for r in rows(BASE/'identity-gate/v18-gates'/(obj+'-static'),'U-*.csv')}
    mapping={}
    for k, candidates in values.items():
        statuses={v['status'] for v in candidates}
        special=next((s for s in ['identity_ambiguous','macro_generated_function','system_header_no_reference'] if s in statuses),None)
        mapping[k]=dict(status=special or candidates[0]['status'],
          in_U=len(candidates)==1 and (candidates[0]['file'],candidates[0]['line']) in u,
          excluded=len(candidates)>1 or any((v['file'],v['line']) not in u for v in candidates))
    classifications={}
    for skid in ['none','prev-inst']:
        counts=collections.Counter();data=[]
        for k,count in profile_entries(temp/('synthetic-'+skid+'.proftext')):
            category,reason=classify_entry(k,names,group_roles,mapping)
            counts[category+':'+reason]+=1
            data.append([k,count,category,reason])
        parts=tables(dest,skid+'-fine-classification',['raw_key','synthetic_body_count','category','reason'],data)
        failures={k:v for k,v in counts.items() if k.startswith('unaligned:')}
        classifications[skid]=dict(counts=counts,parts=parts,failures=failures)
        assert not failures,failures
    dump(dest/'fine-classification.json',classifications)
    db.close();print(json.dumps(dict(object=obj,records=record_count,exclusions=exclusions,differences=0)))


if __name__=='__main__':main(sys.argv[1])
