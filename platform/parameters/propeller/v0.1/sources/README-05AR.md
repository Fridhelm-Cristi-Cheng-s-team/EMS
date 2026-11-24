# EMS V3 A-V3-05AR 交付包

从 `technical_review.md` 阅读结论和边界。`decision_register.md` 列出 P0/P1/P2 的整改及状态，`source_register.md` 记录正式输入与公开实测对照，`verification_report.md` 给出实际执行证据。

## 供审核和电机需求使用的文件

| 文件 | 内容 |
|---|---|
| `outputs/propeller_parameters.json`、`outputs/parameter_comparison.csv` | 三个候选及修订前后参数 |
| `outputs/propeller_map.csv`、`outputs/map_comparison.csv`、`outputs/propeller_map_comparison.png` | 分候选系数、诊断、有效域和修订前后图谱 |
| `outputs/propulsion_matching_results.csv`、`outputs/match_comparison.csv` | 11,577 条候选逐点记录，含失败状态、上下界和根 |
| `outputs/stress_boundary_diagnostics.csv` | 原图谱的连续 RPM 推力界和修订后放宽 RPM 下限的诊断 |
| `outputs/mission_shaft_energy.json`、`outputs/mission_comparison.csv` | 所有 30 个任务与阶段的逐候选功率和加权能耗 |
| `outputs/motor_requirements_PROP-B.csv`、`outputs/motor_duty_PROP-B.json` | 下一阶段仅采用 PROP-B 的任务载荷与两条无时长应力记录 |
| `outputs/motor_requirements_all_candidates.csv` | 全体候选对照，按 candidate_id 使用 |
| `outputs/independent_recalculation.csv`、`outputs/sensitivity_results.csv`、`outputs/results.json` | 独立方程、收敛、边界、敏感性与机器可读汇总 |

数据字段使用 SI 单位和字段后缀。正 Q 为气动阻力矩，P 为桨机械轴功，eta 为无量纲比值。`weight_applicable` 仅在实际任务情景的积分节点为真。M07 原始时间字段只作源对照，Tier 3 无权重文件留空。无效节点输出结果留空或标明状态。图谱 CSV 无效点系数供诊断检查，不能用于插值。转速界为候选筛选，均需结合来流、J、Mach、动量界等条件。

## 复现

需要 Python 标准库、NumPy、SciPy、Matplotlib、Bash、unzip 与 sha256sum。实测版本见 `environment.json`。从 ZIP 的解包根目录运行：

```bash
sha256sum -c SHA256SUMS
bash original_reproduction.sh replay
python review.py --original replay --out reproduced
python plot_maps.py --original replay --out reproduced
for file in reproduced/*; do cmp "$file" "outputs/${file##*/}" || exit 1; done
```

原脚本只有输入快照的读取权限，计算输出写至新的解包目录。原始计算约需两分钟。修订程序从本包 `inputs/` 读正式 main 的四份输入，读取解出的原始结果作对照，向指定目录写出修订复现结果。若只复现修订模型，可从 `original/` 解包 05A 原 ZIP 后直接执行最后三条命令。图像字节复现依赖同版本绘图库与字体环境，CSV 与 JSON 用于数值复核。

本包在临时目录编制。MATLAB/Simulink、实物和动态试验均为 `NOT RUN`。
