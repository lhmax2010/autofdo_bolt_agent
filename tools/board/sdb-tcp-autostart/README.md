# Tizen 有线联网和 TCP SDB 开机准备工具

面向使用 ConnMan、Tizen systemd 244 的 socket activation 和原厂 `sdbd_tcp.socket` / `sdbd.service` 的实验板。参考环境是 RPi4 的 Tizen 11.0 Unified `20261104.160709`（ConnMan 1.42，sdbd 3.0.50）。预期适用于具备相同 unit、ConnMan Ethernet provisioning 和持久可见的 `/var/lib/connman` 的镜像。其他 Tizen 发行版、Wi-Fi、USB gadget 路径及 SELinux/SMACK 策略差异需要单独核对。

## 入口

- `verify IPV4 PORT INTERFACE` 在目标上运行，只读查询接口、监听和 systemd 启动关系。退出 0 表示现有端点应保留，退出 1 表示本次查询未找到端点，退出 2 表示已有部分配置或查询不完整，需要人工核对。识别现有端点时会确认 ConnMan 与厂商 TCP socket 的启动链接，遇到其他实现的监听也保留。使用 TCP 的 SDB 已可用时，可将脚本通过 shell 标准输入传给目标，无需落盘。
- `install --root DIR --cidr IPV4/PREFIX --port PORT --interface IFACE [--gateway IPV4]` 在主机上读取离线镜像树并打印改动清单。加 `--apply` 才写入该树。应先完成只读核对。安装到任何板前须另行取得用户批准。
- `uninstall --root DIR` 在主机上预览回退。加 `--apply` 才按清单回退。操作系统根 `/` 不是有效目标。实际离线根树和持久目录要在同一离线视图中，且管理文件的父目录需为真实目录。

```sh
./verify 192.0.2.7 26101 eth0
./install --root /path/to/offline-tizen --cidr 192.0.2.7/24 --port 26101 --interface eth0 --gateway 192.0.2.1
./uninstall --root /path/to/offline-tizen
```

地址、前缀、接口、端口和网关由使用者指定。示例地址仅作说明。从主控位于另一子网的实验网访问时，应给匹配的返程网关。同网段可以省略。使用唯一的保留地址，避免 IP 冲突。

## 改动与回退

| 路径 | 功能 |
| --- | --- |
| `/var/lib/connman/k1-sdb-tcp-ethernet.config` | 针对所选接口配置有线静态 IPv4。ConnMan 沿用镜像已有的开机启动。 |
| `/etc/systemd/system/sdbd_tcp.socket.d/70-k1-lab-listener.conf` | 把厂商 TCP socket 绑定到实验 IPv4、端口、接口。FreeBind 允许 socket 在 ConnMan 配置地址之前打开，接口仍由 systemd 设备依赖约束。 |
| `/etc/systemd/system/sockets.target.wants/sdbd_tcp.socket` | 复用镜像已有的 socket 与 sdbd 服务、安全标签及配置。 |
| `/etc/systemd/system/.k1-sdb-tcp-autostart.json` | 在任何配置写入前持久化清单，包括原状态、新 SHA-256、文件模式和需新增的目录。 |

工具选择仅新增文件。它识别厂商 wants 链接，检测到现有 SDB 启动项、覆盖文件或 ConnMan Ethernet 配置时会保留它们。新文件的原状态以 `null` 记录，符号链接的新 SHA 针对链接目标文本。安装可用同一参数恢复部分写入。卸载先验证已出现的每项新 SHA 和类型，再恢复原始缺省状态并逐项复核。外部修改或目录新增内容会阻止自动回退。重复卸载会报告缺少清单。离线 staging 不会启动、停止或 reload 运行的任何服务。

## 风险和现场验证

TCP SDB 是远程调试入口，限用隔离实验网和已批准主控。工具没有密码、密钥或额外凭据，不改变 Tizen 开发模式条件。网口标签、SMACK 访问与完整实际开机需另行验证。离线 apply 前保留可启动的原始镜像并确认现场控制台可用。若首次开机无法联网，通过控制台核对现有 ConnMan 和 socket，离线运行 `uninstall --apply` 回退，再按批准流程启动。正在运行的设备不应用此离线编辑流程。

主机测试使用 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v`。测试在临时样例树验证 dry-run、幂等、续跑、已有配置保护和 SHA 回退。实际板上只运行了只读 `verify`。本轮没有授权安装。

- [ConnMan provisioning 格式](https://kernel.googlesource.com/pub/scm/network/connman/connman/+/1d8f060cb6ea86c0f90f633cb37c3b542bfbd244/doc/config-format.txt)
- [systemd.socket 的监听和设备绑定](https://www.freedesktop.org/software/systemd/man/252/systemd.socket.html)
