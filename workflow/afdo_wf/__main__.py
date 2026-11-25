import sys

from . import MIN_PYTHON


def run():
    if sys.version_info[:2] < MIN_PYTHON:
        detected = '.'.join(map(str, sys.version_info[:3]))
        print(f'environment [4] afdo_wf requires Python 3.11 or newer (found {detected}).',
              file=sys.stderr)
        return 4

    from .cli import main
    return main()


raise SystemExit(run())
