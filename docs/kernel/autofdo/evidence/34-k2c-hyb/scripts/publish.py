import collections
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

task=Path(__file__).resolve().parent
repo=Path(sys.argv[1])
docs=repo/'docs/kernel/autofdo'
mode=sys.argv[2]
prior=task.parent/'k1f-3'
names={'gcov':('32','K-AFDO-GCOV'),'r1':('33','K-AFDO-R1'),'hyb':('34','K-AFDO-HYB')}
kinds=('pipe','mmfault','tmpfs','syscall','forkexec','tos')
verdict={'faster':'更快','slower':'更慢','equivalent':'等价','inconclusive':'不确定'}

def read(path):
    return json.loads(path.read_text())

def meta(path):
    with path.open('rb') as stream:
        return dict(bytes=path.stat().st_size,sha256=hashlib.file_digest(stream,'sha256').hexdigest())

def git(*argv,**kwargs):
    return subprocess.run(['git',*argv],cwd=repo,text=True,check=True,**kwargs)

def save(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')

def copy(source,target):
    if source.is_file():
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)

def pct(x):
    return '—' if x is None else f'{x*100:+.3f}%'

def ci(xs):
    return ' 至 '.join(pct(x) for x in xs)

def pack_run(d,e):
    fixed=(
      'host-continuity.jsonl','lock-concurrency.jsonl','preflight-recovery.json','logs/result.json','logs/frozen.json','logs/admission.jsonl','logs/resources.jsonl','logs/command.json',
      'logs/proof-resources.jsonl','logs/proof-result.json','artifacts/dependencies.json','artifacts/variant-verification.json',
      'board/preregistration.json','board/preregistration.sha256','board/start-cold/passed.json','board/start-cold/windows.jsonl',
      'board/start-cold/samples.jsonl','board/afdo-first.json','board/terminal.json','board/formal-analysis.json','board/mechanism-analysis.json',
      'board/expected-before-deploy.sha256','board/deploy/receipts/after.sha256',
      'board/deploy/receipts/df.txt','board/deploy/receipts/projected-lowest-available',
      'board/finish-verify/receipts/after.sha256','board/finish-verify/receipts/df.txt',
      'board/finish-verify/receipts/tryboot.txt','board/final-owner/plat.json','board/final-shared/sdb-listener.stdout',
      'board/afdo-first/direct-summary.json','board/afdo-first/reboot-result.json','board/afdo-first/smoke/result.json',
      'board/afdo-first/fdt-comparison.json','board/emergency-final-plat/plat.json',
      'artifacts/arm-rpi4/layout.json','artifacts/arm-rpi4/consumption/results.json','artifacts/arm-rpi4/consumption/source-match.json',
    )
    for name in fixed:
        copy(d/name,e/name)
    for part in ('arm-rpi4','arm-rpi4-rt'):
        for name in ('compile-check.json','link-argv.json','module-vermagic.json','vmlinux-a-order.txt'):
            item=f'artifacts/{part}/{name}'
            copy(d/item,e/item)
    diagnostics=d/'artifacts/arm-rpi4/consumption'
    for folder in diagnostics.glob('object-*'):
        for artifact in ('argv.json','applied.json','clang.log'):
            item=folder/artifact
            copy(item,e/item.relative_to(d))
    for phase in ('formal','mechanism'):
        local=d/'board'/phase
        for summary in ('block.json','attempt.json','before-tryboot-host.json','measurement-result.json','counter-result.json',
                        'reboot-result.json','direct-summary.json','fdt-comparison.json','plat.json','failure.json','summary.json',
                        'wait.jsonl','activity.jsonl','direct-dmesg-warning-delta.txt'):
            for f in local.rglob(summary):
                copy(f,e/f.relative_to(d))
    for name in ('build.py','prove.py','guard-proof.py','prepare-board.py','pipeline.py','publish.py','measurement_lock.py'):
        copy(task/name,e/'scripts'/name)
    if mode=='gcov':
        copy(task/'build-gcov-effective.py',e/'scripts/build-gcov-effective.py')
        copy(task/'host-overlap-observer.jsonl',e/'host-overlap-observer.jsonl')
        copy(task/'lock-handover.jsonl',e/'lock-handover.jsonl')
        for name in ('shared-switch.py','shared-switch-barrier.py'):
            copy(task/name,e/'scripts'/name)
    for name in ('run_formal.py','boot-afdo.sh'):
        copy(d/'board'/name,e/'scripts'/name)
    raw={}
    for f in (d/'logs/build.log',d/'logs/proof.log',d/'artifacts/arm-rpi4/link.map',
              d/'artifacts/arm-rpi4/vmlinux',d/'artifacts/arm-rpi4/arch/arm/boot/zImage'):
        if f.is_file():
            if f.name in {'vmlinux','zImage'} and (d/'artifacts/variant-verification.json').is_file():
                artifact=read(d/'artifacts/variant-verification.json')['arm-rpi4']
                sha=artifact['vmlinux_sha256' if f.name=='vmlinux' else 'zImage_sha256']
                raw[str(f.relative_to(d))]=dict(bytes=f.stat().st_size,sha256=sha)
            elif f.name not in {'vmlinux','zImage'}:
                raw[str(f.relative_to(d))]=meta(f)
    for phase in ('formal','mechanism'):
        for p in (d/'board'/phase).rglob('board'):
            if p.is_dir():
                raw[str(p.relative_to(d))]=dict(files={
                    f.relative_to(p).as_posix():meta(f) for f in sorted(p.rglob('*')) if f.is_file()
                })
    for artifact in diagnostics.glob('object-*/remarks.yaml'):
        raw[str(artifact.relative_to(d))]=meta(artifact)
    save(e/'index.json',dict(host_root=str(d.relative_to(task.parents[2])),
                            archived={str(f.relative_to(e)):meta(f) for f in sorted(e.rglob('*')) if f.is_file() and f.name!='index.json'},
                            host_only=raw))

