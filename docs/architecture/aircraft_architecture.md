# 飞机系统架构

**A-side Design Baseline V0.1 · REVIEWED / NOT FROZEN**

## 纵向刚体候选

S2 积分 $x=[X,Z,u,w,\theta,q]^\mathsf T$。惯性系水平 $X$ 向前、$Z$ 向上。机体 $x_b$ 向前、$z_b$ 向腹、$y_b$ 向右。$u,w$ 是对地速度在机体的分量。俯仰角、角速度及力矩抬头为正。航迹极坐标候选便于控制律表述，但低速度存在奇异，空气相对航迹形式还需沿航迹风变化率。飞控可消费满足有效域的派生角度。

$$
R(\theta)=\begin{bmatrix}\cos\theta&\sin\theta\\\sin\theta&-\cos\theta\end{bmatrix},
\qquad (\dot X,\dot Z)^\mathsf T=R(u,w)^\mathsf T .
$$

设惯性风为 $\mathbf W$，则 $(u_a,w_a)^\mathsf T=(u,w)^\mathsf T-R^\mathsf T\mathbf W$。$V_a=\sqrt{u_a^2+w_a^2}$，$V_g=\sqrt{u^2+w^2}$，$\alpha=\operatorname{atan2}(w_a,u_a)$，$\gamma_a=\operatorname{atan2}(\dot Z-W_Z,\dot X-W_X)\equiv\theta-\alpha$，$\gamma_g=\operatorname{atan2}(\dot Z,\dot X)$。角度各自依赖对应速度的有效域。若采用空气航迹极坐标，沿轨迹风变化率为 $\mathrm d\mathbf W/\mathrm dt$，惯性加速度为 $\mathbf a_g$，则 $\dot V_a=\mathbf e_t\cdot(\mathbf a_g-\mathrm d\mathbf W/\mathrm dt)$、$\dot\gamma_a=\mathbf e_n\cdot(\mathbf a_g-\mathrm d\mathbf W/\mathrm dt)/V_a$，其中 $\mathbf e_t=(\cos\gamma_a,\sin\gamma_a)$、$\mathbf e_n=(-\sin\gamma_a,\cos\gamma_a)$。

当采用机体内固定重心及名义固定 $I_y$ 近似，$F_x,F_z$ 为机体系非重力合力，$M_y$ 为关于重心总俯仰矩：

$$
\dot u=F_x/m-qw-g\sin\theta,\qquad
\dot w=F_z/m+qu+g\cos\theta,\qquad
\dot\theta=q,\qquad \dot q=M_y/I_y .
$$

动压 $\bar Q=\rho V_a^2/2$。候选 $L=\bar Q S C_L$、$D=\bar Q S C_D$、$M_a=\bar Q S\bar c C_m$。机体气动分量为 $L\sin\alpha-D\cos\alpha$ 和 $-L\cos\alpha-D\sin\alpha$。升力沿空气相对速度上法向，阻力反向。系数与参考点由标定确定。推力轴抬头安装角为 $\delta_T$ 时，机体推进分量为 $F_{T,x}=T\cos\delta_T$、$F_{T,z}=-T\sin\delta_T$。俯仰总矩可汇总气动力矩、实际推进力矩及其它有据载荷。

## 任务、飞控与推进

| 阶段 | 候选激活目标 | 阶段守卫 |
|---|---|---|
| 爬升 | 真空速加对地升降率，可选空气航迹角替代；目标高度附近切换高度捕获 | 高度捕获和稳定跟踪，反馈有效 |
| 巡航 | 真空速加高度保持 | 计划或任务路线进度满足下降条件 |
| 下降 | 真空速加对地下沉率或空气航迹角，可选空中终点高度捕获 | 空中终点和任务完成条件 |

一时只激活一个独立垂向目标，其他量作限制或阶段守卫。S1 拥有已提交阶段，S2 拥有实际飞控模式、舵面和推力请求。S2 接收候选、校验并返回接受、拒绝或暂不可行。接受后仍执行旧目标。在共同调度点用已形成的物理快照重新校验，S2 发本点就绪后，S1 复核守卫并提交，S2 同点采纳并回报。S3 消费已提交阶段。正式接受、当前可行性、实际跟踪或达到分别记录。等待有截止，重复和过期回执不推动状态；同刻已生效停止优先。

S4 由 I05 机体基准点运动及 I08 同源环境统一计算桨处入流。I06 发布关于固定点 $O$ 的等效矩 $M_O$ 及机体力 $(F_x,F_z)$，包括安装力臂。若 $\mathbf r$ 从当前重心指向 $O$，S2 以 $M_{\rm CG}=M_O+r_zF_x-r_xF_z$ 换点一次。推力请求、已采纳请求、可执行目标和实际推力分别关联。飞控按实际量和有效能力限幅、抗饱和并报告持续受限；短时预测、准稳态能力与实际载荷各有用途。

~~~mermaid
sequenceDiagram
    participant M as S1 任务
    participant F as S2 飞控
    participant E as S3 EMS
    M->>F: 发布候选、基准版本和期限
    F-->>M: ACCEPTED 或拒绝/暂不可行
    F-->>M: 共同点给出 READY_AT_TICK 或撤回
    alt 有效且无停止事件
        M->>F: 正式提交
        F-->>M: 同点切换及 APPLIED
        M-->>E: 已提交阶段
    else 失效或终止
        M->>F: 关闭候选
    end
~~~

## 环境、数据与质量

S5 按位置、时刻提供同源总风、密度及大气条件。总风已含启用的阵风。飞控读取具有独立标识的测量或估计，S2 物理模型使用真值。飞行反馈失效时暂停相关阶段守卫；不能用过期能力解除限制，也不能用零或能力值补无效载荷。获准保持或降级须有工况依据和期限，否则按运行场景通知 S6。细则见[系统接口](../interfaces/system_interfaces.md)。

B 方持有唯一燃油库存，S2 用同一库存快照派生总质量及经批准的重心与惯量。采用移动重心或时变惯量时需明确开放系统动量、角动量及参考点关系。油箱位置、不可用燃油及相关变质量模型为 \`TBD\`，正式数据移交 [02C](../interfaces/ab_interface_pending.md)。

来源 [A‑V3‑01R](../history/A-V3-01R.md)、[A‑V3‑02A](../history/A-V3-02A.md)、[A‑V3‑02AR](../history/A-V3-02AR.md)。
