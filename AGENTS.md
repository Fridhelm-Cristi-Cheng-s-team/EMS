# Project development rules

1. Treat original assets in `reference/` as read-only. Do not modify them directly.
2. Develop the platform and engine separately. A方 reviews integration work.
3. Record cross-module interface changes in `docs/` and obtain review from both sides before merging.
4. Mark MATLAB/Simulink tests PASS only after running them in MATLAB/Simulink and observing a successful result.
5. Do all development on an independent branch and merge into `main` through a Pull Request.
6. Do not fabricate simulation results or verification evidence.
7. Do not modify the legacy EMS-Platform or EMS-Engine repositories without explicit authorization.
8. This task does not implement or modify any Simulink model.
