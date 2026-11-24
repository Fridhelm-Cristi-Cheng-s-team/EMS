# 统一接口索引

**A-side Design Baseline V0.1 · REVIEWED / NOT FROZEN**

| Interface ID | 当前契约 | Producer | Consumer | 状态 | 来源任务 | 最近明确修订 | B 方依赖 |
|---|---|---|---|---|---|---|---|
| I01 | [任务目标与阶段转换](system_interfaces.md#i01-任务目标与阶段转换) | S1 | S2 | PROPOSED | A‑V3‑02A | A‑V3‑02AR | 无正式 B 方端口 |
| I02 | [飞行状态和目标反馈](system_interfaces.md#i02-飞行状态和目标反馈) | S2 | S1 | PROPOSED | A‑V3‑02A | A‑V3‑02AR | 有关联，见 [02C](ab_interface_pending.md) |
| I03 | [EMS 任务上下文](system_interfaces.md#i03-ems-任务上下文) | S1 | S3 | PROPOSED | A‑V3‑02A | A‑V3‑02AR | 无正式 B 方端口 |
| I04 | [EMS 可选飞行上下文](system_interfaces.md#i04-ems-可选飞行上下文) | S2 | S3 | PROPOSED | A‑V3‑02A | A‑V3‑02B | 无正式 B 方端口 |
| I05 | [推力请求及机体运动](system_interfaces.md#i05-推力请求及机体运动) | S2 | S4 A 方推进 | PROPOSED | A‑V3‑02A | A‑V3‑02BR | 有关联，见 [02C](ab_interface_pending.md) |
| I06 | [实际推进载荷与推进能力](system_interfaces.md#i06-实际推进载荷与推进能力) | S4 A 方推进 | S2 | PROPOSED | A‑V3‑02A | A‑V3‑02BR | 有关联，见 [02C](ab_interface_pending.md) |
| I07Q | [环境查询](system_interfaces.md#i07q-环境查询) | S2 | S5 | PROPOSED | A‑V3‑02A | A‑V3‑02A | 无正式 B 方端口 |
| I07 | [飞机环境输入](system_interfaces.md#i07-飞机环境输入) | S5 | S2 | PROPOSED | A‑V3‑02A | A‑V3‑02AR | 无正式 B 方端口 |
| I08 | [A 方动力系统环境输入](system_interfaces.md#i08-a-方动力系统环境输入) | S5 | S4 A 方模块 | PROPOSED | A‑V3‑02A | A‑V3‑02B | 有关联，见 [02C](ab_interface_pending.md) |
| I09 | [实验配置与初始化控制](system_interfaces.md#i09-实验配置与初始化控制) | S6 | S1–S5 A 方各系统 | PROPOSED | A‑V3‑02A | A‑V3‑02B | 有关联，见 [02C](ab_interface_pending.md) |
| I10 | [实验状态及记录](system_interfaces.md#i10-实验状态及记录) | S1–S5 A 方各系统 | S6 | PROPOSED | A‑V3‑02A | A‑V3‑02B | 有关联，见 [02C](ab_interface_pending.md) |
| I11 | [EMS 监督策略](energy_interfaces.md#i11-ems-监督策略) | S3 | S4 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 有关联，见 [02C](ab_interface_pending.md) |
| I12 | [能源及推进反馈](energy_interfaces.md#i12-能源及推进反馈) | S4 | S3 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 有关联，见 [02C](ab_interface_pending.md) |
| I13 | [电池端口](energy_interfaces.md#i13-电池端口) | 电池 ↔ 电池侧变换器 | 同左，按契约双向 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 无正式 B 方端口 |
| I14 | [电池支路与公共网络](energy_interfaces.md#i14-电池支路与公共网络) | 电池侧变换器 ↔ 公共网络 | 同左，按契约双向 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 无正式 B 方端口 |
| I15 | [公共网络与电驱](energy_interfaces.md#i15-公共网络与电驱) | 公共网络 ↔ 电驱 | 同左，按契约双向 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 有关联，见 [02C](ab_interface_pending.md) |
| I16 | [电机与共享推进轴](energy_interfaces.md#i16-电机与共享推进轴) | 电驱 ↔ 共享轴 | 同左，按契约双向 | PROPOSED | A‑V3‑02B | A‑V3‑02B | 无正式 B 方端口 |
| I17 | [共享推进轴与螺旋桨](energy_interfaces.md#i17-共享推进轴与螺旋桨) | 共享轴 ↔ 螺旋桨 | 同左，按契约双向 | PROPOSED | A‑V3‑02B | A‑V3‑02B | 无正式 B 方端口 |
| I18 | [推进需求与执行目标](energy_interfaces.md#i18-推进需求与执行目标) | S4 来流/需求/执行 | S4 各消费模块 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 无正式 B 方端口 |
| I19 | [部件能力及推进能力](energy_interfaces.md#i19-部件能力及推进能力) | S4 物理模块/能力形成 | S4 能力形成/执行反馈 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 有关联，见 [02C](ab_interface_pending.md) |
| I20 | [能源初始化及实验记录](energy_interfaces.md#i20-能源初始化及实验记录) | S6 ↔ S4 各能源模块 | 同左，按契约双向 | PROPOSED | A‑V3‑02B | A‑V3‑02BR | 有关联，见 [02C](ab_interface_pending.md) |

[I01–I10 与 I07Q](system_interfaces.md) · [I11–I20](energy_interfaces.md) · [历史报告索引](../history/README.md)

I07Q 为环境查询方向。公共时序、状态及失效规则见[统一规范](interface_standard.md)。
