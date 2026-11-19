# A04 — Absorbing metal film

## Physical scenario

A 30 nm metal film sits between air and glass and is illuminated at normal incidence. Its complex permittivity causes absorption in addition to reflection and transmission. The benchmark uses a fixed illustrative permittivity, so the sweep isolates thin-film interference and loss handling.

## Possible applications

A starting point for modeling thin metallic mirrors, neutral-density coatings, or partially transmitting electrodes. A real device would require wavelength-dependent material data and a specified film morphology.

## Benchmark objective

Check passive absorption and phase against the thin-film reference. The metal uses a fixed illustrative near-infrared permittivity.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [A04.ipynb](A04.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run A/A04
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#a04) · [Numerical dataset](../../../results/benchmark.json)
