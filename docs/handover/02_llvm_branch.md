# LLVM 分支只读查询与 workflow 设计入库

2026-11-14，结果仓库入口 main=`32237219967019e6c2e39a4d3808bbb05ff4b213`。本轮未执行 sdb、构建、质量矩阵或性能测量，未打开真实 sample profile，未推送任何 LLVM/Gerrit 分支，未创建 hq。所有查询串行在 nice19/ionice-c3、3GiB/100% scope 中执行，启动前 MemAvailable≥4GiB。URL用户名/令牌已打码，不修改认证。

## 1. 结论与执行分支

- Gerrit 项目：`platform/upstream/llvm`；地址 `ssh://<redacted>@review.tizen.org:29418/platform/upstream/llvm`。
- `src/llvm` 当前本地分支 **tizen_base**、跟踪 **origin/tizen_base**，HEAD=`f999bd406c0a70fe8107aa992164fe6945c5d46a`。本地跟踪引用尚在旧值，不能只看 `status -sb` 判断远端没有前进。
- 远端只读实查 `refs/heads/tizen_base` tip=**61ef5d31ca91025c414c748477bef0c64ddfa67c**；旧基线是其祖先，新增3个提交（含1个merge）。因此触发用户指定分支门禁：**第一次提交并推送后，第三部分仅登记三.1范围决定，随后停止；不创建发布树、不应用发布补丁、不构建、不回归。等待PM决定是否基于新tip重放。**
- `accepted/tizen_base`、`accepted/tizen_base_x` 的远端tip仍为f999bd40。它们不替代本地明确跟踪的tizen_base，不据此绕过门禁。
- `temp/llvm-profgen-enh` 是同一源码库的开发worktree，分支 **afdo/profgen-enhance**，HEAD=`15a5ec3f46283ad2eccaecf97b2eac2a0e43d65c`，无上游跟踪分支。保留spec本地测试修改及全部未跟踪构建清单，未撤销任何内容。

## 2. 两个工作树的命令输出

以下每条均使用命令级 `-c gc.auto=0 -c maintenance.auto=false`。无上游查询返回128是已知状态，不是网络认证失败。branch输出的`+`表示该分支在另一worktree检出。

### `src/llvm`：`git branch -vv`

退出码：0。

```text
+ afdo/profgen-enhance 15a5ec3f4628 (/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/llvm-profgen-enh) [llvm-profgen] Exclude IP samples with missing non-leaf callsite lines
* tizen_base           f999bd406c0a [origin/tizen_base] Revert clang bootstrap + ThinLTO, fall back to GCC
```

### `src/llvm`：`git status -sb`

退出码：0。

```text
## tizen_base...origin/tizen_base
```

### `src/llvm`：`git rev-parse HEAD`

退出码：0。

```text
f999bd406c0a70fe8107aa992164fe6945c5d46a
```

### `src/llvm`：`git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`

退出码：0。

```text
origin/tizen_base
```

### `src/llvm`：`git remote -v`

退出码：0。

```text
origin	ssh://<redacted>@review.tizen.org:29418/platform/upstream/llvm (fetch)
origin	ssh://<redacted>@review.tizen.org:29418/platform/upstream/llvm (push)
```

### `src/llvm`：`git branch -r --contains f999bd406c0a70fe8107aa992164fe6945c5d46a`

退出码：0。

```text
  origin/accepted/tizen_base
  origin/accepted/tizen_base_x
  origin/sandbox/fangyu.he/kubuds_optimize
  origin/tizen_base
```

### `temp/llvm-profgen-enh`：`git branch -vv`

退出码：0。

```text
* afdo/profgen-enhance 15a5ec3f4628 [llvm-profgen] Exclude IP samples with missing non-leaf callsite lines
+ tizen_base           f999bd406c0a (/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/src/llvm) [origin/tizen_base] Revert clang bootstrap + ThinLTO, fall back to GCC
```

### `temp/llvm-profgen-enh`：`git status -sb`

