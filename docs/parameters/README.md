# 飞机参数归档

归档名称：**EMS V3 — Aircraft Physical Parameter Baseline V0.1**
归档审查状态：`REVIEWED / NOT FROZEN`

本状态表示 A 方对已有候选设计报告和计算证据完成报告层面审查并归档，不等于每个参数或技术决策已正式批准。机器可读飞机参数的唯一规范副本位于 [`platform/parameters/aircraft/v0.1/aircraft_parameters.json`](../../platform/parameters/aircraft/v0.1/aircraft_parameters.json)，任务配置唯一规范副本位于同目录 `mission_profiles.json`；本目录仅提供文档说明及索引。

- [飞机物理参数基线](aircraft_physical_baseline.md)
- [飞行任务说明](mission_profiles.md)
- [技术决策登记](aircraft_decision_register.md)
- [计算验证报告](../verification/aircraft_parameter_verification.md)
- [历史整理稿 A‑V3‑03A](../history/A-V3-03A.md) 与 [A‑V3‑03AR](../history/A-V3-03AR.md)
- [可复现数据、脚本和逐文件校验清单](../../platform/parameters/aircraft/v0.1/README.md)

逐参数 `PROPOSED / NOT FROZEN` 或 `TBD` 状态继续有效。Python 数值复现已有证据；MATLAB/Simulink `NOT RUN`。本归档不冻结 A/B 联合接口。
