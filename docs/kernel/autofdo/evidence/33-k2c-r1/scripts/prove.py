import ast
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import yaml

task=Path(__file__).resolve().parent
k0=task.parent
k1=task.parents[1]/'kernel-afdo-k1'
run=task/sys.argv[1]
root=run/'gbs-root/local/BUILD-ROOTS/scratch.armv7l.0'
ref=k0/'k1f-2/kbase-s2/gbs-root/local/BUILD-ROOTS/scratch.armv7l.0'
kit=k0/'relink-kits/K-BASE'
build=Path('home/abuild/rpmbuild/BUILD/rpi4-linux-kernel-6.12.80/build')
artifacts=run/'artifacts'
artifacts.mkdir(exist_ok=True)
sys.path.insert(0,str(k0/'k1f-2'))
from trace_build import compile_parts, trace, variants

elf_globals={}
elf_source=(k1/'k1c-review/objects.py').read_text().split('archives=',1)[0]
exec(compile(elf_source,'K1c ELF reader','exec'),elf_globals)
elf=elf_globals['elf']

def read(path):
    return json.loads(path.read_text())

def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def call(*args,**kwargs):
    return subprocess.check_output([str(arg) for arg in args],text=True,**kwargs)

def build_id(path):
    return re.search(r'Build ID:\s+([0-9a-f]+)',call('readelf','-n',path))[1]

def commands(path):
    result={}
    for file in path.rglob('*.o.cmd'):
        line=file.open(errors='surrogateescape').readline().rstrip('\n')
        if ' := ' not in line:
            continue
        argv=compile_parts(line.split(' := ',1)[1])
        if argv:
            result[file.relative_to(path).as_posix()]=argv
    return result

def symbols(path):
    return {parts[2]:int(parts[0],16) for row in path.open() if len(parts:=row.split())==3}

def banner(binary, table):
    addr=table['linux_banner']
    section=next(section for section in elf(binary)[3].values()
                 if section[1]==1 and section[2]&2 and section[3]<=addr<section[3]+section[5])
    with binary.open('rb') as stream:
        stream.seek(section[4]+addr-section[3])
        return stream.read(512).split(b'\0',1)[0].decode().rstrip('\n')

def compare(old,new):
    builtin=set(old)&set(new)
    return dict(reference=len(old),candidate=len(new),missing=sorted(set(old)-set(new)),
                extra=sorted(set(new)-set(old)),different=sorted(key for key in builtin if old[key]!=new[key]))

def clean(diff):
    return not (diff['missing'] or diff['extra'] or diff['different'])

def vermagic(path):
    return {file.relative_to(path).as_posix():call('modinfo','-F','vermagic',file).strip()
            for file in sorted(path.rglob('*.ko'))}

def text_sha(path):
    section=elf(path)[3].get('.text')
    if section is None:
        return None
    with path.open('rb') as stream:
        stream.seek(section[4])
        return hashlib.sha256(stream.read(section[5])).hexdigest()

def rt_tool(chroot, name):
    rt=chroot/'emul/usr'
    return [rt/'lib64/ld-linux-x86-64.so.2','--library-path',rt/'lib64',
            '--argv0',name,rt/'bin'/name]

def kbase_profile_function_positions(out, old, name_rows, obj_to_names):
    # Resolve the C declaration of each selected function from the archived K-BASE ELF.
    by_address=defaultdict(set)
    for name,start,_,info,_ in elf(old/'vmlinux',True)[2]:
        if info&15==2 and name in obj_to_names:
            by_address[start & ~1].add(name)
    llvm=k1/'profgen-k1b/review/tool-wrappers/llvm-symbolizer'
    raw=call(llvm,'--no-inlines','--functions=linkage','--output-style=JSON',f'--obj={old/"vmlinux"}',
             input=''.join(f'0x{address:x}\n' for address in sorted(by_address)))
    locations=defaultdict(set)
    for line in raw.splitlines():
        row=json.loads(line)
        for site in row['Symbol']:
            name=site['FunctionName']
            if name in by_address[int(row['Address'],16)] and site['StartLine']:
                source=site['StartFileName'].split('rpi4-linux-kernel-6.12.80/')[-1]
                locations[name].add((source,site['StartLine']))
    selected=[]
    excluded=[]
    for name,weight in name_rows:
        options={(obj,source,lineno) for obj,source in obj_to_names.get(name,[])
                 for f,lineno in locations.get(name,set()) if source==f}
        if len(options)!=1:
            excluded.append(dict(name=name,weight=weight,options=sorted(options)))
            continue
        obj,source,lineno=next(iter(options))
        selected.append(dict(name=name,weight=weight,object=obj,source=source,start_line=lineno))
        if len(selected)==20:
            break
    save(out/'source-match.json',dict(selected=selected,excluded=excluded))
    assert len(selected)==20
    return selected

