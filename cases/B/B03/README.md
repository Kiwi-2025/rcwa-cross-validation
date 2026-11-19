# B03 — Conical incidence

## Physical scenario

The rectangular structure of B01 is illuminated at an oblique polar angle and at an azimuth that is neither parallel nor perpendicular to the ridge direction. The diffracted beams leave in different planes. The resulting vector problem can mix the incident and outgoing s and p components.

## Possible applications

Relevant to grating spectrometers in off-plane mounts, oblique illumination in optical instruments, and polarization-sensitive scatterometry. The off-diagonal amplitudes are especially useful for checking polarization bases.

## Benchmark objective

Compare cross-polarized complex diffraction amplitudes for off-axis illumination of the B01 structure.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [B03.ipynb](B03.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run B/B03
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#b03) · [Numerical dataset](../../../results/benchmark.json)
