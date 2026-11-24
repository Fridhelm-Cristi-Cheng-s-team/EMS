# EMS V3 — Propeller Physical Parameter Baseline V0.1

Archive review state `REVIEWED / NOT FROZEN`. This state records A-side report-level review and archiving, not formal approval of candidate values.

The current candidate data and limits are documented in [the machine-readable archive](../../platform/parameters/propeller/v0.1/README.md). PROP-B is the principal research candidate. PROP-A and PROP-C remain separate alternatives. The effective map and requirements derive from A-V3-05AR. A-V3-05A is retained only for historical traceability.

The candidate model uses fixed-pitch, three-blade PROP-B at 2.20 m diameter, 2.31 m nominal pitch and a 750–1950 rpm candidate search band. Its corrected rotor inertia estimate is 1.3281442669605 kg·m². The unallocated drive mass budget is 15.517229 kg within the inherited 22 kg combined propeller/electric drive budget.

The coefficient map follows CT, CQ and CP=2πCQ consistency and calculates eta=J CT/CP. It comes from a synthetic BEMT model, with finite blade count and Prandtl root/tip corrections. Forward axial-flow validity ranges, sensitivity, calculation source, reproduction and interface mapping are in the archive. 1950 rpm is not a mechanical rating. Clearance, measured full-scale performance, windmill loads, dynamic drive loads and thermal capability remain TBD. 300 km remains a candidate mission scenario. MATLAB/Simulink is `NOT RUN`.

A-V3-05B can use the dedicated PROP-B load file after A-side authorization. It must perform the motor rating, thermal and acceleration-torque work. No interface definitions were changed by this archive.
