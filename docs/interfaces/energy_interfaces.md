# 能源系统内部接口契约

**A-side Design Baseline V0.1 · REVIEWED / NOT FROZEN**

[接口索引](interface_index.md) · [统一规范](interface_standard.md) · [验证计划](../verification/verification_plan.md)

以下仅列当前有效信号。段落声明提供接口编号、方向、状态和来源。逐行继承统一规范的时钟、数据有效性、所有权、恢复及证据规则。C/P/E/I/L 为连续、周期、事件、初始化及日志，D1/D2/D6 为标量/二维/六维 double，E1 为枚举，B1 为布尔，ID 为标识，Bus 为具名结构。R 必需，R* 为启用条件下必需，O 可选。尺寸/位宽、具体物理上下限、周期和阈值待定（TBD）。

## I11 EMS 监督策略

Producer S3 → Consumer S4。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑01。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 11‑01 `batteryPolicyWindow` | S3，方向许可、策略区间及独立的常规/授权回退权限 | W、B1，Bus | 电池网络端，放正、充负，许可与区间相容 | I/P，首策略或获准默认处置就绪 | 与硬界求交，回退只在触发、范围、期限和恢复均成立时执行 | R · V‑B04/V‑B12/V‑B04R/V‑B12R · — | PROPOSED | A‑V3‑02B, BR‑01 |
| 11‑02 `reserveAndChargeIntent` | S3，SOC 目标、储备、计划充电意图、可偏离双源监督目标 | 1、W、s，Bus | SOC 0–1，充电负向，目标与许可分列 | I/P，选用项附时域，可未提供 | 硬界有效，储备只按明确授权回退；到期撤出对应意图 | 储备 R*，其余 O · V‑B05/V‑B11 · — | PROPOSED | A‑V3‑02B |
| 11‑03 `policyMeta` | S3，策略 ID、版本、模式、优先级、起止及逐项授权依据 | ID、s、枚举，Bus | 同运行，授权注明触发、截止和恢复 | I/P/E，校验后采纳 | 到期撤回关联授权。独立批准回退、限载或停止 | R · V‑B04/V‑B12/V‑B04R/V‑B12R · A 方授权 | PROPOSED | A‑V3‑02B, BR‑01 |
| 11‑04 `generationScheduleIntent` | S3，内部发电调度请求及可选正常启停意图 | W、枚举，Bus | 候选净供能口径，供给 A 为正，具有有效期 | I/P/E，配置初始请求 | 与实际交换分开；B 方正式转发及握手待 02C | 调度 R*，启停 O · V‑B11 · 02C | PROPOSED | A‑V3‑02B |

## I12 能源及推进反馈

Producer S4 → Consumer S3。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑02/03/04/05。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 12‑01 `propulsionDemand` | S4，唯一正式准稳态电需求、原请求、采纳及设备限制状态 | W、N、ID，Bus | 电驱入口取电正；设备有效域，未按当前供能限载 | P，首个适用工作点后发布 | 越域保留原请求，报告未知或经验证的设备边界，并说明限值 | R · V‑B09/V‑B13/V‑B09R · 桨/电驱图 | PROPOSED | A‑V3‑02B, BR‑02 |
| 12‑02 `drivePowerExecution` | S4，可执行功率目标和实际电驱入口功率 | W，Bus | 同一入口、请求关联，目标及实测时刻分开 | P/E，初始化与物理工作点相容 | 实际失效揭示状态，保留既有限制 | R · V‑B02/V‑B09 · — | PROPOSED | A‑V3‑02B |
| 12‑03 `batteryActual` | 电池持有 SOC，支路持有实际值；供可选可用能量估计 | 1、W、J，Bus | 电池网络端放正充负，能量注条件 | P，来自同一电池及网络求解点 | 实际失效与估计失效独立；撤出无效可选项 | SOC/实际功率 R，能量 O · V‑B01/V‑B02 · 电池参数 | PROPOSED | A‑V3‑02B |
| 12‑04 `batteryCapability` | S4，当前代数、持续、峰值和策略后范围，附证据及类型 | W、s、K、ID、枚举，Bus | 电池网络端、方向、起始状态、假设、模型/限制来源、空集或未知 | P/E，分别记时域、生成时刻和有效期 | 过期不放宽；峰值缺证据标未知，条件估计明确标注 | 基础 R，短时 O · V‑B03/V‑B04/V‑B10/V‑B03R/V‑B18/V‑B19 · 电池及变换参数 | PROPOSED | A‑V3‑02B, BR‑04 |
| 12‑05 `networkBalanceStatus` | S4 网络，可行类别、请求缺额/过剩及实际残差 | W、s、ID、枚举，Bus | 公共网络；差额非负，残差有符号，实际残差只属有效实际点 | P/E，先求可行初值再发布 | 区分硬无解、策略不可行、授权回退、未知与数值失败；保留最后有效引用 | R · V‑B02/V‑B05/V‑B06/V‑B05R/V‑B06R/V‑B14R · 02C 实供 | PROPOSED | A‑V3‑02B, BR‑05 |
| 12‑06 `policyExecutionStatus` | S4，策略采纳、限制、回退授权、原因及证据，可选热限制 | ID、枚举、s、K，Bus | 同一次策略执行，热量注明测点 | P/E，初始待采纳或已确认，状态变化发布 | 有效期独立；过期或求解失败不作恢复 | 状态 R，热 O · V‑B04/V‑B12/V‑B14R · 热模型可选 | PROPOSED | A‑V3‑02B, BR‑05 |
| 12‑07 动态推进需求及配对差值（正式字段名 TBD） | S4，同源动态总需求、准稳态配对差值和预测起点 | W、s、ID，Bus，可选曲线 | 电驱入口，同一请求和参考条件，设备可行且未按当期供能限载 | P，估计单独声明预测及有效期 | 越域/过期退到有效 12‑01，配对失效不发差值，不入实际账 | O · V‑B09R/V‑B17 · 轴惯量及响应参数 | PROPOSED | A‑V3‑02B, BR‑03 |

