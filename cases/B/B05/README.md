# B05 — Wire-grid polarizer

Compare polarized transmission, absorption and extinction for a metal wire-grid polarizer.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run B/B05 --profile quick
rcwa-cv converge B/B05
```

See the [category consistency table](../../../results/B/consistency.md).

## Notebook and Lumerical model

- [Open the Jupyter notebook](B05.ipynb) to run each solver and generate the plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0.
- Run [model.lsf](model.lsf) in a new unsaved FDTD document to reconstruct that point and export the native results.

## Benchmark figures

![Nominal geometry](figures/geometry.png)

![Reflection, transmission and phase](figures/spectrum-0.png)

![Propagating diffraction-order efficiencies](figures/diffraction-orders.png)

![Pairwise solver differences](figures/solver-differences.png)

See the [pairwise table](../../../results/B/B05/comparison.md) for numerical differences and [sweep coordinates](../../../results/B/B05/points.csv).
