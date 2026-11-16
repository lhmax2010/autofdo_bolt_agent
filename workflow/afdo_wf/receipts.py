"""Durable receipts with content dependencies, invalidation and cleanup journal."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
from .common import require, save, json_load, sha256, canonical

DAG={'preflight':[], 'build':['preflight'], 'deploy':['build'], 'collect':['deploy'],
     'convert':['collect'], 'rebuild':['convert','build'], 'measure':['rebuild','deploy'],
     'report':['measure','convert'], 'restore':[]}

class Store:
    def __init__(self, directory):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
    def path(self,stage):
        require(stage in DAG,'unknown stage');return self.directory/(stage+'.json')
    def verify(self,stage,stack=()):
        require(stage not in stack,'receipt cycle')
        r=json_load(self.path(stage));require(r['stage']==stage and r['status']=='complete','stage not complete')
        require(set(r['upstream'])==set(DAG[stage]),'receipt dependencies incomplete')
        for name,expected in r['upstream'].items():
            self.verify(name,stack+(stage,));require(sha256(self.path(name))==expected,'upstream changed')
        for path,digest in {**r['inputs'],**r['outputs']}.items():
            require(Path(path).is_file() and sha256(path)==digest,'content changed: '+path)
        return r
    def complete(self,stage,inputs,outputs,details=None):
        upstream={}
        for name in DAG[stage]:self.verify(name);upstream[name]=sha256(self.path(name))
        require(not self.path(stage).exists(),'receipt exists; use redo')
        r=dict(stage=stage,status='complete',time=datetime.now(timezone.utc).isoformat(),
               inputs={str(Path(p).resolve()):sha256(p) for p in inputs},
               outputs={str(Path(p).resolve()):sha256(p) for p in outputs},upstream=upstream,details=details or {})
        save(self.path(stage),r);return r
    def redo(self,stage):
        affected={stage}
        while True:
            new=affected|{k for k,v in DAG.items() if set(v)&affected}
            if new==affected:break
            affected=new
        for s in sorted(affected):
            p=self.path(s)
            if p.exists():
                old=json_load(p);digest=sha256(p)
                archive=self.directory/'history'/s/(digest+'.json')
                if not archive.exists():save(archive,old)
                old['status']='invalidated';save(p,old)
        return affected
    def restart(self,stage):
        """Archive invalidated receipt then remove only its active pointer."""
        p=self.path(stage)
        if p.exists():
            require(json_load(p)['status']=='invalidated','redo required')
            p.unlink()
    def failed(self,stage,error):
        save(self.directory/(stage+'.failure.json'),dict(stage=stage,status='failed',reason=getattr(error,'reason','error'),error=str(error)))

class Cleanup:
    """Persist intended undo BEFORE mutation. A dropped connection leaves pending work."""
    def __init__(self,path,identity):
        self.path=Path(path);self.identity=identity
        self.data=json_load(path) if self.path.exists() else dict(identity=identity,cleanup_pending=[])
        require(self.data['identity']==identity,'board changed before restore','identity',3)
    def register(self,action):
        require(action.get('kind') in ['root','governor','process','run'],'unknown cleanup action')
        self.data['cleanup_pending'].append(action);save(self.path,self.data)
    def restore(self,actual_identity,undo):
        require(actual_identity==self.identity,'restore identity mismatch','identity',3)
        errors=[]
        ordered=sorted(reversed(self.data['cleanup_pending']),key=lambda a:{'process':0,'run':1,'governor':2,'root':3}[a['kind']])
        for action in ordered:
            try:
                undo(action)
                self.data['cleanup_pending'].remove(action)
                save(self.path,self.data)
            except Exception as e: errors.append(str(e))
        return errors

def verified_pull(receipt,local_root,manifest,remote_dir):
    root=Path(local_root).resolve()
    require(remote_dir.startswith('/opt/afdo_agent/work/') and '..' not in Path(remote_dir).parts,'unsafe remote delete')
    require(manifest,'empty pull manifest')
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
