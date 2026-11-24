"""Board-specific layout and collection settings for the live runner."""
from dataclasses import dataclass
from pathlib import Path
import tomllib

from .common import require


@dataclass(frozen=True)
class Platform:
    model: str
    arch: str
    isas: list[str]
    runtime_lib: str
    debug_root: str
    gcc_support: str
    perf: str
    perf_lib: str
    cpu: int
    observer_cpu: int
    collect: str
    telemetry: dict[str, list[str]]
    prepare_only: bool
    report_label: str

    def check_identity(self, identity):
        require(
            identity.get('arch') == self.arch and identity.get('model', '').startswith(self.model),
            'board does not match its platform configuration', 'identity', 3,
        )

    def sampling_period(self, package):
        sampling = package['collect']
        selected = sampling.get(self.collect, sampling)
        require('period' in selected, 'live collection requires a fixed period')
        return selected['period']

    def runtime_environment(self, variant, base):
        return f'{variant}/{self.runtime_lib}:{base}/{self.perf_lib}'


def profile_path(name):
    directory = Path(__file__).resolve().parents[1] / 'platforms'
    supported = {path.stem: path for path in directory.glob('*.toml')}
    require(name in supported, f'unknown board platform: {name}')
    return supported[name]


def load(name):
    with profile_path(name).open('rb') as source:
        return Platform(**tomllib.load(source))
