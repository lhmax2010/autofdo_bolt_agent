"""Stage scheduler shared by live jobs and synthetic recovery tests."""
from pathlib import Path
import time
from .common import require,save,sha256,json_load
from .receipts import Store,DAG

def reusable(store, stage, inputs):
    path = store.path(stage)
    record = json_load(path) if path.is_file() else None
    bindings = store.redo_bindings()
    if record is None or store.invalidated(record, bindings.get(stage)):
        return False
    record = store.verify(stage, bindings=bindings)
    require(all(record['inputs'].get(str(Path(p).resolve())) == sha256(p) for p in inputs),
            'resume inputs changed; redo required')
    return True


def execute(stages,handlers,directory,receipt_directory,inputs,notify=None,*,first_output=None):
    store=Store(receipt_directory);directory=Path(directory)
    result=[]
    for stage in stages:
        if reusable(store, stage, inputs):
            result.append(dict(stage=stage,action='reused'))
            if notify:notify(stage,'reused')
            continue
        for dep in DAG[stage]:store.verify(dep)
        original = Path(first_output) / stage if first_output is not None else None
        if original is not None and not original.exists():
            out = original
        else:
            attempts = directory / stage
            attempts.mkdir(parents=True, exist_ok=True)
            out = attempts / ('%03d' % (len(list(attempts.iterdir())) + 1))
        out.mkdir(parents=True, exist_ok=False)
        if notify:notify(stage,'running')
        try:
            detail=handlers[stage](out,store)
            save(out/'result.json',detail)
            # Large immutable artifacts are bound explicitly by a handler. Build roots
            # themselves are mutable implementation state, never receipt outputs.
            outputs=[p for p in out.rglob('*') if p.is_file()]
            outputs+=list(map(Path,detail.get('bound_files',[])))
            store.complete(stage,inputs,outputs,detail)
            result.append(dict(stage=stage,action='completed'))
            if notify:notify(stage,'completed')
        except BaseException as e:
            store.failed(stage,e);save(out/'failure.json',dict(error=repr(e),time=time.time()))
            if notify:notify(stage,'failed')
            raise
    return result
