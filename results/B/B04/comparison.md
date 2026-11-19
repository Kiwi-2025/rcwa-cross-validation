# B04 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 4/4 | 0.000306 | 0.000306 | 7.03e-14 | 0.00579 | 0.0152 | 4.9 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / grcwa | 4/4 | 0.000306 | 0.000306 | 6.82e-14 | 0.00579 | 0.0152 | 4.9 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 4/4 | 0.000573 | 0.000573 | 4.12e-14 | 0.004 | 0.0188 | 5.08 | 0000 | T(1, 0) p to p | INCONCLUSIVE |
| torcwa / grcwa | 4/4 | 8.43e-15 | 1.01e-14 | 8.66e-15 | 8.43e-15 | 6.25e-14 | 2.36e-11 | 0002 | R(0, 0) s to s | INCONCLUSIVE |
| torcwa / lumerical | 4/4 | 0.00053 | 0.00053 | 2.91e-14 | 0.00178 | 0.0153 | 3.83 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
| grcwa / lumerical | 4/4 | 0.00053 | 0.00053 | 2.7e-14 | 0.00178 | 0.0153 | 3.83 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
