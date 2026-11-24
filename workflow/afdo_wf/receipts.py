"""Durable receipts with content dependencies, invalidation and cleanup journal."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import time
from uuid import uuid4
from .common import atomic_write, require, save, json_load, sha256
from .exits import failure_record
from .stages import DAG

class Store:
    def __init__(self, directory, *, create=True):
        self.directory = Path(directory)
        if create:
            self.directory.mkdir(parents=True, exist_ok=True)

    def path(self, stage):
        require(stage in DAG, 'unknown stage')
        return self.directory / (stage + '.json')

    def redo_bindings(self):
        """Newest committed invalidation for each stage. Partial archives are inert."""
        result = {}
        for path in sorted((self.directory / 'redo').glob('*/receipt.json')):
            record = json_load(path)
            digest = sha256(path)
            for stage in record['stages']:
                result[stage] = dict(receipt=str(path.resolve()), sha256=digest, reason=record['reason'])
        return result

    @staticmethod
    def invalidated(receipt, binding):
        return (receipt is not None and receipt['status'] == 'invalidated'
                or binding is not None and (receipt is None or receipt.get('redo') != binding))

    def verify(self, stage, stack=(), *, bindings=None):
        require(stage not in stack, 'receipt cycle')
        if bindings is None:
            bindings = self.redo_bindings()
        require(self.path(stage).is_file(), 'missing stage receipt: ' + stage)
        r = json_load(self.path(stage))
        require(not r.get('redo') or stage in bindings, 'redo receipt missing')
        require(r['stage'] == stage and r['status'] == 'complete'
                and not self.invalidated(r, bindings.get(stage)), 'stage not complete')
        require(set(r['upstream']) == set(DAG[stage]), 'receipt dependencies incomplete')
        for name, expected in r['upstream'].items():
            self.verify(name, stack + (stage,), bindings=bindings)
            require(sha256(self.path(name)) == expected, 'upstream changed')
        for path, digest in {**r['inputs'], **r['outputs']}.items():
            require(Path(path).is_file() and sha256(path) == digest, 'content changed: ' + path)
        return r

    def complete(self, stage, inputs, outputs, details=None, *, gbs_waits=None):
        bindings = self.redo_bindings()
        upstream = {}
        for name in DAG[stage]:
            self.verify(name, bindings=bindings)
            upstream[name] = sha256(self.path(name))
        path = self.path(stage)
        old = json_load(path) if path.exists() else None
        binding = bindings.get(stage)
        require(old is None or self.invalidated(old, binding), 'receipt exists; use redo')
        # The pre-M5 invalidated format retained the original under history/.
        require(old is None or binding is not None or
                any((self.directory / 'history' / stage).glob('*.json')),
                'legacy invalidation has no archived receipt')
        r = dict(stage=stage, status='complete', time=datetime.now(timezone.utc).isoformat(),
                 inputs={str(Path(p).resolve()): sha256(p) for p in inputs},
                 outputs={str(Path(p).resolve()): sha256(p) for p in outputs},
                 upstream=upstream, details=details or {})
        if gbs_waits:
            r['gbs_waits'] = gbs_waits
        if binding:
            r['redo'] = binding
        save(path, r)
        return r

    def failure_paths(self, stage):
        exact = self.directory / (stage + '.failure.json')
        paths = list(self.directory.glob(stage + '.failure-*.json'))
        if exact.is_file():
            paths.append(exact)
        return sorted(paths, key=lambda p: (p.stat().st_mtime_ns, p.name))

    def redo(self, stage, reason='operator requested redo'):
        self.path(stage)
        require(stage != 'restore' and isinstance(reason, str) and reason.strip(),
                'redo requires a workflow stage and reason')
        affected = {stage}
        for name, dependencies in DAG.items():
            if affected.intersection(dependencies):
                affected.add(name)
        now = datetime.now(timezone.utc)
        archive = self.directory / 'redo' / (now.strftime('%Y%m%dT%H%M%S.%fZ') + '-' + uuid4().hex)
        archive.mkdir(parents=True, exist_ok=False)
        stages = {}
        for name in DAG:
            if name not in affected:
                continue
            active = self.path(name)
            originals = ([active] if active.is_file() else []) + self.failure_paths(name)
            saved = []
            for original in originals:
                copy = archive / original.name
                atomic_write(copy, original.read_bytes())
                digest = sha256(copy)
                require(sha256(original) == digest, 'receipt changed during redo: ' + str(original))
                saved.append(dict(original=str(original.resolve()), archive=copy.name, sha256=digest))
            stages[name] = dict(status='invalidated', archived=saved)
        # Publish only after every original is durably archived.
        save(archive / 'receipt.json', dict(schema_version=1, status='invalidated',
             stage=stage, reason=reason.strip(), time=now.isoformat(), stages=stages))
        return affected

    def failed(self, stage, error, *, gbs_waits=None):
        record = dict(stage=stage, **failure_record(error))
        if gbs_waits:
            record['gbs_waits'] = gbs_waits
        binding = self.redo_bindings().get(stage)
        if binding:
            record['redo'] = binding
        save(self.directory / (stage + '.failure-' + str(time.time_ns()) + '.json'), record)


class Cleanup:
    """Persist intended undo BEFORE mutation. A dropped connection leaves pending work."""
    def __init__(self,path,identity):
        self.path=Path(path);self.identity=identity
        self.data=json_load(path) if self.path.exists() else dict(identity=identity,cleanup_pending=[])
        require(self.data['identity']==identity,'board changed before restore','identity',3)
    def register(self,action):
        require(action.get('kind') in ['root','governor','process','run','host_artifact','empty_directory'],'unknown cleanup action')
        self.data['cleanup_pending'].append(action);save(self.path,self.data)
    def reconcile_parent(self,receipt):
        r=json_load(receipt)
        if r.get('status')!='verified' or not r.get('deleted'):return []
        parent=r['remote_dir'].rstrip('/')+'/'
        closed=[]
        for action in list(self.data['cleanup_pending']):
            if action.get('kind')!='run':continue
            remote=action.get('remote')
            if not remote and Path(action['receipt']).exists():remote=json_load(action['receipt']).get('remote_dir')
            if not remote or not remote.startswith(parent):continue
            prefix=remote[len(parent):].rstrip('/')+'/'
            covered={k:v for k,v in r['files'].items() if k.startswith(prefix)}
            for rel,digest in covered.items():require(sha256(Path(r['local_root'])/rel)==digest,'parent evidence changed')
            closed.append(dict(action=action,covered_files=len(covered)))
            self.data['cleanup_pending'].remove(action)
        if closed:
            evidence=self.path.parent/'cleanup-resolutions'/(sha256(receipt)+'.json')
            save(evidence,dict(parent_receipt=str(receipt),parent_sha256=sha256(receipt),closed=closed))
            save(self.path,self.data)
        return closed
    def restore(self,actual_identity,undo):
        require(actual_identity==self.identity,'restore identity mismatch','identity',3)
        failures=[]
        ordered=sorted(reversed(self.data['cleanup_pending']),key=lambda a:{'process':0,'run':2,'host_artifact':1,'empty_directory':3,'governor':4,'root':5}[a['kind']])
        for action in ordered:
            if action not in self.data['cleanup_pending']:continue
            try:
                undo(action)
                if action in self.data['cleanup_pending']:self.data['cleanup_pending'].remove(action)
                save(self.path,self.data)
                if action['kind']=='run' and Path(action['receipt']).exists():self.reconcile_parent(action['receipt'])
            except Exception as e:failures.append((action,str(e)))
        return [error for action,error in failures if action in self.data['cleanup_pending']]

def verified_pull(receipt,local_root,manifest,remote_dir,verified_empty=False):
    root=Path(local_root).resolve()
    require(remote_dir.startswith('/opt/afdo_agent/work/') and '..' not in Path(remote_dir).parts,'unsafe remote delete')
    require(manifest or verified_empty,'empty pull manifest')
    for rel,digest in manifest.items():
        p=(root/rel).resolve();require(p.is_relative_to(root) and p.is_file() and sha256(p)==digest,'pull verification failed: '+rel)
    save(receipt,dict(status='verified',remote_dir=remote_dir,local_root=str(root),files=manifest))

def delete_pulled(receipt,delete):
    r=json_load(receipt);require(r['status']=='verified','unverified pull')
    require(r['remote_dir'].startswith('/opt/afdo_agent/work/') and '..' not in Path(r['remote_dir']).parts,'unsafe remote deletion receipt')
    root=Path(r['local_root']).resolve()
    for rel,digest in r['files'].items():
        path=(root/rel).resolve()
        require(path.is_relative_to(root) and sha256(path)==digest,'pull changed before delete')
    # Callback must be idempotent for this exact path, never a wildcard.
    delete(r['remote_dir'])
    r['deleted']=True;save(receipt,r)
