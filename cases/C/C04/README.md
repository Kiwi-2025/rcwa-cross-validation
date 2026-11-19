# C04 — Rotated nanofin

## Physical scenario

An anisotropic rectangular dielectric nanofin is rotated within a square unit cell. Its principal axes have different complex transmission coefficients. Rotation mixes the lab-frame polarization components, making the full Jones matrix and the opposite-helicity transmission useful observables.

## Possible applications

Rotated elements are used in geometric-phase metasurfaces, polarization converters, and vector-beam optics. The benchmark evaluates the unit-cell response without assuming ideal half-wave retardance.

## Benchmark objective

Compare Jones matrices and circular-polarization conversion under in-plane rotation.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [C04.ipynb](C04.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run C/C04
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#c04) · [Numerical dataset](../../../results/benchmark.json)
