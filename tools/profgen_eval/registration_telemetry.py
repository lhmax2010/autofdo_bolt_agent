"""v1.8 5.9.5 / Q.5 #14 offline telemetry policy. No board I/O."""
import math
import statistics
from pathlib import PurePosixPath


def finite(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)


def result(abnormal=(), unknown=(), warnings=()):
    a=sorted(set(abnormal));u=sorted(set(unknown));w=sorted(set(warnings))
    return dict(status="abnormal" if a else "unknown" if u else "observed_no_anomaly",
                abnormal=a,unknown=u,warnings=w,firmware_throttling="unknown")


def combine(*parts):
    return result(*(sum((p[k] for p in parts),[]) for k in ("abnormal","unknown","warnings")))


def stream_check(name, rows, window, predicate, valid):
    a=[];u=[];w=[];times=[]
    if window is None:
        u.append(name+":missing_monotonic_window")
    elif len(window)!=2 or not all(finite(t) for t in window) or window[0]>window[1]:
        return result(unknown=[name+":invalid_window"])
    for row in rows:
        t=row.get("time");value=row.get("value")
        if not finite(t): u.append(name+":invalid_timestamp");continue
        if window is not None and not window[0]<=t<=window[1]:continue
        times.append(t)
        if row.get("error") or not valid(value):u.append(name+":invalid_reading")
        elif not predicate(value):a.append(name+":threshold_deviation")
    if not times:u.append(name+":missing")
    if any(b<=a for a,b in zip(times,times[1:])):u.append(name+":nonmonotonic_stream")
    gaps=[b-a for a,b in zip(times,times[1:])]
    if sum(x>1.5 for x in gaps)>2 or any(x>3 for x in gaps):u.append(name+":excessive_gap")
    elif any(x>1.5 for x in gaps):w.append(name+":gap")
    if window is not None and times and (times[0]-window[0]>1.5 or window[1]-times[-1]>1.5):u.append(name+":incomplete_window")
    return result(a,u,w)


class Recorder:
    """Offline single-reader saved-sequence state; never opens /dev/kmsg."""
    def __init__(self,boot,path):
        p=PurePosixPath(path)
        if not p.is_absolute() or ".." in p.parts or not p.is_relative_to("/opt/afdo_agent") or str(p)=="/opt/afdo_agent":raise ValueError("recorder_output_path")
        self.boot=boot;self.records=[];self.errors=[];self.last=-1;self.first=None
    def save(self,record,success=True):
        if not success:self.errors.append("save_failed");return
        seq=record["seq"]
        if self.first is None:self.first=seq
        elif seq!=self.last+1:self.errors.append("sequence_gap")
        self.records.append(record.copy());self.last=seq
    def endpoint(self,boot,before,after,pending=(),error=None):
        if boot!=self.boot:self.errors.append("recorder_not_restarted")
        if error:self.errors.append(error)
        for row in pending:self.save(row)
        # EAGAIN retains the last successfully saved sequence.
        return dict(boot=boot,seq=self.last,before=before,after=after,error=error)
    def admit(self,first_run_time,authorization=None):
        if self.first==0 and not self.errors:return True
        return bool(self.first is not None and self.first!=0 and not self.errors and authorization and
                    authorization.get("boot")==self.boot and authorization.get("accept_unknown") is True and
                    finite(authorization.get("time")) and authorization["time"]<first_run_time)
    def snapshot(self,cutoff):
        return dict(boot=self.boot,first=self.first,last=self.last,records=self.records,errors=self.errors,cutoff=cutoff)


def log_check(log, endpoints, monitor):
    if not log or not endpoints or monitor is None:return result(unknown=["kmsg:missing"])
    a=[];u=[]
    if not finite(log.get("cutoff")):u.append("kmsg:missing_evaluation_cutoff")
    records=log.get("records",[]);seqs=[r["seq"] for r in records]
    if log.get("first")!=0 or not seqs or seqs[0]!=0:u.append("kmsg:boot_history_incomplete")
    if any(b!=a+1 for a,b in zip(seqs,seqs[1:])):u.append("kmsg:sequence_gap")
    u.extend("kmsg:"+e for e in log.get("errors",[]))
    if any("Failed to get throttled" in r["text"] for r in records):u.append("kmsg:query_failure_sticky")
    s0,s1=endpoints
    if s0.get("boot")!=s1.get("boot") or s0.get("boot")!=log.get("boot"):u.append("kmsg:boot_mismatch")
    for s in endpoints:
        if s.get("error"):u.append("kmsg:"+s["error"])
    if not all(finite(s.get(k)) for s in endpoints for k in ("before","after")):u.append("kmsg:invalid_endpoint_time")
    elif not (s0["before"]<=s0["after"]<monitor[0]<=monitor[1]<s1["before"]<=s1["after"]):u.append("kmsg:not_enclosing")
    if not all(isinstance(s.get("seq"),int) for s in endpoints):u.append("kmsg:invalid_endpoint_seq")
    else:
        b,e=s0["seq"],s1["seq"]
        if b>e or e>log.get("last",-1):u.append("kmsg:invalid_seq_range")
        window=[r for r in records if b<r["seq"]<=e]
        if len(window)!=e-b:u.append("kmsg:missing_window_records")
        # Sequence window, NOT local_clock timestamps, defines membership.
        if any("Undervoltage detected" in r["text"] for r in window):a.append("kmsg:undervoltage")
    return result(a,u)


