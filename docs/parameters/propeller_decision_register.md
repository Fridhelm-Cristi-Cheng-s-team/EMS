# Propeller decision register

All values remain `PROPOSED / NOT FROZEN` unless marked TBD. See the [verification report](../verification/propeller_parameter_verification.md) for evidence and tests.

| Priority | Proposal | Status and condition |
|---|---|---|
| P0 | Limit lookup to forward powered axial flow within valid J and RPM candidate domains. Reject unknown, stopped, windmill and unsupported low-speed loads. | Current model boundary. Windmill load must not be assumed zero. |
| P0 | Carry corrected PROP-B J_prop=1.3281442669605 kg·m². | Replaces 05A's dimensionally incorrect value. Still a mass-distribution estimate. |
| P0 | Keep PROP-B motor demands separate from alternatives and keep durationless stress points out of energy integration. | Dedicated file includes only PROP-B tasks and its own isolated stress points. |
| P1 | Use PROP-B as principal candidate, with A/C as alternatives. | Complete tier 1/2 match coverage in synthetic study. No measured full-scale calibration. |
| P1 | Treat 750–1950 rpm and M≤0.70 as model search screens. | Structural/manufacturer RPM and actual operational Mach limit TBD. |
| P1 | Keep BEMT losses and shaft accounting on a single boundary. | Do not reapply 03AR shaft efficiency. Motor, electrical and thermal losses belong to later joint matching. |
| P1 | Preserve I05/I06/I08/S4 and I16/I17/I18/I19 ownership. | No ICD changes. Local inflow uses mount motion in dynamic work. Shaft torque is not aircraft pitch moment. |
| P2 | Improve polar, compressibility, dynamic inflow, installed interference and actual mass/inertia from tests. | Validation planned, not executed. |
