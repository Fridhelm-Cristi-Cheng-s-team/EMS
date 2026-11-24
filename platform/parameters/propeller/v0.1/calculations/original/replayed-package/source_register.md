# Source and provenance register

## Project inputs

The four files in `inputs/` were copied from the archived aircraft baseline on repository `main` `544da4e0ad59d8cbe0bf4f2a6f749fc26df0bbcf`. Their SHA-256 values are in `SHA256SUMS`.

| Input | Use | Notes |
|---|---|---|
| `aircraft_parameters.json` | P-B geometry/application point, mass and drive-plus-prop mass budget | Read-only snapshot. P-A/P-C kept as separate aircraft alternatives; propeller candidates are compared against the P-B installation data. |
| `mission_profiles.json` | Mission identity, altitude/speed/wind/mass scenario source, duration/route definition | Read-only snapshot; no duration was invented for isolated tier-3 cases. |
| `propulsion_requirements.csv` | Complete pointwise demand and environment table | All 3,859 unique rows read. The point ID, tier, raw thrust request, cap status, source, domain, phase duration, quadrature weight and trim status are carried to match outputs. |
| `03ar_results.json` | Historic constant-efficiency estimate for energy comparison | Read-only snapshot. Its shaft-energy intervals are compared as historical estimates, not used to scale the new maps. |

## Public technical material reviewed

1. **NASA, Practical Applications of Momentum Theory**, NASA SP-2007-6107? The actual consulted asset is the NTRS PDF at <https://ntrs.nasa.gov/api/citations/19760025039/downloads/19760025039.pdf> (report identifier 19760025039). Read relevant sections on actuator-disk limits, blade-element momentum methods, loss mechanisms and model assumptions. Used to select a physics-based BEMT structure and document limitations; no tabulated performance curve was copied. NASA government report; no source data redistributed.
2. **MathWorks Aerospace Blockset documentation**, PDF <https://www.mathworks.com/help/pdf_doc/aeroblks/aeroblks.pdf>, section describing propeller coefficient definitions and BEMT option. Read for coefficient and modeling-convention cross-check only; no MathWorks code or proprietary assets copied. Access to documentation does not grant redistribution rights.
3. **UIUC Propeller Database, Volume 4**, <https://m-selig.ae.illinois.edu/props/volume-4/propDB-volume-4.html>. Read database description and available test families: APC Thin Electric small propellers, roughly 12–21 inch diameter, two-blade products, bench CT/CQ sweeps over advance ratio at specified test RPM, including static points. These are model-scale low-Reynolds data and are not representative enough to scale directly to this 500 kg class candidate. No data file or measured curve was used or redistributed. Data reuse rights were not independently established.
4. **APC performance-data index**, <https://www.apcprop.com/performance-data-new/>. Listing inspected as a manufacturer data discovery source. No raw files or numeric curve values used.
5. **NACA Technical Note 235, The Theory of the Propeller**, NTRS scan <https://ntrs.nasa.gov/archive/nasa/casi.ntrs.gov/19930081014.pdf>. Bibliographic record and relevance to blade-element propeller analysis checked; detailed numerical tables not extracted or used. Public-domain government report.
6. **EMS reference-v1.0 release**, <https://github.com/Fridhelm-Cristi-Cheng-s-team/EMS/releases/tag/reference-v1.0> and repository `reference/README.md`. Asset index inspected. Listed categories were eVTOL/air taxi/drone and Brayton-related material; no fixed-wing, 500 kg class, full-scale propeller map suitable for this model was identified. No asset downloaded.

## What is synthetic

All PROP-A/B/C geometry, blade count, pitch, chord/twist distributions, RPM screens, areal blade mass, hub mass and section polar are `SYNTHETIC`, `ASSUMED` or `CALCULATED`; none is a user-confirmed or measured full-scale propeller. BEMT maps are generated from the named section polar and geometry in `study.py`. The nominal polar uses lift slope 5.7/rad, a clipped linear lift coefficient with CLmax 1.20, CD=CD0+0.015 CL², Re-dependent CD0 centered on Re=5e5, and section-alpha validity −8° to +12°. Reference Re, density and temperature used to create the base dimensionless map are recorded in the code. Matching reports local 75%-span Reynolds and tip Mach but the base map is only CT(J), CQ(J); Reynolds/Mach dependence is not self-consistently remapped in the base run.

No actual test-backed efficiency or coefficient curve is claimed. No source material with unresolved redistribution restrictions is included in this package.

**UIUC extraction limit:** the index-level review did not transcribe per-propeller pitch or numeric RPM endpoints from individual test files, because no UIUC measurements were used in the candidate maps. The package records only the database family/dimension/measurement scope necessary to reject direct scaling. Any later reference-based calibration must inspect the selected raw record, exact propeller geometry, test RPM, air density/temperature and applicable reuse terms before reuse.
