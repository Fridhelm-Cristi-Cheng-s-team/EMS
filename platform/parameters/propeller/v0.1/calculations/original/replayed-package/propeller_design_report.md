# EMS V3 — A-V3-05A Propeller Physical Parameters and Performance Map

**Report state:** candidate design study; `PROPOSED / NOT FROZEN`  
**Repository baseline:** `main` at `544da4e0ad59d8cbe0bf4f2a6f749fc26df0bbcf`  
**Aircraft case:** P-B primary research case; P-A and P-C aircraft alternatives remain independent  
**Recommended propeller candidate:** PROP-B for A-side review only  
**Persistence:** temporary work product in `/workspace/scratch/av3-05a/`; no repository changes, commit or PR.

## 1. Executive result

A reproducible synthetic blade-element momentum theory (BEMT) study was run against the complete archived CSV: 3,859 unique point records, with 3,854 feasible tier-1/2 mission/cap-reference records and 3 feasible tier-3 isolated stress points. Each of the three propeller candidates matched all 246 tier-1 and 3,608 tier-2 records. PROP-A matched all three feasible tier-3 stress points. PROP-B and PROP-C matched only the 64.45/65.96 kW maximum-effective-power point; their 1,286 N maximum-thrust point was unreachable and their 66 N low-load point had no root within the minimum RPM/J search envelope. Two failed-trim stress records were excluded for every candidate.

PROP-B is the balanced candidate to carry into A-side review because it has complete tier-1/2 coverage, lower 300 km baseline shaft energy than A/C in this model, and keeps 15.59 kg of the 22 kg drive-plus-propeller budget after its prop and installation allowance. PROP-B is **not** a final physical propeller selection, motor match or frozen parameter set. Its geometry and polar are synthetic, the actual aircraft propeller clearance is unknown, and no manufacturer structural limit or full-scale propeller test data supports its map.

**Overall task conclusion: PARTIAL.** The requested numerical candidate study and review package are complete, but the synthetic map is not validated against full-scale test data, and tier-3 coverage is intentionally incomplete for PROP-B/C. Treat it as an A-V3-05B input package after independent A-side review, not as a verified hardware capability.

## 2. Inputs and demand interpretation

The aircraft JSON, mission JSON, 3,859-row propulsion CSV and A-V3-03AR results JSON were copied to `inputs/` without editing. Exact hashes are in `SHA256SUMS`. The P-B aircraft application point and 1° shaft-axis orientation are passed through as compatibility inputs; disk clearance remains TBD.

Input audit found 3,859 unique IDs. Tier 1 has 246 records (M01/M02, 123 each); tier 2 has 3,608 records across normal extensions, 120/300 km scenarios, mass/payload/fuel cases, wind and speed sweeps, and M07 cap-reference groups; tier 3 has five isolated scan points, of which three have FEASIBLE trim status, one is OUTSIDE_SCREEN and one is NO_TRIM_FOUND. The three FEASIBLE isolated points have no duration or quadrature weight and are matched as instantaneous capability points, never integrated as energy.

For mission integration, only the actual M01–M06 task profiles with archived integration weights are accumulated. M07 reference records are retained in the pointwise matching file as raw demand/cap comparisons; their assumed caps and deficits are not represented as actual delivered thrust or a completed mission. Duplicate sample appearances reflect scenario definitions, not flight probabilities.

The CSV request is positive thrust in a steady trimmed point. Source records also give the axial propeller inflow, density, height, mass, phase duration and quadrature weight. Fixed-wing level/inclimb/descent cases use the archived steady condition; prop-installation-point dynamic velocity effects and q-dependent loads remain outside this steady matching study.

## 3. Model and signs

For positive shaft rotation and forward axial inflow:

- `J = Vax/(n D)`, where `n` is rev/s and `J` is advance ratio (distinct from rotor inertia `J_prop`).
- `T = CT ρ n² D⁴`.
- `Q_prop = CQ ρ n² D⁵`, resisting positive rotation.
- `P_shaft = Q_prop ω = 2πn Q_prop` and `CP = 2π CQ`.
- `η_prop = T Vax/P_shaft = J CT/CP` for positive forward thrust, inflow and shaft power.

