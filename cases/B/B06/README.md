# B06 — Volume index grating

## Physical scenario

A 10 µm thick film contains a weak sinusoidal index modulation across the grating direction. The neighboring media match its mean index. Varying incidence angle through the Bragg condition transfers energy from the incident beam to a selected transmitted order within a narrow angular band.

## Possible applications

This is the mechanism of angle-selective volume holograms and Bragg couplers, including waveguide couplers for display optics. [Ansys volume holographic grating example](https://optics.ansys.com/hc/en-us/articles/37118679173267-Volume-Holographic-Grating)

## Benchmark objective

Compare the Bragg angular response of a thick sinusoidal index grating in index-matched surroundings.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [B06.ipynb](B06.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run B/B06
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#b06) · [Numerical dataset](../../../results/benchmark.json)
