"""Synthetic sysfs/kmsg records; no board access or profile inputs."""
import copy
import unittest
from registration_telemetry import *


def fixture():
    rec=Recorder("boot","/opt/afdo_agent/log")
    rec.save(dict(seq=0,text="boot",local_clock=900))
    e0=rec.endpoint("boot",-2,-1)
    rec.save(dict(seq=1,text="normal",local_clock=9999))
    e1=rec.endpoint("boot",35,36)
    values=dict(scaling_cur_freq=1500000000,cpuinfo_cur_freq=1500000000,temperature=60,
                alarm=0,governor="performance",min_freq=600000000,max_freq=1500000000)
    run=dict(fixed_hz=1500000000,workload_window=[2,30],monitor_window=[0,34],
             policy_before={k:values[k] for k in ("governor","min_freq","max_freq")},
             streams={k:[dict(time=t,value=v) for t in range(35)] for k,v in values.items()},
             endpoints=[e0,e1])
    log=rec.snapshot(40)
    c=dict(completed=True,intervals=[dict(dt=1.,cycles=1500000000,task_ms=1000,running_percent=100) for _ in range(27)],monitor=copy.deepcopy(run),log=copy.deepcopy(log))
    batch={side:{str(cpu):copy.deepcopy(c) for cpu in range(4)} for side in ("before","after")}
    return run,log,batch


