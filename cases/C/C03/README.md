# C03 — Cylindrical meta-atom

## Physical scenario

A square array of cylindrical dielectric pillars is illuminated at fixed wavelength while the pillar radius varies. Changing radius changes the modal response and therefore the transmission amplitude and phase. The symmetric nominal cell also makes the two linear polarizations a useful consistency check.

## Possible applications

The radius sweep is the basis of a unit-cell library for metalenses and other phase-gradient metasurfaces. Design would select geometries that supply the required phase while maintaining useful transmission.

## Benchmark objective

Compare transmitted phase and efficiency as the radius of a dielectric pillar changes.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [C03.ipynb](C03.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run C/C03
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#c03) · [Numerical dataset](../../../results/benchmark.json)
