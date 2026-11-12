"""Replay only pre-disclosed telemetry, keep historical labels immutable."""
import collections
import datetime
import json
import re
from pathlib import Path
from run_scoped import WORK, sha
from registration_address_check import BASE,dump
from registration_telemetry import qualify,combine
from pack_static_evidence import tables

OUT=BASE/"registration-checks/batch3"


def main():
    disclosure=json.loads((OUT/"telemetry-disclosure.json").read_text())
    listed={}
    for name in disclosure["parts"]+["telemetry-extra-before.json"]:
        for row in json.loads((OUT/name).read_text()):
            p=Path(row["path"]);p=p if p.is_absolute() else WORK/p
            assert p.is_relative_to(WORK)
            listed[str(p)]=row["sha256"]
    def read(path):
        path=Path(path)
        assert str(path) in listed,("not_predisclosed",str(path))
        assert sha(path)==listed[str(path)],str(path)
        return path.read_text()
    matrix=WORK/disclosure["matrix_metadata"]
    assert sha(matrix)==disclosure["matrix_sha256"]
    original=json.loads(matrix.read_text())
    folders=[Path(x) for x in disclosure["runs"]]
    folders += [WORK/"temp/frequency-disambiguation/runs"/x for x in ("single","four")]
    results={};raw_parts=[]
    for folder in folders:
        streams=collections.defaultdict(list);times=[];parse_errors=[]
        for path in sorted(folder.glob("telemetry/*.txt")):
            text=read(path);lines=text.splitlines()
            try:t=datetime.datetime.fromisoformat(lines[0].replace(",","." )).timestamp()
            except (ValueError,IndexError):parse_errors.append(str(path));continue
            times.append(t)
            for line in lines[1:]:
                if not line.startswith("/sys/"):continue
                parts=line.split()
                if len(parts)!=2:continue
                file,value=parts;kind=None
                if file.endswith("/temp"):kind="temperature"
                elif file.endswith("/in0_lcrit_alarm"):kind="alarm"
                else:
                    for suffix,name in (("scaling_cur_freq","scaling_cur_freq"),("cpuinfo_cur_freq","cpuinfo_cur_freq"),
                                        ("scaling_governor","governor"),("scaling_min_freq","min_freq"),("scaling_max_freq","max_freq")):
                        if file.endswith("/"+suffix):kind=name;break
                if kind is None:continue
                try:v=value if kind=="governor" else float(value)*(0.001 if kind=="temperature" else 1000 if "freq" in kind else 1)
                except ValueError:v=value
                streams[kind+":"+file].append(dict(time=t,value=v,source=str(path),clock="wall_clock_not_monotonic"))
        for stream in streams.values():stream.sort(key=lambda r:r["time"])
        baseline={}
        before=folder/"environment.before"
        if str(before) in listed:
            for line in read(before).splitlines():
                p=line.split()
                if len(p)!=2 or not p[0].startswith("/sys/"):continue
                for suffix,kind in (("scaling_governor","governor"),("scaling_min_freq","min_freq"),("scaling_max_freq","max_freq")):
                    if p[0].endswith("/"+suffix):
                        try:baseline[kind+":"+p[0]]=p[1] if kind=="governor" else float(p[1])*1000
                        except ValueError:pass
        required=list(streams)
        for k in ("scaling_cur_freq","cpuinfo_cur_freq","temperature","alarm","governor","min_freq","max_freq"):
            if not any(x.startswith(k+":") for x in streams):required.append(k)
        run=dict(fixed_hz=1500000000,streams=streams,required_streams=required,policy_before=baseline)
        # Do not invent CLOCK_MONOTONIC windows or kmsg state from wall-clock dates.
        q=qualify(run)
        if parse_errors:q=combine(q,dict(abnormal=[],unknown=["legacy_timestamp_parse_failed"],warnings=[]))
        q.update(source=str(folder),telemetry_records=len(times),wall_clock_only=True,
                 known_temperature_max=max((r["value"] for k,rs in streams.items() if k.startswith("temperature:") for r in rs if isinstance(r["value"],(int,float))),default=None),
                 observed_scaling_hz=sorted({r["value"] for k,rs in streams.items() if k.startswith("scaling_cur_freq:") for r in rs if isinstance(r["value"],(int,float))}),
                 parse_errors=parse_errors)
        results[str(folder)]=q
    groups=[]
    for g in original["groups"]:
        q=combine(*(results[p] for p in g["sources"]))
        groups.append(dict(group=g["group"],sources=g["sources"],old=g["eligibility"],new=q["status"],
                           changed=g["eligibility"]!={"observed_no_anomaly":"clean","abnormal":"abnormal","unknown":"unknown"}[q["status"]],
                           abnormal=q["abnormal"],unknown=q["unknown"],warnings=q["warnings"]))
    parts=tables(OUT,"telemetry-run-replay",["record"],([r] for r in results.values()))
    parts+=tables(OUT,"telemetry-group-differences",["record"],([r] for r in groups))
    counts=collections.Counter(r["new"] for r in groups);cross=collections.Counter(r["old"]+" -> "+r["new"] for r in groups)
    assert len(groups)==70 and len(folders)==108
    assert results[str(WORK/"temp/frequency-disambiguation/runs/four")]["status"]=="abnormal"
    dump(OUT/"telemetry-replay-summary.json",dict(groups=70,physical_formal_runs=106,diagnostics=2,new=counts,transitions=cross,
         changed=sum(r["changed"] for r in groups),parts=parts,diagnostic_results={x:results[str(WORK/"temp/frequency-disambiguation/runs"/x)] for x in ("single","four")},
         old_labels_unchanged=sha(matrix)==disclosure["matrix_sha256"],formal_profiles_opened=False,
         missing="Legacy inputs have no four monotonic endpoints, continuous boot kmsg, cpuinfo readings or prescribed before/after 4x30s calibration. No other RUN fills missing data. Wall timestamps retained as wall timestamps.",
         data_sha_verified=len(listed)))
    print(json.dumps(dict(new=counts,transitions=cross)))


if __name__=="__main__":main()
