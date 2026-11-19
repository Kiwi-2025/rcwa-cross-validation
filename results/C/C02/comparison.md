# C02 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 5/5 | 0.991 | 0.991 | 2.09e-13 | 0.991 | 1.02 | 120 | 0002 | T(0, 0) s to s | INCONCLUSIVE |
| meent / grcwa | 5/5 | 0.991 | 0.991 | 4.61e-13 | 0.991 | 1.02 | 120 | 0002 | T(0, 0) s to s | INCONCLUSIVE |
| meent / lumerical | 5/5 | 0.962 | 0.962 | 7.9e-13 | 0.962 | 0.965 | 115 | 0003 | R(0, 0) p to p | INCONCLUSIVE |
| torcwa / grcwa | 5/5 | 3.22e-13 | 3.02e-13 | 5.2e-13 | 3.22e-13 | 1.86e-12 | 1.07e-10 | 0001 | T(0, 0) s to s | INCONCLUSIVE |
| torcwa / lumerical | 5/5 | 0.459 | 0.459 | 8.19e-13 | 0.459 | 0.464 | 27.8 | 0002 | T(0, 0) p to p | INCONCLUSIVE |
| grcwa / lumerical | 5/5 | 0.459 | 0.459 | 1.25e-12 | 0.459 | 0.464 | 27.8 | 0002 | T(0, 0) p to p | INCONCLUSIVE |