S3/S4 的实际发电交换、发电能力及燃油信息为 [02C 依赖](ab_interface_pending.md)。不在本接口定义 B 方正式信号。

## I13 电池端口

Producer / Consumer 电池 ↔ 电池侧变换器。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑06。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 13‑01 `batteryTerminalPoint` | 电池拥有端模型，S4 支路共同求 U、I 和实际 P，记录候选根与选中支路 | V、A、W、s、ID，Bus | 电池端，离开电池正，P=UI，一组共同势/流变量 | C，初态与 SOC 匹配 | 校验根、端压流、方向及工作支路；不适用根拒绝，端口不可用显式反馈 | R · V‑B01/V‑B03/V‑B03R/V‑B20 · Rint 标定 | PROPOSED | A‑V3‑02B, BR‑06 |
| 13‑02 `terminalHardEnvelope` | 电池，端压、端流及功率硬域和时间证据 | V、A、W、s、ID，Bus | 电池端，充放电方向及状态条件分开 | C/P，随当前状态求解或有据保持 | 过期不扩界，峰值须有另证 | R · V‑B03/V‑B03R/V‑B20 · 电池参数 | PROPOSED | A‑V3‑02B, BR‑06 |

## I14 电池支路与公共网络

Producer / Consumer 电池侧变换器 ↔ 公共网络。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑07/14。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 14‑01 `batteryBusExchange` | A 方支路/网络共同求实际交换，可选同一 V/I | W、V、A，Bus | 公共网络电池支路，注入正；端到网络差为变换损耗及储能 | C，初态满足共同平衡 | 守恒用单一实际值；无可行交换反馈，无虚构能量 | R；V/I R* · V‑B02/V‑B03/V‑B13R · 变换特性 | PROPOSED | A‑V3‑02B, BR‑14 |
| 14‑02 `batteryBranchLimits` | 支路发布端口至网络端的当前、持续或峰值约束及证据映射 | W、s、ID、枚举，Bus | 网络端双向范围，带同一损耗与时域口径 | C/P/E，初态校验方向域 | 缺证据标未知，峰值限时及恢复由支路执行 | R · V‑B03/V‑B04/V‑B18/V‑B19/V‑B20 · 变换特性 | PROPOSED | A‑V3‑02B, BR‑07 |

## I15 公共网络与电驱

Producer / Consumer 公共网络 ↔ 电驱。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑08/14。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 15‑01 `driveElectricalExchange` | S4 联立实际值，电驱拥有取电关系 | W、V、A，Bus | 入口取电正，启用显式端口时 P=VI | C，初态核对轴功与损耗 | 供能受限收紧执行量，无效实际输入按物理边界处置 | R；V/I R* · V‑B02/V‑B07/V‑B13R · 电驱参数 | PROPOSED | A‑V3‑02B, BR‑14 |
| 15‑02 `driveSupplyConstraint` | 网络拥有可交付范围，电驱拥有设备约束，含工作支路与限制 | W、V、A、ID，Bus | 同入口，当期求解域，能力与实测分开 | C/P/E，初态核对适用域 | 上一解须在本时刻重检，失效保持已有约束或报不可用 | R · V‑B02/V‑B06/V‑B10/V‑B06R/V‑B14R · 02C 实供 | PROPOSED | A‑V3‑02B, BR‑08 |

## I16 电机与共享推进轴

Producer / Consumer 电驱 ↔ 共享轴。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md)。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 16‑01 `motorShaftPort` | 电驱拥有实际转矩，轴拥有转速；机械功率派生 | N·m、rad/s、W，Bus | 电机机械输出，同旋转正向，P=τω | C，初值转矩与桨负载相容 | 低速有界转矩，越域明示；一致转速/转矩做功 | R · V‑B07/V‑B08/V‑B07R · 图谱、惯量 | PROPOSED | A‑V3‑02B |

## I17 共享推进轴与螺旋桨

