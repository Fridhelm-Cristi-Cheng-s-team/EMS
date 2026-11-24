# 系统级接口契约

**A-side Design Baseline V0.1 · REVIEWED / NOT FROZEN**

[接口索引](interface_index.md) · [统一规范](interface_standard.md) · [验证计划](../verification/verification_plan.md)

以下仅列当前有效信号。段落声明提供接口编号、方向、状态和来源。逐行继承统一规范的时钟、数据有效性、所有权、恢复及证据规则。C/P/E/I/L 为连续、周期、事件、初始化及日志，D1/D2/D6 为标量/二维/六维 double，E1 为枚举，B1 为布尔，ID 为标识，Bus 为具名结构。R 必需，R* 为启用条件下必需，O 可选。尺寸/位宽、具体物理上下限、周期和阈值待定（TBD）。D01–D05 见 [02C 登记](ab_interface_pending.md)，D06 为 A 方能源/真实供能依赖，D07 为 A 方待标定参数和模型。AR‑12 已移除的旧字段只保留在 [02AR 修订记录](../history/A-V3-02AR.md)。

## I01 任务目标与阶段转换

Producer S1 → Consumer S2。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑01/02/19。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 01‑01 `missionPhase`, `phaseSeq` | S1，活动任务阶段及阶段版本 | 1，E1＋ID | 爬升、巡航、下降；正式转换后递增 | I/E/P，初始化校验并与目标版本原子发布 | 候选不更新活动阶段；旧版本丢弃 | R · T02/T03/T02R · — | PROPOSED | A‑V3‑02A |
| 01‑02 `activeTargetMode` | S1 持有请求组合，S2 持有实际飞控模式 | 1，E1 | 高度、对地升降率或空气航迹角候选 | I/E/P，首个目标组合须可解析 | 只激活一个垂向通道；模式切换遵守阶段或目标提交 | R · T03/T03R · — | PROPOSED | A‑V3‑02A |
| 01‑03 `trueAirspeedTarget` | S1，目标真空速 | m/s，D1 | 空气相对，非负且在模型有效域 | I/P，与活动目标同版本 | 组合越域时拒绝 | R · T03 · D07 | PROPOSED | A‑V3‑02A |
| 01‑04 `verticalTargetSet` | S1，激活高度、对地升降率或空气相对航迹角 | m、m/s、rad，Bus | 向上为正，空气航迹角按空气相对，按模式选一 | I/E/P，初始字段与模式一致 | 缺项、硬目标相冲突或参考系错配时拒绝 | R* · T03/T03R · D07 | PROPOSED | A‑V3‑02A |
| 01‑05 `flightConstraints`, `phaseProgressGoal` | S1，飞行限制及航程、终点或阶段进度 | m、m/s、rad、s，Bus | 航程依任务路线，守卫与硬目标各自有角色 | I/E/P，按场景激活 | 空约束交集报告不可行，守卫由 S1 执行 | 限制 R*，进度 O · T02/T03 · D07 | PROPOSED | A‑V3‑02A |
| 01‑06 `targetId`, `phaseTransition` | S1，提交、取消/替换及目标/阶段生效事件 | ID、s、E1，Bus | 匹配同运行候选、基准版本及生效点 | I/E，初始有目标 ID，最终就绪后在共同更新点一并提交 | 停止优先。无匹配就绪时保留仍有效的旧目标，否则降级或终止 | R，转换事件 R* · T02/T04/T02R/T11R/T13R · — | PROPOSED | A‑V3‑02A, AR‑02 |
| 01‑07 候选目标与转换记录（正式字段名 TBD） | S1，runId、transitionId、targetId、基准 phaseSeq/活动目标、候选阶段与目标和确认截止 | 1、s、目标原单位，Bus | 本运行唯一尝试，目标合法且共同生效点可用 | E，等待接受及最终重校验期限均来自候选 | 错配、取消或超时关闭；接受不保证达到 | R* · T02R/T03R/T04R · — | PROPOSED | A‑V3‑02A, AR‑01 |

