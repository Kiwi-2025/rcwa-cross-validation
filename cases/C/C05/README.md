# C05 — Shifted bilayer

## Physical scenario

Two patterned dielectric layers are separated by a spacer. The upper and lower patterns have different rectangular cross-sections. Moving one layer laterally by a fraction of the period changes their alignment and coupling, which can change the spectrum and transmission phase.

## Possible applications

Models the alignment problem in stacked metasurfaces and multilayer diffractive filters. Comparing several offsets can help separate intentional coupling from fabrication overlay sensitivity.

## Benchmark objective

Compare layer-to-layer coupling and phase when the upper patterned layer is displaced relative to the lower layer.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [C05.ipynb](C05.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run C/C05
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#c05) · [Numerical dataset](../../../results/benchmark.json)
