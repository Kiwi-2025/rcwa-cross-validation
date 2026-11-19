# B02 — High-contrast grating

Compare polarized reflectance, transmittance and phase for a subwavelength high-index grating.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run B/B02 --profile quick
rcwa-cv converge B/B02
```

See the [category consistency table](../../../results/B/consistency.md).

## Notebook and Lumerical model

- [Open the Jupyter notebook](B02.ipynb) to run each solver and generate the plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0.
- Run [model.lsf](model.lsf) in a new unsaved FDTD document to reconstruct that point and export the native results.

## Benchmark figures

![Nominal geometry](figures/geometry.png)

![Reflection, transmission and phase](figures/spectrum-0.png)

![Propagating diffraction-order efficiencies](figures/diffraction-orders.png)

![Pairwise solver differences](figures/solver-differences.png)

See the [pairwise table](../../../results/B/B02/comparison.md) for numerical differences and [sweep coordinates](../../../results/B/B02/points.csv).
