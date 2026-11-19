# B05 — Wire-grid polarizer

## Physical scenario

A subwavelength array of lossy metal wires discriminates between electric fields parallel and perpendicular to the wires. Currents driven along the wires can suppress transmission through reflection and absorption. The benchmark compares extinction together with the reflected, transmitted, and absorbed power.

## Possible applications

Wire grids are used as compact infrared polarizers and polarizing beam splitters in imaging, spectroscopy, and thermal optics. The illustrative metal permittivity here should be replaced by measured dispersion for performance predictions.

## Benchmark objective

Compare polarized transmission, absorption and extinction for a metal wire-grid polarizer.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [B05.ipynb](B05.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run B/B05
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#b05) · [Numerical dataset](../../../results/benchmark.json)