class RemarkLoader(yaml.SafeLoader):
    pass

RemarkLoader.add_multi_constructor('!',lambda loader,_,node:loader.construct_mapping(node,deep=True))

def consumption(out, old, obj, members, profile):
    profdata=k1/'profgen-k1b/review/tool-wrappers/llvm-profdata'
    headings=call(profdata,'show','--sample',profile)
    functions=sorted(((m[1],int(m[2])) for m in re.finditer(
        r'^Function: (.*): (\d+), \d+, \d+ sampled lines',headings,re.M)),
        key=lambda row:(-row[1],row[0]))
    assert len(functions)>=20
    irq_helpers={'_raw_spin_unlock_irqrestore','arch_local_irq_enable','arch_local_irq_restore',
                 'local_irq_enable','local_irq_restore','raw_local_irq_enable','raw_local_irq_restore',
                 '_raw_spin_unlock_irq','_raw_read_unlock_irqrestore','_raw_write_unlock_irqrestore',
                 '_raw_read_unlock_irq','_raw_write_unlock_irq'}
    weights={name for name,_ in functions}-irq_helpers
    by_name=defaultdict(list)
    for member in members:
        entry=Path(member)
        receipt=obj/entry.parent/f'.{entry.name}.cmd'
        if not (kit/'arm-rpi4'/member).is_file() or not receipt.is_file():
            continue
        argv=compile_parts(receipt.open().readline().split(' := ',1)[1])
        if not argv:
            continue
        source=next((arg.split('rpi4-linux-kernel-6.12.80/')[-1] for arg in argv if arg.endswith('.c')),None)
        if source and source.startswith(('kernel/','mm/','fs/','lib/','arch/','drivers/','net/','ipc/','init/','block/',
                                         'security/','sound/','crypto/','io_uring/','virt/','certs/')):
            for name,_,_,info,_ in elf(kit/'arm-rpi4'/member,True)[2]:
                if name in weights and info&15==2:
                    by_name[name].append((member,source))
    selected=kbase_profile_function_positions(out,old,functions,by_name)
    results={}
    for i,member in enumerate(sorted({row['object'] for row in selected})):
        d=out/f'object-{i:02d}'
        d.mkdir()
        kobj=Path(member)
        argv=compile_parts((obj/kobj.parent/f'.{kobj.name}.cmd').open().readline().split(' := ',1)[1])
        assert any(arg==f'-fprofile-sample-use=/home/abuild/rpmbuild/SOURCES/{profile.name}' for arg in argv)
        args=[arg.replace('/home/abuild',str(root)+'/home/abuild') for arg in argv[1:] if not arg.startswith('-Wp,-MMD,')]
        args[args.index('-o')+1]=str(d/'diagnostic.o')
        command=[*rt_tool(root,'clang-22'),'-no-canonical-prefixes',*args,
                 '-fsave-optimization-record=yaml','-foptimization-record-passes=sample-profile',
                 f'-foptimization-record-file={d/"remarks.yaml"}',
                 '-mllvm','-sample-profile-check-record-coverage=100',
                 '-mllvm','-sample-profile-check-sample-coverage=100']
        save(d/'argv.json',list(map(str,command)))
        with (d/'clang.log').open('w') as log:
            subprocess.run(command,cwd=obj,stdout=log,stderr=subprocess.STDOUT,check=True)
        a,b=text_sha(kit/'arm-rpi4'/member),text_sha(obj/member)
        results[member]=dict(kbase_text_sha256=a,candidate_text_sha256=b,text_changed=a!=b)
        applied=defaultdict(Counter)
        remarks=d/'remarks.yaml'
        if remarks.is_file():
            for record in yaml.load_all(remarks.read_text(),Loader=RemarkLoader):
                if record and record.get('Name')=='AppliedSamples' and record.get('Pass') in {'sample-profile','sample-profile-impl'}:
                    samples=next((int(arg['NumSamples']) for arg in record.get('Args',[]) if 'NumSamples' in arg),0)
                    if samples:
                        applied[record['Function']].update(positive_remarks=1,total_num_samples=samples)
        if applied:
            save(d/'applied.json',dict(applied))
        warns=re.compile(r'([^\s:]+):(\d+)(?::\d+)?:\s*(?:warning:\s*)?(\d+) of (\d+) available profile (records|samples) \((\d+)%\) were applied')
        for row in (row for row in selected if row['object']==member):
            row['applied']=dict(applied[row['name']])
            row['coverage']={}
            for line in (d/'clang.log').read_text().splitlines():
                if (m:=warns.search(line)) and int(m[2])==row['start_line'] and (
                   row['source'].endswith(m[1]) or m[1].endswith(row['source'])):
                    row['coverage'][m[5]]=dict(used=int(m[3]),total=int(m[4]),percent=int(m[6]))
    syms=symbols(obj/'System.map')
    a,b=syms['__hot_text_start'],syms['__hot_text_end']
    for row in selected:
        address=syms.get(row['name'])
        row['final_hot']=a<=address<b if address is not None else None
    gate=dict(functions=selected,objects=results,
              positive_functions=sum(bool(row['applied']) for row in selected),
              text_changes=sum(row['text_changed'] for row in results.values()))
    save(out/'results.json',gate)
    assert gate['positive_functions']>0 and gate['text_changes']>0
    return dict(positive=gate['positive_functions'],selected=len(selected),objects=len(results),text_changes=gate['text_changes'])

