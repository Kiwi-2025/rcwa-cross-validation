# A02 — Antireflection film

## Physical scenario

A single lossless dielectric film separates air and glass. Its optical thickness is one quarter of the 550 nm design wavelength. At normal incidence the two main reflected fields cancel near the design point, while the transmitted field accumulates a wavelength-dependent phase.

## Possible applications

Models the basic mechanism of single-layer antireflection coatings on lenses, windows, and sensor covers. This is an idealized index-matching example for checking spectral reflectance and transmitted phase.

## Benchmark objective

Check the reflection minimum and complex transmission against an independent thin-film calculation.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [A02.ipynb](A02.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run A/A02
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#a02) · [Numerical dataset](../../../results/benchmark.json)
