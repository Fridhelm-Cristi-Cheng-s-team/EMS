# Project development rules

1. Keep original reference models unchanged. Treat them as read-only. You may extract copies into a temporary working directory for read-only analysis and model evaluation, but never overwrite or modify the original assets.
2. Develop the Platform and Engine separately. Platform work covers the aircraft physics simulation platform, flight control, EMS, and system integration. Engine work covers engine and electrical generation model adaptation. A方 reviews integration work.
3. Record cross-module interface changes in `docs/` and obtain review from both A and B sides before merging.
4. Mark MATLAB/Simulink tests PASS only after running them in MATLAB/Simulink and observing a successful result.
5. Do all development on an independent branch and merge into `main` through a reviewed Pull Request.
6. Do not fabricate simulation results or verification evidence.
7. Do not modify the legacy EMS-Platform or EMS-Engine repositories without explicit authorization.
