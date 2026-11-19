# C06 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 4/4 | 0.204 | 0.204 | 8.39e-14 | 0.537 | 1.21 | 170 | 0000 | T(1, 0) p to p | INCONCLUSIVE |
| meent / grcwa | 4/4 | 0.204 | 0.204 | 1.45e-13 | 0.537 | 1.21 | 170 | 0000 | T(1, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 4/4 | 0.209 | 0.209 | 1.88e-13 | 0.664 | 1.11 | 179 | 0001 | T(1, 0) p to p | INCONCLUSIVE |
| torcwa / grcwa | 4/4 | 1.67e-13 | 1.4e-13 | 6.08e-14 | 3.05e-13 | 4.81e-13 | 1.25e-10 | 0002 | T(2, 0) s to s | INCONCLUSIVE |
| torcwa / lumerical | 4/4 | 0.186 | 0.186 | 2.19e-13 | 0.238 | 0.824 | 176 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| grcwa / lumerical | 4/4 | 0.186 | 0.186 | 2.8e-13 | 0.238 | 0.824 | 176 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
