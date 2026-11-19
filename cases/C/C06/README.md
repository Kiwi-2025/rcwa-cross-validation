# C06 — Metagrating supercell

## Physical scenario

Four dielectric pillars with different widths repeat as a supercell. Their different scattering phases can redistribute transmitted power among several propagating orders. The benchmark tracks the intended (+1, 0) order as well as power sent to specular and other unwanted orders.

## Possible applications

This setup represents metagratings and beam-deflecting metasurfaces for beam routing, compact projectors, and diffractive couplers. The target order efficiency is a more direct design metric than total transmission.

## Benchmark objective

Compare power in the target (+1, 0) transmitted order and other orders of a four-pillar beam-steering supercell.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [C06.ipynb](C06.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run C/C06
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#c06) · [Numerical dataset](../../../results/benchmark.json)