Producer / Consumer 共享轴 ↔ 螺旋桨。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md)。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 17‑01 `propellerShaftPort` | 共享轴拥有转速，桨拥有负载转矩及实际桨轴功 | rad/s、N·m、W，Bus | 桨轴输入，正转阻力矩按取功为正 | C，初始工况合法 | 低速/风车用经验证模型，超域反馈不可用 | R · V‑B07/V‑B08/V‑B07R · 桨图、惯量 | PROPOSED | A‑V3‑02B |

## I18 推进需求与执行目标

Producer S4 来流/需求/执行 → Consumer S4 各消费模块。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑09/10。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 18‑01 `localPropulsionCondition` | S4，唯一派生局部入流、密度及来源；供需求/桨/能力 | m/s、kg/m³、ID，Bus | I05 与 I08 同源，轴向前正 | C/P，首个快照同源 | 错配重算，真实风缺失传播失效 | R · V‑B08/V‑B09 · 几何 | PROPOSED | A‑V3‑02B |
| 18‑02 `propulsionWorkPointRequest` | S4 需求，向网络/电驱发布候选推力、轴速、转矩和准稳态/设备可行轨迹及未限电需求 | N、rad/s、N·m、W、s，Bus | 设备包线，推进轴与电驱入口，I05 关联 | P，首有效工作点后发布 | 多解按批准支路，越域标未知或设备受限；不由当期受限转矩反推 | R · V‑B09/V‑B09R · 桨图及电驱图 | PROPOSED | A‑V3‑02B, BR‑09 |
| 18‑03 `executableDriveTarget` | S4 执行，向电驱发布经供能限制的可执行目标及原因 | W、N·m、rad/s、ID，Bus | 共同可行点，真实功率和转矩归 I15/I16 | C/P，模式和目标同版本 | 无效时走获准回退，保留原因 | R · V‑B06/V‑B07/V‑B09/V‑B07R · 参数与供能 | PROPOSED | A‑V3‑02B, BR‑09 |
| 18‑04 动态需求估计依据（正式字段名 TBD） | S4 需求，向 I12 发布/能力形成提供起算轴态、轨迹及设备限制 | rad/s、rad/s²、N·m、W、s、ID，Bus | 参考轨迹及损耗图有效域 | P，同一快照起算 | 假设失效撤出预测，不改变实际量 | O · V‑B17 · 响应、惯量和损耗图 | PROPOSED | A‑V3‑02B, BR‑10 |

## I19 部件能力及推进能力

Producer S4 物理模块/能力形成 → Consumer S4 能力形成/执行反馈。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑11/13。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 19‑01 `componentLimitsAndActuals` | 各源模块，发布状态、实际值、硬约束及能力时间证据的引用 | 原生 SI、s、ID，Bus | 沿 I13–I17 原实际端口；能力注明假设及时间类型 | C/P，同源一致 | 关键源缺失则对应能力未知，无重复实际源 | R · V‑B10/V‑B13/V‑B19 · 部件标定 | PROPOSED | A‑V3‑02B, BR‑11 |
| 19‑02 `propulsionCapabilityStatus` | S4，设备/能源硬/策略后范围，送 I06，区分当期、持续、动态可达 | N、s、ID，Bus | 轴向，注明假设、时域、持续/短时证据，空集/未知分开 | P/E，初始证据后发布 | 时域不匹配不作持续主张；过期不放宽，恢复按 02AR | 基础 R，动态 O · V‑B10/V‑B16/V‑B10R/V‑B19 · A 方模型、02C 真实供能 | PROPOSED | A‑V3‑02B, BR‑11 |

## I20 能源初始化及实验记录

Producer / Consumer S6 ↔ S4 各能源模块。状态 `PROPOSED`。来源 [02B](../history/A-V3-02B.md) · [02BR](../history/A-V3-02BR.md) BR‑12。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 20‑01 `energyInitialCondition` | S6 经 I09 提供候选，各模块持有自身初始状态 | 1、rad/s、J、K、ID，Bus | 初始 SOC、轴速、可选储能/热，匹配 S2 空中初态 | I，分别校验并设置 | 不一致拒绝，B 方联合初值留待 02C | R，附加 R* · V‑B15 · 参数、02C 联合初态 | PROPOSED | A‑V3‑02B |
| 20‑02 `energyReadyAndLog` | S4 各源拥有数据，由 I10 向 S6 发布就绪、拒绝、功率和储能等事件及日志 | SI、ID、枚举，Bus／通道集合 | 原测量点，真实及替身注明来源 | I/E/L，校验运行标识 | 日志失效单列，物理异常按场景处理 | R · V‑B13/V‑B15/V‑B16/V‑B13R · 配置 | PROPOSED | A‑V3‑02B, BR‑12 |
| 20‑03 工作点选解审计（正式字段名 TBD） | S4 向 S6 发布求解版本、支路、优先级结果及最终有效样本 | W、J、s、ID、枚举，Bus／日志 | 功率和能量为各原边界，区分无解、输入未知和数值失败 | I/E/L，依据点与残差关联 | 无可行点不接受物理步，保留终止及诊断，无日志在线反馈 | R · V‑B13R/V‑B14R · 数值版本 | PROPOSED | A‑V3‑02B, BR‑12 |
