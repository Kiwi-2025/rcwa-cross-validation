# B04 — Trapezoidal grating

## Physical scenario

Each dielectric ridge has sloped sidewalls, so the ridge width changes through its thickness. The model represents this profile with a stack of constant-width slices. Fourier truncation measures lateral accuracy and slice refinement measures the accuracy of the sidewall representation.

## Possible applications

Represents fabricated relief gratings and optical metrology targets. It can be used to study how etch depth and sidewall angle affect diffraction efficiency before comparing a fabricated device with simulations.

## Benchmark objective

Compare diffraction from an etched relief with independent Fourier and vertical slice refinement.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [B04.ipynb](B04.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run B/B04
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#b04) · [Numerical dataset](../../../results/benchmark.json)
