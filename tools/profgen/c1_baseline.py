#!/usr/bin/env python3
"""Replay existing profgen RUN commands without FileCheck; no LLVM build.

All products stay under WORKDIR/temp. Use the SAME --scratch path for baseline
and candidate: diagnostics may contain absolute filenames. Two passes reuse
that path, archive exact stdout/stderr/profile bytes, and compare without
normalization. FileCheck/not/redirection are harness constructs, not profgen
arguments. Required fixture preparation is replayed via a small allowlist;
unrecognized shell constructs fail closed. No tests or RUNs are generated.
"""
import argparse, hashlib, json, os, re, resource, shlex, shutil, subprocess
from pathlib import Path
W = Path(__file__).resolve().parents[2]
L = W / 'temp/llvm-profgen-enh'
R = W / 'temp/GBS-ROOT-LLVM-X86/local/BUILD-ROOTS/scratch.x86_64.0'
B = L / 'build'
EXPECTED = 'a31073338f9315a0fd6d2934e36431d9135086882ebfb07bd1bda7c36d7f9f1e'

def sha(b): return hashlib.sha256(b).hexdigest()
def under(path, root):
    p = Path(path).resolve()
    if not p.is_relative_to(root.resolve()): raise ValueError(f'outside allowed root: {p}')
    return p

def loaded(exe):
    return ['nice', '-n', '19', 'ionice', '-c3', str(R/'lib64/ld-linux-x86-64.so.2'),
            '--library-path', ':'.join(map(str, [B/'lib64', R/'lib64', R/'usr/lib64'])), str(exe)]

def runlines(path):
    pending = ''; start = 0
    for num, line in enumerate(path.read_text().splitlines(), 1):
        m = re.search(r'\bRUN:\s*(.*)', line)
        if not m: continue
        if not pending: start = num
        x = m[1]; pending += x[:-1] + ' ' if x.endswith('\\') else x
        if not x.endswith('\\'):
            yield start, pending; pending = ''
    if pending: raise ValueError(f'unterminated RUN {path}:{start}')

def expand(cmd, path, tmp):
    for key, value in [('%S', path.parent), ('%p', path.parent), ('%s', path), ('%T', tmp.parent), ('%t', tmp)]:
        cmd = cmd.replace(key, str(value))
    if re.search(r'%[A-Za-z{]', cmd): raise ValueError(f'unknown lit substitution: {cmd}')
    return cmd

def args_only(cmd):
    # Current suite uses shell redirects only for inspection; preserve actual
    # stderr separately rather than treating `not`'s inverted status as tool rc.
    cmd = cmd.split('|', 1)[0]
    cmd = re.sub(r'(?:\s|^)(?:&>|[12]?>&|[12]?>)\s*(?:\d+|[^\s]+)', ' ', cmd)
    args = shlex.split(cmd)
    if args and args[0] == 'not': args.pop(0)
    if any(a in ['&&', ';', '&', '||'] for a in args): raise ValueError(cmd)
    return args

def option(args, names):
    for i, a in enumerate(args):
        for n in names:
            if a == n: return args[i+1]
            if a.startswith(n+'='): return a.split('=', 1)[1]
    return None

def change_format(args, fmt):
    out=[];i=0
    while i < len(args):
        a=args[i]
        if a in ['--format','-format']: i+=2;continue
        if a.startswith(('--format=','-format=')): i+=1;continue
        out.append(a);i+=1
    return out+['--format='+fmt]

