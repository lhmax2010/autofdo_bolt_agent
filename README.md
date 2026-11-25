# Tizen profiling workflow

This workflow builds and profiles FFmpeg on Raspberry Pi 4 (armv7l Thumb) and
Raspberry Pi 5 (AArch64), audits the profile-consuming build, and produces
paired measurement reports. The [workflow skill](skills/afdo-workflow/SKILL.md)
is the operator guide for drafting, running, restoring, and interpreting an
experiment. The CLI implements the stage gates.

## Start from a fresh clone

Use Git and Python 3.11 or later on Linux. Set `REPOSITORY` to the remote
provided by the maintainer.

```bash
git clone --single-branch --no-tags --branch release "$REPOSITORY" afdo-workflow
cd afdo-workflow
```

Follow the skill's Python setup, then use `"$PY" -m afdo_wf doctor` before
drafting. Clone the media branch in a separate directory as shown in the
skill. The [RPi5 draft and dry-run example](examples/ffmpeg-rpi5-draft/README.md)
shows what to expect when all three media hashes match.

A live run requires an authorized Tizen board, SDB, matching board perf tools,
GBS and its Tizen build environment, the package sources and dependencies,
matching host profile tools, and the exact media clips supplied separately by
the maintainer. See the [workflow reference](workflow/README.md), including
[how to build the host profile tools](workflow/README.md#build-the-host-profile-tools).

## Read the sample reports

| Experiment | Platform | Report |
| --- | --- | --- |
| M1 attempt-11 | Raspberry Pi 4, armv7l Thumb | [Markdown](examples/m1-rpi4-thumb/report.md) / [JSON](examples/m1-rpi4-thumb/report.json) |
| M2a | Raspberry Pi 5, AArch64 | [Markdown](examples/m2a-rpi5-aarch64/report.md) / [JSON](examples/m2a-rpi5-aarch64/report.json) |

The examples contain historical results rounded as indicated in Markdown.
Paths and internal evidence references are omitted. For `status` or resume,
use the job and original run directory on the host that owns the experiment.
The media branch supplies the video files. Get the tools, frozen package
archives and original experiment artifacts separately.

## Check the checkout

```bash
export TMPDIR="$WORKDIR/.scratch/tests"
mkdir -p "$TMPDIR"
"$PY" -m unittest discover -s workflow/tests -v
```

The suite uses Linux core utilities and Bash. Three archive replays are
optional and report explicit skips unless their original evidence is supplied.
On the host with the evidence, set `AFDO_WF_ATTEMPT05_MAPS` to the snapshot
directory, `AFDO_WF_ATTEMPT06_RUN` to the formal run directory, or
`AFDO_WF_ATTEMPT07_RUN` to the compiler diagnostic run directory to enable the
corresponding replay. The standalone replay scripts likewise take original
evidence and a new output path as arguments. These checks run without SDB or
GBS.
