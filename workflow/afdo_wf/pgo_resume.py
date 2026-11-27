"""Continue PGO from independently verified prior receipts."""
from pathlib import Path

from .common import json_load, require, sha256
from .pgo import ZERO_DSO_POLICY


def after_collect(job, store, workdir):
    binding = job['pgo_resume_after_collect']
    require(isinstance(binding,dict) and set(binding)=={'job','receipt_sha256'}, 'invalid S3 continuation binding')
    archive = Path(binding['job']).resolve()
    require(archive.is_relative_to(Path(workdir).resolve()), 'S3 job is outside workdir')
    receipt = store.verify('collect')
    require(sha256(store.path('collect'))==binding['receipt_sha256'],
            'S3 continuation receipt SHA mismatch','identity',3)
    require(receipt['inputs'].get(str(archive))==sha256(archive),
            'prior job is missing from the S3 receipt inputs','identity',3)
    baseline = json_load(archive)
    require(baseline.get('method')=='pgo' and not baseline.get('pgo_resume_after_collect'),
            'S3 continuation must bind the original PGO job')
    host = dict(baseline.get('host',{}))
    host.pop('recovery_io_pressure_waived',None)
    host['shared_host_recovery'] = True
    baseline.update(host=host,pgo_collision_policy=ZERO_DSO_POLICY)
    proposed = dict(job)
    del proposed['pgo_resume_after_collect']
    require(baseline==proposed, 'S3 continuation changed a locked input or host rule','identity',3)


def after_rebuild(job, store, workdir):
    binding = job['pgo_resume_after_rebuild']
    require(isinstance(binding, dict) and set(binding) == {'job', 'receipt_sha256'}, 'invalid S5 continuation binding')
    archive = Path(binding['job']).resolve()
    require(archive.is_relative_to(Path(workdir).resolve()), 'S5 job is outside workdir')
    receipt = store.verify('rebuild')
    require(sha256(store.path('rebuild')) == binding['receipt_sha256'], 'S5 continuation receipt SHA mismatch', 'identity', 3)
    require(receipt['inputs'].get(str(archive)) == sha256(archive), 'original job is missing from the S5 receipt inputs', 'identity', 3)
    original = json_load(archive)
    require(original.get('method') == 'pgo' and not original.get('pgo_resume_after_rebuild'), 'S5 continuation needs the original PGO job')
    approved = {name: job.get(name) for name in ('order_seed', 'bootstrap_seed')}
    require(all(type(seed) is int and seed >= 0 for seed in approved.values()), 'invalid pre-registered seeds')
    proposed = dict(job)
    del proposed['pgo_resume_after_rebuild']
    require({**original, **approved} == proposed, 'S5 continuation changed a locked input or host rule', 'identity', 3)
    require(receipt['details']['consumption']['passed'], 'S5 consumption gate was not completed')
