# EMS V3 — Aircraft Physical Parameter Baseline V0.1

**归档层面：`REVIEWED / NOT FROZEN`。** 此状态记录 A 方对既有候选设计报告和计算证据的审查与归档，不代表所有参数和决策获得正式批准。参数及未决事项保留各自的 `PROPOSED / NOT FROZEN` 或 `TBD`。

## 规范文件

本版本只有一个统一飞机参数数据文件 `aircraft_parameters.json` 和一个任务配置文件 `mission_profiles.json`。CSV 是由计算脚本生成的点级需求证据，不是第二份参数基线。

| 路径 | 用途 |
|---|---|
| `aircraft_parameters.json` | P‑A/P‑B/P‑C 参数、单位、来源、状态和派生关系 |
| `environment.json` | 复现环境版本和 MATLAB/Simulink 状态 |
| `mission_profiles.json` | 任务场景及边界条件 |
| `propulsion_requirements.csv` | 3859 个唯一点级推进需求记录 |
| `calculations/original/` | 03A 原始脚本、输入配置和原始 ZIP |
| `calculations/revised/` | 03AR 计算脚本及其运行所需的原始文件副本；`mission_profiles.json` 为指向本目录唯一规范任务配置的相对符号链接 |
| `results/` | 原始 03A、03A 复现与 03AR 结果 JSON |
| `SHA256SUMS` | 本归档所有负载文件的 SHA‑256 |

报告入口：[`docs/parameters/README.md`](../../../../docs/parameters/README.md)。验证和复现说明见 [`docs/verification/aircraft_parameter_verification.md`](../../../../docs/verification/aircraft_parameter_verification.md)。

## 环境

已记录并用于复现：Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0。无需 MATLAB。两轮 Python 结果在该环境下逐字节重现。运行 MATLAB/Simulink 验证为 `NOT RUN`。

从本目录运行：

```sh
sha256sum -c SHA256SUMS
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
PYTHONDONTWRITEBYTECODE=1 python3 calculations/original/study.py > "$TMP/03a-check.json"
cmp results/03a_reproduced_results.json "$TMP/03a-check.json"
PYTHONDONTWRITEBYTECODE=1 python3 calculations/revised/study.py --out "$TMP/03ar-check"
cmp results/03ar_results.json "$TMP/03ar-check/results.json"
cmp propulsion_requirements.csv "$TMP/03ar-check/propulsion_requirements.csv"
```

以上命令仅在脚本及其所需文件都以本目录为当前工作目录时有效；本归档脚本自身不使用临时工作区绝对路径。完整验收记录见验证报告。
