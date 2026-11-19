# C02 — Photonic crystal slab

## Physical scenario

A dielectric slab contains a square lattice of air holes. The periodic modulation couples normally incident light to slab modes that can leak back into free space. Their interference with direct transmission produces narrow spectral features, so comparisons near resonance depend on both spectral sampling and numerical refinement.

## Possible applications

Guided resonances in photonic crystal slabs are used in narrowband filters, wavelength-selective reflectors, and refractive-index sensors. [Ansys photonic crystal slab benchmark](https://optics.ansys.com/hc/en-us/articles/4416343906067-Photonic-Crystal-Slab-RCWA)

## Benchmark objective

Reproduce the guided-resonance spectrum from the [S4 paper](https://web.stanford.edu/group/fan/publication/Liu_ComputerPhysicsCommunications_183_2233_2012.pdf) and the [Ansys example](https://optics.ansys.com/hc/en-us/articles/4416343906067-Photonic-Crystal-Slab-RCWA). Compare the transmission peaks near normalized frequencies 0.5058, 0.5260 and 0.5420.

The geometry, materials, and sweep are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths are in nanometers. Angles are in degrees.

## Reproduce

- Open [C02.ipynb](C02.ipynb) to run the four solvers and draw the comparison plots.
- Open [model.fsp](model.fsp) in Lumerical FDTD to inspect quick-sweep point 0, or use [model.lsf](model.lsf) to rebuild it in a new unsaved document.

```powershell
rcwa-cv run C/C02
```

[Comparison tables and figures](../../../BENCHMARK_REPORT.md#c02) · [Numerical dataset](../../../results/benchmark.json)
