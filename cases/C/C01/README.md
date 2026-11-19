# C01 — Metal nanohole array

## Physical scenario

A lossy metal film is perforated by a square array of circular apertures. Aperture fields, lattice diffraction, and coupling to fields at the metal interfaces can all influence transmission. The complex material response makes absorption part of the energy balance.

## Possible applications

Metallic hole arrays are studied for wavelength-selective transmission and plasmonic sensing. The benchmark is an idealized fixed-permittivity model of this family of structures. [Original hole-array transmission experiment](https://www.nature.com/articles/35570)

## Benchmark objective

Compare the spectrum, absorption and diffraction of a periodic perforated metal film.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [C01.ipynb](C01.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run C/C01
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#c01) · [Numerical dataset](../../../results/benchmark.json)
