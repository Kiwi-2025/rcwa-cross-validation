# B03 solver comparison

Power is normalized to incident flux. Phase is compared above the channel-power floor. Periodic quick runs give provisional differences. See [point coordinates](points.csv).

| Solver pair | Matched points | Max R difference | Max T difference | Max A difference | Max order-power difference | Max complex-amplitude difference | Max phase difference (deg) | Worst amplitude point | Worst amplitude channel | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meent / torcwa | 5/5 | 0.00387 | 0.00387 | 3.1e-14 | 0.00628 | 0.0158 | 7.7 | 0000 | T(-2, 0) p to p | INCONCLUSIVE |
| meent / grcwa | 5/5 | 0.00387 | 0.00387 | 2.45e-14 | 0.00628 | 0.0158 | 7.7 | 0000 | T(-2, 0) p to p | INCONCLUSIVE |
| meent / lumerical | 5/5 | 0.00196 | 0.00196 | 4.41e-13 | 0.00326 | 0.0177 | 4.44 | 0001 | T(1, 0) s to s | INCONCLUSIVE |
| torcwa / grcwa | 5/5 | 1.2e-14 | 4.42e-14 | 5.55e-14 | 4.18e-14 | 1.3e-13 | 4.69e-11 | 0004 | T(-1, 0) s to p | INCONCLUSIVE |
| torcwa / lumerical | 5/5 | 0.00191 | 0.00191 | 4.38e-13 | 0.00303 | 0.017 | 5.76 | 0000 | T(-1, 0) s to p | INCONCLUSIVE |
| grcwa / lumerical | 5/5 | 0.00191 | 0.00191 | 4.37e-13 | 0.00303 | 0.017 | 5.76 | 0000 | T(-1, 0) s to p | INCONCLUSIVE |