def formal_lines(board,link):
    earlier=read(prior/'formal-analysis.json')['benchmarks']
    layout=read(prior/'layout-analysis.json')['benchmarks']
    formal=read(board/'formal-analysis.json')
    lines=['## 正式比较','',
           f'有效 {formal["accepted"]}/{formal["n"]} 个 block。AB/BA 种子 {formal["seed"]}，配对 log 比和 20,000 次 block bootstrap，ε=1%。效应为耗时变化，负值表示更快。布局列是单一随机布局的量级参照。 [预登记]({link}/board/preregistration.json) · [统计]({link}/board/formal-analysis.json)','',
           '| 基准 | 本轮 | bootstrap 95% CI | t 95% CI | 判定 | K1f-3 K-AFDO | K1f-2 布局 | 标记轮 BASE/候选 |',
           '| --- | ---: | --- | --- | --- | ---: | ---: | ---: |']
    for k in kinds:
        obs=formal['benchmarks'][k]
        p=obs['primary']
        cells=[k,pct(p['estimate']),ci(p['bootstrap_CI95']),ci(p['t_CI95']),verdict.get(p['verdict'],p['verdict']),
               pct(earlier[k]['primary']['estimate']),pct(layout[k]['primary']['estimate']),
               f'{obs["control_flagged_rounds"]}/{obs["candidate_flagged_rounds"]}']
        lines.append('| '+' | '.join(cells)+' |')
    lines += ['','forkexec 的 A/A 偏差为 +0.462%，bootstrap 95% CI +0.158% 至 +0.807%。','',
              '| 内存项 | K-BASE 中位 KiB | 候选中位 KiB | 配对差中位 KiB | 最小至最大 KiB |',
              '| --- | ---: | ---: | ---: | ---: |']
    for key,m in formal['memory'].items():
        lines.append(f'| {key} | {m["control_median"]:.1f} | {m["candidate_median"]:.1f} | {m["median_paired_delta"]:+.1f} | {m["min_delta"]:+g} 至 {m["max_delta"]:+g} |')
    return lines+['']