class Telemetry(unittest.TestCase):
    def test_real_nonblocking_fd_EAGAIN(self):
        import os,time
        r,w=os.pipe()
        try:
            os.set_blocking(r,False)
            rec=Recorder("boot","/opt/afdo_agent/log")
            os.write(w,b"6,0,123,-;boot\\n")
            e=drain_nonblocking(rec,r,lambda row:True,time.monotonic)
            self.assertEqual(e["seq"],0)
            e2=drain_nonblocking(rec,r,lambda row:True,time.monotonic)
            self.assertEqual(e2["seq"],0);self.assertLess(e2["after"]-e2["before"],1)
        finally:os.close(r);os.close(w)
    def test_missing_policy_baseline_unknown_not_abnormal(self):
        r,l,b=fixture();r["policy_before"]={}
        q=qualify(r,l,b);self.assertEqual(q["status"],"unknown");self.assertFalse(q["abnormal"])
    def test_mock_sysfs_directory(self):
        import tempfile
        from pathlib import Path
        from run_scoped import WORK
        with tempfile.TemporaryDirectory(dir=WORK/"temp/tmp") as d:
            root=Path(d);(root/"cpuinfo_cur_freq").write_text("1500000")
            rows=[dict(time=0,value=int((root/"cpuinfo_cur_freq").read_text())*1000)]
            self.assertEqual(stream_check("cpuinfo",rows,[0,0],lambda v:v==1500000000,finite)["status"],"observed_no_anomaly")
            (root/"cpuinfo_cur_freq").write_text("<unknown>")
            rows=[dict(time=0,value=(root/"cpuinfo_cur_freq").read_text())]
            self.assertEqual(stream_check("cpuinfo",rows,[0,0],lambda v:v==1500000000,finite)["status"],"unknown")
    def test_required_streams_cannot_hide_missing_sensors(self):
        r,l,b=fixture();r["required_streams"]=[];r["streams"]={}
        self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_blocking_fd_rejected(self):
        import os,time
        r,w=os.pipe()
        try:
            with self.assertRaisesRegex(ValueError,"nonblocking"):drain_nonblocking(Recorder("boot","/opt/afdo_agent/log"),r,lambda row:True,time.monotonic)
        finally:os.close(r);os.close(w)
    def test_all_normal(self):self.assertEqual(qualify(*fixture())["status"],"observed_no_anomaly")
    def changed_stream(self,name,index,value,expected="abnormal"):
        r,l,b=fixture();r["streams"][name][index]["value"]=value
        q=qualify(r,l,b);self.assertEqual(q["status"],expected);return q
    def test_alarm_transient(self):self.changed_stream("alarm",15,1)
    def test_alarm_late_driver_update(self):self.changed_stream("alarm",33,1)
    def test_cpuinfo_deviation_then_recovery(self):self.changed_stream("cpuinfo_cur_freq",10,1400000000)
    def test_policy_max_drop(self):self.changed_stream("max_freq",10,1400000000)
    def test_temperature_75(self):self.changed_stream("temperature",10,75)
    def test_unknown_reading(self):self.changed_stream("temperature",10,"<unknown>","unknown")
    def test_invalid_temperature(self):self.changed_stream("temperature",10,float("nan"),"unknown")
    def test_read_timeout(self):
        r,l,b=fixture();r["streams"]["temperature"][3]["error"]="timeout";self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_hot_and_missing_sensor(self):
        r,l,b=fixture();r["streams"]["temperature"][3]["value"]=80;r["streams"]["alarm"]=[]
        q=qualify(r,l,b);self.assertEqual(q["status"],"abnormal");self.assertTrue(q["unknown"])
    def test_undervoltage_two_seconds_after_workload(self):
        r,l,b=fixture();l["records"][1].update(text="Undervoltage detected",local_clock=32)
        self.assertIn("kmsg:undervoltage",qualify(r,l,b)["abnormal"])
    def test_outside_log_clock_looks_inside(self):
        r,l,b=fixture();l["records"][0].update(text="Undervoltage detected",local_clock=15)
        self.assertEqual(qualify(r,l,b)["status"],"observed_no_anomaly")
    def test_query_failure_boot_sticky(self):
        r,l,b=fixture();l["records"][0]["text"]="Failed to get throttled"
        self.assertIn("kmsg:query_failure_sticky",qualify(r,l,b)["unknown"])
    def test_log_gap(self):
        r,l,b=fixture();l["records"][1]["seq"]=2;self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_EPIPE(self):
        r,l,b=fixture();r["endpoints"][1]["error"]="-EPIPE";self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_log_read_timeout(self):
        r,l,b=fixture();r["endpoints"][1]["error"]="timeout";self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_endpoints_cross_boot(self):
        r,l,b=fixture();r["endpoints"][1]["boot"]="other";self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_endpoints_not_enclosing(self):
        r,l,b=fixture();r["endpoints"][1]["before"]=33;self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_empty_log_window(self):
        r,l,b=fixture();r["endpoints"][1]["seq"]=0;self.assertEqual(qualify(r,l,b)["status"],"observed_no_anomaly")
    def test_background_saved_undervoltage_no_new_endpoint(self):
        rec=Recorder("boot","/opt/afdo_agent/log");rec.save(dict(seq=0,text="boot"))
        e0=rec.endpoint("boot",-2,-1);rec.save(dict(seq=1,text="Undervoltage detected"))
        e1=rec.endpoint("boot",35,36)
        self.assertEqual(e1["seq"],1);self.assertEqual(log_check(rec.snapshot(40),[e0,e1],[0,34])["status"],"abnormal")
    def test_nonblocking_empty_preserves_last(self):
        rec=Recorder("boot","/opt/afdo_agent/log");self.assertEqual(rec.endpoint("boot",0,1)["seq"],-1)
        rec.save(dict(seq=0,text="boot"))
        self.assertEqual(rec.endpoint("boot",2,3)["seq"],0)
        self.assertEqual(rec.endpoint("boot",4,5)["seq"],0)
    def test_recorder_output_invalid(self):
        for p in ("/tmp/log","/opt/afdo_agent/../else","/opt/afdo_agent2/log"):
            with self.assertRaises(ValueError):Recorder("boot",p)
    def test_first_seq37_reject_admission(self):
        rec=Recorder("boot","/opt/afdo_agent/log");rec.save(dict(seq=37,text="normal"));self.assertFalse(rec.admit(10))
    def test_prior_authorization_still_unknown(self):
        rec=Recorder("boot","/opt/afdo_agent/log");rec.save(dict(seq=37,text="normal"))
        self.assertTrue(rec.admit(10,dict(boot="boot",accept_unknown=True,time=9)))
        self.assertIn("kmsg:boot_history_incomplete",log_check(rec.snapshot(40),[rec.endpoint("boot",-2,-1),rec.endpoint("boot",35,36)],[0,34])["unknown"])
    def test_posthoc_authorization_rejected(self):
        rec=Recorder("boot","/opt/afdo_agent/log");rec.save(dict(seq=37,text="normal"))
        self.assertFalse(rec.admit(10,dict(boot="boot",accept_unknown=True,time=11)))
    def test_later_normal_cannot_clear_unknown(self):
        rec=Recorder("boot","/opt/afdo_agent/log");rec.save(dict(seq=37,text="normal"));rec.save(dict(seq=38,text="normal"))
        self.assertFalse(rec.admit(10))
    def test_save_failed_does_not_advance(self):
        rec=Recorder("boot","/opt/afdo_agent/log");rec.save(dict(seq=0,text="boot"));rec.save(dict(seq=1,text="lost"),success=False)
        self.assertEqual(rec.last,0);self.assertIn("save_failed",rec.errors)
    def test_boot_change_without_restart(self):
        rec=Recorder("boot","/opt/afdo_agent/log");rec.save(dict(seq=0,text="boot"));rec.endpoint("new",1,2)
        self.assertIn("recorder_not_restarted",rec.errors);self.assertFalse(rec.admit(5))
    def test_buffer_wrap_between_endpoints(self):
        r,l,b=fixture();l["errors"]=["-EPIPE"];self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def test_policy_missing_after_workload(self):
        r,l,b=fixture();r["streams"]["max_freq"]=r["streams"]["max_freq"][:31]
        self.assertIn("max_freq:incomplete_window",qualify(r,l,b)["unknown"])
    def test_no_postworkload_readings(self):
        r,l,b=fixture()
        for k in r["streams"]:r["streams"][k]=r["streams"][k][:31]
        self.assertEqual(qualify(r,l,b)["status"],"unknown")
    def gap(self,dt,count=1):
        ts=[0.]
        for _ in range(count):ts.append(ts[-1]+dt)
        q=stream_check("x",[dict(time=t,value=1) for t in ts],[0,ts[-1]],lambda v:True,finite);return q
    def test_gap_1_5(self):self.assertFalse(self.gap(1.5)["warnings"])
    def test_gap_1_6(self):self.assertTrue(self.gap(1.6)["warnings"])
    def test_gap_3_0(self):self.assertEqual(self.gap(3)["status"],"observed_no_anomaly")
    def test_gap_3_01(self):self.assertEqual(self.gap(3.01)["status"],"unknown")
    def test_three_gaps(self):self.assertEqual(self.gap(1.6,3)["status"],"unknown")
    def test_each_sensor_separate(self):
        self.assertEqual(combine(self.gap(1.6,2),self.gap(1.6,2))["status"],"observed_no_anomaly")
    def calib(self,change):
        r,l,b=fixture();change(b["before"]["0"]);return calibration_check(b,1500000000)
    def test_calibration_1_44(self):self.assertEqual(self.calib(lambda c:c["intervals"][3].update(cycles=1440000000))["status"],"abnormal")
    def test_calibration_slow_and_1_44(self):
        q=self.calib(lambda c:c["intervals"][3].update(cycles=1512000000,task_ms=1050,dt=1.05))
        self.assertEqual(q["status"],"abnormal");self.assertTrue(q["warnings"])
    def test_calibration_1_015(self):
        self.assertFalse(self.calib(lambda c:c["intervals"][3].update(cycles=1522500000,task_ms=1015,dt=1.015))["warnings"])
    def test_calibration_1_025(self):
        self.assertTrue(self.calib(lambda c:c["intervals"][3].update(cycles=1537500000,task_ms=1025,dt=1.025))["warnings"])
    def test_calibration_time_boundaries(self):
        for dt in (.98,1.02):self.assertFalse(self.calib(lambda c:c["intervals"][3].update(cycles=1500000000*dt,task_ms=dt*1000,dt=dt))["warnings"])
    def test_busy98_warning(self):self.assertTrue(self.calib(lambda c:c["intervals"][3].update(cycles=1470000000,task_ms=980))["warnings"])
    def test_busy98_low_still_abnormal(self):self.assertEqual(self.calib(lambda c:c["intervals"][3].update(cycles=1411200000,task_ms=980))["status"],"abnormal")
    def test_busy98_invalid_still_unknown(self):self.assertEqual(self.calib(lambda c:c["intervals"][3].update(cycles=0,task_ms=980,running_percent=0))["status"],"unknown")
    def test_24_intervals(self):self.assertEqual(self.calib(lambda c:c["intervals"].pop())["status"],"unknown")
    def test_one_invalid_interval(self):self.assertEqual(self.calib(lambda c:c["intervals"][3].update(running_percent=80))["status"],"unknown")
    def test_all_truncated(self):self.assertEqual(self.calib(lambda c:c.update(intervals=[]))["status"],"unknown")
    def test_early_exit(self):self.assertEqual(self.calib(lambda c:c.update(completed=False))["status"],"unknown")
    def test_PMU_not_counted(self):self.assertEqual(self.calib(lambda c:c["intervals"][3].update(cycles="<not counted>"))["status"],"unknown")
    def test_post_calibration_abnormal_whole_batch(self):
        r,l,b=fixture();b["after"]["0"]["intervals"][3]["cycles"]=1440000000
        self.assertEqual(qualify(r,l,b)["status"],"abnormal")
    def test_one_hot_other_unknown_missing_post(self):
        r,l,b=fixture();b["after"]={}
        self.assertEqual(qualify(r,l,b)["status"],"unknown")
        r["streams"]["temperature"][3]["value"]=80
        self.assertEqual(qualify(r,l,b)["status"],"abnormal")
    def test_calibration_monitor_hot(self):
        q=self.calib(lambda c:c["monitor"]["streams"]["temperature"][3].update(value=80))
        self.assertEqual(q["status"],"abnormal")
    def test_MAD_floor_identical15(self):self.assertFalse(effective_frequency_covariate([1.5e9]*15)["outliers"])
    def test_frequency_outlier_flag_only(self):
        r,l,b=fixture();before=qualify(r,l,b)
        self.assertEqual(effective_frequency_covariate([1.5e9]*14+[1.4e9])["outliers"],[14])
        self.assertEqual(qualify(r,l,b),before)
    def test_frequency_confounding(self):self.assertFalse(frequency_comparison([1.5e9]*15,[1.49e9]*15)["performance_interpretation_allowed"])

if __name__=="__main__":unittest.main()
