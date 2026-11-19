from pathlib import Path
import subprocess, json, datetime
p=Path(__file__).resolve().parent
sdb=['sdb','-s','192.168.108.13:26101']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def send(name,args,timeout):
 start=utc()
 with (p/f'{name}.out').open('wb') as out,(p/f'{name}.err').open('wb') as err:
  result=subprocess.run(sdb+args,stdin=subprocess.DEVNULL,stdout=out,stderr=err,timeout=timeout)
 (p/f'{name}.json').write_text(json.dumps({'argv':sdb+args,'start':start,'end':utc(),'rc':result.returncode},indent=2)+'\n')
 return result.returncode
s=r"""export LC_ALL=C
printf 'INITIAL_UID '; id -u
i=0
while test "$i" -le 60; do
 printf 'FRAME %s ' "$i"; cut -d' ' -f1 /proc/uptime
 printf 'LOAD '; cat /proc/loadavg
 ps -eo pid,ppid,user:24,pcpu,time,comm
 for pp in $(ps -C acm-watcher -o pid=); do
  printf 'ACM_PID %s\n' "$pp"
  if test -r "/proc/$pp/cmdline"; then printf 'ACM_CMD '; tr '\000' ' ' < "/proc/$pp/cmdline"; printf '\n'; fi
  cat "/proc/$pp/cgroup" 2>/dev/null
 done
 printf 'FRAME_END %s\n' "$i"
 i=$((i+1))
 if test "$i" -le 60; then sleep 5; fi
done
echo __BASELINE_DONE__"""
try:
 assert send('baseline-root-on',['root','on'],15)==0
 assert send('baseline',['shell',s],360)==0
 assert b'__BASELINE_DONE__' in (p/'baseline.out').read_bytes()
finally:
 send('baseline-root-off',['root','off'],15)
 send('baseline-final',['shell','id -u; echo __END__'],15)
 print((p/'baseline-final.out').read_text(),flush=True)