def calibration_check(batch,fixed_hz):
    if not batch:return result(unknown=["calibration:missing"])
    a=[];u=[];w=[]
    for side in ("before","after"):
        cpus=batch.get(side,{})
        for cpu in range(4):
            r=cpus.get(str(cpu));tag=f"calibration:{side}:cpu{cpu}"
            if not r:u.append(tag+":missing");continue
            intervals=r.get("intervals",[])[1:-1]
            if not r.get("completed"):u.append(tag+":early_exit")
            valid_count=0
            for x in intervals:
                valid=(x.get("running_percent")==100 and finite(x.get("cycles")) and x["cycles"]>=0 and
                       finite(x.get("task_ms")) and x["task_ms"]>0 and finite(x.get("dt")) and x["dt"]>0)
                if not valid:u.append(tag+":invalid_count");continue
                valid_count+=1
                if x["cycles"]/(x["task_ms"]/1000)<fixed_hz*.97:a.append(tag+":frequency_below_97_percent")
                if not .980-1e-12<=x["dt"]<=1.020+1e-12:w.append(tag+":timing")
                if x["task_ms"]/1000<x["dt"]*.99-1e-12:w.append(tag+":busy_below_99_percent")
            if valid_count<25:u.append(tag+":fewer_than_25_intervals")
            if "monitor" not in r:u.append(tag+":monitor_missing")
            else:
                q=qualify(r["monitor"],r.get("log"),check_calibration=False)
                a.extend(q["abnormal"]);u.extend(q["unknown"]);w.extend(q["warnings"])
    return result(a,u,w)


def qualify(run,log=None,batch=None,check_calibration=True):
    ws=run.get("workload_window");ms=run.get("monitor_window")
    base=result()
    if not ws or not ms or not all(finite(v) for v in list(ws or [])+list(ms or [])):
        base=result(unknown=["missing_monotonic_windows"]);ws=ms=None
    elif not (ms[0]<=ws[0]-2 and ms[1]>=ws[1]+4 and ws[0]<=ws[1]):
        base=result(unknown=["monitor_padding_incomplete"])
    fixed=run["fixed_hz"];streams=run.get("streams",{});parts=[base]
    required=set(run.get("required_streams",streams))
    for kind in ("scaling_cur_freq","cpuinfo_cur_freq","temperature","alarm","governor","min_freq","max_freq"):
        if not any(n.split(":")[0]==kind for n in required):required.add(kind)
    for name in sorted(required):
        kind=name.split(":")[0]
        valid=lambda v:finite(v) and v>=0
        window=ws if kind in ("scaling_cur_freq","cpuinfo_cur_freq") else ms
        if kind=="temperature":predicate=lambda v:v<75;valid=finite
        elif kind=="alarm":predicate=lambda v:v==0;valid=lambda v:v in (0,1) and not isinstance(v,bool)
        elif kind in ("scaling_cur_freq","cpuinfo_cur_freq"):predicate=lambda v:v==fixed
        else:
            expected=run.get("policy_before",{}).get(name)
            if expected is None:parts.append(result(unknown=[name+":missing_baseline"]))
            predicate=lambda v,e=expected:e is None or v==e
            if kind=="governor":valid=lambda v:isinstance(v,str) and v in ("performance","schedutil","ondemand","powersave","userspace","conservative")
        parts.append(stream_check(name,streams.get(name,[]),window,predicate,valid))
    parts.append(log_check(log,run.get("endpoints"),ms))
    if check_calibration:parts.append(calibration_check(batch,fixed))
    return combine(*parts)


def effective_frequency_covariate(values):
    """Sensitivity flag only; never changes eligibility."""
    if not values or any(not finite(x) or x<=0 for x in values):raise ValueError("invalid_effective_frequency")
    med=statistics.median(values);mad=statistics.median(abs(x-med) for x in values)
    threshold=med-3*max(mad,.001*med)
    return dict(median=med,mad=mad,threshold=threshold,outliers=[i for i,x in enumerate(values) if x<threshold])


def frequency_comparison(a,b):
    ma=effective_frequency_covariate(a)["median"];mb=effective_frequency_covariate(b)["median"]
    delta=abs(ma-mb)/((ma+mb)/2)
    return dict(relative_difference=delta,performance_interpretation_allowed=delta<=.005,
                label="confounding_risk" if delta>.005 else "no_frequency_confounding_flag")


def drain_nonblocking(recorder, fd, save, clock):
    """Offline-testable kmsg drain. Caller supplies an already nonblocking FD."""
    import os
    if os.get_blocking(fd):raise ValueError("recorder_requires_nonblocking_fd")
    before=clock()
    while True:
        try:raw=os.read(fd,65536)
        except BlockingIOError:break
        except OSError as e:
            recorder.errors.append("EPIPE" if e.errno==32 else "read_error")
            break
        if not raw:break
        for line in raw.decode().splitlines():
            header,sep,text=line.partition(";")
            try:
                fields=header.split(",")
                if not sep or len(fields)<4:raise ValueError()
                record=dict(seq=int(fields[1]),local_clock=int(fields[2]),text=text)
            except ValueError:
                recorder.errors.append("parse_failed");continue
            recorder.save(record,success=save(record))
    return dict(boot=recorder.boot,seq=recorder.last,before=before,after=clock(),error=None)
