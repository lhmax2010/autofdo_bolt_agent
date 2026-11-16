from pathlib import Path
import json,shutil,hashlib,datetime
w=Path.cwd();d=w/'temp/verify-361624-fix-v3-20261116'
base=w/'docs/reviews/gerrit/361624/suggested-fix';e=base/'evidence/v3'
def load(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
build=load(d/'build-authorized/result.json');artifact=load(d/'verification/result.json')
flags=load(d/'flags/result.json');oldwait=load(d/'build/result.json')
assert build['status']=='success' and build['exit_code']==0
assert load(d/'build-authorized/acceptance.json')['accepted']
assert artifact['status']=='success' and flags['all_passed']
assert 'ActiveState=inactive' in (d/'final-service.txt').read_text()
raw=[]
def copy(p,target):
 assert p.is_file()
 raw.append(dict(path=str(p.relative_to(w)),sha256=sha(p),bytes=p.stat().st_size))
 if p.stat().st_size<1000000:
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 else:print('Large raw retained in temp:',p)
for p in sorted(d.iterdir()):
 if p.is_file() and p.name!='finalize.py':copy(p,e/p.name)
copy(d/'finalize.py',e/'finalize.py')
for dirname in ['build','build-authorized','flags','verification']:
 for p in sorted((d/dirname).iterdir()):
  if p.is_file():copy(p,e/dirname/p.name)
r=d/'root-x86_64/local/BUILD-ROOTS/scratch.x86_64.0'
b=r/'home/abuild/rpmbuild/BUILD/llvm-22.1.8/bolt-build'
for source,dest in [(b/'CMakeCache.txt','bolt-CMakeCache.txt'),(b/'bolt_rt-bins/CMakeCache.txt','bolt-rt-CMakeCache.txt')]:
 copy(source,e/'flags'/dest)
for x in load(d/'flags/input-shas.json'):
 p=Path(x['path']);assert sha(p)==x['sha256']
 if p.name=='build.ninja':raw.append(dict(path=str(p.relative_to(w)),sha256=sha(p),bytes=p.stat().st_size))
rpms=load(d/'verification/all-rpms.json')
for row in rpms:
 p=Path(row['path']);assert sha(p)==row['sha256']
 raw.append(dict(path=str(p.relative_to(w)),sha256=row['sha256'],bytes=row['bytes']))
(e/'raw-index.json').write_text(json.dumps(raw,indent=2)+'\n')
summary=dict(conclusion='v3 patch validation passed',patch_sha256=sha(base/'361624-suggested-fix-v3.patch'),
 applied_commit='bd6dd0d009b4c70e89d1a5730dbc30d3e6c7dce8',
 parsing_commands=38,build=build,wait_seconds=oldwait['elapsed_seconds'],
 flags_assertions=flags['all_passed'],artifact_status=artifact['status'],
 authorization='本轮不用考虑限制；取消16GiB启动等待，保留-j2、6G与OOM停止保护',
 verification_resource=load(d/'artifact-check-execution.json'),final_service=(d/'final-service.txt').read_text())
(e/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
report=base/'verification.md';s=report.read_text()
old='此前临时取消16GiB门槛的授权**不沿用**。启动条件为MemAvailable≥16GiB、load1<0.6×nproc、磁盘可用≥50GiB，最多等待1800秒。构建时每60秒采样；连续两次MemAvailable<6GiB、磁盘<20GiB，或MemoryMax/max/oom事件出现即停止本任务单元，不提高上限、不改-j、不重试。'
new='''最初按本轮指令恢复MemAvailable≥16GiB、load1<0.6×nproc、磁盘≥50GiB、最多1800秒的门禁，未沿用旧授权。等待944.208秒后，用户在本会话新授权“本轮不用考虑限制”。据此停止**尚未启动GBS的等待监督器**，取消本次16GiB等待，保留负载/磁盘检查、-j2、6G/5G/200%与运行中停止保护。不是构建失败重试；该root在真正启动前不存在。两次监督器收据分别保留在build/（signal 15、GBS退出码null）与build-authorized/（实际构建）。

最新实际[完整argv](evidence/v3/planned-command-authorized.json)、[授权及停止等待收据](evidence/v3/gate-waiver-stop.json)、[执行器](evidence/v3/run_build_authorized.py)。每60秒采样；连续两次MemAvailable<6GiB、磁盘<20GiB或max/oom事件停止本任务，未提高6G上限或并行度。实际新root的两份RPM宏与前置解析root逐字节相同，见[actual-root-macros.json](evidence/v3/actual-root-macros.json)。'''
assert old in s;s=s.replace(old,new)
marker='进行中：门禁等待。尚无GBS退出码、产物或冒烟结果；后续只按真实收据更新。本节的预备验证脚本不构成验收结果。'
assert marker in s
t='''**GBS退出0，v3补丁通过验证。** 仅构建x86_64的llvm-tools-subpkgs.spec，不是完整llvm.spec或AArch64主机构建。

| 用户项 | 结果 | 原始证据与行号 |
|---|---|---|
| 四.1 Tizen导出flags | 通过：CFLAGS/CXXFLAGS含-g2 -gdwarf-4，三者均export | build-authorized/build.log 486–491；flags/result.json |
| 四.2 CMakeCache | 通过：C/CXX与各自导出值逐字节相同；EXE/SHARED链接flags等于LDFLAGS加-Wl,--build-id=sha1 | flags/bolt-CMakeCache.txt 66、96、114、240；flags/result.json |
| 四.3 编译规则 | 通过：BOLT保留完整发行版flags及-g2，之后-O3 -DNDEBUG；bolt_rt的C/CXX缓存为空 | flags/bolt-rule.txt（原build.ninja 418起）；flags/bolt-rt-rule.txt（原52起）；flags/bolt-rt-CMakeCache.txt 43、70 |
| 四.4 provider/targets | 通过：Version-Release一致22.1.8-4.1；aarch64与x86-64均在版本表，两个grep通过 | build-authorized/build.log 550–551、773–774；verification/bolt-version.txt；flags/result.json |
| 四.5 RPM/依赖 | 通过：3个二进制包+1个源码包；bolt含两份lib64 runtime归档，依赖libllvm=22.1.8和LLVM_22.1(64bit)，无compiler-rt运行依赖 | verification/all-rpms.json；rpm-list-0/1/2.stdout、source-rpm-0.stdout；bolt-requires.stdout 2、11 |
| 四.6 调试信息 | 通过：5份.debug与对应运行文件build-id一致；有BinaryFunction.cpp编译单元；debugsource非空且含BOLT源码 | verification/result.json；llvm-bolt-dwarf.stdout 1265；rpm-list-2.stdout 138 |
| 四.7 链接与运行 | 通过：5个ELF均GNU_RELRO，逐个ldd无缺失、--version退出0 | verification/relro-*.stdout（llvm-bolt第21行）；ldd-*.stdout、version-*.stdout；commands.json |
| 四.8 两项冒烟 | 通过：两架构均relocation模式、改写退出0、objdump退出0；x86输入/输出均退出7 | verification/aarch64-bolt.stdout、x86_64-bolt.stdout第5行；commands.json、result.json；smoke-equivalence.json |
| 四.9 资源 | 构建成功；high回收事件2342，max/oom/oom_kill均0，未触发停止或重试 | build-authorized/resources.json、child-result.json、result.json、end.log |

以上相对证据路径均位于[evidence/v3](evidence/v3/summary.json)。实际执行的[flags断言](evidence/v3/verify_flags.py)与[产物/冒烟检查器](evidence/v3/verify_artifacts.py)已归档；不把检查器存在当作结果，结果由各命令真实退出码与[验收JSON](evidence/v3/verification/result.json)支持。两项冒烟源码与旧素材逐字节相同；除新root与测试目录外，编译、链接、BOLT与objdump参数相同（smoke-equivalence.json）。

'''
start=build['ended']-build['build_seconds'];utc=lambda x:datetime.datetime.fromtimestamp(x,datetime.timezone.utc).isoformat()
t+=f"实际GBS墙钟 **{build['build_seconds']:.3f}秒**（子进程收据{build['child']['seconds']:.3f}秒）；开始约{utc(start)}，结束{utc(build['ended'])}。此前等待 **{oldwait['elapsed_seconds']:.3f}秒** 单列，不计入构建墙钟。构建cgroup实读memory.peak **{build['memory_peak']:,} B（{build['memory_peak']/2**30:.4f} GiB）**，每60秒采样的最低MemAvailable **{build['min_mem_available']:,} B（{build['min_mem_available']/2**30:.4f} GiB）**；MemoryHigh=2342、max=0、oom=0、oom_kill=0、oom_group_kill=0。产物轻量检查scope峰值705,003,520 B，无max/OOM；本任务全部监督单元已结束。\n\n"
t+='### 8.4 产物清单与身份\n\n| RPM | 字节数 | SHA-256 |\n|---|---:|---|\n'
for row in rpms:t+=f"| {Path(row['path']).name} | {row['bytes']} | {row['sha256']} |\n"
t+='\n完整文件清单见verification/rpm-list-0.stdout（bolt）、rpm-list-1.stdout（bolt-debuginfo）、rpm-list-2.stdout（debugsource）、source-rpm-0.stdout（源码RPM）。源码RPM和二进制只留temp，不进Git。\n\n| 运行文件 | runtime/.debug一致的build-id |\n|---|---|\n'
for row in artifact['checks']['runtime_debug_build_ids']:t+=f"| {Path(row['runtime']).name} | {row['build_id']} |\n"
t+='\nllvm-bolt SHA-256：'+artifact['checks']['runtime_debug_build_ids'][0]['sha256']+'。每个运行文件与.debug的SHA均见verification/result.json。两个runtime归档为/usr/lib64/libbolt_rt_instr.a、/usr/lib64/libbolt_rt_hugify.a。\n\n'
t+='''### 8.5 结论与边界

**v3 补丁通过验证。** 这次在完整Tizen前置段下实际构建并验证了BOLT源码DWARF和debugsource，闭合第7节指出的正常环境验收缺口。旧错误环境的产物与结论保留为历史，不覆盖或复用其调试身份。

AArch64只完成spec解析和x86_64工具改写AArch64 ELF冒烟，没有实际构建AArch64主机包；完整llvm.spec构建未执行。两项无profile最小程序冒烟不代表真实工作负载优化收益。

原件和大产物保存在temp/verify-361624-fix-v3-20261116/；[raw-index.json](evidence/v3/raw-index.json)记录路径、SHA、大小。原补丁/v1/v2证据未改，未删除任何既有temp目录；未操作开发板、Gerrit或hq，未安装主机软件。GBS只在本任务独立root安装依赖，自动生成的HOME/.gbs.conf位于本任务temp内；没有新增WORKDIR外项目产物。完成后停止。
'''
s=s.replace(marker,t);report.write_text(s)
status=w/'docs/STATUS.md';s=status.read_text();heading='## Gerrit 361624 v3正常Tizen前置段验收完成（2026-11-16）'
assert heading not in s
text=heading+'\n\n'
text+='- 指定v3补丁原样mv，SHA 81f41716aa2fe1761d1a3f228c83ab86e6559e0f09c7c5defeac762afec5116b；基于da885208干净git am，结果 **bd6dd0d009b4c70e89d1a5730dbc30d3e6c7dce8**。38次只读解析/展开全0：tools包与依赖同v2，llvm.spec仅3行注释；实际root宏与executor-v4取证root相同。\n'
text+=f"- **v3补丁通过验证。** 正常前置段x86_64 tools GBS退出0、墙钟 **{build['build_seconds']:.3f}秒**。三种发行版flags导出、CMake缓存/编译规则、provider22.1.8-4.1通过；产出3个二进制RPM与源码RPM。5份debug身份一致，BOLT源码CU与非空debugsource已确认；5个GNU_RELRO/ldd/version通过。两架构relocation改写退出0，x86前后退出7。\n"
text+='- 开始按16GiB门禁等待944.208秒；随后用户本轮新授权“本轮不用考虑限制”，取消启动内存等待，保留-j2、6G/5G/200%及停止保护。实际构建峰值5,369,176,064 B，最低采样MemAvailable12,783,538,176 B；high2342、max/OOM0，无资源停止/重试。等待与构建分别保留真实结束收据。\n'
text+='- [报告第8节](reviews/gerrit/361624/suggested-fix/verification.md#8-v3-正常前置段构建验收)、[证据汇总](reviews/gerrit/361624/suggested-fix/evidence/v3/summary.json)、SHA256SUMS已更新。闭合第7节正常环境验收缺口；旧证据保持原样，AArch64主机包/完整llvm.spec仍未实构建。不接板、不操作Gerrit、不改hq、不安装主机软件，所有本任务单元结束后停止。\n\n'
pos=s.index('## Gerrit 361624 v2评审归档')
status.write_text(s[:pos]+text+s[pos:])
print('Report/STATUS/evidence prepared.',len(raw),'raw-index entries')