The first candidate model is a fixed-pitch, single equivalent propulsor on a direct shared motor shaft. It uses annular BEMT with finite blade count/Prandtl tip loss, blade-element profile drag and induced/swirl work. Radial blade pitch is `β(r)=atan(P/(2πr))`; chord varies linearly over the specified blade span. A 34-station radial calculation uses a bounded nonlinear least-squares induction solve. Synthetic section polar assumptions, reference Reynolds number, map sampling and validity screening are recorded in `study.py` and `propeller_parameters.json`.

Each candidate has its own geometry and its own BEMT map. The maps are not fitted independently: CP derives from CQ and efficiency derives from CT/CP. The base map is one-variable CT(J)/CQ(J), generated at reference n=20 rev/s, ρ=1.10 kg/m³, and T=278 K. Actual matched work points report a local 75%-span Reynolds estimate and tip Mach, but the base map does not recalculate coefficients with local Re/Mach; this is a material model uncertainty. The section polar and geometry are synthetic, with no measured full-scale calibration point.

No map is defined for n=0, reverse rotation, static parked propeller under forward flow, negative torque/windmilling, or negative thrust. The solver returns excluded/failure states and does not extrapolate beyond the longest contiguous valid J range or the candidate RPM range. A zero-thrust/zero-speed efficiency must not be inferred from these forward maps.

## 4. Candidates

All values below are candidates, not approved hardware data. Blade areal mass is assumed 10 kg/m² over projected planform; hub mass and installation allowance are separately assumed. Inertia integrates that radial distribution plus a solid-disk hub approximation.

| Candidate | D / P / P:D | Blades | RPM candidate range | Valid J | Prop / install mass | J_prop | Remainder within 22 kg | Tier 1 / Tier 2 / Tier 3 matched |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PROP-A large/low rpm | 2.50 / 2.375 m / 0.95 | 3 | 650–1750 | 0.4658–0.9462 | 5.843 / 2.000 kg | 3.532 kg·m² | 14.157 kg | 246/246; 3608/3608; 3/3 |
| PROP-B balanced | 2.20 / 2.310 m / 1.05 | 3 | 750–1950 | 0.5373–1.0382 | 4.413 / 2.000 kg | 2.230 kg·m² | 15.587 kg | 246/246; 3608/3608; 1/3 |
| PROP-C small/high rpm | 1.80 / 2.070 m / 1.15 | 4 | 850–2350 | 0.5782–1.1200 | 3.680 / 2.000 kg | 1.518 kg·m² | 16.320 kg | 246/246; 3608/3608; 1/3 |

Mass remainder is for motor and other drive items inside the inherited 22 kg combined allowance; it is not a motor mass recommendation. Candidate RPM caps are aerodynamic search screens only, not structural/manufacturer limits. The 0.70 tip-Mach screen is likewise a proposed aerodynamic screen, not a certified limit.

The machine-readable parameter file records source class per quantity (`SYNTHETIC`, `ASSUMED`, `CALCULATED`, or TBD), status, geometry, dimensions, mass assumptions, inertia, candidate speeds and installation point. `J_prop` is shaft-axis rotor inertia, not aircraft pitch inertia `Iy`.

## 5. Performance maps and working domain

`propeller_map.csv` contains 91 sampled J values for each independent candidate, with CT, CQ, CP, η, section-angle bounds, solver residual, validity Boolean and reason. Valid contiguous intervals are shown above. No invalid map point is interpolated or extended. All matching roots are searched using the archived requested thrust and source density/inflow; roots are enumerated and a candidate is selected by passing the 0.70 tip-Mach screen, then highest η, then lower RPM. Work point search first samples 281 RPM brackets and refines each crossing with Brent's method (xtol 1e-8 rpm, rtol 1e-12).

Across all matched rows, the requested-thrust inversion maximum absolute residual was 1.26×10⁻⁸ N. Maximum matched synthetic η was 0.85126; maximum matched tip Mach was 0.56433. This numerical result is only for the assumed candidates, polar and search envelope. Local Reynolds/Mach values do not prove the polar remains valid at full-scale operating conditions.

### Candidate work ranges by tier

Ranges below are matched dataset extrema; pointwise values, including every condition identifier, are in `propulsion_matching_results.csv` and `motor_requirements.csv`.