def layout(out,old,obj,members,final):
    supplied=final[1:].copy()
    supplied[supplied.index('-o')+1]=str(out/'diagnostic.vmlinux')
    supplied.append(f'-Map={out/"link.map"}')
    command=[*rt_tool(root,'ld.lld'),*supplied]
    save(out/'map-argv.json',list(map(str,command)))
    with (out/'link-replay.stderr').open('w') as error:
        subprocess.run(command,cwd=obj,stderr=error,check=True)
    assert build_id(out/'diagnostic.vmlinux')==build_id(obj/'vmlinux')
    row=re.compile(r'^\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+[0-9]+( +)(.+)$')
    def collect(path):
        dest=''
        result=[]
        with path.open() as stream:
            for line in stream:
                match=row.match(line.rstrip('\n'))
                if not match:
                    continue
                addr,size,indent,value=match.groups()
                if len(indent)==1 and re.fullmatch(r'[^\s:]+',value):
                    dest=value
                if len(indent)==9 and dest and (m:=re.fullmatch(r'(.*):\(([^)]+)\)',value)):
                    result.append((dest,m[1],m[2],int(addr,16),int(size,16)))
        return result
    baseline=collect(k1/'k1e/link-maps/kbase.map')
    candidate=collect(out/'link.map')
    a=[(path,sect) for dest,path,sect,_,size in baseline if dest=='.text' and sect.startswith('.text') and size]
    b=[(path,sect) for dest,path,sect,_,size in candidate if dest=='.text' and sect.startswith('.text') and size]
    multiplicity_a,multiplicity_b=Counter(a),Counter(b)
    common={key for key in set(a)&set(b) if multiplicity_a[key]==multiplicity_b[key]==1}
    a=[key for key in a if key in common]
    b=[key for key in b if key in common]
    assert common and Counter(a)==Counter(b)
    name_counts=Counter()
    profile_objects=0
    for member in members:
        _,callgraph,function_symbols,sections=elf(obj/member,True)
        profile_objects+=bool(callgraph)
        for name,section in sections.items():
            for prefix in ('.text.hot','.text.unlikely'):
                if name.startswith(prefix):
                    name_counts[prefix+'_input_sections']+=1
                    name_counts[prefix+'_bytes']+=section[5]
                    name_counts[prefix+'_functions']+=len({s[0] for s in function_symbols if s[3]&15==2 and s[4]==name})
    names=('__hot_text_start','__hot_text_end','__unlikely_text_start','__unlikely_text_end','_stext','_etext','_end')
    def sizes(loc):
        syms=symbols(loc/'System.map')
        sec=elf(loc/'vmlinux')[3]
        assert all(sym in syms for sym in names)
        result={name:sec[name][5] for name in ('.text','.rodata','.data','.bss')}
        result.update({name:syms[name] for name in names})
        result.update(image_span=syms['_end']-syms['_stext'],
                      text_slack=syms['_etext']-sec['.text'][3]-sec['.text'][5],
                      tier_2MiB=(syms['_end']-syms['_stext']+0x1fffff)//0x200000,
                      hot_bytes=syms[names[1]]-syms[names[0]],cold_bytes=syms[names[3]]-syms[names[2]],
                      zImage_bytes=(loc/'arch/arm/boot/zImage').stat().st_size)
        return result
    table=symbols(obj/'System.map')
    special=('.head.text','.idmap.text','.entry.text','.irqentry.text','.softirqentry.text',
             '.ARM.exidx','.ARM.extab','.init.text','.exit.text')
    def special_destinations(rows):
        return {source:sorted({out for out,_,sect,_,_ in rows if sect==source}) for source in special}
    baseline_special=special_destinations(baseline)
    candidate_special=special_destinations(candidate)
    misplaced=[]
    for dest,path,sect,addr,size in candidate:
        tag=next((name for name in ('hot','unlikely') if sect.startswith('.text.'+name)),None)
        if tag and size:
            low,high=(table[f'__{tag}_text_start'],table[f'__{tag}_text_end'])
            if dest!='.text' or not (low<=addr<addr+size<=high):
                misplaced.append((dest,path,sect,addr,size))
    id_first,id_last=table['__idmap_text_start'],table['__idmap_text_end']
    exports_file=k0/'k1f-1d/exports.py'
    tree=ast.parse(exports_file.read_text(),filename=str(exports_file))
    tree.body=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom,ast.FunctionDef))]
    export_env={}
    exec(compile(tree,str(exports_file),'exec'),export_env)
    exports={section:row for section,row,_,_ in export_env['inspect'](obj/'vmlinux',obj/'Module.symvers')}
    bad=('strict_order_violations','crc_order_violations','crc_name_slot_mismatch',
         'crc_values_differ_from_named_module_symvers')
    assert exports and all(not row[key] for row in exports.values() for key in bad)
    assert any(row['module_layout']['bsearch_index'] is not None for row in exports.values())
    assert id_first//4096==(id_last-1)//4096
    status=dict(export_tables=exports, arm_special_destinations=candidate_special,
                arm_special_destinations_match_base=baseline_special==candidate_special,
                misplaced_hot_cold_inputs=misplaced,idmap_first=id_first,idmap_last=id_last,
                text_input_destinations=dict(Counter(f'{source} -> {out}' for out,_,source,_,size in candidate
                                                     if size and source.startswith('.text.'))),
                common_text_inputs=len(common),changed_positions=sum(left!=right for left,right in zip(a,b,strict=True)),
                profile_objects=profile_objects,section_counts=dict(name_counts),base=sizes(old),candidate=sizes(obj))
    save(out/'layout.json',status)
    assert not misplaced and baseline_special==candidate_special
    return status

