"""Board contracts. Transport is injected; this phase never opens an SDB connection."""
from contextlib import contextmanager
import fnmatch
import signal
from pathlib import PurePosixPath
from .common import StopRequested,require
from .receipts import Cleanup

def check_maps(text,manifest,must_load,deploy_patterns,observed_sha):
    """manifest maps every deploy-set SONAME/alias to exact real path and SHA."""
    mapped=set();seen=set()
    for line in text.splitlines():
        fields=line.split(None,5)
        if len(fields)<6 or not fields[5].startswith('/'):continue
        path=fields[5];base=PurePosixPath(path).name
        # Include unexpected files matching a deploy glob, not just known targets.
        belongs=base in manifest or any(fnmatch.fnmatch(base,PurePosixPath(g).name) for g in deploy_patterns)
        if not belongs:continue
        require(not path.endswith(' (deleted)'),'deleted mapped library','identity',3)
        require(base in manifest,'unlisted deploy-set DSO: '+path,'identity',3)
        expected=manifest[base]
        require(path==expected['board_path'] and observed_sha.get(path)==expected['sha256'],'loaded DSO identity mismatch: '+path,'identity',3)
        mapped.add(base);seen.add(expected['id'])
    require(set(must_load)<=seen,'must-load DSO absent','identity',3)
    return sorted(mapped)

def oracle_check(expected,actual):
    require(actual.get('status')=='ok' and actual.get('eos') is True,'decoder did not complete','correctness',3)
    for k in ['frames','bytes','digest','caps','threads']:
        require(actual.get(k)==expected.get(k),'oracle mismatch: '+k,'correctness',3)
    require(actual['frames']>0 and actual['bytes']>0,'empty oracle','correctness',3)
    return True

@contextmanager
def session(transport,expected_identity,journal):
    """Save state before changes; transport errors persist cleanup_pending.
    Each mutating transport call is single-shot; retries belong only to verified
    read-only transport operations. No global process kills are exposed.
    """
    actual=transport.identity();require(actual==expected_identity,'board identity mismatch','identity',3)
    cleanup=Cleanup(journal,expected_identity)
    errors=cleanup.restore(actual,transport.undo)
    require(not errors,'pending cleanup failed: '+str(errors),'environment')
    old={}
    def stop(signum,frame):raise StopRequested(signum)
    try:
        for s in [signal.SIGTERM,signal.SIGINT]:old[s]=signal.signal(s,stop)
        root=transport.root_state()
        if not root:
            cleanup.register(dict(kind='root',previous=False));transport.root(True)
        governors=transport.governors()
        for policy,value in governors.items():
            cleanup.register(dict(kind='governor',policy=policy,previous=value));transport.governor(policy,'performance')
        yield cleanup
    finally:
        try:
            cleanup.restore(transport.identity(),transport.undo)
        finally:
            for s,h in old.items():signal.signal(s,h)


def observer_cadence(directory):
    from pathlib import Path
    from decimal import Decimal, InvalidOperation
    from .common import save
    root=Path(directory);path=root/'samples.tsv'
    require(path.is_file(),'observer cadence evidence missing','identity',3)
    try:
        rows=[line.split() for line in path.read_text().splitlines()]
        require(rows and all(len(x)==2 for x in rows),'invalid observer cadence evidence','identity',3)
        times=[Decimal(x[1]) for x in rows]
        require(all(x.is_finite() for x in times),'nonfinite observer timestamp','identity',3)
        gaps=[b-a for a,b in zip(times,times[1:])]
    except InvalidOperation:
        require(False,'invalid observer timestamp','identity',3)
    evidence=dict(samples=len(rows),max_gap_seconds=float(max(gaps,default=Decimal(0))),
                  intervals_over_limit=[dict(after_sample=rows[i][0],seconds=float(g)) for i,g in enumerate(gaps) if g>Decimal('0.5')])
    save(root/'cadence-check.json',evidence)
    require(all(Decimal(0)<g<=Decimal('0.5') for g in gaps),'observer cadence exceeds 0.5 seconds or is nonmonotonic','identity',3)
    return evidence


def decoder_maps(directory, manifest, must_load, deploy_patterns, rule, input_path):
    """Unique declared workload process, exact argv, complete procfs snapshots."""
    from pathlib import Path
    from .common import save
    root=Path(directory); observer_cadence(root)
    candidates={}; invalid=[]; observations=[]
    expected=[arg.replace('{input}',input_path) for arg in rule['argv']]
    for snapshot in sorted(root.glob('*-*')):
        if not snapshot.is_dir():continue
        cp=snapshot/'cmdline.txt'
        if not cp.exists():continue
        argv=[x.decode('utf-8',errors='strict') for x in cp.read_bytes().split(b'\0') if x]
        if not argv or PurePosixPath(argv[0]).name!=rule['executable']:continue
        require(argv[1:]==expected,'decoder pipeline does not match declared round: '+str(snapshot),'identity',3)
        ident=(snapshot/'identity.txt').read_text().split()
        require(len(ident)==6,'decoder identity record incomplete','identity',3)
        key=(ident[0],ident[4]);candidates.setdefault(key,[]).append(str(snapshot))
        if not (snapshot/'complete').exists() or (snapshot/'complete').read_text().strip()!='1':
            invalid.append(str(snapshot));continue
        text=(snapshot/'maps.txt').read_text()
        hashes={line.split(None,1)[1].strip():line.split()[0] for line in (snapshot/'mapped-sha256.txt').read_text().splitlines()}
        # Check any deployed DSO even during dynamic-loader startup. Only a
        # complete must-load set counts as a successful identity observation.
        mapped=check_maps(text,manifest,[],deploy_patterns,hashes)
        seen={manifest[name]['id'] for name in mapped}
        if set(must_load)<=seen:observations.append(dict(snapshot=str(snapshot),mapped=mapped))
    evidence=dict(candidates=[dict(pid=k[0],starttime=k[1],snapshots=v) for k,v in candidates.items()],incomplete_snapshots=invalid,observations=observations)
    save(root/'decoder-check.json',evidence)
    require(len(candidates)==1,'expected one decoder process; found '+str(len(candidates)),'identity',3)
    require(observations,'no decoder loaded-library evidence','identity',3)
    return len(observations)


def check_perf_buildids(text, artifacts, manifest):
    """Cross evidence only; never replaces decoder maps."""
    rows=[]
    for target,artifact in artifacts.items():
        paths={v['board_path'] for v in manifest.values() if v['id']==target}
        found=[line.split(None,1) for line in text.splitlines() if len(line.split(None,1))==2 and line.split(None,1)[1] in paths]
        require(found and all(x[0]==artifact['build_id'] for x in found),'perf build-id mismatch or missing: '+target,'identity',3)
        rows.append(dict(target=target,expected=artifact['build_id'],records=found))
    return rows
