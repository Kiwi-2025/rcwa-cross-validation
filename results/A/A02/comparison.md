# A02 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference / meent | 5/5 | 1.04e-17 | 5.55e-16 | 5.55e-16 | 5.55e-16 | 4.57e-16 | 5.35e-13 | 0003 | R(0, 0) p to p | PASS |
| reference / torcwa | 5/5 | 1.56e-17 | 4.44e-16 | 5.55e-16 | 4.44e-16 | 3.51e-16 | 2.41e-13 | 0004 | T(0, 0) s to s | PASS |
| reference / grcwa | 5/5 | 4.16e-17 | 8.88e-16 | 8.88e-16 | 8.88e-16 | 5.66e-16 | 3.04e-13 | 0000 | T(0, 0) s to s | PASS |
| reference / s4 | 5/5 | 2.26e-17 | 2.22e-16 | 2.22e-16 | 2.22e-16 | 4e-16 | 1.81e-13 | 0000 | T(0, 0) s to s | PASS |
| reference / lumerical | 5/5 | 6.02e-16 | 1.38e-14 | 1.43e-14 | 1.38e-14 | 7.94e-15 | 1.85e-12 | 0000 | T(0, 0) s to s | PASS |
| meent / torcwa | 5/5 | 1.91e-17 | 5.55e-16 | 6.66e-16 | 5.55e-16 | 3.89e-16 | 4.44e-13 | 0003 | R(0, 0) s to s | PASS |
| meent / grcwa | 5/5 | 4.51e-17 | 1.22e-15 | 1.22e-15 | 1.22e-15 | 6.75e-16 | 5.17e-13 | 0000 | T(0, 0) s to s | PASS |
| meent / s4 | 5/5 | 2.6e-17 | 3.33e-16 | 3.33e-16 | 3.33e-16 | 5.55e-16 | 3.93e-13 | 0000 | T(0, 0) p to p | PASS |
| meent / lumerical | 5/5 | 6.12e-16 | 1.41e-14 | 1.47e-14 | 1.41e-14 | 7.9e-15 | 2.16e-12 | 0000 | T(0, 0) p to p | PASS |
| torcwa / grcwa | 5/5 | 2.6e-17 | 6.66e-16 | 7.77e-16 | 6.66e-16 | 5.66e-16 | 1.89e-13 | 0000 | T(0, 0) s to s | PASS |
| torcwa / s4 | 5/5 | 6.94e-18 | 4.44e-16 | 5.55e-16 | 4.44e-16 | 5.98e-16 | 1.34e-13 | 0000 | T(0, 0) s to s | PASS |
| torcwa / lumerical | 5/5 | 6.14e-16 | 1.42e-14 | 1.48e-14 | 1.42e-14 | 8.05e-15 | 1.72e-12 | 0000 | T(0, 0) s to s | PASS |
| grcwa / s4 | 5/5 | 1.91e-17 | 8.88e-16 | 9.99e-16 | 8.88e-16 | 5.55e-16 | 1.26e-13 | 0000 | T(0, 0) s to s | PASS |
| grcwa / lumerical | 5/5 | 6.4e-16 | 1.47e-14 | 1.52e-14 | 1.47e-14 | 8.49e-15 | 1.65e-12 | 0000 | T(0, 0) s to s | PASS |
| s4 / lumerical | 5/5 | 6.21e-16 | 1.38e-14 | 1.43e-14 | 1.38e-14 | 8e-15 | 1.77e-12 | 0000 | T(0, 0) s to s | PASS |
