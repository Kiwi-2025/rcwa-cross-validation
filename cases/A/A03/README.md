# A03 — DBR mirror

## Physical scenario

An eight-pair stack alternates high- and low-index dielectric films, each with one-quarter-wave optical thickness at 1550 nm. Reflections from successive interfaces add coherently near the design wavelength and produce a stopband. Sweeping through the stopband and its edges probes layer order and reflection phase.

## Possible applications

Represents a distributed Bragg reflector used as a laser cavity mirror, an optical filter element, or a high-reflectance coating for near-infrared photonics.

## Benchmark objective

Check layer order, stopband and phase for eight quarter-wave dielectric pairs at a design wavelength of 1550 nm.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [A03.ipynb](A03.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run A/A03
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#a03) · [Numerical dataset](../../../results/benchmark.json)