退出码：0。

```text
## afdo/profgen-enhance
 M packaging/llvm.spec
?? debugfiles.list
?? debuglinks.list
?? debugsourcefiles.list
?? debugsources.list
?? elfbins.list
?? llvm-debuginfo.manifest
?? llvm-debugsource.manifest
?? llvm.manifest
?? mlgo_verify_assets/
```

### `temp/llvm-profgen-enh`：`git rev-parse HEAD`

退出码：0。

```text
15a5ec3f46283ad2eccaecf97b2eac2a0e43d65c
```

### `temp/llvm-profgen-enh`：`git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`

退出码：128。

```text
fatal: no upstream configured for branch 'afdo/profgen-enhance'
```

### `temp/llvm-profgen-enh`：`git remote -v`

退出码：0。

```text
origin	ssh://<redacted>@review.tizen.org:29418/platform/upstream/llvm (fetch)
origin	ssh://<redacted>@review.tizen.org:29418/platform/upstream/llvm (push)
```

### `temp/llvm-profgen-enh`：`git branch -r --contains f999bd406c0a70fe8107aa992164fe6945c5d46a`

退出码：0。

```text
  origin/accepted/tizen_base
  origin/accepted/tizen_base_x
  origin/sandbox/fangyu.he/kubuds_optimize
  origin/tizen_base
```

## 3. 远端查询、基线所属与 sandbox 命名参考

执行：`git -C src/llvm ls-remote origin 'refs/heads/*'`；仅查询，没有在src/llvm或开发worktree fetch，也不改其refs。GIT_TERMINAL_PROMPT=0、ssh BatchMode=yes避免交互索取凭据；仍使用既有认证。

查询时间：`2026-11-14T16:05:31.346096+08:00`；exit=0；stderr为空；返回144个heads，含53个sandbox名字。远端原始stdout SHA-256：`1f4348dd0897c2143b8f4d1c58fb08d40f9afbf1ecfdfe5926baa302d2499032`。

旧基线在本地已知远端引用的包含关系见上节 `branch -r --contains`；它只是已缓存历史，不是全部远端祖先关系的实时枚举。独立fetch额外证明f999bd40是当前tizen_base tip祖先。

非sandbox远端heads完整快照：