| Candidate | Tier | RPM | Q_prop (N·m) | Shaft power (kW) | Efficiency | Max tip Mach |
|---|---|---:|---:|---:|---:|---:|
| PROP-A | 1 | 993–1137 | 80.8–244.5 | 8.40–28.59 | 0.788–0.835 | 0.420 |
| PROP-A | 2 | 966–1243 | 80.2–339.4 | 8.34–43.15 | 0.787–0.837 | 0.463 |
| PROP-A | 3 | 667–1527 | 31.9–405.7 | 2.23–64.88 | 0.735–0.839 | 0.564 |
| PROP-B | 1 | 1061–1285 | 71.4–218.4 | 7.93–28.73 | 0.825–0.851 | 0.399 |
| PROP-B | 2 | 1061–1429 | 70.8–302.0 | 7.87–43.93 | 0.795–0.851 | 0.439 |
| PROP-B | 3 | 1695 (one match) | 363.0 | 64.45 | 0.844 | 0.540 |
| PROP-C | 1 | 1232–1563 | 60.8–186.1 | 7.85–29.70 | 0.796–0.845 | 0.379 |
| PROP-C | 2 | 1232–1763 | 60.3–257.4 | 7.78–46.02 | 0.757–0.845 | 0.416 |
| PROP-C | 3 | 2034 (one match) | 309.6 | 65.96 | 0.825 | 0.514 |

Tier 3 has no defined duration and is not an endurance/continuous rating. PROP-B and C each have only the 64.45/65.96 kW maximum-effective-power point matched; each misses the 1,286 N maximum-thrust point as `THRUST_UNREACHABLE` and the 66 N low-load point as `NO_ROOT_OR_RPM_LIMIT` within the candidate minimum-RPM/J search envelope. A matches all three feasible stress points. These are candidate-map capabilities only, not proof of motor, structural or continuous capability.

## 6. Mission energies and power demand

Energy uses the archived sample quadrature weight, `Σ(Pshaft × quadrature_weight_s)/3.6e6`, never phase duration multiplied by the number of samples. For PROP-B:

| Mission | Interpretation | Energy | Peak shaft power | Duration distinction |
|---|---|---:|---:|---|
| M01 | 120 km tier-1, nominal normal 2.5 m/s climb | 14.927 kWh | 28.73 kW climb | climb 8 min; cruise 35.15 min; descent 11.90 min |
| M02 | 300 km tier-1, nominal normal climb | 36.809 kWh | 28.73 kW climb | cruise 116.23 min; climb/descent are not continuous cruise load |
| M03-120 | 120 km tier-2, 5 m/s high climb | 15.048 kWh | 43.93 kW high climb | high climb is 4 min, not a continuous rating |
| M03-300 | 300 km tier-2, 5 m/s high climb | 36.930 kWh | 43.93 kW high climb | combines 116.23 min cruise with 4 min high climb |

These are candidate propeller shaft energies only. No motor/drive electrical loss, generator, battery, thermal or fuel energy is included.

A-V3-03AR's archived constant-efficiency shaft energy bands for P-B were 15.356–18.517 kWh for M01 and 38.069–45.907 kWh for M02. PROP-B's synthetic-map values are 14.927 and 36.809 kWh, respectively. The 2.8% and 3.3% reductions relative to the old lower bounds reflect the new synthetic operating-point-dependent polar/map and its assumptions. They do not validate an actual efficiency improvement; measured propeller data, local Reynolds/Mach corrections and a common loss model would be required for that conclusion. No A-V3-03AR 0.97–0.99 shaft-loss multiplier was applied again.

The complete scenario JSON also includes 435/471/500 kg cases, payload/fuel variations, calm/head/tail winds, and 32/34/37/41 m/s cruise cases. In the 471 kg nominal P-B row the 120/300 km shaft energies are 14.927/36.809 kWh; the 500 kg extension is 15.461/38.078 kWh. 300 km remains a candidate research task, not a demonstrated actual range.

## 7. A-V3-05B motor demand package

