# B01 — Binary dielectric grating

Compare individual propagating orders and order cutoffs. Sample both sides of Rayleigh thresholds.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run B/B01 --profile quick
rcwa-cv converge B/B01
```

See the [category consistency table](../../../results/B/consistency.md).
