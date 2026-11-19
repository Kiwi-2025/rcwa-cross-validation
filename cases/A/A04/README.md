# A04 — Absorbing metal film

Check passive absorption and phase against the thin-film reference. The metal uses a fixed illustrative near-infrared permittivity.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run A/A04 --profile quick
rcwa-cv converge A/A04
```

See the [category consistency table](../../../results/A/consistency.md).

## Notebook and Lumerical model

- [Open the Jupyter notebook](A04.ipynb) to run each solver and generate the plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0.
- Run [model.lsf](model.lsf) in a new unsaved FDTD document to reconstruct that point and export the native results.

## Benchmark figures

![Nominal geometry](figures/geometry.png)

![Reflection, transmission and phase](figures/spectrum-0.png)

![Propagating diffraction-order efficiencies](figures/diffraction-orders.png)

![Pairwise solver differences](figures/solver-differences.png)

See the [pairwise table](../../../results/A/A04/comparison.md) for numerical differences and [sweep coordinates](../../../results/A/A04/points.csv).
