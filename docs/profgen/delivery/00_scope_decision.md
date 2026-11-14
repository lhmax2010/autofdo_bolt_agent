# 第一批有限范围交付决定

用户批准日期：2026-11-14。本文件登记范围决定，不代表发布构建或交付验收已完成。设计v1.8正文保留原样。

## 1. 用户决定原文

1. llvm-profgen 增强按"第一批有限范围交付"收尾：交付补丁 1–9 的用户态 DWARF IP 路径（aarch64；armv7l Thumb-2/A32）。
2. 不修改 CLI：--ip-aggregation 仍必须显式给出；head、zero-fill、skid 保持现有默认 none。调用方（workflow）显式传入 --ip-aggregation=max --ip-skid=none --ip-zero-fill=none --ip-head-samples=none，称为"显式保守策略"，不得称"默认值已验证"。
3. 三个质量门槛保持可选，工具不设默认；门槛政策由 workflow 的各包配置决定。
4. 设计 §10 步骤 5（5.8 质量矩阵）、步骤 6（5.9 性能与过期复用）、步骤 7（第二阶段冻结）延期，不取消；交付文档须写明 "统计质量等价与性能收益未验证"。性能收益改由 AutoFDO workflow 的端到端 A/B 测量，之后据此再决定默认值。
5. 预注册材料全部保留；将来若登记修正案 3，workflow 期间在相同对象上生成或查看过的 profile 须按 Q.5 第 17 项披露。
6. 本次交付不含：pseudo-probe、--perfdata、内核 profile、BOLT。
7. 设计文档 v1.8 不修改。

## 2. 受影响的设计条款索引

依据：[设计v1.8](../design/02_llvm_profgen_enhance_design_v1.8.md)，SHA-256 `ae667bd61470118179f6876c912285b7c57ab22518640c2af9f42103ad428e59`。

| 条款 | 本决定的关系 | 不得扩大的结论 |
|---|---|---|
| §10步骤5 / §5.8 | 正式质量矩阵延期；保留既有静态产物、模拟、预注册与披露 | 模拟开关true不等于正式质量等价通过；不计算未授权受控量 |
| §10步骤6 / §5.9 | 性能与过期复用延期；性能收益交由workflow端到端A/B测量 | 统计质量等价与性能收益未验证；不能声称过期复用已验收 |
| §10步骤7 / §12 | 第二阶段冻结延期；显式保守策略不改CLI默认值或门槛 | 不称默认值已验证；保留后续默认值/阈值决策 |
| §10步骤8 | probe子方案不在本次交付内 | 不能把DWARF路径验收外推到probe |
| §10步骤9 | 有限范围发布仍需干净补丁序列、原样spec、正常非增量GBS、产物身份与回归、非★局限登记 | 既有开发树增量验收不能替代本轮发布验收 |
| 附录Q.5（含第17/19项） | 全部准备材料保留，当前不登记修正案3；以后同对象profile生成/查看须披露 | workflow期间的数据接触不豁免将来预注册披露，也不自动授权正式质量矩阵 |

支持范围中的armv7l Thumb-2/A32与aarch64沿用补丁1–9已验收契约；本决定未授权修改补丁、放宽身份或边界规则、恢复CLI自动默认、改三个质量门槛。BOLT属于后续workflow设计范围，不属于本次profgen有限交付。

## 3. 本轮分支门禁与停止点

第一批规则/分支查询/workflow设计已提交并推送：`e0beb1bce1a067cc2be0ea9d0817cd7967325155`。[只读查询报告](../../handover/02_llvm_branch.md)

- 本地src/llvm的tizen_base与补丁起点：`f999bd406c0a70fe8107aa992164fe6945c5d46a`。
- 查询时Gerrit `platform/upstream/llvm` 的 `refs/heads/tizen_base`：`61ef5d31ca91025c414c748477bef0c64ddfa67c`，新增3提交，包含packaging/llvm.spec修改。
- 依据用户明确的分支判断，本轮第三部分**只完成三.1**。没有创建 `temp/llvm-profgen-release/`，没有git am，没有GBS构建，没有发布RPM/工具，没有C1/IP回归或新lit结果。
- 未撤销/改动开发树的spec测试修改。查询clone `temp/llvm-upstream-query-20261114/`只用于读取远端增量，不是发布树。
- `01_release.md`尚不生成，避免把未执行步骤写成发布报告；第二次提交仅本范围决定与STATUS。后续是否基于新tip重放补丁、以及相应发布构建基线，由PM决定。
- 当前Gerrit sandbox项目为 `platform/upstream/llvm`；分支与推送人待确认，commit ID待推送。本轮不推送任何LLVM/Gerrit引用、不创建hq，不接板，不登记修正案3，不运行质量矩阵或性能测量。

完成本登记并推送后停止，等待基线裁决；这不是有限范围发布已经完成的声明。

## 4. 发布基线（PM决定，2026-11-14）

发布基线采用 `f999bd406c0a70fe8107aa992164fe6945c5d46a`（即查询时 accepted/tizen_base 与 accepted/tizen_base_x 的 tip；也是补丁1–9开发与验收所用基线），不基于 tizen_base 新 tip `61ef5d31ca91025c414c748477bef0c64ddfa67c` 构建。

理由：新增3个提交只改打包（重新启用clang bootstrap + ThinLTO及相关脚本），不涉及llvm-profgen；以已接受快照为基线，发布验收可与既有证据直接对应，避免把打包策略变化混入本次交付。

新增提交为：`cf4b6777d056131e2534ecb460c5575327d99646`（修改llvm.spec并新增native静态归档脚本）、`13c3e223d9e1b35e4affb55255c5042f8c940f35`（修改该脚本）、`61ef5d31ca91025c414c748477bef0c64ddfa67c`（合并提交）。路径核查见[分支报告](../../handover/02_llvm_branch.md)。

本决定解除第3节的分支停止门禁。允许在独立临时树对61ef5d31依次git am补丁1–9做前向兼容核对（不构建、不改补丁）；发布树从src/llvm本地克隆并检出f999bd40，按原序应用同一补丁，保留git am产生的提交作为未来sandbox候选。原开发树及其中spec测试改动保持原状。本轮允许执行已授权的正常非增量GBS、产物身份和固定回归；仍不接板、不推任何LLVM/Gerrit分支、不登记修正案3、不计算质量受控量。