按 [02AR](../history/A-V3-02AR.md) 的 S1/S2 状态机执行。S2 在同一逻辑更新点以旧目标下已形成的状态确认就绪，S1 再提交，S2 采纳，随后 S3 获取已提交上下文。提交后回执错配按协议异常。

## I02 飞行状态和目标反馈

Producer S2 → Consumer S1。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑03/04/05/19。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 02‑01 `missionFlightState` | S2，X、Z、真空速、地速、实际对地升降率 | m、m/s，Bus | 惯性位置及向上垂速，速度模非负 | P，初始化后同一有效快照 | 注明测量/估计通道；过期或缺失暂停相关守卫 | R · T02/T04/T15 · — | PROPOSED | A‑V3‑02A |
| 02‑02 `flightPathAngles` | S2，空气相对及对地航迹角 | rad，D2 | 相应速度方向，向上为正 | P，首个有效快照后 | 低速超域时独立失效 | O，守卫使用时 R* · T02/T09 · D07 | PROPOSED | A‑V3‑02A |
| 02‑03 `targetTracking` | S2，APPLIED、实际飞控模式、活动 targetId、跟踪/达到/不可持续 | 1、s、ID，Bus | 实际状态，跟踪归属活动目标 | P/E，先确认采纳，再发布实际跟踪 | 错配报告协议异常；过期暂停相关守卫。S1 决定转换 | R · T02/T03/T08/T02R/T03R/T13R · — | PROPOSED | A‑V3‑02A, AR‑04 |
| 02‑04 `propulsionLimited` | S2 发布对任务的影响，S4 拥有来源能力 | 1、s，Bus | 关联活动目标，区分当前未知、受限、恢复及历史约束 | P/E，随源和影响更新；初始未知可报告 | 过期不推断解除，S1 挂起有关守卫 | R · T08/T08R/T14 · D06 真源 | PROPOSED | A‑V3‑02A, AR‑05 |
| 02‑05 候选目标回执（正式字段名 TBD） | S2，接收、接受、拒绝、暂不可行、最终就绪或撤回 | ID、s、枚举，Bus | 匹配事务条目和证据快照，最终就绪限该时点 | E，校验与共同采纳点发布 | 过期或乱序只记录，截止关闭 | R* · T02R/T03R/T04R · — | PROPOSED | A‑V3‑02A, AR‑03 |

## I03 EMS 任务上下文

Producer S1 → Consumer S3。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑06。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 03‑01 `missionContext` | S1，已提交阶段、阶段版本及运行状态 | 1、s，Bus | 与目标提交版本一致 | I/E/P，同点采纳完成后发布 | 过期为阶段未知或反应式回退；待提交阶段不作为当前阶段 | 阶段感知 R*，反应式 O · T02/T05/T02R/T16 · — | PROPOSED | A‑V3‑02A, AR‑06 |
| 03‑02 `remainingMissionEstimate` | S1，预计剩余航程、时长和后续阶段 | m、s、1，Bus | 按任务路线，距离与时长非负 | P/E，可从未提供开始 | 计划变化使旧估计失效 | O · T05 · — | PROPOSED | A‑V3‑02A |
| 03‑03 `missionForecast` | S1 发布未来阶段、工况或注明来源的推进需求预测 | s、m、m/s、可选 W，Bus，长度 TBD | 按预测时域及工况，电预测须注明边界 | P/E，有算法及有效期时发布 | 和当前阶段独立；缺失或失效切回基础策略 | O · T05/T16 · D06 未来电需求 | PROPOSED | A‑V3‑02A, AR‑06 |

## I04 EMS 可选飞行上下文