```text
da4a2839d80ac52958be0129b871beedfe90136e	refs/heads/5_0
d488f5bb9039453c1988aa71df3291343c0a0cfd	refs/heads/5_0_monorepo
3ab1c6c46b8ad3dab8b2adf6218ff83dc6a0afff	refs/heads/aarch64_ilp32
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/accepted/tizen/ivi/genivi
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/accepted/tizen/ivi/stable
e402f33c508c1c8703837022b2af762b709869cc	refs/heads/accepted/tizen_10.0_base
e402f33c508c1c8703837022b2af762b709869cc	refs/heads/accepted/tizen_10.0_base_mr
e402f33c508c1c8703837022b2af762b709869cc	refs/heads/accepted/tizen_10.1_base
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/accepted/tizen_3.0.2014.q3_common
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/accepted/tizen_3.0.m14.3_ivi
0635323e7e5e8b311e33026dcbe92d877cd3ef94	refs/heads/accepted/tizen_3.0.m2_base
0635323e7e5e8b311e33026dcbe92d877cd3ef94	refs/heads/accepted/tizen_3.0_base
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/accepted/tizen_3.0_ivi
d1571fe8b803fddaf77aa042910fdd27439ecbcd	refs/heads/accepted/tizen_4.0_base
fd838714af57b671533acefa14e7610045ea61f2	refs/heads/accepted/tizen_5.0_base
8649f27ca9065631cc2958aaf138662f17a536b9	refs/heads/accepted/tizen_5.5_base
cb219cd7e0ddb7a24d8cff7c4deed9a12c6f1c06	refs/heads/accepted/tizen_5.5_base_mobile_hotfix
9543676f257463a2cfacee4117ca67f5a407ebd2	refs/heads/accepted/tizen_5.5_base_wearable_hotfix
7b5b85e4e458240b5732290222dd0753053948fd	refs/heads/accepted/tizen_6.0_base
b7e6617743230bab62dd2b3b3f1ba54634549993	refs/heads/accepted/tizen_6.0_base_tool
728f25df8347841482bef649372e2a244c7e9044	refs/heads/accepted/tizen_6.0_base_tool_hotfix
3576b70d4b0d152ba1b463f1e8a1ae1c16d55f85	refs/heads/accepted/tizen_6.5_base
5486b0b541ae01001a7db710dd5ff986ede0acfb	refs/heads/accepted/tizen_6.5_base_tool
135dca9a97dd27ac926fb4511fab394a5d23a814	refs/heads/accepted/tizen_7.0_base
135dca9a97dd27ac926fb4511fab394a5d23a814	refs/heads/accepted/tizen_7.0_base_hotfix
ed14c368bfb4aa61b0b79b3dcd3f0cb87d8ce404	refs/heads/accepted/tizen_7.0_base_tool
ed14c368bfb4aa61b0b79b3dcd3f0cb87d8ce404	refs/heads/accepted/tizen_7.0_base_tool_hotfix
0245a0d6448c073e22204a8937d4f7c24807f38f	refs/heads/accepted/tizen_8.0_base
043cffcae527f038beafb4d0b3ad7931b81d773b	refs/heads/accepted/tizen_9.0_base
f999bd406c0a70fe8107aa992164fe6945c5d46a	refs/heads/accepted/tizen_base
043cffcae527f038beafb4d0b3ad7931b81d773b	refs/heads/accepted/tizen_base_asan
cb67996861d070d68fec2b4c623eed7d20ba2e23	refs/heads/accepted/tizen_base_dev
e78041f2aa3df8efce837e5a7cc9df5a7dd0f919	refs/heads/accepted/tizen_base_riscv
cb67996861d070d68fec2b4c623eed7d20ba2e23	refs/heads/accepted/tizen_base_sc
0245a0d6448c073e22204a8937d4f7c24807f38f	refs/heads/accepted/tizen_base_test
0245a0d6448c073e22204a8937d4f7c24807f38f	refs/heads/accepted/tizen_base_tool
c691a60fe5ed816dbe1d909c6e8936572e5a1100	refs/heads/accepted/tizen_base_tool_dev
cb67996861d070d68fec2b4c623eed7d20ba2e23	refs/heads/accepted/tizen_base_toolchain
f999bd406c0a70fe8107aa992164fe6945c5d46a	refs/heads/accepted/tizen_base_x
c97476acc22f955339bae02dc6cc064eec0095d9	refs/heads/accepted/tizen_base_x_asan
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/accepted/tizen_common
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/accepted/tizen_generic
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/accepted/tizen_ivi
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/accepted/tizen_mobile
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/accepted/tizen_tv
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/accepted/tizen_wearable
2c8418b0f8576425c086862887da2cf822b72556	refs/heads/backup/tizen_base
a9739522938496d72cd9fa06853ce242e0b1dcd8	refs/heads/devel_backup
075f6a6892ebaddc796ba606f7459de4be401039	refs/heads/develop_backup
a5d93708875f4b701c5e2085691b2917b3f631bd	refs/heads/pristine-tar-3.8
233a7612f95eb58dc8af6ec865df8312773a8548	refs/heads/sanbox/kaic/dev
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/tizen
e402f33c508c1c8703837022b2af762b709869cc	refs/heads/tizen_10.0_base
e402f33c508c1c8703837022b2af762b709869cc	refs/heads/tizen_10.1_base
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/tizen_3.0.2014.q3_common
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/tizen_3.0.2014.q4_common
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/tizen_3.0.2015.q1_common
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/tizen_3.0.2015.q2_common
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/tizen_3.0.m14.2_ivi
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/tizen_3.0.m14.3_ivi
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/tizen_3.0.m1_mobile
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/tizen_3.0.m1_tv
0635323e7e5e8b311e33026dcbe92d877cd3ef94	refs/heads/tizen_3.0.m2_base
0635323e7e5e8b311e33026dcbe92d877cd3ef94	refs/heads/tizen_3.0_base
b9fdfa6602883f23859631ec2373dc51e2f7ac01	refs/heads/tizen_3.0_ivi
d1571fe8b803fddaf77aa042910fdd27439ecbcd	refs/heads/tizen_4.0_base
bed5819e659719daab9c0a27bc6f32bc4795ec7d	refs/heads/tizen_4.0_tv
fd838714af57b671533acefa14e7610045ea61f2	refs/heads/tizen_5.0_base
8649f27ca9065631cc2958aaf138662f17a536b9	refs/heads/tizen_5.5_base
cb219cd7e0ddb7a24d8cff7c4deed9a12c6f1c06	refs/heads/tizen_5.5_base_mobile_hotfix
9543676f257463a2cfacee4117ca67f5a407ebd2	refs/heads/tizen_5.5_base_wearable_hotfix
cb219cd7e0ddb7a24d8cff7c4deed9a12c6f1c06	refs/heads/tizen_5.5_tv
7b5b85e4e458240b5732290222dd0753053948fd	refs/heads/tizen_6.0_base
728f25df8347841482bef649372e2a244c7e9044	refs/heads/tizen_6.0_base_hotfix
3576b70d4b0d152ba1b463f1e8a1ae1c16d55f85	refs/heads/tizen_6.5_base
135dca9a97dd27ac926fb4511fab394a5d23a814	refs/heads/tizen_7.0_base
ed14c368bfb4aa61b0b79b3dcd3f0cb87d8ce404	refs/heads/tizen_7.0_base_hotfix
0245a0d6448c073e22204a8937d4f7c24807f38f	refs/heads/tizen_8.0_base
043cffcae527f038beafb4d0b3ad7931b81d773b	refs/heads/tizen_9.0_base
61ef5d31ca91025c414c748477bef0c64ddfa67c	refs/heads/tizen_base
a71244988ca36db4cf269c65ad1cf860f8172c21	refs/heads/tizen_base_15.0.7
07b7ee1197c46342c8b0b8486d42e1b6936318d7	refs/heads/tizen_base_19.1.4
157ff194b1acebec5a9ca7bb3af66c3c45d11847	refs/heads/tizen_base_21.1.1
79386b0d70fa25191cc890738153e32aa1271bcd	refs/heads/tizen_base_dev
fd7a4929c0e424d564cdd1f0c55af9153dcea321	refs/heads/tizen_base_next
d860bd21c282d949117b5c9b73865809e1c5aacc	refs/heads/tizen_ivi_genivi
57b71fcd136e5ce8a2cd191d6bd07aaa6bc73219	refs/heads/toolchain_upgrade
aadaa00de76ed0c4987b97450dd638f63a385bed	refs/heads/upstream
d32170dbd5b0d54436537b6b75beaf44324e0c28	refs/heads/upstream-10.0.0
960f60c8c4616f9a5dc72cc5fef803175d797c06	refs/heads/upstream-3.8
d488f5bb9039453c1988aa71df3291343c0a0cfd	refs/heads/upstream-5.0.2
```

