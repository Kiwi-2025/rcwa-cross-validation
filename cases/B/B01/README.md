# B01 — Binary dielectric grating

## Physical scenario

A binary grating consists of rectangular dielectric ridges on a substrate. Its period is comparable to the swept wavelength, so multiple diffraction orders can propagate. A Rayleigh cutoff occurs when an order becomes grazing and crosses between propagation and evanescence.

## Possible applications

This geometry is a baseline for transmissive diffraction gratings, beam splitters, and diffractive encoders. Resolving individual orders matters when only one beam or a narrow angular range is collected.

## Benchmark objective

Compare individual propagating orders and order cutoffs. Sample both sides of Rayleigh thresholds.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [B01.ipynb](B01.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run B/B01
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#b01) · [Numerical dataset](../../../results/benchmark.json)