Producer S2 → Consumer S3。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑07 · [02B](../history/A-V3-02B.md) E‑Δ04。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 04‑01 `flightContext` | S2，真空速、高度、实际垂速及需求变化摘要 | m/s、m、1，Bus | 高度及垂速向上，注明真值/测量/估计 | P，首个有效同源快照后 | 错配、过期则停用可选项 | O · T04/T05/T16 · — | PROPOSED | A‑V3‑02A, AR‑07 |
| 04‑02 `thrustRequestContext` | S2，原始推力及 requestId 副本 | N、ID，Bus | I05 同轴同号 | P，同源复制 | 仅研究上下文；正式电需求来自 S4 | O · T05/T06 · — | PROPOSED | A‑V3‑02A |
| 04‑03 `flightImpact` | S2，目标受推进限制的影响 | 1、s、ID，Bus | 与目标和请求关联，源和证据标识明确 | P/E，初始可未知 | 失效时退出可选通道 | O · T05/T08/T16 · D06 真源 | PROPOSED | A‑V3‑02A, AR‑07 |

## I05 推力请求及机体运动

Producer S2 → Consumer S4 A 方推进。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑08/09 · [02B](../history/A-V3-02B.md) E‑Δ01 · [02BR](../history/A-V3-02BR.md) BR‑14。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 05‑01 `thrustRequest` | S2，飞控希望的轴向推力 | N，D1 | 轴向前推正，首版非负请求候选 | I/P，初始设置经验证，保持至下一有效值或到期 | 约束执行及实际载荷由 S4 回报 | R · T06/T07/T08/V‑B09R · D07 | PROPOSED | A‑V3‑02A, E‑Δ01, BR‑14 |
| 05‑02 `propulsionRequestMeta` | S2，请求标识、源时间、有效期、活动目标或降级来源 | s、ID、枚举，Bus | 请求同一运行版本，生效顺序明确 | I/P，按采纳期限保持 | 乱序拒绝；过期撤出执行权，按批准回退或结束 | R · T04/T06/T04R/T07R/T15 · — | PROPOSED | A‑V3‑02A, AR‑08, E‑Δ01, BR‑14 |
| 05‑03 `mountKinematics` | S2，O 点对地速度、俯仰角及角速度、位姿引用 | m、m/s、rad、rad/s，Bus | 速度 B 系，位置 I 系，抬头正 | C，机体初始化后派生 | 连续量同刻；离散副本仅许可保持；无有效运动则来流不可用 | R · T04/T06/T09/T09R/T15 · D07 | PROPOSED | A‑V3‑02A, AR‑09, E‑Δ01 |
| 05‑04 `installationRef` | A 方 S2/集成，安装点、推进轴、固定点与版本 | m、1，Bus | 机体系同一安装基准，轴向归一 | I，双方同版本且运行内固定 | 错配阻止采纳 | R · T01/T06 · D07 | PROPOSED | A‑V3‑02A |

## I06 实际推进载荷与推进能力

