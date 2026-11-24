"""Apply the evidence-backed AArch64 support path only during this job's audit."""
from dataclasses import replace
import json
from pathlib import Path

import launch
from afdo_wf.common import require, save
from afdo_wf.live import Experiment

original_rebuild = Experiment.rebuild


def rebuild(self, out, store):
    platform = self.platform
    require(self.job['experiment'] == 'm2a-ffmpeg-rpi5-aarch64-01'
            and self.platform_name == 'rpi5-aarch64'
            and platform.gcc_support == 'usr/lib/gcc',
            'S5 recovery adapter is limited to the locked M2a job and original path')
    self.platform = replace(platform, gcc_support='usr/lib64/gcc')
    try:
        save(out/'gcc-support-path.json', dict(previous=platform.gcc_support, audited=self.platform.gcc_support,
                                             platform_config_unchanged=True, classifier_unchanged=True,
                                             source_fixture=str(launch.OUT/'gcc-support-path-regression.json')))
        return original_rebuild(self, out, store)
    finally:
        self.platform = platform


if __name__ == '__main__':
    log = launch.OUT/'wait-budget.jsonl'
    if log.is_file():
        launch.spent = json.loads(log.read_text().splitlines()[-1])['total_wait_seconds']
    Experiment.rebuild = rebuild
    raise SystemExit(launch.main())