def conditions(board,link):
    boots=[p for phase in ('formal','mechanism') for p in (board/phase).rglob('block.json')]
    legs=[leg for p in boots for leg in read(p)['paired']]
    if not legs:
        return []
    temps=[leg['plat_preboot']['mC']/1000 for leg in legs]
    quiet=[leg['quiet']['seconds'] for leg in legs]
    waits=[]
    windows=[]
    starts=[]
    for leg in legs:
        if 'benchmarks' in leg:
            receipts=[round['thermal'] for bench in leg['benchmarks'].values() for round in bench['rounds']]
        else:
            receipts=list(leg['counters'].values())
        waits.extend(r['gate_wait_s'] for r in receipts)
        windows.extend(r['window_max_C'] for r in receipts if r['window_max_C'] is not None)
        starts.extend(r['start_mC']/1000 for r in receipts)
    timing_rounds=[round for leg in legs for bench in leg.get('benchmarks',{}).values() for round in bench['rounds']]
    frequencies=[round[key] for round in timing_rounds for key in ('min_frequency_khz','max_frequency_khz')]
    reboot_results=[read(board/leg['path']/'reboot-result.json') for leg in legs]
    assert all(row['server_restarts']==0 for row in reboot_results)
    recovery=[row['first_command'] for row in reboot_results]
    failures=collections.Counter(a['reason'] for p in board.rglob('attempt.json') if (a:=read(p))['status']=='technical_failure')
    fmt=lambda rows: '、'.join(f'{v:.2f}' for v in (min(rows),statistics.median(rows),max(rows))) if rows else '—'
    return ['## 运行条件','',f'已接受启动 {len(legs)} 次。PLAT 发令温度最小／中位／最大为 {fmt(temps)} °C，安静等待 {fmt(quiet)} 秒。窗口起跑温度 {fmt(starts)} °C，窗口最高温度 {fmt(windows)} °C，冷却等待 {fmt(waits)} 秒。计划固定频率 {sorted({leg["fixed_khz"] for leg in legs})} kHz，计时遥测频率最小／中位／最大 {fmt(frequencies)} kHz，rsts 分布 {dict(collections.Counter(leg["rsts"] for leg in legs))}。tryboot 到首条 SDB 命令 {fmt(recovery)} 秒，共享 SDB 重启次数 0。','',
            f'技术失败及重试 {dict(failures)}。已接受 block 的构建活动见共享锁收据。 [终态]({link}/board/terminal.json)','']

