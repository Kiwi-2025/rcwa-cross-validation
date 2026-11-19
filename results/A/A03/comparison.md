# A03 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference / meent | 5/5 | 1.08e-15 | 3e-15 | 2.89e-15 | 3e-15 | 3.73e-15 | 2.13e-13 | 0001 | T(0, 0) p to p | PASS |
| reference / torcwa | 5/5 | 8.88e-16 | 2.33e-15 | 3e-15 | 2.33e-15 | 3.41e-15 | 4.03e-13 | 0001 | T(0, 0) p to p | PASS |
| reference / grcwa | 5/5 | 1.12e-15 | 2.78e-15 | 3.55e-15 | 2.78e-15 | 4.27e-15 | 4.82e-13 | 0000 | T(0, 0) s to s | PASS |
| reference / s4 | 5/5 | 7.91e-16 | 2e-15 | 2.66e-15 | 2e-15 | 4.41e-15 | 2.59e-13 | 0000 | T(0, 0) s to s | PASS |
| reference / lumerical | 5/5 | 2.05e-14 | 2.53e-13 | 2.54e-13 | 2.53e-13 | 1.38e-13 | 1.96e-11 | 0001 | T(0, 0) p to p | PASS |
| meent / torcwa | 5/5 | 7.22e-16 | 4.55e-15 | 4.11e-15 | 4.55e-15 | 2.49e-15 | 2.81e-13 | 0001 | T(0, 0) s to s | PASS |
| meent / grcwa | 5/5 | 1.29e-15 | 5.33e-15 | 6e-15 | 5.33e-15 | 4.48e-15 | 3.6e-13 | 0000 | T(0, 0) p to p | PASS |
| meent / s4 | 5/5 | 7.63e-16 | 4.55e-15 | 5.11e-15 | 4.55e-15 | 4.55e-15 | 2.6e-13 | 0000 | T(0, 0) p to p | PASS |
| meent / lumerical | 5/5 | 2.06e-14 | 2.55e-13 | 2.55e-13 | 2.55e-13 | 1.38e-13 | 1.95e-11 | 0001 | T(0, 0) p to p | PASS |
| torcwa / grcwa | 5/5 | 1.28e-15 | 4.44e-15 | 5.66e-15 | 4.44e-15 | 6.02e-15 | 3.33e-13 | 0000 | T(0, 0) s to s | PASS |
| torcwa / s4 | 5/5 | 1.18e-15 | 3.66e-15 | 4.77e-15 | 3.66e-15 | 6.11e-15 | 3.47e-13 | 0000 | T(0, 0) s to s | PASS |
| torcwa / lumerical | 5/5 | 2.08e-14 | 2.51e-13 | 2.51e-13 | 2.51e-13 | 1.36e-13 | 1.92e-11 | 0001 | T(0, 0) s to s | PASS |
| grcwa / s4 | 5/5 | 6.87e-16 | 7.77e-16 | 9.99e-16 | 7.77e-16 | 1.8e-15 | 2.68e-13 | 0001 | R(0, 0) s to s | PASS |
| grcwa / lumerical | 5/5 | 1.99e-14 | 2.53e-13 | 2.52e-13 | 2.53e-13 | 1.36e-13 | 1.92e-11 | 0001 | T(0, 0) s to s | PASS |
| s4 / lumerical | 5/5 | 1.99e-14 | 2.53e-13 | 2.53e-13 | 2.53e-13 | 1.37e-13 | 1.94e-11 | 0001 | T(0, 0) s to s | PASS |
