# B01 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](convergence-points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 1/1 | 0.000474 | 0.000474 | 5.82e-14 | 0.000891 | 0.0033 | 0.347 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / grcwa | 1/1 | 0.000474 | 0.000474 | 1.28e-13 | 0.000891 | 0.0033 | 0.347 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / s4 | 1/1 | 0.000477 | 0.000477 | 2.05e-13 | 0.000899 | 0.00332 | 0.349 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 1/1 | 0.00024 | 0.00024 | 6.46e-13 | 0.000443 | 0.00238 | 0.245 | 0000 | T(1, 0) p to p | INCONCLUSIVE |
| torcwa / grcwa | 1/1 | 6.79e-14 | 1.86e-13 | 1.55e-13 | 2.79e-13 | 3.48e-13 | 8.56e-11 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| torcwa / s4 | 1/1 | 2.7e-06 | 2.7e-06 | 2.63e-13 | 7.29e-06 | 2.31e-05 | 0.0024 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| torcwa / lumerical | 1/1 | 0.000234 | 0.000234 | 6.18e-13 | 0.000448 | 0.0024 | 0.247 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
| grcwa / s4 | 1/1 | 2.7e-06 | 2.7e-06 | 2.76e-13 | 7.29e-06 | 2.31e-05 | 0.0024 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| grcwa / lumerical | 1/1 | 0.000234 | 0.000234 | 7.74e-13 | 0.000448 | 0.0024 | 0.247 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
| s4 / lumerical | 1/1 | 0.000236 | 0.000236 | 7.52e-13 | 0.000456 | 0.00241 | 0.248 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
