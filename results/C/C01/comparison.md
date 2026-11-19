# C01 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 5/5 | 0.106 | 0.126 | 0.0362 | 0.106 | 0.117 | 9.33 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
| meent / grcwa | 5/5 | 0.106 | 0.126 | 0.0362 | 0.106 | 0.117 | 9.33 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 5/5 | 0.136 | 0.141 | 0.0172 | 0.136 | 0.103 | 23.7 | 0003 | T(0, 0) s to s | INCONCLUSIVE |
| torcwa / grcwa | 5/5 | 2.66e-15 | 3.28e-15 | 2.22e-15 | 2.66e-15 | 2.93e-15 | 7.06e-13 | 0000 | T(0, 1) s to p | INCONCLUSIVE |
| torcwa / lumerical | 5/5 | 0.0298 | 0.0507 | 0.0209 | 0.0298 | 0.0524 | 7.67 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
| grcwa / lumerical | 5/5 | 0.0298 | 0.0507 | 0.0209 | 0.0298 | 0.0524 | 7.67 | 0000 | T(-1, 0) p to p | INCONCLUSIVE |