Producer S4 A 方推进 → Consumer S2。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑10–15 · [02B](../history/A-V3-02B.md) E‑Δ02 · [02BR](../history/A-V3-02BR.md) BR‑13/14。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 06‑01 `actualPropulsionForceB` | S4，实际净推进力 Fx、Fz | N，D2 | 机体前/腹正，真实量可带符号 | C，初态由一致推进点形成 | 与 06‑02 同刻有效。仅经建模批准的限时保持，否则终止 | R · T06/T07/T07R/T15/V‑B16 · D06/D07 | PROPOSED | A‑V3‑02A, AR‑10, E‑Δ02, BR‑14 |
| 06‑02 `actualPitchMomentAtDatum` | S4，含安装力臂的 O 点净俯仰矩 | N·m，D1 | 固定机体点 O，抬头正，作用点与力同源 | C，与实际力同刻 | 基准错配拒绝，S2 仅换算到重心 | R · T06/T07/T07R/T15 · D07 | PROPOSED | A‑V3‑02A, AR‑10, E‑Δ02, BR‑14 |
| 06‑03 `axialThrustTracking` | S4，已采纳请求、可执行目标、实际轴向力及 ID | N、s、ID，Bus | 与推力请求同轴；实际力来自 06‑01 投影 | P，采样后发布，可执行目标初始未知 | 旧回执不解释新请求；过期按获准抗饱和回退 | R · T04/T07/T08/T07R/T08R · D06 | PROPOSED | A‑V3‑02A, AR‑11, E‑Δ02, BR‑14 |
| 06‑04 准稳态能力与 `limitStatus`（正式字段名 TBD） | S4，准稳态范围、适用条件与时域、有效性及限制状态/原因 | N、s、ID、枚举，Bus | 与 I05 同轴，空集与未知分开 | P/E，首个有效证据前未知，能力突变更新 | 过期不放宽；当期范围不得外推持续；按恢复守卫放宽 | R · T08/T08R/T14/V‑B10R/V‑B19 · D06/02C 时域 | PROPOSED | A‑V3‑02A, AR‑13, E‑Δ02, BR‑13 |
| 06‑05 `dynamicThrustCapability`, `applicationPoint` | S4，可选上升/下降能力及诊断作用点 | N/s、m、s，Bus | 说明适用区间和同轴方向，位置以 O 为参考 | P，有依据的动态域才发布 | 预测失效撤出；诊断作用点不重复计矩 | O · T06/T08/T17 · D06/D07 | PROPOSED | A‑V3‑02A, AR‑14, E‑Δ02 |
| 06‑06 瞬时可行范围（正式字段名 TBD） | S4，当前状态/同刻允许作用下的输出范围 | N、s、ID，Bus | 起始物理状态与约束明确，可退化为单点 | P/E，有可信来源后发布 | 与准稳态分列；失效回到有效基础接口 | O · T14/T17/V‑B10R · D06/D07 | PROPOSED | A‑V3‑02A, AR‑15, E‑Δ02, BR‑13 |
| 06‑07 有限时域可达能力（正式字段名 TBD） | S4，预测点、区间及近似类别 | N、s、ID，Bus | 起始状态、预测时域、工况、约束及证据；区间不保证任意共同轨迹 | P/E，随有效预测刷新 | 独立到期，撤出后沿用有效基础能力和既有限制 | O · T17/V‑B19 · D06/D07/02C 时域 | PROPOSED | A‑V3‑02A, AR‑15, E‑Δ02, BR‑13 |

## I07Q 环境查询

Producer S2 → Consumer S5。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md)。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 07Q‑01 `environmentQuery` | S2，飞机位置及共同求值时刻 | m、s，Bus | I 系 X、Z，高度向上，点在环境域 | C，可由初值做预查询 | S5 反馈越界，禁止默默替代 | R · T09/T11 · D07 | PROPOSED | A‑V3‑02A |

## I07 飞机环境输入

Producer S5 → Consumer S2。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑16/19。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 07‑01 `atmosphereTruth` | S5，密度、静压和绝对温度 | kg/m³、Pa、K，Bus | 查询位置大气，实数为正且处场景域 | C，初始化首个有效大气 | 越界传播原因，作为运行边界输入 | 密度 R，压温 R* · T09/T11 · D07 | PROPOSED | A‑V3‑02A |
| 07‑02 `windTruth`, `gustComponent` | S5，总风及可选阵风分量 | m/s，D2＋可选 D2 | I 系，总风包含已启用阵风 | C，初始场景和种子可追溯 | 未知风不可作零，阵风分解不再叠加 | 总风 R，分解 O · T09/T12/T09R · D07 | PROPOSED | A‑V3‑02A |
| 07‑03 `environmentValidity` | S5，状态及查询、位置、时刻、版本关联 | 1、s、ID，Bus | 本次求值与场景适用范围 | C/E，初态确认有效 | 错配拒绝并重发或重算，物理真值和测量分开处置 | R · T09/T11/T09R · D07 | PROPOSED | A‑V3‑02A, AR‑16 |

## I08 A 方动力系统环境输入

