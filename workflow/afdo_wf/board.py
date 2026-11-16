"""Board contracts. Transport is injected; this phase never opens an SDB connection."""
from contextlib import contextmanager
import fnmatch
import signal
from pathlib import PurePosixPath
from .common import require
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
    def stop(signum,frame):raise InterruptedError('signal '+str(signum))
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