def prep(cmd, cwd, scratch, env):
    a=shlex.split(cmd)
    if not a:return cwd,None
    op=a[0]
    if op == 'cd': return under(a[1], scratch), None
    if op == 'rm':
        assert a[1]=='-rf';p=under(a[2],scratch)
        if p.exists(): shutil.rmtree(p) if p.is_dir() else p.unlink()
        return cwd,None
    if op=='mkdir':
        assert a[1]=='-p';under(a[2],scratch).mkdir(parents=True,exist_ok=True);return cwd,None
    if op=='cp':
        assert len(a)==3;shutil.copyfile(under(a[1],W),under(a[2],scratch));return cwd,None
    if op=='echo':
        assert a[1]=='-e' and a[-2]=='>'
        under(a[-1],scratch).write_text(bytes(a[2],'utf8').decode('unicode_escape')+'\n');return cwd,None
    if op in ['llvm-objcopy','yaml2obj','llvm-dwp']:
        c=loaded(B/'bin'/op)+a[1:];p=subprocess.run(c,cwd=cwd,env=env,capture_output=True)
        r={'command':shlex.join(c),'exit':p.returncode,'stderr':p.stderr.decode(errors='replace')}
        if p.returncode: raise RuntimeError(r)
        return cwd,r
    if op in ['FileCheck','diff','llvm-profdata']: return cwd,None
    raise ValueError(f'unsupported preparation: {cmd}')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tool',type=Path,default=B/'bin/llvm-profgen')
    ap.add_argument('--scratch',type=Path,default=W/'temp/profgen-c1-baseline')
    ap.add_argument('--manifest',type=Path,default=W/'tools/profgen/c1-baseline.json')
    ap.add_argument('--compare',type=Path)
    ap.add_argument('--expected-tool-sha',default=EXPECTED)
    opt=ap.parse_args()
    if opt.compare and opt.compare.resolve()==opt.manifest.resolve():
        raise SystemExit('--manifest must differ from --compare; preserve the baseline manifest')
    under(opt.tool,W);scratch=under(opt.scratch,W/'temp');under(opt.manifest,W)
    digest=sha(opt.tool.read_bytes())
    if opt.expected_tool_sha and digest!=opt.expected_tool_sha:raise SystemExit('tool SHA mismatch: '+digest)
    scratch.mkdir(parents=True,exist_ok=True)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env={**os.environ,'TMPDIR':str(W/'temp/tmp'),'LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
    tests=sorted(p for p in (L/'llvm/test/tools/llvm-profgen').rglob('*') if p.suffix in ['.test','.ll','.s','.yaml'] and 'Inputs' not in p.parts and p.is_file())
    passes=[];preparations=[]
    for turn in [1,2]:
        work=scratch/'work'
        if work.exists():shutil.rmtree(work)
        work.mkdir();archive=scratch/f'pass{turn}';archive.mkdir(exist_ok=True)
        records=[]
        for test in tests:
            home=work/test.stem;home.mkdir();tmp=home/'tmp';cwd=home
            for line,raw in runlines(test):
                cmd=expand(raw,test,tmp)
                if not re.match(r'^(?:not\s+)?llvm-profgen\b', cmd):
                    cwd,r=prep(cmd,cwd,scratch,env)
                    if r:preparations.append({'pass':turn,'test':test.name,'line':line,**r})
                    continue
                args=args_only(cmd)
                ident=f'{test.stem}-{line}'
                original=option(args,['--output','-o']);original_bytes=None
                # Fixed superset of C1: binary on CS/probe/diagnostic paths is
                # extra error-behavior coverage, never a supported-profile claim.
                modes=['original','text','extbinary','gcc','binary']
                for fmt in modes:
                    av=args[1:] if fmt=='original' else change_format(args[1:],fmt)
                    output=option(av,['--output','-o'])
                    # A producer can read a previous output; snapshot only its
                    # own output, restoring original bytes after matrix replay.
                    if output and output not in ['-', '/dev/null']:
                        pth=under(output,scratch)
                        if pth.exists():pth.unlink()
                    c=loaded(opt.tool)+av
                    p=subprocess.run(c,cwd=cwd,env=env,capture_output=True,timeout=180)
                    profile=p.stdout if output=='-' else (Path(output).read_bytes() if output and Path(output).is_file() else None)
                    tag=ident+'-'+fmt
                    (archive/(tag+'.stderr')).write_bytes(p.stderr);(archive/(tag+'.stdout')).write_bytes(p.stdout)
                    if profile is not None:(archive/(tag+'.profile')).write_bytes(profile)
                    record={'test':str(test.relative_to(L)),'line':line,'format':fmt,'original_RUN':raw,'command':shlex.join(['llvm-profgen', *av]),'cwd':str(cwd),'exit':p.returncode,'profile_sha256':sha(profile) if profile is not None else None,'profile_bytes':len(profile) if profile is not None else None,'stderr_sha256':sha(p.stderr),'stdout_sha256':sha(p.stdout),'stderr_file':tag+'.stderr'}
                    records.append(record)
                    if fmt=='original':original_bytes=profile
                if original and original not in ['-', '/dev/null']:
                    pp=Path(original)
                    if original_bytes is not None:pp.write_bytes(original_bytes)
                    elif pp.exists():pp.unlink()
            print(f'pass{turn}: {test.name}',flush=True)
        # Legacy pure-IP negative, binary is known readable x86 fixture so the
        # failure must come from the reader, not ARM support or missing ELF.
        pure=work/'pure-ip.perfscript'
        source=W/'docs/probe/evidence/05/02_perf_formats_mapping.txt'
        selected=[(n,l) for n,l in enumerate(source.read_text().splitlines(),1) if re.match(r'^\s*\d+/\d+\s+\d+ cycles:\s+[a-f0-9]+ \(',l)][:20]
        assert selected;pure.write_text('\n'.join(l for _,l in selected)+'\n')
        av=['--perfscript='+str(pure),'--binary='+str(L/'llvm/test/tools/llvm-profgen/Inputs/inline-noprobe.perfbin'),'--output='+str(work/'pure.profile')]
        c=loaded(opt.tool)+av;p=subprocess.run(c,env=env,cwd=work,capture_output=True)
        (archive/'pure-ip.stderr').write_bytes(p.stderr);(archive/'pure-ip.stdout').write_bytes(p.stdout)
        pure_output=work/'pure.profile'
        pure_profile=pure_output.read_bytes() if pure_output.exists() else None
        if pure_profile is not None:(archive/'pure-ip.profile').write_bytes(pure_profile)
        records.append({'test':'pure-ip-from-05','line':selected[0][0],'format':'original','command':shlex.join(['llvm-profgen', *av]),'exit':p.returncode,'profile_sha256':sha(pure_profile) if pure_profile is not None else None,'stderr_sha256':sha(p.stderr),'stdout_sha256':sha(p.stdout),'stderr_file':'pure-ip.stderr','source':str(source.relative_to(W)),'source_lines':[n for n,_ in selected]})
        passes.append(records)
    differences=[{'index':i,'first':x,'second':y} for i,(x,y) in enumerate(zip(*passes)) if x!=y]
    assert len(passes[0])==len(passes[1])
    result={'launch_prefix':loaded(opt.tool),'command_expansion':'replace leading llvm-profgen token with launch_prefix; no normalization of measured bytes','tool_sha256':digest,'tool':str(opt.tool),'scratch':str(scratch),'tests_scanned':len(tests),'original_commands':sum(x['format']=='original' for x in passes[0])-1,'pure_ip_commands':1,'format_variants':sum(x['format']!='original' for x in passes[0]),'runs_per_pass':len(passes[0]),'two_pass_equal':not differences,'differences':differences,'preparations':preparations,'records':passes[0]}
    opt.manifest.parent.mkdir(parents=True,exist_ok=True);opt.manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if opt.compare:
        old=json.loads(opt.compare.read_text());diff=[]
        for i,(a,b) in enumerate(zip(old['records'],result['records'])):
            if any(a.get(k)!=b.get(k) for k in ['test','line','format','exit','profile_sha256','stderr_sha256']):diff.append(i)
        assert len(old['records'])==len(result['records']), 'matrix changed'
        print('candidate differing rows:',diff)
        if diff:raise SystemExit(1)
    print(json.dumps({k:result[k] for k in ['tests_scanned','original_commands','format_variants','runs_per_pass','two_pass_equal']},indent=2))
    if differences:raise SystemExit(1)
if __name__=='__main__':main()
