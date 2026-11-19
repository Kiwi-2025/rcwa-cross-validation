# B05 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 3/3 | 0.116 | 0.268 | 0.152 | 0.268 | 0.203 | 8.67 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / grcwa | 3/3 | 0.116 | 0.268 | 0.152 | 0.268 | 0.203 | 8.67 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / s4 | 3/3 | 0.121 | 0.262 | 0.141 | 0.262 | 0.205 | 9.21 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 3/3 | 0.016 | 0.0191 | 0.0031 | 0.0191 | 0.0281 | 1.61 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| torcwa / grcwa | 3/3 | 2.75e-13 | 3.98e-13 | 1.23e-13 | 3.98e-13 | 3.89e-13 | 2.57e-11 | 0002 | T(0, 0) p to p | INCONCLUSIVE |
| torcwa / s4 | 3/3 | 0.0053 | 0.00629 | 0.0107 | 0.00629 | 0.00857 | 0.916 | 0001 | T(0, 0) p to p | INCONCLUSIVE |
| torcwa / lumerical | 3/3 | 0.0995 | 0.248 | 0.149 | 0.248 | 0.18 | 7.31 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| grcwa / s4 | 3/3 | 0.0053 | 0.00629 | 0.0107 | 0.00629 | 0.00857 | 0.916 | 0001 | T(0, 0) p to p | INCONCLUSIVE |
| grcwa / lumerical | 3/3 | 0.0995 | 0.248 | 0.149 | 0.248 | 0.18 | 7.31 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
| s4 / lumerical | 3/3 | 0.105 | 0.243 | 0.138 | 0.243 | 0.182 | 7.6 | 0000 | T(0, 0) p to p | INCONCLUSIVE |