`motor_requirements.csv` has 11,567 matched candidate-point rows, including all source fields needed for pointwise motor matching: source ID, task/tier/phase, aircraft mass, altitude/density, Vax, thrust request and actual synthetic prop thrust, RPM/ω, torque, power, efficiency, duration, quadrature weight, map validity and source reference. Tier-3 duration/weight are blank because the source provides no duration. The recommended PROP-B's tier-1 continuous/repeated demand collection reaches 28.73 kW and 218.4 N·m; tier-2 reaches 43.93 kW and 302.0 N·m in the 5 m/s high-climb, 4-minute scenario. Its one matched tier-3 point is 64.45 kW / 363.0 N·m, but max-thrust stress is unmatched; no stress duration is specified. These are loads, not a single rated motor recommendation.

The motor study should match the whole torque-speed envelope, define continuous/intermittent thermal duty, motor inertia and torque response, and jointly revisit the 22 kg allocation. Axis dynamics remain `J_eq dω/dt = τ_motor − Q_prop − τ_loss`; `J_eq=J_motor+J_prop+J_other`, with motor/other inertia and friction TBD. `Q_prop` is the aerodynamic resisting torque; it is not the airplane pitch moment. Rotor kinetic energy `0.5 J_eq ω²` and acceleration torque are separate from steady `Q_prop ω`.

## 8. Architecture and existing interfaces

The candidate keeps one equivalent forward fixed-pitch propeller and direct motor shaft. Variable pitch could widen efficient operating range but adds actuator/control state, mass and failure handling; multiple propellers add distribution/control channels and structural integration; reduction gearing adds ratio, losses, reflected inertia and another mechanical interface. None is added without approval.

No ICD or state ownership changes are proposed. I05 still owns/communicates S2 thrust request, aircraft motion and installation inputs; S4 calculates the local propeller inflow using installation-point velocity for dynamics and I08 environment from S5. I16 carries motor mechanical shaft behavior; I17 represents the propeller load; I18/I19 carry propulsion demand/capability. I06 actual force and fixed-point moment remain S4 outputs. The steady study uses q=0. Actual installation force and moment about fixed aircraft point O are computed once from installation location/orientation; S2 performs the existing CG shift once. Shaft-axis resisting torque is a shared-axis load and must not be converted directly into aircraft pitch moment.

## 9. Sensitivity and uncertainty

The 19-case sensitivity file varies thrust/inflow/density ±10%, diameter and pitch ratio ±5%, section lift slope ±8%, profile polar drag ±25% (correlated BEMT reruns), candidate RPM cap ±5%, and prop mass/inertia ±10%. At a representative PROP-B M01 cruise node, ±10% thrust shifted the matched point from about 1,172–1,211 rpm and 14.57–17.83 kW; ±10% axial inflow shifted it from about 1,113–1,273 rpm and 14.62–17.83 kW. A ±25% correlated drag polar changed η from 0.8299 to 0.8735 and power from 15.78 to 16.61 kW. A ±5% diameter change shifted RPM 1,117–1,277 at the same representative load. Mass/inertia changes alone do not alter a steady aerodynamic solution; they alter acceleration/energy in a dynamic model. The ±5% RPM cap perturbation had no effect at this base point because it is well below the cap.

Highest-priority evidence gaps are full-scale thrust/torque map data across Re/Mach and the blade geometry/polar; actual hub/prop/installation mass and inertia; mechanical RPM and structural limits; airframe envelope, clearance and interference; and a jointly validated drive/motor model. Candidate map values and mass assumptions are only a working hypothesis.

## 10. Decisions, limitations and next-stage gate

P0/P1/P2 proposals are itemized in `decision_register.md`; all remain proposed and not frozen. In particular, there is no negative-torque or windmill performance claim, the RPM/Mach screens are not structural limits, and the 300 km case is not range validation. Python numerical checks are documented in `verification_report.md`; MATLAB/Simulink and physical tests are NOT RUN.

This package contains a structured work envelope sufficient for A-side review and, once approved, can serve as the propeller input to A-V3-05B motor design. The stage must not treat PROP-B's assumed map as verified hardware performance or use the stress point as a sustained rating. A-V3-05B itself was not started.

## 11. Files and reproduction

See `README.md` for package inventory and exact reproduction command. `SHA256SUMS` covers the deliverable and immutable input snapshot. The ZIP is independently extracted and reproduced as part of this task; see `verification_report.md` and the final task report for outcome. The whole package remains temporary and has not been saved to the EMS repository.
