# C05 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 12/12 | 0.0208 | 0.0208 | 1.07e-14 | 0.0208 | 0.123 | 9.89 | 0008 | T(0, 0) s to s | INCONCLUSIVE |
| meent / grcwa | 12/12 | 0.0208 | 0.0208 | 4.91e-14 | 0.0208 | 0.123 | 9.89 | 0008 | T(0, 0) s to s | INCONCLUSIVE |
| meent / s4 | 12/12 | 0.0176 | 0.0176 | 6.92e-13 | 0.0176 | 0.112 | 8.09 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 12/12 | 0.00679 | 0.00679 | 1.33e-13 | 0.00679 | 0.053 | 5.71 | 0008 | T(0, 0) s to s | INCONCLUSIVE |
| torcwa / grcwa | 12/12 | 6.39e-14 | 1.84e-14 | 4.55e-14 | 6.39e-14 | 5.22e-13 | 2.44e-10 | 0011 | R(0, 0) s to s | INCONCLUSIVE |
| torcwa / s4 | 12/12 | 0.00325 | 0.00325 | 6.89e-13 | 0.00325 | 0.0146 | 5.57 | 0008 | T(0, 0) s to s | INCONCLUSIVE |
| torcwa / lumerical | 12/12 | 0.014 | 0.014 | 1.41e-13 | 0.014 | 0.0724 | 11 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| grcwa / s4 | 12/12 | 0.00325 | 0.00325 | 6.43e-13 | 0.00325 | 0.0146 | 5.57 | 0008 | T(0, 0) s to s | INCONCLUSIVE |
| grcwa / lumerical | 12/12 | 0.014 | 0.014 | 1.23e-13 | 0.014 | 0.0724 | 11 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| s4 / lumerical | 12/12 | 0.0108 | 0.0108 | 6.98e-13 | 0.0108 | 0.0615 | 5.46 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
