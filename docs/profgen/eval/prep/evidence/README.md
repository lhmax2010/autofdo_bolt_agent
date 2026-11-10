# 证据使用

仅静态 ELF/DWARF 和 C 构建覆盖参考，无正式 sample profile。

- 每个任务目录：command.json为实际argv、scope资源级别；result.json为真实退出码、耗时、原始输出SHA；resources.json为运行中读取的cgroup memory.peak和MemAvailable。
- FFmpeg lcov完整stdout以stdout-000.txt等按字节顺序分片；stdout.parts.json / lcov-storage.json记录拼接SHA。可按索引顺序拼接恢复原路径再复算。
- *-coverage-tables与*-inventory-tables：CSV包含JSON数组字段时须用csv.reader，再json.loads该字段。index.json给出每片SHA及原派生JSON的SHA。完整ELF dump通过索引的platform command再生；不需要任何sample profile。
- 派生JSON先由coverage_reference.py/dwarf_inventory.py生成，再由pack_static_evidence.py存为CSV小文本；只移除本轮生成的冗余中间JSON，不删除任何原始输入。
- input-sha256.json：显式允许的输入及哈希。没有递归扫描第一轮S目录。
- artifact-sha256.json：本轮产物、代码的最终SHA；该文件本身不自引用。
- coverage-summary.json的summary_differences是尚未闭合的跨视图差异，不是DA与segments不一致。
- audit结果是预筛查，不是完整身份对应表，更不是可排除清单。
- 脚本初稿和证据用于恢复调查；未通过完整N.5 #13/#16验收，不可用于修订3登记。