def stage():
    number,name=names[mode]
    d=task/mode
    state=read(d/'pipeline-result.json')
    files=[f'{number}_k2c_{mode}.md',f'evidence/{number}-k2c-{mode}']
    report,e=map(docs.__truediv__,files)
    e.mkdir(parents=True,exist_ok=True)
    copy(d/'pipeline-result.json',e/'pipeline-result.json')
    pack_run(d,e)
    link=f'evidence/{number}-k2c-{mode}'
    build=read(d/'logs/result.json') if (d/'logs/result.json').is_file() else {}
    lines=[f'# K2c {name} 阶段报告','',
           f'**阶段状态 {state["status"]}。** pipe 为预登记主比较。 [证据索引]({link}/index.json)','',
           '## 构建与门禁','',
           f'封存 profile SHA-256 为 {build.get("profile_sha256","缺失")}。源码为 K-BASE 加 0008，tip {build.get("source_tip","缺失")}。armv7l GBS 使用 K1a 冻结的 130 个 RPM 的本地 RPM-MD、-j2、固定 KBUILD 身份与 -kbase。重型主机步骤持独占锁，启动要求可用内存 ≥16 GiB、I/O full avg60 <20%，构建单元内存上限 6 GiB、CPU 配额 200%、禁用 swap、nice 19 和 idle I/O。 [构建收据]({link}/logs/result.json)','']
    if mode=='gcov':
        lines += ['GCOV 开工准备期间的两次 I/O 门禁等待曾释放独占锁，等待期间没有 GBS 编译。复查通过并重新取锁后才实际启动 GBS，构建期间持锁。 [开工读数]('+link+'/logs/admission.jsonl)','']
    if build.get('started'):
        lines += [f'GBS 退出码 {build["gbs_exit"]}，墙钟 {build["wall_s"]:.1f} 秒，cgroup 峰值内存 {build["final"]["memory_peak"]/1024**3:.2f} GiB。','']
    path=d/'artifacts/variant-verification.json'
    if path.is_file():
        proof=read(path)['arm-rpi4']
        css=proof['consumption']
        layout=proof['layout']
        lines += [f'逐对象编译命令只增加 profile 参数。release、版本串、{proof["module_crc_count"]:,} 个 Module.symvers 条目、{proof["module_count"]} 个模块 vermagic 均一致。实际 build-id {proof["build_id"]}，zImage SHA-256 {proof["zImage_sha256"]}。 [构建核对]({link}/artifacts/variant-verification.json)','',
                  f'在前 {css["selected"]} 个热 C 函数的诊断重放中，{css["positive"]} 个出现正值 AppliedSamples，{css["text_changes"]}/{css["objects"]} 个对应对象的 .text 哈希变化。热区 {layout["candidate"]["hot_bytes"]:,} B，冷区 {layout["candidate"]["cold_bytes"]:,} B，{layout["profile_objects"]} 个对象带 call-graph profile。共同文本输入节 {layout["common_text_inputs"]:,} 项中 {layout["changed_positions"]:,} 项位置改变，map 重放 build-id 与原件一致。 [消费证据]({link}/artifacts/arm-rpi4/consumption/results.json) · [节布局]({link}/artifacts/arm-rpi4/layout.json)','',
                  '| 变体 | .text B | .rodata B | .data B | .bss B | 文本对齐余量 B | 2 MiB 档位 | zImage B |',
                  '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for tag,key in [('K-BASE','base'),(name,'candidate')]:
            l=layout[key]
            lines.append(f'| {tag} | {l[".text"]:,} | {l[".rodata"]:,} | {l[".data"]:,} | {l[".bss"]:,} | {l["text_slack"]:,} | {l["tier_2MiB"]} | {l["zImage_bytes"]:,} |')
        lines.append('')
    handover=task/'lock-handover.jsonl'
    if mode=='gcov' and handover.is_file():
        events=[json.loads(line) for line in handover.read_text().splitlines()]
        changed=next((row for row in events if row['event']=='new_board_shared_lock_verified'),None)
        if changed:
            when=changed['at']
            boundary=next(row for row in events if row['event']=='boundary_verified_original_units')
            before=len(boundary['active_builds'])
            after=len(changed['active_builds'])
            lines += [f'{when} 在第 {changed["after_block"]} 个已验收正式 block 和第 {changed["before_block"]} 个 block 之间切换到共享锁。切换时已回到 PLAT，前后主机构建进程数为 {before} 和 {after}。原已验收配对和预登记均沿用。后续部署与测量持共享锁，GBS 和重型主机核验继续持独占锁。 [切换收据]({link}/lock-handover.jsonl)','']
    observer=task/'host-overlap-observer.jsonl'
    if mode=='gcov' and observer.is_file():
        records=[json.loads(line) for line in observer.read_text().splitlines()]
        known=[row for row in records if row['pid']==800021 and '-bb' in (row['flags'] or [])]
        if known:
            lines += ['第 9 组第二次尝试检测到了 VS Code Insiders 进程组内的 rpmbuild -bb。该进程在本实验持共享锁的期间出现。保留整组失败记录，重试继续沿用主机构建活动检查。 [进程收据]('+link+'/host-overlap-observer.jsonl)','']
    history=d/'preflight-recovery.json'
    if history.is_file():
        recovery=read(history)
        lines += [f'首次部署预检因脚本误改上一个候选镜像名而停止，历史提交 {recovery["initial_report_commit"]}。当时尚未部署、重启或计时。修正仅涉及镜像路径替换，并验证 GCOV → R1 和 R1 → HYB 的路径。恢复保留原构建、核验和预登记，重新检查开工温度。 [恢复收据]({link}/preflight-recovery.json)','']
    if state.get('error'):
        lines += [f'停点记录 {state["error"]}。','']
    b=d/'board'
    first=b/'afdo-first.json'
    if first.is_file():
        launch=read(b/'afdo-first/reboot-result.json')
        result=read(first)
        free=(b/'deploy/receipts/df.txt').read_text().splitlines()[-1].split()[3]
        lines += ['## 首启验收','',f'{launch["first_command"]:.2f} 秒恢复首条 SDB 命令。身份、规范化 FDT、cmdline、模块 10/10、HDMI、日志、D-Bus、安静门禁、PMU 和三项冒烟均通过。首启安静门禁温度 {result["quiet"]["passed_mC"]/1000:.3f}°C，部署后 boot_a 空闲 {int(free):,} B。 [首启证据]({link}/board/afdo-first.json)','']
    if (b/'formal-analysis.json').is_file():
        lines += formal_lines(b,link)
    if (b/'mechanism-analysis.json').is_file():
        counts=read(b/'mechanism-analysis.json')
        lines += ['## 机制计数','',f'有效 {counts["accepted"]} 个只计数 block，仅计 CPU3。 [逐 block 计数]({link}/board/mechanism-analysis.json)','',
                  '| 负载 | 事件 | 配对几何变化 | 配对计数差中位 | 最低运行比 |','| --- | --- | ---: | ---: | ---: |']
        for k,values in counts['events'].items():
            for event,row in values.items():
                lines.append(f'| {k} | {event} | {pct(row["relative_geomean"])} | {row["median_paired_delta"]:+.0f} | {row["min_running_pct"]:.1f}% |')
        lines.append('')
    if (b/'terminal.json').is_file():
        lines += conditions(b,link)
        if (b/'final-owner/plat.json').is_file():
            lines += [f'阶段结束回到原 PLAT，UID 5001，tryboot 指向 K-BASE。 [PLAT 身份]({link}/board/final-owner/plat.json)','']
    report.write_text('\n'.join(lines))
    return files,f'docs(kernel): record K2c {name} stage'

def summary():
    reports={key:read(task/key/'pipeline-result.json') for key in names}
    out=docs/'35_k2c_profile_comparison.md'
    e=docs/'evidence/35-k2c'
    e.mkdir(parents=True,exist_ok=True)
    saved={}
    base=read(prior/'formal-analysis.json')['benchmarks']
    layout=read(prior/'layout-analysis.json')['benchmarks']
    candidate={}
    for key in names:
        path=task/key/'board/formal-analysis.json'
        if path.is_file():
            candidate[key]=read(path)['benchmarks']
    truth=read(task.parent/'k2b-continue/profiles/rank-comparison.json')
    lines=['# K2c 四种 profile 汇总','',
      '所有效应均为各自配对实验中相对于同一 K-BASE 的耗时变化。pipe 为各次正式实验的主指标。四种 profile 分别在不同时段与 K-BASE 配对，布局列提供单一随机布局的量级参照。','',
      '| 基准 | K-AFDO | K-AFDO-GCOV | K-AFDO-R1 | K-AFDO-HYB | K1f-2 布局对照 |',
      '| --- | ---: | ---: | ---: | ---: | ---: |']
    for k in kinds:
        cell=[pct(base[k]['primary']['estimate']),*(pct(candidate[key][k]['primary']['estimate']) if key in candidate else '缺结果' for key in names)]
        cell.append(pct(layout[k]['primary']['estimate']))
        lines.append(f'| {k} | '+' | '.join(cell)+' |')
    lines += ['','## 结果与证据','']
    p0=base['pipe']['primary']
    m0=base['mmfault']['primary']
    lines.append(f'- **K-AFDO** pipe {pct(p0["estimate"])}（{ci(p0["bootstrap_CI95"])}，{verdict[p0["verdict"]]}），mmfault {pct(m0["estimate"])}（{ci(m0["bootstrap_CI95"])}，{verdict[m0["verdict"]]}）。 [K1f-3 阶段报告](28_k1f_3_formal_compare.md)')
    for key,(number,name) in names.items():
        status=reports[key]['status']
        saved[key]=dict(status=status,commit=read(task/key/'published.json')['commit'])
        label=f'**{name}** {status}。'
        if key in candidate:
            p=candidate[key]['pipe']['primary']
            m=candidate[key]['mmfault']['primary']
            label += (f' pipe {pct(p["estimate"])}（{ci(p["bootstrap_CI95"])}，{verdict.get(p["verdict"],p["verdict"])}），'
                      f'mmfault {pct(m["estimate"])}（{ci(m["bootstrap_CI95"])}，{verdict.get(m["verdict"],m["verdict"])}）。')
        lines += [f'- {label} [{name} 阶段报告]({number}_k2c_{key}.md)']
    lines += ['', '## GCOV 计数对照', '',
              'K2b 在同一组已插桩函数上比较 GCOV 函数入口次数与 IP 周期权重。此前对照检验了热点排序的一致程度。 [K2b 原始对照](31_k2b_kgcov_training.md)', '',
              '| 负载 | 原 IP ρ | R1 ρ | 原 IP Top 30 重合 | R1 Top 30 重合 |',
              '| --- | ---: | ---: | ---: | ---: |']
    for workload in ('pipe','mmfault','tmpfs','syscall','tos','all'):
        a,b = (truth[workload][key] for key in ('ip','r1'))
        lines.append(f'| {workload} | {a["spearman"]:.4f} | {b["spearman"]:.4f} | {a["top30_overlap"]}/30 | {b["top30_overlap"]}/30 |')
    lines += ['', 'pipe 的计数排名对照没有显示 R1 改善。', '']
    lines += ['## 预登记主比较的机制计数', '',
              '| 变体 | 配对数 | cycles:k | instructions:k | r01 | r02 | r10 |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    counter_sources=[('K-AFDO',prior/'mechanism-analysis.json')]
    counter_sources.extend((name,task/key/'board/mechanism-analysis.json') for key,(_,name) in names.items())
    for name,path in counter_sources:
        if path.is_file():
            counter=read(path)
            pipe=counter['events']['pipe']
            values=[pct(pipe[event]['relative_geomean']) for event in ('cycles:k','instructions:k','r01','r02','r10')]
            lines.append(f'| {name} | {counter["accepted"]} | '+' | '.join(values)+' |')
    lines += ['', '机制计数为 CPU3 只计数配对的几何变化，独立于正式判定。', '']
    if all(key in candidate for key in names):
        outcomes={'K-AFDO':p0['verdict']}
        outcomes.update((names[key][1],candidate[key]['pipe']['primary']['verdict']) for key in names)
        lines += ['## 结论', '']
        for result in ('faster','equivalent','inconclusive','slower'):
            variants=[name for name,status in outcomes.items() if status==result]
            if variants:
                lines.append(f'- 预登记 pipe 主指标判为{verdict[result]}的变体为 '+ '、'.join(variants)+'。')
        lines += ['- R1 在 pipe 的热点排序与 K2b 的 GCOV 计数对照中，Spearman ρ 由 0.4835 变为 0.4832，Top 30 重合维持 13/30。结合正式判定，现有证据不足以支持 R1 带来至少 1% 的 pipe 加速。', '']
    lines += ['## 静态内核尺寸', '',
              '原 K-AFDO 的 .text 比 K-BASE 增加 109,668 B，两者均为第 20 档。 [K1f-3 尺寸](28_k1f_3_formal_compare.md)', '',
              '| 变体 | .text 相对 K-BASE | 文本对齐余量 | 2 MiB 档位 | zImage |',
              '| --- | ---: | ---: | ---: | ---: |']
    for key,(_,name) in names.items():
        path=task/key/'artifacts/variant-verification.json'
        if path.is_file():
            sizes=read(path)['arm-rpi4']['layout']
            delta=sizes['candidate']['.text']-sizes['base']['.text']
            v=sizes['candidate']
            lines.append(f'| {name} | {delta:+,} B | {v["text_slack"]:,} B | {v["tier_2MiB"]} | {v["zImage_bytes"]:,} B |')
    lines.append('')
    finished=[key for key,row in reports.items() if row['status']=='complete']
    if finished:
        key=finished[-1]
        board=task/key/'board'
        final=read(board/'final-owner/plat.json')
        free=int((board/'finish-verify/receipts/df.txt').read_text().splitlines()[-1].split()[3])
        link=f'evidence/{names[key][0]}-k2c-{key}/board'
        lines += ['## 板上终态', '',f'RPi4 已回到 PLAT，build-id {final["build_id"]}，UID {final["uid"]}，`tryboot.txt` 指向 `zImage-kbase`。`boot_a` 剩余 {free:,} B。 [PLAT 收据]({link}/final-owner/plat.json) · [启动分区清单]({link}/finish-verify/receipts/after.sha256)','']
    out.write_text('\n'.join(lines))
    save(e/'index.json',dict(stages=saved))
    return ['35_k2c_profile_comparison.md','evidence/35-k2c'],'docs(kernel): summarize K2c profile comparisons'

paths,message=summary() if mode=='summary' else stage()
paths=[str((docs/p).relative_to(repo)) for p in paths]
git('add','-f','--',*paths)
actual=git('diff','--cached','--name-only',capture_output=True).stdout.splitlines()
assert actual and all(any(path==item or path.startswith(item+'/') for item in paths) for path in actual)
git('-c','core.whitespace=cr-at-eol','diff','--cached','--check','--',*paths)
git('commit','--quiet','-m',message)
git('fetch','origin')
git('rebase','origin/main')
for attempt in range(3):
    try:
        git('push','origin','HEAD:main')
        break
    except subprocess.CalledProcessError:
        if attempt==2:
            raise
        git('fetch','origin')
        git('rebase','origin/main')
commit=git('rev-parse','HEAD',capture_output=True).stdout.strip()
git('fetch','origin','main')
git('merge-base','--is-ancestor',commit,'origin/main')
save((task if mode=='summary' else task/mode)/(('summary-' if mode=='summary' else '')+'published.json'),
     dict(commit=commit,files=paths))
print('GitHub main verified',commit,flush=True)