本项目可见sandbox分支**仅列名称**，不选择或推送其中任何一个：

```text
refs/heads/sandbox/Pusha/329225-4
refs/heads/sandbox/Pusha/330332-1
refs/heads/sandbox/Pusha/clang
refs/heads/sandbox/Pusha/test
refs/heads/sandbox/Pusha/with_link
refs/heads/sandbox/Pusha/with_ninja
refs/heads/sandbox/adrians/upgrade-to-6.x
refs/heads/sandbox/denis13/LTO
refs/heads/sandbox/dkson95/build
refs/heads/sandbox/dkson95/clang
refs/heads/sandbox/dkson95/libc++
refs/heads/sandbox/dkson95/lld
refs/heads/sandbox/dkson95/mlgo
refs/heads/sandbox/fangyu.he/custom_mlgo_model
refs/heads/sandbox/fangyu.he/dev_optimize_llvm
refs/heads/sandbox/fangyu.he/kubuds_optimize
refs/heads/sandbox/fangyu.he/llvm_opt
refs/heads/sandbox/fangyu.he/llvm_optmize
refs/heads/sandbox/fangyuhe/libomp
refs/heads/sandbox/giuliana/x86_baselibs
refs/heads/sandbox/hoegeun/devel
refs/heads/sandbox/hoegeun/llvm-static
refs/heads/sandbox/jolfzverb/fix_5.1
refs/heads/sandbox/kaic/omp
refs/heads/sandbox/lhmax2025/bolt_pgo
refs/heads/sandbox/lhmax2025/libcxx-ehabi-backport
refs/heads/sandbox/lhmax2025/libcxx-migration
refs/heads/sandbox/lhmax2025/lld
refs/heads/sandbox/lhmax2025/llvm_only_clang
refs/heads/sandbox/lhmax2025/llvm_optimize
refs/heads/sandbox/lhmax2025/mlgo
refs/heads/sandbox/lhmax2025/mlgo_aot
refs/heads/sandbox/liushanshan/lld
refs/heads/sandbox/liushanshan/llvm_upgrade
refs/heads/sandbox/lstelmach/tizen_riscv_base
refs/heads/sandbox/mkashkarov/disable_asan
refs/heads/sandbox/mkashkarov/tizen_6.0_build
refs/heads/sandbox/nmerinov/llvm
refs/heads/sandbox/rpietruch/bpf-support
refs/heads/sandbox/v.solomin/21.1
refs/heads/sandbox/v.solomin/21.1.1
refs/heads/sandbox/v.solomin/clang-links
refs/heads/sandbox/v.solomin/clang-links-19
refs/heads/sandbox/v.solomin/mb_len_max
refs/heads/sandbox/v.solomin/ninja
refs/heads/sandbox/vbarinov/clang
refs/heads/sandbox/vbarinov/clang-path
refs/heads/sandbox/vbarinov/clean-clang
refs/heads/sandbox/vbarinov/fix-check
refs/heads/sandbox/vbarinov/newspec
refs/heads/sandbox/vbarinov/tizen_base
refs/heads/sandbox/vbarinov/tizen_base_new
refs/heads/sandbox/vbarinov/upstream
```