def main():
    status=read(run/'logs/result.json')
    assert status['status']=='passed'
    profile=next((run/'export-src/packaging').glob('K-AFDO-*.prof'))
    assert digest(profile)==status['profile_sha256']
    assert digest(root/'home/abuild/rpmbuild/SOURCES'/profile.name)==status['profile_sha256']
    expected={f'{row["installed"]} {row["rpm_header_sha256"]}'
              for row in read(k1/'base-0fac5de6/dependencies/installed-matched-04.json')}
    installed=set(call('rpm','--dbpath',root/'var/lib/rpm','-qa','--qf',
                    '%{NAME} %{VERSION} %{RELEASE} %{ARCH} %{SHA256HEADER}\n').splitlines())
    save(artifacts/'dependencies.json',dict(count=len(installed),missing=sorted(expected-installed),
                                           extra=sorted(installed-expected)))
    assert expected==installed and len(installed)==130
    basecc,baseld,basemods,_=trace(k1/'k1e/kbase-s/logs/build.log')
    newcc,newld,newmods,_=trace(run/'logs/build.log')
    prof_arg=f'-fprofile-sample-use=/home/abuild/rpmbuild/SOURCES/{profile.name}'
    result={}
    for variant in variants:
        old=k1/'kbase/artifacts'/variant
        obj=root/build/variant
        reference=ref/build/variant
        out=artifacts/variant
        out.mkdir(exist_ok=True)
        raw=commands(obj)
        ref_cmd=commands(reference)
        profile_flags=sum(row.count(prof_arg) for row in raw.values())
        def strip(table):
            return {key:[token for token in value if token!=prof_arg] for key,value in table.items()}
        checks=dict(saved_argv=compare(ref_cmd,strip(raw)),verbose_argv=compare(basecc[variant],strip(newcc[variant])),
                    modules_argv=compare(basemods[variant],newmods[variant]),profile_compile_count=profile_flags)
        save(out/'compile-check.json',checks)
        assert profile_flags and all(clean(checks[key]) for key in ('saved_argv','verbose_argv','modules_argv')),checks
        assert (obj/'.config').read_bytes()==(old/'.config').read_bytes()
        assert sorted((obj/'Module.symvers').read_text().splitlines())==sorted((old/'Module.symvers').read_text().splitlines())
        a,b=vermagic(reference),vermagic(obj)
        assert a==b and a
        release=(obj/'include/generated/utsrelease.h').read_text().split('"')[1]
        assert all(value.startswith(release+' ') for value in b.values())
        for header in ('compile.h','utsrelease.h','utsversion.h'):
            expected=(old/'include/generated'/header).read_bytes()
            if variant.endswith('-rt'):
                expected=expected.replace(b'Wed Nov 18 15:19:44 UTC 2026',b'Wed Nov 18 14:59:26 UTC 2026')
            assert (obj/'include/generated'/header).read_bytes()==expected
        expected_banner=banner(old/'vmlinux',symbols(old/'System.map')).replace('Wed Nov 18 15:19:44 UTC 2026','Wed Nov 18 14:59:26 UTC 2026') if variant.endswith('-rt') else banner(old/'vmlinux',symbols(old/'System.map'))
        build_banner=banner(obj/'vmlinux',symbols(obj/'System.map'))
        assert build_banner==expected_banner
        ld=newld[variant]
        assert {key:[v for v in argv if v!='--shuffle-sections=.text*=20261120'] for key,argv in baseld[variant].items()}==ld
        assert ld['vmlinux']==read(kit/variant/'final-ld-argv.json')
        assert (obj/'arch/arm/kernel/vmlinux.lds').read_bytes()==(reference/'arch/arm/kernel/vmlinux.lds').read_bytes()
        member_order=call('ar','t','vmlinux.a',cwd=obj).splitlines()
        assert member_order==(kit/variant/'vmlinux-a-order.txt').read_text().splitlines()
        events=dict(release=release,banner=build_banner,build_id=build_id(obj/'vmlinux'),
                    zImage_sha256=digest(obj/'arch/arm/boot/zImage'), module_count=len(b),
                    module_crc_count=len((obj/'Module.symvers').read_text().splitlines()),
                    compiler=checks, vmlinux_sha256=digest(obj/'vmlinux'))
        save(out/'link-argv.json',ld)
        save(out/'module-vermagic.json',b)
        (out/'vmlinux-a-order.txt').write_text('\n'.join(member_order)+'\n')
        for name in ('.config','vmlinux','System.map','Module.symvers','arch/arm/boot/zImage'):
            p=out/name
            p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(obj/name,p)
        if variant=='arm-rpi4':
            events['layout']=layout(out,old,obj,member_order,ld['vmlinux'])
            diag=out/'consumption'
            diag.mkdir()
            events['consumption']=consumption(diag,old,obj,member_order,profile)
        result[variant]=events
    save(artifacts/'variant-verification.json',result)

if __name__=='__main__':
    main()
