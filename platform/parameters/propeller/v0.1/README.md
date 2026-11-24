# EMS V3 — Propeller Physical Parameter Baseline V0.1

Status `REVIEWED / NOT FROZEN`. PROP-B is the recommended research candidate. PROP-A and PROP-C remain independent alternatives. All candidate values stay `PROPOSED` or `TBD`.

The authoritative current data are `propeller_parameters.json`, each candidate-specific set of map rows in `maps/propeller_map.csv`, full results in `results/`, and the PROP-B-specific motor requirement files. The all-candidate load CSV is comparative and must be filtered by candidate ID. The 05A outputs are historical. Development and future model work use the 05AR revision.

PROP-B parameters are D=2.20 m, pitch=2.31 m, three blades, candidate RPM 750–1950, J_prop=1.3281442669605 kg m² and remaining drive mass allowance 15.517229 kg. The 1950 rpm value is a candidate search cap, not a structural limit. The prop plus installation stays inside the 22 kg combined electric-drive/prop allowance.

The BEMT maps are synthetic and valid for forward, positive-thrust axial flow in their per-candidate valid J cells. The propeller moment is a shaft load. S4 continues to own local inflow and actual force/application-point moment per I05/I06/I08. I16/I17 retain shared-shaft motor/prop load ownership, and I18/I19 retain demand/capability ownership. No ICD semantics changed.

## Limits

No full-scale propeller calibration, structural or mechanical RPM substantiation, actual installation clearance, windmill/parked load map, dynamic response or joint motor thermal capability has been established. The 66 N low-load point is outside PROP-B's current candidate RPM domain. Three tier-3 source records have defined duration: none. The 300 km mission is a research scenario, not validated range capability. MATLAB/Simulink remains `NOT RUN`.

The mass distribution, geometry, polar and RPM candidate envelope are preliminary. This archive does not approve/freeze individual parameters. A-V3-05B may consume `motor_requirements/motor_requirements_PROP-B.csv` after A-side approval. It must not interpret shaft mechanical loads as electrical input or assume acceleration torque/losses are already included.

## Archive verification and reproduction

From this directory run:

```sh
python reproduce_archive.py
```

From the repository root run `python platform/parameters/propeller/v0.1/reproduce_archive.py`.
The script finds the archive from its own path. It verifies the outer manifest, the ZIP hashes
and CRCs, both ZIPs' internal manifests and the unpacked copies. It runs 05A and 05AR in a fresh
temporary directory, checks the exact set of outputs, and compares 9 original and 16 revised
files byte for byte. The revised comparison includes the PNG and
[`results/match_comparison.csv`](results/match_comparison.csv).
The exit status is zero only when all requested checks pass. Add `--check-only` for integrity checks
without running the calculations.

The reference runtime is Linux x86_64, Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, and
Matplotlib 3.10.8. See [the recorded environment](sources/environment.json). For the full run,
install the three packages in the Python environment used to launch the script:

```sh
python -m pip install numpy==2.3.5 scipy==1.17.0 matplotlib==3.10.8
```

The Python entry point needs no Bash, unzip, or sha256sum executable. Byte equality also depends
on the numerical libraries, platform line endings and rendering stack, including fonts.
On another environment, a byte difference, including one limited to the PNG or to line endings,
is reported as a failed check with both SHA-256 values.

### Evidence layout

- [`SHA256SUMS`](SHA256SUMS) covers every archive file except itself and includes the nested 05A manifest.
- `sources/` stores both historical ZIPs with their original SHA-256 values. The 05A hash record
  was taken from the 05AR ZIP's `original/05A-ZIP-SHA256`. The historical READMEs and Bash scripts
  describe the unpacked ZIP layout. Use the Python command above for this repository layout.
- `calculations/original/replayed-package/` holds the original 05A input snapshot, scripts, manifest,
  outputs and prior replay. `calculations/revised/inputs/` holds the 05AR aircraft input snapshot.
- `maps/`, `results/` and `motor_requirements/` hold the unpacked 05AR outputs. Public references
  are tracked in the [source register](sources/source_register.md).

Git stores archived CSV files with their exact ZIP bytes. This preserves CRLF for generated
CSV files and the 05A input snapshot, and LF for the 05AR input snapshot. The historical
manifests and the reviewed physical data retain their original bytes.