`sanbox/kaic/dev` 是远端实际拼写，不属于 `refs/heads/sandbox/*`，未把它算进sandbox命名参考。以上名字只说明命名惯例，既不是本任务的新分支，也不是用户已批准的目标。sandbox分支名与推送人仍待确认。

## 4. 独立克隆中的新增提交

为满足A.3，仅新建 `temp/llvm-upstream-query-20261114/`：先从WORKDIR/src/llvm本地 `git clone --no-checkout`（独立refs；Git本地克隆可以硬链接不可变对象），再在此克隆执行：

```text
git fetch --no-tags <既有Gerrit-URL> refs/heads/tizen_base:refs/remotes/query/tizen_base
git merge-base --is-ancestor f999bd406c0a70fe8107aa992164fe6945c5d46a 61ef5d31ca91025c414c748477bef0c64ddfa67c
```

clone/fetch/祖先检查均exit0。该目录是查询克隆，**不是发布树**，没有checkout、git am或构建。src/llvm及开发worktree共用refs的查询前后`git show-ref`逐字节一致，SHA-256=`666e48824690abf59d95c11107cb37cf8de96e9f3928d7dce54e916cfb2c6dac`。

完整新增提交（提交日期为Git记录，不按日期推断实际远端合入时间）：

```text
cf4b6777d056131e2534ecb460c5575327d99646 2026-10-16T11:24:26+09:00 Revert "Revert clang bootstrap + ThinLTO, fall back to GCC"
13c3e223d9e1b35e4affb55255c5042f8c940f35 2026-11-02T22:22:34+09:00 packaging: classify -feliminate-unused-debug-types and mirror recorded backend policy
61ef5d31ca91025c414c748477bef0c64ddfa67c 2026-11-11T04:28:07+00:00 Merge "packaging: classify -feliminate-unused-debug-types and mirror recorded backend policy" into tizen_base
```

