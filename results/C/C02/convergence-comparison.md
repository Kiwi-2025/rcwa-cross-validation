# C02 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](convergence-points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 1/1 | 0.0127 | 0.0127 | 3.11e-15 | 0.0127 | 0.0157 | 0.968 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
| meent / grcwa | 1/1 | 0.0127 | 0.0127 | 1.11e-15 | 0.0127 | 0.0157 | 0.968 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
| meent / s4 | 1/1 | 0.0125 | 0.0125 | 3.33e-15 | 0.0125 | 0.0154 | 0.946 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
| meent / lumerical | 1/1 | 0.00921 | 0.00921 | 1.69e-14 | 0.00921 | 0.0115 | 0.71 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
| torcwa / grcwa | 1/1 | 6.11e-15 | 3.33e-15 | 2.66e-15 | 6.11e-15 | 1.77e-14 | 1.24e-12 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
| torcwa / s4 | 1/1 | 0.000204 | 0.000204 | 4.44e-16 | 0.000204 | 0.000334 | 0.0221 | 0000 | R(0, 0) p to p | INCONCLUSIVE |
| torcwa / lumerical | 1/1 | 0.00347 | 0.00347 | 2e-14 | 0.00347 | 0.00421 | 0.258 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
| grcwa / s4 | 1/1 | 0.000204 | 0.000204 | 2.89e-15 | 0.000204 | 0.000334 | 0.0221 | 0000 | R(0, 0) p to p | INCONCLUSIVE |
| grcwa / lumerical | 1/1 | 0.00347 | 0.00347 | 1.73e-14 | 0.00347 | 0.00421 | 0.258 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
| s4 / lumerical | 1/1 | 0.00326 | 0.00326 | 2.02e-14 | 0.00326 | 0.00388 | 0.236 | 0000 | R(0, 0) s to s | INCONCLUSIVE |
