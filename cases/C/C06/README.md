# C06 — Metagrating supercell

Compare power in the target (+1, 0) transmitted order and other orders of a four-pillar beam-steering supercell.

The geometry and scan points are defined in [case.yaml](case.yaml). Lengths and vacuum wavelengths use nanometers, and angles use degrees.

The upper scan point is 1799.9 nm, just below the transmitted second-order Rayleigh cutoff at 1800 nm.

```powershell
rcwa-cv run C/C06 --profile quick
rcwa-cv converge C/C06
```

See the [category consistency table](../../../results/C/consistency.md).
