# B06 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 7/7 | 1.74e-08 | 1.74e-08 | 4.2e-14 | 9.06e-05 | 8.69e-05 | 0.00623 | 0002 | T(0, 0) s to s | INCONCLUSIVE |
| meent / grcwa | 7/7 | 1.74e-08 | 1.74e-08 | 6.65e-14 | 9.06e-05 | 8.69e-05 | 0.00623 | 0002 | T(0, 0) s to s | INCONCLUSIVE |
| meent / s4 | 7/7 | 2.81e-10 | 2.81e-10 | 4.3e-14 | 1.78e-07 | 5.04e-06 | 0.00049 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 7/7 | 1.53e-08 | 1.53e-08 | 4.54e-13 | 7.96e-05 | 0.0196 | 2.65 | 0003 | T(-1, 0) s to s | INCONCLUSIVE |
| torcwa / grcwa | 7/7 | 5.52e-14 | 3.06e-14 | 2.81e-14 | 7.7e-14 | 1.08e-11 | 1.74e-11 | 0005 | R(-2, 0) p to p | INCONCLUSIVE |
| torcwa / s4 | 7/7 | 1.74e-08 | 1.74e-08 | 3.66e-14 | 9.06e-05 | 8.69e-05 | 0.00623 | 0002 | T(0, 0) s to s | INCONCLUSIVE |
| torcwa / lumerical | 7/7 | 3.28e-08 | 3.28e-08 | 4.72e-13 | 0.00017 | 0.0196 | 2.65 | 0003 | T(-1, 0) s to s | INCONCLUSIVE |
| grcwa / s4 | 7/7 | 1.74e-08 | 1.74e-08 | 6.12e-14 | 9.06e-05 | 8.69e-05 | 0.00623 | 0002 | T(0, 0) s to s | INCONCLUSIVE |
| grcwa / lumerical | 7/7 | 3.28e-08 | 3.28e-08 | 4.96e-13 | 0.00017 | 0.0196 | 2.65 | 0003 | T(-1, 0) s to s | INCONCLUSIVE |
| s4 / lumerical | 7/7 | 1.53e-08 | 1.53e-08 | 4.35e-13 | 7.96e-05 | 0.0196 | 2.65 | 0003 | T(-1, 0) s to s | INCONCLUSIVE |
