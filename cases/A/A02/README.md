# A02 — Antireflection film

Check the reflection minimum and complex transmission against an independent thin-film calculation.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run A/A02 --profile quick
rcwa-cv converge A/A02
```

See the [category consistency table](../../../results/A/consistency.md).
