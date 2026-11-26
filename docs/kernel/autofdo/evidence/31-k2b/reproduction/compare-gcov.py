#!/usr/bin/env python3
"""Use K2a's GCOV parser to compare entry counters to K1e and R1 weights."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

from gcov_to_sample import dump_blocks, gcno_paths

ROOT = Path(__file__).resolve().parent
K1 = ROOT.parents[1] / 'kernel-afdo-k1'
BIN = K1 / 'profgen-k1b/review/tool-wrappers'
COV, PROFDATA = BIN/'llvm-cov', BIN/'llvm-profdata'
KBASE = K1/'kbase/artifacts/arm-rpi4/vmlinux'
K1E = K1/'k1e'
R1 = ROOT.parent/'k2a/r1/replay'
BUILD_BUILDDIR = Path('home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80')
SOURCE_ROOT = '/'+str(BUILD_BUILDDIR)+'/'
PROFILE_HEAD = re.compile(r'([^:\s]+):(\d+):(\d+)')
PROFILE_BODY = re.compile(r'( +)(\d+)(?:\.(\d+))?: (\d+)(?=$| )')
PROFILE_INLINE = re.compile(r'( +)\d+(?:\.\d+)?: ([^:\s]+):\d+')
WORKLOADS = ('pipe','mmfault','tmpfs','syscall','tos')
MAX_COUNT = (1 << 64) - 1


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,data):
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')


def run(argv, commands=None, **kwargs):
    if commands is not None:
        commands.write(shlex.join(map(str,argv))+'\n')
        commands.flush()
    return subprocess.run(argv,check=True,text=True,**kwargs)


def relative_name(path):
    return path.removeprefix(SOURCE_ROOT)


def baseline_keys():
    """Require an unambiguous ELF linkage name and exact DWARF decl source/line."""
    readelf = run([BIN/'llvm-readelf','--symbols','--wide',KBASE],capture_output=True).stdout
    syms=defaultdict(set)
    for line in readelf.splitlines():
        match=re.fullmatch(r'\s*\d+:\s+(\S+)\s+(\d+)\s+FUNC\s+\w+\s+\w+\s+\d+\s+(\S+)\s*',line)
        if match and int(match[2]):
            syms[match[3]].add(int(match[1],16) & ~1)
    by_ip=defaultdict(set)
    for name, values in syms.items():
        if len(values)==1:
            address=next(iter(values))
            by_ip[address].add(name)
    addresses=''.join(f'0x{addr:x}\n' for addr in sorted(by_ip))
    out=run([BIN/'llvm-symbolizer','--no-inlines','--functions=linkage','--output-style=JSON',
             '--obj='+str(KBASE)],input=addresses,capture_output=True).stdout
    exact={}
    for line in out.splitlines():
        row=json.loads(line)
        assert len(row['Symbol'])==1
        details=row['Symbol'][0]
        name=details['FunctionName']
        if (name in by_ip[int(row['Address'],16)] and details['StartLine']
                and details['StartFileName'].startswith(SOURCE_ROOT)):
            exact[name]=(relative_name(details['StartFileName']),details['StartLine'])
    return exact,{name for name,ip in syms.items() if len(ip)>1}


@dataclass
class Count:
    head: int = 0
    body: Counter = field(default_factory=Counter)
    foreign_locations: int = 0
    multiple_blocks_on_line: int = 0

    def add(self, row):
        self.head+=row.head
        self.body.update(row.body)
        self.foreign_locations+=row.foreign_locations
        self.multiple_blocks_on_line+=row.multiple_blocks_on_line


def collect_unit(note, data, scratch):
    notes, files = gcno_paths(note, allow_empty=True)
    with note.open('rb') as source_file, data.open('rb') as data_file:
        note_header, data_header = source_file.read(12), data_file.read(12)
        if data_header != b'adcg' + note_header[4:]:
            raise ValueError(f'GCOV version or TU stamp mismatch: {note} / {data}')
        if not notes:
            if data_file.read(1):
                raise ValueError(f'counter records for an empty GCNO: {data}')
            return {}
    with tempfile.TemporaryDirectory(dir=scratch) as t:
        tmp=Path(t)
        (tmp/'unit.gcno').symlink_to(note)
        (tmp/'unit.gcda').symlink_to(data)
        source=files[next(iter(notes.values())).file]
        diag=tmp/'blocks.txt'
        with diag.open('w') as err:
            argv=[COV,'gcov','-n','-a','-b','-c','-f','-dump','-o',tmp/'unit.o',source]
            run(argv,cwd=tmp,stdout=subprocess.DEVNULL,stderr=err)
        try:
            dump_blocks(diag,notes,files)
        except ValueError as e:
            raise ValueError(f'{note} / {data}: {e}') from e
    rows={}
    for fn in notes.values():
        path=relative_name(files[fn.file])
        key=(fn.name,path,fn.start)
        if key in rows:
            raise ValueError(f'ambiguous GCOV declaration in {note}: {key}')
        hits=defaultdict(list)
        foreign=0
        for count,locations in fn.blocks.values():
            foreign+=sum(len(lines) for index,lines in locations.items() if index!=fn.file)
            for line in locations.get(fn.file,()):
                if line>=fn.start:
                    hits[line-fn.start].append(count)
        body=Counter({offset:max(counts) for offset,counts in hits.items()})
        rows[key]=Count(fn.blocks[0][0],body,foreign,sum(len(counts)>1 for counts in hits.values()))
    return rows


def collect(data_root, notes_root, scratch):
    source_root=data_root/BUILD_BUILDDIR/'build/arm-rpi4'
    data=sorted(source_root.rglob('*.gcda'))
    assert data
    notes=[notes_root/f.relative_to(source_root).with_suffix('.gcno') for f in data]
    assert len(data)==len(list(data_root.rglob('*.gcda')))
    assert all(note.is_file() for note in notes)
    merged=defaultdict(Count)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(lambda pair:collect_unit(*pair, scratch),zip(notes,data,strict=True)):
            for key,row in result.items():
                merged[key].add(row)
    return dict(merged)


def matches(rows, keys, duplicates):
    definitions=defaultdict(set)
    for name,filename,line in rows:
        definitions[name].add((filename,line))
    verified={}
    reasons=Counter()
    for name, options in definitions.items():
        if name in duplicates or len(options)!=1 or ':' in name or any(c.isspace() for c in name):
            reasons['ambiguous_or_unsupported_name']+=1
            continue
        candidate=next(iter(options))
        if name not in keys:
            reasons['no_unique_out_of_line_KBASE_symbol_and_source']+=1
        elif keys[name]!=candidate:
            reasons['different_source_or_start_line']+=1
        else:
            verified[name]=(name,*candidate)
    return verified,reasons


def nearest(v):
    return (2*v.numerator+v.denominator)//(2*v.denominator)


def sample_rows(row, scale=Fraction(1), *, preserve_positive_root=False):
    body = {n:nearest(hit*scale) for n,hit in row.body.items()}
    head = nearest(row.head*scale)
    if head>MAX_COUNT or max(body.values(),default=0)>MAX_COUNT:
        raise ValueError('GCOV counter overflows LLVM uint64')
    if not any(body.values()):
        if not preserve_positive_root or not any(row.body.values()):
            return None
        # Keep one sample on the highest-count line to preserve the function.
        strongest = min(row.body, key=lambda line: (-row.body[line], line))
        body[strongest] = 1
    total=max(head,sum(body.values()))
    if total>MAX_COUNT:
        raise ValueError('GCOV profile total overflows LLVM uint64')
    return head,body,total


def text_profile(quantities, scale=Fraction(1), *, preserve_positive_root=False):
    lines=[]
    skipped=0
    for name,row in sorted(quantities.items()):
        out=sample_rows(row, scale, preserve_positive_root=preserve_positive_root)
        if out is None:
            skipped+=1
            continue
        head,body,total=out
        lines.append(f'{name}:{total}:{head}')
        lines.extend(f' {line}: {hits}' for line,hits in sorted(body.items()))
    return ('\n'.join(lines)+'\n' if lines else ''),skipped


def parse_ip(text):
    groups={}
    leaf=Counter()
    root_mass=Counter()
    context=[]
    root=None
    for line in text.splitlines():
        if exact:=PROFILE_HEAD.fullmatch(line):
            root=exact[1]
            assert root not in groups,root
            groups[root]=[line]
            context=[root]
            continue
        assert root is not None and line.startswith(' '),line
        groups[root].append(line)
        if inline:=PROFILE_INLINE.fullmatch(line):
            depth=len(inline[1])
            context=context[:depth]+[inline[2]]
        elif body:=PROFILE_BODY.match(line):
            depth=len(body[1])
            weight=int(body[4])
            context=context[:depth]
            leaf[context[-1]]+=weight
            root_mass[root]+=weight
        else:
            raise ValueError(f'unsupported LLVM sample profile line {line!r}')
    return groups,leaf,root_mass


def average_ranks(items):
    ranks={}
    ordered=sorted(items.items(),key=lambda pair:(pair[1],pair[0]))
    first=0
    while first<len(ordered):
        stop=first+1
        while stop<len(ordered) and ordered[stop][1]==ordered[first][1]:
            stop+=1
        rank=(first+1+stop)/2
        ranks.update((key,rank) for key,_ in ordered[first:stop])
        first=stop
    return ranks


def compare(names, count_weights, ip_weights):
    """Spearman with midranks, including all matched instrumented zeroes."""
    a={name:count_weights.get(name,0) for name in names}
    b={name:ip_weights.get(name,0) for name in names}
    def spearman(a_weights,b_weights):
        p,q=average_ranks(a_weights),average_ranks(b_weights)
        middle=(len(p)+1)/2
        num=sum((p[n]-middle)*(q[n]-middle) for n in p)
        den=math.sqrt(sum((v-middle)**2 for v in p.values())*sum((v-middle)**2 for v in q.values()))
        return num/den if den else None
    visible={name for name in names if a[name] or b[name]}
    def top(table):
        return sorted((n for n in table if table[n]>0),key=lambda n:(-table[n],n))[:30]
    a_top,b_top=top(a),top(b)
    return dict(n=len(names), gcov_nonzero=sum(v>0 for v in a.values()), ip_nonzero=sum(v>0 for v in b.values()),
                spearman=spearman(a,b), spearman_observed_union=spearman({n:a[n] for n in visible},{n:b[n] for n in visible}),
                n_observed_union=len(visible), top30_overlap=len(set(a_top)&set(b_top)),
                top30_gcov=[(name,a[name]) for name in a_top],top30_ip=[(name,b[name]) for name in b_top])


def llvm_merge(output, inputs, commands, text=False, fs=False):
    argv=[PROFDATA,'merge','--sample','--text' if text else '--extbinary']
    if fs:
        argv.append('--profile-isfs')
    run([*argv,'-o',output,*inputs],commands)


def main():
    art=ROOT/'artifacts'
    accepted=json.loads((ROOT/'board-result.json').read_text())
    assert accepted['status']=='complete' and len(accepted['sessions'])==3
    out=ROOT/'profiles'
    out.mkdir()
    keys,duplicates=baseline_keys()
    write(out/'baseline-keys.json',{'unique':keys,'duplicates':sorted(duplicates)})
    per_load=defaultdict(lambda:defaultdict(Count))
    seen_keys=None
    segments=[]
    samples=[]
    with (out/'commands.log').open('w') as commands:
        for run_id in accepted['sessions']:
            for load in WORKLOADS:
                raw=ROOT/run_id/'training'/load/'raw'
                subdir=out/f'{run_id}-{load}'
                subdir.mkdir()
                rows=collect(raw,art/'gcno',subdir)
                if seen_keys is None:
                    seen_keys=set(rows)
                    filtered, exclusions=matches(seen_keys,keys,duplicates)
                assert set(rows)==seen_keys, (run_id, load)
                weights={name:rows[key] for name,key in filtered.items()}
                text,no_body=text_profile(weights)
                if not text:
                    raise ValueError(f'no usable counters in {run_id}/{load}')
                segment=subdir/'segment.proftext'
                segment.write_text(text)
                samples.append(segment)
                for name,row in weights.items():
                    per_load[load][name].add(row)
                segments.append(dict(session=run_id,workload=load,gcno_functions=len(rows),
                      matched_functions=len(filtered),profile_functions=len(filtered)-no_body,
                      zero_or_no_body=no_body,line_locations_foreign=sum(row.foreign_locations for row in weights.values()),
                      lines_with_multiple_blocks=sum(row.multiple_blocks_on_line for row in weights.values()),
                      entry_count=sum(row.head for row in weights.values()),
                      max_entry_count=max(row.head for row in weights.values()),
                      max_line_count=max(max(row.body.values(),default=0) for row in weights.values()),
                      sha256=digest(segment)))
                print(f'{run_id}/{load} {len(filtered)-no_body} executed eligible functions',flush=True)
        write(out/'matched-functions.json',filtered)
        assert len(samples)==15
        gcov_path=out/'K-AFDO-GCOV.prof'
        llvm_merge(gcov_path,samples,commands)
        summary_info=run([PROFDATA,'show','--sample','--show-sec-info-only',gcov_path],
                         commands,capture_output=True).stdout
        assert 'fs-discriminator' not in summary_info
        (out/'gcov-header.txt').write_text(summary_info)
        original,corrected,merged=Counter(),Counter(),defaultdict(Count)
        stats={}
        for load in WORKLOADS:
            ips=[[root/f'session-{n:02d}'/load/'segment.prof' for n in (1,2,3)] for root in (K1E,R1)]
            vectors=[]
            for method, paths in zip(('ip','r1'),ips,strict=True):
                proftext=out/f'{method}-{load}.proftext'
                llvm_merge(proftext,paths,commands,text=True)
                vectors.append(parse_ip(proftext.read_text())[1])
            original.update(vectors[0])
            corrected.update(vectors[1])
            for name,row in per_load[load].items():
                merged[name].add(row)
            using={name:row.head for name,row in per_load[load].items()}
            stats[load]={'ip':compare(filtered,using,vectors[0]), 'r1':compare(filtered,using,vectors[1])}
        using={name:row.head for name,row in merged.items()}
        stats['all']={'ip':compare(filtered,using,original),'r1':compare(filtered,using,corrected)}
        write(out/'rank-comparison.json',stats)
        merged_text=out/'gcov-merged.proftext'
        llvm_merge(merged_text,[gcov_path],commands,text=True)
        observed=parse_ip(merged_text.read_text())[1]
        assert all(observed[name]==sum(row.body.values()) for name,row in merged.items())
        quality={'sessions':len(accepted['sessions']), 'segments':segments,
                 'gcno_declarations':len(seen_keys),'gcno_distinct_names':len({name for name,_,_ in seen_keys}),
                 'matched_KBASE_names':len(filtered),'unmatched_names':dict(exclusions),
                 'matched_name_pct':100*len(filtered)/len({name for name,_,_ in seen_keys}),
                 'merged_positive_profile_names':sum(value>0 for value in observed.values()),
                 'gcov_sha256':digest(gcov_path),'gcov_profile_has_fs_discriminators':False}
        write(out/'gcov-quality.json',quality)

        # Partition on the outer function. An inlined R1 copy under an
        # uninstrumented caller keeps that caller's context and discriminator.
        r1_text=out/'r1-all.proftext'
        llvm_merge(r1_text,[R1/'K-AFDO-R1.prof'],commands,text=True)
        r1,_,root_mass=parse_ip(r1_text.read_text())
        assert sum(root_mass.values())>0
        positive={name for name in filtered if observed[name]>0}
        zero={name for name,row in merged.items() if row.body and not row.head and not observed[name]}
        replace=positive|zero
        mass=sum(root_mass[name] for name in replace)
        counts=sum(observed[name] for name in positive)
        assert mass>0 and counts>0
        scale=Fraction(mass,counts)
        positive_counts = {name: merged[name] for name in positive}
        _, roots_preserved = text_profile(positive_counts, scale)
        scaled, dropped = text_profile(positive_counts, scale, preserve_positive_root=True)
        g,_leaf,_root=parse_ip(scaled)
        assert set(g) == positive and dropped == 0
        keep=set(r1)-replace
        hybrid_text=out/'hybrid.proftext'
        hybrid_text.write_text(scaled+''.join('\n'.join(r1[name])+'\n' for name in sorted(keep)))
        hybrid=out/'K-AFDO-HYB.prof'
        llvm_merge(hybrid,[hybrid_text],commands,fs=True)
        summary_info=run([PROFDATA,'show','--sample','--show-sec-info-only',hybrid],
                         commands,capture_output=True).stdout
        assert 'fs-discriminator' in summary_info
        (out/'hybrid-header.txt').write_text(summary_info)
        readback=out/'hybrid-readback.proftext'
        llvm_merge(readback,[hybrid],commands,text=True)
        groups2,_,mass2=parse_ip(readback.read_text())
        assert set(groups2)==set(g)|keep
        assert all(groups2[name]==r1[name] for name in keep)
        hybrid_summary={'sha256':digest(hybrid), 'scale_numerator':scale.numerator, 'scale_denominator':scale.denominator,
                        'covered_r1_mass':mass, 'unscaled_gcov_line_mass':counts, 'scaled_gcov_line_mass':sum(mass2[n] for n in g),
                        'covered_roots_used':len(g), 'r1_roots_retained':len(keep),
                        'gcov_roots_preserved_by_one_line_floor':roots_preserved,
                        'gcov_roots_lost_to_rounding':dropped,
                        'covered_roots':len(replace), 'covered_zero_roots':len(zero),
                        'covered_R1_roots_replaced_by_zero':len(zero&set(r1)),
                        'uses_fs_flag_for_untouched_R1_contexts':True, 'gcov_rows_have_discriminator_zero':True,
                        'partition':('root names with unique KBASE source/line match and a positive GCOV body '
                                     'or mapped zero body with zero entry count')}
        write(out/'hybrid-quality.json',hybrid_summary)


if __name__=='__main__':
    main()
