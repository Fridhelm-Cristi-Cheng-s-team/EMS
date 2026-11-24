# EMS V3 — Propeller Physical Parameter Baseline V0.1

Status `REVIEWED / NOT FROZEN`. PROP-B is the recommended research candidate. PROP-A and PROP-C remain independent alternatives. All candidate values stay `PROPOSED` or `TBD`.

The authoritative current data are `propeller_parameters.json`, each candidate-specific set of map rows in `maps/propeller_map.csv`, full results in `results/`, and the PROP-B-specific motor requirement files. The all-candidate load CSV is comparative and must be filtered by candidate ID. The 05A outputs are historical. Development and future model work use the 05AR revision.

PROP-B parameters are D=2.20 m, pitch=2.31 m, three blades, candidate RPM 750–1950, J_prop=1.3281442669605 kg m² and remaining drive mass allowance 15.517229 kg. The 1950 rpm value is a candidate search cap, not a structural limit. The prop plus installation stays inside the 22 kg combined electric-drive/prop allowance.

The BEMT maps are synthetic and valid for forward, positive-thrust axial flow in their per-candidate valid J cells. The propeller moment is a shaft load. S4 continues to own local inflow and actual force/application-point moment per I05/I06/I08. I16/I17 retain shared-shaft motor/prop load ownership, and I18/I19 retain demand/capability ownership. No ICD semantics changed.

## Limits

No full-scale propeller calibration, structural or mechanical RPM substantiation, actual installation clearance, windmill/parked load map, dynamic response or joint motor thermal capability has been established. The 66 N low-load point is outside PROP-B's current candidate RPM domain. Three tier-3 source records have defined duration: none. The 300 km mission is a research scenario, not validated range capability. MATLAB/Simulink remains `NOT RUN`.

The mass distribution, geometry, polar and RPM candidate envelope are preliminary. This archive does not approve/freeze individual parameters. A-V3-05B may consume `motor_requirements/motor_requirements_PROP-B.csv` after A-side approval. It must not interpret shaft mechanical loads as electrical input or assume acceleration torque/losses are already included.

## Evidence and reproduction

`calculations/original/replayed-package/` records the byte-verified original 05A run. `calculations/revised/` contains the 05AR independent implementation and immutable input snapshots. `sources/` stores the two deliverable ZIPs and the 05AR ZIP hash record. Public third-party data are cited in `sources/source_register.md`, not redistributed in full.

From `calculations/revised/`, use the supplied reproduction instructions in `sources/README-05AR.md`. The parent `SHA256SUMS` covers this archive subtree. The aircraft inputs are independent snapshots of aircraft baseline V0.1, and their hashes are included in the subtree manifest. On checkout, run `sha256sum -c SHA256SUMS` from `platform/parameters/propeller/v0.1/`.
