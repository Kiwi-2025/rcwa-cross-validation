# Lumerical RCWA examples

These scripts are generated from the case definitions and the quick profile. Open one in the script editor of a new, unsaved Lumerical FDTD document. Each script builds a single point and writes its native datasets to a case-specific MAT file.

| Case | Script | Setting |
| --- | --- | --- |
| A01 | [Fresnel interface](A/A01.lsf) | Normal incidence from air |
| A02 | [Antireflection film](A/A02.lsf) | 400 nm |
| B01 | [Binary dielectric grating](B/B01.lsf) | 620 nm |
| C02 | [Photonic crystal slab](C/C02.lsf) | a/λ = 0.5058 |

Generate additional models with `rcwa-cv export-lumerical <category>/<case> --point <index>`.
