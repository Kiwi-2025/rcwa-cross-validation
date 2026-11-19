# A01 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference / meent | 14/14 | 2.66e-15 | 1.44e-15 | 2.66e-15 | 2.66e-15 | 1.34e-15 | 2.74e-14 | 0013 | R(0, 0) s to s | PASS |
| reference / torcwa | 14/14 | 4.44e-16 | 9.99e-16 | 7.77e-16 | 9.99e-16 | 1.85e-15 | 1.06e-13 | 0010 | R(0, 0) p to p | PASS |
| reference / grcwa | 14/14 | 9.71e-16 | 3.55e-15 | 2.66e-15 | 3.55e-15 | 2e-15 | 8.52e-14 | 0006 | T(0, 0) p to p | PASS |
| reference / lumerical | 14/14 | 9.63e-14 | 9.59e-14 | 3.61e-14 | 9.63e-14 | 1.59e-13 | 1.24e-11 | 0006 | R(0, 0) s to s | PASS |
| meent / torcwa | 14/14 | 2.44e-15 | 8.88e-16 | 2.44e-15 | 2.44e-15 | 1.94e-15 | 1.12e-13 | 0010 | R(0, 0) p to p | PASS |
| meent / grcwa | 14/14 | 2.44e-15 | 3.33e-15 | 2.66e-15 | 3.33e-15 | 1.78e-15 | 6.01e-14 | 0006 | T(0, 0) p to p | PASS |
| meent / lumerical | 14/14 | 9.59e-14 | 9.59e-14 | 3.87e-14 | 9.59e-14 | 1.59e-13 | 1.24e-11 | 0006 | R(0, 0) s to s | PASS |
| torcwa / grcwa | 14/14 | 9.71e-16 | 3.55e-15 | 2.66e-15 | 3.55e-15 | 2e-15 | 8.23e-14 | 0006 | T(0, 0) p to p | PASS |
| torcwa / lumerical | 14/14 | 9.6e-14 | 9.59e-14 | 3.63e-14 | 9.6e-14 | 1.59e-13 | 1.24e-11 | 0006 | R(0, 0) s to s | PASS |
| grcwa / lumerical | 14/14 | 9.63e-14 | 9.59e-14 | 3.63e-14 | 9.63e-14 | 1.59e-13 | 1.24e-11 | 0006 | R(0, 0) s to s | PASS |