Producer S5 → Consumer S4 A 方模块。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑16/19 · [02B](../history/A-V3-02B.md) E‑Δ04。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 08‑01 `propulsionEnvironmentTruth` | S5，桨所需同源密度与总风 | kg/m³、m/s，Bus | 密度正，风 I 系，同源环境求值 | C，与初始运动时空对齐 | 失效或错配标记推进输入不可用；S4 从 I05/I08 唯一计算桨处来流 | R · T06/T09 · D07 | PROPOSED | A‑V3‑02A |
| 08‑02 `thermalAmbient` | S5，电机/电池简化热环境候选 | K、Pa、kg/m³、m/s，Bus | 注明冷却来流测点和正向，依场景热模型域 | C/P，配置启用时才初始化 | 缺项则不启用该热模型 | O，启用时 R* · T09/T11 · D07 | PROPOSED | A‑V3‑02A |
| 08‑03 `environmentSourceRef` | S5，源版本、采样点位和时刻关联 | 1、s、ID，Bus | 时空基准明确，可区分局部查询 | C/P，同调度点直接关联，跨速率保留采样引用 | 错配拒绝并重发，不采用未知风即无风假设 | R · T04/T09/T09R · — | PROPOSED | A‑V3‑02A, AR‑16 |

## I09 实验配置与初始化控制

Producer S6 → Consumer S1–S5 A 方各系统。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑17 · [02B](../history/A-V3-02B.md) E‑Δ03。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 09‑01 `experimentManifest` | S6，运行、场景、配置和日志版本 | 1、ID，Bus | 具名配置及模型合法版本 | I，校验并锁定运行配置 | 不兼容即拒绝 Ready | R · T01/T11/T12 · D07 | PROPOSED | A‑V3‑02A |
| 09‑02 `initialStateProposal` | S6 提供候选，各系统持有各自状态 | 本系统 SI，Bus | S2 六状态、S1 阶段、S3 策略、S5 环境、S4 外部初态 | I，每个所有者校验设置并回显；能源展开到 I20 | 不一致拒绝就绪，真实联合初态另议 | R · T11/T11R/V‑B15 · D06/D07/02C | PROPOSED | A‑V3‑02A, E‑Δ03 |
| 09‑03 `experimentControl` | S6，启动/停止及生效点 | 1、s、ID，Bus | 运行关联并核对生效顺序 | E，Ready 后开始 | 已生效停止优先于提交，关闭待处理，保存最终输出 | R · T11/T13/T11R/T13R · — | PROPOSED | A‑V3‑02A, AR‑17 |

## I10 实验状态及记录

Producer S1–S5 A 方各系统 → Consumer S6。状态 `PROPOSED`。来源 [02A](../history/A-V3-02A.md) · [02AR](../history/A-V3-02AR.md) AR‑18 · [02B](../history/A-V3-02B.md) E‑Δ03。

| Signal ID / Name | Owner / Description | SI Unit / Type / Dimension | Boundary / Frame / Sign / Valid Domain | Update / Initialization | Validity / Constraint / Fallback | Required / Verification / Dependency | Status | Source / Revision |
|---|---|---|---|---|---|---|---|---|
| 10‑01 `initializationStatus` | 各状态所有者，就绪、拒绝和实际采用的配置 | 1、s、ID，Bus | 标识本运行与版本 | I/E，校验后发布 | 旧运行回执不计入 Ready | R · T11/T11R · — | PROPOSED | A‑V3‑02A, E‑Δ03 |
| 10‑02 `experimentStatusEvent` | S1 任务完成，源系统拥有故障或越界事件，S6 裁定 | 1、s、ID，Bus | 同运行、源时刻及原因 | E，正常完成、物理输入缺失、数值、协议与模型域分开 | 主因与并发事件同保存，关闭未完事务 | R · T13/T13R/T15 · — | PROPOSED | A‑V3‑02A, AR‑18 |
| 10‑03 `sourceLogChannels` | 各模块保有源，S6 聚合 | 原生 SI，多具名通道 | 保留真实/替身/缺失、模型参数及测量引用 | L，初始化登记，直接从源独立采集 | 日志缺失追溯，不通过日志回送实时控制 | 核心 R，扩展 O · T08/T12/T13 · D01–D07 按场景 | PROPOSED | A‑V3‑02A, E‑Δ03 |
