# A01 — Fresnel interface

Compare both incidence directions against Fresnel coefficients, including Brewster reflection and total internal reflection.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run A/A01 --profile quick
rcwa-cv converge A/A01
```

See the [category consistency table](../../../results/A/consistency.md).
