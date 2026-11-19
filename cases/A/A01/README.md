# A01 — Fresnel interface

## Physical scenario

A plane wave meets a single, flat air–glass boundary. The angular sweep runs in both directions. Air-to-glass incidence shows the Brewster minimum for p polarization, while glass-to-air incidence crosses into total internal reflection. The reflected phase above the critical angle is part of the comparison.

## Possible applications

Useful as a reference for prism coupling, total-internal-reflection illumination, and polarization at glass windows. The Fresnel solution also gives a direct check on amplitude normalization and forward/reverse incidence conventions.

## Benchmark objective

Compare both incidence directions against Fresnel coefficients, including Brewster reflection and total internal reflection.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [A01.ipynb](A01.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run A/A01
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#a01) · [Numerical dataset](../../../results/benchmark.json)
