# 飞机物理参数归档验证报告

**归档状态：`REVIEWED / NOT FROZEN`。** 参数与未批准决策仍按各自 `PROPOSED` 或 `TBD` 状态管理。验证报告审查的是来源完整性、脚本复现和数据一致性，不构成实机性能验证。MATLAB/Simulink：`NOT RUN`。

## 原始资产

03A 原始临时目录中的文件核验后复制入本归档的 `calculations/original/` 和 `results/`，原工作目录未更改。03AR ZIP 实际 SHA‑256 为 `4d89ddf292dc15d927c6e68d749143099354a2799b817eb63c7f01326fed38c3`，与先前记录一致；ZIP CRC/完整性检查通过，14 个条目齐全，包内 `SHA256SUMS` 全部通过。独立临时解包重算：原 03A 输出与包内 `03a_reproduced_results.json` 逐字节一致；修订 `study.py` 输出的 `results.json` 和 `propulsion_requirements.csv` 与原包均逐字节一致。原 ZIP 和原始结果未覆盖。

## 环境与复现

运行环境：Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0。独立解包目录执行的命令：

```sh
sha256sum -c SHA256SUMS
PYTHONDONTWRITEBYTECODE=1 python3 source_03a/study.py > 03a-local-recheck.json
cmp 03a_reproduced_results.json 03a-local-recheck.json
PYTHONDONTWRITEBYTECODE=1 python3 study.py --out reproduced
cmp results.json reproduced/results.json
cmp propulsion_requirements.csv reproduced/propulsion_requirements.csv
```

所有命令成功；数值结果及 CSV 均无字节差异。原始资产 SHA‑256 与 ZIP 内部清单随来源文件保留。归档根 `SHA256SUMS` 覆盖整个可读归档负载（清单本身除外）。

## 参数与数据一致性

- 原任务记录的关键质量预算、P‑B 几何、CG、惯量、37 m/s 巡航和爬升率与结构化文件一致；P‑A/P‑B/P‑C 独立保存，P‑B 为推荐主研究方案。
- M01/M02 的任务总量分别为 120/300 km、55.0531/136.1342 min、12.591570/31.216480 kWh 有效推进能耗；条件性电驱入口能耗分别为 16.327032–21.692848/40.477276–53.779978 kWh。
- 03A 扫描记录 1500 点，其中 1384 点通过研究筛选。03AR 含 30 个扩展任务实例、3690 个任务配平点。CSV 表头声明单位，3859 个数据行的 `point_id` 均唯一。
- CSV 含一级正常设计、二级扩展研究、三级极端应力层级；持续时间、运行域、来源及配平状态字段保留。M07 静态限幅不是动态闭环证据。轴功率、电机机械功率和入口功率为注明假设下的条件性估算。
- 质量预算分项不能同时无条件取上限；电池容量、公共母线、发电功率、燃油需求及 A/B 联合匹配仍未完成。

## 文档及仓库检查

新增文档使用相对链接；在提交前执行链接目标检查、JSON 解析、CSV 单位/数量/唯一性核验、SHA‑256 校验、`git diff --check`、文件大小及敏感信息/临时文件扫描。脚本不依赖临时绝对路径。无计算缓存或虚拟环境归档。

## 结论与适用边界

归档文件链和计算复现通过。300 km 是候选研究任务，不代表实航程能力。条件性电驱入口能耗不是电池容量，动力设备质量是候选预算。没有进行新的物理参数设计，没有 MATLAB/Simulink 结果，没有冻结参数或 A/B 接口。
