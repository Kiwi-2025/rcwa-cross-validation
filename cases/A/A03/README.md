# A03 — DBR mirror

Check layer order, stopband and phase for eight quarter-wave dielectric pairs at a design wavelength of 1550 nm.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run A/A03 --profile quick
rcwa-cv converge A/A03
```

See the [category consistency table](../../../results/A/consistency.md).
