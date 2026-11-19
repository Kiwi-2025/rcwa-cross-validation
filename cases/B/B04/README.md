# B04 — Trapezoidal grating

Compare diffraction from an etched relief with independent Fourier and vertical slice refinement.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run B/B04 --profile quick
rcwa-cv converge B/B04
```

See the [category consistency table](../../../results/B/consistency.md).
