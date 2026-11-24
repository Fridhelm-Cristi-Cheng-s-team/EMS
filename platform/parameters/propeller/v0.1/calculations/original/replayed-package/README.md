# A-V3-05A temporary design package

**Baseline:** EMS repository `main` at `544da4e0ad59d8cbe0bf4f2a6f749fc26df0bbcf`  
**Design state:** EMS V3 — Propeller Candidate Parameter Set A-V3-05A, `PROPOSED / NOT FROZEN`  
**Recommended for A review:** PROP-B, balanced fixed-pitch, direct-drive candidate.  
**Persistence:** this package is in `/workspace/scratch/av3-05a/`; it is temporary and has not been committed or archived to GitHub.

## Contents

- `propeller_design_report.md`: full design and decision summary.
- `propeller_parameters.json`: one canonical parameter set for all three candidates.
- `propeller_map.csv`: synthetic BEMT CT/CQ/CP/efficiency maps, explicitly tagged by candidate and validity.
- `propeller_candidate_comparison.csv`: candidate mass/inertia/coverage/status comparison.
- `propulsion_matching_results.csv`: all 3,859 input records matched against each candidate, with exclusions and reasons.
- `motor_requirements.csv`: 11,567 matched loads for A-V3-05B; tier, mission, raw source and time weights retained.
- `mission_shaft_energy.json`: complete mission integrations using source quadrature weights; stress-only cases are not integrated.
- `sensitivity_results.csv`, `results.json`, `verification_interpolation.json`, `source_register.md`, `verification_report.md`, `decision_register.md`.
- `study.py`: reproducible BEMT-map generation and matching implementation; `verify_interpolation.py` provides an independent interpolation spot check; `annotate_parameter_sources.py` adds explicit provenance/status labels to parameters.
- `inputs/`: immutable snapshots of the four aircraft baseline source files used as inputs.
- `environment.json`, `SHA256SUMS`.

## Reproduce

Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0 were used. From this directory run:

```sh
python study.py --out reproduced
```

The program reads only `inputs/` and writes model outputs to `reproduced/`. It asserts source point count/uniqueness and numerical invariants. Then run `python verify_interpolation.py --map reproduced/propeller_map.csv --out reproduced/verification_interpolation.json`, followed by `python annotate_parameter_sources.py reproduced/propeller_parameters.json`. Run time is roughly two minutes on the execution host. Reproduced output files can be compared with the root outputs; CSV floating point text should be byte stable for the recorded versions/platform, while JSON object formatting is deterministic.

The ZIP contains this directory's inputs and script. After extraction, run the command above. The BEMT polar and candidate geometry are synthetic assumptions, not manufacturer data or full-scale test results. See `source_register.md` and the report before using results.

## Scope boundary

This is a temporary research model for forward powered flight. It is not a frozen parameter baseline, a manufactured propeller design, structural/installation certification, motor/electrical/thermal matching, or MATLAB/Simulink validation. No repository file, branch, commit, pull request, or GitHub state was changed.