逐提交按第一父提交的路径变化核对；merge另说明其内容来自合入：

| 提交 | 路径 | llvm-profgen源码 | CommandGuide/llvm-profgen.rst | packaging/llvm.spec |
|---|---|---|---|---|
| cf4b6777d056131e2534ecb460c5575327d99646 | 新增packaging/llvm-static-archives-native.py；修改packaging/llvm.spec | 无 | 无 | **有** |
| 13c3e223d9e1b35e4affb55255c5042f8c940f35 | 修改packaging/llvm-static-archives-native.py | 无 | 无 | 无 |
| 61ef5d31ca91025c414c748477bef0c64ddfa67c | merge；相对第一父提交修改同一native脚本 | 无 | 无 | 无 |

第一个提交撤销旧基线的“回退GCC”提交，涉及bootstrap/ThinLTO打包策略。没有profgen源码路径改动不意味着新tip发布构建等同于旧基线；本轮不试重放、不修改spec，留给PM决定基线。

## 5. afdo/profgen-enhance 是否推送过

可核实结论：本地开发分支无upstream；两worktree只配置同一Gerrit origin；本次远端heads没有 `refs/heads/afdo/profgen-enhance`，没有以开发HEAD `15a5ec3f…` 为tip的head。本任务没有任何LLVM push。既有补丁1–9实施报告和[PM交接](01_pm_handover_report.md)均记录仅本地提交/导出、不推LLVM或Gerrit；仓库可审计执行记录中没有该开发分支的推送。

**历史证明边界**：客户端配置、当前ls-remote和执行报告不能证明“所有操作者、任何已删除或不可见远端历史上从未发生push”。未取得服务器审计日志，因此不把“当前不存在”伪装成绝对历史证明。项目现有证据支持它一直仅本地使用；如必须取得绝对证明，需由远端管理员提供审计，不通过试推送验证。

## 6. workflow设计入库

只处理指定源文件 `/home/linhao/Downloads/01_afdo_bolt_workflow_design_v0.1.md`，执行mv至 `docs/workflow/01_afdo_bolt_workflow_design_v0.1.md`，Downloads原文件已不存在。移动前/后SHA-256均为 **`cf935c5344067faba8f296bd508e871aad2428d9ebc416d42e2482ff5601699f`**，正文未修改。目标：[workflow设计v0.1](../workflow/01_afdo_bolt_workflow_design_v0.1.md)。新建 `docs/workflow/reviews/.gitkeep` 供后续评审意见入库，本轮不生成评审意见。§14明确Gerrit sandbox与GitHub orphan hq的发布边界，本轮只登记规则、不创建hq。

## 7. 取证位置、停止点

原始查询记录位于 `temp/llvm-branch-query-20261114/`：`local.json`（URL打码）、`remote-heads.json`、`clone.json`、`fetch.json`、`upstream-delta.json`、`commit-paths.json`、`source-refs-before.txt`/`after.txt`、`design-move.json`。本报告已给出远端可读的必要命令输出、全部增量与分支清单，temp原件不进入结果仓库；没有LLVM源码树入库。

第一批提交仅STATUS、本报告、workflow设计、reviews/.gitkeep，推送main供评审方读取。第二批按门禁只登记有限范围交付决定与STATUS引用，然后停止。构建墙钟/发布工具/新回归结果均**未产生**，不得引用旧补丁9验收冒充本轮发布验收。原开发树及旧证据保留不变；不登记修正案3。
