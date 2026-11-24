# A-V3-05AR 来源登记

| 来源 | 实际用途与范围 |
|---|---|
| EMS 正式 main `544da4e0ad59d8cbe0bf4f2a6f749fc26df0bbcf` | 从 Git 对象直接读取 `platform/parameters/aircraft/v0.1/` 下的四份输入。CSV Git 对象为 LF，仓库属性 `text eol=crlf`，05A 快照为 CRLF。所有字段及行顺序一致。另读取系统接口与能量接口文件。 |
| 05A 原始交付 ZIP | 原样保存于 `original/`。读取完整设计报告、来源登记、验证报告、原 Python 脚本、三组图谱、11,577 条匹配记录和 11,567 条工作点。逐项复现与差分。 |
| NASA Glenn, Propeller Thrust | 用于核对匀载理想盘的推力、盘面速度与功率下界。对均匀轴向来流、无旋、无黏理想盘适用。未用作实际桨数据。[NASA Glenn](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/propeller-thrust/) |
| A. Ning, CCBlade 理论与 API | 入流角标量求根及 Prandtl 桨尖/桨根修正的独立参考。05AR 从无量纲速度关系自行实现方程，未移植外部实现或极曲线。[理论](https://flow.byu.edu/CCBlade.jl/stable/theory/) · [API](https://flow.byu.edu/CCBlade.jl/stable/reference/) |
| Dantsker 等，AIAA 2022-4020，UIUC 数据库 Vol. 4（2022-06-12） | 读取风洞方法与两组原始数表。两叶片，标称直径 20/21 in，螺距 10/13 in，所选转速 4,025/3,021 rpm，论文记录试验气温、气压、推力与转矩测量及风洞修正方法。只摘录下列少量量级对照点，不使用训练、标定或缩放，不分发整套原数据。[论文](https://m-selig.ae.illinois.edu/pubs/DantskerCaccamoDetersSelig-2022-AIAA-Paper-2022-4020-APCEPropTestsVol4.pdf) · [数据索引](https://m-selig.ae.illinois.edu/props/volume-4/propDB-volume-4.html) |
| NACA TN 2859，Corson 与 Maynard，1952 | NTRS 书目记录为全尺寸高速两叶片测功机试验，叶片角 20°–55°，最高约 500 mph。高桨速、叶型、桨距和安装环境均与本研究不同，本次只作全尺寸试验类型参考，不引用其效率作为定量证据。[NTRS](https://ntrs.nasa.gov/citations/19930083637) |

## 公开实测对照数据

| 风洞桨 | 名义 P/D | 取值 J | CT | CP | 用原系数重算 η |
|---|---:|---:|---:|---:|---:|
| [APC 20×10，4,025 rpm](https://m-selig.ae.illinois.edu/props/volume-4/data/apce_20x10_2206od_4025.txt) | 0.500 | 0.400957 | 0.062011 | 0.031704 | 0.78425 |
| 同上，所选转速最高实测效率点 | 0.500 | 0.452953 | 0.050533 | 0.028331 | 0.80790 |
| [APC 21×13，3,021 rpm](https://m-selig.ae.illinois.edu/props/volume-4/data/apce_21x13_2214od_3021.txt) | 0.619 | 0.493551 | 0.057113 | 0.034681 | 0.81277 |
| 同上，所选转速最高实测效率点 | 0.619 | 0.534613 | 0.048626 | 0.031746 | 0.81889 |

前两种桨以 J/名义(P/D) 约 0.80 的点作区间对照，PROP-B M02 巡航约 0.805。该归一化只用于展示工况相对螺距的位置。雷诺数、马赫数、径向弦长、扭转、叶片数与安装干扰未匹配，公开实测值只能提供量级参照。05AR 未得到 PROP-B 对应尺寸的翼型极曲线或推力/扭矩实测。合成极曲线沿用 05A 的 5.7/rad、约束 CL ±1.2、CD0(Re=5×10⁵)=0.012、二次项 0.015 和 Re 指数 −0.2，在模型内作联合扰动。全部几何、质量分布及损失假设标记为候选。
