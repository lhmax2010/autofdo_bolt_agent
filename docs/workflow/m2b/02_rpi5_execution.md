# M2b 阶段 B · RPi5 启动前核对与停止记录

**停止点：依赖冻结前。** 两套指定快照的元数据 URL 均返回 HTTP 404，Base 的目标架构 compiler-rt RPM 原址也返回 404。M2a 冻结仓库中的 109 个 RPM 全部通过 SHA 校验，且每个 SHA 在原固定快照的已归档 primary 中有匹配记录。该集合缺少本轮新增的 compiler-rt。未用其他快照或同版本异 SHA 的 RPM 替代。[执行证据](evidence/rpi5-stage-b-preflight.json)

## 板子和 job

- 唯一连接 `192.168.108.13:26101`。预先只读断言取得 `Raspberry Pi 5 Model B Rev 1.1`、`aarch64`、内核 `6.12.80-arm64-rpi4-v8`、`tizen-unified-toolchain_20261118.083201`、UID `5001`，与 M2a 锁定身份一致。板上有 `gst-inspect-1.0`、`gst-launch-1.0`。
- 从真实媒体重新 init，补齐原始 `missing_for_run`，绑定 M2a 发布工具、aarch64 perf、媒体及 AFDO profile SHA `db4d4c196cde3afb20803580ed5317d83a7d4a95f0d8f830c5394f1536b99d5a`。源码在独立检出的 `5fe76358596f66e955f005094e6f34ca525ab23d`，应用并验证 PGO 补丁，构建环境目录另建。
- `doctor --job` 为 13 项 ok，missing、mismatch、unknown 均为 0；主机工具 SDB 为 4.2.36，M2a 记录为 4.2.25，本轮只用于只读核验。doctor 验证主机及锁文件，不检查在线快照是否可取。已 review 并设 `draft=false`，`run --dry-run --stop-after rebuild` 显示 preflight、build、deploy、collect、convert、rebuild 六个阶段。正式运行目录和收据尚未创建。
- 最终只读复核 UID 5001、CPU governor `schedutil`、RPM 数 1230，两次相同。`/opt/afdo_agent` 不存在。本轮未切换 root 或 governor、未部署、未创建清理待办、未持有 GBS 共享锁、未启动 GBS。

## 指定快照与新增依赖

| 取证对象 | 结果 |
| --- | --- |
| Base `tizen-base-toolchain_20261030.120529` 的 repomd | 两次 GET HTTP 404 |
| Unified `tizen-unified-toolchain_20261104.125239` 的 repomd | GET HTTP 404 |
| Base aarch64 `compiler-rt-22.1.8-4.1.aarch64.rpm` | 原址 HEAD 与范围 GET 均为 HTTP 404 |
| 同名 RPM 在 Base 公开目录其余七个快照下的查询 | 七个 URL 均为 HTTP 404，只用于寻找原 SHA 的字节 |
| M2a 冻结仓库 | 109/109 RPM 的文件 SHA 与原快照 metadata 匹配；缺 compiler-rt |
| 本机可用包 | 现有 M2a/交付冻结仓库和 RPM 归档未找到该 aarch64 RPM |

缺少的 RPM 必须符合原始 Base 元数据，SHA-256 为 `396c1e890736844acb981cb52f1a044d945022bcd8170d5ca6f5b538af9c7981`。预期 109 → 110 尚未实现。既有 Tizen `rpmspec` 对 aarch64 的 BASE、AFDO、PGOGEN、PGO 分别核验，BuildRequires 均为 `clang` 与 `compiler-rt = 22.1.8-4.1`。仅 PGO 的展开脚本含按目标同步编译输出设置。

## 执行范围

| 要求 | 状态 |
| --- | --- |
| 正式 S0 与 S1 依赖冻结 | 未启动，缺精确锁定的新增包 |
| BASE、PGOGEN、AFDO、PGO、BASE-r 构建与 runtime 门禁 | 未执行 |
| PLAT oracle、三轮 BBB 训练、profraw 清单 | 未执行 |
| profdata 合并、版本、覆盖率和前 20 个函数 | 未生成 |
| 实际警告、构建锁、目标 `.text`、非计时正确性 | 未审计；警告门禁已在主机实现并用夹具校验 |
| 板上清理与共享锁 | 只读复核通过；无本轮部署产物、待办或持锁 |
| measure | 未开始 |

## 主机回归

完整工作流测试 249/249 通过，含 8 项新增警告或来源测试。M1 封存运行回放 48/48 通过。首轮全量执行因稀疏 worktree 缺夹具位置而失败；添加必要的只读夹具路径后完成复验。既有 x86_64 合成 PGOGEN 对象的真实 `__llvm_prf_names` 解码出各自的函数名。阶段 B 的 ARM 构建日志与真实前 20 函数归属仍待实跑。

已锁定 job 与原始记录保存在 WORKDIR 的 `temp/m2b-stage-b-20261125/`，路径和 SHA 见证据索引。
