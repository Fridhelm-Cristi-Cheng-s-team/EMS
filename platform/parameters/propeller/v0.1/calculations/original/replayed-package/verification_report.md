# A-V3-05A verification report

## Evidence set

Run: `python study.py --out generated` under Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0. Full run took about two minutes. Exact source snapshots and hashes are included in the package. It read all 3,859 unique input IDs and emitted three candidate matches per ID (11,577 rows).

## Executed checks

| Check | Result |
|---|---|
| Input schema count / IDs | PASS: 3,859 records; all point IDs unique. |
| Candidate map size | PASS: 91 J stations × 3 candidates = 273 rows. Valid ranges are contiguous in this run: A 0.46578–0.94622, B 0.53733–1.03822, C 0.57822–1.12000. |
| Coefficient consistency | PASS: CP=2πCQ at every row; maximum floating error 0. |
| Shaft units/identity | PASS: P=Q·2πn for all 11,567 matched points. |
| Forward efficiency | PASS: every matched point has 0<η≤1; maximum η=0.85126. |
| Thrust inverse | PASS: maximum absolute residual 1.26×10⁻⁸ N. Numerical root uses Brent's method with xtol 1e-8 rpm and rtol 1e-12, with selection over a 281-point RPM bracket scan. |
| Interpolation accuracy | PASS: independent direct BEMT solves at one in-domain midpoint per candidate; max absolute errors were ΔCT=1.23×10⁻⁶, ΔCQ=7.42×10⁻⁷, Δη=6.42×10⁻⁵. Evidence: `verification_interpolation.json`. |
| Candidate limits | PASS: all returned points are inside RPM/J domains and satisfy the proposed Mtip≤0.70 screen; worst matched Mtip 0.56433. |
| Invalid inputs | PASS: the two non-feasible tier-3 rows are excluded and their trim states retained. Three feasible isolated tier-3 points are matched, but duration/weight remain blank. |
| Tier coverage | PASS for all 246 tier-1 and all 3,608 tier-2 rows for all candidates. Tier 3: A 3/3; B 1/3; C 1/3. B/C failed one at RPM/no-root and one as thrust-unreachable; inspect row-level result for IDs/reasons. |
| Task integration | PASS: energy is sum(Pshaft×archived quadrature weight)/3.6e6; the phase duration is not counted once per quadrature sample. Complete mission energy only reported when every feasible sample matched. |
| Loss accounting | PASS: map's profile/induced effects are part of BEMT; the A-V3-03AR 0.97–0.99 shaft-loss multiplier was not applied again and no additional friction loss is asserted. |
| Low-speed / windmill | PASS as bounded behavior: no n=0, reverse, negative-torque or parked-flow performance is invented; those cases are outside this map and must stop/warn in a future model. No low-speed experimental validation was run. |
| Mass / inertia | PASS arithmetic and budget: all candidates leave positive mass for motor/other drive within the 22 kg combined budget. `J_prop` is positive and is not aircraft `Iy`. |
| Sensitivity | PASS: 19 cases include ±10% demand, inflow and density; ±5% diameter and pitch; correlated polar changes; RPM cap changes; and mass/inertia-only changes. Mass/inertia do not alter steady aerodynamic operating point. |
| MATLAB/Simulink | NOT RUN. |
| Structural, fatigue, acoustic, thermal, motor, electrical, full-scale test or clearance validation | NOT RUN. |

The solver's candidate-point fit establishes numerical feasibility only for this synthetic model. It does not establish that a manufactured propeller or motor can produce these loads.

## Independent package reproduction

The ZIP was extracted to a separate scratch directory. `study.py --out reproduced`, the interpolation check, and the parameter-source annotation step were run from that extracted copy. All reproduced data outputs (map, candidate comparison, point matches, motor loads, mission energy, results, sensitivity, parameter JSON and interpolation check) byte-matched the deliverable outputs. The ZIP passed `unzip -t`. After the reproduced data matched, source-document detail and the tier-3 status explanation were clarified. The post-reproduction edits were documentation and deterministic parameter-provenance formatting; the numerical engine, input snapshots and numeric outputs are unchanged. The final ZIP was rebuilt with refreshed hashes and passed compressed-integrity and SHA checks.
