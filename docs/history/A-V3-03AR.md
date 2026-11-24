# A‑V3‑03AR — 飞行任务补充与参数收口（历史整理版）

> **历史整理版，非逐字原文。** 根据当前可读取的 A‑V3‑03AR 完整任务文本、交付包及数值结果整理；不是历史助手回复的逐字导出。所有数值均保留在机器可读结果文件中。

## 工作范围

03AR 沿用 03A P‑B 参数与纵向配平约束，没有调整 P‑B 机体参数。补充 M01 120 km、M02 300 km、M03 高爬升、M04 质量及载荷、M05 风场、M06 巡航速度，以及 M07 静态推进限制研究。任务与推进点在 [`mission_profiles.json`](../../platform/parameters/aircraft/v0.1/mission_profiles.json)、[`03ar_results.json`](../../platform/parameters/aircraft/v0.1/results/03ar_results.json) 和 CSV 中保存。

## 计算摘要

M01 总时间 3303.1869 s（55.0531 min），有效推进能耗 12.591570 kWh，条件性电驱入口能耗 16.327032–21.692848 kWh。M02 总时间 8168.0518 s（136.1342 min），有效推进能耗 31.216480 kWh，条件性电驱入口能耗 40.477276–53.779978 kWh。两个任务的爬升和下降段按任务高度及速度显式计算，300 km 任务只增加相应巡航段；这不是实际 300 km 航程能力验证。

新增 30 个任务场景实例、3690 个任务配平点。CSV 有 3859 条唯一 `point_id` 记录，包含三个需求层级、配平状态、残差、单位、持续时间及来源/有效域字段。极端需求、效率折算及推进能力上限是研究输入或条件估算，不是设备额定值。公共母线、电池、发电功率分担及燃油需求尚未完成联合匹配。

03AR 将 `∂γ̇ₐ/∂T` 的单位更正为 `rad/(s·N)`；候选有效域、实际推进能力域与任务能源可行域保持区分。A/B 联合接口未冻结。MATLAB/Simulink 全部 `NOT RUN`。

## 复现与归档

03A 原始副本和 03AR 新计算脚本分别保存在 [`calculations/original/`](../../platform/parameters/aircraft/v0.1/calculations/original/) 与 [`calculations/revised/`](../../platform/parameters/aircraft/v0.1/calculations/revised/)，结果位于同目录的 `results/`。复现命令、环境、哈希和差异检查见[验证报告](../verification/aircraft_parameter_verification.md)。本文件为历史整理稿，不冒充原始逐字报告。
