# Propeller archive verification

A-V3-05A original ZIP and 05AR ZIP integrity, SHA-256 and independent replay evidence are included in the archived package. The 05AR result corrected the blade inertia dimensional factor, fixed the induced-velocity index used for tip Mach, and separated the PROP-B motor demand from all-candidate comparisons.

The revised run covered 3,859 unique input rows and 11,577 candidate/point combinations. It matched all 246 tier-1 and 3,608 tier-2 rows for each candidate. The effective tier-3 coverage was A 3/3, B 2/3, C 1/3. Two trim-invalid rows were excluded for each candidate. The B/C 1,286 N and 66 N points remain outside at least one candidate's stated envelope, with row-level boundary details in the archive.

PROP-B's revised M01/M02 shaft energies are 15.0284359718 and 37.0556645783 kWh. M02 effective thrust power integrates to 31.2164804065 kWh. Revised mission efficiency is 84.24%. A correlated +25% synthetic profile-drag sensitivity yields about 82.06% and is not a confidence bound.

The corrected inertia is 1.3281442669605 kg·m². The PROP-B motor file includes 3,690 task nodes and two durationless stress points. M07 cap references do not enter mission integrals or the dedicated motor file.

Python map, matching, integration, interpolation and mass-moment checks passed. The original and revised calculation outputs reproduced after separate archive extraction. Full-scale calibration, mechanical limits, installation clearance, thermal/electrical matching and MATLAB/Simulink remain `NOT RUN`. The numerical checks establish consistency of the synthetic candidate study, not hardware capability.
