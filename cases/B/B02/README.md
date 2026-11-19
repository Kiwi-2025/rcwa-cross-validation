# B02 — High-contrast grating

## Physical scenario

High-index rectangular bars form a one-dimensional subwavelength grating. Even with only the zeroth order propagating in the exterior media over the modeled band, the patterned layer supports internal modes and polarization-dependent interference. The case compares both efficiency and phase.

## Possible applications

High-contrast gratings are used as thin mirrors and polarization-selective elements, including compact mirrors for vertical-cavity surface-emitting lasers. [Demonstrated high-contrast grating VCSEL](https://doi.org/10.1364/CLEO.2009.CThB1)

## Benchmark objective

Compare polarized reflectance, transmittance and phase for a subwavelength high-index grating.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [B02.ipynb](B02.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run B/B02
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#b02) · [Numerical dataset](../../../results/benchmark.json)
