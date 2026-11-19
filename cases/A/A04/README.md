# A04 — Absorbing metal film

Check passive absorption and phase against the thin-film reference. The metal uses a fixed illustrative near-infrared permittivity.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

```powershell
rcwa-cv run A/A04 --profile quick
rcwa-cv converge A/A04
```

See the [category consistency table](../../../results/A/consistency.md).
