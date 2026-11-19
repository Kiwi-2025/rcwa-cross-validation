# C05 — Shifted bilayer

Compare layer-to-layer coupling and phase when the upper patterned layer is displaced relative to the lower layer.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run C/C05 --profile quick
rcwa-cv converge C/C05
```

See the [category consistency table](../../../results/C/consistency.md).

## Notebook and Lumerical model

- [Open the Jupyter notebook](C05.ipynb) to run each solver and generate the plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0.
- Run [model.lsf](model.lsf) in a new unsaved FDTD document to reconstruct that point and export the native results.

## Benchmark figures

![Nominal geometry](figures/geometry.png)

![Reflection, transmission and phase](figures/spectrum-0.png)

![Propagating diffraction-order efficiencies](figures/diffraction-orders.png)

![Pairwise solver differences](figures/solver-differences.png)

See the [pairwise table](../../../results/C/C05/comparison.md) for numerical differences and [sweep coordinates](../../../results/C/C05/points.csv).
