# RCWA Cross-Validation

Many open-source scientific computing tools have small user communities, relatively few GitHub stars, and limited public feedback. This makes it hard to tell how thoroughly a solver has been exercised, especially on edge cases that could reveal implementation errors or numerical discrepancies large enough to matter in practice.

We built this reproducible benchmark to compare meent, torcwa on CUDA, and grcwa against Lumerical RCWA across 16 optical cases, using results that have passed independent convergence checks.

Since personal laptop have limited memory and GPU resources, more cases are wanted to cover a wider range of physical scenarios. The benchmark is designed to be extensible, so that new cases can be added.

**If you have a use case that isn't covered by the current benchmark, please consider contributing a new case. Feel free to submit a pull request or open an issue.**

## Conclusion

**For routine problems similar to the benchmark cases, we have high confidence that the tested open-source solver configurations agree with Lumerical within the reported tolerances.**

| Start here | Contents |
| --- | --- |
| [Benchmark report](BENCHMARK_REPORT.md) | Convergence and paired agreement for A, B, and C, with figures, software versions, and a conclusion |
| [Case catalog](cases/README.md) | Physical scenarios, possible applications, notebooks, and Lumerical models |
| [Numerical dataset](results/benchmark.json) | Point coordinates, final solver settings, refinement evidence, optical samples, and eligible comparisons |
| [Comparison conventions](docs/conventions.md) | Polarization, reference planes, tolerances, and convergence criteria |

## Physical scenarios

The 16 cases span planar films, one-dimensional gratings, and two-dimensional periodic structures.

| Group | Scenarios covered |
| --- | --- |
| [A · Planar structures](cases/A/) | Fresnel reflection and transmission, total internal reflection, antireflection coatings, Bragg mirrors, and metal-film absorption. |
| [B · One-dimensional gratings](cases/B/) | Binary and high-contrast gratings, conical incidence, trapezoidal profiles, wire-grid polarization, and volume index modulation. |
| [C · Two-dimensional structures](cases/C/) | Perforated absorbing films and dielectric slabs, cylindrical pillar transmission phase, rotated-fin polarization response, laterally shifted bilayers, and first-order diffraction along both transverse axes. |

## Software

| Software or environment | Version or device |
| --- | --- |
| Python | 3.11.8 |
| rcwa-cross-validation | 0.2.0 |
| numpy | 2.4.6 |
| scipy | 1.17.1 |
| matplotlib | 3.10.8 |
| PyYAML | 6.0.3 |
| threadpoolctl | 3.8.0 |
| meent | 0.13.2 |
| grcwa | 0.1.2 |
| torcwa | 0.1.4.2 |
| torch | 2.8.0+cu128 |
| jupyterlab | 4.6.6 |
| ipykernel | 7.4.0 |
| torcwa CUDA runtime | 12.8 |
| torcwa GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| lumerical | v252 |
| Lumerical build | 8.34.4175 |
| Ansys | 2025 R2 |
| OS | Windows 11 (build 22621) |

## Run the benchmark

On Windows, install [uv](https://docs.astral.sh/uv/), use a compatible NVIDIA driver, and install and license Ansys Lumerical FDTD. Run the setup once and then run the benchmark from the repository root:

```powershell
& .\scripts\setup_windows.ps1
& .\.venv\Scripts\rcwa-cv.exe benchmark
```

The benchmark verifies the planar reference, refines the periodic calculations, and updates the report, figures, and single dataset. It resumes A and C from the local convergence cache and reuses the published B evidence when the case definitions and solver versions match. To recompute all three groups from scratch, use `benchmark --fresh-b --cache .runs/full-rebuild` with a new cache directory. The setup installs CUDA PyTorch and Jupyter. For a nonstandard Lumerical installation, set `lumapi_path` in `configs/local.yaml` using [the example](configs/local.example.yaml).

To repeat the targeted B02, B04, and B05 refinements against the current benchmark, run the following from the repository root. The first command can resume from saved samples and supports `--case`, `--solver`, and zero-based `--point` selections.

```powershell
& .\.venv\Scripts\python.exe -m rcwa_cv.validation.b_followup
& .\.venv\Scripts\python.exe -m rcwa_cv.validation.b_followup --publish
```

Class C uses representative two-dimensional structures with shallow patterns and moderate material contrast. Each point requires two successive Fourier checks and an independent grid check before it can enter the four-solver comparison. C06 checks the two transverse Fourier axes separately. Use the following commands to recompute or publish the class C evidence.

```powershell
& .\.venv\Scripts\python.exe -m rcwa_cv.validation.study --group C
& .\.venv\Scripts\python.exe -m rcwa_cv.validation.study --publish
```

## Explore or reproduce a single case

Each case contains `case.yaml`, a Jupyter notebook, and Lumerical `model.fsp` and `model.lsf` files. The notebook starts with the mathematical model, physical scenario, and possible applications. It displays each solver's reported settings for every point, then reruns and compares the observables supported by the convergence evidence. Open the native model to inspect the first excitation point. The class C native models use the reported Lumerical settings for that point. Run the reconstruction script in a **new unsaved FDTD document** because it clears the current layout.

```powershell
& .\.venv\Scripts\jupyter-lab.exe
& .\.venv\Scripts\rcwa-cv.exe run B/B01
& .\.venv\Scripts\rcwa-cv.exe converge C/C02 --profile pilot --representative
& .\.venv\Scripts\rcwa-cv.exe report --run <run_id>
& .\.venv\Scripts\rcwa-cv.exe report --published
& .\.venv\Scripts\python.exe -m pytest -q
```

Individual runs, temporary files, and manually exported Lumerical scripts use the local `.runs/` directory. Use `report --published` to regenerate the unified report and figures from `results/benchmark.json`. The individual `report --run` command only compares points with recorded convergence evidence on both sides.

To export a different sweep point or add a manually computed point to an individual run, use the same zero-based index:

```powershell
& .\.venv\Scripts\rcwa-cv.exe export-lumerical C/C02 --point 2
& .\.venv\Scripts\rcwa-cv.exe import-lumerical --run <run_id> --point 2 --mat <path-to-rcwa_output.mat>
```

## License

The project's original benchmark materials, including the reports, case models, figures, data, and reproduction code, are available under the [MIT License](LICENSE). Third-party software and materials retain their respective licenses.

## Open-source solver repositories

- [meent](https://github.com/kc-ml2/meent)
- [torcwa](https://github.com/kch3782/torcwa)
- [grcwa](https://github.com/weiliangjinca/grcwa)
